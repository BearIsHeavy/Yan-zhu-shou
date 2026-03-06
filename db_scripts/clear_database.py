"""
Database cleanup script.
Deletes all data from all tables while keeping the table structure.

Usage:
    python db_scripts/clear_database.py

Warning: This will permanently delete all data!
"""

import asyncio
import sys
import os

# Add project root to sys.path for relative imports
# This allows the script to be run from any directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from database import AsyncSessionLocal, engine
from models import (
    User,
    UserQuestionLog,
    SecurityLog,
    QuestionBank,
    QBQuestion,
    StemText,
    AnswerText,
)


# Order matters due to foreign key constraints
# Tables with foreign keys should be cleared first
TABLES_TO_CLEAR = [
    UserQuestionLog,
    SecurityLog,
    StemText,
    AnswerText,
    QBQuestion,
    QuestionBank,
    User,
]


async def clear_all_tables():
    """Delete all records from all tables."""
    async with AsyncSessionLocal() as session:
        try:
            print("=" * 60)
            print("Starting database cleanup...")
            print("=" * 60)

            for model in TABLES_TO_CLEAR:
                table_name = model.__tablename__

                # Count records before deletion
                count_result = await session.execute(
                    text(f"SELECT COUNT(*) FROM \"{table_name}\"")
                )
                count = count_result.scalar()

                if count > 0:
                    # Delete all records
                    await session.execute(
                        text(f"DELETE FROM \"{table_name}\"")
                    )
                    await session.commit()
                    print(f"  ✓ Deleted {count} records from {table_name}")
                else:
                    print(f"  - {table_name} is already empty ({count} records)")

            print("=" * 60)
            print("Database cleanup completed successfully!")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error during cleanup: {e}")
            raise


async def reset_sequences():
    """Reset all auto-increment sequences to start from 1."""
    async with AsyncSessionLocal() as session:
        try:
            print("\nResetting auto-increment sequences...")

            for model in TABLES_TO_CLEAR:
                table_name = model.__tablename__
                primary_key = model.__table__.primary_key.columns.keys()[0]
                sequence_name = f"{table_name}_{primary_key}_seq"

                try:
                    await session.execute(
                        text(f"ALTER SEQUENCE \"{sequence_name}\" RESTART WITH 1")
                    )
                    await session.commit()
                    print(f"  ✓ Reset sequence for {table_name}")
                except Exception as e:
                    # Sequence might not exist, continue
                    print(f"  - Sequence for {table_name} not found or already reset")

            print("Sequence reset completed!")

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Error resetting sequences: {e}")


async def main():
    """Main function."""
    print("\n" + "!" * 60)
    print("WARNING: This will delete ALL data from the database!")
    print("!" * 60)

    # Check if --yes flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        print("\nProceeding with cleanup (--yes flag provided)...\n")
    else:
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cleanup cancelled.")
            sys.exit(0)

    try:
        await clear_all_tables()
        await reset_sequences()
    except Exception as e:
        print(f"\nCleanup failed: {e}")
        sys.exit(1)

    print("\nAll done!\n")


if __name__ == "__main__":
    asyncio.run(main())
