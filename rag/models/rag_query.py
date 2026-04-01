"""
RAG Query Model.

Stores query history for analytics and improvement.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class RAGQuery(Base):
    """
    RAG query history.
    
    Attributes:
        id: Primary key
        user_id: Reference to User
        query_text: Original query text
        query_embedding: Query vector embedding
        results_count: Number of results returned
        response_type: Type of response (analysis, recommendation, search)
        created_at: Query timestamp
    """
    
    __tablename__ = "rag_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("User.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536) if Vector else Text, nullable=True)
    results_count = Column(Integer, default=0)
    response_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<RAGQuery(id={self.id}, user_id={self.user_id}, type={self.response_type})>"
