"""
Database Models

SQLAlchemy models for reminders, users, and statistics
with comprehensive relationships and indexes.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, func
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Telegram user info
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # User preferences
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Tracking info
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    reminders: Mapped[List["Reminder"]] = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    statistics: Mapped[Optional["UserStatistics"]] = relationship("UserStatistics", back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class Reminder(Base):
    """Reminder model for storing user reminders."""
    
    __tablename__ = "reminders"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Reminder content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Scheduling info
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Status tracking
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Recurring reminders
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "daily", "weekly", etc.
    recurrence_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Category and priority
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)  # low, normal, high
    
    # Additional metadata
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original user input
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reminders")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_scheduled_time", "user_id", "scheduled_time"),
        Index("idx_scheduled_unsent", "scheduled_time", "is_sent"),
        Index("idx_user_category", "user_id", "category"),
    )
    
    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, title='{self.title}', scheduled_time={self.scheduled_time})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if reminder is overdue."""
        return not self.is_sent and self.scheduled_time < datetime.utcnow()
    
    @property
    def time_until_due(self) -> Optional[timedelta]:
        """Get time until reminder is due."""
        if self.is_sent:
            return None
        
        now = datetime.utcnow()
        if self.scheduled_time > now:
            return self.scheduled_time - now
        return None


class UserStatistics(Base):
    """User statistics model for tracking usage."""
    
    __tablename__ = "user_statistics"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Reminder statistics
    total_reminders_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_reminders_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_reminders_missed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Usage statistics
    total_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_commands_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Time statistics
    average_reminder_lead_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    most_active_hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-23
    
    # Tracking
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="statistics")
    
    def __repr__(self) -> str:
        return f"<UserStatistics(user_id={self.user_id}, total_reminders={self.total_reminders_created})>"
    
    @property
    def completion_rate(self) -> float:
        """Calculate reminder completion rate."""
        if self.total_reminders_created == 0:
            return 0.0
        return (self.total_reminders_sent / self.total_reminders_created) * 100
    
    @property
    def miss_rate(self) -> float:
        """Calculate reminder miss rate."""
        if self.total_reminders_created == 0:
            return 0.0
        return (self.total_reminders_missed / self.total_reminders_created) * 100


class ReminderTemplate(Base):
    """Template model for reusable reminders."""
    
    __tablename__ = "reminder_templates"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Template content
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title_template: Mapped[str] = mapped_column(String(255), nullable=False)
    description_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Default settings
    default_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    default_priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    default_lead_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_template_name"),
        Index("idx_user_templates", "user_id", "usage_count"),
    )
    
    def __repr__(self) -> str:
        return f"<ReminderTemplate(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"


class SystemLog(Base):
    """System log model for tracking bot operations."""
    
    __tablename__ = "system_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Log info
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR
    message: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Context
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    reminder_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    
    # Additional data (JSON string)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"
