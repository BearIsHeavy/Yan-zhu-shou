"""
Migration: Add role column to User table

This migration adds the role column for RBAC (Role-Based Access Control).
The role column is used to distinguish between regular users, admins, and developers.

Run: python db_scripts/migrations/012_add_user_role.py
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
    """Add role column to User table."""
    async with engine.begin() as conn:
        print("=" * 60)
        print("Add User Role Column Migration")
        print("=" * 60)
        
        # Check if role column already exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'User' AND column_name = 'role'
            )
        """))
        
        if result.scalar():
            print("\n✓ User.role column already exists, skipping migration.")
            return
        
        print("\nAdding role column to User table...")
        
        # Add role column with default value 'user'
        await conn.execute(text("""
            ALTER TABLE "User" 
            ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL
        """))
        
        print("✓ Added User.role column (VARCHAR(20), DEFAULT 'user', NOT NULL)")
        
        # Add index for faster role-based queries
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_role ON "User"(role)
        """))
        
        print("✓ Created index on User.role")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nChanges applied:")
        print("  - Added User.role column")
        print("  - Created index on role column")
        print("\nExisting users:")
        print("  - All existing users have been assigned role='user'")
        print("\nUsage:")
        print("  - Regular users: role='user'")
        print("  - Administrators: role='admin'")
        print("  - Developers: role='developer'")


async def rollback():
    """Rollback migration changes."""
    async with engine.begin() as conn:
        print("Rolling back migration...")
        
        # Drop index
        await conn.execute(text("""
            DROP INDEX IF EXISTS idx_user_role
        """))
        print("  ✓ Dropped index on User.role")
        
        # Drop column
        await conn.execute(text("""
            ALTER TABLE "User" DROP COLUMN IF EXISTS role
        """))
        print("  ✓ Dropped User.role column")
        
        print("\nRollback completed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
