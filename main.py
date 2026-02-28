from datetime import datetime
from typing import Optional, Any
from fastapi import FastAPI
from sqlalchemy import create_engine, ForeignKey, String, Integer, BigInteger, Boolean, Text, JSON, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# 1. Setup SQLite engine
# The file 'app.db' will be created in your current working directory.
DATABASE_URL = "sqlite:///./app.db"

# Setting check_same_thread to False is crucial for SQLite in FastAPI to allow concurrent thread access.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Base class utilizing SQLAlchemy 2.0 strict typing
class Base(DeclarativeBase):
    pass

# 3. Mapped Models
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

# 4. FastAPI App Initialization
app = FastAPI()

@app.on_event("startup")
def on_startup():
    # This command inspects all classes inheriting from Base and automatically creates
    # the SQLite file and all tables if they do not already exist.
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"status": "Database setup complete."}