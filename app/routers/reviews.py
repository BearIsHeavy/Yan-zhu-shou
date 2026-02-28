# app/routers/reviews.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def calculate_next_review_date(mistake_count: int, result: models.ReviewResultEnum) -> date:
    """
    Implements a basic Ebbinghaus spacing interval.
    If the user gets it wrong, reset the interval.
    If correct, increase the interval based on how many times they've reviewed it.
    """
    today: date = datetime.now(timezone.utc).date()

    if result == models.ReviewResultEnum.wrong:
        # Review again tomorrow if wrong
        return today + timedelta(days=1)

    # Standard Ebbinghaus intervals (in days): 1, 2, 4, 7, 15, 30
    intervals: list[int] = [1, 2, 4, 7, 15, 30]

    # The fewer mistakes (and more corrects), the further out it gets pushed.
    index: int = max(0, min(len(intervals) - 1, 5 - mistake_count))
    days_to_add: int = intervals[index]

    return today + timedelta(days=days_to_add)


@router.post("", response_model=schemas.ReviewRecordResponse, status_code=status.HTTP_201_CREATED)
def submit_review(
        review_in: schemas.ReviewRecordCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> models.ReviewRecord:
    question: Optional[models.WrongQuestion] = db.query(models.WrongQuestion).filter(
        models.WrongQuestion.id == review_in.question_id,
        models.WrongQuestion.user_id == current_user.id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # 1. Create the review record
    record = models.ReviewRecord(
        question_id=review_in.question_id,
        user_id=current_user.id,
        result=review_in.result,
        time_spent_seconds=review_in.time_spent_seconds,
        notes=review_in.notes
    )
    db.add(record)

    # 2. Update the main question statistics and Ebbinghaus scheduling
    if review_in.result == models.ReviewResultEnum.wrong:
        question.mistake_count += 1
        question.status = models.QuestionStatusEnum.reviewing
    elif review_in.result == models.ReviewResultEnum.correct:
        # Optionally decrease mistake count over time or mark as mastered
        # if it's been correct many times. For MVP, we just let Ebbinghaus push the date.
        pass

    question.last_reviewed_at = datetime.now(timezone.utc)
    question.next_review_date = calculate_next_review_date(question.mistake_count, review_in.result)

    db.commit()
    db.refresh(record)

    return record