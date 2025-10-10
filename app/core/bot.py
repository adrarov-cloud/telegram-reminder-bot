"""
Bot Factory Module

Creates and configures the Bot instance with all necessary settings:
- Token validation
- Session configuration
- Error handling setup
- Production optimizations
"""

import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import settings


logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """
    Create and configure Bot instance.
    
    Returns:
        Bot: Configured aiogram Bot instance
    
    Raises:
        ValueError: If bot token is invalid
    """
    logger.info("Creating bot instance...")
    
    # Validate token format
    if not settings.BOT_TOKEN or ':' not in settings.BOT_TOKEN:
        raise ValueError("Invalid bot token format")
    
    # Configure default properties
    default_properties = DefaultBotProperties(
        parse_mode=ParseMode.HTML,  # Use HTML parsing by default
        link_preview_is_disabled=True,  # Disable link previews
        protect_content=False,  # Allow forwarding (can be changed per message)
    )
    
    # Create bot instance
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=default_properties,
        # Session configuration for production
        session=None,  # Will use default aiohttp session
    )
    
    logger.info(f"Bot instance created successfully")
    return bot


async def get_bot_info(bot: Bot) -> dict:
    """
    Get bot information for logging and validation.
    
    Args:
        bot: Bot instance
        
    Returns:
        dict: Bot information
    """
    try:
        me = await bot.get_me()
        return {
            'id': me.id,
            'username': me.username,
            'first_name': me.first_name,
            'is_bot': me.is_bot,
            'can_join_groups': me.can_join_groups,
            'can_read_all_group_messages': me.can_read_all_group_messages,
            'supports_inline_queries': me.supports_inline_queries
        }
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        return {}


async def validate_bot_token(bot: Bot) -> bool:
    """
    Validate bot token by making a test API call.
    
    Args:
        bot: Bot instance
        
    Returns:
        bool: True if token is valid
    """
    try:
        await bot.get_me()
        logger.info("✅ Bot token is valid")
        return True
    except Exception as e:
        logger.error(f"❌ Invalid bot token: {e}")
        return False
