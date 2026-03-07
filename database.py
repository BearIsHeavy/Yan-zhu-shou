from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://api:api@localhost:5432/fastapi_db")

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Redis client initialization
redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

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
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency: Get Redis client
async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client