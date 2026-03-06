import json
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models
from database import get_db, get_redis
from routes import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
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
    
    # Try to get user from Redis cache
    cache_key = f"user:{email}"
    cached_user = await redis.get(cache_key)
    
    if cached_user:
        # Deserialize cached user data and return
        user_data = json.loads(cached_user)
        # Reconstruct user object from cached data
        return models.User(**user_data)
    
    # Query database if not in cache
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Cache the user data with TTL
    cache_ttl = int(os.getenv("REDIS_CACHE_TTL", 300))
    user_dict = {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "hash_password": user.hash_password,
        "phone": user.phone,
        "gender": user.gender,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    await redis.setex(cache_key, cache_ttl, json.dumps(user_dict))
    
    return user
