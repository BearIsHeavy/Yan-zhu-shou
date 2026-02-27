# main.py
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import csv
import io
import json
import xml.etree.ElementTree as ET

from database import engine, Base, get_db, redis_client
import models
import schemas
import security
from dependencies import get_current_user

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Secure Authentication API",
    description="API documentation for user authentication and management.",
    version="1.0.0"
)

# --- CORS CONFIGURATION ---
origins: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SYSTEM & AUTH ROUTES ---

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    redis_status = "connected" if redis_client.ping() else "disconnected"
    return {"status": "healthy", "database": "connected", "redis": redis_status}


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    hashed_pw = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")


@app.post("/login", response_model=schemas.Token, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict[
    str, str]:
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.email)}, expires_delta=access_token_expires
    )
    redis_client.setex(
        name=f"session:{user.id}",
        time=int(access_token_expires.total_seconds()),
        value=access_token
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout", tags=["Auth"])
def logout_user(current_user: models.User = Depends(get_current_user)) -> dict[str, str]:
    redis_client.delete(f"session:{current_user.id}")
    return {"message": "Successfully logged out"}


@app.get("/users/me", response_model=schemas.UserResponse, tags=["Users"])
def read_users_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


# --- QUESTION MANAGEMENT ROUTES ---

@app.get("/questions", response_model=list[schemas.QuestionResponse], tags=["Questions"])
def get_questions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve a list of all questions from the Question Bank.
    Supports pagination via 'skip' and 'limit' query parameters.
    """
    questions = db.query(models.Question).offset(skip).limit(limit).all()
    return questions


@app.get("/questions/{question_id}", response_model=schemas.QuestionResponse, tags=["Questions"])
def get_question_by_id(
        question_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    """Retrieve a single specific question by its ID."""
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@app.post("/questions/upload", tags=["Questions"], summary="Upload Questions via CSV/XML")
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
            stem = row.get("Question Stem")
            options_raw = row.get("Options")
            if not stem or not options_raw:
                continue
            try:
                options = json.loads(options_raw) if options_raw.startswith('[') else options_raw.split('|')
            except json.JSONDecodeError:
                continue
            db_question = models.Question(
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
            stem_elem = q_elem.find("Stem")
            options_elem = q_elem.find("Options")
            if stem_elem is None or stem_elem.text is None or options_elem is None:
                continue
            options = [opt.text for opt in options_elem.findall("Option") if opt.text]
            if not options:
                continue
            db_question = models.Question(
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


# --- ERROR BANK / MISTAKE NOTEBOOK ROUTES ---

@app.post("/errors", response_model=schemas.ErrorRecordResponse, tags=["Error Bank"],
          status_code=status.HTTP_201_CREATED)
def record_error(
        error_data: schemas.ErrorRecordCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
) -> models.ErrorRecord:
    question = db.query(models.Question).filter(models.Question.id == error_data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    new_error = models.ErrorRecord(
        user_id=current_user.id,
        question_id=error_data.question_id,
        selected_option=error_data.selected_option
    )
    db.add(new_error)
    db.commit()
    db.refresh(new_error)
    return new_error


@app.get("/errors/me", response_model=list[schemas.ErrorRecordResponse], tags=["Error Bank"])
def get_my_errors(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    errors = db.query(models.ErrorRecord).filter(models.ErrorRecord.user_id == current_user.id).all()
    return errors