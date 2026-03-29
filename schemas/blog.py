"""Pydantic schemas for blog API."""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum as PyEnum


class ContentTypeEnum(str, PyEnum):
    """Content type for blog posts."""
    MARKDOWN = "markdown"
    HTML = "html"


class BlogTagResponse(BaseModel):
    """Tag response schema."""
    tag_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class BlogCreate(BaseModel):
    """Schema for creating a new blog post."""
    title: str = Field(min_length=1, max_length=200, description="Blog post title")
    content_type: ContentTypeEnum = Field(default=ContentTypeEnum.MARKDOWN, description="Content format")
    is_published: bool = Field(default=True, description="Whether to publish immediately")
    tags: Optional[list[str]] = Field(default=None, description="List of tags (max 5, each max 10 chars)")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 tags allowed")
        for tag in v:
            if len(tag) > 10:
                raise ValueError("Each tag must be at most 10 characters")
            if not tag.strip():
                raise ValueError("Tags cannot be empty or whitespace only")
        return v


class BlogUpdate(BaseModel):
    """Schema for updating a blog post."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content_type: Optional[ContentTypeEnum] = None
    is_published: Optional[bool] = None
    tags: Optional[list[str]] = Field(default=None, description="List of tags (max 5, each max 10 chars)")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("Maximum 5 tags allowed")
        for tag in v:
            if len(tag) > 10:
                raise ValueError("Each tag must be at most 10 characters")
            if not tag.strip():
                raise ValueError("Tags cannot be empty or whitespace only")
        return v


class BlogUserResponse(BaseModel):
    """Simplified user info for blog responses."""
    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class BlogResponse(BaseModel):
    """Full blog post response."""
    blog_id: int
    user_id: int
    title: str
    content_file_path: Optional[str] = None  # Relative path to content file
    content_type: str
    is_published: bool
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime
    author: Optional[BlogUserResponse] = None
    has_liked: bool = False  # Whether current user has liked
    tags: list[BlogTagResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class BlogListItem(BaseModel):
    """Blog item for list responses (without full content)."""
    blog_id: int
    user_id: int
    title: str
    content_type: str
    is_published: bool
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime
    author: Optional[BlogUserResponse] = None
    has_liked: bool = False
    tags: list[BlogTagResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class BlogListResponse(BaseModel):
    """Paginated blog list response."""
    items: list[BlogListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class BlogCommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str = Field(min_length=1, max_length=5000, description="Comment content")
    parent_id: Optional[int] = Field(default=None, description="Parent comment ID for replies")


class BlogCommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(min_length=1, max_length=5000)


class BlogCommentResponse(BaseModel):
    """Comment response with nested replies."""
    comment_id: int
    blog_id: int
    user_id: int
    parent_id: Optional[int] = None
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[BlogUserResponse] = None
    replies: list["BlogCommentResponse"] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class BlogCommentListResponse(BaseModel):
    """Paginated comment list response."""
    items: list[BlogCommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BlogLikeResponse(BaseModel):
    """Response for like operations."""
    has_liked: bool
    like_count: int


class BlogStats(BaseModel):
    """Blog statistics."""
    total_posts: int
    total_views: int
    total_likes: int
    total_comments: int
    published_count: int
    draft_count: int


class BlogSubmissionStatus(BaseModel):
    """Response for checking submission limits."""
    can_submit: bool
    message: str


class BlogTagListResponse(BaseModel):
    """Paginated tag list response."""
    items: list[BlogTagResponse]
    total: int
