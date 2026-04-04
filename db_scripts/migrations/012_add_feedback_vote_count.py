"""
Migration 012: Add vote_count to Feedback table

This migration adds the vote_count column to the Feedback table that is defined
in the SQLAlchemy model but missing from the database.

Run: python db_scripts/migrations/012_add_feedback_vote_count.py
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
    """Add vote_count column to Feedback table."""
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'Feedback' AND column_name = 'vote_count'
        """))
        exists = result.fetchone()

        if not exists:
            await conn.execute(text("""
                ALTER TABLE "Feedback"
                ADD COLUMN vote_count INTEGER NOT NULL DEFAULT 0
            """))
            print("Added 'vote_count' column to Feedback table.")
        else:
            print("Column 'vote_count' already exists in Feedback table.")

        print("Migration 012 completed successfully.")


async def rollback():
    """Rollback: drop the vote_count column."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE "Feedback"
            DROP COLUMN IF EXISTS vote_count
        """))
        print("Dropped 'vote_count' column from Feedback table.")
        print("Rolled back migration 012 successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 012")
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
