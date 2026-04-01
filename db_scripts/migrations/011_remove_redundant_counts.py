"""
Migration: Remove redundant count columns and enhance FeedbackNotification

Changes:
1. Remove Blog.like_count and Blog.comment_count (now computed from relationships)
2. Remove Feedback.vote_count (now computed from relationships)
3. Add new columns to FeedbackNotification for better notification tracking

Run: python db_scripts/migrations/011_remove_redundant_counts.py
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
    """Apply migration changes."""
    async with engine.begin() as conn:
        print("=" * 60)
        print("Remove Redundant Counts Migration")
        print("=" * 60)
        
        # 1. Remove Blog.like_count and Blog.comment_count
        print("\n[1/2] Removing redundant columns from blogs table...")
        
        # Check and drop like_count
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'blogs' AND column_name = 'like_count'
            )
        """))
        if result.scalar():
            await conn.execute(text("ALTER TABLE blogs DROP COLUMN like_count"))
            print("  ✓ Dropped blogs.like_count")
        else:
            print("  - blogs.like_count does not exist, skipping")
        
        # Check and drop comment_count
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'blogs' AND column_name = 'comment_count'
            )
        """))
        if result.scalar():
            await conn.execute(text("ALTER TABLE blogs DROP COLUMN comment_count"))
            print("  ✓ Dropped blogs.comment_count")
        else:
            print("  - blogs.comment_count does not exist, skipping")
        
        # 2. Remove Feedback.vote_count
        print("\n[2/3] Removing redundant column from Feedback table...")
        
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'Feedback' AND column_name = 'vote_count'
            )
        """))
        if result.scalar():
            await conn.execute(text("ALTER TABLE \"Feedback\" DROP COLUMN vote_count"))
            print("  ✓ Dropped Feedback.vote_count")
        else:
            print("  - Feedback.vote_count does not exist, skipping")
        
        # 3. Add new columns to FeedbackNotification
        print("\n[3/3] Adding new columns to FeedbackNotification table...")
        
        # recipient_user_id
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'recipient_user_id'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN recipient_user_id INTEGER REFERENCES "User"(user_id) ON DELETE CASCADE
            """))
            print("  ✓ Added FeedbackNotification.recipient_user_id")
        else:
            print("  - recipient_user_id already exists, skipping")
        
        # notification_channel
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'notification_channel'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN notification_channel VARCHAR(20) DEFAULT 'in_app' NOT NULL
            """))
            print("  ✓ Added FeedbackNotification.notification_channel")
        else:
            print("  - notification_channel already exists, skipping")
        
        # notification_content
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'notification_content'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN notification_content TEXT
            """))
            print("  ✓ Added FeedbackNotification.notification_content")
        else:
            print("  - notification_content already exists, skipping")
        
        # sent_at
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'sent_at'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN sent_at TIMESTAMP
            """))
            print("  ✓ Added FeedbackNotification.sent_at")
        else:
            print("  - sent_at already exists, skipping")
        
        # is_read
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'is_read'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN is_read SMALLINT DEFAULT 0
            """))
            print("  ✓ Added FeedbackNotification.is_read")
        else:
            print("  - is_read already exists, skipping")
        
        # read_at
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'FeedbackNotification' AND column_name = 'read_at'
            )
        """))
        if not result.scalar():
            await conn.execute(text("""
                ALTER TABLE "FeedbackNotification" 
                ADD COLUMN read_at TIMESTAMP
            """))
            print("  ✓ Added FeedbackNotification.read_at")
        else:
            print("  - read_at already exists, skipping")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nChanges applied:")
        print("  - Removed blogs.like_count (now computed)")
        print("  - Removed blogs.comment_count (now computed)")
        print("  - Removed Feedback.vote_count (now computed)")
        print("  - Added FeedbackNotification.recipient_user_id")
        print("  - Added FeedbackNotification.notification_channel")
        print("  - Added FeedbackNotification.notification_content")
        print("  - Added FeedbackNotification.sent_at")
        print("  - Added FeedbackNotification.is_read")
        print("  - Added FeedbackNotification.read_at")


async def rollback():
    """Rollback migration changes."""
    async with engine.begin() as conn:
        print("Rolling back migration...")
        
        # Add back redundant columns
        await conn.execute(text("ALTER TABLE blogs ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0"))
        print("  ✓ Added back blogs.like_count")
        
        await conn.execute(text("ALTER TABLE blogs ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0"))
        print("  ✓ Added back blogs.comment_count")
        
        await conn.execute(text('ALTER TABLE "Feedback" ADD COLUMN IF NOT EXISTS vote_count INTEGER DEFAULT 0'))
        print("  ✓ Added back Feedback.vote_count")
        
        # Drop new columns
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS recipient_user_id'))
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS notification_channel'))
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS notification_content'))
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS sent_at'))
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS is_read'))
        await conn.execute(text('ALTER TABLE "FeedbackNotification" DROP COLUMN IF EXISTS read_at'))
        
        print("\nRollback completed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
