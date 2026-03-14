"""
Migration: Add Feedback System Tables

This migration creates the tables for the "You Say, I Fix" feedback system:
- Feedback: Main feedback table
- FeedbackVote: User votes on feedback
- FeedbackNotification: Notification tracking

Run this migration after ensuring the User table exists.
"""

from sqlalchemy import text
from database import engine


async def migrate():
    """Run the migration."""
    async with engine.begin() as conn:
        # Create Feedback table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS "Feedback" (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                category VARCHAR(50) DEFAULT 'other',
                status VARCHAR(50) DEFAULT 'pending',
                vote_count INTEGER DEFAULT 0,
                developer_response TEXT,
                responded_at TIMESTAMP,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create index on user_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_user_id 
            ON "Feedback"(user_id)
        """))
        
        # Create index on status
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_status 
            ON "Feedback"(status)
        """))
        
        # Create index on vote_count for sorting
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_vote_count 
            ON "Feedback"(vote_count DESC)
        """))
        
        # Create index on created_at for sorting
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at 
            ON "Feedback"(created_at DESC)
        """))
        
        # Create FeedbackVote table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS "FeedbackVote" (
                id SERIAL PRIMARY KEY,
                feedback_id INTEGER NOT NULL REFERENCES "Feedback"(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES "User"(user_id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_feedback_user_vote UNIQUE (feedback_id, user_id)
            )
        """))
        
        # Create index on feedback_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_vote_feedback_id 
            ON "FeedbackVote"(feedback_id)
        """))
        
        # Create index on user_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_vote_user_id 
            ON "FeedbackVote"(user_id)
        """))
        
        # Create FeedbackNotification table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS "FeedbackNotification" (
                id SERIAL PRIMARY KEY,
                feedback_id INTEGER NOT NULL REFERENCES "Feedback"(id) ON DELETE CASCADE,
                notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_type VARCHAR(50) NOT NULL,
                is_sent SMALLINT DEFAULT 0
            )
        """))
        
        # Create index on feedback_id
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_notification_feedback_id 
            ON "FeedbackNotification"(feedback_id)
        """))
        
        print("✓ Feedback system tables created successfully")


async def rollback():
    """Rollback the migration."""
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS "FeedbackNotification"'))
        await conn.execute(text('DROP TABLE IF EXISTS "FeedbackVote"'))
        await conn.execute(text('DROP TABLE IF EXISTS "Feedback"'))
        print("✓ Feedback system tables dropped successfully")


if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("Running feedback system migration...")
        await migrate()
        print("Migration complete!")
    
    asyncio.run(main())
