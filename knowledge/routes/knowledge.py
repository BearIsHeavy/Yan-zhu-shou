"""
Knowledge Point API Routes.

Provides RESTful endpoints for knowledge point management.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from knowledge.services.knowledge_service import KnowledgeService
from knowledge.schemas.knowledge import (
    KnowledgePointCreate,
    KnowledgePointUpdate,
    KnowledgePointResponse,
    KnowledgePointTreeResponse,
    QuestionKnowledgeCreate,
    QuestionKnowledgeResponse,
)
import models

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/tree", response_model=List[KnowledgePointTreeResponse])
async def get_knowledge_tree(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get knowledge tree structure.
    
    Returns a hierarchical tree of knowledge points.
    """
    service = KnowledgeService(db)
    tree = await service.build_knowledge_tree(subject=subject)
    return tree


@router.get("", response_model=List[KnowledgePointResponse])
async def list_knowledge_points(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    parent_id: Optional[int] = Query(None, description="Filter by parent ID"),
    limit: int = Query(100, ge=1, le=500, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List knowledge points with filtering.
    """
    service = KnowledgeService(db)
    points = await service.get_knowledge_points(
        subject=subject,
        parent_id=parent_id,
        limit=limit,
        offset=offset,
    )
    return points


@router.get("/{knowledge_id}", response_model=KnowledgePointResponse)
async def get_knowledge_point(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get a specific knowledge point by ID.
    """
    service = KnowledgeService(db)
    point = await service.get_knowledge_point(knowledge_id)
    
    if not point:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    return point


@router.post("", response_model=KnowledgePointResponse, status_code=201)
async def create_knowledge_point(
    data: KnowledgePointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new knowledge point.
    
    **Requires admin or developer role.**
    """
    if current_user.role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = KnowledgeService(db)
    point = await service.create_knowledge_point(data)
    return point


@router.put("/{knowledge_id}", response_model=KnowledgePointResponse)
async def update_knowledge_point(
    knowledge_id: int,
    data: KnowledgePointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update a knowledge point.
    
    **Requires admin or developer role.**
    """
    if current_user.role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = KnowledgeService(db)
    point = await service.update_knowledge_point(knowledge_id, data)
    
    if not point:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    return point


@router.delete("/{knowledge_id}", status_code=204)
async def delete_knowledge_point(
    knowledge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete a knowledge point (soft delete).
    
    **Requires admin or developer role.**
    """
    if current_user.role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = KnowledgeService(db)
    success = await service.delete_knowledge_point(knowledge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge point not found")
    
    return None


@router.post("/questions/link", response_model=QuestionKnowledgeResponse)
async def link_question_to_knowledge(
    data: QuestionKnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Link a question to a knowledge point.
    
    **Requires admin or developer role.**
    """
    if current_user.role not in ("admin", "developer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    service = KnowledgeService(db)
    
    try:
        association = await service.link_question_to_knowledge(
            question_no=data.question_no,
            knowledge_id=data.knowledge_id,
            weight=data.weight,
        )
        return association
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/questions/{question_no}/knowledge", response_model=List[QuestionKnowledgeResponse])
async def get_question_knowledge(
    question_no: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get knowledge points associated with a question.
    """
    service = KnowledgeService(db)
    associations = await service.get_question_knowledge(question_no)
    return associations
