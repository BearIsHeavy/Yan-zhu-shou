"""
Pydantic schemas for Mistake Notebook API.

Defines request/response models for wrong question operations.
Wrong questions are derived from user_question_logs where is_correct = False.

Database Schema Reference: docs/数据库设计.sql
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class QuestionStatusEnum(str, Enum):
    """
    Status of a wrong question in the notebook.
    
    Derived from user_question_logs:
    - new: Recently answered incorrectly
    - reviewing: Actively being reviewed
    - mastered: Marked as mastered by user
    - removed: No longer relevant
    """
    NEW = "new"
    REVIEWING = "reviewing"
    MASTERED = "mastered"
    REMOVED = "removed"


class QuestionTypeEnum(str, Enum):
    """
    Type of question from qb_questions.qus_type.
    
    - 0: Essay/解答
    - 1: Single Choice/单选
    - 2: Multiple Choice/多选
    - 3: Fill in Blank/填空
    """
    ESSAY = "essay"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"


class ErrorReasonEnum(str, Enum):
    """
    Reason for making a mistake.
    
    User-categorized error reasons for analysis.
    """
    CARELESS = "careless"
    CONCEPT_GAP = "concept_gap"
    LOGIC_ERROR = "logic_error"
    TIME_LIMIT = "time_limit"
    OTHER = "other"


# ==========================================
# WRONG QUESTION SCHEMAS
# ==========================================

class WrongQuestionBase(BaseModel):
    """
    Base schema for wrong question.
    
    Combines data from user_question_logs and qb_questions tables.
    """
    question_no: int = Field(..., description="Question ID from qb_questions")
    category: str = Field(..., description="Subject/topic category")
    stem: str = Field(..., description="Question stem/summary")
    question_type: QuestionTypeEnum = Field(..., description="Type of question")
    source_info: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Source of the question (e.g., question bank name)"
    )
    difficulty_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Difficulty level 1-5"
    )


class WrongQuestionResponse(WrongQuestionBase):
    """
    Schema for wrong question response.
    
    Combines data from user_question_logs and qb_questions tables.
    """
    log_id: int = Field(..., description="Log ID from user_question_logs")
    user_id: int = Field(..., description="User ID")
    user_answer: Optional[str] = Field(None, description="User's incorrect answer")
    correct_ans_summary: Optional[str] = Field(None, description="Correct answer summary")
    options: Optional[dict] = Field(None, description="Question options")
    error_reason_type: Optional[ErrorReasonEnum] = Field(None, description="Type of error made")
    error_reason_detail: Optional[str] = Field(None, description="Detailed analysis of the error")
    status: QuestionStatusEnum = Field(default=QuestionStatusEnum.NEW, description="Question status")
    mistake_count: int = Field(default=1, description="Number of times answered incorrectly")
    is_mastered: bool = Field(default=False, description="User marked as mastered")
    attempt_time: datetime = Field(..., description="Time of wrong attempt")
    created_at: datetime = Field(..., description="Question creation time")
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class WrongQuestionListResponse(BaseModel):
    """Schema for paginated list of wrong questions."""
    data: List[WrongQuestionResponse]
    total: int
    page: int
    size: int


class WrongQuestionUpdate(BaseModel):
    """Schema for updating a wrong question's metadata."""
    error_reason_type: Optional[ErrorReasonEnum] = Field(default=None)
    error_reason_detail: Optional[str] = Field(default=None)
    status: Optional[QuestionStatusEnum] = Field(default=None)
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=5)
    is_mastered: Optional[bool] = Field(default=None)


class WrongQuestionBatchUpdate(BaseModel):
    """Schema for batch updating wrong questions."""
    question_log_ids: List[int] = Field(..., description="List of user_question_logs IDs to update")
    is_mastered: bool = Field(..., description="New mastered status")


# ==========================================
# QUESTION BANK STATS SCHEMA
# ==========================================

class MistakeNotebookStats(BaseModel):
    """
    Statistics for the mistake notebook.
    
    Provides overview of wrong questions by status and category.
    """
    total_wrong: int = Field(..., description="Total wrong questions")
    new_count: int = Field(..., description="Questions with 'new' status")
    reviewing_count: int = Field(..., description="Questions with 'reviewing' status")
    mastered_count: int = Field(..., description="Questions marked as mastered")
    by_category: dict = Field(default_factory=dict, description="Count by category")
