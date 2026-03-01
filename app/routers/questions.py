# filepath: app/routers/questions.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io
import json

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/upload", summary="Upload Questions via CSV")
async def upload_questions(
        file: UploadFile = File(...),
        bank_id: int | None = None,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> dict[str, int | str]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV is supported.")

    contents = await file.read()
    decoded_content = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded_content))
    valid_count = 0

    try:
        for row in reader:
            options_raw = row.get("options")
            parsed_options = None
            if options_raw:
                try:
                    parsed_options = json.loads(options_raw)
                except json.JSONDecodeError:
                    parsed_options = []

            # 1. Main Question Table
            db_question = models.QbQuestion(
                bank_id=bank_id,
                user_id=current_user.user_id,
                category=row.get('category', 'General'),
                stem=row.get('stem', 'No Summary'),
                qus_type=int(row.get('qus_type', 1)),
                options=parsed_options,
                correct_ans_summary=row.get('correct_ans_summary', '')
            )
            db.add(db_question)
            db.flush()  # Flush to get db_question.No populated

            # 2. Stem Text Details
            db_stem = models.StemText(
                question_no=db_question.No,
                full_text=row.get('stem_full_text', ''),
                image_url=row.get('image_url')
            )
            db.add(db_stem)

            # 3. Answer Text Details
            db_answer = models.AnswerText(
                question_no=db_question.No,
                full_answer=row.get('full_answer', ''),
                explanation=row.get('explanation')
            )
            db.add(db_answer)
            valid_count += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during upload: {str(e)}")

    return {"message": "Import successful", "questions_imported": valid_count}


@router.get("", response_model=list[schemas.QbQuestionResponse])
def get_questions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    questions = db.query(models.QbQuestion).order_by(models.QbQuestion.created_at.desc()).offset(skip).limit(
        limit).all()
    return questions


@router.get("/{question_no}", response_model=schemas.QbQuestionResponse)
def get_question_by_id(
        question_no: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    question = db.query(models.QbQuestion).filter(models.QbQuestion.No == question_no).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question