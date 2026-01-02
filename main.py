from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import platform
import sys
import logging
from contextlib import asynccontextmanager

from database.db import get_db, init_db
from database.models import Review, Response, TelegramNotification, ReviewStatus
from services.wb_service import WBService
from handlers.review_handler import ReviewHandler
from scheduler.tasks import start_scheduler, stop_scheduler
from services.telegram_service import TelegramService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Инициализация приложения...")
    
    # Инициализация БД
    try:
        init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
    
    # Запуск планировщика
    try:
        start_scheduler()
        logger.info("Планировщик запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")
    
    # Запуск Telegram бота в фоне
    try:
        import asyncio
        telegram_service = TelegramService()
        telegram_service.initialize()
        # Запуск polling в фоне
        async def run_bot():
            await telegram_service.start_polling()
        asyncio.create_task(run_bot())
        logger.info("Telegram бот запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram бота: {e}")
    
    yield
    
    # Shutdown
    logger.info("Остановка приложения...")
    stop_scheduler()
    logger.info("Приложение остановлено")


app = FastAPI(
    title="WB Reviews Agent",
    version="1.0.0",
    description="Система автоматической обработки отзывов Wildberries",
    lifespan=lifespan
)


@app.get("/")
def root():
    """Главная страница - проверка работы сервера"""
    return {
        "status": "ok",
        "message": "WB Reviews Agent работает! 🚀",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "reviews": "/reviews",
            "stats": "/stats",
            "process": "/reviews/process (POST)"
        }
    }


@app.get("/health")
def health_check():
    """Health check эндпоинт для мониторинга"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/info")
def server_info():
    """Информация о сервере и системе"""
    return {
        "server": {
            "status": "running",
            "timestamp": datetime.now().isoformat()
        },
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "processor": platform.processor()
        }
    }


@app.get("/test")
def test_endpoint():
    """Простой тестовый эндпоинт"""
    return {
        "message": "Тест пройден успешно! ✅",
        "timestamp": datetime.now().isoformat(),
        "test_data": {
            "number": 42,
            "text": "Hello, Server!",
            "boolean": True
        }
    }


@app.get("/reviews")
def get_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка всех отзывов"""
    reviews = db.query(Review).offset(skip).limit(limit).all()
    return {
        "total": db.query(Review).count(),
        "reviews": [
            {
                "id": review.id,
                "wb_review_id": review.wb_review_id,
                "rating": review.rating,
                "author": review.author,
                "status": review.status.value,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ]
    }


@app.get("/reviews/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Получение детальной информации об отзыве"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    responses = db.query(Response).filter(Response.review_id == review_id).all()
    
    return {
        "id": review.id,
        "wb_review_id": review.wb_review_id,
        "product_id": review.product_id,
        "nm_id": review.nm_id,
        "supplier_article": review.supplier_article,
        "rating": review.rating,
        "text": review.text,
        "pros": review.pros,
        "cons": review.cons,
        "author": review.author,
        "date": review.date.isoformat() if review.date else None,
        "status": review.status.value,
        "created_at": review.created_at.isoformat(),
        "responses": [
            {
                "id": resp.id,
                "text": resp.text,
                "status": resp.status.value,
                "is_manual_edit": resp.is_manual_edit,
                "created_at": resp.created_at.isoformat(),
                "published_at": resp.published_at.isoformat() if resp.published_at else None
            }
            for resp in responses
        ]
    }


@app.post("/reviews/process")
async def process_reviews(db: Session = Depends(get_db)):
    """Ручной запуск обработки новых отзывов"""
    try:
        wb_service = WBService()
        reviews = await wb_service.get_reviews()
        
        if not reviews:
            return {"message": "Новых отзывов не найдено", "processed": 0}
        
        handler = ReviewHandler(db)
        await handler.process_reviews(reviews)
        
        return {
            "message": "Обработка завершена",
            "processed": len(reviews)
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке отзывов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Статистика обработки отзывов"""
    total_reviews = db.query(Review).count()
    published = db.query(Review).filter(Review.status == ReviewStatus.PUBLISHED).count()
    pending = db.query(Review).filter(Review.status == ReviewStatus.PENDING).count()
    skipped = db.query(Review).filter(Review.status == ReviewStatus.SKIPPED).count()
    new_reviews = db.query(Review).filter(Review.status == ReviewStatus.NEW).count()
    
    total_responses = db.query(Response).count()
    published_responses = db.query(Response).filter(Response.status == "published").count()
    
    return {
        "reviews": {
            "total": total_reviews,
            "published": published,
            "pending": pending,
            "skipped": skipped,
            "new": new_reviews
        },
        "responses": {
            "total": total_responses,
            "published": published_responses
        },
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 WB Reviews Agent запускается...")
    print("📡 Доступные эндпоинты:")
    print("   - GET  /              - Главная страница")
    print("   - GET  /health        - Health check")
    print("   - GET  /info          - Информация о системе")
    print("   - GET  /reviews       - Список отзывов")
    print("   - GET  /reviews/{id}  - Детали отзыва")
    print("   - POST /reviews/process - Ручная обработка отзывов")
    print("   - GET  /stats         - Статистика")
    print("\n🌐 Откройте в браузере: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("⏰ Планировщик проверяет отзывы каждый час")
    print("🤖 Telegram бот работает в фоне\n")
    uvicorn.run(app, host="0.0.0.0", port=8000) 