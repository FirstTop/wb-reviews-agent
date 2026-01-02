"""Планировщик задач для периодической проверки отзывов"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from database.db import SessionLocal
from services.wb_service import WBService
from handlers.review_handler import ReviewHandler
from config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_new_reviews():
    """Задача для проверки новых отзывов"""
    logger.info("Запуск проверки новых отзывов")
    
    db: Session = SessionLocal()
    try:
        wb_service = WBService()
        
        # Получаем дату последней проверки (например, час назад)
        date_from = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        
        # Получение отзывов из WB API
        reviews = await wb_service.get_reviews(date_from=date_from)
        
        if not reviews:
            logger.info("Новых отзывов не найдено")
            return
        
        logger.info(f"Найдено {len(reviews)} новых отзывов")
        
        # Обработка отзывов
        handler = ReviewHandler(db)
        await handler.process_reviews(reviews)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке новых отзывов: {e}")
    finally:
        db.close()


def start_scheduler():
    """Запуск планировщика"""
    interval = settings.SCHEDULER_INTERVAL
    
    scheduler.add_job(
        check_new_reviews,
        trigger=IntervalTrigger(seconds=interval),
        id="check_reviews",
        name="Проверка новых отзывов",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Планировщик запущен. Интервал проверки: {interval} секунд ({interval // 60} минут)")


def stop_scheduler():
    """Остановка планировщика"""
    scheduler.shutdown()
    logger.info("Планировщик остановлен")

