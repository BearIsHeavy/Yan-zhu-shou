"""
Pydantic schemas for Books module.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import IntEnum


class BookStatusEnum(IntEnum):
    """Book processing status."""
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


class UserBookBase(BaseModel):
    """Base schema for user book."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Book title")


class UserBookCreate(UserBookBase):
    """Schema for creating a user book."""
    pass


class UserBookUpdate(BaseModel):
    """Schema for updating a user book."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    knowledge_tree: Optional[Dict[str, Any]] = None
    status: Optional[BookStatusEnum] = None


class UserBookResponse(UserBookBase):
    """Response schema for user book."""
    
    id: int
    user_id: int
    file_path: str
    file_type: str
    file_size: int
    status: BookStatusEnum
    knowledge_tree: Optional[Dict[str, Any]] = None
    chapter_count: int = 0
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BookUploadResponse(BaseModel):
    """Response for book upload."""
    
    id: int
    title: str
    file_path: str
    status: BookStatusEnum
    message: str = "Upload successful. Processing will begin shortly."
    
    model_config = ConfigDict(from_attributes=True)
