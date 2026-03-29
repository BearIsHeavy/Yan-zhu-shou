from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
import redis.asyncio as redis
from typing import Optional

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://api:api@localhost:5432/fastapi_db")

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Redis client initialization (lazy loading to handle connection errors)
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance, returns None if Redis is not available."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            print(f"Warning: Failed to connect to Redis: {e}")
            return None
    return _redis_client

# Base class for models
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency: Get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Don't auto-commit here - let service functions handle their own commits
            # This prevents double-commit issues
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency: Get Redis client
async def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance, returns None if Redis is not available."""
    return get_redis_client()