"""
Weak Point Analyzer.

Analyzes user's wrong questions to identify knowledge gaps and error patterns.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

import models
from ai_analysis.llm_client import LLMClient
from ai_analysis.config import AIAnalysisConfig

logger = logging.getLogger(__name__)


class WeakPointAnalyzer:
    """Analyzer for identifying user's weak points."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        """
        Initialize analyzer.
        
        Args:
            db: Database session
            user_id: User ID to analyze
        """
        self.db = db
        self.user_id = user_id
        self.llm = LLMClient() if AIAnalysisConfig.is_available() else None
    
    async def get_wrong_questions(
        self,
        limit: int = 50,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's wrong questions from database.
        
        Args:
            limit: Maximum questions to retrieve
            category: Optional category filter
            
        Returns:
            List of wrong question data
        """
        # Build query
        query = (
            select(models.UserQuestionLog, models.QBQuestion)
            .join(
                models.QBQuestion,
                models.UserQuestionLog.question_no == models.QBQuestion.No
            )
            .where(
                and_(
                    models.UserQuestionLog.user_id == self.user_id,
                    models.UserQuestionLog.is_correct == False
                )
            )
            .order_by(models.UserQuestionLog.attempt_time.desc())
            .limit(limit)
        )
        
        if category:
            query = query.where(models.QBQuestion.category == category)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Format for analysis
        questions = []
        for log, question in rows:
            questions.append({
                "log_id": log.id,
                "question_no": question.No,
                "category": question.category,
                "stem": question.stem,
                "qus_type": question.qus_type,
                "user_answer": log.user_answer,
                "correct_ans_summary": question.correct_ans_summary,
                "attempt_time": log.attempt_time.isoformat() if log.attempt_time else None,
                "is_mastered": log.is_mastered,
            })
        
        return questions
    
    async def analyze_by_category(self) -> Dict[str, Any]:
        """
        Analyze wrong questions by category.
        
        Returns:
            Statistics grouped by category
        """
        query = (
            select(
                models.QBQuestion.category,
                func.count().label('error_count'),
                func.avg(models.QBQuestion.qus_type).label('avg_type'),
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
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        categories = {}
        total_errors = 0
        
        for row in rows:
            category, error_count, _ = row
            categories[category] = {
                "error_count": error_count,
                "percentage": 0,  # Will calculate below
            }
            total_errors += error_count
        
        # Calculate percentages
        for category in categories:
            if total_errors > 0:
                categories[category]["percentage"] = round(
                    categories[category]["error_count"] / total_errors * 100, 2
                )
        
        return {
            "total_errors": total_errors,
            "categories": categories,
            "top_weak_category": max(categories.items(), key=lambda x: x[1]["error_count"])[0] if categories else None,
        }
    
    async def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze error patterns in user's answers.
        
        Returns:
            Pattern analysis results
        """
        questions = await self.get_wrong_questions(limit=100)
        
        patterns = {
            "by_type": defaultdict(int),
            "recent_trend": "stable",
            "mastery_rate": 0,
        }
        
        # Count by question type
        for q in questions:
            qus_type = q.get("qus_type", 1)
            type_names = {0: "essay", 1: "single_choice", 2: "multiple_choice", 3: "fill_blank"}
            type_name = type_names.get(qus_type, "unknown")
            patterns["by_type"][type_name] += 1
        
        # Calculate mastery rate
        total = len(questions)
        mastered = sum(1 for q in questions if q.get("is_mastered", False))
        patterns["mastery_rate"] = round(mastered / total * 100, 2) if total > 0 else 0
        
        # Analyze recent trend (last 10 vs previous 10)
        if len(questions) >= 20:
            recent_mastered = sum(1 for q in questions[:10] if q.get("is_mastered", False))
            previous_mastered = sum(1 for q in questions[10:20] if q.get("is_mastered", False))
            
            if recent_mastered > previous_mastered:
                patterns["recent_trend"] = "improving"
            elif recent_mastered < previous_mastered:
                patterns["recent_trend"] = "declining"
        
        # Convert defaultdict to regular dict
        patterns["by_type"] = dict(patterns["by_type"])
        
        return patterns
    
    async def generate_ai_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Generate AI-powered analysis using LLM.
        
        Returns:
            AI analysis result or None if AI not available
        """
        if not self.llm:
            logger.info("AI analysis not available (missing API key)")
            return None
        
        # Get wrong questions
        questions = await self.get_wrong_questions(limit=50)
        
        if len(questions) < 3:
            logger.info("Not enough wrong questions for AI analysis")
            return None
        
        # Generate analysis
        try:
            analysis = await self.llm.analyze_weak_points(questions)
            return analysis
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None
    
    async def get_full_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive weak point analysis.
        
        Returns:
            Complete analysis combining statistical and AI analysis
        """
        # Statistical analysis
        category_analysis = await self.analyze_by_category()
        pattern_analysis = await self.analyze_error_patterns()
        
        # AI analysis (if available)
        ai_analysis = None
        if AIAnalysisConfig.is_available():
            ai_analysis = await self.generate_ai_analysis()
        
        return {
            "user_id": self.user_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "statistical_analysis": {
                "by_category": category_analysis,
                "error_patterns": pattern_analysis,
            },
            "ai_analysis": ai_analysis,
        }
