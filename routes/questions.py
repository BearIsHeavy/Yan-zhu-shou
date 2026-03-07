import json
import csv
import io
import xml.etree.ElementTree as ET
from typing import Optional
from fastapi import Depends, File, UploadFile, HTTPException, status, Form
from fastapi.routing import APIRouter
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
import schemas
from database import get_db
from dependencies import get_current_user

router = APIRouter()

STEM_MARKER = "###"  # Marker prefix for stems stored in StemText table


def get_byte_length(text: str) -> int:
    """Get byte length of UTF-8 encoded text."""
    return len(text.encode('utf-8'))


async def get_full_stem(db: AsyncSession, question: models.QBQuestion) -> str:
    """
    Get the full stem text for a question.
    
    If the stem field starts with the marker '###', fetches the full text
    from the StemText table. Otherwise, returns the stem field directly.
    
    Args:
        db: Database session
        question: QBQuestion object
        
    Returns:
        Full stem text
    """
    if question.stem.startswith(STEM_MARKER):
        # Fetch full stem from StemText table
        result = await db.execute(
            select(models.StemText).where(models.StemText.question_no == question.No)
        )
        stem_record = result.scalar_one_or_none()
        if stem_record:
            return stem_record.full_text
        # Fallback to stem if no record found (should not happen)
        return question.stem[len(STEM_MARKER):]
    return question.stem


async def store_stem_and_answer(
    db: AsyncSession,
    question_no: int,
    stem: str,  # The original full stem text
    full_answer: Optional[str] = None,
    explanation: Optional[str] = None
):
    """
    Store stem text and answer text for a question.
    
    Only stores stem in StemText table if stem > 255 bytes.
    When stem exceeds 255 bytes, the stem column in qb_questions 
    will contain the marker '###' to indicate external storage.
    
    Args:
        db: Database session
        question_no: Question number/ID
        stem: Full stem text
        full_answer: Optional full answer text for AnswerText table
        explanation: Optional answer explanation
    """
    stem_byte_length = get_byte_length(stem)
    
    # Only store in StemText if stem exceeds 255 bytes
    if stem_byte_length > 255:
        stem_record = models.StemText(
            question_no=question_no,
            full_text=stem
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
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are allowed."
        )

    # Verify question bank exists and belongs to current user
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
        # Read CSV content directly from uploaded file (in-memory processing)
        content = await file.read()
        csv_text = content.decode("utf-8")
        
        # Parse CSV from string
        csv_file = io.StringIO(csv_text)
        reader = csv.DictReader(csv_file)

        questions_added = 0
        for row in reader:
            # Parse options from JSON string if provided
            options = None
            if row.get("options"):
                try:
                    options = json.loads(row["options"])
                except json.JSONDecodeError:
                    options = {"format": "JSON"}

            qus_type = int(row.get("qus_type", 1))
            full_stem = row.get("stem", "")
            stem_byte_length = get_byte_length(full_stem)

            # If stem > 255 bytes, store marker in stem column, otherwise store the stem
            stem_value = STEM_MARKER if stem_byte_length > 255 else full_stem[:255]

            item = models.QBQuestion(
                bank_id=bank_id,
                category=row.get("category", "General"),
                stem=stem_value,
                qus_type=qus_type,
                options=json.dumps(options) if options else None,
                correct_ans_summary=row.get("correct_ans_summary"),
                is_public=question_bank.is_public,
                user_id=current_user.user_id
            )
            db.add(item)
            await db.flush()

            # Store full stem in StemText only if it exceeds 255 bytes
            if stem_byte_length > 255:
                await store_stem_and_answer(
                    db=db,
                    question_no=item.No,
                    stem=full_stem,
                    full_answer=row.get("full_answer"),
                    explanation=row.get("explanation")
                )
            elif row.get("full_answer") or row.get("explanation"):
                # Still store answer/explanation if provided (even without full stem)
                await store_stem_and_answer(
                    db=db,
                    question_no=item.No,
                    stem=full_stem,
                    full_answer=row.get("full_answer"),
                    explanation=row.get("explanation")
                )
            questions_added += 1

        await db.commit()

        return {
            "detail": f"Successfully imported {questions_added} questions to question bank '{question_bank.name}'",
            "questions_added": questions_added
        }

    except UnicodeDecodeError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file encoding. Please use UTF-8 encoded CSV files: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
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
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only XML files are allowed."
        )

    # Verify question bank exists and belongs to current user
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
        # Read XML content directly from uploaded file (in-memory processing)
        content = await file.read()
        xml_text = content.decode("utf-8")
        
        # Parse XML from string
        tree = ET.parse(io.StringIO(xml_text))
        root = tree.getroot()

        questions_added = 0
        for question_elem in root.findall("question"):
            def get_elem_text(tag):
                elem = question_elem.find(tag)
                return elem.text if elem is not None and elem.text else ""

            # Parse options from JSON string if provided
            options = None
            options_str = get_elem_text("options")
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    options = {"format": "JSON"}

            qus_type_str = get_elem_text("qus_type")
            qus_type = int(qus_type_str) if qus_type_str else 1

            full_stem = get_elem_text("stem")
            stem_byte_length = get_byte_length(full_stem)

            # If stem > 255 bytes, store marker in stem column, otherwise store the stem
            stem_value = STEM_MARKER if stem_byte_length > 255 else full_stem[:255]

            item = models.QBQuestion(
                bank_id=bank_id,
                category=get_elem_text("category") or "General",
                stem=stem_value,
                qus_type=qus_type,
                options=json.dumps(options) if options else None,
                correct_ans_summary=get_elem_text("correct_ans_summary"),
                is_public=question_bank.is_public,
                user_id=current_user.user_id
            )
            db.add(item)
            await db.flush()

            # Store full stem in StemText only if it exceeds 255 bytes
            if stem_byte_length > 255:
                await store_stem_and_answer(
                    db=db,
                    question_no=item.No,
                    stem=full_stem,
                    full_answer=get_elem_text("full_answer"),
                    explanation=get_elem_text("explanation")
                )
            elif get_elem_text("full_answer") or get_elem_text("explanation"):
                # Still store answer/explanation if provided (even without full stem)
                await store_stem_and_answer(
                    db=db,
                    question_no=item.No,
                    stem=full_stem,
                    full_answer=get_elem_text("full_answer"),
                    explanation=get_elem_text("explanation")
                )
            questions_added += 1

        await db.commit()

        return {
            "detail": f"Successfully imported {questions_added} questions to question bank '{question_bank.name}'",
            "questions_added": questions_added
        }

    except ET.ParseError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid XML format: {str(e)}"
        )
    except UnicodeDecodeError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file encoding. Please use UTF-8 encoded XML files: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
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
    full_answer: Optional[str] = Form(None),
    explanation: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload a single question to a question bank.

    - bank_id: ID of the question bank (must belong to current user)
    - category: Subject/topic category
    - stem: Question stem (if <= 255 bytes) or '###' marker if stored externally
    - qus_type: Question type (0:Essay, 1:Single, 2:Multiple, 3:Fill-in)
    - options: JSON string of options (optional)
    - correct_ans_summary: Summary of correct answer (optional)
    - is_public: Whether question is public (default: True)
    - full_answer: Optional full answer for AnswerText table
    - explanation: Optional answer explanation
    
    Note: If stem exceeds 255 bytes, it will be stored in StemText table
    and the stem field will contain '###' marker.
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
        stem_byte_length = get_byte_length(stem)
        stem_value = STEM_MARKER if stem_byte_length > 255 else stem[:255]
        
        item = models.QBQuestion(
            bank_id=bank_id,
            category=category,
            stem=stem_value,
            qus_type=qus_type,
            options=options,
            correct_ans_summary=correct_ans_summary,
            is_public=is_public,
            user_id=current_user.user_id
        )
        db.add(item)
        await db.flush()

        # Store full stem in StemText only if it exceeds 255 bytes
        if stem_byte_length > 255:
            await store_stem_and_answer(
                db=db,
                question_no=item.No,
                stem=stem,
                full_answer=full_answer,
                explanation=explanation
            )
        elif full_answer or explanation:
            # Still store answer/explanation if provided (even without full stem)
            await store_stem_and_answer(
                db=db,
                question_no=item.No,
                stem=stem,
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
