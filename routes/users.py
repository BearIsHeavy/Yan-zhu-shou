import json
from datetime import timedelta
from typing import Optional
from pathlib import Path

from fastapi import Depends, HTTPException, status, UploadFile, File
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from routes import auth
import models
import schemas
from dependencies import get_current_user
from database import get_db, get_redis
from utils.file_storage import save_bio_file, read_bio_file, delete_bio_file

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def user_login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
        redis: Optional[Redis] = Depends(get_redis)
):
    """Login and get access token. Cache frequently accessed users in Redis."""
    # Find user by email
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Check if user exists and has a valid password hash
    if user is None or user.hash_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not auth.verify_password(form_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cache user data in Redis for faster subsequent access (only if Redis is available)
    if redis:
        cache_ttl = 300
        try:
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
        except Exception as e:
            # Log error but don't fail login if Redis fails
            print(f"Warning: Failed to cache user data: {e}")

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
    redis: Optional[Redis] = Depends(get_redis)
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
    await db.commit()  # Commit to get created_at
    await db.refresh(new_user)

    # Cache the new user data (only if Redis is available)
    if redis:
        cache_ttl = 300
        try:
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
        except Exception as e:
            # Log error but don't fail registration if Redis fails
            print(f"Warning: Failed to cache user data: {e}")

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
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    token: str = Depends(oauth2_scheme)
):
    """Update current user information and invalidate cache."""
    # Get user email from token
    from routes import auth
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
    
    # Load user in the same session used for update
    result = await db.execute(select(models.User).where(models.User.email == email))
    current_user = result.scalar_one_or_none()
    
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)

    # Invalidate cache after update
    cache_key = f"user:{current_user.email}"
    await redis.delete(cache_key)

    return current_user


# ============== Self-Introduction (Bio File) Endpoints ==============


@router.post("/bio", response_model=schemas.BioFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_bio(
    file: UploadFile = File(..., description="Markdown file for self-introduction"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a self-introduction markdown file.

    **Requirements:**
    - File must be in Markdown format (.md or .markdown)
    - Maximum file size: 1MB

    Replaces existing bio file if one already exists.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    # Read file content
    content = await file.read()

    # Save file and get relative path
    file_path = save_bio_file(
        file_content=content,
        original_filename=file.filename,
        user_id=current_user.user_id,
    )

    # Delete old bio file if exists
    if current_user.bio_file_path:
        delete_bio_file(current_user.user_id, current_user.bio_file_path)

    # Update user record with new file path
    result = await db.execute(select(models.User).where(models.User.user_id == current_user.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.bio_file_path = file_path
        await db.flush()

    return schemas.BioFileResponse(
        file_path=file_path,
        file_name=file.filename,
        uploaded_at=user.created_at if user else current_user.created_at,
    )


@router.get("/bio", response_model=str)
async def get_bio(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the current user's self-introduction markdown content.

    Returns the raw markdown content as plain text.
    """
    if not current_user.bio_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No self-introduction uploaded yet",
        )

    content = read_bio_file(current_user.user_id, current_user.bio_file_path)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bio file not found on server",
        )

    return content


@router.get("/bio/{user_id}", response_model=str)
async def get_user_bio(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get another user's self-introduction markdown content.

    Returns the raw markdown content as plain text.
    """
    result = await db.execute(select(models.User).where(models.User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.bio_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not uploaded a self-introduction",
        )

    content = read_bio_file(user.user_id, user.bio_file_path)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bio file not found on server",
        )

    return content


@router.delete("/bio", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bio(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete the current user's self-introduction file.

    Removes both the file from storage and the reference from the database.
    """
    if not current_user.bio_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No self-introduction to delete",
        )

    # Delete file from storage
    delete_bio_file(current_user.user_id, current_user.bio_file_path)

    # Update user record
    result = await db.execute(select(models.User).where(models.User.user_id == current_user.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.bio_file_path = None
        await db.flush()

    return None
