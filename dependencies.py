import json
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

import models
from database import get_db, get_redis
from routes import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Optional[Redis] = Depends(get_redis)
) -> models.User:
    """Get current authenticated user from JWT token with Redis cache."""
    payload = auth.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try to get user from Redis cache first (only if Redis is available)
    if redis:
        cache_key = f"user:{email}"
        try:
            cached_data = await redis.get(cache_key)
            if cached_data:
                user_dict = json.loads(cached_data)
                # Reconstruct user object from cache
                # Note: We still need to query DB to get a session-bound ORM object
                # But we can use cached data to avoid loading relationships
                result = await db.execute(select(models.User).where(models.User.email == email))
                user = result.scalar_one_or_none()
                if user:
                    return user
        except Exception as e:
            # Log error but continue to DB query if Redis fails
            print(f"Warning: Failed to read user cache: {e}")

    # Query database
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cache the user data with TTL (only if Redis is available)
    # Note: Do NOT cache hash_password for security reasons
    if redis:
        cache_key = f"user:{email}"
        cache_ttl = int(os.getenv("REDIS_CACHE_TTL", 300))
        try:
            user_dict = {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "gender": user.gender,
                "role": user.role,
                "created_at": str(user.created_at) if user.created_at else None
            }
            await redis.setex(cache_key, cache_ttl, json.dumps(user_dict))
        except Exception as e:
            # Log error but don't fail the request if Redis fails
            print(f"Warning: Failed to cache user data: {e}")

    return user
