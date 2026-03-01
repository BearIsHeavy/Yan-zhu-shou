# filepath: main.py
import csv
import io
import json
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Generator

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, ForeignKey, String, Integer, BigInteger, Boolean, Text, JSON, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from pydantic import BaseModel, EmailStr, Field
from jose import jwt, JWTError

# ---------------------------------------------------------
# 1. Database Setup
# ---------------------------------------------------------
DATABASE_URL = "mysql+pymysql://api:api@127.0.0.1:3306/backend_db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# 2. SQLAlchemy Base & Models (Strictly Typed)
# ---------------------------------------------------------
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    gender: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='0:Unknown 1:Male 2:Female')
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


class QuestionBank(Base):
    __tablename__ = "question_banks"
    bank_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


class QbQuestion(Base):
    __tablename__ = "qb_questions"
    No: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bank_id: Mapped[Optional[int]] = mapped_column(ForeignKey("question_banks.bank_id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(50), comment='学科/主题')
    stem: Mapped[str] = mapped_column(String(255), comment='题干摘要（用于列表显示）')
    qus_type: Mapped[int] = mapped_column(Integer, default=1, comment='0:解答 1:单选 2:多选 3:填空')
    options: Mapped[Optional[Any]] = mapped_column(JSON, comment='选项结构化存储')
    correct_ans_summary: Mapped[Optional[str]] = mapped_column(String(255))
    correct_num: Mapped[int] = mapped_column(Integer, default=0)
    uncorrect_num: Mapped[int] = mapped_column(Integer, default=0)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("User.user_id", ondelete="SET NULL"))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


class StemText(Base):
    __tablename__ = "stem_text"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True)
    full_text: Mapped[str] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(255))


class AnswerText(Base):
    __tablename__ = "answer_text"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True)
    full_answer: Mapped[str] = mapped_column(Text, comment='完整正确答案')
    explanation: Mapped[Optional[str]] = mapped_column(Text, comment='答案解析/解题过程')


class UserQuestionLog(Base):
    __tablename__ = "user_question_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"))
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"))
    user_answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    attempt_time: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    is_mastered: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)


class SecurityLog(Base):
    __tablename__ = "security_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"))
    ip_address: Mapped[str] = mapped_column(String(45))
    device_info: Mapped[Optional[str]] = mapped_column(String(255))
    action_type: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------
# 3. Pydantic Schemas
# ---------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=64, description="Maximum length 64 characters")
    name: str
    phone: Optional[str] = None
    gender: Optional[int] = 0


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=64)


class Token(BaseModel):
    access_token: str
    token_type: str


# ---------------------------------------------------------
# 4. Security & JWT Utilities
# ---------------------------------------------------------
SECRET_KEY = "your-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password using SHA-256 pre-hashing and bcrypt."""
    password_bytes = plain_password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).hexdigest().encode('ascii')

    # bcrypt.checkpw requires both inputs to be bytes
    return bcrypt.checkpw(sha256_hash, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hashes a password using SHA-256 pre-hashing to bypass bcrypt's 72-byte limit."""
    password_bytes = password.encode('utf-8')
    sha256_hash = hashlib.sha256(password_bytes).hexdigest().encode('ascii')

    salt = bcrypt.gensalt()
    # Return as string to save nicely in the database
    return bcrypt.hashpw(sha256_hash, salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
        db: Session = Depends(get_db)
) -> User:
    """Dependency to extract and verify the JWT token from the Authorization header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.user_id == token_data_id).first()
    if user is None:
        raise credentials_exception
    return user


# ---------------------------------------------------------
# 5. FastAPI App Initialization & Routes
# ---------------------------------------------------------
app = FastAPI(title="Question Bank API")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> dict[str, str]:
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


@app.post("/login", response_model=Token)
def login_user(request: Request, user: UserLogin, db: Session = Depends(get_db)) -> dict[str, str]:
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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.user_id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout")
def logout_user() -> dict[str, str]:
    """Logs out the user (instructs the client to discard the token)."""
    return {"message": "Successfully logged out. Please remove the token from your client."}


@app.post("/upload-questions/")
async def upload_questions_csv(
        bank_id: int = Form(..., description="The ID of the Question Bank"),
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> dict[str, Any]:
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
        return {"status": "success", "inserted_records": inserted_count}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {str(e)}")