"""
Handlers Package

Collection of message handlers for the Telegram bot:
- Basic commands (start, help, settings)
- Reminder management (create, list, edit, delete)
- Template management
- User preferences and timezone settings
- Interactive flows with FSM
"""

from aiogram import Dispatcher
from .basic import register_basic_handlers
from .reminders import register_reminder_handlers
from .templates import register_template_handlers
from .settings import register_settings_handlers


def register_all_handlers(dp: Dispatcher) -> None:
    """
    Register all handlers with the dispatcher.
    
    Args:
        dp: Aiogram dispatcher instance
    """
    register_basic_handlers(dp)
    register_reminder_handlers(dp)
    register_template_handlers(dp)
    register_settings_handlers(dp)


__all__ = ['register_all_handlers']