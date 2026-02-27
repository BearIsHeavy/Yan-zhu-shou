# schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address", examples=["user@example.com"])
    # Added max_length=64 to strictly validate at the API gateway
    password: str = Field(..., min_length=8, max_length=64, description="8 to 64 characters",
                          examples=["StrongPass!123"])


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str = Field(..., description="The JWT access token string.")
    token_type: str = Field(..., description="Type of token (e.g., bearer).")


# --- NEW QUESTION SCHEMAS ---

class QuestionBase(BaseModel):
    stem: str = Field(..., description="The main question text")
    options: list[str] = Field(..., description="List of possible options")
    correct_answer: str | None = None
    explanation: str | None = None
    knowledge_points: str | None = None


class QuestionResponse(QuestionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- NEW ERROR RECORD SCHEMAS ---

class ErrorRecordCreate(BaseModel):
    question_id: int = Field(..., description="The ID of the question the user answered incorrectly.")
    selected_option: str = Field(..., description="The wrong option the user selected.")


class ErrorRecordResponse(BaseModel):
    id: int
    question_id: int
    selected_option: str
    question: QuestionResponse | None = Field(None, description="The full details of the associated question.")

    model_config = ConfigDict(from_attributes=True)