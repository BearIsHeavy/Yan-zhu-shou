from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, min_length=11, max_length=20)
    gender: int = Field(default=0, ge=0, le=2, description="0:Unknown 1:Male 2:Female")


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserRegister(UserBase):
    """Alias for UserCreate - kept for backward compatibility"""
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, min_length=11, max_length=20)
    gender: Optional[int] = Field(default=None, ge=0, le=2)


class UserResponse(UserBase):
    user_id: int
    email: str
    name: str
    phone: Optional[str] = None
    gender: int = 0
    bio_file_path: Optional[str] = None  # Relative path to self-introduction markdown file
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class BioFileResponse(BaseModel):
    """Response for bio file operations."""
    file_path: str
    file_name: str
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)
