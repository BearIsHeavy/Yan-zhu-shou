"""
Knowledge Service.

Business logic for knowledge point management.
"""

import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete as delete_stmt
from sqlalchemy.orm import selectinload

from knowledge.models.knowledge_point import KnowledgePoint
from knowledge.models.question_knowledge import QuestionKnowledge
from knowledge.schemas.knowledge import KnowledgePointCreate, KnowledgePointUpdate

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing knowledge points."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize knowledge service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_knowledge_point(self, knowledge_id: int) -> Optional[KnowledgePoint]:
        """
        Get a knowledge point by ID.
        
        Args:
            knowledge_id: Knowledge point ID
            
        Returns:
            Knowledge point or None
        """
        result = await self.db.execute(
            select(KnowledgePoint)
            .where(KnowledgePoint.id == knowledge_id)
            .options(selectinload(KnowledgePoint.parent))
        )
        return result.scalar_one_or_none()
    
    async def get_knowledge_points(
        self,
        subject: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KnowledgePoint]:
        """
        Get knowledge points with filters.
        
        Args:
            subject: Filter by subject
            parent_id: Filter by parent ID
            is_active: Filter by active status
            limit: Limit results
            offset: Offset for pagination
            
        Returns:
            List of knowledge points
        """
        query = select(KnowledgePoint).where(KnowledgePoint.is_active == is_active)
        
        if subject:
            query = query.where(KnowledgePoint.subject == subject)
        
        if parent_id is not None:
            query = query.where(KnowledgePoint.parent_id == parent_id)
        
        query = query.order_by(KnowledgePoint.name).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_knowledge_point(
        self,
        data: KnowledgePointCreate,
    ) -> KnowledgePoint:
        """
        Create a new knowledge point.
        
        Args:
            data: Creation data
            
        Returns:
            Created knowledge point
        """
        knowledge_point = KnowledgePoint(
            name=data.name,
            subject=data.subject,
            difficulty=data.difficulty,
            description=data.description,
            parent_id=data.parent_id,
        )
        
        self.db.add(knowledge_point)
        await self.db.flush()
        await self.db.refresh(knowledge_point)
        
        logger.info(f"Created knowledge point: {knowledge_point.id} - {knowledge_point.name}")
        return knowledge_point
    
    async def update_knowledge_point(
        self,
        knowledge_id: int,
        data: KnowledgePointUpdate,
    ) -> Optional[KnowledgePoint]:
        """
        Update a knowledge point.
        
        Args:
            knowledge_id: Knowledge point ID
            data: Update data
            
        Returns:
            Updated knowledge point or None
        """
        knowledge_point = await self.get_knowledge_point(knowledge_id)
        
        if not knowledge_point:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(knowledge_point, field, value)
        
        await self.db.flush()
        await self.db.refresh(knowledge_point)
        
        logger.info(f"Updated knowledge point: {knowledge_id}")
        return knowledge_point
    
    async def delete_knowledge_point(self, knowledge_id: int) -> bool:
        """
        Delete a knowledge point (soft delete by setting is_active=False).
        
        Args:
            knowledge_id: Knowledge point ID
            
        Returns:
            True if deleted
        """
        knowledge_point = await self.get_knowledge_point(knowledge_id)
        
        if not knowledge_point:
            return False
        
        # Soft delete
        knowledge_point.is_active = False
        await self.db.flush()
        
        logger.info(f"Soft deleted knowledge point: {knowledge_id}")
        return True
    
    async def hard_delete_knowledge_point(self, knowledge_id: int) -> bool:
        """
        Permanently delete a knowledge point and its associations.
        
        Args:
            knowledge_id: Knowledge point ID
            
        Returns:
            True if deleted
        """
        await self.db.execute(
            delete_stmt(QuestionKnowledge).where(
                QuestionKnowledge.knowledge_id == knowledge_id
            )
        )
        
        await self.db.execute(
            delete_stmt(KnowledgePoint).where(KnowledgePoint.id == knowledge_id)
        )
        
        await self.db.commit()
        
        logger.info(f"Hard deleted knowledge point: {knowledge_id}")
        return True
    
    async def build_knowledge_tree(
        self,
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build a knowledge tree structure.
        
        Args:
            subject: Optional subject filter
            
        Returns:
            Tree structure as nested dicts
        """
        # Get all root knowledge points (no parent)
        query = select(KnowledgePoint).where(
            and_(
                KnowledgePoint.is_active == True,
                KnowledgePoint.parent_id.is_(None)
            )
        )
        
        if subject:
            query = query.where(KnowledgePoint.subject == subject)
        
        query = query.order_by(KnowledgePoint.name)
        
        result = await self.db.execute(query)
        root_points = result.scalars().all()
        
        # Build tree recursively
        async def build_node(parent: KnowledgePoint) -> Dict[str, Any]:
            node = {
                "id": parent.id,
                "name": parent.name,
                "subject": parent.subject,
                "difficulty": parent.difficulty,
                "description": parent.description,
                "children": [],
            }
            
            # Get children
            children_query = select(KnowledgePoint).where(
                and_(
                    KnowledgePoint.parent_id == parent.id,
                    KnowledgePoint.is_active == True
                )
            ).order_by(KnowledgePoint.name)
            
            children_result = await self.db.execute(children_query)
            children = children_result.scalars().all()
            
            for child in children:
                node["children"].append(await build_node(child))
            
            return node
        
        tree = []
        for root in root_points:
            tree.append(await build_node(root))
        
        return tree
    
    async def link_question_to_knowledge(
        self,
        question_no: int,
        knowledge_id: int,
        weight: float = 1.0,
    ) -> QuestionKnowledge:
        """
        Link a question to a knowledge point.
        
        Args:
            question_no: Question ID
            knowledge_id: Knowledge point ID
            weight: Association weight
            
        Returns:
            Created association
        """
        # Check if already exists
        existing = await self.db.execute(
            select(QuestionKnowledge).where(
                and_(
                    QuestionKnowledge.question_no == question_no,
                    QuestionKnowledge.knowledge_id == knowledge_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Question already linked to this knowledge point")
        
        association = QuestionKnowledge(
            question_no=question_no,
            knowledge_id=knowledge_id,
            weight=weight,
        )
        
        self.db.add(association)
        await self.db.flush()
        await self.db.refresh(association)
        
        logger.info(f"Linked question {question_no} to knowledge {knowledge_id}")
        return association
    
    async def get_question_knowledge(
        self,
        question_no: int,
    ) -> List[QuestionKnowledge]:
        """
        Get knowledge points associated with a question.
        
        Args:
            question_no: Question ID
            
        Returns:
            List of associations
        """
        result = await self.db.execute(
            select(QuestionKnowledge)
            .where(QuestionKnowledge.question_no == question_no)
            .options(selectinload(QuestionKnowledge.knowledge_point))
        )
        return list(result.scalars().all())
