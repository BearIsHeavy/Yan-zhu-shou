# app/models/question_bank.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func
from app.models.base import Base


class QuestionBank(Base):
    __tablename__ = "question_banks"
    bank_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    is_public = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class QbQuestion(Base):
    __tablename__ = "qb_questions"
    No = Column(Integer, primary_key=True, autoincrement=True)
    bank_id = Column(Integer, ForeignKey("question_banks.bank_id", ondelete="SET NULL"), nullable=True)
    category = Column(String(50), comment='学科/主题')
    stem = Column(String(255), comment='题干摘要（用于列表显示）')
    qus_type = Column(Integer, default=1, comment='0:解答 1:单选 2:多选 3:填空')
    options = Column(JSON, comment='选项结构化存储')
    correct_ans_summary = Column(String(255), nullable=True)
    correct_num = Column(Integer, default=0)
    uncorrect_num = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class StemText(Base):
    __tablename__ = "stem_text"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True, nullable=False)
    full_text = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)


class AnswerText(Base):
    __tablename__ = "answer_text"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), unique=True, nullable=False)
    full_answer = Column(Text, comment='完整正确答案')
    explanation = Column(Text, comment='答案解析/解题过程')