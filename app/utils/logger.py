"""
Logging Configuration

Sets up comprehensive logging for the bot:
- File and console logging
- Structured log formatting
- Log rotation
- Different log levels for different components
- Performance monitoring
- Error tracking
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration for the bot.
    
    Args:
        log_file: Optional log file path override
    """
    # Use settings log file or provided override
    log_file_path = log_file or settings.LOG_FILE
    
    # Create logs directory if it doesn't exist
    if log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (if log file is specified)
    if log_file_path:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Error file handler for errors only
    if log_file_path:
        error_file_path = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    configure_library_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log file: {log_file_path or 'Console only'}")
    logger.info(f"Debug mode: {settings.DEBUG}")


def configure_library_loggers() -> None:
    """
    Configure logging levels for third-party libraries.
    """
    # Reduce aiogram verbosity
    logging.getLogger('aiogram').setLevel(logging.INFO)
    logging.getLogger('aiogram.dispatcher').setLevel(logging.INFO)
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    
    # Reduce aiohttp verbosity
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    
    # Reduce SQLAlchemy verbosity (unless in debug mode)
    if not settings.DEBUG:
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    # APScheduler
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    logging.getLogger('apscheduler.executors').setLevel(logging.WARNING)
    
    # Redis (if used)
    logging.getLogger('redis').setLevel(logging.WARNING)


class ContextFilter(logging.Filter):
    """
    Custom filter to add context information to log records.
    """
    
    def __init__(self, user_id: Optional[int] = None, chat_id: Optional[int] = None):
        super().__init__()
        self.user_id = user_id
        self.chat_id = chat_id
    
    def filter(self, record):
        record.user_id = getattr(record, 'user_id', self.user_id)
        record.chat_id = getattr(record, 'chat_id', self.chat_id)
        return True


def get_logger_with_context(name: str, user_id: Optional[int] = None, chat_id: Optional[int] = None) -> logging.Logger:
    """
    Get logger with user/chat context.
    
    Args:
        name: Logger name
        user_id: User ID for context
        chat_id: Chat ID for context
    
    Returns:
        Logger with context filter
    """
    logger = logging.getLogger(name)
    context_filter = ContextFilter(user_id, chat_id)
    logger.addFilter(context_filter)
    return logger


class PerformanceLogger:
    """
    Logger for tracking performance metrics.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"performance.{name}")
        self.logger.setLevel(logging.INFO)
    
    def log_duration(self, operation: str, duration: float, **kwargs):
        """Log operation duration."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{operation}: {duration:.3f}s | {extra_info}")
    
    def log_count(self, metric: str, count: int, **kwargs):
        """Log count metric."""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{metric}: {count} | {extra_info}")


# Create performance loggers for different components
db_perf_logger = PerformanceLogger("database")
api_perf_logger = PerformanceLogger("telegram_api")
scheduler_perf_logger = PerformanceLogger("scheduler")
