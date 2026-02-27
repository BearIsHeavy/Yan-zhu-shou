# questions.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io
import json
import xml.etree.ElementTree as ET

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.post("/upload", summary="Upload Questions via CSV/XML")
async def upload_questions(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> dict[str, int | str]:
    contents = await file.read()
    decoded_content = contents.decode("utf-8")
    valid_count = 0

    if file.filename and file.filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(decoded_content))
        for row in reader:
            question_type = row.get("Question Type")
            stem = row.get("Question Stem")
            options_raw = row.get("Options")

            # Reject rows missing the newly required Question Type
            if not stem or not options_raw or not question_type:
                continue
            try:
                options = json.loads(options_raw) if options_raw.startswith('[') else options_raw.split('|')
            except json.JSONDecodeError:
                continue
            db_question = models.Question(
                question_type=question_type,
                stem=stem,
                options=options,
                correct_answer=row.get("Correct Answer"),
                explanation=row.get("Explanation/Analysis"),
                knowledge_points=row.get("Knowledge Points")
            )
            db.add(db_question)
            valid_count += 1

    elif file.filename and file.filename.endswith(".xml"):
        root = ET.fromstring(decoded_content)
        for q_elem in root.findall("Question"):
            type_elem = q_elem.find("Type")
            stem_elem = q_elem.find("Stem")
            options_elem = q_elem.find("Options")

            # Ensure the <Type> tag is present in XML
            if stem_elem is None or stem_elem.text is None or options_elem is None or type_elem is None or type_elem.text is None:
                continue
            options = [opt.text for opt in options_elem.findall("Option") if opt.text]
            if not options:
                continue
            db_question = models.Question(
                question_type=type_elem.text,
                stem=stem_elem.text,
                options=options,
                correct_answer=q_elem.findtext("CorrectAnswer"),
                explanation=q_elem.findtext("Explanation"),
                knowledge_points=q_elem.findtext("KnowledgePoints")
            )
            db.add(db_question)
            valid_count += 1
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV and XML are supported.")

    db.commit()
    return {"message": "Import successful", "questions_imported": valid_count}


@router.get("", response_model=list[schemas.QuestionResponse])
def get_questions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # Sort the database query by the new created_at timestamp in descending order
    questions = db.query(models.Question).order_by(models.Question.created_at.desc()).offset(skip).limit(limit).all()
    return questions


@router.get("/{question_id}", response_model=schemas.QuestionResponse)
def get_question_by_id(
        question_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question