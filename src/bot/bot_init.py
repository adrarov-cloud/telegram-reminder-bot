"""
Bot Initialization Module

Bot instance creation, configuration, and middleware setup.
"""

import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import config

logger = logging.getLogger(__name__)


def create_bot(token: str) -> Bot:
    """
    Create and configure bot instance.
    
    Args:
        token: Telegram Bot API token
        
    Returns:
        Configured Bot instance
    """
    try:
        # Bot default properties
        default_properties = DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN,
            protect_content=False,
            allow_sending_without_reply=True
        )
        
        # Create bot instance
        bot = Bot(
            token=token,
            default=default_properties
        )
        
        logger.info("✅ Bot instance created successfully")
        return bot
        
    except Exception as e:
        logger.error(f"❌ Failed to create bot: {e}")
        raise


async def setup_bot_commands(bot: Bot) -> None:
    """Setup bot commands menu."""
    from aiogram.types import BotCommand
    
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Показать справку"),
        BotCommand(command="cancel", description="❌ Отменить текущую операцию"),
        BotCommand(command="stats", description="📊 Показать статистику"),
        BotCommand(command="settings", description="⚙️ Настройки бота"),
    ]
    
    try:
        await bot.set_my_commands(commands)
        logger.info("✅ Bot commands configured")
    except Exception as e:
        logger.error(f"❌ Failed to set bot commands: {e}")


async def get_bot_info(bot: Bot) -> dict:
    """Get bot information."""
    try:
        bot_info = await bot.get_me()
        
        return {
            "id": bot_info.id,
            "username": bot_info.username,
            "first_name": bot_info.first_name,
            "can_join_groups": bot_info.can_join_groups,
            "can_read_all_group_messages": bot_info.can_read_all_group_messages,
            "supports_inline_queries": bot_info.supports_inline_queries
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get bot info: {e}")
        return {}


async def validate_bot_token(bot: Bot) -> bool:
    """Validate bot token by making a test request."""
    try:
        await bot.get_me()
        logger.info("✅ Bot token is valid")
        return True
    except Exception as e:
        logger.error(f"❌ Invalid bot token: {e}")
        return False