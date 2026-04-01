from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
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
    developer_response = Column(Text, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="feedbacks")
    votes = relationship("FeedbackVote", back_populates="feedback", cascade="all, delete-orphan")
    notifications = relationship("FeedbackNotification", back_populates="feedback", cascade="all, delete-orphan")

    # Computed property (dynamically calculated from relationships)
    @hybrid_property
    def vote_count(self) -> int:
        """Get vote count dynamically from relationships."""
        return len(self.votes) if self.votes else 0

    def __repr__(self):
        return f"<Feedback(id={self.id}, user_id={self.user_id}, status={self.status})>"


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
    """Feedback notification model for tracking notifications sent to users."""
    __tablename__ = "FeedbackNotification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("Feedback.id", ondelete="CASCADE"), nullable=False)
    
    # Notification recipient
    recipient_user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=True)
    
    # Notification channel (email, in_app, webhook)
    notification_channel = Column(String(20), default="in_app", nullable=False)
    
    # Notification content
    notification_content = Column(Text, nullable=True)
    
    # Notification type (threshold_reached, status_changed, etc.)
    notification_type = Column(String(50), nullable=False)
    
    # Delivery status
    is_sent = Column(SmallInteger, default=0)  # 0: pending, 1: sent
    sent_at = Column(DateTime, nullable=True)
    
    # Read status
    is_read = Column(SmallInteger, default=0)  # 0: unread, 1: read
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    notified_at = Column(DateTime, server_default=func.now())

    # Relationships
    feedback = relationship("Feedback", back_populates="notifications")
    recipient = relationship("User")

    def __repr__(self):
        return f"<FeedbackNotification(id={self.id}, feedback_id={self.feedback_id}, type={self.notification_type})>"
