from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


# ==================== QuestionBank Schemas ====================

class QuestionBankBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    is_public: bool = False
    description: Optional[str] = None


class QuestionBankCreate(QuestionBankBase):
    pass


class QuestionBankUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_public: Optional[bool] = None
    description: Optional[str] = None


class QuestionBankResponse(QuestionBankBase):
    bank_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== CSV/XML Question Import Schemas ====================

class QuestionImportItem(BaseModel):
    """Schema for importing a single question from CSV/XML"""
    category: str = Field(min_length=1, max_length=50)
    stem: str = Field(min_length=1)
    qus_type: int = Field(default=1, ge=0, le=3)
    options: Optional[Dict[str, Any]] = None
    correct_ans_summary: Optional[str] = None
    full_text: Optional[str] = None  # Full stem text for StemText
    image_url: Optional[str] = None
    full_answer: Optional[str] = None
    explanation: Optional[str] = None


class QuestionImportBatch(BaseModel):
    """Schema for batch question import"""
    questions: List[QuestionImportItem]


# ==================== QBQuestion Schemas ====================

class QBQuestionBase(BaseModel):
    bank_id: Optional[int] = None
    category: str = Field(min_length=1, max_length=50)
    stem: str = Field(min_length=1, max_length=255)
    qus_type: int = Field(default=1, ge=0, le=3)  # 0:Essay 1:Single 2:Multiple 3:Fill-in
    options: Dict[str, Any] = Field(default={"format": "JSON"})
    correct_ans_summary: Optional[str] = Field(default=None, max_length=255)
    is_public: bool = True


class QBQuestionCreate(QBQuestionBase):
    pass


class QBQuestionUpdate(BaseModel):
    bank_id: Optional[int] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    stem: Optional[str] = Field(default=None, min_length=1, max_length=255)
    qus_type: Optional[int] = Field(default=None, ge=0, le=3)
    options: Optional[Dict[str, Any]] = None
    correct_ans_summary: Optional[str] = Field(default=None, max_length=255)
    is_public: Optional[bool] = None


class QBQuestionResponse(QBQuestionBase):
    No: int
    correct_num: int = 0
    uncorrect_num: int = 0
    user_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Aliases for backward compatibility
QBQuestionItem = QBQuestionCreate
