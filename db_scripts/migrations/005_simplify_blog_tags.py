"""
Migration 005: Simplify blog tags - store as comma-separated string in blogs table

This migration:
- Adds tags column to blogs table
- Drops blog_tags and blog_tags_association tables

Run: python db_scripts/migrations/005_simplify_blog_tags.py
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
    """Add tags column and drop unused tables."""
    async with engine.begin() as conn:
        # Check if tags column already exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'blogs' AND column_name = 'tags'
        """))
        tags_exists = result.fetchone()

        if not tags_exists:
            # Add tags column
            await conn.execute(text("""
                ALTER TABLE blogs 
                ADD COLUMN tags VARCHAR(100)
            """))
            print("Added 'tags' column to blogs table.")
        else:
            print("Column 'tags' already exists in blogs table.")

        # Drop blog_tags_association table
        await conn.execute(text("""
            DROP TABLE IF EXISTS blog_tags_association
        """))
        print("Dropped blog_tags_association table.")

        # Drop blog_tags table
        await conn.execute(text("""
            DROP TABLE IF EXISTS blog_tags
        """))
        print("Dropped blog_tags table.")

        print("Migration completed: blogs table now stores tags as comma-separated string.")


async def rollback():
    """Rollback: add back blog_tags tables, drop tags column."""
    async with engine.begin() as conn:
        # Drop tags column
        await conn.execute(text("""
            ALTER TABLE blogs 
            DROP COLUMN IF EXISTS tags
        """))

        # Recreate blog_tags table
        await conn.execute(text("""
            CREATE TABLE blog_tags (
                tag_id SERIAL NOT NULL,
                name VARCHAR(10) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT now(),
                PRIMARY KEY (tag_id)
            )
        """))

        # Recreate blog_tags_association table
        await conn.execute(text("""
            CREATE TABLE blog_tags_association (
                blog_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (blog_id, tag_id),
                FOREIGN KEY(blog_id) REFERENCES blogs (blog_id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES blog_tags (tag_id) ON DELETE CASCADE
            )
        """))

        print("Rolled back: recreated blog_tags tables, dropped tags column.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 005")
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
