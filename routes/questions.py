import shutil
import json
from fastapi import Depends, File, UploadFile, HTTPException, status, Form
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

import models
import schemas
from database import get_db

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def get_byte_length(text: str) -> int:
    """Get byte length of UTF-8 encoded Text"""
    return len(text.encode('utf-8', text))

async def store_stem(
    db: AsyncSession,
    stem: schemas.StemTextItem,
):
      stem_record = models.StemText(
          question_no=stem.question_no,
          full_text=stem.full_text
      )
      db.add(stem_record)

@router.post("/file")
async def get_file_question_information(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # 检查文件
    if not file.filename:
         raise HTTPException(status_code=400, detail="No filename provided")
    # 检查文件后缀是否符合要求
    if not file.filename.endswith((".xls", ".xlsx", ".csv")):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid file type"
        )

    # 将上传文件保存到本地
    file_location = UPLOAD_DIR / file.filename
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return {"detail": "success"}


@router.post("/question")
async def store_question(
        question_data: schemas.QBQuestionItem,
        db: AsyncSession = Depends(get_db)
):

    # 检查题干是否超过了256个字符
    try:
        if get_byte_length(question_data.stem) > 256:
            stem_text = question_data.stem
            options_json = (
                json.dumps(question_data.options)
                if isinstance(question_data.options, dict)
                else question_data.options
            )
            item = models.QBQuestion(
                bank_id=question_data.bank_id,
                category=question_data.category,
                stem=question_data.stem,  # May be truncated later if offloaded
                qus_type=question_data.qus_type,
                options=options_json,
                correct_ans_summary=question_data.correct_ans_summary,
                is_public=question_data.is_public,
                user_id=1  # Replace with actual current user
            )
            db.add(item)
            await db.flush()
            stem_item = schemas.StemTextItem(
                question_no=item.No,
                full_text=stem_text
            )
            await store_stem(db, stem_item)
            await db.commit()
        return {"No": item.No}
    except Exception as e:
        raise e


if __name__ == "__main__":
    question: schemas.QBQuestionCreate = schemas.QBQuestionCreate(
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
