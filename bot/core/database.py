import asyncio
import logging
import ssl as ssl_module

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from bot.core.config import settings

class Base(DeclarativeBase):
    pass

# Build engine kwargs — disable SSL for asyncpg (fixes Railway internal connections)
engine_kwargs = {"echo": False}
if "asyncpg" in settings.database_url:
    engine_kwargs["connect_args"] = {"ssl": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

async def wait_for_db(retries: int = 10, delay: float = 3.0):
    """Try connecting to the database with retries."""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            logging.info("Database connection established")
            return
        except Exception as e:
            logging.warning(
                f"DB connection attempt {attempt}/{retries} failed: {e}"
            )
            if attempt < retries:
                await asyncio.sleep(delay)
    raise RuntimeError(f"Could not connect to database after {retries} attempts")
