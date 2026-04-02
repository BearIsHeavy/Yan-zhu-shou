"""Blog API routes for user-generated content sharing."""

import math
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from schemas import blog as blog_schemas
from dependencies import get_current_user, get_db
from services import blog_service, tags_from_string

router = APIRouter(prefix="/blogs", tags=["Blog"])


@router.get("", response_model=blog_schemas.BlogListResponse)
async def list_blogs(
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    sort_by: str = "created_at",
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """
    List all published blog posts with filtering and pagination.

    - **search**: Search in title
    - **user_id**: Filter by author ID
    - **content_type**: Filter by content type (markdown, html)
    - **tags**: Filter by tags (comma-separated)
    - **sort_by**: Sort by (created_at, updated_at, view_count, like_count)
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page
    """
    if sort_by not in ["created_at", "updated_at", "view_count", "like_count"]:
        sort_by = "created_at"

    offset = (page - 1) * page_size

    blogs, total = await blog_service.list_blogs(
        db=db,
        search=search,
        user_id=user_id,
        content_type=content_type,
        tags=tags,
        sort_by=sort_by,
        limit=page_size,
        offset=offset,
        current_user_id=current_user.user_id if current_user else None,
    )

    items = []
    for blog in blogs:
        has_liked = False
        if current_user:
            like_status = await blog_service.get_like_status(db, blog.blog_id, current_user.user_id)
            has_liked = like_status["has_liked"]

        # Safely access user data (already loaded by selectinload)
        author_data = None
        if blog.user:
            author_data = blog_schemas.BlogUserResponse(
                user_id=blog.user.user_id,
                name=blog.user.name,
            )

        items.append(blog_schemas.BlogListItem(
            blog_id=blog.blog_id,
            user_id=blog.user_id,
            title=blog.title,
            content_type=blog.content_type,
            is_published=blog.is_published,
            view_count=blog.view_count,
            like_count=blog.like_count,
            comment_count=blog.comment_count,
            created_at=blog.created_at,
            updated_at=blog.updated_at,
            author=author_data,
            has_liked=has_liked,
            tags=tags_from_string(blog.tags),
        ))

    return blog_schemas.BlogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/stats", response_model=blog_schemas.BlogStats)
async def get_blog_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """Get blog statistics (personal if authenticated, global otherwise)."""
    if current_user:
        # Personal stats for authenticated user
        stats = await blog_service.get_blog_stats(db, user_id=current_user.user_id)
        return blog_schemas.BlogStats(
            total_posts=stats["total_posts"],
            total_views=stats["total_views"],
            total_likes=stats["total_likes"],
            total_comments=stats["total_comments"],
            my_posts=stats["total_posts"],
            my_drafts=stats["draft_count"],
        )
    else:
        # Global stats for unauthenticated
        stats = await blog_service.get_blog_stats(db, user_id=None)
        return blog_schemas.BlogStats(
            total_posts=stats["total_posts"],
            total_views=stats["total_views"],
            total_likes=stats["total_likes"],
            total_comments=stats["total_comments"],
            my_posts=0,
            my_drafts=0,
        )


@router.get("/my", response_model=blog_schemas.BlogListResponse)
async def get_my_blogs(
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get current user's blog posts (including drafts)."""
    offset = (page - 1) * page_size

    blogs, total = await blog_service.get_user_blog_submissions(
        db=db,
        user_id=current_user.user_id,
        limit=page_size,
        offset=offset,
    )

    items = []
    for blog in blogs:
        items.append(blog_schemas.BlogListItem(
            blog_id=blog.blog_id,
            user_id=blog.user_id,
            title=blog.title,
            content_type=blog.content_type,
            is_published=blog.is_published,
            view_count=blog.view_count,
            like_count=blog.like_count,
            comment_count=blog.comment_count,
            created_at=blog.created_at,
            updated_at=blog.updated_at,
            author=blog_schemas.BlogUserResponse(
                user_id=current_user.user_id,
                name=current_user.name,
            ),
            has_liked=False,
            tags=tags_from_string(blog.tags),
        ))

    return blog_schemas.BlogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ============== Tags Endpoints (must be before /{blog_id}) ==============


@router.get("/tags", response_model=blog_schemas.BlogTagListResponse)
async def list_tags(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """
    List all available tags.

    - **search**: Filter tags by name (partial match)
    """
    from sqlalchemy import distinct
    
    query = select(distinct(models.Blog.tags)).where(models.Blog.is_published == True)
    
    if search:
        query = query.where(models.Blog.tags.ilike(f"%{search}%"))
    
    result = await db.execute(query)
    all_tags_str = result.scalars().all()
    
    tags_set = set()
    for tags_str in all_tags_str:
        if tags_str:
            for tag in tags_from_string(tags_str):
                tags_set.add(tag)
    
    sorted_tags = sorted(tags_set)
    
    if search:
        sorted_tags = [t for t in sorted_tags if search.lower() in t.lower()]
    
    items = [
        blog_schemas.BlogTagResponse(tag_id=i, name=tag)
        for i, tag in enumerate(sorted_tags, start=1)
    ]

    return blog_schemas.BlogTagListResponse(
        items=items,
        total=len(items),
    )


@router.post("/tags", response_model=blog_schemas.BlogTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: blog_schemas.BlogTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new tag.

    Note: Since tags are stored as comma-separated strings in blogs table,
    this endpoint just validates and returns the tag.
    Tags are automatically created when used in blog creation.
    """
    result = await db.execute(
        select(models.Blog.tags).where(
            models.Blog.tags.ilike(f"{tag_data.name},%") |
            models.Blog.tags.ilike(f"%,{tag_data.name},%") |
            models.Blog.tags.ilike(f"%,{tag_data.name}") |
            (models.Blog.tags == tag_data.name)
        ).limit(1)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return blog_schemas.BlogTagResponse(tag_id=0, name=tag_data.name)
    
    return blog_schemas.BlogTagResponse(tag_id=0, name=tag_data.name)


# ============== Blog Endpoints ==============


@router.post("", response_model=blog_schemas.BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    title: str = Form(..., min_length=1, max_length=200),
    content_type: str = Form(default="markdown"),
    is_published: str = Form(default="true"),
    tags: Optional[str] = Form(default=None),
    content_file: UploadFile = File(..., description="Markdown or HTML content file (max 5MB)"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new blog post with file upload.

    **Content-Type:** `multipart/form-data`
    """
    # Validate file
    if not content_file or not content_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content file is required"
        )
    
    # Read and validate file content
    file_content = await content_file.read()
    if not file_content or len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content file cannot be empty"
        )
    
    # Create a new UploadFile with the content for passing to service
    from io import BytesIO
    content_file_for_service = UploadFile(
        filename=content_file.filename,
        file=BytesIO(file_content),
    )

    # Parse tags from comma-separated string
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Parse is_published
    published = str(is_published).lower() in ("true", "1", "yes", "on")

    blog_data = blog_schemas.BlogCreate(
        title=title,
        content_type=blog_schemas.ContentTypeEnum(content_type),
        is_published=published,
        tags=tag_list,
    )

    blog = await blog_service.create_blog(
        db=db,
        user_id=current_user.user_id,
        blog_data=blog_data,
        content_file=content_file_for_service,
    )

    # blog is now a dict, no lazy loading issues
    return blog_schemas.BlogResponse(
        blog_id=blog["blog_id"],
        user_id=blog["user_id"],
        title=blog["title"],
        content_file_path=blog["content_file_path"],
        content_type=blog["content_type"],
        is_published=blog["is_published"],
        view_count=blog["view_count"],
        like_count=blog["like_count"],
        comment_count=blog["comment_count"],
        created_at=blog["created_at"],
        updated_at=blog["updated_at"],
        author=blog_schemas.BlogUserResponse(
            user_id=current_user.user_id,
            name=current_user.name,
        ),
        has_liked=False,
        tags=blog["tags"],
    )


@router.get("/{blog_id}", response_model=blog_schemas.BlogResponse)
async def get_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """Get blog post details by ID."""
    blog = await blog_service.get_blog(db, blog_id)

    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if not blog.is_published:
        if not current_user or blog.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this blog post",
            )

    await blog_service.increment_view_count(db, blog_id)

    has_liked = False
    if current_user:
        like_status = await blog_service.get_like_status(db, blog_id, current_user.user_id)
        has_liked = like_status["has_liked"]

    # Get author data before accessing to avoid lazy loading
    author_data = None
    if blog.user:
        author_data = blog_schemas.BlogUserResponse(
            user_id=blog.user.user_id,
            name=blog.user.name,
        )

    # Refresh only the view_count, not relationships
    await db.refresh(blog, attribute_names=["view_count"])

    return blog_schemas.BlogResponse(
        blog_id=blog.blog_id,
        user_id=blog.user_id,
        title=blog.title,
        content_file_path=blog.content_file_path,
        content_type=blog.content_type,
        is_published=blog.is_published,
        view_count=blog.view_count,
        like_count=blog.like_count,
        comment_count=blog.comment_count,
        created_at=blog.created_at,
        updated_at=blog.updated_at,
        author=author_data,
        has_liked=has_liked,
        tags=tags_from_string(blog.tags),
    )


@router.get("/{blog_id}/content", response_model=blog_schemas.BlogContentResponse)
async def get_blog_content(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """Get blog post content as raw text."""
    blog = await blog_service.get_blog(db, blog_id)

    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if not blog.is_published:
        if not current_user or blog.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this blog post",
            )

    content = await blog_service.get_blog_content(blog, blog.user_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog content file not found",
        )

    return blog_schemas.BlogContentResponse(content=content)


@router.put("/{blog_id}", response_model=blog_schemas.BlogResponse)
async def update_blog(
    blog_id: int,
    title: Optional[str] = Form(default=None, min_length=1, max_length=200),
    content_type: Optional[str] = Form(default=None),
    is_published: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    content_file: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a blog post. **Requires ownership.**"""
    blog = await blog_service.get_blog(db, blog_id)

    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own blog posts",
        )

    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Build update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if content_type is not None:
        update_data["content_type"] = blog_schemas.ContentTypeEnum(content_type).value
    if is_published is not None:
        update_data["is_published"] = str(is_published).lower() in ("true", "1", "yes", "on")
    if tag_list is not None:
        update_data["tags"] = tag_list

    updated_blog = await blog_service.update_blog(
        db=db,
        blog_id=blog_id,
        blog_update=update_data,
        content_file=content_file,
        user_id=current_user.user_id,
    )

    return blog_schemas.BlogResponse(
        blog_id=updated_blog.blog_id,
        user_id=updated_blog.user_id,
        title=updated_blog.title,
        content_file_path=updated_blog.content_file_path,
        content_type=updated_blog.content_type,
        is_published=updated_blog.is_published,
        view_count=updated_blog.view_count,
        like_count=updated_blog.like_count,
        comment_count=updated_blog.comment_count,
        created_at=updated_blog.created_at,
        updated_at=updated_blog.updated_at,
        author=blog_schemas.BlogUserResponse(
            user_id=current_user.user_id,
            name=current_user.name,
        ),
        has_liked=False,
        tags=tags_from_string(updated_blog.tags),
    )


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a blog post. **Requires ownership.**"""
    blog = await blog_service.get_blog(db, blog_id)

    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if blog.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own blog posts",
        )

    await blog_service.delete_blog(db, blog_id, user_id=current_user.user_id)
    return None


@router.post("/{blog_id}/like", response_model=blog_schemas.BlogLikeResponse)
async def like_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Toggle like for a blog post."""
    result = await blog_service.toggle_like(
        db=db,
        blog_id=blog_id,
        user_id=current_user.user_id,
    )

    return blog_schemas.BlogLikeResponse(**result)


@router.get("/{blog_id}/like", response_model=blog_schemas.BlogLikeResponse)
async def get_like_status(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get current user's like status for a blog post."""
    result = await blog_service.get_like_status(
        db=db,
        blog_id=blog_id,
        user_id=current_user.user_id,
    )

    return blog_schemas.BlogLikeResponse(**result)


# ============== Comments ==============


@router.get("/{blog_id}/comments", response_model=blog_schemas.BlogCommentListResponse)
async def list_blog_comments(
    blog_id: int,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """List all comments for a blog post."""
    blog = await blog_service.get_blog(db, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found",
        )

    if not blog.is_published:
        if not current_user or blog.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this blog post",
            )

    offset = (page - 1) * page_size

    comments, total = await blog_service.list_comments(
        db=db,
        blog_id=blog_id,
        limit=page_size,
        offset=offset,
    )

    def build_comment_response(comment: models.BlogComment) -> blog_schemas.BlogCommentResponse:
        replies = [build_comment_response(reply) for reply in comment.replies if not reply.is_deleted]
        return blog_schemas.BlogCommentResponse(
            comment_id=comment.comment_id,
            blog_id=comment.blog_id,
            user_id=comment.user_id,
            parent_id=comment.parent_id,
            content=comment.content,
            is_deleted=comment.is_deleted,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author=blog_schemas.BlogUserResponse(
                user_id=comment.user.user_id,
                name=comment.user.name,
            ) if comment.user else None,
            replies=replies,
        )

    items = [build_comment_response(comment) for comment in comments]

    return blog_schemas.BlogCommentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/{blog_id}/comments", response_model=blog_schemas.BlogCommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    blog_id: int,
    comment_data: blog_schemas.BlogCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new comment on a blog post."""
    comment = await blog_service.create_comment(
        db=db,
        blog_id=blog_id,
        user_id=current_user.user_id,
        comment_data=comment_data,
    )

    return blog_schemas.BlogCommentResponse(
        comment_id=comment.comment_id,
        blog_id=comment.blog_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=blog_schemas.BlogUserResponse(
            user_id=current_user.user_id,
            name=current_user.name,
        ),
        replies=[],
    )


@router.put("/comments/{comment_id}", response_model=blog_schemas.BlogCommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: blog_schemas.BlogCommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a comment. **Requires ownership.**"""
    comment = await blog_service.update_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.user_id,
        content=comment_data.content,
    )

    return blog_schemas.BlogCommentResponse(
        comment_id=comment.comment_id,
        blog_id=comment.blog_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=blog_schemas.BlogUserResponse(
            user_id=current_user.user_id,
            name=current_user.name,
        ),
        replies=[],
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a comment (soft delete)."""
    await blog_service.delete_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.user_id,
    )
    return None
