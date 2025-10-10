"""
Logging Middleware

Provides comprehensive request/response logging:
- Logs all incoming messages and callbacks
- Performance monitoring
- User activity tracking
- Debug information
- Request correlation
"""

import logging
import time
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineQuery


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging requests and responses."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Log request and response with timing.
        
        Args:
            handler: Next handler in chain
            event: Telegram update event
            data: Handler data
        
        Returns:
            Handler result
        """
        start_time = time.time()
        
        # Log incoming request
        request_info = self._extract_request_info(event)
        logger.info(f"[{request_info['type']}] {request_info['summary']}")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request details: {request_info}")
        
        try:
            # Process the request
            result = await handler(event, data)
            
            # Log successful completion
            duration = time.time() - start_time
            logger.info(
                f"[{request_info['type']}] Completed in {duration:.3f}s - {request_info['user']}"
            )
            
            return result
        
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"[{request_info['type']}] Failed in {duration:.3f}s - {request_info['user']}: {e}"
            )
            raise
    
    def _extract_request_info(self, event: TelegramObject) -> Dict[str, Any]:
        """Extract useful information from the event for logging."""
        info = {
            'type': type(event).__name__,
            'timestamp': time.time(),
            'user': 'Unknown',
            'chat': 'Unknown',
            'summary': 'Unknown event'
        }
        
        if isinstance(event, Message):
            info.update({
                'user': self._format_user(event.from_user),
                'chat': self._format_chat(event.chat),
                'summary': self._format_message_summary(event)
            })
        
        elif isinstance(event, CallbackQuery):
            info.update({
                'user': self._format_user(event.from_user),
                'chat': self._format_chat(event.message.chat) if event.message else 'Inline',
                'summary': f"Callback: {event.data}"
            })
        
        elif isinstance(event, InlineQuery):
            info.update({
                'user': self._format_user(event.from_user),
                'chat': 'Inline Query',
                'summary': f"Inline query: {event.query}"
            })
        
        return info
    
    def _format_user(self, user) -> str:
        """Format user information for logging."""
        if not user:
            return "Unknown"
        
        username = f"@{user.username}" if user.username else "no_username"
        return f"{user.id} ({user.first_name} {user.last_name or ''} {username})".strip()
    
    def _format_chat(self, chat) -> str:
        """Format chat information for logging."""
        if not chat:
            return "Unknown"
        
        chat_type = chat.type
        if chat_type == "private":
            return "Private"
        else:
            title = getattr(chat, 'title', 'Unknown')
            return f"{chat_type.title()}: {title} ({chat.id})"
    
    def _format_message_summary(self, message: Message) -> str:
        """Create a summary of the message for logging."""
        if message.text:
            text = message.text[:100]
            if len(message.text) > 100:
                text += "..."
            return f"Text: {text}"
        
        if message.photo:
            return "Photo message"
        
        if message.document:
            return f"Document: {message.document.file_name}"
        
        if message.voice:
            return "Voice message"
        
        if message.video:
            return "Video message"
        
        if message.sticker:
            return f"Sticker: {message.sticker.emoji}"
        
        if message.location:
            return "Location message"
        
        if message.contact:
            return "Contact message"
        
        # Check for other message types
        content_types = []
        for attr in ['audio', 'animation', 'video_note', 'poll', 'venue']:
            if getattr(message, attr, None):
                content_types.append(attr)
        
        if content_types:
            return f"Message with: {', '.join(content_types)}"
        
        return "Unknown message type"
