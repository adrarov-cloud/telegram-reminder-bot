"""
Database Connection Module

Handles async database connections, session management, and initialization:
- SQLAlchemy async engine setup
- Session factory configuration
- Database initialization
- Connection pooling
- Transaction management
"""

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    async_sessionmaker, 
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database.models import Base


logger = logging.getLogger(__name__)


# Global engine and session factory
engine: AsyncEngine = None
SessionLocal: async_sessionmaker[AsyncSession] = None


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with proper configuration.
    
    Returns:
        AsyncEngine: Configured async engine
    """
    logger.info(f"Creating database engine for: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    
    # Configure engine parameters based on database type
    engine_kwargs = {
        "echo": settings.DEBUG,  # Log SQL queries in debug mode
        "pool_pre_ping": True,   # Verify connections before use
    }
    
    # Special configuration for SQLite
    if "sqlite" in settings.DATABASE_URL:
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,  # Allow SQLite usage across threads
            }
        })
    else:
        # For PostgreSQL and other databases
        engine_kwargs.update({
            "pool_size": 20,         # Connection pool size
            "max_overflow": 0,       # No overflow connections
            "pool_recycle": 3600,    # Recycle connections every hour
        })
    
    return create_async_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create session factory for database operations.
    
    Args:
        engine: Async database engine
        
    Returns:
        async_sessionmaker: Session factory
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
        autoflush=True,          # Automatically flush before queries
        autocommit=False,        # Manual transaction control
    )


async def init_database() -> None:
    """
    Initialize database connection and create tables.
    
    This function should be called once during application startup.
    """
    global engine, SessionLocal
    
    try:
        logger.info("Initializing database connection...")
        
        # Create engine and session factory
        engine = create_engine()
        SessionLocal = create_session_factory(engine)
        
        # Test connection
        async with engine.begin() as conn:
            # Create all tables
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/verified")
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_database() -> None:
    """
    Close database connections.
    
    Should be called during application shutdown.
    """
    global engine
    
    if engine:
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("✅ Database connections closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic cleanup.
    
    Usage:
        async with get_session() as session:
            # Use session for database operations
            result = await session.execute(query)
            await session.commit()
    
    Yields:
        AsyncSession: Database session
    """
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic transaction management.
    
    Automatically commits on success and rolls back on exceptions.
    
    Usage:
        async with get_transaction() as session:
            # All operations will be in a transaction
            session.add(new_object)
            # Automatically commits here
    
    Yields:
        AsyncSession: Database session in transaction
    """
    async with get_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                # Transaction will be automatically rolled back
                raise


async def execute_in_transaction(operation):
    """
    Execute a database operation in a transaction.
    
    Args:
        operation: Async function that takes a session parameter
        
    Returns:
        Result of the operation
    """
    async with get_transaction() as session:
        return await operation(session)


# Utility functions for common operations
async def health_check() -> bool:
    """
    Check database health.
    
    Returns:
        bool: True if database is healthy
    """
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information for monitoring.
    
    Returns:
        dict: Database information
    """
    try:
        info = {
            'engine': str(engine.url) if engine else None,
            'pool_size': engine.pool.size() if engine and hasattr(engine.pool, 'size') else None,
            'checked_out': engine.pool.checkedout() if engine and hasattr(engine.pool, 'checkedout') else None,
        }
        return info
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {'error': str(e)}
