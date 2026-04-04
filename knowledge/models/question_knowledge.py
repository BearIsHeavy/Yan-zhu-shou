"""
Question-Knowledge Association Model.

Links questions to knowledge points with weights.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class QuestionKnowledge(Base):
    """
    Association between questions and knowledge points.
    
    Attributes:
        id: Primary key
        question_no: Question ID (foreign key to qb_questions)
        knowledge_id: Knowledge point ID
        weight: Association strength (0.0-1.0)
    """
    
    __tablename__ = "question_knowledge"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_no = Column(
        Integer,
        ForeignKey("qb_questions.No", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    knowledge_id = Column(
        Integer,
        ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight = Column(Float, default=1.0, nullable=False)  # 0.0-1.0
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    knowledge_point = relationship("KnowledgePoint", back_populates="questions")
    
    # Unique constraint: one association per question-knowledge pair
    __table_args__ = (
        UniqueConstraint("question_no", "knowledge_id", name="uq_question_knowledge"),
    )
    
    def __repr__(self):
        return f"<QuestionKnowledge(question_no={self.question_no}, knowledge_id={self.knowledge_id})>"
