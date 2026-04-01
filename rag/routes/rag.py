"""
RAG API Routes.

Provides endpoints for:
- Semantic search
- RAG-enhanced analysis
- Q&A with textbook context
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
import models

from rag.services.retrieval_service import RetrievalService
from rag.services.rag_enhancer import RAGEnhancer
from rag.services.book_vectorization_service import BookVectorizationService

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/search")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    include_knowledge: bool = Query(True, description="Include knowledge points"),
    include_documents: bool = Query(True, description="Include document chunks"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Semantic search across knowledge points and textbooks.
    
    Uses vector embeddings to find semantically similar content.
    """
    retrieval = RetrievalService(db)
    
    results = await retrieval.hybrid_search(
        query=query,
        limit=limit,
        include_knowledge=include_knowledge,
        include_documents=include_documents,
        subject=subject
    )
    
    # Log query
    await retrieval.log_query(
        user_id=current_user.user_id,
        query=query,
        results_count=len(results.get('knowledge', [])) + len(results.get('documents', [])),
        response_type="search"
    )
    
    return results


@router.get("/search/knowledge")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    subject: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Search knowledge points semantically."""
    retrieval = RetrievalService(db)
    
    results = await retrieval.search_similar_knowledge(
        query=query,
        limit=limit,
        subject=subject
    )
    
    return {"results": results}


@router.get("/search/documents")
async def search_documents(
    query: str = Query(..., description="Search query"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Search textbook content semantically."""
    retrieval = RetrievalService(db)
    
    results = await retrieval.search_similar_documents(
        query=query,
        limit=limit,
        book_id=book_id
    )
    
    return {"results": results}


@router.post("/analyze")
async def analyze_with_rag(
    wrong_questions: List[dict],
    subject: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Analyze wrong questions with RAG enhancement.
    
    Retrieves relevant textbook content and knowledge points,
    then generates personalized analysis using LLM.
    """
    enhancer = RAGEnhancer(db)
    
    analysis = await enhancer.analyze_wrong_questions_with_rag(
        wrong_questions=wrong_questions,
        user_id=current_user.user_id,
        subject=subject
    )
    
    return analysis


@router.post("/answer")
async def answer_question(
    question: str = Query(..., description="Student's question"),
    subject: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Answer student question using RAG.
    
    Retrieves relevant context from textbooks and knowledge base,
    then generates an answer with citations.
    """
    enhancer = RAGEnhancer(db)
    
    result = await enhancer.answer_question_with_rag(
        question=question,
        user_id=current_user.user_id,
        subject=subject
    )
    
    return result


@router.post("/books/{book_id}/vectorize")
async def vectorize_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Vectorize a book for semantic search.
    
    Processes the book content, chunks it, generates embeddings,
    and stores them for RAG retrieval.
    """
    service = BookVectorizationService(db)
    
    result = await service.vectorize_book(book_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.get("/query-history")
async def get_query_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's RAG query history."""
    retrieval = RetrievalService(db)
    
    history = await retrieval.get_query_history(
        user_id=current_user.user_id,
        limit=limit
    )
    
    return {"history": history}
