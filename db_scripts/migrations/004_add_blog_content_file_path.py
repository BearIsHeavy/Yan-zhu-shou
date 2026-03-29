"""
Migration 004: Change blog content from text to file path

This migration:
- Adds content_file_path column to blogs table
- Drops the old content column

Run: python db_scripts/migrations/004_add_blog_content_file_path.py
"""

import asyncio
import os
import sys

# Add project root to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from database import engine


async def migrate():
    """Update blogs table to use content_file_path instead of content."""
    async with engine.begin() as conn:
        # Check if content_file_path column already exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'blogs' AND column_name = 'content_file_path'
        """))
        path_exists = result.fetchone()

        if path_exists:
            print("Column 'content_file_path' already exists in blogs table.")
            return

        # Add content_file_path column
        await conn.execute(text("""
            ALTER TABLE blogs 
            ADD COLUMN content_file_path VARCHAR(255)
        """))

        # Drop old content column
        await conn.execute(text("""
            ALTER TABLE blogs 
            DROP COLUMN content
        """))

        print("Updated blogs table: added content_file_path, dropped content column.")


async def rollback():
    """Rollback: add content column back, drop content_file_path."""
    async with engine.begin() as conn:
        # Add content column back (TEXT, nullable to allow existing rows)
        await conn.execute(text("""
            ALTER TABLE blogs 
            ADD COLUMN content TEXT
        """))

        # Drop content_file_path column
        await conn.execute(text("""
            ALTER TABLE blogs 
            DROP COLUMN content_file_path
        """))

        print("Rolled back: added content column, dropped content_file_path.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 004")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration"
    )
    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
