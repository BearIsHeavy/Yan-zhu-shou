from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class QuestionBank(Base):
    __tablename__ = "question_banks"

    bank_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="question_banks")
    questions = relationship("QBQuestion", back_populates="question_bank", cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<QuestionBank(bank_id={self.bank_id}, name={self.name}, "
                f"user_id={self.user_id}, is_public={self.is_public}, "
                f"description={self.description}, created_at={self.created_at})>")


class QBQuestion(Base):
    __tablename__ = "qb_questions"

    No = Column(Integer, primary_key=True, autoincrement=True)
    bank_id = Column(Integer, ForeignKey("question_banks.bank_id", ondelete="SET NULL"))
    category = Column(String(50), nullable=False)  # 学科/主题
    stem = Column(String(255), nullable=False)  # 题干摘要（用于列表显示）
    qus_type = Column(SmallInteger, default=1, nullable=False)  # 0:解答 1:单选 2:多选 3:填空
    options = Column(String)  # JSON stored as string
    correct_ans_summary = Column(String(255))  # 答案摘要（用于列表预览）
    correct_num = Column(Integer, default=0, nullable=False)
    uncorrect_num = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="SET NULL"))  # 用户 ID，NULL=系统题
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    question_bank = relationship("QuestionBank", back_populates="questions")
    stem_text = relationship("StemText", back_populates="question", uselist=False, cascade="all, delete-orphan")
    answer_text = relationship("AnswerText", back_populates="question", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<QBQuestion(No={self.No}, stem={self.stem})>"


class StemText(Base):
    __tablename__ = "stem_text"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True, nullable=False)
    full_text = Column(Text, nullable=False)
    image_url = Column(String(255))

    question = relationship("QBQuestion", back_populates="stem_text")

    def __repr__(self):
        return f"<StemText(id={self.id}, question_no={self.question_no})>"


class AnswerText(Base):
    __tablename__ = "answer_text"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True, nullable=False)
    full_answer = Column(Text, nullable=False)  # 完整正确答案
    explanation = Column(Text)  # 答案解析/解题过程

    question = relationship("QBQuestion", back_populates="answer_text")

    def __repr__(self):
        return f"<AnswerText(id={self.id}, question_no={self.question_no})>"
