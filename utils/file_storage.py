"""File storage utility for managing user-uploaded files."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

# Base directory for uploaded files
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

# User bio files directory
BIO_DIR = UPLOAD_DIR / "bios"

# Blog content files directory
BLOG_DIR = UPLOAD_DIR / "blogs"

# User books directory
BOOKS_DIR = UPLOAD_DIR / "books"


def ensure_upload_dirs() -> None:
    """Ensure upload directories exist."""
    UPLOAD_DIR.mkdir(exist_ok=True)
    BIO_DIR.mkdir(exist_ok=True)
    BLOG_DIR.mkdir(exist_ok=True)
    BOOKS_DIR.mkdir(exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving the original extension.

    Args:
        original_filename: Original filename from upload

    Returns:
        Unique filename with UUID prefix
    """
    # Get file extension
    ext = Path(original_filename).suffix.lower()
    if ext not in ['.md', '.markdown']:
        ext = '.md'  # Default to .md for safety

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{ext}"


def save_bio_file(file_content: bytes, original_filename: str, user_id: int) -> str:
    """
    Save a user's self-introduction bio file.

    Args:
        file_content: Raw file content in bytes
        original_filename: Original filename from upload
        user_id: User ID for organizing files

    Returns:
        Relative path to saved file

    Raises:
        HTTPException: If file validation fails
    """
    # Ensure directories exist
    ensure_upload_dirs()

    # Validate file type
    ext = Path(original_filename).suffix.lower()
    if ext not in ['.md', '.markdown']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only Markdown files (.md, .markdown) are allowed.",
        )

    # Validate file size (max 1MB)
    if len(file_content) > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 1MB limit.",
        )

    # Create user-specific directory
    user_dir = BIO_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)

    # Generate unique filename
    filename = generate_unique_filename(original_filename)
    file_path = user_dir / filename

    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)

    # Return relative path (relative to project root)
    relative_path = file_path.relative_to(UPLOAD_DIR)
    return str(Path("uploads") / relative_path)


def get_bio_file_path(user_id: int, file_path: str) -> Optional[Path]:
    """
    Get the absolute path to a user's bio file.

    Args:
        user_id: User ID
        file_path: Relative path stored in database

    Returns:
        Absolute file path or None if file doesn't exist
    """
    if not file_path:
        return None

    # Convert to absolute path
    abs_path = UPLOAD_DIR.parent / file_path

    # Security check: ensure file is within upload directory
    try:
        abs_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return None

    if not abs_path.exists():
        return None

    return abs_path


def read_bio_file(user_id: int, file_path: str) -> Optional[str]:
    """
    Read a user's bio file content.

    Args:
        user_id: User ID
        file_path: Relative path stored in database

    Returns:
        File content as string or None if not found
    """
    abs_path = get_bio_file_path(user_id, file_path)
    if abs_path is None:
        return None

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def delete_bio_file(user_id: int, file_path: str) -> bool:
    """
    Delete a user's bio file.

    Args:
        user_id: User ID
        file_path: Relative path stored in database

    Returns:
        True if deleted, False otherwise
    """
    abs_path = get_bio_file_path(user_id, file_path)
    if abs_path is None:
        return False

    try:
        abs_path.unlink()

        # Clean up user directory if empty
        user_dir = abs_path.parent
        if user_dir.exists() and not any(user_dir.iterdir()):
            user_dir.rmdir()

        return True
    except Exception:
        return False


# ============== Blog Content File Storage ==============


def generate_blog_filename(blog_id: int, original_filename: str) -> str:
    """
    Generate a unique filename for blog content.

    Args:
        blog_id: Blog ID
        original_filename: Original filename from upload

    Returns:
        Unique filename with blog_id prefix
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ['.md', '.markdown', '.html', '.htm']:
        ext = '.md'  # Default to .md

    unique_id = uuid.uuid4().hex[:8]
    return f"blog_{blog_id}_{unique_id}{ext}"


def save_blog_content(
    file_content: bytes,
    blog_id: int,
    original_filename: str,
    user_id: int,
) -> str:
    """
    Save blog content file.

    Args:
        file_content: Raw file content in bytes
        blog_id: Blog ID
        original_filename: Original filename from upload
        user_id: User ID for organizing files

    Returns:
        Relative path to saved file

    Raises:
        HTTPException: If file validation fails
    """
    ensure_upload_dirs()

    # Validate file type
    ext = Path(original_filename).suffix.lower()
    if ext not in ['.md', '.markdown', '.html', '.htm']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only Markdown (.md, .markdown) or HTML (.html, .htm) files are allowed.",
        )

    # Validate file size (max 5MB)
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit.",
        )

    # Create user-specific directory
    user_dir = BLOG_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)

    # Generate filename
    filename = generate_blog_filename(blog_id, original_filename)
    file_path = user_dir / filename

    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)

    # Return relative path from project root
    relative_path = file_path.relative_to(UPLOAD_DIR.parent)
    return str(relative_path)


def get_blog_content_file_path(user_id: int, file_path: str) -> Optional[Path]:
    """
    Get the absolute path to a blog content file.

    Args:
        user_id: User ID
        file_path: Relative path from project root (e.g., 'uploads/blogs/40/blog_1.md')

    Returns:
        Absolute file path or None if file doesn't exist
    """
    if not file_path:
        return None

    # file_path is already relative to project root
    abs_path = UPLOAD_DIR.parent / file_path

    # Security check: ensure file is within upload directory
    try:
        abs_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return None

    if not abs_path.exists():
        return None

    return abs_path


def read_blog_content(user_id: int, file_path: str) -> Optional[str]:
    """
    Read a blog content file.

    Args:
        user_id: User ID
        file_path: Relative path stored in database

    Returns:
        File content as string or None if not found
    """
    abs_path = get_blog_content_file_path(user_id, file_path)
    if abs_path is None:
        return None

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def delete_blog_content(user_id: int, file_path: str) -> bool:
    """
    Delete a blog content file.

    Args:
        user_id: User ID
        file_path: Relative path stored in database

    Returns:
        True if deleted, False otherwise
    """
    abs_path = get_blog_content_file_path(user_id, file_path)
    if abs_path is None:
        return False

    try:
        abs_path.unlink()

        # Clean up user directory if empty
        user_dir = abs_path.parent
        if user_dir.exists() and not any(user_dir.iterdir()):
            user_dir.rmdir()

        return True
    except Exception:
        return False
