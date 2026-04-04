"""
Retrieval Service.

Semantic search using vector embeddings.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload

from rag.models.knowledge_embedding import KnowledgeEmbedding
from rag.models.document_chunk import DocumentChunk
from rag.models.rag_query import RAGQuery
from rag.services.embedding_service import EmbeddingService
from rag.config import RAGConfig

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service for semantic retrieval using vector embeddings.
    
    Supports:
    - Knowledge point search
    - Document chunk search
    - Hybrid search (vector + keyword)
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize retrieval service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = EmbeddingService()
        self.top_k = RAGConfig.SEARCH_TOP_K
        self.threshold = RAGConfig.SIMILARITY_THRESHOLD
    
    async def search_similar_knowledge(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge points.
        
        Args:
            query: Search query
            limit: Max results (default: from config)
            threshold: Similarity threshold (default: from config)
            subject: Filter by subject
            
        Returns:
            List of results with knowledge point info and similarity score
        """
        limit = limit or self.top_k
        threshold = threshold or self.threshold
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Use pgvector similarity search
        # 1 - (embedding <=> query_embedding) gives cosine similarity
        similarity = 1 - (KnowledgeEmbedding.embedding.op('<=>')(query_embedding))
        
        stmt = (
            select(
                KnowledgeEmbedding,
                similarity.label('similarity')
            )
            .where(similarity >= threshold)
            .join(KnowledgeEmbedding.knowledge_point)
            .order_by(similarity.desc())
            .limit(limit)
        )
        
        if subject:
            stmt = stmt.where(KnowledgeEmbedding.knowledge_point.subject == subject)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        results = []
        for row in rows:
            embedding_obj, similarity = row
            kp = embedding_obj.knowledge_point
            results.append({
                'id': embedding_obj.id,
                'knowledge_id': kp.id,
                'name': kp.name,
                'subject': kp.subject,
                'content': embedding_obj.content,
                'similarity': float(similarity),
                'description': kp.description,
                'difficulty': kp.difficulty
            })
        
        return results
    
    async def search_similar_documents(
        self,
        query: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
        book_id: Optional[int] = None,
        chapter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks.
        
        Args:
            query: Search query
            limit: Max results
            threshold: Similarity threshold
            book_id: Filter by book ID
            chapter: Filter by chapter
            
        Returns:
            List of results with chunk info and similarity score
        """
        limit = limit or self.top_k
        threshold = threshold or self.threshold
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        similarity = 1 - (DocumentChunk.embedding.op('<=>')(query_embedding))
        
        stmt = (
            select(
                DocumentChunk,
                similarity.label('similarity')
            )
            .where(similarity >= threshold)
            .join(DocumentChunk.book)
            .order_by(similarity.desc())
            .limit(limit)
        )
        
        if book_id:
            stmt = stmt.where(DocumentChunk.book_id == book_id)
        
        if chapter:
            stmt = stmt.where(DocumentChunk.chapter == chapter)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        results = []
        for row in rows:
            chunk_obj, similarity = row
            book = chunk_obj.book
            results.append({
                'id': chunk_obj.id,
                'book_id': chunk_obj.book_id,
                'book_title': book.title,
                'chapter': chunk_obj.chapter,
                'content': chunk_obj.content,
                'page_number': chunk_obj.page_number,
                'similarity': float(similarity),
                'metadata': json.loads(chunk_obj.extra_meta) if chunk_obj.extra_meta else {}
            })
        
        return results
    
    async def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        include_knowledge: bool = True,
        include_documents: bool = True,
        subject: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform hybrid search across knowledge and documents.
        
        Args:
            query: Search query
            limit: Max results per category
            include_knowledge: Include knowledge points
            include_documents: Include document chunks
            subject: Filter knowledge by subject
            
        Returns:
            Dict with 'knowledge' and 'documents' keys
        """
        results = {
            'knowledge': [],
            'documents': []
        }
        
        if include_knowledge:
            results['knowledge'] = await self.search_similar_knowledge(
                query, limit=limit, subject=subject
            )
        
        if include_documents:
            results['documents'] = await self.search_similar_documents(
                query, limit=limit
            )
        
        return results
    
    async def log_query(
        self,
        user_id: int,
        query: str,
        results_count: int,
        response_type: str
    ) -> None:
        """
        Log a RAG query for analytics.
        
        Args:
            user_id: User ID
            query: Query text
            results_count: Number of results returned
            response_type: Type of response
        """
        # Generate query embedding (optional, for future analysis)
        query_embedding = await self.embedding_service.embed_text(query)
        
        rag_query = RAGQuery(
            user_id=user_id,
            query_text=query,
            query_embedding=query_embedding,
            results_count=results_count,
            response_type=response_type
        )
        
        self.db.add(rag_query)
        await self.db.flush()
    
    async def get_query_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's query history.
        
        Args:
            user_id: User ID
            limit: Max results
            
        Returns:
            List of query records
        """
        stmt = (
            select(RAGQuery)
            .where(RAGQuery.user_id == user_id)
            .order_by(RAGQuery.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        queries = result.scalars().all()
        
        return [
            {
                'id': q.id,
                'query_text': q.query_text,
                'results_count': q.results_count,
                'response_type': q.response_type,
                'created_at': q.created_at.isoformat()
            }
            for q in queries
        ]
