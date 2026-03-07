from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class UserQuestionLog(Base):
    __tablename__ = "user_question_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False, index=True)
    question_no = Column(Integer, ForeignKey("qb_questions.No", ondelete="CASCADE"), nullable=False, index=True)
    user_answer = Column(String)
    is_correct = Column(Boolean, nullable=False)
    attempt_time = Column(DateTime, server_default=func.now())
    is_mastered = Column(Boolean, default=False, comment="User marked as mastered")

    # Relationships
    user = relationship("User", back_populates="question_logs")
    question = relationship("QBQuestion", back_populates="logs")

    def __repr__(self):
        return f"<UserQuestionLog(id={self.id}, user_id={self.user_id}, question_no={self.question_no})>"


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    device_info = Column(String(255))
    action_type = Column(String(50))  # LOGIN_SUCCESS, LOGIN_FAIL, UNAUTHORIZED_ACCESS
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="security_logs")

    def __repr__(self):
        return f"<SecurityLog(id={self.id}, user_id={self.user_id}, action_type={self.action_type})>"
