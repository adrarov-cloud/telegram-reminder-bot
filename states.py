"""
Enhanced FSM States

Comprehensive state management with confirmation flows,
editing capabilities, and quick actions.
"""

from aiogram.fsm.state import State, StatesGroup


class ReminderStates(StatesGroup):
    """FSM states for reminder creation and management."""
    
    # Main creation flow
    waiting_for_text = State()
    waiting_for_time = State()
    confirming_reminder = State()
    
    # Editing states
    editing_text = State()
    editing_time = State()
    
    # Quick creation
    quick_reminder = State()
    
    # Statistics viewing
    viewing_stats = State()
    
    # Settings management
    managing_settings = State()


class ReminderEditStates(StatesGroup):
    """FSM states for editing existing reminders."""
    
    selecting_reminder = State()
    editing_selected_text = State()
    editing_selected_time = State()
    confirming_edit = State()
    confirming_delete = State()


class CategoryStates(StatesGroup):
    """FSM states for category management (future feature)."""
    
    selecting_category = State()
    creating_category = State()
    editing_category = State()


class RecurringStates(StatesGroup):
    """FSM states for recurring reminders (future feature)."""
    
    setting_pattern = State()
    confirming_pattern = State()
    managing_recurring = State()