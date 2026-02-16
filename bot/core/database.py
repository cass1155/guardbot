import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from bot.core.config import settings

class Base(DeclarativeBase):
    pass

db_url = settings.database_url
logging.info(f"Database URL scheme: {db_url.split('@')[0].split('://')[0] if '://' in db_url else db_url}")

engine = create_async_engine(db_url, echo=False)

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
                await conn.execute(text("SELECT 1"))
            logging.info("Database connection established")
            return
        except Exception as e:
            logging.warning(
                f"DB connection attempt {attempt}/{retries} failed: {type(e).__name__}: {repr(e)}",
                exc_info=True
            )
            if attempt < retries:
                await asyncio.sleep(delay)
    raise RuntimeError(f"Could not connect to database after {retries} attempts")
