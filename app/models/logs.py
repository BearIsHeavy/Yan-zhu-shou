# app/models/logs.py
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, func
from app.models.base import Base


class UserQuestionLog(Base):
    __tablename__ = "user_question_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    attempt_time = Column(DateTime, server_default=func.now())
    is_mastered = Column(Boolean, default=False)


class SecurityLog(Base):
    __tablename__ = "security_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    device_info = Column(String(255), nullable=True)
    action_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())