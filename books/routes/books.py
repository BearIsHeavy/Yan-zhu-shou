"""
User Books API Routes.

Provides RESTful endpoints for book upload and management.
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from books.services.book_upload_service import BookUploadService
from books.services.book_parser_service import BookParserService
from books.schemas.book import BookStatusEnum, UserBookResponse, BookUploadResponse
import models

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/upload", response_model=BookUploadResponse, status_code=201)
async def upload_book(
    file: UploadFile = File(..., description="Book file (PDF, Markdown, or DOCX)"),
    title: Optional[str] = Form(None, description="Book title (optional, defaults to filename)"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a book for knowledge extraction.
    
    **Supported formats:** PDF, Markdown (.md), DOCX
    **Max file size:** 50MB
    
    The book will be processed asynchronously to extract knowledge points.
    """
    # Read file content
    file_content = await file.read()
    
    if not file_content or len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    service = BookUploadService(db, current_user.user_id)
    
    try:
        book = await service.upload_book(
            file_content=file_content,
            original_filename=file.filename or "untitled",
            title=title,
        )
        
        return BookUploadResponse(
            id=book.id,
            title=book.title,
            file_path=book.file_path,
            status=BookStatusEnum(book.status),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=List[UserBookResponse])
async def list_books(
    status: Optional[BookStatusEnum] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List user's uploaded books.
    """
    service = BookUploadService(db, current_user.user_id)
    books = await service.get_user_books(status=status, limit=limit, offset=offset)
    return books


@router.get("/{book_id}", response_model=UserBookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get a specific book by ID.
    """
    service = BookUploadService(db, current_user.user_id)
    book = await service.get_book(book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a book.
    """
    service = BookUploadService(db, current_user.user_id)
    success = await service.delete_book(book_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return None


@router.post("/{book_id}/parse")
async def parse_book(
    book_id: int,
    subject: Optional[str] = Form(None, description="Subject context for better extraction"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Trigger knowledge extraction for a book.
    
    This processes the book content and extracts a knowledge tree structure.
    Processing happens asynchronously.
    """
    service = BookUploadService(db, current_user.user_id)
    book = await service.get_book(book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book.status == BookStatusEnum.PROCESSING:
        raise HTTPException(status_code=400, detail="Book is already being processed")
    
    # Update status to processing
    await service.update_book_status(book_id, BookStatusEnum.PROCESSING)
    
    # Parse book in background
    from ai_analysis.tasks.analysis_tasks import process_book_knowledge
    from fastapi import BackgroundTasks
    
    # Note: In production, use Celery/RQ for background tasks
    # For now, we'll process immediately but this should be moved to background
    parser = BookParserService(db)
    result = await parser.parse_book(book.file_path, subject=subject)
    
    if result["success"]:
        await service.update_book_status(
            book_id,
            BookStatusEnum.COMPLETED,
            knowledge_tree=result.get("knowledge_tree"),
        )
    else:
        await service.update_book_status(
            book_id,
            BookStatusEnum.FAILED,
            error_message=result.get("error", "Unknown error"),
        )
    
    return {
        "book_id": book_id,
        "status": "completed" if result["success"] else "failed",
        "result": result,
    }


@router.get("/{book_id}/content")
async def get_book_content(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get book content as text.
    """
    service = BookUploadService(db, current_user.user_id)
    book = await service.get_book(book_id)
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    parser = BookParserService(db)
    content = parser.read_file_content(book.file_path)
    
    if not content:
        raise HTTPException(status_code=500, detail="Failed to read book content")
    
    return {
        "book_id": book_id,
        "title": book.title,
        "content": content[:10000],  # Limit content length
        "truncated": len(content) > 10000,
    }
