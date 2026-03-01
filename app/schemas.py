# filepath: app/schemas.py
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=64, description="Maximum length 64 characters")
    name: str = Field(..., max_length=50)
    phone: str | None = None
    gender: int | None = Field(default=0, description="0:Unknown 1:Male 2:Female")


class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    name: str
    phone: str | None
    gender: int | None
    created_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# --- QUESTION BANK SCHEMAS ---
class QuestionBankCreate(BaseModel):
    name: str = Field(..., max_length=100)
    is_public: bool = False
    description: str | None = None


class QuestionBankResponse(QuestionBankCreate):
    bank_id: int
    user_id: int
    created_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


# --- QUESTION SCHEMAS ---
class QbQuestionCreate(BaseModel):
    bank_id: int | None = None
    category: str = Field(..., max_length=50)
    stem: str = Field(..., max_length=255, description="Question summary")
    qus_type: int = Field(default=1, description="0:Solution 1:Single 2:Multi 3:Fill")
    options: Any | None = None
    correct_ans_summary: str | None = None
    is_public: bool = True

    # Detailed text mapping for related tables
    stem_full_text: str
    image_url: str | None = None
    full_answer: str
    explanation: str | None = None


class StemTextResponse(BaseModel):
    full_text: str
    image_url: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AnswerTextResponse(BaseModel):
    full_answer: str
    explanation: str | None = None
    model_config = ConfigDict(from_attributes=True)


class QbQuestionResponse(BaseModel):
    No: int
    bank_id: int | None
    category: str
    stem: str
    qus_type: int
    options: Any | None
    correct_ans_summary: str | None
    correct_num: int
    uncorrect_num: int
    is_public: bool
    user_id: int | None
    created_at: datetime | None

    # Nested related relationships
    stem_text: StemTextResponse | None = None
    answer_text: AnswerTextResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# --- LOG SCHEMAS ---
class UserQuestionLogCreate(BaseModel):
    question_no: int
    user_answer: str | None = None
    is_correct: bool
    is_mastered: bool = False


class UserQuestionLogResponse(UserQuestionLogCreate):
    id: int
    user_id: int
    attempt_time: datetime | None
    model_config = ConfigDict(from_attributes=True)