from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================

class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6)
    phone: Optional[str] = Field(default=None, min_length=11, max_length=20)
    gender: Optional[int] = Field(default=0, ge=0, le=2, title="性别", description="0:Unknown 1:Male 2:Female")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: int
    email: str
    name: str
    phone: Optional[str] = None
    gender: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, min_length=11, max_length=20)
    gender: Optional[int] = Field(default=None, ge=0, le=2)


# ==================== Token Schemas ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


# ==================== QuestionBank Schemas ====================

class QuestionBankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    is_public: bool = False
    description: Optional[str] = None


class QuestionBankResponse(BaseModel):
    bank_id: int
    name: str
    user_id: int
    is_public: bool
    description: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class QuestionBankUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_public: Optional[bool] = None
    description: Optional[str] = None


# ==================== QBQuestion Schemas ====================

class QBQuestionCreate(BaseModel):
    bank_id: Optional[int] = None
    category: str = Field(min_length=1, max_length=50)
    stem: str = Field(min_length=1, max_length=255)
    qus_type: int = Field(default=1, ge=0, le=3)  # 0:解答 1:单选 2:多选 3:填空
    options: dict[str, str] = Field(default={"format": "JSON"})# JSON string
    correct_ans_summary: Optional[str] = Field(default=None, max_length=255)
    is_public: bool = True


class QBQuestionResponse(BaseModel):
    No: int
    bank_id: Optional[int] = None
    category: str
    stem: str
    qus_type: int
    options: Optional[str] = None
    correct_ans_summary: Optional[str] = None
    correct_num: int = 0
    uncorrect_num: int = 0
    is_public: bool
    user_id: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class QBQuestionUpdate(BaseModel):
    bank_id: Optional[int] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    stem: Optional[str] = Field(default=None, min_length=1, max_length=255)
    qus_type: Optional[int] = Field(default=None, ge=0, le=3)
    options: Optional[str] = None
    correct_ans_summary: Optional[str] = Field(default=None, max_length=255)
    is_public: Optional[bool] = None


# ==================== StemText Schemas ====================

class StemTextCreate(BaseModel):
    question_no: int
    full_text: str
    image_url: Optional[str] = Field(default=None, max_length=255)


class StemTextResponse(BaseModel):
    id: int
    question_no: int
    full_text: str
    image_url: Optional[str] = None
    model_config = {"from_attributes": True}


class StemTextUpdate(BaseModel):
    full_text: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=255)


# ==================== AnswerText Schemas ====================

class AnswerTextCreate(BaseModel):
    question_no: int
    full_answer: str
    explanation: Optional[str] = None


class AnswerTextResponse(BaseModel):
    id: int
    question_no: int
    full_answer: str
    explanation: Optional[str] = None
    model_config = {"from_attributes": True}


class AnswerTextUpdate(BaseModel):
    full_answer: Optional[str] = None
    explanation: Optional[str] = None


# ==================== UserQuestionLog Schemas ====================

class UserQuestionLogCreate(BaseModel):
    user_id: int
    question_no: int
    user_answer: Optional[str] = None
    is_correct: bool
    is_mastered: bool = False


class UserQuestionLogResponse(BaseModel):
    id: int
    user_id: int
    question_no: int
    user_answer: Optional[str] = None
    is_correct: bool
    attempt_time: datetime
    is_mastered: bool = False
    model_config = {"from_attributes": True}


class UserQuestionLogUpdate(BaseModel):
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    is_mastered: Optional[bool] = None


# ==================== SecurityLog Schemas ====================

class SecurityLogCreate(BaseModel):
    user_id: int
    ip_address: str = Field(max_length=45)
    device_info: Optional[str] = Field(default=None, max_length=255)
    action_type: Optional[str] = Field(default=None, max_length=50)


class SecurityLogResponse(BaseModel):
    id: int
    user_id: int
    ip_address: str
    device_info: Optional[str] = None
    action_type: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
