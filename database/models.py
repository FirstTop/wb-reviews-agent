"""Модели базы данных"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .db import Base


class ReviewStatus(str, enum.Enum):
    """Статусы отзывов"""
    NEW = "new"
    PENDING = "pending"
    SKIPPED = "skipped"
    PUBLISHED = "published"


class ResponseStatus(str, enum.Enum):
    """Статусы ответов"""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


class Review(Base):
    """Модель отзыва из Wildberries"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    wb_review_id = Column(String, unique=True, index=True, nullable=False)
    product_id = Column(String, index=True)
    nm_id = Column(String, index=True)
    supplier_article = Column(String)
    rating = Column(Integer, nullable=False)
    text = Column(Text)
    pros = Column(Text)
    cons = Column(Text)
    author = Column(String)
    date = Column(DateTime)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.NEW, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    responses = relationship("Response", back_populates="review", cascade="all, delete-orphan")
    telegram_notifications = relationship("TelegramNotification", back_populates="review", cascade="all, delete-orphan")


class Response(Base):
    """Модель ответа на отзыв"""
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    text = Column(Text, nullable=False)
    status = Column(SQLEnum(ResponseStatus), default=ResponseStatus.DRAFT, nullable=False)
    is_manual_edit = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    
    # Связи
    review = relationship("Review", back_populates="responses")


class TelegramNotification(Base):
    """Модель уведомления в Telegram"""
    __tablename__ = "telegram_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    message_id = Column(String, index=True)
    status = Column(String, default="sent")
    action_type = Column(String)  # publish, regenerate, skip, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    action_taken_at = Column(DateTime, nullable=True)
    
    # Связи
    review = relationship("Review", back_populates="telegram_notifications")

