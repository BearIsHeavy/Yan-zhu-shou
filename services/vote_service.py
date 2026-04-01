"""Vote service for managing feedback votes."""

import os
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from services.notification_service import check_and_send_threshold_notification


# Configuration
FEEDBACK_VOTE_THRESHOLD = int(os.getenv("FEEDBACK_VOTE_THRESHOLD", "10"))


async def get_user_vote(db: AsyncSession, feedback_id: int, user_id: int) -> Optional[models.FeedbackVote]:
    """Get user's vote for a specific feedback."""
    result = await db.execute(
        select(models.FeedbackVote)
        .where(
            models.FeedbackVote.feedback_id == feedback_id,
            models.FeedbackVote.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def vote_feedback(
    db: AsyncSession,
    feedback_id: int,
    user_id: int,
) -> dict:
    """
    Toggle vote for a feedback (vote if not voted, remove if already voted).
    
    Args:
        db: Database session
        feedback_id: Feedback ID
        user_id: User ID
        
    Returns:
        dict: {has_voted: bool, vote_count: int}
        
    Raises:
        HTTPException: If feedback not found or user voting on own feedback
    """
    # Get feedback
    result = await db.execute(
        select(models.Feedback)
        .options(selectinload(models.Feedback.votes))
        .where(models.Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    # Check if user is trying to vote on their own feedback
    if feedback.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot vote on your own feedback",
        )
    
    # Check existing vote
    existing_vote = await get_user_vote(db, feedback_id, user_id)

    if existing_vote:
        # Remove vote (toggle off)
        await db.delete(existing_vote)
        has_voted = False
    else:
        # Add vote (toggle on)
        vote = models.FeedbackVote(
            feedback_id=feedback_id,
            user_id=user_id,
        )
        db.add(vote)
        has_voted = True

    await db.flush()
    await db.commit()
    await db.refresh(feedback)
    
    # vote_count is now a column_property, automatically calculated
    vote_count = feedback.vote_count

    # Check if threshold is reached and send notification
    if has_voted and vote_count >= FEEDBACK_VOTE_THRESHOLD:
        await check_and_send_threshold_notification(db, feedback)

    return {
        "has_voted": has_voted,
        "vote_count": vote_count,
    }


async def get_vote_status(
    db: AsyncSession,
    feedback_id: int,
    user_id: int,
) -> dict:
    """
    Get vote status for a feedback.

    Args:
        db: Database session
        feedback_id: Feedback ID
        user_id: User ID

    Returns:
        dict: {has_voted: bool, vote_count: int}
    """
    # Get feedback with vote_count (column_property handles this)
    result = await db.execute(
        select(models.Feedback)
        .where(models.Feedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()

    if feedback is None:
        return {"has_voted": False, "vote_count": 0}

    # Check if user has voted
    user_vote = await get_user_vote(db, feedback_id, user_id)
    has_voted = user_vote is not None

    return {
        "has_voted": has_voted,
        "vote_count": feedback.vote_count,
    }


async def check_threshold(feedback_id: int, vote_count: int) -> bool:
    """
    Check if vote count has reached the threshold.
    
    Args:
        feedback_id: Feedback ID
        vote_count: Current vote count
        
    Returns:
        bool: True if threshold is reached
    """
    return vote_count >= FEEDBACK_VOTE_THRESHOLD
