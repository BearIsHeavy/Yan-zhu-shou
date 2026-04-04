"""
Recommendation Engine.

Generates personalized learning recommendations based on weak point analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

import models
from ai_analysis.llm_client import LLMClient
from ai_analysis.config import AIAnalysisConfig

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine for generating learning recommendations."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize recommendation engine.
        
        Args:
            db: Database session
            user_id: User ID
        """
        self.db = db
        self.user_id = user_id
        self.llm = LLMClient() if AIAnalysisConfig.is_available() else None
    
    async def get_user_level(self) -> str:
        """
        Determine user's current level based on performance.
        
        Returns:
            User level: 'beginner', 'intermediate', or 'advanced'
        """
        # Get overall statistics
        query = (
            select(
                func.count().label('total'),
                func.sum(models.UserQuestionLog.is_correct.cast(int)).label('correct'),
            )
            .where(models.UserQuestionLog.user_id == self.user_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row or row.total == 0:
            return "beginner"
        
        accuracy = row.correct / row.total
        
        if accuracy >= 0.8:
            return "advanced"
        elif accuracy >= 0.6:
            return "intermediate"
        else:
            return "beginner"
    
    async def get_priority_knowledge_points(
        self,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge points that need most attention.
        
        Args:
            limit: Number of points to return
            
        Returns:
            List of priority knowledge points
        """
        # Query wrong questions grouped by category
        query = (
            select(
                models.QBQuestion.category,
                func.count().label('error_count'),
                func.avg(models.QBQuestion.qus_type).label('difficulty'),
            )
            .join(
                models.UserQuestionLog,
                models.UserQuestionLog.question_no == models.QBQuestion.No
            )
            .where(
                and_(
                    models.UserQuestionLog.user_id == self.user_id,
                    models.UserQuestionLog.is_correct == False,
                    models.UserQuestionLog.is_mastered == False
                )
            )
            .group_by(models.QBQuestion.category)
            .order_by(func.count().desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "knowledge": row.category,
                "error_count": row.error_count,
                "priority": i + 1,
            }
            for i, row in enumerate(rows)
        ]
    
    async def generate_practice_recommendations(
        self,
        weak_points: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate practice question recommendations.
        
        Args:
            weak_points: List of identified weak points
            
        Returns:
            List of practice recommendations
        """
        recommendations = []
        
        for point in weak_points[:3]:  # Top 3 weak points
            # Find related questions from question banks
            query = (
                select(models.QBQuestion)
                .where(
                    and_(
                        models.QBQuestion.category == point["knowledge"],
                        models.QBQuestion.is_public == True
                    )
                )
                .limit(5)
            )
            
            result = await self.db.execute(query)
            questions = result.scalars().all()
            
            if questions:
                recommendations.append({
                    "type": "practice",
                    "priority": point.get("priority", 5),
                    "knowledge": point["knowledge"],
                    "action": f"Practice 5 questions on {point['knowledge']}",
                    "question_ids": [q.No for q in questions],
                    "estimated_time": "20 minutes",
                })
        
        return recommendations
    
    async def generate_review_recommendations(
        self,
        weak_points: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate review recommendations.
        
        Args:
            weak_points: List of weak points
            
        Returns:
            List of review recommendations
        """
        recommendations = []
        
        for point in weak_points[:3]:
            recommendations.append({
                "type": "review",
                "priority": point.get("priority", 5),
                "knowledge": point["knowledge"],
                "action": (
                    f"Review key concepts and formulas for {point['knowledge']}. "
                    f"Focus on common error patterns."
                ),
                "estimated_time": "15 minutes",
            })
        
        return recommendations
    
    async def generate_ai_recommendations(
        self,
        weak_points: List[Dict[str, Any]],
        user_level: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered personalized recommendations.
        
        Args:
            weak_points: List of weak points
            user_level: User's current level
            
        Returns:
            AI-generated recommendations
        """
        if not self.llm:
            return []
        
        try:
            recommendations = await self.llm.generate_recommendations(
                weak_points=weak_points,
                user_level=user_level,
            )
            return recommendations
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            return []
    
    async def get_all_recommendations(self) -> Dict[str, Any]:
        """
        Get comprehensive learning recommendations.
        
        Returns:
            Complete recommendations combining all sources
        """
        # Get user level
        user_level = await self.get_user_level()
        
        # Get priority knowledge points
        weak_points = await self.get_priority_knowledge_points(limit=5)
        
        # Generate recommendations from different sources
        practice_recs = await self.generate_practice_recommendations(weak_points)
        review_recs = await self.generate_review_recommendations(weak_points)
        
        ai_recs = []
        if AIAnalysisConfig.is_available():
            ai_recs = await self.generate_ai_recommendations(weak_points, user_level)
        
        # Combine all recommendations
        all_recommendations = practice_recs + review_recs + ai_recs
        
        # Sort by priority
        all_recommendations.sort(key=lambda x: x.get("priority", 5))
        
        return {
            "user_id": self.user_id,
            "user_level": user_level,
            "generated_at": datetime.utcnow().isoformat(),
            "weak_points": weak_points,
            "recommendations": all_recommendations,
            "total_count": len(all_recommendations),
        }
    
    async def get_next_study_plan(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a study plan for the next N days.
        
        Args:
            days: Number of days to plan
            
        Returns:
            Study plan schedule
        """
        weak_points = await self.get_priority_knowledge_points(limit=days)
        user_level = await self.get_user_level()
        
        # Distribute weak points across days
        daily_plan = []
        start_date = datetime.utcnow().date()
        
        for i, point in enumerate(weak_points):
            date = start_date + timedelta(days=i)
            daily_plan.append({
                "date": date.isoformat(),
                "focus": point["knowledge"],
                "tasks": [
                    {
                        "type": "review",
                        "description": f"Review {point['knowledge']} concepts",
                        "duration": 15,
                    },
                    {
                        "type": "practice",
                        "description": f"Practice {point['knowledge']} questions",
                        "duration": 25,
                    },
                ],
            })
        
        return {
            "user_id": self.user_id,
            "user_level": user_level,
            "plan_start": start_date.isoformat(),
            "plan_end": (start_date + timedelta(days=days)).isoformat(),
            "daily_plan": daily_plan,
            "total_days": len(daily_plan),
        }
