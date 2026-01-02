"""Скрипт для инициализации базы данных"""
from database.db import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Инициализация базы данных...")
    try:
        init_db()
        logger.info("✅ База данных успешно инициализирована!")
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации БД: {e}")
        raise

