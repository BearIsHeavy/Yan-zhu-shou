from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Blog(Base):
    """Blog post model for user-generated content."""
    __tablename__ = "blogs"

    blog_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    content_file_path = Column(String(255))  # Relative path to content file
    content_type = Column(String(20), default="markdown", nullable=False)
    tags = Column(String(100))  # Comma-separated tags (max 5 tags, each max 10 chars)
    is_published = Column(Boolean, default=True, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="blogs")
    likes = relationship("BlogLike", back_populates="blog", cascade="all, delete-orphan")
    comments = relationship("BlogComment", back_populates="blog", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Blog(blog_id={self.blog_id}, title={self.title}, user_id={self.user_id})>"


class BlogLike(Base):
    """Blog like model for tracking user likes."""
    __tablename__ = "blog_likes"

    like_id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(Integer, ForeignKey("blogs.blog_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    blog = relationship("Blog", back_populates="likes")
    user = relationship("User", back_populates="blog_likes")

    def __repr__(self):
        return f"<BlogLike(like_id={self.like_id}, blog_id={self.blog_id}, user_id={self.user_id})>"


class BlogComment(Base):
    """Blog comment model for user comments."""
    __tablename__ = "blog_comments"

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(Integer, ForeignKey("blogs.blog_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("blog_comments.comment_id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    blog = relationship("Blog", back_populates="comments")
    user = relationship("User", back_populates="blog_comments")
    parent = relationship("BlogComment", remote_side=[comment_id], backref="replies")

    def __repr__(self):
        return f"<BlogComment(comment_id={self.comment_id}, blog_id={self.blog_id}, user_id={self.user_id})>"
