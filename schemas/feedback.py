from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum as PyEnum


class FeedbackCategoryEnum(str, PyEnum):
    BUG = "bug"
    FEATURE = "feature"
    UI = "ui"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class FeedbackStatusEnum(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class FeedbackCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000, description="Feedback content")
    category: FeedbackCategoryEnum = Field(default=FeedbackCategoryEnum.OTHER, description="Feedback category")


class FeedbackUpdate(BaseModel):
    status: Optional[FeedbackStatusEnum] = None
    developer_response: Optional[str] = Field(default=None, max_length=2000)


class FeedbackUserResponse(BaseModel):
    """Simplified user info for feedback responses"""
    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    content: str
    category: str
    status: str
    vote_count: int
    developer_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[FeedbackUserResponse] = None
    has_voted: bool = False  # Whether current user has voted
    model_config = ConfigDict(from_attributes=True)


class FeedbackListResponse(BaseModel):
    """Paginated feedback list response"""
    items: list[FeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FeedbackVoteResponse(BaseModel):
    has_voted: bool
    vote_count: int


class FeedbackStats(BaseModel):
    """Feedback statistics"""
    total_count: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    top_voted: list[dict]  # Top voted feedbacks (id, content preview, vote_count)


class FeedbackSubmissionStatus(BaseModel):
    """Response for checking if user can submit feedback today"""
    can_submit: bool
    next_submission_at: Optional[datetime] = None
    message: str
