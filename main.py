#!/usr/bin/env python3
"""
Telegram Reminder Bot - Main Entry Point

A professional reminder bot built with aiogram 3.x, featuring:
- Asynchronous architecture with rate limiting protection
- SQLAlchemy ORM with async support
- APScheduler for reliable reminder delivery
- Comprehensive error handling and logging
- FSM (Finite State Machine) for user interactions
- Production-ready with Docker support

Author: Assistant AI
Created: 2025-10-10
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.bot import create_bot
from app.core.dispatcher import create_dispatcher
from app.database.connection import init_database
from app.scheduler.reminder_scheduler import create_scheduler
from app.config import settings
from app.utils.logger import setup_logging


async def main() -> None:
    """
    Main application entry point.
    
    Initializes all components and starts the bot:
    1. Sets up logging
    2. Initializes database
    3. Creates bot and dispatcher
    4. Sets up scheduler
    5. Starts polling
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Telegram Reminder Bot...")
        
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        logger.info("✅ Database initialized")
        
        # Create bot instance
        logger.info("Creating bot instance...")
        bot = create_bot()
        logger.info("✅ Bot created")
        
        # Create dispatcher with all handlers and middlewares
        logger.info("Setting up dispatcher...")
        dp = create_dispatcher()
        logger.info("✅ Dispatcher created")
        
        # Initialize and start scheduler
        logger.info("Starting scheduler...")
        scheduler = create_scheduler(bot)
        scheduler.start()
        logger.info("✅ Scheduler started")
        
        logger.info("✅ Handlers registered")
        logger.info(f"✅ Bot @{settings.BOT_USERNAME} is ready!")
        logger.info("🔄 Starting with polling...")
        
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message", 
                "callback_query", 
                "inline_query",
                "chosen_inline_result"
            ]
        )
        
    except Exception as e:
        logger.error(f"Critical error during startup: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down...")
        if 'scheduler' in locals():
            scheduler.shutdown()
        if 'bot' in locals():
            await bot.session.close()
        logger.info("✅ Cleanup completed")


if __name__ == "__main__":
    try:
        # For Windows compatibility
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
