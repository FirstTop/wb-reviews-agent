"""Сервис для работы с Telegram ботом"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from typing import Optional
from config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для работы с Telegram ботом"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.application: Optional[Application] = None
        self.callback_handlers = {}
    
    def initialize(self):
        """Инициализация Telegram бота"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Регистрация обработчиков
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message)
        )
        
        logger.info("Telegram бот инициализирован")
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        if not self.application:
            self.initialize()
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            logger.info("Telegram бот запущен в режиме polling")
        except Exception as e:
            logger.error(f"Ошибка при запуске Telegram бота: {e}")
            raise
    
    async def stop_polling(self):
        """Остановка бота"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    def format_review_card(self, review_data: dict, draft_response: str) -> str:
        """
        Форматирование карточки отзыва для отправки в Telegram
        
        Args:
            review_data: Данные отзыва
            draft_response: Черновик ответа ИИ
        
        Returns:
            Отформатированный текст карточки
        """
        rating = review_data.get("rating", 0)
        author = review_data.get("author", "Неизвестно")
        date = review_data.get("date", "")
        supplier_article = review_data.get("supplier_article", "N/A")
        nm_id = review_data.get("nm_id", "N/A")
        
        # Форматирование даты
        if isinstance(date, str):
            try:
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                formatted_date = date
        else:
            formatted_date = str(date)
        
        # Сборка текста отзыва
        review_parts = []
        if review_data.get("pros"):
            review_parts.append(f"✅ Плюсы:\n{review_data['pros']}")
        if review_data.get("cons"):
            review_parts.append(f"❌ Минусы:\n{review_data['cons']}")
        if review_data.get("text"):
            review_parts.append(f"📝 Текст:\n{review_data['text']}")
        
        review_text = "\n\n".join(review_parts) if review_parts else "Нет текста"
        
        card = f"""⭐ Рейтинг: {rating}/5
👤 {author}
📅 {formatted_date}

📦 Артикул: {supplier_article}
🆔 nmId: {nm_id}

📝 Отзыв:
{review_text}

💬 Черновик ответа:
{draft_response}"""
        
        return card
    
    def create_review_keyboard(self, review_id: int, nm_id: str) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры с кнопками для карточки отзыва
        
        Args:
            review_id: ID отзыва в нашей БД
            nm_id: nmId товара для ссылки
        
        Returns:
            InlineKeyboardMarkup с кнопками
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{review_id}"),
                InlineKeyboardButton("🔁 Перегенерировать", callback_data=f"regenerate_{review_id}"),
                InlineKeyboardButton("✍️ Правка вручную", callback_data=f"edit_manual_{review_id}")
            ],
            [
                InlineKeyboardButton("🚫 Пропустить", callback_data=f"skip_{review_id}"),
                InlineKeyboardButton("📎 Показать товар", callback_data=f"show_product_{nm_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_review_card(self, review_data: dict, draft_response: str, 
                              review_id: int, nm_id: str) -> Optional[int]:
        """
        Отправка карточки отзыва в Telegram
        
        Args:
            review_data: Данные отзыва
            draft_response: Черновик ответа ИИ
            review_id: ID отзыва в нашей БД
            nm_id: nmId товара
        
        Returns:
            message_id отправленного сообщения или None
        """
        try:
            if not self.application:
                self.initialize()
            
            card_text = self.format_review_card(review_data, draft_response)
            keyboard = self.create_review_keyboard(review_id, nm_id)
            
            message = await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=card_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Карточка отзыва {review_id} отправлена в Telegram (message_id: {message.message_id})")
            return message.message_id
            
        except Exception as e:
            logger.error(f"Ошибка при отправке карточки отзыва в Telegram: {e}")
            return None
    
    def register_callback_handler(self, action_type: str, handler):
        """
        Регистрация обработчика callback для определенного действия
        
        Args:
            action_type: Тип действия (publish, regenerate, skip, etc.)
            handler: Функция-обработчик
        """
        self.callback_handlers[action_type] = handler
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback от inline-кнопок"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        # Парсинг callback_data
        if callback_data.startswith("publish_"):
            review_id = int(callback_data.split("_")[1])
            handler = self.callback_handlers.get("publish")
            if handler:
                await handler(review_id, update, context)
        
        elif callback_data.startswith("regenerate_"):
            review_id = int(callback_data.split("_")[1])
            handler = self.callback_handlers.get("regenerate")
            if handler:
                await handler(review_id, update, context)
        
        elif callback_data.startswith("edit_manual_"):
            review_id = int(callback_data.split("_")[2])
            handler = self.callback_handlers.get("edit_manual")
            if handler:
                await handler(review_id, update, context)
        
        elif callback_data.startswith("skip_"):
            review_id = int(callback_data.split("_")[1])
            handler = self.callback_handlers.get("skip")
            if handler:
                await handler(review_id, update, context)
        
        elif callback_data.startswith("show_product_"):
            nm_id = callback_data.split("_")[2]
            product_url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"
            await query.message.reply_text(f"📎 Ссылка на товар:\n{product_url}")
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений (для режима ручного редактирования)"""
        # Эта логика будет реализована в review_handler
        # Здесь можно добавить обработку ввода текста для ручного редактирования
        pass

