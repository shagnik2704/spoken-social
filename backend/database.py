    # ============================================================
# Database Connection — Engine + Session
# ============================================================
# Engine = the connection to PostgreSQL
# SessionLocal = a factory that creates DB sessions (async, for API)
# SyncSessionLocal = a factory that creates sync sessions (for scripts)
# Base = all models inherit from this
# ============================================================

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shagniksarkar@localhost:5432/spoken_social")
if DATABASE_URL and "@postgres/" in DATABASE_URL and not os.path.exists("/.dockerenv"):
    DATABASE_URL = DATABASE_URL.replace("@postgres/", "@localhost:5432/")
elif DATABASE_URL and "@postgres:" in DATABASE_URL and not os.path.exists("/.dockerenv"):
    DATABASE_URL = DATABASE_URL.replace("@postgres:", "@localhost:")

# --- Async engine (for the API server) ---
ASYNC_DATABASE_URL = DATABASE_URL
if ASYNC_DATABASE_URL and ASYNC_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True
)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# --- Sync engine (for offline scripts like seed.py) ---
SYNC_DATABASE_URL = DATABASE_URL
if SYNC_DATABASE_URL and SYNC_DATABASE_URL.startswith("postgresql+asyncpg://"):
    SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    """All models inherit from this. It tracks all your tables."""
    pass


async def get_db():
    """
    FastAPI dependency that gives each request its own DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
