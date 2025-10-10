"""
Basic Handlers

Handles fundamental bot commands and interactions:
- /start command with user registration
- /help command with comprehensive help
- /cancel command for FSM reset
- Basic error handling
- Status and info commands
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.database.models import User
from app.utils.keyboards import get_main_menu_keyboard


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, user: User):
    """
    Handle /start command.
    
    Welcome new users and show main menu to existing users.
    """
    if user:
        # Existing user
        await message.answer(
            f"Welcome back, {user.first_name}! 😊\n\n"
            f"I'm your personal reminder assistant. "
            f"I'll help you never forget important tasks and events.\n\n"
            f"What would you like to do?",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # New user (shouldn't happen due to middleware, but just in case)
        await message.answer(
            f"Hello {message.from_user.first_name}! 👋\n\n"
            f"Welcome to your **Personal Reminder Bot**! 🗺️\n\n"
            f"🎆 **What I can do:**\n"
            f"• Create one-time and recurring reminders\n"
            f"• Support multiple time zones\n"
            f"• Save reminder templates for quick reuse\n"
            f"• Send timely notifications\n"
            f"• Manage your reminder preferences\n\n"
            f"Let's get started! 🚀",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    logger.info(f"User {message.from_user.id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command.
    
    Provide comprehensive help information.
    """
    help_text = (
        "📚 **Help - Personal Reminder Bot**\n\n"
        
        "📝 **Basic Commands:**\n"
        "• `/start` - Start the bot and show main menu\n"
        "• `/help` - Show this help message\n"
        "• `/cancel` - Cancel current operation\n"
        "• `/status` - Show your account status\n\n"
        
        "⏰ **Reminder Management:**\n"
        "• Create reminders with custom titles and descriptions\n"
        "• Set specific dates and times\n"
        "• Configure recurring reminders (daily, weekly, monthly, yearly)\n"
        "• Edit and delete existing reminders\n"
        "• View all your active reminders\n\n"
        
        "📋 **Templates:**\n"
        "• Create reusable reminder templates\n"
        "• Quickly create reminders from templates\n"
        "• Manage your template library\n\n"
        
        "⚙️ **Settings:**\n"
        "• Set your timezone for accurate reminders\n"
        "• Configure notification preferences\n"
        "• Manage account settings\n\n"
        
        "🕰️ **Time Formats:**\n"
        "• `2025-01-15 14:30` - Date and time\n"
        "• `tomorrow 9am` - Natural language\n"
        "• `next friday 2pm` - Relative dates\n"
        "• `in 2 hours` - Relative time\n\n"
        
        "🔄 **Repeat Options:**\n"
        "• Daily, Weekly, Monthly, Yearly\n"
        "• Custom intervals (every 2 days, every 3 weeks, etc.)\n"
        "• Set end dates for recurring reminders\n\n"
        
        "🌍 **Timezone Support:**\n"
        "• Full timezone support worldwide\n"
        "• Automatic daylight saving time handling\n"
        "• Set your preferred timezone in settings\n\n"
        
        "📞 **Need Help?**\n"
        "• Use the menu buttons for easy navigation\n"
        "• Type `/cancel` anytime to start over\n"
        "• All operations are confirmed before execution\n\n"
        
        "**Ready to organize your life?** Click a button below! 💪"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Handle /cancel command.
    
    Cancel current FSM state and return to main menu.
    """
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Operation cancelled. Returning to main menu.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "Nothing to cancel. Here's the main menu:",
            reply_markup=get_main_menu_keyboard()
        )


@router.message(Command("status"))
async def cmd_status(message: Message, user: User):
    """
    Handle /status command.
    
    Show user account status and statistics.
    """
    if not user:
        await message.answer("User not found. Please start the bot with /start")
        return
    
    # Calculate statistics
    total_reminders = len(user.reminders) if user.reminders else 0
    active_reminders = len([r for r in user.reminders if not r.is_deleted and r.status == 'pending']) if user.reminders else 0
    total_templates = len(user.templates) if user.templates else 0
    
    status_text = (
        f"📊 **Account Status**\n\n"
        f"👤 **User:** {user.first_name} {user.last_name or ''}\n"
        f"🌍 **Timezone:** {user.timezone}\n"
        f"🔔 **Notifications:** {'Enabled' if user.notifications_enabled else 'Disabled'}\n"
        f"⭐ **Premium:** {'Yes' if user.is_premium else 'No'}\n\n"
        
        f"📊 **Statistics:**\n"
        f"• Total reminders: {total_reminders}\n"
        f"• Active reminders: {active_reminders}\n"
        f"• Templates: {total_templates}\n"
        f"• Member since: {user.created_at.strftime('%Y-%m-%d')}\n"
        f"• Last activity: {user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'Never'}\n\n"
        
        f"Use the buttons below to manage your reminders! 🚀"
    )
    
    await message.answer(
        status_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "🏠 Main Menu")
async def show_main_menu(message: Message, state: FSMContext):
    """
    Show main menu and clear any active state.
    """
    await state.clear()
    await message.answer(
        "What would you like to do?",
        reply_markup=get_main_menu_keyboard()
    )


@router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """
    Handle unknown messages when not in any specific state.
    """
    current_state = await state.get_state()
    
    if not current_state:
        await message.answer(
            "I didn't understand that command. 🤔\n\n"
            "Try using the menu buttons below or type /help for assistance.",
            reply_markup=get_main_menu_keyboard()
        )


def register_basic_handlers(dp):
    """Register basic handlers with the dispatcher."""
    dp.include_router(router)
