"""
Database Operations

Async CRUD operations for all models with comprehensive
error handling and transaction management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Dict, Any

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from src.config import config
from src.database.models import Base, User, Reminder, UserStatistics, ReminderTemplate, SystemLog

from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Database engine and session
engine = create_async_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class UserOperations:
    """User database operations."""
    
    @staticmethod
    async def create_or_update_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> User:
        """Create new user or update existing one."""
        # Check if user exists
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.language_code = language_code
            user.last_activity = datetime.utcnow()
            user.is_active = True
        else:
            # Create new user
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )
            session.add(user)
            
            # Create user statistics
            stats = UserStatistics(user=user)
            session.add(stats)
        
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user_timezone(session: AsyncSession, telegram_id: int, timezone: str) -> bool:
        """Update user timezone."""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(timezone=timezone)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_active_users_count(session: AsyncSession) -> int:
        """Get count of active users."""
        stmt = select(func.count(User.id)).where(User.is_active == True)
        result = await session.execute(stmt)
        return result.scalar() or 0


class ReminderOperations:
    """Reminder database operations."""
    
    @staticmethod
    async def create_reminder(
        session: AsyncSession,
        user_id: int,
        title: str,
        description: Optional[str],
        scheduled_time: datetime,
        category: Optional[str] = None,
        priority: str = "normal",
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        recurrence_end_date: Optional[datetime] = None,
        original_text: Optional[str] = None,
    ) -> Reminder:
        """Create new reminder."""
        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=description,
            scheduled_time=scheduled_time,
            category=category,
            priority=priority,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern,
            recurrence_end_date=recurrence_end_date,
            original_text=original_text,
        )
        
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
        
        # Update user statistics
        await UserOperations.increment_reminders_created(session, user_id)
        
        return reminder
    
    @staticmethod
    async def get_user_reminders(
        session: AsyncSession,
        user_id: int,
        include_sent: bool = False,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Reminder]:
        """Get user's reminders."""
        stmt = select(Reminder).where(Reminder.user_id == user_id)
        
        if not include_sent:
            stmt = stmt.where(Reminder.is_sent == False)
        
        if category:
            stmt = stmt.where(Reminder.category == category)
        
        stmt = stmt.order_by(Reminder.scheduled_time)
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_pending_reminders(session: AsyncSession, before_time: datetime) -> List[Reminder]:
        """Get reminders scheduled before specified time that haven't been sent."""
        stmt = (
            select(Reminder)
            .options(selectinload(Reminder.user))
            .where(
                and_(
                    Reminder.scheduled_time <= before_time,
                    Reminder.is_sent == False
                )
            )
            .order_by(Reminder.scheduled_time)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def mark_reminder_sent(session: AsyncSession, reminder_id: int) -> bool:
        """Mark reminder as sent."""
        stmt = (
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(is_sent=True, sent_at=datetime.utcnow())
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        if result.rowcount > 0:
            # Update user statistics
            reminder = await ReminderOperations.get_reminder_by_id(session, reminder_id)
            if reminder:
                await UserOperations.increment_reminders_sent(session, reminder.user_id)
            return True
        
        return False
    
    @staticmethod
    async def get_reminder_by_id(session: AsyncSession, reminder_id: int) -> Optional[Reminder]:
        """Get reminder by ID."""
        stmt = select(Reminder).where(Reminder.id == reminder_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_reminder(
        session: AsyncSession,
        reminder_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> bool:
        """Update reminder."""
        updates = {}
        if title is not None:
            updates["title"] = title
        if description is not None:
            updates["description"] = description
        if scheduled_time is not None:
            updates["scheduled_time"] = scheduled_time
        if category is not None:
            updates["category"] = category
        if priority is not None:
            updates["priority"] = priority
        
        if not updates:
            return False
        
        stmt = update(Reminder).where(Reminder.id == reminder_id).values(**updates)
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount > 0
    
    @staticmethod
    async def delete_reminder(session: AsyncSession, reminder_id: int, user_id: int) -> bool:
        """Delete reminder (with user ownership check)."""
        stmt = delete(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount > 0
    
    @staticmethod
    async def delete_all_user_reminders(session: AsyncSession, user_id: int) -> int:
        """Delete all user's reminders."""
        stmt = delete(Reminder).where(Reminder.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount or 0
    
    @staticmethod
    async def get_overdue_reminders(session: AsyncSession, user_id: int) -> List[Reminder]:
        """Get user's overdue reminders."""
        now = datetime.utcnow()
        stmt = (
            select(Reminder)
            .where(
                and_(
                    Reminder.user_id == user_id,
                    Reminder.scheduled_time < now,
                    Reminder.is_sent == False
                )
            )
            .order_by(Reminder.scheduled_time)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_reminder_stats(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Get user's reminder statistics."""
        # Total reminders
        total_stmt = select(func.count(Reminder.id)).where(Reminder.user_id == user_id)
        total_result = await session.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # Sent reminders
        sent_stmt = select(func.count(Reminder.id)).where(
            and_(Reminder.user_id == user_id, Reminder.is_sent == True)
        )
        sent_result = await session.execute(sent_stmt)
        sent = sent_result.scalar() or 0
        
        # Pending reminders
        pending_stmt = select(func.count(Reminder.id)).where(
            and_(Reminder.user_id == user_id, Reminder.is_sent == False)
        )
        pending_result = await session.execute(pending_stmt)
        pending = pending_result.scalar() or 0
        
        # Overdue reminders
        now = datetime.utcnow()
        overdue_stmt = select(func.count(Reminder.id)).where(
            and_(
                Reminder.user_id == user_id,
                Reminder.scheduled_time < now,
                Reminder.is_sent == False
            )
        )
        overdue_result = await session.execute(overdue_stmt)
        overdue = overdue_result.scalar() or 0
        
        return {
            "total": total,
            "sent": sent,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": (sent / total * 100) if total > 0 else 0,
        }


class StatisticsOperations:
    """Statistics database operations."""
    
    @staticmethod
    async def get_user_statistics(session: AsyncSession, user_id: int) -> Optional[UserStatistics]:
        """Get user statistics."""
        stmt = select(UserStatistics).where(UserStatistics.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def increment_reminders_created(session: AsyncSession, user_id: int) -> None:
        """Increment user's reminders created count."""
        stmt = (
            update(UserStatistics)
            .where(UserStatistics.user_id == user_id)
            .values(
                total_reminders_created=UserStatistics.total_reminders_created + 1,
                last_updated=datetime.utcnow()
            )
        )
        await session.execute(stmt)
        await session.commit()
    
    @staticmethod
    async def increment_reminders_sent(session: AsyncSession, user_id: int) -> None:
        """Increment user's reminders sent count."""
        stmt = (
            update(UserStatistics)
            .where(UserStatistics.user_id == user_id)
            .values(
                total_reminders_sent=UserStatistics.total_reminders_sent + 1,
                last_updated=datetime.utcnow()
            )
        )
        await session.execute(stmt)
        await session.commit()


class SystemLogOperations:
    """System log database operations."""
    
    @staticmethod
    async def create_log(
        session: AsyncSession,
        level: str,
        message: str,
        module: Optional[str] = None,
        user_id: Optional[int] = None,
        reminder_id: Optional[int] = None,
        extra_data: Optional[str] = None,
    ) -> SystemLog:
        """Create system log entry."""
        log = SystemLog(
            level=level,
            message=message,
            module=module,
            user_id=user_id,
            reminder_id=reminder_id,
            extra_data=extra_data,
        )
        
        session.add(log)
        await session.commit()
        return log
    
    @staticmethod
    async def cleanup_old_logs(session: AsyncSession, days_to_keep: int = 30) -> int:
        """Clean up old log entries."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        stmt = delete(SystemLog).where(SystemLog.created_at < cutoff_date)
        result = await session.execute(stmt)
        await session.commit()
        
        return result.rowcount or 0
