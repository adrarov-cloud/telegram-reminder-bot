"""
Logging Module

Comprehensive logging setup with rotation, structured output,
and different handlers for different environments.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from src.config import config


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        if record.levelname in self.COLORS:
            colored_level = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
            record.levelname = colored_level
        
        # Format the message
        formatted = super().format(record)
        
        # Reset color at the end
        return f"{formatted}{self.COLORS['RESET']}"


class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records."""
    
    def filter(self, record):
        """Add context to log record."""
        # Add module name if not present
        if not hasattr(record, 'module'):
            record.module = getattr(record, 'name', 'unknown').split('.')[-1]
        
        # Add user context if available
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(record, 'user_id', None)
        
        # Add request ID for tracing (if available)
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(record, 'request_id', None)
        
        return True


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> None:
    """
    Setup comprehensive logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path (None for no file logging)
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt=(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | '
            '%(funcName)-15s:%(lineno)-4d | %(message)s'
        ),
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt=(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | '
            '%(message)s'
        ),
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Use colored formatter for console
        console_handler.setFormatter(colored_formatter)
        
        # Add context filter
        console_handler.addFilter(ContextFilter())
        
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        file_handler.addFilter(ContextFilter())
        
        root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    if log_file:
        error_log_file = str(Path(log_file).with_suffix('.error.log'))
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        error_handler.addFilter(ContextFilter())
        
        root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    configure_library_loggers()
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging configured - Level: {level}, File: {log_file}")


def configure_library_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    
    # Reduce noise from libraries
    library_configs = {
        'aiogram': logging.WARNING,
        'aiohttp': logging.WARNING, 
        'apscheduler': logging.WARNING,
        'sqlalchemy.engine': logging.WARNING,
        'sqlalchemy.pool': logging.WARNING,
        'asyncio': logging.WARNING,
        'telegram': logging.WARNING,
    }
    
    for lib_name, lib_level in library_configs.items():
        logging.getLogger(lib_name).setLevel(lib_level)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with name."""
    return logging.getLogger(name)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"📞 Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} failed: {e}")
            raise
    
    return wrapper


async def log_async_function_call(func):
    """Decorator to log async function calls."""
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"📞 Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ {func.__name__} failed: {e}")
            raise
    
    return wrapper


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Performance logging utilities
import time
from contextlib import contextmanager


@contextmanager
def log_execution_time(operation_name: str, logger: Optional[logging.Logger] = None):
    """Context manager to log execution time."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    start_time = time.time()
    logger.debug(f"⏱️ Starting {operation_name}")
    
    try:
        yield
        execution_time = time.time() - start_time
        logger.info(f"⏱️ {operation_name} completed in {execution_time:.3f}s")
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ {operation_name} failed after {execution_time:.3f}s: {e}")
        raise


# Structured logging utilities
def log_user_action(
    user_id: int,
    action: str,
    details: Optional[dict] = None,
    logger: Optional[logging.Logger] = None
):
    """Log user action with structured data."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    log_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': time.time()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"👤 User action: {action}", extra=log_data)


def log_system_event(
    event_type: str,
    message: str,
    details: Optional[dict] = None,
    logger: Optional[logging.Logger] = None
):
    """Log system event with structured data."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    log_data = {
        'event_type': event_type,
        'timestamp': time.time()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"🔧 System event: {message}", extra=log_data)


def log_reminder_event(
    reminder_id: int,
    user_id: int,
    event: str,
    details: Optional[dict] = None,
    logger: Optional[logging.Logger] = None
):
    """Log reminder-related event."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    log_data = {
        'reminder_id': reminder_id,
        'user_id': user_id,
        'event': event,
        'timestamp': time.time()
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"🔔 Reminder event: {event}", extra=log_data)


# Health check logging
def log_health_check(component: str, status: bool, details: Optional[str] = None):
    """Log component health check result."""
    logger = logging.getLogger('health_check')
    
    status_emoji = "✅" if status else "❌"
    status_text = "OK" if status else "FAIL"
    
    message = f"{status_emoji} {component}: {status_text}"
    if details:
        message += f" - {details}"
    
    if status:
        logger.info(message)
    else:
        logger.error(message)


# Error reporting utilities
def log_exception_with_context(
    e: Exception,
    context: Optional[dict] = None,
    logger: Optional[logging.Logger] = None
):
    """Log exception with additional context."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    error_data = {
        'exception_type': type(e).__name__,
        'exception_message': str(e),
        'timestamp': time.time()
    }
    
    if context:
        error_data.update(context)
    
    logger.error(f"💥 Exception occurred: {type(e).__name__}: {str(e)}", 
                extra=error_data, exc_info=True)


# Initialize logging when module is imported
if config.LOG_FILE:
    setup_logging(
        level=config.LOG_LEVEL,
        log_file=config.LOG_FILE,
        max_bytes=config.LOG_MAX_BYTES,
        backup_count=config.LOG_BACKUP_COUNT
    )