"""Feedback service for managing user feedback."""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

import models
from schemas.feedback import FeedbackCreate


# Configuration
FEEDBACK_SUBMISSION_LIMIT_HOURS = int(os.getenv("FEEDBACK_SUBMISSION_LIMIT_HOURS", "24"))


async def check_daily_submission_limit(db: AsyncSession, user_id: int) -> tuple[bool, Optional[datetime]]:
    """
    Check if user has already submitted feedback today.
    
    Returns:
        tuple: (can_submit: bool, next_submission_at: datetime | None)
    """
    limit_hours = FEEDBACK_SUBMISSION_LIMIT_HOURS
    cutoff_time = datetime.utcnow() - timedelta(hours=limit_hours)
    
    result = await db.execute(
        select(models.Feedback)
        .where(
            and_(
                models.Feedback.user_id == user_id,
                models.Feedback.created_at >= cutoff_time
            )
        )
        .order_by(models.Feedback.created_at.desc())
        .limit(1)
    )
    recent_feedback = result.scalar_one_or_none()
    
    if recent_feedback:
        next_submission_at = recent_feedback.created_at + timedelta(hours=limit_hours)
        return False, next_submission_at
    
    return True, None


async def create_feedback(
    db: AsyncSession,
    user_id: int,
    feedback_data: FeedbackCreate
) -> models.Feedback:
    """
    Create a new feedback entry.
    
    Raises:
        HTTPException: If user has already submitted feedback today
    """
    # Check daily submission limit
    can_submit, next_submission_at = await check_daily_submission_limit(db, user_id)
    if not can_submit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"You can only submit feedback once every {FEEDBACK_SUBMISSION_LIMIT_HOURS} hours. Try again after {next_submission_at.isoformat()}",
        )
    
    # Create feedback
    feedback = models.Feedback(
        user_id=user_id,
        content=feedback_data.content,
        category=feedback_data.category.value,
    )
    
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)
    
    return feedback


async def get_feedback(db: AsyncSession, feedback_id: int) -> Optional[models.Feedback]:
    """Get feedback by ID with user info."""
    result = await db.execute(
        select(models.Feedback)
        .options(selectinload(models.Feedback.user))
        .where(models.Feedback.id == feedback_id)
    )
    return result.scalar_one_or_none()


async def list_feedbacks(
    db: AsyncSession,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "vote_count",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[models.Feedback], int]:
    """
    List feedbacks with filtering and pagination.
    
    Args:
        db: Database session
        status_filter: Filter by status
        category: Filter by category
        sort_by: Sort field (vote_count, created_at, resolved_at)
        limit: Page size
        offset: Page offset
        
    Returns:
        tuple: (feedbacks list, total count)
    """
    # Build base query
    query = select(models.Feedback).options(selectinload(models.Feedback.user))
    
    # Apply filters
    if status_filter:
        query = query.where(models.Feedback.status == status_filter)
    if category:
        query = query.where(models.Feedback.category == category)
    
    # Get total count
    count_query = select(func.count()).select_from(models.Feedback)
    if status_filter:
        count_query = count_query.where(models.Feedback.status == status_filter)
    if category:
        count_query = count_query.where(models.Feedback.category == category)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    if sort_by == "created_at":
        query = query.order_by(models.Feedback.created_at.desc())
    elif sort_by == "resolved_at":
        query = query.order_by(
            models.Feedback.resolved_at.desc().nullsfirst()
            if models.Feedback.resolved_at is not None
            else models.Feedback.created_at.desc()
        )
    else:  # Default: vote_count
        query = query.order_by(models.Feedback.vote_count.desc())
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return list(feedbacks), total


async def update_feedback(
    db: AsyncSession,
    feedback_id: int,
    status_update: Optional[str] = None,
    developer_response: Optional[str] = None,
) -> models.Feedback:
    """
    Update feedback status and/or developer response.
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        status_update: New status (optional)
        developer_response: Developer response text (optional)
        
    Returns:
        Updated feedback
        
    Raises:
        HTTPException: If feedback not found
    """
    feedback = await get_feedback(db, feedback_id)
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    if status_update:
        feedback.status = status_update
        if status_update in [models.FeedbackStatus.COMPLETED.value, models.FeedbackStatus.REJECTED.value]:
            feedback.resolved_at = datetime.utcnow()
    
    if developer_response is not None:
        feedback.developer_response = developer_response
        if developer_response:
            feedback.responded_at = datetime.utcnow()
        else:
            feedback.responded_at = None
    
    await db.flush()
    await db.refresh(feedback)
    
    return feedback


async def delete_feedback(
    db: AsyncSession,
    feedback_id: int,
) -> bool:
    """
    Delete feedback.
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        
    Returns:
        True if deleted
        
    Raises:
        HTTPException: If feedback not found
    """
    result = await db.execute(
        select(models.Feedback).where(models.Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    await db.delete(feedback)
    await db.flush()
    
    return True


async def get_feedback_stats(db: AsyncSession) -> dict:
    """Get feedback statistics."""
    # Total count
    total_result = await db.execute(select(func.count()).select_from(models.Feedback))
    total_count = total_result.scalar() or 0
    
    # Count by status
    status_result = await db.execute(
        select(models.Feedback.status, func.count())
        .group_by(models.Feedback.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}
    
    # Count by category
    category_result = await db.execute(
        select(models.Feedback.category, func.count())
        .group_by(models.Feedback.category)
    )
    by_category = {row[0]: row[1] for row in category_result.all()}
    
    # Top voted feedbacks
    top_voted_result = await db.execute(
        select(models.Feedback.id, models.Feedback.content, models.Feedback.vote_count)
        .where(models.Feedback.vote_count > 0)
        .order_by(models.Feedback.vote_count.desc())
        .limit(5)
    )
    top_voted = [
        {"id": row[0], "content": row[1][:100] + "..." if len(row[1]) > 100 else row[1], "vote_count": row[2]}
        for row in top_voted_result.all()
    ]
    
    return {
        "total_count": total_count,
        "by_status": by_status,
        "by_category": by_category,
        "top_voted": top_voted,
    }


async def get_user_feedback_submissions(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[models.Feedback], int]:
    """Get all feedback submissions by a user."""
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(models.Feedback).where(models.Feedback.user_id == user_id)
    )
    total = count_result.scalar() or 0
    
    # Get feedbacks
    result = await db.execute(
        select(models.Feedback)
        .where(models.Feedback.user_id == user_id)
        .order_by(models.Feedback.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    feedbacks = result.scalars().all()
    
    return list(feedbacks), total
