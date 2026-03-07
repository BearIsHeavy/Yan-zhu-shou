"""
FastAPI routes for Mistake Notebook feature.

Provides CRUD operations for wrong questions derived from user_question_logs
where is_correct = False.

The Mistake Notebook feature uses the existing user_question_logs table to track
wrong questions. When a user answers a question incorrectly (is_correct = False),
it automatically appears in their mistake notebook.

Database Schema Reference: docs/数据库设计.sql
"""

import json
from typing import Optional, List
from datetime import datetime
from fastapi import Depends, HTTPException, status, Query, APIRouter
from sqlalchemy import select, and_, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def map_question_type(qus_type: int) -> str:
    """Map qb_questions.qus_type integer to QuestionTypeEnum string."""
    type_map = {
        0: "essay",
        1: "single_choice",
        2: "multiple_choice",
        3: "fill_blank"
    }
    return type_map.get(qus_type, "essay")


def parse_options(options_str: Optional[str]) -> Optional[dict]:
    """Parse options JSON string from qb_questions."""
    if not options_str:
        return None
    try:
        return json.loads(options_str)
    except (json.JSONDecodeError, TypeError):
        return None


# ==========================================
# MISTAKE NOTEBOOK ENDPOINTS
# ==========================================

@router.get(
    "/mistake-notebook/questions",
    response_model=schemas.WrongQuestionListResponse,
    summary="Get wrong questions for current user"
)
async def get_wrong_questions(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category/subject"),
    status_filter: Optional[schemas.QuestionStatusEnum] = Query(
        None, 
        alias="status",
        description="Filter by status (new, reviewing, mastered, removed)"
    ),
    needs_review: Optional[bool] = Query(
        None, 
        description="If true, return questions not yet mastered"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get paginated list of wrong questions for the current user.
    
    Wrong questions are derived from user_question_logs where is_correct = False.
    The query joins with qb_questions to get full question details.
    
    - **page**: Page number (default: 1)
    - **size**: Items per page (default: 20, max: 100)
    - **category**: Optional filter by question category
    - **status**: Optional filter by status
    - **needs_review**: If true, returns questions that are not mastered
    
    Returns questions sorted by attempt_time descending (most recent first).
    """
    # Build base query - join user_question_logs with qb_questions
    query = (
        select(models.UserQuestionLog, models.QBQuestion, models.QuestionBank)
        .join(
            models.QBQuestion,
            models.UserQuestionLog.question_no == models.QBQuestion.No
        )
        .outerjoin(
            models.QuestionBank,
            models.QBQuestion.bank_id == models.QuestionBank.bank_id
        )
        .where(
            and_(
                models.UserQuestionLog.user_id == current_user.user_id,
                models.UserQuestionLog.is_correct == False  # Wrong answers only
            )
        )
    )
    
    # Apply category filter
    if category:
        query = query.where(models.QBQuestion.category == category)
    
    # Apply status filter (mapped to is_mastered field)
    if status_filter:
        if status_filter == schemas.QuestionStatusEnum.MASTERED:
            query = query.where(models.UserQuestionLog.is_mastered == True)
        elif status_filter == schemas.QuestionStatusEnum.NEW:
            query = query.where(
                and_(
                    models.UserQuestionLog.is_mastered == False,
                    models.UserQuestionLog.attempt_time >= func.date_sub(func.now(), interval=7)  # Recent
                )
            )
        elif status_filter == schemas.QuestionStatusEnum.REVIEWING:
            query = query.where(
                and_(
                    models.UserQuestionLog.is_mastered == False,
                    models.UserQuestionLog.attempt_time < func.date_sub(func.now(), interval=7)
                )
            )
    
    # Apply needs_review filter
    if needs_review:
        query = query.where(models.UserQuestionLog.is_mastered == False)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    offset = (page - 1) * size
    query = query.order_by(models.UserQuestionLog.attempt_time.desc()).offset(offset).limit(size)
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Build response
    questions = []
    for log, question, bank in rows:
        # Determine status based on is_mastered and attempt_time
        if log.is_mastered:
            q_status = schemas.QuestionStatusEnum.MASTERED
        else:
            days_since_attempt = (datetime.now() - log.attempt_time).days
            if days_since_attempt <= 7:
                q_status = schemas.QuestionStatusEnum.NEW
            else:
                q_status = schemas.QuestionStatusEnum.REVIEWING
        
        # Count mistakes for this question
        mistake_count_query = select(func.count()).where(
            and_(
                models.UserQuestionLog.user_id == current_user.user_id,
                models.UserQuestionLog.question_no == question.No,
                models.UserQuestionLog.is_correct == False
            )
        )
        mistake_count_result = await db.execute(mistake_count_query)
        mistake_count = mistake_count_result.scalar() or 0
        
        questions.append(
            schemas.WrongQuestionResponse(
                log_id=log.id,
                question_no=question.No,
                user_id=log.user_id,
                category=question.category,
                stem=question.stem,
                question_type=map_question_type(question.qus_type),
                source_info=bank.name if bank else None,
                difficulty_level=3,  # Default, can be customized
                user_answer=log.user_answer,
                correct_ans_summary=question.correct_ans_summary,
                options=parse_options(question.options),
                error_reason_type=None,  # Can be added with extended schema
                error_reason_detail=None,
                status=q_status,
                mistake_count=mistake_count,
                is_mastered=log.is_mastered,
                attempt_time=log.attempt_time,
                created_at=question.created_at
            )
        )
    
    return {
        "data": questions,
        "total": total,
        "page": page,
        "size": size
    }


@router.get(
    "/mistake-notebook/stats",
    response_model=schemas.MistakeNotebookStats,
    summary="Get mistake notebook statistics"
)
async def get_mistake_notebook_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get statistics for the current user's mistake notebook.
    
    Returns counts of wrong questions by status and category.
    """
    # Total wrong questions
    total_query = select(func.count()).where(
        and_(
            models.UserQuestionLog.user_id == current_user.user_id,
            models.UserQuestionLog.is_correct == False
        )
    )
    total_result = await db.execute(total_query)
    total_wrong = total_result.scalar() or 0
    
    # Mastered count
    mastered_query = select(func.count()).where(
        and_(
            models.UserQuestionLog.user_id == current_user.user_id,
            models.UserQuestionLog.is_correct == False,
            models.UserQuestionLog.is_mastered == True
        )
    )
    mastered_result = await db.execute(mastered_query)
    mastered_count = mastered_result.scalar() or 0
    
    # New count (wrong and not mastered, attempted within last 7 days)
    new_query = select(func.count()).where(
        and_(
            models.UserQuestionLog.user_id == current_user.user_id,
            models.UserQuestionLog.is_correct == False,
            models.UserQuestionLog.is_mastered == False,
            models.UserQuestionLog.attempt_time >= func.date_sub(func.now(), interval=7)
        )
    )
    new_result = await db.execute(new_query)
    new_count = new_result.scalar() or 0
    
    # Reviewing count (wrong, not mastered, attempted more than 7 days ago)
    reviewing_count = total_wrong - mastered_count - new_count
    
    # Count by category
    category_query = select(
        models.QBQuestion.category,
        func.count().label('count')
    ).join(
        models.UserQuestionLog,
        models.UserQuestionLog.question_no == models.QBQuestion.No
    ).where(
        and_(
            models.UserQuestionLog.user_id == current_user.user_id,
            models.UserQuestionLog.is_correct == False,
            models.UserQuestionLog.is_mastered == False
        )
    ).group_by(models.QBQuestion.category)
    
    category_result = await db.execute(category_query)
    by_category = {row.category: row.count for row in category_result}
    
    return {
        "total_wrong": total_wrong,
        "new_count": new_count,
        "reviewing_count": reviewing_count,
        "mastered_count": mastered_count,
        "by_category": by_category
    }


@router.put(
    "/mistake-notebook/questions/{log_id}/status",
    response_model=schemas.WrongQuestionResponse,
    summary="Update wrong question status"
)
async def update_wrong_question_status(
    log_id: int,
    status_update: schemas.WrongQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the status/metadata of a wrong question.
    
    This updates the user_question_logs record to mark a question as mastered
    or update error analysis information.
    
    - **log_id**: ID of the user_question_logs record
    - **is_mastered**: Mark the question as mastered
    - **error_reason_type**: Type of error made
    - **error_reason_detail**: Detailed analysis
    """
    # Get the log entry
    result = await db.execute(
        select(models.UserQuestionLog, models.QBQuestion)
        .join(
            models.QBQuestion,
            models.UserQuestionLog.question_no == models.QBQuestion.No
        )
        .where(
            and_(
                models.UserQuestionLog.id == log_id,
                models.UserQuestionLog.user_id == current_user.user_id
            )
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wrong question log {log_id} not found or you don't have access."
        )
    
    log, question = row
    
    # Update fields
    if status_update.is_mastered is not None:
        log.is_mastered = status_update.is_mastered
    
    # Note: error_reason_type and error_reason_detail would need a separate table
    # or JSON column in user_question_logs for full implementation
    
    await db.commit()
    await db.refresh(log)
    
    # Determine status
    if log.is_mastered:
        q_status = schemas.QuestionStatusEnum.MASTERED
    else:
        days_since_attempt = (datetime.now() - log.attempt_time).days
        q_status = schemas.QuestionStatusEnum.NEW if days_since_attempt <= 7 else schemas.QuestionStatusEnum.REVIEWING
    
    # Count mistakes
    mistake_count_query = select(func.count()).where(
        and_(
            models.UserQuestionLog.user_id == current_user.user_id,
            models.UserQuestionLog.question_no == question.No,
            models.UserQuestionLog.is_correct == False
        )
    )
    mistake_count_result = await db.execute(mistake_count_query)
    mistake_count = mistake_count_result.scalar() or 0
    
    return schemas.WrongQuestionResponse(
        log_id=log.id,
        question_no=question.No,
        user_id=log.user_id,
        category=question.category,
        stem=question.stem,
        question_type=map_question_type(question.qus_type),
        source_info=None,
        difficulty_level=3,
        user_answer=log.user_answer,
        correct_ans_summary=question.correct_ans_summary,
        options=parse_options(question.options),
        error_reason_type=None,
        error_reason_detail=None,
        status=q_status,
        mistake_count=mistake_count,
        is_mastered=log.is_mastered,
        attempt_time=log.attempt_time,
        created_at=question.created_at
    )


@router.post(
    "/mistake-notebook/questions/{log_id}/master",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark wrong question as mastered"
)
async def mark_question_as_mastered(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Mark a wrong question as mastered.
    
    This is a convenience endpoint that sets is_mastered = True for the
    specified user_question_logs record.
    """
    result = await db.execute(
        select(models.UserQuestionLog).where(
            and_(
                models.UserQuestionLog.id == log_id,
                models.UserQuestionLog.user_id == current_user.user_id
            )
        )
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wrong question log {log_id} not found or you don't have access."
        )
    
    log.is_mastered = True
    await db.commit()
    
    return None


@router.post(
    "/mistake-notebook/questions/{log_id}/unmaster",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark wrong question as not mastered"
)
async def mark_question_as_unmastered(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Mark a wrong question as not mastered (needs review).
    
    This is a convenience endpoint that sets is_mastered = False for the
    specified user_question_logs record.
    """
    result = await db.execute(
        select(models.UserQuestionLog).where(
            and_(
                models.UserQuestionLog.id == log_id,
                models.UserQuestionLog.user_id == current_user.user_id
            )
        )
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wrong question log {log_id} not found or you don't have access."
        )
    
    log.is_mastered = False
    await db.commit()
    
    return None


@router.delete(
    "/mistake-notebook/questions/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove wrong question from notebook"
)
async def remove_wrong_question(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Remove a wrong question from the notebook.
    
    This deletes the user_question_logs record. The actual question
    in qb_questions is not deleted.
    """
    result = await db.execute(
        select(models.UserQuestionLog).where(
            and_(
                models.UserQuestionLog.id == log_id,
                models.UserQuestionLog.user_id == current_user.user_id
            )
        )
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wrong question log {log_id} not found or you don't have access."
        )
    
    await db.delete(log)
    await db.commit()
    
    return None


@router.post(
    "/mistake-notebook/questions/batch-update",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Batch update wrong questions"
)
async def batch_update_wrong_questions(
    update_data: schemas.WrongQuestionBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Batch update multiple wrong questions.
    
    Currently supports batch marking questions as mastered/not mastered.
    
    - **question_log_ids**: List of user_question_logs IDs to update
    - **is_mastered**: New mastered status for all specified questions
    """
    # Update all specified logs
    await db.execute(
        models.UserQuestionLog.__table__.update()
        .where(
            and_(
                models.UserQuestionLog.id.in_(update_data.question_log_ids),
                models.UserQuestionLog.user_id == current_user.user_id
            )
        )
        .values(is_mastered=update_data.is_mastered)
    )
    
    await db.commit()
    
    return None
