"""
Rate Limiting Middleware

Implements sophisticated rate limiting to protect against spam and abuse:
- Global rate limits
- Per-user rate limits
- Per-chat rate limits
- Configurable time windows
- Redis backend for distributed systems
- Memory backend for simple deployments
- Automatic cleanup of old records
"""

import time
import logging
from typing import Dict, Any, Callable, Awaitable
from collections import defaultdict, deque
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.config import settings


logger = logging.getLogger(__name__)


class MemoryRateLimiter:
    """In-memory rate limiter using sliding window."""
    
    def __init__(self):
        self._global_requests = deque()
        self._user_requests = defaultdict(lambda: deque())
        self._chat_requests = defaultdict(lambda: deque())
        self._last_cleanup = time.time()
    
    def _cleanup_old_records(self, current_time: float):
        """Remove records older than 1 minute."""
        cutoff_time = current_time - 60
        
        # Clean global requests
        while self._global_requests and self._global_requests[0] < cutoff_time:
            self._global_requests.popleft()
        
        # Clean user requests
        for user_id in list(self._user_requests.keys()):
            requests = self._user_requests[user_id]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self._user_requests[user_id]
        
        # Clean chat requests
        for chat_id in list(self._chat_requests.keys()):
            requests = self._chat_requests[chat_id]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self._chat_requests[chat_id]
        
        self._last_cleanup = current_time
    
    async def is_allowed(self, user_id: int, chat_id: int = None) -> tuple[bool, str]:
        """
        Check if request is allowed under rate limits.
        
        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID (optional)
        
        Returns:
            tuple: (is_allowed, reason_if_blocked)
        """
        current_time = time.time()
        
        # Periodic cleanup (every 30 seconds)
        if current_time - self._last_cleanup > 30:
            self._cleanup_old_records(current_time)
        
        # Check global rate limit
        global_count = len(self._global_requests)
        if global_count >= settings.MAX_MESSAGES_PER_MINUTE:
            return False, "Global rate limit exceeded. Please try again later."
        
        # Check per-user rate limit
        user_count = len(self._user_requests[user_id])
        if user_count >= settings.MAX_MESSAGES_PER_CHAT_PER_MINUTE:
            return False, "You're sending messages too quickly. Please slow down."
        
        # Check per-chat rate limit (if in a group)
        if chat_id and chat_id != user_id:  # Group chat
            chat_count = len(self._chat_requests[chat_id])
            if chat_count >= settings.MAX_MESSAGES_PER_CHAT_PER_MINUTE:
                return False, "This chat is being used too frequently. Please wait."
        
        return True, ""
    
    async def record_request(self, user_id: int, chat_id: int = None):
        """Record a new request."""
        current_time = time.time()
        
        # Record global request
        self._global_requests.append(current_time)
        
        # Record user request
        self._user_requests[user_id].append(current_time)
        
        # Record chat request (if in a group)
        if chat_id and chat_id != user_id:
            self._chat_requests[chat_id].append(current_time)


class RedisRateLimiter:
    """Redis-based rate limiter for distributed systems."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_allowed(self, user_id: int, chat_id: int = None) -> tuple[bool, str]:
        """Check if request is allowed using Redis sliding window."""
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window
        
        # Check global rate limit
        global_key = "rate_limit:global"
        global_count = await self._count_requests(global_key, window_start, current_time)
        if global_count >= settings.MAX_MESSAGES_PER_MINUTE:
            return False, "Global rate limit exceeded. Please try again later."
        
        # Check per-user rate limit
        user_key = f"rate_limit:user:{user_id}"
        user_count = await self._count_requests(user_key, window_start, current_time)
        if user_count >= settings.MAX_MESSAGES_PER_CHAT_PER_MINUTE:
            return False, "You're sending messages too quickly. Please slow down."
        
        # Check per-chat rate limit
        if chat_id and chat_id != user_id:
            chat_key = f"rate_limit:chat:{chat_id}"
            chat_count = await self._count_requests(chat_key, window_start, current_time)
            if chat_count >= settings.MAX_MESSAGES_PER_CHAT_PER_MINUTE:
                return False, "This chat is being used too frequently. Please wait."
        
        return True, ""
    
    async def record_request(self, user_id: int, chat_id: int = None):
        """Record a new request in Redis."""
        current_time = int(time.time())
        
        # Record global request
        await self._record_request("rate_limit:global", current_time)
        
        # Record user request
        await self._record_request(f"rate_limit:user:{user_id}", current_time)
        
        # Record chat request
        if chat_id and chat_id != user_id:
            await self._record_request(f"rate_limit:chat:{chat_id}", current_time)
    
    async def _count_requests(self, key: str, start_time: int, end_time: int) -> int:
        """Count requests in time window using Redis ZCOUNT."""
        try:
            count = await self.redis.zcount(key, start_time, end_time)
            return count
        except Exception as e:
            logger.error(f"Redis count error for {key}: {e}")
            return 0  # Fail open
    
    async def _record_request(self, key: str, timestamp: int):
        """Record a request using Redis ZADD with automatic cleanup."""
        try:
            pipe = self.redis.pipeline()
            # Add current request
            pipe.zadd(key, {str(timestamp): timestamp})
            # Remove old requests (older than 2 minutes to be safe)
            pipe.zremrangebyscore(key, 0, timestamp - 120)
            # Set expiration for the key
            pipe.expire(key, 180)  # 3 minutes
            await pipe.execute()
        except Exception as e:
            logger.error(f"Redis record error for {key}: {e}")


class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting middleware for aiogram."""
    
    def __init__(self):
        super().__init__()
        self.limiter = self._create_limiter()
        logger.info(f"Rate limiter initialized: {type(self.limiter).__name__}")
    
    def _create_limiter(self):
        """Create appropriate rate limiter based on configuration."""
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis
                redis_client = redis.from_url(settings.REDIS_URL)
                logger.info("Using Redis rate limiter")
                return RedisRateLimiter(redis_client)
            except ImportError:
                logger.warning("Redis not available, falling back to memory rate limiter")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}. Using memory rate limiter")
        
        logger.info("Using memory rate limiter")
        return MemoryRateLimiter()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process incoming update through rate limiter.
        
        Args:
            handler: Next handler in chain
            event: Telegram update event
            data: Handler data
        
        Returns:
            Handler result or None if rate limited
        """
        # Extract user and chat IDs
        user_id = None
        chat_id = None
        
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id if event.from_user else None
            
            if isinstance(event, Message):
                chat_id = event.chat.id
            elif isinstance(event, CallbackQuery) and event.message:
                chat_id = event.message.chat.id
        
        if not user_id:
            # No user info, allow the request
            return await handler(event, data)
        
        # Check rate limits
        is_allowed, reason = await self.limiter.is_allowed(user_id, chat_id)
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for user {user_id} in chat {chat_id}: {reason}"
            )
            
            # Send rate limit message
            if isinstance(event, Message):
                await event.answer(
                    f"⚠️ {reason}\n\nRate limits help keep the bot fast and reliable for everyone.",
                    show_alert=True
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"⚠️ {reason}",
                    show_alert=True
                )
            
            return  # Don't process the update
        
        # Record the request
        await self.limiter.record_request(user_id, chat_id)
        
        # Continue to next handler
        return await handler(event, data)
