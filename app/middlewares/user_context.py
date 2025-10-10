"""
User Context Middleware

Provides user context loading and management:
- Loads user data from database
- Creates new users automatically
- Updates user activity
- Provides user object in handler data
- Timezone management
- User preferences loading
"""

import logging
from typing import Dict, Any, Callable, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, User as TgUser
from sqlalchemy import select
from datetime import datetime, timezone

from app.database.connection import get_session
from app.database.models import User, UserStats


logger = logging.getLogger(__name__)


class UserContextMiddleware(BaseMiddleware):
    """Middleware for loading user context from database."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Load user context and add to handler data.
        
        Args:
            handler: Next handler in chain
            event: Telegram update event
            data: Handler data
        
        Returns:
            Handler result
        """
        # Extract Telegram user from event
        tg_user = self._extract_telegram_user(event)
        
        if tg_user:
            # Load or create user in database
            try:
                db_user = await self._get_or_create_user(tg_user)
                data['user'] = db_user
                
                # Update user activity
                await self._update_user_activity(db_user, tg_user)
                
                logger.debug(f"Loaded user context: {db_user}")
                
            except Exception as e:
                logger.error(f"Failed to load user context: {e}")
                # Continue without user context rather than fail
                data['user'] = None
        else:
            data['user'] = None
        
        return await handler(event, data)
    
    def _extract_telegram_user(self, event: TelegramObject) -> Optional[TgUser]:
        """Extract Telegram user from event."""
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user
        return None
    
    async def _get_or_create_user(self, tg_user: TgUser) -> User:
        """Get existing user or create new one."""
        async with get_session() as session:
            # Try to find existing user
            result = await session.execute(
                select(User).where(User.telegram_id == tg_user.id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update user information if needed
                updated = False
                
                if user.username != tg_user.username:
                    user.username = tg_user.username
                    updated = True
                
                if user.first_name != tg_user.first_name:
                    user.first_name = tg_user.first_name
                    updated = True
                
                if user.last_name != tg_user.last_name:
                    user.last_name = tg_user.last_name
                    updated = True
                
                if user.language_code != tg_user.language_code:
                    user.language_code = tg_user.language_code
                    updated = True
                
                if user.is_premium != getattr(tg_user, 'is_premium', False):
                    user.is_premium = getattr(tg_user, 'is_premium', False)
                    updated = True
                
                if updated:
                    await session.commit()
                    logger.debug(f"Updated user info for {user.telegram_id}")
                
                return user
            
            else:
                # Create new user
                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    language_code=tg_user.language_code,
                    is_premium=getattr(tg_user, 'is_premium', False),
                    timezone="UTC",  # Default timezone
                    is_active=True,
                    last_activity=datetime.now(timezone.utc)
                )
                
                session.add(user)
                
                # Create user stats
                stats = UserStats(
                    user=user,
                    first_interaction=datetime.now(timezone.utc),
                    last_interaction=datetime.now(timezone.utc)
                )
                
                session.add(stats)
                
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"Created new user: {user.telegram_id} (@{user.username})")
                return user
    
    async def _update_user_activity(self, user: User, tg_user: TgUser):
        """Update user's last activity timestamp."""
        try:
            async with get_session() as session:
                # Update user activity
                user.last_activity = datetime.now(timezone.utc)
                
                # Update stats
                if user.stats:
                    user.stats.last_interaction = datetime.now(timezone.utc)
                    user.stats.total_messages_sent += 1
                
                session.add(user)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update user activity for {user.telegram_id}: {e}")
