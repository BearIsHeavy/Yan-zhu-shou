"""
Migration 002: Add bio_file_path column to User table

This migration adds a column for storing the relative path to user's
self-introduction markdown file.

Run: python db_scripts/migrations/002_add_user_bio_file.py
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
    """Add bio_file_path column to User table."""
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'User' AND column_name = 'bio_file_path'
        """))
        exists = result.fetchone()

        if exists:
            print("Column 'bio_file_path' already exists in User table.")
            return

        # Add the column
        await conn.execute(text("""
            ALTER TABLE "User" 
            ADD COLUMN bio_file_path VARCHAR(255)
        """))

        print("Added 'bio_file_path' column to User table.")


async def rollback():
    """Remove bio_file_path column from User table."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE "User" 
            DROP COLUMN IF EXISTS bio_file_path
        """))
        print("Removed 'bio_file_path' column from User table.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 002")
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
