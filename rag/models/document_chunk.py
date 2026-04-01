"""
Document Chunk Model.

Stores chunked document content with vector embeddings.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class DocumentChunk(Base):
    """
    Chunk of a document with vector embedding.
    
    Attributes:
        id: Primary key
        book_id: Reference to user_books
        chapter: Chapter name
        content: Chunk content
        embedding: Vector embedding
        page_number: Page number in original document
        chunk_index: Index of chunk within document
        token_count: Number of tokens in chunk
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(
        Integer,
        ForeignKey("user_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chapter = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536) if Vector else Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    book = relationship("UserBook")
    
    # Index for vector similarity search
    __table_args__ = (
        Index('idx_dc_chapter', 'chapter'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, book_id={self.book_id}, chapter={self.chapter})>"
