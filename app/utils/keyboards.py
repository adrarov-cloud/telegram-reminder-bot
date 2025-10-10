"""
Keyboard Utilities

Builds various keyboards for the Telegram bot interface:
- Main menu keyboard
- Reminder management keyboards
- Settings and preferences keyboards
- Inline keyboards for actions
- Dynamic keyboards based on data
"""

from typing import List, Optional
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    ReplyKeyboardRemove
)
from datetime import datetime


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get main menu keyboard with all primary actions.
    
    Returns:
        InlineKeyboardMarkup: Main menu keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Create Reminder", callback_data="create_reminder"),
            InlineKeyboardButton(text="📋 View Reminders", callback_data="list_reminders")
        ],
        [
            InlineKeyboardButton(text="📝 Templates", callback_data="templates"),
            InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="📊 Statistics", callback_data="statistics"),
            InlineKeyboardButton(text="🎆 Help", callback_data="help")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get simple back to menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Back to menu keyboard
    """
    keyboard = [[
        InlineKeyboardButton(text="🏠 Back to Menu", callback_data="main_menu")
    ]]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reminder_actions_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    """
    Get keyboard for reminder actions.
    
    Args:
        reminder_id: ID of the reminder
    
    Returns:
        InlineKeyboardMarkup: Reminder actions keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_reminder:{reminder_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"delete_reminder:{reminder_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 Duplicate", callback_data=f"duplicate_reminder:{reminder_id}"),
            InlineKeyboardButton(text="📝 Create Template", callback_data=f"create_template:{reminder_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to List", callback_data="list_reminders")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reminders_list_keyboard(reminders: List, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Get paginated keyboard for reminders list.
    
    Args:
        reminders: List of reminder objects
        page: Current page number
        per_page: Reminders per page
    
    Returns:
        InlineKeyboardMarkup: Reminders list keyboard
    """
    keyboard = []
    
    # Calculate pagination
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(reminders))
    total_pages = (len(reminders) - 1) // per_page + 1 if reminders else 0
    
    # Add reminder buttons
    for i in range(start_idx, end_idx):
        reminder = reminders[i]
        
        # Format reminder title (truncate if too long)
        title = reminder.title
        if len(title) > 30:
            title = title[:27] + "..."
        
        # Add status emoji
        status_emoji = "⏰" if reminder.status == 'pending' else "✅" if reminder.status == 'sent' else "❌"
        
        # Format date
        date_str = reminder.scheduled_at.strftime('%m/%d %H:%M')
        
        button_text = f"{status_emoji} {title} - {date_str}"
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"view_reminder:{reminder.id}")
        ])
    
    # Add pagination controls if needed
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="◀️ Previous", callback_data=f"reminders_page:{page-1}")
            )
        
        pagination_row.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="Next ▶️", callback_data=f"reminders_page:{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add control buttons
    if reminders:
        keyboard.append([
            InlineKeyboardButton(text="➕ New Reminder", callback_data="create_reminder"),
            InlineKeyboardButton(text="🗑️ Delete All", callback_data="delete_all_reminders")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="➕ Create Your First Reminder", callback_data="create_reminder")
        ])
    
    # Back to menu
    keyboard.append([
        InlineKeyboardButton(text="🏠 Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_repeat_type_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting repeat type.
    
    Returns:
        InlineKeyboardMarkup: Repeat type selection keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(text="⏰ One Time", callback_data="repeat:none"),
            InlineKeyboardButton(text="📅 Daily", callback_data="repeat:daily")
        ],
        [
            InlineKeyboardButton(text="📆 Weekly", callback_data="repeat:weekly"),
            InlineKeyboardButton(text="🗺 Monthly", callback_data="repeat:monthly")
        ],
        [
            InlineKeyboardButton(text="🎆 Yearly", callback_data="repeat:yearly"),
            InlineKeyboardButton(text="⚙️ Custom", callback_data="repeat:custom")
        ],
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_operation")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_timezone_keyboard(common_timezones: List[str]) -> InlineKeyboardMarkup:
    """
    Get keyboard for timezone selection.
    
    Args:
        common_timezones: List of common timezone strings
    
    Returns:
        InlineKeyboardMarkup: Timezone selection keyboard
    """
    keyboard = []
    
    # Add common timezones in pairs
    for i in range(0, len(common_timezones), 2):
        row = []
        for j in range(2):
            if i + j < len(common_timezones):
                tz = common_timezones[i + j]
                # Extract city name for display
                display_name = tz.split('/')[-1].replace('_', ' ')
                row.append(
                    InlineKeyboardButton(text=display_name, callback_data=f"timezone:{tz}")
                )
        keyboard.append(row)
    
    # Add option to search for other timezones
    keyboard.append([
        InlineKeyboardButton(text="🔍 Search Other Timezone", callback_data="timezone_search")
    ])
    
    # Cancel button
    keyboard.append([
        InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_operation")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel_operation") -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard with confirm/cancel options.
    
    Args:
        confirm_data: Callback data for confirm button
        cancel_data: Callback data for cancel button
    
    Returns:
        InlineKeyboardMarkup: Confirmation keyboard
    """
    keyboard = [[
        InlineKeyboardButton(text="✅ Confirm", callback_data=confirm_data),
        InlineKeyboardButton(text="❌ Cancel", callback_data=cancel_data)
    ]]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Get settings menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Settings menu keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(text="🌍 Timezone", callback_data="settings_timezone"),
            InlineKeyboardButton(text="🔔 Notifications", callback_data="settings_notifications")
        ],
        [
            InlineKeyboardButton(text="🎨 Interface", callback_data="settings_interface"),
            InlineKeyboardButton(text="📊 Export Data", callback_data="settings_export")
        ],
        [
            InlineKeyboardButton(text="🗑️ Delete Account", callback_data="settings_delete_account")
        ],
        [
            InlineKeyboardButton(text="🏠 Back to Menu", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_templates_keyboard(templates: List, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Get keyboard for templates management.
    
    Args:
        templates: List of template objects
        page: Current page number
        per_page: Templates per page
    
    Returns:
        InlineKeyboardMarkup: Templates keyboard
    """
    keyboard = []
    
    # Calculate pagination
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(templates))
    total_pages = (len(templates) - 1) // per_page + 1 if templates else 0
    
    # Add template buttons
    for i in range(start_idx, end_idx):
        template = templates[i]
        
        # Format template name (truncate if too long)
        name = template.name
        if len(name) > 25:
            name = name[:22] + "..."
        
        # Add usage count
        usage_text = f" ({template.usage_count} uses)" if template.usage_count > 0 else ""
        
        button_text = f"📝 {name}{usage_text}"
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=f"template:{template.id}")
        ])
    
    # Add pagination if needed
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="◀️ Previous", callback_data=f"templates_page:{page-1}")
            )
        
        pagination_row.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="Next ▶️", callback_data=f"templates_page:{page+1}")
            )
        
        keyboard.append(pagination_row)
    
    # Add control buttons
    keyboard.append([
        InlineKeyboardButton(text="➕ New Template", callback_data="create_template"),
        InlineKeyboardButton(text="🏠 Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Get keyboard removal object.
    
    Returns:
        ReplyKeyboardRemove: Object to remove custom keyboard
    """
    return ReplyKeyboardRemove()
