# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=64, description="Maximum length 64 characters")
    name: str
    phone: Optional[str] = None
    gender: Optional[int] = 0


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=64)


class Token(BaseModel):
    access_token: str
    token_type: str