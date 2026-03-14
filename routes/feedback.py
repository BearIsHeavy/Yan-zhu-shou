"""Feedback API routes for 'You Say, I Fix' system."""

import math
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

import models
from schemas import feedback as feedback_schemas
from dependencies import get_current_user, get_db
from services import feedback_service, vote_service

router = APIRouter(tags=["Feedback"])


def _is_developer_or_admin(user: models.User) -> bool:
    """Check if user is developer or admin.
    
    TODO: Implement proper role-based access control.
    For now, returns True for all authenticated users.
    """
    # TODO: Add role field to User model and check here
    return True


@router.get("", response_model=feedback_schemas.FeedbackListResponse)
async def list_feedbacks(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "vote_count",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    List all feedback with filtering and pagination.
    
    - **status_filter**: Filter by status (pending, in_progress, completed, rejected)
    - **category**: Filter by category (bug, feature, ui, performance, documentation, other)
    - **sort_by**: Sort by field (vote_count, created_at)
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page
    """
    # Validate sort_by
    if sort_by not in ["vote_count", "created_at", "resolved_at"]:
        sort_by = "vote_count"
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get feedbacks
    feedbacks, total = await feedback_service.list_feedbacks(
        db=db,
        status_filter=status_filter,
        category=category,
        sort_by=sort_by,
        limit=page_size,
        offset=offset,
    )
    
    # Build response
    items = []
    for feedback in feedbacks:
        items.append(feedback_schemas.FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            content=feedback.content,
            category=feedback.category,
            status=feedback.status,
            vote_count=feedback.vote_count,
            developer_response=feedback.developer_response,
            responded_at=feedback.responded_at,
            resolved_at=feedback.resolved_at,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            author=feedback_schemas.FeedbackUserResponse(
                user_id=feedback.user.user_id,
                name=feedback.user.name,
            ) if feedback.user else None,
        ))
    
    return feedback_schemas.FeedbackListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/stats", response_model=feedback_schemas.FeedbackStats)
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get feedback statistics."""
    stats = await feedback_service.get_feedback_stats(db)
    return feedback_schemas.FeedbackStats(**stats)


@router.post("", response_model=feedback_schemas.FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: feedback_schemas.FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Submit new feedback.
    
    **Rate limit**: 1 submission per user every 24 hours.
    
    - **content**: Feedback text (required, 1-2000 characters)
    - **category**: Feedback category (bug, feature, ui, performance, documentation, other)
    """
    feedback = await feedback_service.create_feedback(
        db=db,
        user_id=current_user.user_id,
        feedback_data=feedback_data,
    )
    
    return feedback_schemas.FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        content=feedback.content,
        category=feedback.category,
        status=feedback.status,
        vote_count=feedback.vote_count,
        developer_response=feedback.developer_response,
        responded_at=feedback.responded_at,
        resolved_at=feedback.resolved_at,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        author=feedback_schemas.FeedbackUserResponse(
            user_id=current_user.user_id,
            name=current_user.name,
        ),
    )


@router.get("/{feedback_id}", response_model=feedback_schemas.FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """
    Get feedback details by ID.

    Includes author info and whether current user has voted.
    """
    feedback = await feedback_service.get_feedback(db, feedback_id)

    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # Check if current user has voted
    has_voted = False
    if current_user:
        vote_status = await vote_service.get_vote_status(db, feedback_id, current_user.user_id)
        has_voted = vote_status["has_voted"]

    return feedback_schemas.FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        content=feedback.content,
        category=feedback.category,
        status=feedback.status,
        vote_count=feedback.vote_count,
        developer_response=feedback.developer_response,
        responded_at=feedback.responded_at,
        resolved_at=feedback.resolved_at,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        author=feedback_schemas.FeedbackUserResponse(
            user_id=feedback.user.user_id,
            name=feedback.user.name,
        ) if feedback.user else None,
        has_voted=has_voted,
    )


@router.put("/{feedback_id}", response_model=feedback_schemas.FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: feedback_schemas.FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update feedback status and/or developer response.

    **Requires developer/admin role.**

    - **status**: New status (pending, in_progress, completed, rejected)
    - **developer_response**: Response text (optional)
    """
    if not _is_developer_or_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    feedback = await feedback_service.update_feedback(
        db=db,
        feedback_id=feedback_id,
        status_update=feedback_update.status.value if feedback_update.status else None,
        developer_response=feedback_update.developer_response,
    )

    return feedback_schemas.FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        content=feedback.content,
        category=feedback.category,
        status=feedback.status,
        vote_count=feedback.vote_count,
        developer_response=feedback.developer_response,
        responded_at=feedback.responded_at,
        resolved_at=feedback.resolved_at,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        author=feedback_schemas.FeedbackUserResponse(
            user_id=feedback.user.user_id,
            name=feedback.user.name,
        ) if feedback.user else None,
    )


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete feedback.
    
    **Requires admin role** or **original author (if no votes)**.
    """
    # TODO: Implement proper admin check
    # For now, allow deletion only if user is author and no votes
    feedback = await feedback_service.get_feedback(db, feedback_id)
    
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    # Check permissions
    is_author = feedback.user_id == current_user.user_id
    is_admin = False  # TODO: Implement admin check
    
    if not is_admin:
        if not is_author:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author or admin can delete feedback",
            )
        if feedback.vote_count > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete feedback with votes",
            )
    
    await feedback_service.delete_feedback(db, feedback_id)
    return None


@router.post("/{feedback_id}/vote", response_model=feedback_schemas.FeedbackVoteResponse)
async def vote_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Toggle vote for feedback.

    - If not voted: Add vote
    - If already voted: Remove vote

    **Requires authentication.** Cannot vote on own feedback.
    """
    result = await vote_service.vote_feedback(
        db=db,
        feedback_id=feedback_id,
        user_id=current_user.user_id,
    )

    return feedback_schemas.FeedbackVoteResponse(**result)


@router.get("/{feedback_id}/vote", response_model=feedback_schemas.FeedbackVoteResponse)
async def get_vote_status(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get current user's vote status for a feedback.

    Returns whether user has voted and total vote count.
    """
    result = await vote_service.get_vote_status(
        db=db,
        feedback_id=feedback_id,
        user_id=current_user.user_id,
    )

    return feedback_schemas.FeedbackVoteResponse(**result)


@router.get("/me/submissions", response_model=feedback_schemas.FeedbackListResponse)
async def get_my_feedback(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Get current user's feedback submissions.

    Paginated list of all feedback submitted by the current user.
    """
    offset = (page - 1) * page_size

    feedbacks, total = await feedback_service.get_user_feedback_submissions(
        db=db,
        user_id=current_user.user_id,
        limit=page_size,
        offset=offset,
    )

    items = []
    for feedback in feedbacks:
        items.append(feedback_schemas.FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            content=feedback.content,
            category=feedback.category,
            status=feedback.status,
            vote_count=feedback.vote_count,
            developer_response=feedback.developer_response,
            responded_at=feedback.responded_at,
            resolved_at=feedback.resolved_at,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            has_voted=False,  # User knows their own feedback
        ))

    return feedback_schemas.FeedbackListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/me/submission-status", response_model=feedback_schemas.FeedbackSubmissionStatus)
async def get_submission_status(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Check if current user can submit feedback today.

    Returns whether user can submit and when they can submit next.
    """
    can_submit, next_submission_at = await feedback_service.check_daily_submission_limit(
        db=db,
        user_id=current_user.user_id,
    )

    if can_submit:
        return feedback_schemas.FeedbackSubmissionStatus(
            can_submit=True,
            message="You can submit feedback now",
        )
    else:
        return feedback_schemas.FeedbackSubmissionStatus(
            can_submit=False,
            next_submission_at=next_submission_at,
            message=f"You can submit feedback again after {next_submission_at.isoformat()}",
        )
