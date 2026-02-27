# errors.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db, engine
from ..dependencies import get_current_user

router = APIRouter(prefix="/errors", tags=["Error Bank"])


@router.post("", response_model=schemas.ErrorRecordResponse, status_code=status.HTTP_201_CREATED)
def record_error(
        error_data: schemas.ErrorRecordCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # 1. Verify the question exists in the main bank
    question = db.query(models.Question).filter(models.Question.id == error_data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 2. Get the dynamically generated table for THIS specific user
    UserErrorModel = models.get_user_error_table(current_user.id)

    # 3. Ensure the physical table actually exists in MySQL (creates it if it doesn't)
    UserErrorModel.__table__.create(bind=engine, checkfirst=True)

    # 4. Insert the record
    new_error = UserErrorModel(
        question_id=error_data.question_id,
        selected_option=error_data.selected_option
    )
    db.add(new_error)
    db.commit()
    db.refresh(new_error)
    return new_error


@router.get("/me", response_model=schemas.PaginatedErrorResponse)
def get_my_errors(
        # Strict typing: Page must be >= 1. Size must be <= 20.
        page: int = Query(1, ge=1, description="Page number (starts at 1)"),
        size: int = Query(20, ge=1, le=20, description="Items per page (max 20)"),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # 1. Get the dynamic model
    UserErrorModel = models.get_user_error_table(current_user.id)

    # Ensure table exists (in case they call GET before ever calling POST)
    UserErrorModel.__table__.create(bind=engine, checkfirst=True)

    # 2. Calculate pagination offset
    # If page=3, size=20 -> skip = (3-1)*20 = 40. It will fetch records 41-60.
    skip = (page - 1) * size

    # 3. Query the database
    total_errors = db.query(UserErrorModel).count()
    errors = db.query(UserErrorModel).offset(skip).limit(size).all()

    # 4. Return formatted data compatible with our new Pagination schema
    return {
        "data": errors,
        "total": total_errors,
        "page": page,
        "size": size
    }