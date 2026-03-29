"""Blog service for managing blog posts, likes, and comments."""

import math
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload, joinedload

import models
from schemas.blog import BlogCreate, BlogCommentCreate
from utils.file_storage import (
    save_blog_content,
    read_blog_content,
    delete_blog_content,
)


async def get_or_create_tag(db: AsyncSession, name: str) -> models.BlogTag:
    """Get existing tag or create new one."""
    name = name.strip()
    result = await db.execute(
        select(models.BlogTag).where(models.BlogTag.name == name)
    )
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = models.BlogTag(name=name)
        db.add(tag)
        await db.flush()
    return tag


async def set_blog_tags(db: AsyncSession, blog: models.Blog, tag_names: Optional[list[str]]) -> None:
    """Set tags for a blog post."""
    # First, remove all existing tag associations
    await db.execute(
        delete(models.blog_tags_association).where(
            models.blog_tags_association.c.blog_id == blog.blog_id
        )
    )
    
    if tag_names is None:
        return

    # Add new tag associations
    for name in tag_names:
        tag = await get_or_create_tag(db, name)
        assoc = models.blog_tags_association.insert().values(blog_id=blog.blog_id, tag_id=tag.tag_id)
        await db.execute(assoc)


async def get_blog(db: AsyncSession, blog_id: int) -> Optional[models.Blog]:
    """Get blog by ID with user info and tags."""
    result = await db.execute(
        select(models.Blog)
        .options(
            selectinload(models.Blog.user),
            selectinload(models.Blog.tags)
        )
        .where(models.Blog.blog_id == blog_id)
    )
    return result.scalar_one_or_none()


async def list_blogs(
    db: AsyncSession,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    content_type: Optional[str] = None,
    tags: Optional[list[str]] = None,
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
        tags: Filter by tags (blogs must have ALL specified tags)
        sort_by: Sort field (created_at, updated_at, view_count, like_count)
        limit: Page size
        offset: Page offset
        include_unpublished: Include unpublished blogs (for owner)
        current_user_id: Current user ID for filtering unpublished

    Returns:
        tuple: (blogs list, total count)
    """
    # Build base query with tags loaded
    query = select(models.Blog).options(
        selectinload(models.Blog.user),
        selectinload(models.Blog.tags)
    )

    # Filter by published status
    if not include_unpublished:
        query = query.where(models.Blog.is_published == True)
    elif current_user_id:
        # Include user's own unpublished blogs
        query = query.where(
            or_(
                models.Blog.is_published == True,
                models.Blog.user_id == current_user_id
            )
        )

    # Apply filters
    if search:
        query = query.where(models.Blog.title.ilike(f"%{search}%"))
    if user_id:
        query = query.where(models.Blog.user_id == user_id)
    if content_type:
        query = query.where(models.Blog.content_type == content_type)
    
    # Filter by tags (blogs must have ALL specified tags)
    if tags:
        tag_subquery = (
            select(models.blog_tags_association.c.blog_id)
            .join(models.BlogTag)
            .where(models.BlogTag.name.in_([t.strip() for t in tags]))
            .group_by(models.blog_tags_association.c.blog_id)
            .having(func.count(models.blog_tags_association.c.tag_id) == len(tags))
        )
        query = query.where(models.Blog.blog_id.in_(tag_subquery))

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
        count_query = count_query.where(models.Blog.title.ilike(f"%{search}%"))
    if user_id:
        count_query = count_query.where(models.Blog.user_id == user_id)
    if content_type:
        count_query = count_query.where(models.Blog.content_type == content_type)
    if tags:
        tag_count_subquery = (
            select(models.blog_tags_association.c.blog_id)
            .join(models.BlogTag)
            .where(models.BlogTag.name.in_([t.strip() for t in tags]))
            .group_by(models.blog_tags_association.c.blog_id)
            .having(func.count(models.blog_tags_association.c.tag_id) == len(tags))
        )
        count_query = count_query.where(models.Blog.blog_id.in_(tag_count_subquery))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    if sort_by == "view_count":
        query = query.order_by(models.Blog.view_count.desc())
    elif sort_by == "like_count":
        query = query.order_by(models.Blog.like_count.desc())
    elif sort_by == "updated_at":
        query = query.order_by(models.Blog.updated_at.desc())
    else:  # Default: created_at
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
) -> models.Blog:
    """Create a new blog post with optional content file."""
    blog = models.Blog(
        user_id=user_id,
        title=blog_data.title,
        content_file_path=None,  # Will be set after file upload
        content_type=blog_data.content_type.value,
        is_published=blog_data.is_published,
    )

    db.add(blog)
    await db.flush()
    await db.refresh(blog)

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
        await db.flush()

    # Set tags if provided
    if blog_data.tags is not None:
        await set_blog_tags(db, blog, blog_data.tags)
        await db.flush()

    # Explicitly load tags using selectinload to avoid lazy loading
    await db.refresh(blog, attribute_names=["tags"])
    
    # Ensure tags are loaded by re-querying with selectinload
    result = await db.execute(
        select(models.Blog)
        .options(selectinload(models.Blog.tags))
        .where(models.Blog.blog_id == blog.blog_id)
    )
    blog = result.scalar_one_or_none()

    return blog


async def update_blog(
    db: AsyncSession,
    blog_id: int,
    blog_update: dict,
    content_file: Optional[UploadFile] = None,
    user_id: Optional[int] = None,
) -> models.Blog:
    """
    Update a blog post.

    Args:
        db: Database session
        blog_id: Blog ID
        blog_update: Dict of fields to update
        content_file: Optional new content file
        user_id: User ID for file operations

    Returns:
        Updated blog

    Raises:
        HTTPException: If blog not found
    """
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    # Handle tags separately
    tags = blog_update.pop("tags", None)
    if tags is not None:
        await set_blog_tags(db, blog, tags)
        await db.flush()

    # Handle content file upload
    if content_file and user_id:
        # Delete old file if exists
        if blog.content_file_path:
            delete_blog_content(user_id, blog.content_file_path)

        # Save new file
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

    # Explicitly load tags using selectinload to avoid lazy loading
    await db.execute(
        select(models.Blog)
        .options(selectinload(models.Blog.tags))
        .where(models.Blog.blog_id == blog.blog_id)
    )
    # Re-query to get fully loaded blog
    result = await db.execute(
        select(models.Blog)
        .options(selectinload(models.Blog.tags))
        .where(models.Blog.blog_id == blog_id)
    )
    blog = result.scalar_one_or_none()

    return blog


async def get_blog_content(blog: models.Blog, user_id: int) -> Optional[str]:
    """
    Get blog content from file.

    Args:
        blog: Blog instance
        user_id: User ID for file access

    Returns:
        Blog content as string or None
    """
    if not blog.content_file_path:
        return None
    return read_blog_content(user_id, blog.content_file_path)


async def delete_blog(
    db: AsyncSession,
    blog_id: int,
    user_id: Optional[int] = None,
) -> bool:
    """
    Delete a blog post.

    Args:
        db: Database session
        blog_id: Blog ID
        user_id: User ID for file deletion

    Returns:
        True if deleted

    Raises:
        HTTPException: If blog not found
    """
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    # Delete content file if exists
    if blog.content_file_path and user_id:
        delete_blog_content(user_id, blog.content_file_path)

    await db.delete(blog)
    await db.flush()

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
    """
    Toggle like for a blog (like if not liked, remove if already liked).

    Args:
        db: Database session
        blog_id: Blog ID
        user_id: User ID

    Returns:
        dict: {has_liked: bool, like_count: int}

    Raises:
        HTTPException: If blog not found or user liking own blog
    """
    # Get blog
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    # Check if user is trying to like their own blog
    if blog.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot like your own blog post",
        )

    # Check existing like
    existing_like = await get_user_like(db, blog_id, user_id)

    if existing_like:
        # Remove like (toggle off)
        await db.delete(existing_like)
        blog.like_count = max(0, blog.like_count - 1)
        has_liked = False
    else:
        # Add like (toggle on)
        like = models.BlogLike(
            blog_id=blog_id,
            user_id=user_id,
        )
        db.add(like)
        blog.like_count += 1
        has_liked = True

    await db.flush()
    await db.refresh(blog)

    return {
        "has_liked": has_liked,
        "like_count": blog.like_count,
    }


async def get_like_status(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
) -> dict:
    """
    Get like status for a blog.

    Args:
        db: Database session
        blog_id: Blog ID
        user_id: User ID

    Returns:
        dict: {has_liked: bool, like_count: int}
    """
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
    """
    List comments for a blog with pagination.

    Args:
        db: Database session
        blog_id: Blog ID
        limit: Page size
        offset: Page offset

    Returns:
        tuple: (comments list, total count)
    """
    # Get total count (excluding deleted)
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

    # Get comments (top-level only, excluding deleted)
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

    # Load replies for each comment
    for comment in comments:
        await db.refresh(comment, attribute_names=["replies"])

    return list(comments), total


async def create_comment(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
    comment_data: BlogCommentCreate,
) -> models.BlogComment:
    """
    Create a new comment.

    Args:
        db: Database session
        blog_id: Blog ID
        user_id: User ID
        comment_data: Comment data

    Returns:
        Created comment

    Raises:
        HTTPException: If blog not found or parent comment not found
    """
    # Verify blog exists
    blog = await get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    # Verify parent comment if provided
    parent_comment = None
    if comment_data.parent_id:
        parent_comment = await get_comment(db, comment_data.parent_id)
        if parent_comment is None or parent_comment.blog_id != blog_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )

    # Create comment
    comment = models.BlogComment(
        blog_id=blog_id,
        user_id=user_id,
        parent_id=comment_data.parent_id,
        content=comment_data.content,
    )

    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    # Increment blog comment count
    blog.comment_count += 1
    await db.flush()

    return comment


async def update_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    content: str,
) -> models.BlogComment:
    """
    Update a comment.

    Args:
        db: Database session
        comment_id: Comment ID
        user_id: User ID (for ownership check)
        content: New content

    Returns:
        Updated comment

    Raises:
        HTTPException: If comment not found or user is not author
    """
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
    await db.refresh(comment)

    return comment


async def delete_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
) -> bool:
    """
    Delete a comment (soft delete).

    Args:
        db: Database session
        comment_id: Comment ID
        user_id: User ID (for ownership check)

    Returns:
        True if deleted

    Raises:
        HTTPException: If comment not found or insufficient permissions
    """
    comment = await get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Check if user is author or blog owner
    blog = await get_blog(db, comment.blog_id)
    is_author = comment.user_id == user_id
    is_blog_owner = blog.user_id == user_id if blog else False

    if not is_author and not is_blog_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    # Soft delete
    comment.is_deleted = True
    comment.content = "[Deleted]"
    await db.flush()

    # Decrement blog comment count
    blog.comment_count = max(0, blog.comment_count - 1)
    await db.flush()

    return True


async def get_blog_stats(db: AsyncSession, user_id: Optional[int] = None) -> dict:
    """
    Get blog statistics.

    Args:
        db: Database session
        user_id: Optional user ID for personal stats

    Returns:
        dict: Blog statistics
    """
    if user_id:
        # Personal stats
        base_filter = models.Blog.user_id == user_id
    else:
        # Global stats
        base_filter = True

    # Total posts
    total_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_posts = total_result.scalar() or 0

    # Published count
    published_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(and_(base_filter, models.Blog.is_published == True))
    )
    published_count = published_result.scalar() or 0

    # Draft count
    draft_count = total_posts - published_count

    # Total views
    views_result = await db.execute(
        select(func.coalesce(func.sum(models.Blog.view_count), 0))
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_views = views_result.scalar() or 0

    # Total likes
    likes_result = await db.execute(
        select(func.coalesce(func.sum(models.Blog.like_count), 0))
        .select_from(models.Blog)
        .where(base_filter)
    )
    total_likes = likes_result.scalar() or 0

    # Total comments
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


async def list_all_tags(
    db: AsyncSession,
    search: Optional[str] = None,
    limit: int = 100,
) -> tuple[list[models.BlogTag], int]:
    """
    List all tags with optional search.

    Args:
        db: Database session
        search: Search in tag name
        limit: Maximum number of tags to return

    Returns:
        tuple: (tags list, total count)
    """
    # Get total count
    count_query = select(func.count()).select_from(models.BlogTag)
    if search:
        count_query = count_query.where(models.BlogTag.name.ilike(f"%{search}%"))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get tags
    query = select(models.BlogTag).order_by(models.BlogTag.name)
    if search:
        query = query.where(models.BlogTag.name.ilike(f"%{search}%"))
    query = query.limit(limit)

    result = await db.execute(query)
    tags = result.scalars().all()

    return list(tags), total


async def get_user_blog_submissions(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[models.Blog], int]:
    """Get all blog submissions by a user."""
    # Get total count
    count_result = await db.execute(
        select(func.count())
        .select_from(models.Blog)
        .where(models.Blog.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Get blogs
    result = await db.execute(
        select(models.Blog)
        .where(models.Blog.user_id == user_id)
        .order_by(models.Blog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    blogs = result.scalars().all()

    return list(blogs), total
