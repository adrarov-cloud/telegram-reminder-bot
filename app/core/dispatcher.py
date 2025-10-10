"""
Dispatcher Factory Module

Sets up the Dispatcher with:
- All middlewares (rate limiting, error handling, logging)
- Handler registration
- FSM configuration
- Filters setup
"""

import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.config import settings
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.error_handler import ErrorHandlerMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.user_context import UserContextMiddleware
from app.handlers import register_all_handlers


logger = logging.getLogger(__name__)


def create_storage():
    """
    Create FSM storage based on configuration.
    
    Returns:
        Storage instance (Memory or Redis)
    """
    if settings.REDIS_URL:
        logger.info("Using Redis storage for FSM")
        # Redis storage for production
        return RedisStorage.from_url(settings.REDIS_URL)
    else:
        logger.info("Using Memory storage for FSM")
        # Memory storage for development
        return MemoryStorage()


def create_dispatcher() -> Dispatcher:
    """
    Create and configure Dispatcher with all middlewares and handlers.
    
    Returns:
        Dispatcher: Configured aiogram Dispatcher
    """
    logger.info("Creating dispatcher...")
    
    # Create storage
    storage = create_storage()
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register middlewares in correct order
    logger.info("Registering middlewares...")
    
    # 1. Logging middleware (should be first to log everything)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.inline_query.middleware(LoggingMiddleware())
    
    # 2. Rate limiting middleware
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    
    # 3. User context middleware (loads user data)
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    
    # 4. Error handling middleware (should be last to catch all errors)
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    dp.inline_query.middleware(ErrorHandlerMiddleware())
    
    logger.info("✅ Middlewares registered")
    
    # Register all handlers
    logger.info("Registering handlers...")
    register_all_handlers(dp)
    logger.info("✅ Handlers registered")
    
    # Setup error handler for uncaught exceptions
    @dp.error()
    async def global_error_handler(event, exception):
        """Handle uncaught errors."""
        logger.error(f"Uncaught error: {exception}", exc_info=True)
        return True  # Mark as handled
    
    logger.info("✅ Dispatcher created and configured")
    return dp


def setup_dispatcher_logging(dp: Dispatcher):
    """
    Configure dispatcher-specific logging.
    
    Args:
        dp: Dispatcher instance
    """
    # Set up logging for dispatcher events
    @dp.startup()
    async def on_startup():
        logger.info("🚀 Bot is starting up...")
    
    @dp.shutdown()
    async def on_shutdown():
        logger.info("🛑 Bot is shutting down...")
    
    logger.info("✅ Dispatcher logging configured")
