"""
User Book Model.

Represents a book uploaded by a user for knowledge extraction.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, SmallInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class UserBook(Base):
    """
    User-uploaded book for knowledge extraction.
    
    Attributes:
        id: Primary key
        user_id: Owner user ID
        title: Book title
        file_path: Path to the uploaded file
        file_type: File type (pdf, markdown, docx)
        file_size: File size in bytes
        status: Processing status
        knowledge_tree: Extracted knowledge structure (JSON)
        chapter_count: Number of chapters detected
    """
    
    __tablename__ = "user_books"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, markdown, docx
    file_size = Column(Integer, nullable=False)  # in bytes
    status = Column(SmallInteger, default=0, nullable=False)  # 0:pending, 1:processing, 2:completed, 3:failed
    knowledge_tree = Column(Text, nullable=True)  # JSON string
    chapter_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="books")
    
    def __repr__(self):
        return f"<UserBook(id={self.id}, title={self.title}, user_id={self.user_id})>"
