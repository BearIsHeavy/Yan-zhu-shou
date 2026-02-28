# app/routers/wrong_questions.py
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/wrong-questions", tags=["Wrong Questions"])


@router.post("", response_model=schemas.WrongQuestionResponse, status_code=status.HTTP_201_CREATED)
def create_wrong_question(
        question_in: schemas.WrongQuestionCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> models.WrongQuestion:
    # Verify subject exists
    subject: Optional[models.Subject] = db.query(models.Subject).filter(
        models.Subject.id == question_in.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    db_question = models.WrongQuestion(
        user_id=current_user.id,
        subject_id=question_in.subject_id,
        question_text=question_in.question_text,
        question_images=question_in.question_images,
        options_json=question_in.options_json,
        correct_answer=question_in.correct_answer,
        user_answer=question_in.user_answer,
        question_type=question_in.question_type,
        source_info=question_in.source_info,
        error_reason_type=question_in.error_reason_type,
        error_reason_detail=question_in.error_reason_detail,
        difficulty_level=question_in.difficulty_level,
        status=models.QuestionStatusEnum.new
    )

    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    # Link knowledge points if provided
    if question_in.knowledge_point_ids:
        for kp_id in question_in.knowledge_point_ids:
            kp_map = models.QuestionKnowledgeMap(
                question_id=db_question.id,
                kp_id=kp_id
            )
            db.add(kp_map)
        db.commit()
        db.refresh(db_question)

    return db_question


@router.get("", response_model=schemas.PaginatedWrongQuestionResponse)
def get_wrong_questions(
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=50, description="Items per page"),
        subject_id: Optional[int] = Query(None, description="Filter by subject"),
        status_filter: Optional[models.QuestionStatusEnum] = Query(None, alias="status",
                                                                   description="Filter by status"),
        needs_review: Optional[bool] = Query(False, description="Fetch questions due for review today"),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> dict[str, Any]:
    query = db.query(models.WrongQuestion).filter(models.WrongQuestion.user_id == current_user.id)

    if subject_id is not None:
        query = query.filter(models.WrongQuestion.subject_id == subject_id)
    if status_filter is not None:
        query = query.filter(models.WrongQuestion.status == status_filter)

    # Ebbinghaus Review Filter
    if needs_review:
        today: date = datetime.now(timezone.utc).date()
        query = query.filter(
            models.WrongQuestion.next_review_date != None,
            models.WrongQuestion.next_review_date <= today,
            models.WrongQuestion.status != models.QuestionStatusEnum.mastered
        )

    total: int = query.count()
    skip: int = (page - 1) * size
    questions = query.order_by(models.WrongQuestion.created_at.desc()).offset(skip).limit(size).all()

    return {
        "data": questions,
        "total": total,
        "page": page,
        "size": size
    }


@router.patch("/{question_id}/status", response_model=schemas.WrongQuestionResponse)
def update_question_status(
        question_id: int,
        new_status: models.QuestionStatusEnum,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> models.WrongQuestion:
    question: Optional[models.WrongQuestion] = db.query(models.WrongQuestion).filter(
        models.WrongQuestion.id == question_id,
        models.WrongQuestion.user_id == current_user.id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = new_status
    db.commit()
    db.refresh(question)
    return question