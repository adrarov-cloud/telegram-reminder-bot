"""
Reminder FSM States

Defines all finite state machine states for reminder creation and management:
- Creating new reminders
- Editing existing reminders
- Setting repeat options
- Template management
"""

from aiogram.fsm.state import State, StatesGroup


class ReminderCreateStates(StatesGroup):
    """States for creating a new reminder."""
    
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_datetime = State()
    waiting_for_repeat_type = State()
    waiting_for_repeat_interval = State()
    waiting_for_repeat_until = State()
    confirming_reminder = State()


class ReminderEditStates(StatesGroup):
    """States for editing existing reminders."""
    
    selecting_reminder = State()
    selecting_field = State()
    editing_title = State()
    editing_description = State()
    editing_datetime = State()
    editing_repeat = State()
    confirming_changes = State()


class TemplateStates(StatesGroup):
    """States for template management."""
    
    creating_template_name = State()
    creating_template_title = State()
    creating_template_description = State()
    editing_template = State()
    confirming_template = State()
    using_template = State()


class SettingsStates(StatesGroup):
    """States for user settings."""
    
    selecting_timezone = State()
    configuring_notifications = State()
    confirming_settings = State()
