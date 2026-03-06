from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


# ==================== StemText Schemas ====================

class StemTextBase(BaseModel):
    full_text: str
    image_url: Optional[str] = Field(default=None, max_length=255)


class StemTextCreate(StemTextBase):
    question_no: int


class StemTextUpdate(BaseModel):
    full_text: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=255)


class StemTextResponse(StemTextBase):
    id: int
    question_no: int
    model_config = ConfigDict(from_attributes=True)


# Aliases for backward compatibility
StemTextItem = StemTextCreate


# ==================== AnswerText Schemas ====================

class AnswerTextBase(BaseModel):
    full_answer: str
    explanation: Optional[str] = None


class AnswerTextCreate(AnswerTextBase):
    question_no: int


class AnswerTextUpdate(BaseModel):
    full_answer: Optional[str] = None
    explanation: Optional[str] = None


class AnswerTextResponse(AnswerTextBase):
    id: int
    question_no: int
    model_config = ConfigDict(from_attributes=True)
