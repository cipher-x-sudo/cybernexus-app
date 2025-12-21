"""
Database Connection and Session Management

Handles async database connections using SQLAlchemy 2.0.
Uses thread-local storage to support multiple event loops (main loop + background job threads).
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

# Thread-local storage for engines (each thread/event loop gets its own engine)
_thread_local = threading.local()

# Global engine for main event loop (backward compatibility)
_main_engine: AsyncEngine | None = None
_main_session_maker: async_sessionmaker[AsyncSession] | None = None
_already_initialized_logged: bool = False

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


def _get_thread_engine():
    """Get or create engine for current thread."""
    if not hasattr(_thread_local, 'engine'):
        db_url = get_database_url()
        thread_id = threading.get_ident()
        logger.debug(f"Creating database engine for thread {thread_id}")
        
        _thread_local.engine = create_async_engine(
            db_url,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.DEBUG,  # Log SQL queries in debug mode
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


# Create a module-level accessor for backward compatibility
# This allows code to use _async_session_maker as if it were a variable
class _SessionMakerAccessor:
    """Accessor that returns thread-local session maker."""
    def __call__(self):
        """Call like _async_session_maker() to get session maker."""
        init_db()  # Ensure engine is initialized
        _, session_maker = _get_thread_engine()
        return session_maker
    
    def __bool__(self):
        """Check if session maker is available (for 'if _async_session_maker:' checks)."""
        try:
            init_db()
            _, session_maker = _get_thread_engine()
            return session_maker is not None
        except Exception:
            return False

# Module-level accessor instance
_async_session_maker = _SessionMakerAccessor()


def init_db() -> None:
    """Initialize database connection pool for current thread."""
    global _main_engine, _main_session_maker, _already_initialized_logged
    
    # Get or create engine for current thread
    engine, session_maker = _get_thread_engine()
    
    # Store main engine for backward compatibility (first initialization)
    if _main_engine is None:
        _main_engine = engine
        _main_session_maker = session_maker
        db_url = get_database_url()
        logger.info(f"Initializing database connection: {db_url.split('@')[1] if '@' in db_url else 'local'}")
        logger.info("Database connection pool initialized")
        _already_initialized_logged = True


async def close_db() -> None:
    """Close database connection pool for current thread."""
    global _main_engine, _main_session_maker
    
    # Close thread-local engine if it exists
    if hasattr(_thread_local, 'engine'):
        thread_engine = _thread_local.engine
        # Only dispose if it's not the main engine (main engine should persist)
        if thread_engine != _main_engine:
            await thread_engine.dispose()
            logger.debug(f"Closed database engine for thread {threading.get_ident()}")
        # Always clear thread-local storage
        delattr(_thread_local, 'engine')
        if hasattr(_thread_local, 'session_maker'):
            delattr(_thread_local, 'session_maker')
    
    # Note: We don't dispose _main_engine here as it may still be in use by the main event loop
    # The main engine should be disposed during application shutdown via lifespan handler


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    init_db()  # Ensure engine is initialized for current thread
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
    """Create all database tables."""
    init_db()  # Ensure engine is initialized for current thread
    engine, _ = _get_thread_engine()
    
    if engine is None:
        raise RuntimeError("Database not initialized")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")


async def drop_tables() -> None:
    """Drop all database tables (use with caution!)."""
    init_db()  # Ensure engine is initialized for current thread
    engine, _ = _get_thread_engine()
    
    if engine is None:
        raise RuntimeError("Database not initialized")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("Database tables dropped")

