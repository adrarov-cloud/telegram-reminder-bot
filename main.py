"""
Telegram Reminder Bot - Main Entry Point

Production-ready Telegram bot with modular architecture,
comprehensive error handling, and advanced scheduling features.

Author: AI Development Team
Version: 2.0.0
License: MIT
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.bot_init import create_bot
from src.config import config
from src.database.operations import init_database
from src.handlers.start import router as start_router
from src.handlers.reminders import router as reminders_router
from src.services.scheduler_service import SchedulerService
from src.utils.logging import setup_logging


class TelegramReminderBot:
    """Main bot application class."""

    def __init__(self):
        """Initialize the bot application."""
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.scheduler: SchedulerService | None = None
        self._shutdown_event = asyncio.Event()

    async def startup(self) -> None:
        """Initialize and start all bot components."""
        try:
            # Setup logging
            setup_logging(config.LOG_LEVEL, config.LOG_FILE)
            logger = logging.getLogger(__name__)
            logger.info("🚀 Starting Telegram Reminder Bot v2.0.0")

            # Validate configuration
            if not config.BOT_TOKEN:
                raise ValueError("BOT_TOKEN is not set in environment variables")

            # Initialize database
            logger.info("📦 Initializing database...")
            await init_database()

            # Create bot and dispatcher
            logger.info("🤖 Creating bot instance...")
            self.bot = create_bot(config.BOT_TOKEN)
            storage = MemoryStorage()
            self.dp = Dispatcher(storage=storage)

            # Register handlers
            logger.info("📝 Registering handlers...")
            self.dp.include_router(start_router)
            self.dp.include_router(reminders_router)

            # Initialize scheduler
            logger.info("⏰ Starting scheduler service...")
            self.scheduler = SchedulerService(self.bot)
            await self.scheduler.start()

            # Load pending reminders
            logger.info("📥 Loading pending reminders...")
            await self.scheduler.load_pending_reminders()

            logger.info("✅ Bot initialization completed successfully")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"💥 Failed to initialize bot: {e}")
            raise

    async def shutdown(self) -> None:
        """Gracefully shutdown all bot components."""
        logger = logging.getLogger(__name__)
        logger.info("🛑 Shutting down Telegram Reminder Bot...")

        try:
            # Stop scheduler
            if self.scheduler:
                logger.info("⏰ Stopping scheduler...")
                await self.scheduler.stop()

            # Close bot session
            if self.bot:
                logger.info("🤖 Closing bot session...")
                await self.bot.session.close()

            # Close database connections
            # Note: SQLite connections are closed automatically
            logger.info("✅ Shutdown completed successfully")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum: int, frame: Any) -> None:
            logger = logging.getLogger(__name__)
            logger.info(f"📡 Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self) -> None:
        """Run the bot with polling."""
        logger = logging.getLogger(__name__)
        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            # Initialize components
            await self.startup()

            # Start polling
            logger.info("🔄 Starting polling...")
            polling_task = asyncio.create_task(
                self.dp.start_polling(
                    self.bot,
                    skip_updates=True,
                    allowed_updates=self.dp.resolve_used_update_types()
                )
            )

            # Wait for shutdown signal
            await self._shutdown_event.wait()

            # Cancel polling
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                logger.info("📴 Polling stopped")

        except Exception as e:
            logger.error(f"💥 Critical error in main loop: {e}")
            raise
        finally:
            await self.shutdown()


async def main() -> None:
    """Main entry point."""
    app = TelegramReminderBot()
    try:
        await app.run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("👋 Bot stopped by user")
    except Exception as e:
        logging.getLogger(__name__).error(f"💥 Unhandled error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Ensure we're running from the project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Run the bot
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Failed to start bot: {e}")
        sys.exit(1)