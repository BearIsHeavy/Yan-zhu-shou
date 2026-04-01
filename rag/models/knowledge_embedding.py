"""
Knowledge Embedding Model.

Stores vector embeddings for knowledge points.
"""

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback if pgvector not installed
    Vector = None


class KnowledgeEmbedding(Base):
    """
    Vector embedding for a knowledge point.
    
    Attributes:
        id: Primary key
        knowledge_id: Reference to knowledge_points
        content: Original text content used for embedding
        embedding: Vector embedding (1536 dimensions for OpenAI)
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "knowledge_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(
        Integer,
        ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536) if Vector else Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    knowledge_point = relationship("KnowledgePoint")
    
    def __repr__(self):
        return f"<KnowledgeEmbedding(id={self.id}, knowledge_id={self.knowledge_id})>"
