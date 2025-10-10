"""
Keyboards Module

Comprehensive inline keyboards for all bot interactions
with smart layout and responsive design.
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard with primary actions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать напоминание", callback_data="create_reminder")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="my_reminders")],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])


def confirmation_keyboard(
    confirm_data: str,
    edit_text_data: str,
    edit_time_data: str,
    cancel_data: str
) -> InlineKeyboardMarkup:
    """Confirmation keyboard for reminder creation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Создать", callback_data=confirm_data)],
        [
            InlineKeyboardButton(text="✏️ Изменить текст", callback_data=edit_text_data),
            InlineKeyboardButton(text="🕐 Изменить время", callback_data=edit_time_data)
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_data)]
    ])


def time_suggestions_keyboard(suggestions: List[str]) -> InlineKeyboardMarkup:
    """Time suggestions keyboard."""
    keyboard = []
    
    # Add suggestion buttons
    for suggestion in suggestions[:3]:  # Max 3 suggestions
        keyboard.append([
            InlineKeyboardButton(
                text=f"⏰ {suggestion}", 
                callback_data=f"time_suggestion_{suggestion}"
            )
        ])
    
    # Add manual input option
    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_time_input")
    ])
    
    # Add cancel option
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def reminder_actions_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    """Actions keyboard for individual reminders."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_reminder_{reminder_id}"),
            InlineKeyboardButton(text="📅 Перенести", callback_data=f"reschedule_reminder_{reminder_id}")
        ],
        [
            InlineKeyboardButton(text="🔔 Отправить сейчас", callback_data=f"send_now_{reminder_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_reminder_{reminder_id}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_reminders")]
    ])


def reminders_list_keyboard(
    reminders: List[tuple],
    page: int = 1,
    per_page: int = 5
) -> InlineKeyboardMarkup:
    """Paginated reminders list keyboard."""
    keyboard = []
    
    # Add reminder buttons
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    for reminder_id, title, is_sent in reminders[start_idx:end_idx]:
        status_icon = "✅" if is_sent else "⏳"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"reminder_details_{reminder_id}"
            )
        ])
    
    # Add pagination if needed
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"reminders_page_{page-1}")
        )
    
    if end_idx < len(reminders):
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ Вперед", callback_data=f"reminders_page_{page+1}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Add control buttons
    keyboard.extend([
        [
            InlineKeyboardButton(text="🗑 Очистить все", callback_data="clear_all_reminders"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="reminders_stats")
        ],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Back to main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])


def creation_method_keyboard() -> InlineKeyboardMarkup:
    """Reminder creation method selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Быстро", callback_data="quick_create")],
        [InlineKeyboardButton(text="📋 Пошагово", callback_data="step_by_step")],
        [InlineKeyboardButton(text="🎤 Голосом (скоро)", callback_data="voice_create")],
        [InlineKeyboardButton(text="📝 По шаблону", callback_data="from_template")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ])


def category_keyboard() -> InlineKeyboardMarkup:
    """Category selection keyboard."""
    categories = [
        ("💼", "Работа", "work"),
        ("🏥", "Здоровье", "health"),
        ("🛒", "Покупки", "shopping"),
        ("👨‍👩‍👧‍👦", "Семья", "family"),
        ("🎯", "Личное", "personal"),
        ("📚", "Учеба", "education"),
        ("🏠", "Дом", "home"),
        ("🚗", "Транспорт", "transport")
    ]
    
    keyboard = []
    
    # Add categories in pairs
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                icon, name, data = categories[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{icon} {name}",
                    callback_data=f"category_{data}"
                ))
        keyboard.append(row)
    
    # Add skip option
    keyboard.append([
        InlineKeyboardButton(text="⏭ Без категории", callback_data="category_none")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def priority_keyboard() -> InlineKeyboardMarkup:
    """Priority selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔴 Высокий", callback_data="priority_high"),
            InlineKeyboardButton(text="🟡 Обычный", callback_data="priority_normal"),
            InlineKeyboardButton(text="🟢 Низкий", callback_data="priority_low")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ])


def settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings_timezone")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
        [InlineKeyboardButton(text="🗑 Удалить все данные", callback_data="settings_delete_data")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard for deletion."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_operation")]
    ])


def help_keyboard() -> InlineKeyboardMarkup:
    """Help menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создание напоминаний", callback_data="help_creating")],
        [InlineKeyboardButton(text="⏰ Форматы времени", callback_data="help_time_formats")],
        [InlineKeyboardButton(text="📋 Управление списком", callback_data="help_managing")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="help_settings")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])


def stats_keyboard() -> InlineKeyboardMarkup:
    """Statistics menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_general")],
        [InlineKeyboardButton(text="📈 По категориям", callback_data="stats_categories")],
        [InlineKeyboardButton(text="📅 По времени", callback_data="stats_time")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel keyboard (for future use)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика системы", callback_data="admin_system_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs")],
        [InlineKeyboardButton(text="🔧 Настройки", callback_data="admin_settings")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])


# Utility functions
def build_dynamic_keyboard(
    buttons: List[tuple],
    columns: int = 1,
    add_back: bool = True,
    back_data: str = "main_menu"
) -> InlineKeyboardMarkup:
    """Build dynamic keyboard from button data."""
    keyboard = []
    
    # Add buttons in rows
    for i in range(0, len(buttons), columns):
        row = []
        for j in range(columns):
            if i + j < len(buttons):
                text, callback_data = buttons[i + j]
                row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        keyboard.append(row)
    
    # Add back button if requested
    if add_back:
        keyboard.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data=back_data)
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)