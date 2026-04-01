"""
Book Vectorization Service.

Converts book content into vector embeddings for RAG.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from books.models.user_book import UserBook
from books.services.book_parser_service import BookParserService
from rag.models.document_chunk import DocumentChunk
from rag.services.embedding_service import EmbeddingService
from rag.config import RAGConfig

logger = logging.getLogger(__name__)


class BookVectorizationService:
    """
    Service for vectorizing book content.
    
    Processes books by:
    1. Reading and parsing content
    2. Chunking into manageable pieces
    3. Generating embeddings
    4. Storing in database
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize book vectorization service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.parser = BookParserService(db)
        self.embedding_service = EmbeddingService()
        self.chunk_size = RAGConfig.CHUNK_SIZE
        self.chunk_overlap = RAGConfig.CHUNK_OVERLAP
    
    async def vectorize_book(self, book_id: int) -> Dict[str, Any]:
        """
        Vectorize a book's content.
        
        Args:
            book_id: Book ID to vectorize
            
        Returns:
            Result with chunk count and status
        """
        # Get book
        book = await self._get_book(book_id)
        if not book:
            return {"success": False, "error": "Book not found"}
        
        # Read content
        content = self.parser.read_file_content(book.file_path)
        if not content:
            return {"success": False, "error": "Failed to read book content"}
        
        # Check if already vectorized
        existing = await self._check_existing_chunks(book_id)
        if existing:
            logger.info(f"Book {book_id} already has {existing} chunks")
            return {
                "success": True,
                "chunks": existing,
                "message": "Book already vectorized"
            }
        
        # Chunk content
        chunks = self._chunk_content(content, book.title)
        
        if not chunks:
            return {"success": False, "error": "Failed to chunk content"}
        
        # Generate embeddings and store
        await self._store_chunks(book_id, chunks)
        
        return {
            "success": True,
            "chunks": len(chunks),
            "book_id": book_id,
            "book_title": book.title
        }
    
    async def _get_book(self, book_id: int) -> Optional[UserBook]:
        """Get book by ID."""
        result = await self.db.execute(
            select(UserBook).where(UserBook.id == book_id)
        )
        return result.scalar_one_or_none()
    
    async def _check_existing_chunks(self, book_id: int) -> Optional[int]:
        """Check if book already has chunks."""
        result = await self.db.execute(
            select(DocumentChunk.id)
            .where(DocumentChunk.book_id == book_id)
            .limit(1)
        )
        row = result.first()
        if row:
            # Count total chunks
            count_result = await self.db.execute(
                select(DocumentChunk.id)
                .where(DocumentChunk.book_id == book_id)
            )
            return len(count_result.all())
        return None
    
    def _chunk_content(
        self,
        content: str,
        book_title: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk book content into manageable pieces.
        
        Strategy:
        1. Split by chapters (if Markdown with # headings)
        2. Split long paragraphs into chunk_size pieces
        3. Add overlap for context
        """
        chunks = []
        
        # Try to split by chapters first (Markdown)
        if '# ' in content:
            chapters = self._split_by_chapters(content)
            for chapter in chapters:
                chapter_chunks = self._chunk_text(
                    chapter['content'],
                    chapter=chapter.get('title', ''),
                    page=chapter.get('page', 0)
                )
                chunks.extend(chapter_chunks)
        else:
            # No chapter markers, chunk by size
            chunks = self._chunk_text(content)
        
        logger.info(f"Created {len(chunks)} chunks for '{book_title}'")
        return chunks
    
    def _split_by_chapters(self, content: str) -> List[Dict[str, Any]]:
        """Split Markdown content by chapter headings."""
        chapters = []
        current_chapter = None
        current_content = []
        current_page = 0
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('# '):
                # Save previous chapter
                if current_chapter is not None:
                    chapters.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content),
                        'page': current_page
                    })
                
                current_chapter = line[2:].strip()
                current_content = []
                # Estimate page number (rough: 30 lines per page)
                current_page = (i // 30) + 1
            else:
                current_content.append(line)
        
        # Save last chapter
        if current_chapter:
            chapters.append({
                'title': current_chapter,
                'content': '\n'.join(current_content),
                'page': current_page
            })
        
        return chapters
    
    def _chunk_text(
        self,
        text: str,
        chapter: str = "",
        page: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            chapter: Chapter name
            page: Page number
            
        Returns:
            List of chunk dicts
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para.split())  # Word count
            
            # If paragraph itself is too long, split it
            if para_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append({
                        'chapter': chapter,
                        'content': '\n\n'.join(current_chunk),
                        'page': page,
                        'token_count': current_length
                    })
                    current_chunk = []
                    current_length = 0
                
                # Split long paragraph
                sentences = para.split('.')
                for sent in sentences:
                    sent = sent.strip() + '.'
                    sent_length = len(sent.split())
                    
                    if current_length + sent_length > self.chunk_size:
                        chunks.append({
                            'chapter': chapter,
                            'content': '\n'.join(current_chunk),
                            'page': page,
                            'token_count': current_length
                        })
                        # Keep overlap
                        current_chunk = current_chunk[-2:] if len(current_chunk) >= 2 else []
                        current_length = sum(len(c.split()) for c in current_chunk)
                    
                    current_chunk.append(sent)
                    current_length += sent_length
            else:
                # Add paragraph to current chunk
                if current_length + para_length > self.chunk_size:
                    # Save current chunk
                    chunks.append({
                        'chapter': chapter,
                        'content': '\n\n'.join(current_chunk),
                        'page': page,
                        'token_count': current_length
                    })
                    # Keep overlap
                    current_chunk = current_chunk[-(self.chunk_overlap // 100):] if self.chunk_overlap > 0 else []
                    current_length = sum(len(c.split()) for c in current_chunk)
                
                current_chunk.append(para)
                current_length += para_length
        
        # Save last chunk
        if current_chunk:
            chunks.append({
                'chapter': chapter,
                'content': '\n\n'.join(current_chunk),
                'page': page,
                'token_count': current_length
            })
        
        return chunks
    
    async def _store_chunks(self, book_id: int, chunks: List[Dict[str, Any]]) -> None:
        """
        Generate embeddings and store chunks.
        
        Args:
            book_id: Book ID
            chunks: List of chunk dicts
        """
        # Generate embeddings in batches
        contents = [c['content'] for c in chunks]
        
        logger.info(f"Generating {len(contents)} embeddings...")
        embeddings = await self.embedding_service.embed_batch(contents, batch_size=32)
        
        # Store chunks
        for i, chunk in enumerate(chunks):
            doc_chunk = DocumentChunk(
                book_id=book_id,
                chapter=chunk.get('chapter', ''),
                content=chunk['content'],
                embedding=embeddings[i],
                page_number=chunk.get('page'),
                chunk_index=i,
                token_count=chunk.get('token_count'),
                metadata=json.dumps({
                    'source': f"Book {book_id}",
                    'created_at': datetime.utcnow().isoformat()
                })
            )
            self.db.add(doc_chunk)
        
        await self.db.commit()
        logger.info(f"Stored {len(chunks)} chunks for book {book_id}")
    
    async def vectorize_knowledge_point(
        self,
        knowledge_id: int,
        knowledge_name: str,
        knowledge_description: Optional[str],
        subject: str,
        parent_name: Optional[str] = None
    ) -> bool:
        """
        Vectorize a knowledge point.
        
        Args:
            knowledge_id: Knowledge point ID
            knowledge_name: Knowledge point name
            knowledge_description: Description
            subject: Subject area
            parent_name: Parent knowledge point name (optional)
            
        Returns:
            True if successful
        """
        # Build text for embedding
        text_parts = [f"{subject}: {knowledge_name}"]
        if knowledge_description:
            text_parts.append(knowledge_description)
        if parent_name:
            text_parts.insert(0, f"{parent_name} >")
        
        text = " ".join(text_parts)
        
        # Generate embedding
        embedding = await self.embedding_service.embed_text(text)
        
        # Store
        from rag.models.knowledge_embedding import KnowledgeEmbedding
        
        ke = KnowledgeEmbedding(
            knowledge_id=knowledge_id,
            content=text,
            embedding=embedding,
            metadata=json.dumps({
                'name': knowledge_name,
                'subject': subject,
                'parent': parent_name
            })
        )
        
        self.db.add(ke)
        await self.db.commit()
        
        logger.info(f"Vectorized knowledge point {knowledge_id}: {knowledge_name}")
        return True
