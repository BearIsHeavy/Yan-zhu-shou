from fastapi import APIRouter, Depends
from .. import models, schemas
from ..dependencies import get_current_user

# The prefix automatically applies "/users" to all routes in this file
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user