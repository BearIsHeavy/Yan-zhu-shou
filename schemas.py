from pydantic import BaseModel, EmailStr, ConfigDict

# What we expect the frontend to send when registering
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# What we send back to the frontend (notice we omit the password!)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    # This tells Pydantic it can read data directly from the SQLAlchemy User object
    model_config = ConfigDict(from_attributes=True)