from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum


class FeedbackCategory(str, PyEnum):
    BUG = "bug"
    FEATURE = "feature"
    UI = "ui"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class FeedbackStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Feedback(Base):
    __tablename__ = "Feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default=FeedbackCategory.OTHER.value)
    status = Column(String(50), default=FeedbackStatus.PENDING.value)
    vote_count = Column(Integer, default=0)
    developer_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    votes = relationship("FeedbackVote", back_populates="feedback", cascade="all, delete-orphan")
    notifications = relationship("FeedbackNotification", back_populates="feedback", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, status={self.status}, votes={self.vote_count})>"


class FeedbackVote(Base):
    __tablename__ = "FeedbackVote"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("Feedback.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    feedback = relationship("Feedback", back_populates="votes")
    user = relationship("User", back_populates="feedback_votes")

    # Unique constraint: one vote per user per feedback
    __table_args__ = (
        UniqueConstraint("feedback_id", "user_id", name="uq_feedback_user_vote"),
    )

    def __repr__(self):
        return f"<FeedbackVote(feedback_id={self.feedback_id}, user_id={self.user_id})>"


class FeedbackNotification(Base):
    __tablename__ = "FeedbackNotification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("Feedback.id", ondelete="CASCADE"), nullable=False)
    notified_at = Column(DateTime, server_default=func.now())
    notification_type = Column(String(50), nullable=False)  # threshold_reached, status_changed, etc.
    is_sent = Column(SmallInteger, default=0)  # 0: pending, 1: sent

    # Relationships
    feedback = relationship("Feedback", back_populates="notifications")

    def __repr__(self):
        return f"<FeedbackNotification(id={self.id}, feedback_id={self.feedback_id}, type={self.notification_type})>"
