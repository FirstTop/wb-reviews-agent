"""Обработчик логики работы с отзывами"""
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import logging

from database.models import Review, Response, TelegramNotification, ReviewStatus, ResponseStatus
from services.wb_service import WBService
from services.ai_service import AIService
from services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class ReviewHandler:
    """Обработчик отзывов"""
    
    def __init__(self, db: Session):
        self.db = db
        self.wb_service = WBService()
        self.ai_service = AIService()
        self.telegram_service = TelegramService()
        self.telegram_service.initialize()
        
        # Регистрация обработчиков callback
        self.telegram_service.register_callback_handler("publish", self._handle_publish)
        self.telegram_service.register_callback_handler("regenerate", self._handle_regenerate)
        self.telegram_service.register_callback_handler("edit_manual", self._handle_edit_manual)
        self.telegram_service.register_callback_handler("skip", self._handle_skip)
    
    async def process_reviews(self, reviews_list: List[Dict]):
        """
        Обработка списка отзывов
        
        Args:
            reviews_list: Список отзывов из WB API
        """
        for review_data in reviews_list:
            try:
                await self.process_review(review_data)
            except Exception as e:
                logger.error(f"Ошибка при обработке отзыва: {e}")
                continue
    
    async def process_review(self, review_data: Dict):
        """
        Обработка одного отзыва
        
        Args:
            review_data: Данные отзыва из WB API
        """
        # Парсинг данных отзыва
        parsed_data = self.wb_service.parse_review(review_data)
        wb_review_id = parsed_data["wb_review_id"]
        
        # Проверка, существует ли отзыв в БД
        existing_review = self.db.query(Review).filter(
            Review.wb_review_id == wb_review_id
        ).first()
        
        if existing_review:
            logger.info(f"Отзыв {wb_review_id} уже обработан, пропускаем")
            return
        
        # Создание записи в БД
        review = Review(
            wb_review_id=wb_review_id,
            product_id=parsed_data.get("product_id"),
            nm_id=parsed_data.get("nm_id"),
            supplier_article=parsed_data.get("supplier_article"),
            rating=parsed_data.get("rating", 0),
            text=parsed_data.get("text"),
            pros=parsed_data.get("pros"),
            cons=parsed_data.get("cons"),
            author=parsed_data.get("author"),
            date=parsed_data.get("date"),
            status=ReviewStatus.NEW
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        logger.info(f"Новый отзыв {review.id} (WB ID: {wb_review_id}) добавлен в БД")
        
        # Маршрутизация по рейтингу
        if review.rating >= 4:
            await self.handle_positive_review(review)
        else:
            await self.handle_negative_review(review)
    
    async def handle_positive_review(self, review: Review):
        """
        Обработка положительного отзыва (4+ звезд)
        Автоматическая генерация и публикация ответа
        
        Args:
            review: Объект отзыва из БД
        """
        logger.info(f"Обработка положительного отзыва {review.id} (рейтинг: {review.rating})")
        
        # Генерация ответа
        response_text = await self.ai_service.generate_response(
            review_text=review.text or "",
            rating=review.rating,
            pros=review.pros,
            cons=review.cons
        )
        
        if not response_text:
            logger.error(f"Не удалось сгенерировать ответ для отзыва {review.id}")
            review.status = ReviewStatus.PENDING
            self.db.commit()
            return
        
        # Сохранение ответа в БД
        response = Response(
            review_id=review.id,
            text=response_text,
            status=ResponseStatus.DRAFT,
            is_manual_edit=False
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        
        # Публикация ответа
        success = await self.wb_service.post_response(
            review.wb_review_id,
            response_text
        )
        
        if success:
            response.status = ResponseStatus.PUBLISHED
            response.published_at = datetime.utcnow()
            review.status = ReviewStatus.PUBLISHED
            logger.info(f"Ответ на отзыв {review.id} успешно опубликован")
        else:
            response.status = ResponseStatus.APPROVED
            review.status = ReviewStatus.PENDING
            logger.warning(f"Не удалось опубликовать ответ на отзыв {review.id}")
        
        self.db.commit()
    
    async def handle_negative_review(self, review: Review):
        """
        Обработка отрицательного отзыва (<4 звезд)
        Генерация черновика и отправка в Telegram
        
        Args:
            review: Объект отзыва из БД
        """
        logger.info(f"Обработка отрицательного отзыва {review.id} (рейтинг: {review.rating})")
        
        # Генерация черновика ответа
        draft_response = await self.ai_service.generate_response(
            review_text=review.text or "",
            rating=review.rating,
            pros=review.pros,
            cons=review.cons
        )
        
        if not draft_response:
            logger.error(f"Не удалось сгенерировать черновик для отзыва {review.id}")
            review.status = ReviewStatus.PENDING
            self.db.commit()
            return
        
        # Сохранение черновика в БД
        response = Response(
            review_id=review.id,
            text=draft_response,
            status=ResponseStatus.DRAFT,
            is_manual_edit=False
        )
        self.db.add(response)
        review.status = ReviewStatus.PENDING
        self.db.commit()
        self.db.refresh(response)
        
        # Отправка карточки в Telegram
        review_data = {
            "rating": review.rating,
            "author": review.author or "Неизвестно",
            "date": review.date.isoformat() if review.date else "",
            "supplier_article": review.supplier_article or "N/A",
            "nm_id": review.nm_id or "N/A",
            "text": review.text or "",
            "pros": review.pros or "",
            "cons": review.cons or ""
        }
        
        message_id = await self.telegram_service.send_review_card(
            review_data=review_data,
            draft_response=draft_response,
            review_id=review.id,
            nm_id=review.nm_id or "N/A"
        )
        
        if message_id:
            # Сохранение информации о Telegram уведомлении
            notification = TelegramNotification(
                review_id=review.id,
                message_id=str(message_id),
                status="sent"
            )
            self.db.add(notification)
            self.db.commit()
            logger.info(f"Карточка отзыва {review.id} отправлена в Telegram")
    
    async def _handle_publish(self, review_id: int, update, context):
        """Обработка нажатия кнопки 'Опубликовать'"""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            await update.callback_query.message.reply_text("Отзыв не найден")
            return
        
        # Получение последнего ответа
        response = self.db.query(Response).filter(
            Response.review_id == review_id
        ).order_by(Response.created_at.desc()).first()
        
        if not response:
            await update.callback_query.message.reply_text("Ответ не найден")
            return
        
        # Публикация ответа
        success = await self.wb_service.post_response(
            review.wb_review_id,
            response.text
        )
        
        if success:
            response.status = ResponseStatus.PUBLISHED
            response.published_at = datetime.utcnow()
            review.status = ReviewStatus.PUBLISHED
            
            # Обновление уведомления
            notification = self.db.query(TelegramNotification).filter(
                TelegramNotification.review_id == review_id
            ).order_by(TelegramNotification.created_at.desc()).first()
            if notification:
                notification.action_type = "publish"
                notification.action_taken_at = datetime.utcnow()
                notification.status = "completed"
            
            self.db.commit()
            await update.callback_query.message.reply_text("✅ Ответ успешно опубликован!")
        else:
            await update.callback_query.message.reply_text("❌ Ошибка при публикации ответа")
    
    async def _handle_regenerate(self, review_id: int, update, context):
        """Обработка нажатия кнопки 'Перегенерировать'"""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            await update.callback_query.message.reply_text("Отзыв не найден")
            return
        
        # Генерация нового ответа
        new_response = await self.ai_service.generate_response(
            review_text=review.text or "",
            rating=review.rating,
            pros=review.pros,
            cons=review.cons
        )
        
        if not new_response:
            await update.callback_query.message.reply_text("❌ Ошибка при генерации ответа")
            return
        
        # Обновление ответа в БД
        response = self.db.query(Response).filter(
            Response.review_id == review_id
        ).order_by(Response.created_at.desc()).first()
        
        if response:
            response.text = new_response
        else:
            response = Response(
                review_id=review_id,
                text=new_response,
                status=ResponseStatus.DRAFT,
                is_manual_edit=False
            )
            self.db.add(response)
        
        self.db.commit()
        
        # Отправка новой карточки
        review_data = {
            "rating": review.rating,
            "author": review.author or "Неизвестно",
            "date": review.date.isoformat() if review.date else "",
            "supplier_article": review.supplier_article or "N/A",
            "nm_id": review.nm_id or "N/A",
            "text": review.text or "",
            "pros": review.pros or "",
            "cons": review.cons or ""
        }
        
        await self.telegram_service.send_review_card(
            review_data=review_data,
            draft_response=new_response,
            review_id=review.id,
            nm_id=review.nm_id or "N/A"
        )
        
        await update.callback_query.message.reply_text("🔁 Ответ перегенерирован! Новая карточка отправлена.")
    
    async def _handle_edit_manual(self, review_id: int, update, context):
        """Обработка нажатия кнопки 'Правка вручную'"""
        await update.callback_query.message.reply_text(
            "✍️ Введите текст ответа, который хотите опубликовать:"
        )
        # TODO: Реализовать сохранение состояния ожидания ввода текста
        # Можно использовать context.user_data для хранения review_id
    
    async def _handle_skip(self, review_id: int, update, context):
        """Обработка нажатия кнопки 'Пропустить'"""
        review = self.db.query(Review).filter(Review.id == review_id).first()
        if not review:
            await update.callback_query.message.reply_text("Отзыв не найден")
            return
        
        review.status = ReviewStatus.SKIPPED
        
        # Обновление уведомления
        notification = self.db.query(TelegramNotification).filter(
            TelegramNotification.review_id == review_id
        ).order_by(TelegramNotification.created_at.desc()).first()
        if notification:
            notification.action_type = "skip"
            notification.action_taken_at = datetime.utcnow()
            notification.status = "completed"
        
        self.db.commit()
        await update.callback_query.message.reply_text("🚫 Отзыв пропущен. Переходим к следующему.")

