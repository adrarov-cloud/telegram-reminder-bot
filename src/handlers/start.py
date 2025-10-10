"""
Start Handlers Module

Command handlers for /start, /help, and basic bot commands.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext

from src.database.operations import get_session, UserOperations
from src.utils.keyboards import main_menu_keyboard, help_keyboard, back_to_menu_keyboard
from src.utils.formatters import format_help_message

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    await state.clear()  # Clear any existing state
    
    user = message.from_user
    user_name = user.first_name or "друг"
    
    try:
        async with get_session() as session:
            # Create or update user
            db_user = await UserOperations.create_or_update_user(
                session=session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code
            )
            
            logger.info(f"👤 User {user.id} started bot (DB ID: {db_user.id})")
        
        welcome_message = (
            f"👋 **Добро пожаловать, {user_name}!**\n\n"
            "🤖 Я умный бот-напоминалка! Помогу тебе никогда не забывать важные дела.\n\n"
            "🎯 **Что я умею:**\n"
            "• 📝 Создавать напоминания с умным парсингом времени\n"
            "• ⏰ Отправлять уведомления точно в срок\n"
            "• 📋 Управлять списком всех напоминаний\n"
            "• 📊 Показывать статистику использования\n"
            "• 🌍 Работать в любом часовом поясе\n\n"
            "🚀 **Быстрый старт:**\n"
            "Просто напиши `Напомни купить хлеб через час` или используй кнопки ниже!\n\n"
            "💡 Я понимаю естественный язык и работаю 24/7!"
        )
        
        await message.answer(
            welcome_message,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in /start handler: {e}")
        await message.answer(
            "❌ **Ошибка запуска**\n\nПопробуйте еще раз или обратитесь в поддержку.",
            parse_mode="Markdown"
        )


@router.message(Command(commands=["help"]))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = format_help_message("main")
    
    await message.answer(
        help_text,
        reply_markup=help_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "help")
async def show_help_menu(callback: CallbackQuery):
    """Show help menu."""
    await callback.answer()
    
    help_text = format_help_message("main")
    
    await callback.message.edit_text(
        help_text,
        reply_markup=help_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("help_"))
async def show_help_section(callback: CallbackQuery):
    """Show specific help section."""
    await callback.answer()
    
    section = callback.data.replace("help_", "")
    help_text = format_help_message(section)
    
    await callback.message.edit_text(
        help_text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu."""
    await callback.answer()
    await state.clear()  # Clear any FSM state
    
    user_name = callback.from_user.first_name or "друг"
    
    message_text = (
        f"🏠 **Главное меню**\n\n"
        f"Привет, **{user_name}**! Что будем делать?\n\n"
        "💡 Выбери действие из меню ниже или просто напиши мне что нужно не забыть!"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command(commands=["stats"]))
async def cmd_stats(message: Message):
    """Handle /stats command."""
    try:
        async with get_session() as session:
            from src.database.operations import StatisticsOperations
            
            # Get user
            user = await UserOperations.get_user_by_telegram_id(
                session, message.from_user.id
            )
            
            if not user:
                await message.answer(
                    "❌ **Пользователь не найден**\n\nИспользуйте /start для регистрации",
                    parse_mode="Markdown"
                )
                return
            
            # Get statistics
            stats = await StatisticsOperations.get_user_statistics(session, user.id)
            
            if not stats:
                await message.answer(
                    "📊 **Статистика пуста**\n\nСоздайте первое напоминание чтобы увидеть статистику!",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            from src.utils.formatters import format_user_statistics
            stats_text = format_user_statistics(stats)
            
            await message.answer(
                stats_text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"❌ Error in /stats handler: {e}")
        await message.answer(
            "❌ **Ошибка получения статистики**\n\nПопробуйте позже",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "show_stats")
async def show_stats_callback(callback: CallbackQuery):
    """Show statistics via callback."""
    await callback.answer()
    
    try:
        async with get_session() as session:
            from src.database.operations import StatisticsOperations
            
            # Get user
            user = await UserOperations.get_user_by_telegram_id(
                session, callback.from_user.id
            )
            
            if not user:
                await callback.message.edit_text(
                    "❌ **Пользователь не найден**\n\nИспользуйте /start для регистрации",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            # Get statistics
            stats = await StatisticsOperations.get_user_statistics(session, user.id)
            
            if not stats:
                await callback.message.edit_text(
                    "📊 **Статистика пуста**\n\nСоздайте первое напоминание чтобы увидеть статистику!",
                    reply_markup=main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            from src.utils.formatters import format_user_statistics
            stats_text = format_user_statistics(stats)
            
            await callback.message.edit_text(
                stats_text,
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"❌ Error showing stats: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка получения статистики**\n\nПопробуйте позже",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )


@router.message(Command(commands=["settings"]))
async def cmd_settings(message: Message):
    """Handle /settings command."""
    from src.utils.keyboards import settings_keyboard
    
    settings_text = (
        "⚙️ **Настройки**\n\n"
        "Здесь вы можете настроить бота под себя:\n\n"
        "🌍 **Часовой пояс** - для точного времени уведомлений\n"
        "🔔 **Уведомления** - включить/отключить\n"
        "🗑 **Удаление данных** - полная очистка профиля\n\n"
        "Выберите что хотите настроить:"
    )
    
    await message.answer(
        settings_text,
        reply_markup=settings_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings")
async def show_settings_callback(callback: CallbackQuery):
    """Show settings via callback."""
    await callback.answer()
    
    from src.utils.keyboards import settings_keyboard
    
    settings_text = (
        "⚙️ **Настройки**\n\n"
        "Здесь вы можете настроить бота под себя:\n\n"
        "🌍 **Часовой пояс** - для точного времени уведомлений\n"
        "🔔 **Уведомления** - включить/отключить\n"
        "🗑 **Удаление данных** - полная очистка профиля\n\n"
        "Выберите что хотите настроить:"
    )
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=settings_keyboard(),
        parse_mode="Markdown"
    )


# Handle unknown commands
@router.message(Command(commands=["unknown"]))
async def unknown_command(message: Message):
    """Handle unknown commands."""
    await message.answer(
        "🤷‍♂️ **Неизвестная команда**\n\n"
        "Используйте /help для просмотра доступных команд или /start для главного меню.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


# Handle text messages (quick reminders)
@router.message(F.text)
async def handle_text_message(message: Message, state: FSMContext):
    """Handle plain text messages as potential quick reminders."""
    # Check if we're in any FSM state
    current_state = await state.get_state()
    if current_state:
        # Let other handlers process FSM states
        return
    
    text = message.text.strip()
    
    # Check for quick reminder patterns
    quick_patterns = [
        'напомни', 'напоминание', 'reminder', 'remind',
        'не забыть', 'через', 'завтра', 'сегодня'
    ]
    
    if any(pattern in text.lower() for pattern in quick_patterns):
        # This looks like a quick reminder attempt
        from src.bot.states import ReminderStates
        
        await state.set_state(ReminderStates.quick_reminder)
        await state.update_data(original_message=text)
        
        # Process as quick reminder
        from src.handlers.reminders import process_quick_reminder
        await process_quick_reminder(message, state)
    else:
        # Generic help message
        await message.answer(
            "👋 **Привет!**\n\n"
            "Я бот для напоминаний. Чтобы создать напоминание, используйте кнопки меню или напишите что-то вроде:\n\n"
            "• `Напомни купить хлеб через час`\n"
            "• `Встреча завтра в 15:30`\n"
            "• `Не забыть позвонить маме`\n\n"
            "Или выберите действие из меню:",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
