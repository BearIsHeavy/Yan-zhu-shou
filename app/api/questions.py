# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, Token
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.logs import SecurityLog
from datetime import timedelta


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user."""
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password=hashed_password,
        name=user.name,
        phone=user.phone,
        gender=user.gender
    )

    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login_user(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    """Authenticates a user and returns a JWT."""
    db_user = db.query(User).filter(User.email == user.email).first()

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    if not db_user or not verify_password(user.password, db_user.password):
        if db_user:
            failed_log = SecurityLog(
                user_id=db_user.user_id,
                ip_address=client_ip,
                device_info=user_agent,
                action_type="LOGIN_FAIL"
            )
            db.add(failed_log)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    success_log = SecurityLog(
        user_id=db_user.user_id,
        ip_address=client_ip,
        device_info=user_agent,
        action_type="LOGIN_SUCCESS"
    )
    db.add(success_log)
    db.commit()

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user():
    """Logs out the user (instructs the client to discard the token)."""
    return {"message": "Successfully logged out. Please remove the token from your client."}

# app/api/questions.py
import csv
import io
import json
from typing import Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.question_bank import QbQuestion, StemText, AnswerText
from app.models.user import User
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.question import QuestionUploadResponse


router = APIRouter()


@router.post("/upload-csv", response_model=QuestionUploadResponse)
async def upload_questions_csv(
        bank_id: int = Form(..., description="The ID of the Question Bank"),
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> QuestionUploadResponse:
    """
    Uploads a CSV file containing questions and saves them to the database.
    Requires a valid JWT Bearer token.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        contents = await file.read()
        decoded_content = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))

        inserted_count = 0

        for row in csv_reader:
            parsed_options = None
            if row.get('options'):
                try:
                    parsed_options = json.loads(row['options'])
                except json.JSONDecodeError:
                    parsed_options = []

            # 1. Create the main question record securely attached to the current user
            new_question = QbQuestion(
                bank_id=bank_id,
                user_id=current_user.user_id,  # Fetched safely from the JWT token
                category=row.get('category', 'General'),
                stem=row.get('stem', 'No Summary'),
                qus_type=int(row.get('qus_type', 1)),
                options=parsed_options,
                correct_ans_summary=row.get('correct_ans_summary', '')
            )

            db.add(new_question)
            db.flush()

            # 2. Create the stem text record
            new_stem_text = StemText(
                question_no=new_question.No,
                full_text=row.get('stem_full_text', ''),
                image_url=row.get('image_url', None) or None
            )
            db.add(new_stem_text)

            # 3. Create the answer text record
            new_answer_text = AnswerText(
                question_no=new_question.No,
                full_answer=row.get('full_answer', ''),
                explanation=row.get('explanation', '')
            )
            db.add(new_answer_text)

            inserted_count += 1

        db.commit()
        return QuestionUploadResponse(status="success", inserted_records=inserted_count)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {str(e)}")