from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "User"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    hash_password = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True)
    gender = Column(SmallInteger, default=0)  # 0:Unknown 1:Male 2:Female
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    question_banks = relationship("QuestionBank", back_populates="user", cascade="all, delete-orphan")
    security_logs = relationship("SecurityLog", back_populates="user", cascade="all, delete-orphan")
    question_logs = relationship("UserQuestionLog", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    feedback_votes = relationship("FeedbackVote", back_populates="user", cascade="all, delete-orphan")
    blogs = relationship("Blog", back_populates="user", cascade="all, delete-orphan")
    blog_likes = relationship("BlogLike", back_populates="user", cascade="all, delete-orphan")
    blog_comments = relationship("BlogComment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, name={self.name})>"
