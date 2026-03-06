# Add project root to sys.path for relative imports
# This allows the script to be run from any directory
import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import schemas
from database import get_db

router = APIRouter()

@router.post("/store_question")
async def store_question(
    question_infor: schemas.QBQuestionCreate,
    db: AsyncSession = Depends(get_db)
):
    stem_length = len(question_infor.stem)
    print(f"stem: {question_infor.stem}, stem_length: {stem_length}")
    return "True"

if __name__ == "__main__":
    question: schemas.QBQuestionCreate =schemas.QBQuestionCreate(
        bank_id=1,
        category='english',
        stem='who is best beautiful woman?',
        qus_type=1,
        options={"A": "mother", "B": "B"},
        correct_ans_summary='B',
        is_public=True
    )

    def store_question(
            question: schemas.QBQuestionCreate,
            db: AsyncSession = Depends(get_db)
    ):
        stem_length = len(question.stem)
        print(stem_length)
        return "True"
    store_question(question)