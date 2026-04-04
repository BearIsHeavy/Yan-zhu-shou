"""
Migration: Add AI Analysis tables

This migration creates tables for:
- knowledge_points: Knowledge point hierarchy
- question_knowledge: Question-Knowledge associations
- user_books: User-uploaded books
- analysis_reports: AI analysis reports

Run: python db_scripts/migrations/009_add_ai_analysis_tables.py
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
    """Create AI analysis tables."""
    async with engine.begin() as conn:
        print("=" * 60)
        print("AI Analysis Tables Migration")
        print("=" * 60)
        
        # 1. Create knowledge_points table
        print("\n[1/4] Creating knowledge_points table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_points (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                parent_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
                difficulty SMALLINT DEFAULT 3 NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_name ON knowledge_points(name)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_subject ON knowledge_points(subject)"))
        print("✓ Created knowledge_points table")
        
        # 2. Create question_knowledge table
        print("\n[2/4] Creating question_knowledge table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS question_knowledge (
                id SERIAL PRIMARY KEY,
                question_no INTEGER NOT NULL REFERENCES qb_questions(No) ON DELETE CASCADE,
                knowledge_id INTEGER NOT NULL REFERENCES knowledge_points(id) ON DELETE CASCADE,
                weight FLOAT DEFAULT 1.0 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(question_no, knowledge_id)
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qk_question ON question_knowledge(question_no)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_qk_knowledge ON question_knowledge(knowledge_id)"))
        print("✓ Created question_knowledge table")
        
        # 3. Create user_books table
        print("\n[3/4] Creating user_books table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_books (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
                title VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000) NOT NULL,
                file_type VARCHAR(20) NOT NULL,
                file_size INTEGER NOT NULL,
                status SMALLINT DEFAULT 0 NOT NULL,
                knowledge_tree TEXT,
                chapter_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_user ON user_books(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_status ON user_books(status)"))
        print("✓ Created user_books table")
        
        # 4. Create analysis_reports table
        print("\n[4/4] Creating analysis_reports table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analysis_reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
                report_type VARCHAR(50) NOT NULL,
                data TEXT NOT NULL,
                summary TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_user ON analysis_reports(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_type ON analysis_reports(report_type)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_user_type ON analysis_reports(user_id, report_type)"))
        print("✓ Created analysis_reports table")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)


async def rollback():
    """Drop AI analysis tables."""
    async with engine.begin() as conn:
        print("Rolling back AI analysis tables...")
        
        await conn.execute(text("DROP TABLE IF EXISTS analysis_reports CASCADE"))
        print("✓ Dropped analysis_reports")
        
        await conn.execute(text("DROP TABLE IF EXISTS user_books CASCADE"))
        print("✓ Dropped user_books")
        
        await conn.execute(text("DROP TABLE IF EXISTS question_knowledge CASCADE"))
        print("✓ Dropped question_knowledge")
        
        await conn.execute(text("DROP TABLE IF EXISTS knowledge_points CASCADE"))
        print("✓ Dropped knowledge_points")
        
        print("Rollback completed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
