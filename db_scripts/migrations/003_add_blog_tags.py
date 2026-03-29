"""
Migration 003: Add blog tags system

This migration creates:
- blog_tags table for storing unique tags
- blog_tags_association table for many-to-many blog-tag relationship

Run: python db_scripts/migrations/003_add_blog_tags.py
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
    """Create blog tags tables."""
    async with engine.begin() as conn:
        # Check if tables already exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'blog_tags'
        """))
        tags_exists = result.fetchone()

        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'blog_tags_association'
        """))
        assoc_exists = result.fetchone()

        if tags_exists and assoc_exists:
            print("Blog tags tables already exist.")
            return

        # Create blog_tags table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS blog_tags (
                tag_id SERIAL NOT NULL,
                name VARCHAR(10) NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                PRIMARY KEY (tag_id)
            )
        """))

        # Create index on name for faster lookups
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_blog_tags_name ON blog_tags (name)
        """))

        # Create unique constraint on name
        await conn.execute(text("""
            ALTER TABLE blog_tags ADD CONSTRAINT uq_blog_tags_name UNIQUE (name)
        """))

        # Create blog_tags_association table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS blog_tags_association (
                blog_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (blog_id, tag_id),
                FOREIGN KEY(blog_id) REFERENCES blogs (blog_id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES blog_tags (tag_id) ON DELETE CASCADE
            )
        """))

        print("Created blog_tags and blog_tags_association tables.")


async def rollback():
    """Remove blog tags tables."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            DROP TABLE IF EXISTS blog_tags_association CASCADE
        """))
        await conn.execute(text("""
            DROP TABLE IF EXISTS blog_tags CASCADE
        """))
        print("Removed blog_tags and blog_tags_association tables.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 003")
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
