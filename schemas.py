# schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address", examples=["user@example.com"])
    # Added max_length=64 to strictly validate at the API gateway
    password: str = Field(..., min_length=8, max_length=64, description="8 to 64 characters", examples=["StrongPass!123"])

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str = Field(..., description="The JWT access token string.")
    token_type: str = Field(..., description="Type of token (e.g., bearer).")