# app/models.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Text, JSON, ForeignKey, DateTime, Integer, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime, date
import enum
from .database import Base


# --- ENUMS FOR STRICT TYPING ---

class QuestionTypeEnum(str, enum.Enum):
    choice = 'choice'
    fill = 'fill'
    solution = 'solution'
    other = 'other'


class ErrorReasonEnum(str, enum.Enum):
    careless = 'careless'
    concept_gap = 'concept_gap'
    logic_error = 'logic_error'
    time_limit = 'time_limit'
    other = 'other'


class QuestionStatusEnum(str, enum.Enum):
    new = 'new'
    reviewing = 'reviewing'
    mastered = 'mastered'
    removed = 'removed'


class ReviewResultEnum(str, enum.Enum):
    correct = 'correct'
    wrong = 'wrong'
    hint_used = 'hint_used'


# --- DATABASE MODELS ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("user_id", primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    wrong_questions = relationship("WrongQuestion", back_populates="user", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="user", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column("subject_id", primary_key=True, index=True)
    name: Mapped[str] = mapped_column("subject_name", String(50), nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    knowledge_points = relationship("KnowledgePoint", back_populates="subject")
    wrong_questions = relationship("WrongQuestion", back_populates="subject")


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column("kp_id", primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.subject_id"), nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_points.kp_id"), nullable=True)
    name: Mapped[str] = mapped_column("kp_name", String(100), nullable=False)
    full_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    subject = relationship("Subject", back_populates="knowledge_points")
    parent = relationship("KnowledgePoint", remote_side=[id], backref="children")


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id: Mapped[int] = mapped_column("question_id", primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.subject_id"), nullable=False)

    # Question Content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_images: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Store OSS URLs
    options_json: Mapped[list[str] | dict | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Category & Tags
    question_type: Mapped[QuestionTypeEnum] = mapped_column(SQLEnum(QuestionTypeEnum), default=QuestionTypeEnum.choice)
    source_info: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Error Cause
    error_reason_type: Mapped[ErrorReasonEnum | None] = mapped_column(SQLEnum(ErrorReasonEnum), nullable=True)
    error_reason_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status & Statistics
    status: Mapped[QuestionStatusEnum] = mapped_column(SQLEnum(QuestionStatusEnum), default=QuestionStatusEnum.new,
                                                       index=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    mistake_count: Mapped[int] = mapped_column(Integer, default=1)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="wrong_questions")
    subject = relationship("Subject", back_populates="wrong_questions")
    review_records = relationship("ReviewRecord", back_populates="question", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="question", uselist=False, cascade="all, delete-orphan")
    knowledge_points = relationship("QuestionKnowledgeMap", back_populates="question", cascade="all, delete-orphan")


class QuestionKnowledgeMap(Base):
    __tablename__ = "question_knowledge_map"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("wrong_questions.question_id", ondelete="CASCADE"),
                                             nullable=False)
    kp_id: Mapped[int] = mapped_column(ForeignKey("knowledge_points.kp_id"), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    question = relationship("WrongQuestion", back_populates="knowledge_points")
    knowledge_point = relationship("KnowledgePoint")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column("record_id", primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("wrong_questions.question_id", ondelete="CASCADE"),
                                             nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    result: Mapped[ReviewResultEnum | None] = mapped_column(SQLEnum(ReviewResultEnum), nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    question = relationship("WrongQuestion", back_populates="review_records")
    user = relationship("User", back_populates="review_records")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column("analysis_id", primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("wrong_questions.question_id", ondelete="CASCADE"), unique=True,
                                             nullable=False)
    ai_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    similar_questions_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    question = relationship("WrongQuestion", back_populates="ai_analysis")