"""
Configuration Management

Centralized configuration with environment variable support,
validation, and type safety.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'reminders.db')
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE', 'bot.log')
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Scheduler Configuration
    SCHEDULER_TIMEZONE: str = os.getenv('SCHEDULER_TIMEZONE', 'UTC')
    
    # Performance Configuration
    MAX_REMINDERS_PER_USER: int = int(os.getenv('MAX_REMINDERS_PER_USER', '100'))
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv('CLEANUP_INTERVAL_HOURS', '24'))
    
    # Feature Flags
    ENABLE_STATS: bool = os.getenv('ENABLE_STATS', 'true').lower() == 'true'
    ENABLE_CATEGORIES: bool = os.getenv('ENABLE_CATEGORIES', 'false').lower() == 'true'
    ENABLE_RECURRING: bool = os.getenv('ENABLE_RECURRING', 'false').lower() == 'true'
    
    # Development Configuration
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if cls.LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append(f"Invalid LOG_LEVEL: {cls.LOG_LEVEL}")
        
        if cls.MAX_REMINDERS_PER_USER <= 0:
            errors.append("MAX_REMINDERS_PER_USER must be positive")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    @classmethod
    def get_database_path(cls) -> Path:
        """Get database file path."""
        return Path(cls.DATABASE_PATH)
    
    @classmethod
    def get_log_path(cls) -> Optional[Path]:
        """Get log file path."""
        if cls.LOG_FILE:
            return Path(cls.LOG_FILE)
        return None


# Global configuration instance
config = Config()

# Validate configuration on import
config.validate()