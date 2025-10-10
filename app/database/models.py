"""
Database Models

Defines all SQLAlchemy models for the reminder bot:
- User: Telegram user information and settings
- Reminder: Individual reminder entries with scheduling
- ReminderTemplate: Reusable reminder templates
- UserStats: Usage statistics and analytics

Features:
- Async SQLAlchemy 2.0 compatible
- Proper relationships and indexes
- Timezone support
- Status tracking
- Soft delete support
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, 
    ForeignKey, Enum, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class ReminderStatus(enum.Enum):
    """Reminder status enumeration."""
    PENDING = "pending"      # Scheduled but not sent
    SENT = "sent"            # Successfully sent
    FAILED = "failed"        # Failed to send
    CANCELLED = "cancelled"  # Cancelled by user
    EXPIRED = "expired"      # Past due date


class RepeatType(enum.Enum):
    """Repeat type enumeration."""
    NONE = "none"        # One-time reminder
    DAILY = "daily"      # Every day
    WEEKLY = "weekly"    # Every week
    MONTHLY = "monthly"  # Every month
    YEARLY = "yearly"    # Every year
    CUSTOM = "custom"    # Custom interval


class User(Base):
    """User model for storing Telegram user information and preferences."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Telegram data
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="en")
    
    # User preferences
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status and tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    templates: Mapped[List["ReminderTemplate"]] = relationship(
        "ReminderTemplate", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    stats: Mapped[Optional["UserStats"]] = relationship(
        "UserStats", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class Reminder(Base):
    """Reminder model for storing individual reminders."""
    
    __tablename__ = "reminders"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Reminder content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    
    # Repeat settings
    repeat_type: Mapped[RepeatType] = mapped_column(
        Enum(RepeatType), 
        nullable=False, 
        default=RepeatType.NONE
    )
    repeat_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For custom repeats
    repeat_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status and metadata
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus), 
        nullable=False, 
        default=ReminderStatus.PENDING
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # Soft delete
    
    # Execution info
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Additional data (JSON field for extensibility)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reminders")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_scheduled', user_id, scheduled_at),
        Index('idx_status_scheduled', status, scheduled_at),
        Index('idx_user_status', user_id, status),
    )
    
    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, title='{self.title[:50]}', scheduled_at='{self.scheduled_at}')>"


class ReminderTemplate(Base):
    """Template model for reusable reminder templates."""
    
    __tablename__ = "reminder_templates"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Template content
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Default settings
    default_repeat_type: Mapped[RepeatType] = mapped_column(
        Enum(RepeatType), 
        nullable=False, 
        default=RepeatType.NONE
    )
    default_repeat_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="templates")
    
    def __repr__(self) -> str:
        return f"<ReminderTemplate(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class UserStats(Base):
    """User statistics model for analytics and usage tracking."""
    
    __tablename__ = "user_stats"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Usage statistics
    total_reminders_created: Mapped[int] = mapped_column(Integer, default=0)
    total_reminders_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_reminders_failed: Mapped[int] = mapped_column(Integer, default=0)
    total_templates_created: Mapped[int] = mapped_column(Integer, default=0)
    
    # Activity statistics
    total_messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_commands_used: Mapped[int] = mapped_column(Integer, default=0)
    first_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_interaction: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="stats")
    
    def __repr__(self) -> str:
        return f"<UserStats(user_id={self.user_id}, total_reminders={self.total_reminders_created})>"
