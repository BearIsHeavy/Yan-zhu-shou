from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str  # 创建时需要密码


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    # 开启 from_attributes 以支持从 ORM 对象读取数据
    model_config = {"from_attributes": True}


# --- Item Schemas ---
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}