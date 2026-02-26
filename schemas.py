from pydantic import BaseModel, EmailStr, ConfigDict, Field

# Schema for incoming registration requests (Frontend -> Backend)
class UserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="A valid email address for the new user.",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="A strong password with a minimum of 8 characters.",
        examples=["StrongPassword123!"]
    )

# Schema for outgoing user data responses (Backend -> Frontend)
class UserResponse(BaseModel):
    id: int = Field(..., description="The unique database ID of the user.")
    email: EmailStr = Field(..., description="The registered email address.")
    is_active: bool = Field(..., description="Whether the user account is currently active.")

    # Allows Pydantic to read data directly from the SQLAlchemy ORM model
    model_config = ConfigDict(from_attributes=True)