from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models
import schemas
from database import get_db

router = APIRouter()

@router.post("/book", response_model=schemas.QuestionBankResponse)
async def post_question(
    infor: schemas.QuestionBankCreate,
    db: AsyncSession = Depends(get_db)
):
    """store book information"""
    try:
        result = await db.execute(select(models.QuestionBank).where(models.QuestionBank.name == infor.name))
        existing_book = result.scalar_one_or_none()
    except MultipleResultsFound as e:
        return f"have a error: {e}"

    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="already this book"
        )

    # store this book information to database
    book_infor = models.QuestionBank(
        **infor.model_dump(),
        user_id=1
    )
    db.add(book_infor)
    await db.flush()
    await db.refresh(book_infor)
    return book_infor