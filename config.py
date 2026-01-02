"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # Wildberries API
    WB_API_KEY: str
    WB_API_URL: str = "https://suppliers-api.wildberries.ru"
    
    # OpenRouter API
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./wb_reviews.db"
    
    # Scheduler
    SCHEDULER_INTERVAL: int = 3600  # секунды (1 час)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

