from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/errors", tags=["Error Bank"])

@router.post("", response_model=schemas.ErrorRecordResponse, status_code=status.HTTP_201_CREATED)
def record_error(
    error_data: schemas.ErrorRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> models.ErrorRecord:
    question = db.query(models.Question).filter(models.Question.id == error_data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    new_error = models.ErrorRecord(
        user_id=current_user.id,
        question_id=error_data.question_id,
        selected_option=error_data.selected_option
    )
    db.add(new_error)
    db.commit()
    db.refresh(new_error)
    return new_error

@router.get("/me", response_model=list[schemas.ErrorRecordResponse])
def get_my_errors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    errors = db.query(models.ErrorRecord).filter(models.ErrorRecord.user_id == current_user.id).all()
    return errors