"""Blog service for managing blog posts, likes, and comments."""

import math
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

import models
from schemas.blog import BlogCreate, BlogCommentCreate
from utils.file_storage import (
    save_blog_content,
    read_blog_content,
    delete_blog_content,
)


def tags_to_string(tags: Optional[list[str]]) -> Optional[str]:
    """Convert tags list to comma-separated string."""
    if not tags:
        return None
    return ",".join(tags)


def tags_from_string(tags_str: Optional[str]) -> list[str]:
    """Convert comma-separated string to tags list."""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


async def get_blog(db: AsyncSession, blog_id: int) -> Optional[models.Blog]:
    """Get blog by ID with user info."""
    result = await db.execute(
        select(models.Blog)
        .options(selectinload(models.Blog.user))
        .where(models.Blog.blog_id == blog_id)
    )
    return result.scalar_one_or_none()


async def list_blogs(
    db: AsyncSession,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    sort_by: str = "created_at",
    limit: int = 20,
    offset: int = 0,
    include_unpublished: bool = False,
    current_user_id: Optional[int] = None,
) -> tuple[list[models.Blog], int]:
    """
    List blogs with filtering and pagination.

    Args:
        db: Database session
        search: Search in title
        user_id: Filter by author ID
        content_type: Filter by content type (markdown, html)
        tags: Filter by tags (comma-separated, blogs must have the tag)
        sort_by: Sort field (created_at, updated_at, view_count, like_count)
        limit: Page size
        offset: Page offset
        include_unpublished: Include unpublished blogs (for owner)
        current_user_id: Current user ID for filtering unpublished

    Returns:
        tuple: (blogs list, total count)
    """
    # Build base query
    query = select(models.Blog).options(selectinload(models.Blog.user))

    # Filter by published status
    if not include_unpublished:
        query = query.where(models.Blog.is_published == True)
    elif current_user_id:
        query = query.where(
            or_(
                models.Blog.is_published == True,
                models.Blog.user_id == current_user_id
            )
        )

    # Apply filters
    if search:
        # Search in title OR tags (fuzzy match)
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                models.Blog.title.ilike(search_pattern),
                models.Blog.tags.ilike(search_pattern),
            )
        )
    if user_id:
        query = query.where(models.Blog.user_id == user_id)
    if content_type:
        query = query.where(models.Blog.content_type == content_type)
    
    # Filter by tags (using LIKE for comma-separated storage)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            # Build LIKE conditions for each tag
            tag_conditions = []
            for tag in tag_list:
                # Match tag at start, middle, or end of comma-separated list
                tag_conditions.append(models.Blog.tags.ilike(f"{tag},%"))
                tag_conditions.append(models.Blog.tags.ilike(f"%,{tag},%"))
                tag_conditions.append(models.Blog.tags.ilike(f"%,{tag}"))
                tag_conditions.append(models.Blog.tags == tag)
            query = query.where(or_(*tag_conditions))

    # Get total count
    count_query = select(func.count()).select_from(models.Blog)
    if not include_unpublished:
        count_query = count_query.where(models.Blog.is_published == True)
    elif current_user_id:
        count_query = count_query.where(
            or_(
                models.Blog.is_published == True,
                models.Blog.user_id == current_user_id
            )
        )
    if search:
        # Search in title OR tags (fuzzy match)
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                models.Blog.title.ilike(search_pattern),
                models.Blog.tags.ilike(search_pattern),
            )
        )
    if user_id:
        count_query = count_query.where(models.Blog.user_id == user_id)
    if content_type:
        count_query = count_query.where(models.Blog.content_type == content_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_by == "view_count":
        query = query.order_by(models.Blog.view_count.desc())
    elif sort_by == "like_count":
        query = query.order_by(models.Blog.like_count.desc())
    elif sort_by == "updated_at":
        query = query.order_by(models.Blog.updated_at.desc())
    else:
        query = query.order_by(models.Blog.created_at.desc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    blogs = result.scalars().all()

    return list(blogs), total


async def create_blog(
    db: AsyncSession,
    user_id: int,
    blog_data: BlogCreate,
    content_file: Optional[UploadFile] = None,
) -> dict:
    """Create a new blog post with optional content file. Returns dict."""
    blog = models.Blog(
        user_id=user_id,
        title=blog_data.title,
        content_file_path=None,
        content_type=blog_data.content_type.value,
        is_published=blog_data.is_published,
        tags=tags_to_string(blog_data.tags),
    )

    db.add(blog)
    await db.flush()  # Get blog_id
    
    # Save content file if provided
    if content_file:
        file_content = await content_file.read()
        original_filename = content_file.filename or "blog.md"
        file_path = save_blog_content(
            file_content=file_content,
            blog_id=blog.blog_id,
            original_filename=original_filename,
            user_id=user_id,
        )
        blog.content_file_path = file_path
    
    # Commit the transaction to ensure data is persisted
    await db.commit()
    
    # Refresh to get all committed data
    await db.refresh(blog)

    # Convert to dict to avoid lazy loading issues
    return {
        "blog_id": blog.blog_id,
        "user_id": blog.user_id,
        "title": blog.title,
        "content_file_path": blog.content_file_path,
        "content_type": blog.content_type,
        "is_published": blog.is_published,
        "view_count": blog.view_count,
        "like_count": blog.like_count,
        "comment_count": blog.comment_count,
        "created_at": blog.created_at,
        "updated_at": blog.updated_at,
        "tags": tags_from_string(blog.tags),
    }


async def update_blog(
    db: AsyncSession,
    blog_id: int,
    blog_update: dict,
    content_file: Optional[UploadFile] = None,
    user_id: Optional[int] = None,
) -> models.Blog:
    """
    Update a blog post.
    """
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    # Handle tags - convert list to comma-separated string
    if "tags" in blog_update:
        blog_update["tags"] = tags_to_string(blog_update["tags"])

    # Handle content file upload
    if content_file and user_id:
        if blog.content_file_path:
            delete_blog_content(user_id, blog.content_file_path)

        file_content = await content_file.read()
        original_filename = content_file.filename or "blog.md"
        file_path = save_blog_content(
            file_content=file_content,
            blog_id=blog_id,
            original_filename=original_filename,
            user_id=user_id,
        )
        blog.content_file_path = file_path

    for field, value in blog_update.items():
        if value is not None:
            setattr(blog, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(blog)

    return blog


async def get_blog_content(blog: models.Blog, user_id: int) -> Optional[str]:
    """Get blog content from file."""
    if not blog.content_file_path:
        return None
    return read_blog_content(user_id, blog.content_file_path)


async def delete_blog(
    db: AsyncSession,
    blog_id: int,
    user_id: Optional[int] = None,
) -> bool:
    """Delete a blog post."""
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.content_file_path and user_id:
        delete_blog_content(user_id, blog.content_file_path)

    await db.delete(blog)
    await db.commit()

    return True


async def increment_view_count(db: AsyncSession, blog_id: int) -> None:
    """Increment blog view count."""
    result = await db.execute(
        select(models.Blog).where(models.Blog.blog_id == blog_id)
    )
    blog = result.scalar_one_or_none()
    if blog:
        blog.view_count += 1
        await db.flush()
        await db.commit()


async def get_user_like(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
) -> Optional[models.BlogLike]:
    """Get user's like for a specific blog."""
    result = await db.execute(
        select(models.BlogLike)
        .where(
            and_(
                models.BlogLike.blog_id == blog_id,
                models.BlogLike.user_id == user_id,
            )
        )
    )
    return result.scalar_one_or_none()


async def toggle_like(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
) -> dict:
    """Toggle like for a blog."""
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot like your own blog post",
        )

    existing_like = await get_user_like(db, blog_id, user_id)

    if existing_like:
        await db.delete(existing_like)
        has_liked = False
    else:
        like = models.BlogLike(
            blog_id=blog_id,
            user_id=user_id,
        )
        db.add(like)
        has_liked = True

    await db.flush()
    await db.refresh(blog)

    # like_count is now computed from relationships
    return {
        "has_liked": has_liked,
        "like_count": len(blog.likes) if blog.likes else 0,
    }


async def get_like_status(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
) -> dict:
    """Get like status for a blog."""
    blog = await get_blog(db, blog_id)
    if blog is None:
        return {"has_liked": False, "like_count": 0}

    user_like = await get_user_like(db, blog_id, user_id)
    has_liked = user_like is not None

    return {
        "has_liked": has_liked,
        "like_count": blog.like_count,
    }


async def get_comment(db: AsyncSession, comment_id: int) -> Optional[models.BlogComment]:
    """Get comment by ID with user info."""
    result = await db.execute(
        select(models.BlogComment)
        .options(selectinload(models.BlogComment.user))
        .where(models.BlogComment.comment_id == comment_id)
    )
    return result.scalar_one_or_none()


async def list_comments(
    db: AsyncSession,
    blog_id: int,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[models.BlogComment], int]:
    """List comments for a blog with pagination."""
    count_result = await db.execute(
        select(func.count())
        .select_from(models.BlogComment)
        .where(
            and_(
                models.BlogComment.blog_id == blog_id,
                models.BlogComment.is_deleted == False
            )
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.BlogComment)
        .options(selectinload(models.BlogComment.user))
        .where(
            and_(
                models.BlogComment.blog_id == blog_id,
                models.BlogComment.parent_id.is_(None),
                models.BlogComment.is_deleted == False,
            )
        )
        .order_by(models.BlogComment.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    comments = result.scalars().all()

    for comment in comments:
        await db.refresh(comment, attribute_names=["replies"])

    return list(comments), total


async def create_comment(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
    comment_data: BlogCommentCreate,
) -> models.BlogComment:
    """Create a new comment."""
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    parent_comment = None
    if comment_data.parent_id:
        parent_comment = await get_comment(db, comment_data.parent_id)
        if parent_comment is None or parent_comment.blog_id != blog_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )

    comment = models.BlogComment(
        blog_id=blog_id,
        user_id=user_id,
        parent_id=comment_data.parent_id,
        content=comment_data.content,
    )

    db.add(comment)
    await db.flush()
    await db.commit()
    await db.refresh(comment)

    blog.comment_count += 1
    await db.flush()
    await db.commit()

    return comment


async def update_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    content: str,
) -> models.BlogComment:
    """Update a comment."""
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    comment.content = content
    await db.flush()
    await db.commit()
    await db.refresh(comment)

    return comment


async def delete_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
) -> bool:
    """Delete a comment (soft delete)."""
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    blog = await get_blog(db, comment.blog_id)
    is_author = comment.user_id == user_id
    is_blog_owner = blog.user_id == user_id if blog else False

    if not is_author and not is_blog_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    comment.is_deleted = True
    comment.content = "[Deleted]"
    await db.flush()
    await db.commit()

    # comment_count is now computed from relationships, no need to update
    await db.refresh(blog, attribute_names=["comments"])

    return True


async def get_blog_stats(db: AsyncSession, user_id: Optional[int] = None) -> dict:
    """Get blog statistics."""
    if user_id:
        base_filter = models.Blog.user_id == user_id
    else:
        base_filter = True

    total_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_posts = total_result.scalar() or 0

    published_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(and_(base_filter, models.Blog.is_published == True))
    )
    published_count = published_result.scalar() or 0

    draft_count = total_posts - published_count

    views_result = await db.execute(
        select(func.coalesce(func.sum(models.Blog.view_count), 0))
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_views = views_result.scalar() or 0

    likes_result = await db.execute(
        select(func.coalesce(func.sum(models.Blog.like_count), 0))
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_likes = likes_result.scalar() or 0

    comments_result = await db.execute(
        select(func.coalesce(func.sum(models.Blog.comment_count), 0))
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_comments = comments_result.scalar() or 0

    return {
        "total_posts": total_posts,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "published_count": published_count,
        "draft_count": draft_count,
    }


async def get_user_blog_submissions(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[models.Blog], int]:
    """Get all blog submissions by a user."""
    count_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(models.Blog.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Blog)
        .where(models.Blog.user_id == user_id)
        .order_by(models.Blog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    blogs = result.scalars().all()

    return list(blogs), total
