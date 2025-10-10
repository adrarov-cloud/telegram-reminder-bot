"""
Database Package

Handles all database operations:
- SQLAlchemy models and relationships
- Async connection management
- Session handling and transactions
- Database initialization and migrations
"""

from .models import Base, User, Reminder, ReminderTemplate, UserStats
from .connection import init_database, close_database, get_session, get_transaction

__all__ = [
    'Base',
    'User', 
    'Reminder',
    'ReminderTemplate',
    'UserStats',
    'init_database',
    'close_database', 
    'get_session',
    'get_transaction'
]