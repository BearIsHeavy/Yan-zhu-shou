#!/bin/bash
set -e

echo "🚀 Starting YanZhuShou Application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
engine = create_async_engine('${DATABASE_URL:-postgresql+asyncpg://api:api@postgres:5432/fastapi_db}')
async def check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
            await engine.dispose()
            return True
    except Exception as e:
        print(f'PostgreSQL check failed: {e}')
        return False
exit(0 if asyncio.run(check()) else 1)
" 2>&1; do
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! python -c "
import asyncio
import redis.asyncio as redis
async def check():
    try:
        r = redis.from_url('${REDIS_URL:-redis://redis:6379/0}')
        await r.ping()
        await r.close()
        return True
    except Exception as e:
        print(f'Redis check failed: {e}')
        return False
exit(0 if asyncio.run(check()) else 1)
" 2>&1; do
    sleep 2
done
echo "✅ Redis is ready"

echo "✅ All dependencies ready"

# Start the application
exec "$@"
