from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Registration
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6)

    def __repr__(self):
        return f"<UserRegister={self.email}, username={self.username}, password={self.password})>"

# Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    def __repr__(self):
        return f"<UserLogin={self.email}, password={self.password}>"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    def __repr__(self):
        return f"<Token={self.access_token}, token_type={self.token_type}>"

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_activate: bool
    created_at: datetime
    model_config = {"from_attributes": True}
    def __repr__(self):
        return f"<UserResponse=({self.id}, email={self.emial}, username={self.username}, is_activate={self.is_activate})>"
