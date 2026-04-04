from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=list[schemas.QuestionBankResponse])
async def get_question_banks(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all question banks owned by the current user."""
    result = await db.execute(
        select(models.QuestionBank)
        .where(models.QuestionBank.user_id == current_user.user_id)
        .order_by(models.QuestionBank.created_at.desc())
    )
    question_banks = result.scalars().all()
    return question_banks


@router.get("/{bank_id}", response_model=schemas.QuestionBankResponse)
async def get_question_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific question bank by ID (must belong to current user)."""
    result = await db.execute(
        select(models.QuestionBank)
        .where(
            and_(
                models.QuestionBank.bank_id == bank_id,
                models.QuestionBank.user_id == current_user.user_id
            )
        )
    )
    question_bank = result.scalar_one_or_none()
    
    if not question_bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question bank not found or you don't have access."
        )
    
    return question_bank


@router.get("/{bank_id}/questions", response_model=list[schemas.QBQuestionResponse])
async def get_question_bank_questions(
    bank_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all questions from a specific question bank."""
    # First verify the bank belongs to the user
    bank_result = await db.execute(
        select(models.QuestionBank)
        .where(
            and_(
                models.QuestionBank.bank_id == bank_id,
                models.QuestionBank.user_id == current_user.user_id
            )
        )
    )
    question_bank = bank_result.scalar_one_or_none()
    
    if not question_bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question bank not found or you don't have access."
        )
    
    # Get questions with pagination
    result = await db.execute(
        select(models.QBQuestion)
        .where(models.QBQuestion.bank_id == bank_id)
        .offset(skip)
        .limit(limit)
        .order_by(models.QBQuestion.No.desc())
    )
    questions = result.scalars().all()
    
    # Parse options for response
    response_questions = []
    for q in questions:
        q_dict = q.__dict__.copy()
        if q.options and isinstance(q.options, str):
            try:
                q_dict['options'] = __import__('json').loads(q.options)
            except Exception:
                q_dict['options'] = {"format": "JSON"}
        
        response_questions.append(schemas.QBQuestionResponse(**q_dict))
    
    return response_questions


@router.delete("/{bank_id}")
async def delete_question_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a question bank and all its questions."""
    # First verify the bank belongs to the user
    result = await db.execute(
        select(models.QuestionBank)
        .where(
            and_(
                models.QuestionBank.bank_id == bank_id,
                models.QuestionBank.user_id == current_user.user_id
            )
        )
    )
    question_bank = result.scalar_one_or_none()
    
    if not question_bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question bank not found or you don't have access."
        )
    
    await db.delete(question_bank)
    await db.commit()
    
    return {"detail": f"Question bank '{question_bank.name}' deleted successfully."}


@router.post("/book", response_model=schemas.QuestionBankResponse)
async def post_question(
    infor: schemas.QuestionBankCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new question bank."""
    try:
        result = await db.execute(select(models.QuestionBank).where(models.QuestionBank.name == infor.name))
        existing_book = result.scalar_one_or_none()
    except MultipleResultsFound as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: duplicate question bank name '{infor.name}' with multiple entries."
        ) from e

    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="already this book"
        )

    # store this book information to database
    book_infor = models.QuestionBank(
        **infor.model_dump(),
        user_id=current_user.user_id
    )
    db.add(book_infor)
    await db.flush()
    await db.refresh(book_infor)
    await db.commit()  # Commit the transaction
    return book_infor