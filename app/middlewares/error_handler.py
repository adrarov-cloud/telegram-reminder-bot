"""
Error Handling Middleware

Provides comprehensive error handling:
- Catches and logs all exceptions
- Provides user-friendly error messages
- Different handling for different error types
- Error reporting for monitoring
- Graceful degradation
"""

import logging
import traceback
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError
)

from app.config import settings


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware for handling exceptions in message handlers."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Handle exceptions from message handlers.
        
        Args:
            handler: Next handler in chain
            event: Telegram update event
            data: Handler data
        
        Returns:
            Handler result or error response
        """
        try:
            return await handler(event, data)
        
        except TelegramRetryAfter as e:
            # Rate limited by Telegram
            logger.warning(f"Telegram rate limit: retry after {e.retry_after}s")
            await self._send_error_message(
                event, 
                "The bot is temporarily rate limited. Please try again in a moment."
            )
        
        except TelegramForbiddenError as e:
            # Bot blocked or chat restricted
            logger.warning(f"Telegram forbidden: {e}")
            # Don't send error message as user blocked the bot
        
        except TelegramNotFound as e:
            # Message or chat not found
            logger.warning(f"Telegram not found: {e}")
            await self._send_error_message(
                event,
                "The requested item was not found. It may have been deleted."
            )
        
        except TelegramBadRequest as e:
            # Invalid request parameters
            logger.error(f"Telegram bad request: {e}")
            await self._send_error_message(
                event,
                "There was an error with your request. Please try again."
            )
        
        except TelegramNetworkError as e:
            # Network connectivity issues
            logger.error(f"Telegram network error: {e}")
            await self._send_error_message(
                event,
                "Network error occurred. Please try again."
            )
        
        except TelegramServerError as e:
            # Telegram server issues
            logger.error(f"Telegram server error: {e}")
            await self._send_error_message(
                event,
                "Telegram server error. Please try again later."
            )
        
        except Exception as e:
            # All other exceptions
            error_id = self._generate_error_id()
            
            logger.error(
                f"Unhandled error [{error_id}]: {e}\n"
                f"Event: {type(event).__name__}\n"
                f"Data: {data}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Send user-friendly error message
            await self._send_error_message(
                event,
                f"An unexpected error occurred. "
                f"Error ID: {error_id}\n\n"
                f"Please try again or contact support if the problem persists."
            )
    
    async def _send_error_message(self, event: TelegramObject, message: str):
        """Send error message to user."""
        try:
            if isinstance(event, Message):
                await event.answer(f"❌ {message}")
            elif isinstance(event, CallbackQuery):
                await event.answer(f"❌ {message}", show_alert=True)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]
