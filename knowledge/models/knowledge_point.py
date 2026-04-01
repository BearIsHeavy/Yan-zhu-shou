"""
Knowledge Point Model.

Represents a knowledge point in the knowledge graph.
Supports hierarchical structure through parent-child relationships.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, SmallInteger, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class KnowledgePoint(Base):
    """
    Knowledge point in the knowledge graph.
    
    Attributes:
        id: Primary key
        name: Knowledge point name
        subject: Subject area (e.g., 'Mathematics', 'Physics')
        parent_id: Parent knowledge point ID (for hierarchy)
        difficulty: Difficulty level (1-5)
        description: Detailed description
        is_active: Whether this knowledge point is active
    """
    
    __tablename__ = "knowledge_points"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("knowledge_points.id", ondelete="CASCADE"), nullable=True)
    difficulty = Column(SmallInteger, default=3, nullable=False)  # 1-5
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship(
        "KnowledgePoint",
        remote_side=[id],
        backref="children",
    )
    
    # Question associations
    questions = relationship(
        "QuestionKnowledge",
        back_populates="knowledge_point",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<KnowledgePoint(id={self.id}, name={self.name}, subject={self.subject})>"
