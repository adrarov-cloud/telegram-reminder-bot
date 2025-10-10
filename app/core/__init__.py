"""
Core Package

Core components for the Telegram bot:
- Bot factory and configuration
- Dispatcher setup with middleware
- Event handling and routing
- Application lifecycle management
"""

from .bot import create_bot, get_bot_info, validate_bot_token
from .dispatcher import create_dispatcher, setup_dispatcher_logging

__all__ = [
    'create_bot',
    'get_bot_info',
    'validate_bot_token',
    'create_dispatcher',
    'setup_dispatcher_logging'
]