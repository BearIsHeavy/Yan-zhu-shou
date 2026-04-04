"""
Book Upload Service.

Handles book upload, storage, and metadata management.
"""

import os
import uuid
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from books.models.user_book import UserBook
from books.schemas.book import BookStatusEnum
from utils.file_storage import ensure_upload_dirs

logger = logging.getLogger(__name__)

# Upload directory for books
BOOKS_UPLOAD_DIR = "uploads/books"


class BookUploadService:
    """Service for handling book uploads."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize book upload service.
        
        Args:
            db: Database session
            user_id: User ID
        """
        self.db = db
        self.user_id = user_id
        self.upload_dir = os.path.join(BOOKS_UPLOAD_DIR, str(user_id))
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """
        Generate a unique filename preserving extension.
        
        Args:
            original_filename: Original filename
            
        Returns:
            Unique filename with UUID prefix
        """
        ext = os.path.splitext(original_filename)[1].lower()
        unique_id = uuid.uuid4().hex[:12]
        return f"{unique_id}{ext}"
    
    @staticmethod
    def _get_file_type(filename: str) -> Optional[str]:
        """
        Get file type from extension.
        
        Args:
            filename: Filename
            
        Returns:
            File type (pdf, markdown, docx) or None
        """
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.pdf': 'pdf',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.docx': 'docx',
            '.doc': 'docx',
        }
        return type_map.get(ext)
    
    async def upload_book(
        self,
        file_content: bytes,
        original_filename: str,
        title: Optional[str] = None,
    ) -> UserBook:
        """
        Upload a book file.
        
        Args:
            file_content: File content in bytes
            original_filename: Original filename
            title: Optional title (defaults to filename)
            
        Returns:
            Created UserBook record
        """
        # Validate file type
        file_type = self._get_file_type(original_filename)
        if not file_type:
            raise ValueError("Unsupported file type. Allowed: PDF, Markdown, DOCX")
        
        # Validate file size (max 50MB)
        if len(file_content) > 50 * 1024 * 1024:
            raise ValueError("File size exceeds 50MB limit")
        
        # Create upload directory
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(original_filename)
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Create database record
        book = UserBook(
            user_id=self.user_id,
            title=title or os.path.splitext(original_filename)[0],
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_content),
            status=BookStatusEnum.PENDING,
        )
        
        self.db.add(book)
        await self.db.flush()
        await self.db.refresh(book)
        
        logger.info(f"Uploaded book: {book.id} - {book.title}")
        return book
    
    async def get_book(self, book_id: int) -> Optional[UserBook]:
        """
        Get a book by ID.
        
        Args:
            book_id: Book ID
            
        Returns:
            UserBook or None
        """
        result = await self.db.execute(
            select(UserBook)
            .where(
                UserBook.id == book_id,
                UserBook.user_id == self.user_id
            )
            .options(selectinload(UserBook.user))
        )
        return result.scalar_one_or_none()
    
    async def get_user_books(
        self,
        status: Optional[BookStatusEnum] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[UserBook]:
        """
        Get user's books with optional status filter.
        
        Args:
            status: Filter by status
            limit: Limit results
            offset: Offset for pagination
            
        Returns:
            List of UserBook records
        """
        query = select(UserBook).where(UserBook.user_id == self.user_id)
        
        if status is not None:
            query = query.where(UserBook.status == status)
        
        query = query.order_by(UserBook.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_book(self, book_id: int) -> bool:
        """
        Delete a book (file and database record).
        
        Args:
            book_id: Book ID
            
        Returns:
            True if deleted
        """
        book = await self.get_book(book_id)
        
        if not book:
            return False
        
        # Delete file
        try:
            if os.path.exists(book.file_path):
                os.remove(book.file_path)
                logger.info(f"Deleted book file: {book.file_path}")
        except Exception as e:
            logger.error(f"Failed to delete book file: {e}")
        
        # Delete database record
        await self.db.delete(book)
        await self.db.commit()
        
        logger.info(f"Deleted book: {book_id}")
        return True
    
    async def update_book_status(
        self,
        book_id: int,
        status: BookStatusEnum,
        error_message: Optional[str] = None,
        knowledge_tree: Optional[dict] = None,
    ) -> Optional[UserBook]:
        """
        Update book processing status.
        
        Args:
            book_id: Book ID
            status: New status
            error_message: Error message if failed
            knowledge_tree: Extracted knowledge tree
            
        Returns:
            Updated UserBook or None
        """
        book = await self.get_book(book_id)
        
        if not book:
            return None
        
        book.status = status
        
        if error_message:
            book.error_message = error_message
        
        if knowledge_tree:
            import json
            book.knowledge_tree = json.dumps(knowledge_tree)
        
        if status == BookStatusEnum.COMPLETED:
            book.processed_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(book)
        
        logger.info(f"Updated book {book_id} status to {status.name}")
        return book
