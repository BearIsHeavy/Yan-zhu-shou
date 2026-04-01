"""
Migration: Create user_school_mapping table

Run: python db_scripts/migrations/008_add_user_school_mapping.py
"""

import asyncio
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from database import engine


async def migrate():
    """Create user_school_mapping table and clear existing data."""
    async with engine.begin() as conn:
        # Clear existing data
        print("Clearing existing school_info data...")
        await conn.execute(text("TRUNCATE TABLE school_info CASCADE"))
        print("✓ Cleared school_info table.")
        
        # Check if table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'user_school_mapping'
            )
        """))
        exists = result.fetchone()[0]

        if exists:
            print("Table 'user_school_mapping' already exists.")
            return

        # Create table
        await conn.execute(text("""
            CREATE TABLE user_school_mapping (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                school_id VARCHAR(64) NOT NULL,
                UNIQUE(user_id, school_id),
                FOREIGN KEY (school_id) REFERENCES school_info(id) ON DELETE CASCADE
            )
        """))
        
        # Create indexes
        await conn.execute(text("""
            CREATE INDEX idx_user_school_mapping_user_id ON user_school_mapping(user_id)
        """))
        await conn.execute(text("""
            CREATE INDEX idx_user_school_mapping_school_id ON user_school_mapping(school_id)
        """))

        print("✓ Created table 'user_school_mapping' with indexes.")


async def rollback():
    """Drop user_school_mapping table."""
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS user_school_mapping CASCADE"))
        print("Dropped table 'user_school_mapping'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run migration 008")
    parser.add_argument("--rollback", action="store_true", help="Rollback")
    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
