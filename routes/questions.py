import shutil
import json
import csv
import xml.etree.ElementTree as ET
from typing import Optional
from fastapi import Depends, File, UploadFile, HTTPException, status, Form
from fastapi.routing import APIRouter
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def get_byte_length(text: str) -> int:
    """Get byte length of UTF-8 encoded Text"""
    return len(text.encode('utf-8'))


async def store_stem_and_answer(
    db: AsyncSession,
    question_no: int,
    full_text: Optional[str] = None,
    image_url: Optional[str] = None,
    full_answer: Optional[str] = None,
    explanation: Optional[str] = None
):
    """Store stem text and answer text for a question"""
    if full_text:
        stem_record = models.StemText(
            question_no=question_no,
            full_text=full_text,
            image_url=image_url
        )
        db.add(stem_record)
    
    if full_answer:
        answer_record = models.AnswerText(
            question_no=question_no,
            full_answer=full_answer,
            explanation=explanation
        )
        db.add(answer_record)


@router.post("/csv")
async def upload_csv_questions(
    file: UploadFile = File(...),
    bank_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload CSV file to bulk import questions to a question bank.
    
    CSV format expected columns:
    - category: Subject/topic category
    - stem: Question stem (summary for list display)
    - qus_type: Question type (0:Essay, 1:Single, 2:Multiple, 3:Fill-in)
    - options: JSON string of options (optional)
    - correct_ans_summary: Summary of correct answer (optional)
    - full_text: Full stem text for StemText (optional)
    - image_url: Image URL for stem (optional)
    - full_answer: Full answer text for AnswerText (optional)
    - explanation: Answer explanation (optional)
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are allowed."
        )
    
    result = await db.execute(
        select(models.QuestionBank).where(
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
            detail=f"Question bank {bank_id} not found or you don't have access."
        )
    
    file_location = UPLOAD_DIR / file.filename
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        questions_added = 0
        with open(file_location, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                options = None
                if row.get("options"):
                    try:
                        options = json.loads(row["options"])
                    except json.JSONDecodeError:
                        options = {"format": "JSON"}
                
                qus_type = int(row.get("qus_type", 1))
                item = models.QBQuestion(
                    bank_id=bank_id,
                    category=row.get("category", "General"),
                    stem=row.get("stem", "")[:255],
                    qus_type=qus_type,
                    options=json.dumps(options) if options else None,
                    correct_ans_summary=row.get("correct_ans_summary"),
                    is_public=question_bank.is_public,
                    user_id=current_user.user_id
                )
                db.add(item)
                await db.flush()
                
                await store_stem_and_answer(
                    db=db,
                    question_no=item.No,
                    full_text=row.get("full_text"),
                    image_url=row.get("image_url"),
                    full_answer=row.get("full_answer"),
                    explanation=row.get("explanation")
                )
                questions_added += 1
        
        await db.commit()
        file_location.unlink(missing_ok=True)
        
        return {
            "detail": f"Successfully imported {questions_added} questions to question bank '{question_bank.name}'",
            "questions_added": questions_added
        }
        
    except Exception as e:
        await db.rollback()
        file_location.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV file: {str(e)}"
        )


@router.post("/xml")
async def upload_xml_questions(
    file: UploadFile = File(...),
    bank_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload XML file to bulk import questions to a question bank.
    
    XML format expected:
    <questions>
        <question>
            <category>Subject/Topic</category>
            <stem>Question stem</stem>
            <qus_type>1</qus_type>
            <options>{"A": "option1", "B": "option2"}</options>
            <correct_ans_summary>A</correct_ans_summary>
            <full_text>Full question text</full_text>
            <image_url>http://...</image_url>
            <full_answer>Full answer</full_answer>
            <explanation>Explanation</explanation>
        </question>
    </questions>
    """
    if not file.filename or not file.filename.endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only XML files are allowed."
        )
    
    result = await db.execute(
        select(models.QuestionBank).where(
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
            detail=f"Question bank {bank_id} not found or you don't have access."
        )
    
    file_location = UPLOAD_DIR / file.filename
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        tree = ET.parse(file_location)
        root = tree.getroot()
        
        questions_added = 0
        for question_elem in root.findall("question"):
            def get_elem_text(tag):
                elem = question_elem.find(tag)
                return elem.text if elem is not None and elem.text else ""
            
            options = None
            options_str = get_elem_text("options")
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    options = {"format": "JSON"}
            
            qus_type_str = get_elem_text("qus_type")
            qus_type = int(qus_type_str) if qus_type_str else 1
            
            stem = get_elem_text("stem")
            item = models.QBQuestion(
                bank_id=bank_id,
                category=get_elem_text("category") or "General",
                stem=stem[:255],
                qus_type=qus_type,
                options=json.dumps(options) if options else None,
                correct_ans_summary=get_elem_text("correct_ans_summary"),
                is_public=question_bank.is_public,
                user_id=current_user.user_id
            )
            db.add(item)
            await db.flush()
            
            await store_stem_and_answer(
                db=db,
                question_no=item.No,
                full_text=get_elem_text("full_text"),
                image_url=get_elem_text("image_url"),
                full_answer=get_elem_text("full_answer"),
                explanation=get_elem_text("explanation")
            )
            questions_added += 1
        
        await db.commit()
        file_location.unlink(missing_ok=True)
        
        return {
            "detail": f"Successfully imported {questions_added} questions to question bank '{question_bank.name}'",
            "questions_added": questions_added
        }
        
    except ET.ParseError as e:
        await db.rollback()
        file_location.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid XML format: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        file_location.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process XML file: {str(e)}"
        )


@router.post("/question", response_model=schemas.QBQuestionResponse)
async def store_single_question(
    bank_id: int = Form(...),
    category: str = Form(...),
    stem: str = Form(...),
    qus_type: int = Form(1),
    options: Optional[str] = Form(None),
    correct_ans_summary: Optional[str] = Form(None),
    is_public: bool = Form(True),
    full_text: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    full_answer: Optional[str] = Form(None),
    explanation: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload a single question to a question bank.
    
    - bank_id: ID of the question bank (must belong to current user)
    - category: Subject/topic category
    - stem: Question stem (summary for list display, max 255 chars)
    - qus_type: Question type (0:Essay, 1:Single, 2:Multiple, 3:Fill-in)
    - options: JSON string of options (optional)
    - correct_ans_summary: Summary of correct answer (optional)
    - is_public: Whether question is public (default: True)
    - full_text: Optional full stem text for StemText table
    - image_url: Optional image URL for the question
    - full_answer: Optional full answer for AnswerText table
    - explanation: Optional answer explanation
    """
    result = await db.execute(
        select(models.QuestionBank).where(
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
            detail=f"Question bank {bank_id} not found or you don't have access."
        )

    try:
        item = models.QBQuestion(
            bank_id=bank_id,
            category=category,
            stem=stem[:255],
            qus_type=qus_type,
            options=options,
            correct_ans_summary=correct_ans_summary,
            is_public=is_public,
            user_id=current_user.user_id
        )
        db.add(item)
        await db.flush()

        await store_stem_and_answer(
            db=db,
            question_no=item.No,
            full_text=full_text,
            image_url=image_url,
            full_answer=full_answer,
            explanation=explanation
        )

        await db.commit()
        await db.refresh(item)

        # Parse options for response
        response_data = item.__dict__.copy()
        if item.options and isinstance(item.options, str):
            try:
                response_data['options'] = json.loads(item.options)
            except json.JSONDecodeError:
                response_data['options'] = {"format": "JSON"}
        
        # Create response manually
        return schemas.QBQuestionResponse(
            No=item.No,
            bank_id=item.bank_id,
            category=item.category,
            stem=item.stem,
            qus_type=item.qus_type,
            options=response_data['options'],
            correct_ans_summary=item.correct_ans_summary,
            is_public=item.is_public,
            correct_num=item.correct_num,
            uncorrect_num=item.uncorrect_num,
            user_id=item.user_id,
            created_at=item.created_at
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question: {str(e)}"
        )
