"""
Migration 011: Add view_count, like_count, comment_count to blogs table

This migration adds statistics columns to the blogs table that are defined
in the SQLAlchemy model but missing from the database.

Run: python db_scripts/migrations/011_add_blog_statistics_columns.py
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
    """Add view_count, like_count, comment_count columns to blogs table."""
    async with engine.begin() as conn:
        columns_to_add = [
            ("view_count", "INTEGER NOT NULL DEFAULT 0"),
            ("like_count", "INTEGER NOT NULL DEFAULT 0"),
            ("comment_count", "INTEGER NOT NULL DEFAULT 0"),
        ]

        for col_name, col_def in columns_to_add:
            # Check if column already exists
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'blogs' AND column_name = :col_name
            """), {"col_name": col_name})
            exists = result.fetchone()

            if not exists:
                await conn.execute(text(f"""
                    ALTER TABLE blogs
                    ADD COLUMN {col_name} {col_def}
                """))
                print(f"Added '{col_name}' column to blogs table.")
            else:
                print(f"Column '{col_name}' already exists in blogs table.")

        print("Migration 011 completed successfully.")


async def rollback():
    """Rollback: drop the added columns."""
    async with engine.begin() as conn:
        columns_to_drop = ["view_count", "like_count", "comment_count"]

        for col_name in columns_to_drop:
            await conn.execute(text(f"""
                ALTER TABLE blogs
                DROP COLUMN IF EXISTS {col_name}
            """))
            print(f"Dropped '{col_name}' column from blogs table.")

        print("Rolled back migration 011 successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 011")
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
