from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ==================== UserQuestionLog Schemas ====================

class UserQuestionLogBase(BaseModel):
    user_id: int
    question_no: int
    user_answer: Optional[str] = None
    is_correct: bool
    is_mastered: bool = False


class UserQuestionLogCreate(UserQuestionLogBase):
    pass


class UserQuestionLogUpdate(BaseModel):
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    is_mastered: Optional[bool] = None


class UserQuestionLogResponse(UserQuestionLogBase):
    id: int
    attempt_time: datetime
    model_config = ConfigDict(from_attributes=True)


# ==================== SecurityLog Schemas ====================

class SecurityLogBase(BaseModel):
    user_id: int
    ip_address: str = Field(max_length=45)
    device_info: Optional[str] = Field(default=None, max_length=255)
    action_type: Optional[str] = Field(default=None, max_length=50)


class SecurityLogCreate(SecurityLogBase):
    pass


class SecurityLogUpdate(BaseModel):
    ip_address: Optional[str] = None
    device_info: Optional[str] = Field(default=None, max_length=255)
    action_type: Optional[str] = Field(default=None, max_length=50)


class SecurityLogResponse(SecurityLogBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
