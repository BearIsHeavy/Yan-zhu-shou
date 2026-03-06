import json
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from routes import auth
import models
import schemas
from dependencies import get_current_user
from database import get_db, get_redis

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def user_login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    """Login and get access token. Cache frequently accessed users in Redis."""
    # Find user by email
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if user is None or not auth.verify_password(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cache user data in Redis for faster subsequent access
    cache_ttl = 300
    user_dict = {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "hash_password": user.hash_password,
        "phone": user.phone,
        "gender": user.gender,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    await redis.setex(f"user:{user.email}", cache_ttl, json.dumps(user_dict))

    # create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "user_id": user.user_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserResponse)
async def user_register(
    user_data: schemas.UserRegister,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Register a new user"""
    # check if email already exists
    result = await db.execute(select(models.User).where(models.User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already register"
        )

    #Create new user
    hashed_password = auth.hash_password(user_data.password)
    new_user: models.User = models.User(
        email=user_data.email,
        name=user_data.name,
        hash_password=hashed_password,
        phone=user_data.phone,
        gender=user_data.gender
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    
    # Cache the new user data
    cache_ttl = 300
    user_dict = {
        "user_id": new_user.user_id,
        "email": new_user.email,
        "name": new_user.name,
        "hash_password": new_user.hash_password,
        "phone": new_user.phone,
        "gender": new_user.gender,
        "created_at": new_user.created_at.isoformat() if new_user.created_at else None
    }
    await redis.setex(f"user:{new_user.email}", cache_ttl, json.dumps(user_dict))
    
    return new_user

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Update current user information and invalidate cache."""
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    
    # Invalidate cache after update
    cache_key = f"user:{current_user.email}"
    await redis.delete(cache_key)
    
    return current_user
