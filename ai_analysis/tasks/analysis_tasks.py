"""
Background tasks for AI analysis.

These tasks can be run asynchronously using FastAPI's BackgroundTasks
or a task queue like Celery/RQ.
"""

import logging
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models
from ai_analysis.analyzers.weak_point import WeakPointAnalyzer
from ai_analysis.analyzers.recommendation import RecommendationEngine
from ai_analysis.config import AIAnalysisConfig

logger = logging.getLogger(__name__)


async def run_full_analysis(
    db: AsyncSession,
    user_id: int,
) -> Optional[dict]:
    """
    Run complete AI analysis for a user.
    
    Args:
        db: Database session
        user_id: User ID to analyze
        
    Returns:
        Analysis result or None if failed
    """
    try:
        logger.info(f"Starting AI analysis for user {user_id}")
        
        # Run weak point analysis
        analyzer = WeakPointAnalyzer(db, user_id)
        analysis_result = await analyzer.get_full_analysis()
        
        # Run recommendation engine
        recommender = RecommendationEngine(db, user_id)
        recommendations = await recommender.get_all_recommendations()
        
        # Combine results
        result = {
            "user_id": user_id,
            "completed_at": datetime.utcnow().isoformat(),
            "analysis": analysis_result,
            "recommendations": recommendations,
        }
        
        logger.info(f"Completed AI analysis for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"AI analysis failed for user {user_id}: {e}")
        return None


async def run_weak_point_analysis(
    db: AsyncSession,
    user_id: int,
) -> Optional[dict]:
    """
    Run weak point analysis only.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Analysis result or None
    """
    try:
        analyzer = WeakPointAnalyzer(db, user_id)
        return await analyzer.get_full_analysis()
    except Exception as e:
        logger.error(f"Weak point analysis failed: {e}")
        return None


async def run_recommendation_generation(
    db: AsyncSession,
    user_id: int,
) -> Optional[dict]:
    """
    Generate recommendations only.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Recommendations or None
    """
    try:
        recommender = RecommendationEngine(db, user_id)
        return await recommender.get_all_recommendations()
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        return None


async def schedule_analysis_check(
    db: AsyncSession,
    user_id: int,
) -> bool:
    """
    Check if user needs analysis and schedule if needed.
    
    Criteria:
    - Has new wrong questions since last analysis
    - Last analysis is older than 7 days
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if analysis was scheduled
    """
    try:
        # Check last analysis time (from analysis_reports table if exists)
        # For now, always return True to trigger analysis
        return True
        
    except Exception as e:
        logger.error(f"Analysis check failed: {e}")
        return False
