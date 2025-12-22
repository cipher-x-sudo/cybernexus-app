"""Database connection and session management.

This module provides database connection pooling and session management for
PostgreSQL using SQLAlchemy async engine. Does not use custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

from typing import AsyncGenerator
import threading
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
)
from sqlalchemy.orm import declarative_base
from loguru import logger

from app.config import settings
from app.core.database.models import Base

_thread_local = threading.local()

_main_engine: AsyncEngine | None = None
_main_session_maker: async_sessionmaker[AsyncSession] | None = None
_already_initialized_logged: bool = False

__all__ = ["get_db", "init_db", "close_db", "create_tables", "drop_tables", "_async_session_maker"]


def get_database_url() -> str:
    """Get the database URL with async driver prefix.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Returns:
        Database URL with postgresql+asyncpg:// prefix
    """
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    return db_url


def _get_thread_engine():
    if not hasattr(_thread_local, 'engine'):
        db_url = get_database_url()
        thread_id = threading.get_ident()
        logger.debug(f"Creating database engine for thread {thread_id}")
        
        _thread_local.engine = create_async_engine(
            db_url,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )
        
        _thread_local.session_maker = async_sessionmaker(
            _thread_local.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        logger.debug(f"Database engine created for thread {thread_id}")
    
    return _thread_local.engine, _thread_local.session_maker


def _get_async_session_maker():
    init_db()
    _, session_maker = _get_thread_engine()
    return session_maker


class _SessionMakerAccessor:
    def __call__(self):
        session_maker = _get_async_session_maker()
        return session_maker()
    
    def __bool__(self):
        try:
            session_maker = _get_async_session_maker()
            return session_maker is not None
        except Exception:
            return False

_async_session_maker = _SessionMakerAccessor()


def init_db() -> None:
    """Initialize the database connection pool.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Creates the main database engine and session maker if not already initialized.
    """
    global _main_engine, _main_session_maker, _already_initialized_logged
    
    engine, session_maker = _get_thread_engine()
    
    if _main_engine is None:
        _main_engine = engine
        _main_session_maker = session_maker
        db_url = get_database_url()
        logger.info(f"Initializing database connection: {db_url.split('@')[1] if '@' in db_url else 'local'}")
        logger.info("Database connection pool initialized")
        _already_initialized_logged = True


async def close_db() -> None:
    """Close database connections for the current thread.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Disposes of thread-local database engine if it differs from the main engine.
    """
    global _main_engine, _main_session_maker
    
    if hasattr(_thread_local, 'engine'):
        thread_engine = _thread_local.engine
        if thread_engine != _main_engine:
            await thread_engine.dispose()
            logger.debug(f"Closed database engine for thread {threading.get_ident()}")
        delattr(_thread_local, 'engine')
        if hasattr(_thread_local, 'session_maker'):
            delattr(_thread_local, 'session_maker')


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for dependency injection.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Yields:
        AsyncSession: Database session that commits on success or rolls back on error
    
    Raises:
        RuntimeError: If database is not initialized
    """
    init_db()
    _, session_maker = _get_thread_engine()
    
    if session_maker is None:
        raise RuntimeError("Database not initialized")
    
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables defined in the models.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Raises:
        RuntimeError: If database is not initialized
    """
    init_db()
    engine, _ = _get_thread_engine()
    
    if engine is None:
        raise RuntimeError("Database not initialized")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def drop_tables() -> None:
    """Drop all database tables.
    
    DSA-USED:
    - None: This function does not use custom DSA structures from app.core.dsa.
    
    Raises:
        RuntimeError: If database is not initialized
    """
    init_db()
    engine, _ = _get_thread_engine()
    
    if engine is None:
        raise RuntimeError("Database not initialized")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("Database tables dropped")

