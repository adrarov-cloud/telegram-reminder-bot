"""
Configuration Management

Uses Pydantic Settings for type-safe configuration with environment variable support.
Automatically validates all settings and provides sensible defaults.
"""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    For example: BOT_TOKEN, DATABASE_URL, DEBUG, etc.
    """
    
    # Bot Configuration
    BOT_TOKEN: str = Field(..., description="Telegram Bot API token from @BotFather")
    BOT_USERNAME: Optional[str] = Field(None, description="Bot username (without @)")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///reminder_bot.db",
        description="Database connection URL"
    )
    
    # Redis (optional)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching and sessions"
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development/production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # Webhook settings (for production)
    WEBHOOK_HOST: Optional[str] = Field(None, description="Webhook host URL")
    WEBHOOK_PATH: str = Field(default="/webhook", description="Webhook endpoint path")
    WEBHOOK_SECRET: Optional[str] = Field(None, description="Webhook secret token")
    
    # Timezone
    DEFAULT_TIMEZONE: str = Field(default="Europe/Moscow", description="Default timezone")
    
    # Rate limiting
    MAX_MESSAGES_PER_MINUTE: int = Field(default=30, description="Global rate limit")
    MAX_MESSAGES_PER_CHAT_PER_MINUTE: int = Field(default=1, description="Per-chat rate limit")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: Optional[str] = Field(default="bot.log", description="Log file path")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=8000, description="Metrics server port")
    
    @validator('BOT_TOKEN')
    def validate_bot_token(cls, v):
        """Validate bot token format."""
        if not v or v == "your_bot_token_here":
            raise ValueError("BOT_TOKEN must be set to a valid Telegram Bot API token")
        
        # Basic format validation: should contain numbers and colon
        if ':' not in v or not any(c.isdigit() for c in v):
            raise ValueError("BOT_TOKEN appears to be invalid (should contain ':' and numbers)")
        
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate logging level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {valid_envs}")
        return v.lower()
    
    @validator('MAX_MESSAGES_PER_MINUTE', 'MAX_MESSAGES_PER_CHAT_PER_MINUTE')
    def validate_rate_limits(cls, v):
        """Validate rate limit values."""
        if v <= 0:
            raise ValueError("Rate limit values must be positive integers")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"\n❌ Configuration Error: {e}")
    print("\n📝 Please check your .env file and ensure:")
    print("1. BOT_TOKEN is set to your actual Telegram bot token")
    print("2. All required settings are properly configured")
    print("3. Copy .env.example to .env and update the values")
    raise


# Convenient access to common settings
IS_PRODUCTION = settings.ENVIRONMENT == "production"
IS_DEBUG = settings.DEBUG and not IS_PRODUCTION
USE_WEBHOOK = IS_PRODUCTION and settings.WEBHOOK_HOST is not None
