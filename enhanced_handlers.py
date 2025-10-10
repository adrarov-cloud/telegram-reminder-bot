"""
Enhanced Reminder Handlers

Comprehensive handlers with confirmation flows, editing capabilities,
smart suggestions, and error recovery.
"""

import logging
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from src.database.operations import get_session, ReminderOperations, UserOperations
from src.services.time_parser import time_parser, TimeParseError
from src.services.scheduler_service import scheduler_service
from src.bot.states import ReminderStates
from src.utils.formatters import format_reminder_preview, format_reminder_list, format_datetime
from src.utils.keyboards import (
    main_menu_keyboard, confirmation_keyboard, time_suggestions_keyboard,
    reminder_actions_keyboard, cancel_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "create_reminder")
async def start_create_reminder(callback: CallbackQuery, state: FSMContext):
    """Start reminder creation process."""
    await callback.answer()
    
    # Clear any existing state
    await state.clear()
    
    # Show creation options
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Быстро", callback_data="quick_create")],
        [InlineKeyboardButton(text="📋 Пошагово", callback_data="step_by_step")],
        [InlineKeyboardButton(text="🎤 Голосом (скоро)", callback_data="voice_create")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ])
    
    await callback.message.edit_text(
        "📝 **Как создать напоминание?**\n\n"
        "⚡ **Быстро** - одним сообщением\n"
        "📋 **Пошагово** - текст, затем время\n"
        "🎤 **Голосом** - голосовое сообщение\n\n"
        "Выберите удобный способ:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "step_by_step")
async def start_step_by_step_creation(callback: CallbackQuery, state: FSMContext):
    """Start step-by-step reminder creation."""
    await callback.answer()
    
    await callback.message.edit_text(
        "📝 **Создание напоминания (1/3)**\n\n"
        "Введите **текст напоминания**:\n\n"
        "*Примеры:*\n"
        "• Купить молоко\n"
        "• Встреча с врачом\n"
        "• Позвонить маме\n\n"
        "💡 Пишите кратко и понятно",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.waiting_for_text)


@router.callback_query(F.data == "quick_create")
async def start_quick_creation(callback: CallbackQuery, state: FSMContext):
    """Start quick reminder creation."""
    await callback.answer()
    
    await callback.message.edit_text(
        "⚡ **Быстрое создание**\n\n"
        "Напишите напоминание и время **одним сообщением**:\n\n"
        "*Примеры:*\n"
        "• `Купить хлеб через 2 часа`\n"
        "• `Встреча завтра в 15:30`\n"
        "• `Позвонить маме в воскресенье в 10:00`\n\n"
        "💡 Бот сам разберёт текст и время",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.quick_reminder)


@router.message(ReminderStates.waiting_for_text)
async def process_reminder_text(message: Message, state: FSMContext):
    """Process reminder text and ask for time."""
    reminder_text = message.text.strip()
    
    # Validate text length
    if len(reminder_text) < 3:
        await message.answer(
            "⚠️ **Слишком короткий текст**\n\n"
            "Введите более подробное описание (минимум 3 символа):",
            parse_mode="Markdown"
        )
        return
    
    if len(reminder_text) > 255:
        await message.answer(
            "⚠️ **Слишком длинный текст**\n\n"
            "Сократите до 255 символов. Подробности можно добавить в описание.",
            parse_mode="Markdown"
        )
        return
    
    # Save reminder text to state
    await state.update_data(reminder_text=reminder_text)
    
    # Get smart time suggestions
    suggestions = time_parser.get_suggestions(reminder_text)
    
    await message.answer(
        f"⏰ **Создание напоминания (2/3)**\n\n"
        f"**Текст:** {reminder_text} ✅\n\n"
        f"Когда напомнить?\n\n"
        f"💡 **Умные предложения:**",
        reply_markup=time_suggestions_keyboard(suggestions),
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.waiting_for_time)


@router.callback_query(F.data.startswith("time_suggestion_"))
async def process_time_suggestion(callback: CallbackQuery, state: FSMContext):
    """Process selected time suggestion."""
    await callback.answer()
    
    time_text = callback.data.replace("time_suggestion_", "")
    await process_time_input(callback.message, state, time_text, from_callback=True)


@router.message(ReminderStates.waiting_for_time)
async def process_time_input(message: Message, state: FSMContext, time_text: Optional[str] = None, from_callback: bool = False):
    """Process time input and show confirmation."""
    input_text = time_text or message.text.strip()
    
    try:
        # Parse time
        scheduled_time = time_parser.parse(input_text)
        
        # Validate time
        is_valid, error_message = time_parser.validate_time(scheduled_time)
        if not is_valid:
            error_text = f"❌ **Ошибка времени**\n\n{error_message}\n\nПопробуйте еще раз:"
            
            if from_callback:
                await message.edit_text(error_text, parse_mode="Markdown")
            else:
                await message.answer(error_text, parse_mode="Markdown")
            return
        
        # Get state data
        data = await state.get_data()
        reminder_text = data.get('reminder_text')
        
        # Save time to state
        await state.update_data(
            scheduled_time=scheduled_time,
            scheduled_time_text=input_text
        )
        
        # Show confirmation
        preview_text = format_reminder_preview(
            text=reminder_text,
            scheduled_time=scheduled_time,
            original_input=input_text
        )
        
        keyboard = confirmation_keyboard(
            confirm_data="confirm_create_reminder",
            edit_text_data="edit_reminder_text", 
            edit_time_data="edit_reminder_time",
            cancel_data="cancel_operation"
        )
        
        confirmation_message = (
            f"✅ **Подтверждение напоминания (3/3)**\n\n"
            f"{preview_text}\n\n"
            f"**Всё верно?**"
        )
        
        if from_callback:
            await message.edit_text(
                confirmation_message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                confirmation_message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        
        await state.set_state(ReminderStates.confirming_reminder)
        
    except TimeParseError as e:
        error_suggestions = [
            "через 30 минут",
            "завтра в 10:00", 
            "в понедельник в 9:00"
        ]
        
        error_message = (
            f"❌ **Не понял формат времени**\n\n"
            f"Ваш ввод: `{input_text}`\n"
            f"Ошибка: {str(e)}\n\n"
            f"**Попробуйте:**"
        )
        
        keyboard = time_suggestions_keyboard(error_suggestions)
        
        if from_callback:
            await message.edit_text(error_message, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(error_message, reply_markup=keyboard, parse_mode="Markdown")


@router.message(ReminderStates.quick_reminder)
async def process_quick_reminder(message: Message, state: FSMContext):
    """Process quick reminder creation."""
    text = message.text.strip()
    
    try:
        # Try to parse the entire message
        # First, try to extract time patterns
        parsed_time = None
        reminder_text = text
        
        # Simple heuristic: try common time patterns at the end
        time_patterns = [
            r'через\s+\d+\s+(минут|час|день|неделя)',
            r'завтра\s+в\s+\d{1,2}:\d{2}',
            r'в\s+\d{1,2}:\d{2}',
            r'сегодня\s+в\s+\d{1,2}:\d{2}',
        ]
        
        import re
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_part = match.group(0)
                text_part = text.replace(time_part, '').strip()
                
                if text_part:  # Make sure there's text left
                    try:
                        parsed_time = time_parser.parse(time_part)
                        reminder_text = text_part
                        break
                    except TimeParseError:
                        continue
        
        if not parsed_time:
            # Fallback: try to parse the whole thing
            parsed_time = time_parser.parse(text)
            reminder_text = "Напоминание"  # Generic text
        
        # Validate
        is_valid, error_message = time_parser.validate_time(parsed_time)
        if not is_valid:
            await message.answer(
                f"❌ **Ошибка времени**\n\n{error_message}\n\n"
                f"Попробуйте еще раз или используйте пошаговое создание.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Пошаговое создание", callback_data="step_by_step")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
                ]),
                parse_mode="Markdown"
            )
            return
        
        # Save to state and show confirmation
        await state.update_data(
            reminder_text=reminder_text,
            scheduled_time=parsed_time,
            scheduled_time_text=text
        )
        
        preview_text = format_reminder_preview(
            text=reminder_text,
            scheduled_time=parsed_time,
            original_input=text
        )
        
        keyboard = confirmation_keyboard(
            confirm_data="confirm_create_reminder",
            edit_text_data="edit_reminder_text",
            edit_time_data="edit_reminder_time", 
            cancel_data="cancel_operation"
        )
        
        await message.answer(
            f"⚡ **Быстрое создание - подтверждение**\n\n"
            f"{preview_text}\n\n"
            f"**Всё верно?**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(ReminderStates.confirming_reminder)
        
    except TimeParseError as e:
        await message.answer(
            f"❌ **Не удалось разобрать сообщение**\n\n"
            f"Ваш текст: `{text}`\n\n"
            f"**Попробуйте:**\n"
            f"• Более четко разделить текст и время\n"
            f"• Использовать пошаговое создание\n\n"
            f"**Примеры:**\n"
            f"• `Купить хлеб через 2 часа`\n"
            f"• `Встреча завтра в 15:30`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Пошаговое создание", callback_data="step_by_step")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
            ]),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "confirm_create_reminder")
async def confirm_create_reminder(callback: CallbackQuery, state: FSMContext):
    """Confirm and create reminder."""
    await callback.answer()
    
    data = await state.get_data()
    reminder_text = data.get('reminder_text')
    scheduled_time = data.get('scheduled_time')
    
    if not reminder_text or not scheduled_time:
        await callback.message.edit_text(
            "❌ **Ошибка создания**\n\nПопробуйте еще раз.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return
    
    try:
        async with get_session() as session:
            # Get user
            user = await UserOperations.get_user_by_telegram_id(
                session, callback.from_user.id
            )
            if not user:
                await callback.message.edit_text(
                    "❌ **Пользователь не найден**\n\nПопробуйте /start",
                    reply_markup=main_menu_keyboard()
                )
                await state.clear()
                return
            
            # Create reminder
            reminder = await ReminderOperations.create_reminder(
                session=session,
                user_id=user.id,
                title=reminder_text,
                description=None,
                scheduled_time=scheduled_time,
                original_text=data.get('scheduled_time_text', '')
            )
            
            # Schedule reminder
            await scheduler_service.schedule_reminder(reminder.id, scheduled_time)
            
            # Success message
            await callback.message.edit_text(
                f"✅ **Напоминание создано!**\n\n"
                f"📝 **Текст:** {reminder_text}\n"
                f"⏰ **Время:** {format_datetime(scheduled_time)}\n"
                f"🆔 **ID:** #{reminder.id}\n\n"
                f"🔔 Я напомню вам точно в срок!",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
            logger.info(f"Created reminder {reminder.id} for user {user.telegram_id}")
            
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка создания напоминания**\n\n"
            "Попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    await state.clear()


@router.callback_query(F.data == "edit_reminder_text")
async def edit_reminder_text(callback: CallbackQuery, state: FSMContext):
    """Edit reminder text."""
    await callback.answer()
    
    await callback.message.edit_text(
        "✏️ **Редактирование текста**\n\n"
        "Введите новый текст напоминания:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.editing_text)


@router.callback_query(F.data == "edit_reminder_time")
async def edit_reminder_time(callback: CallbackQuery, state: FSMContext):
    """Edit reminder time."""
    await callback.answer()
    
    data = await state.get_data()
    reminder_text = data.get('reminder_text', 'напоминание')
    suggestions = time_parser.get_suggestions(reminder_text)
    
    await callback.message.edit_text(
        "🕐 **Редактирование времени**\n\n"
        "Введите новое время напоминания:\n\n"
        "💡 **Предложения:**",
        reply_markup=time_suggestions_keyboard(suggestions),
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.editing_time)


@router.message(ReminderStates.editing_text)
async def process_edit_text(message: Message, state: FSMContext):
    """Process edited reminder text."""
    new_text = message.text.strip()
    
    if len(new_text) < 3:
        await message.answer(
            "⚠️ **Слишком короткий текст**\n\n"
            "Введите более подробное описание (минимум 3 символа):",
            parse_mode="Markdown"
        )
        return
    
    # Update state
    await state.update_data(reminder_text=new_text)
    
    # Get current data and show confirmation
    data = await state.get_data()
    scheduled_time = data.get('scheduled_time')
    
    preview_text = format_reminder_preview(
        text=new_text,
        scheduled_time=scheduled_time,
        original_input=data.get('scheduled_time_text', '')
    )
    
    keyboard = confirmation_keyboard(
        confirm_data="confirm_create_reminder",
        edit_text_data="edit_reminder_text",
        edit_time_data="edit_reminder_time",
        cancel_data="cancel_operation"
    )
    
    await message.answer(
        f"✏️ **Текст обновлён**\n\n"
        f"{preview_text}\n\n"
        f"**Подтверждаете изменения?**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await state.set_state(ReminderStates.confirming_reminder)


@router.message(ReminderStates.editing_time)
async def process_edit_time(message: Message, state: FSMContext):
    """Process edited reminder time."""
    await process_time_input(message, state, message.text)


@router.callback_query(F.data == "cancel_operation")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Cancel current operation."""
    await callback.answer()
    
    await callback.message.edit_text(
        "❌ **Операция отменена**\n\n"
        "Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.clear()


# Cancel command
@router.message(Command("cancel"))
@router.message(F.text.in_(["отмена", "отменить", "cancel", "❌"]))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current operation via command."""
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.answer(
            "❌ **Операция отменена**",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🤷‍♂️ **Нечего отменять**\n\n"
            "Вы в главном меню.",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )