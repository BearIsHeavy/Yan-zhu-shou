"""
Pydantic schemas for Knowledge module.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class KnowledgePointBase(BaseModel):
    """Base schema for knowledge point."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Knowledge point name")
    subject: str = Field(..., min_length=1, max_length=100, description="Subject area")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level 1-5")
    description: Optional[str] = Field(None, description="Detailed description")


class KnowledgePointCreate(KnowledgePointBase):
    """Schema for creating a knowledge point."""
    
    parent_id: Optional[int] = Field(None, description="Parent knowledge point ID")


class KnowledgePointUpdate(BaseModel):
    """Schema for updating a knowledge point."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None


class KnowledgePointResponse(KnowledgePointBase):
    """Response schema for knowledge point."""
    
    id: int
    parent_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    children_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgePointTreeResponse(KnowledgePointResponse):
    """Response schema for knowledge point with children."""
    
    children: List["KnowledgePointTreeResponse"] = Field(default_factory=list)


class QuestionKnowledgeBase(BaseModel):
    """Base schema for question-knowledge association."""
    
    question_no: int = Field(..., description="Question ID")
    knowledge_id: int = Field(..., description="Knowledge point ID")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Association weight")


class QuestionKnowledgeCreate(QuestionKnowledgeBase):
    """Schema for creating question-knowledge association."""
    pass


class QuestionKnowledgeResponse(QuestionKnowledgeBase):
    """Response schema for question-knowledge association."""
    
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Rebuild recursive model
KnowledgePointTreeResponse.model_rebuild()
