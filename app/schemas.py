# app/schemas.py
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from .models import QuestionTypeEnum, ErrorReasonEnum, QuestionStatusEnum, ReviewResultEnum


# --- USER SCHEMAS ---

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr | None = Field(None, description="Optional user email")
    password: str = Field(..., min_length=8, max_length=64, description="8 to 64 characters")


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# --- SUBJECT & KNOWLEDGE POINT SCHEMAS ---

class SubjectResponse(BaseModel):
    id: int
    name: str
    icon_url: str | None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class KnowledgePointResponse(BaseModel):
    id: int
    subject_id: int
    parent_id: int | None
    name: str
    full_path: str | None
    model_config = ConfigDict(from_attributes=True)


# --- WRONG QUESTION SCHEMAS ---

class WrongQuestionCreate(BaseModel):
    subject_id: int = Field(..., description="ID of the subject (e.g., Math)")
    question_text: str = Field(..., description="The main question text or OCR result")
    question_images: list[str] | None = Field(None, description="List of image URLs (OSS/S3)")
    options_json: list[str] | dict | None = Field(None, description="Options if it's a multiple choice question")
    correct_answer: str | None = Field(None, description="The correct answer")
    user_answer: str | None = Field(None, description="The answer the user originally provided")

    question_type: QuestionTypeEnum = Field(default=QuestionTypeEnum.choice)
    source_info: str | None = Field(None, description="e.g., '2025 Midterm Exam'")

    error_reason_type: ErrorReasonEnum | None = Field(None)
    error_reason_detail: str | None = Field(None)
    difficulty_level: int = Field(default=1, ge=1, le=5, description="Self-rated difficulty 1-5")

    # Optional list of knowledge point IDs to tag this question with
    knowledge_point_ids: list[int] = Field(default_factory=list)


class WrongQuestionResponse(BaseModel):
    id: int
    subject_id: int
    question_text: str
    question_images: list[str] | None
    options_json: list[str] | dict | None
    correct_answer: str | None
    user_answer: str | None

    question_type: QuestionTypeEnum
    source_info: str | None
    error_reason_type: ErrorReasonEnum | None
    error_reason_detail: str | None

    status: QuestionStatusEnum
    difficulty_level: int
    mistake_count: int
    last_reviewed_at: datetime | None
    next_review_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- REVIEW RECORD SCHEMAS ---

class ReviewRecordCreate(BaseModel):
    question_id: int
    result: ReviewResultEnum
    time_spent_seconds: int | None = Field(None, description="How long the user took to answer in seconds")
    notes: str | None = Field(None, description="Any personal notes taken during the review")


class ReviewRecordResponse(BaseModel):
    id: int
    question_id: int
    review_date: datetime
    result: ReviewResultEnum | None
    time_spent_seconds: int | None
    notes: str | None
    model_config = ConfigDict(from_attributes=True)


# --- PAGINATION SCHEMAS ---

class PaginatedWrongQuestionResponse(BaseModel):
    data: list[WrongQuestionResponse]
    total: int
    page: int
    size: int