"""
Database Connection and Session Management

Handles async database connections using SQLAlchemy 2.0.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
)
from sqlalchemy.orm import declarative_base
from loguru import logger

from app.config import settings
from app.core.database.models import Base

# Global engine and session factory
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None

# Export session maker for middleware use
__all__ = ["get_db", "init_db", "close_db", "create_tables", "drop_tables", "_async_session_maker"]


def get_database_url() -> str:
    """Get database URL, converting postgresql:// to postgresql+asyncpg:// if needed."""
    db_url = settings.DATABASE_URL
    
    # Convert postgresql:// to postgresql+asyncpg:// for async operations
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    return db_url


def init_db() -> None:
    """Initialize database connection pool."""
    global _engine, _async_session_maker
    
    if _engine is not None:
        logger.warning("Database already initialized")
        return
    
    db_url = get_database_url()
    
    logger.info(f"Initializing database connection: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    _engine = create_async_engine(
        db_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.DEBUG,  # Log SQL queries in debug mode
    )
    
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    logger.info("Database connection pool initialized")


async def close_db() -> None:
    """Close database connection pool."""
    global _engine, _async_session_maker
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connection pool closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    if _async_session_maker is None:
        init_db()
    
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized")
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    if _engine is None:
        init_db()
    
    if _engine is None:
        raise RuntimeError("Database not initialized")
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def drop_tables() -> None:
    """Drop all database tables (use with caution!)."""
    if _engine is None:
        init_db()
    
    if _engine is None:
        raise RuntimeError("Database not initialized")
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("Database tables dropped")

