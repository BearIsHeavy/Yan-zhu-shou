# filepath: app/models.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, Boolean, Text, JSON, ForeignKey, DateTime, func
from datetime import datetime
from typing import Any
from .database import Base

class User(Base):
    __tablename__ = "User"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    gender: Mapped[int | None] = mapped_column(Integer, default=0, comment='0:Unknown 1:Male 2:Female')
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    question_banks = relationship("QuestionBank", back_populates="user", cascade="all, delete-orphan")
    created_questions = relationship("QbQuestion", back_populates="creator")
    question_logs = relationship("UserQuestionLog", back_populates="user", cascade="all, delete-orphan")
    security_logs = relationship("SecurityLog", back_populates="user", cascade="all, delete-orphan")


class QuestionBank(Base):
    __tablename__ = "question_banks"

    bank_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="question_banks")
    questions = relationship("QbQuestion", back_populates="bank", cascade="all, delete-orphan")


class QbQuestion(Base):
    __tablename__ = "qb_questions"

    No: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bank_id: Mapped[int | None] = mapped_column(ForeignKey("question_banks.bank_id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment='学科/主题')
    stem: Mapped[str] = mapped_column(String(255), nullable=False, comment='题干摘要（用于列表显示）')
    qus_type: Mapped[int] = mapped_column(Integer, default=1, comment='0:解答 1:单选 2:多选 3:填空')
    options: Mapped[Any | None] = mapped_column(JSON, comment='选项结构化存储', nullable=True)
    correct_ans_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correct_num: Mapped[int] = mapped_column(Integer, default=0)
    uncorrect_num: Mapped[int] = mapped_column(Integer, default=0)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("User.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    bank = relationship("QuestionBank", back_populates="questions")
    creator = relationship("User", back_populates="created_questions")
    stem_text = relationship("StemText", back_populates="question", uselist=False, cascade="all, delete-orphan")
    answer_text = relationship("AnswerText", back_populates="question", uselist=False, cascade="all, delete-orphan")
    logs = relationship("UserQuestionLog", back_populates="question", cascade="all, delete-orphan")


class StemText(Base):
    __tablename__ = "stem_text"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    question = relationship("QbQuestion", back_populates="stem_text")


class AnswerText(Base):
    __tablename__ = "answer_text"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True)
    full_answer: Mapped[str] = mapped_column(Text, nullable=False, comment='完整正确答案')
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True, comment='答案解析/解题过程')

    # Relationships
    question = relationship("QbQuestion", back_populates="answer_text")


class UserQuestionLog(Base):
    __tablename__ = "user_question_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    question_no: Mapped[int] = mapped_column(ForeignKey("qb_questions.No", ondelete="CASCADE"), nullable=False)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempt_time: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
    is_mastered: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="question_logs")
    question = relationship("QbQuestion", back_populates="logs")


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="security_logs")