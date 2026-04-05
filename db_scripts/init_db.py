#!/usr/bin/env python
"""
Database Initialization Script for YanZhuShou.

Creates all tables, verifies their creation, and optionally seeds initial data.

Usage:
    python db_scripts/init_db.py              # Interactive mode
    python db_scripts/init_db.py --yes        # Non-interactive mode
    python db_scripts/init_db.py --verbose    # Show detailed SQL output
    python db_scripts/init_db.py --seed       # Create tables + seed demo data
    python db_scripts/init_db.py --drop       # Drop all tables first, then create
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to sys.path for relative imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from database import engine, Base
from sqlalchemy import inspect, text

# Import ALL models to register them with Base.metadata
from models import (
    # Core models
    User,
    QuestionBank,
    QBQuestion,
    StemText,
    AnswerText,
    UserQuestionLog,
    SecurityLog,
    Feedback,
    FeedbackVote,
    FeedbackNotification,
    Blog,
    BlogLike,
    BlogComment,
    SchoolInfo,
    UserSchoolMapping,
    # Books module
    UserBook,
    # Knowledge module
    KnowledgePoint,
    QuestionKnowledge,
    # Reports module
    AnalysisReport,
    # RAG module
    KnowledgeEmbedding,
    DocumentChunk,
    RAGQuery,
)

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def _color(text, color):
    """Apply color to text if terminal supports it."""
    if not sys.stdout.isatty():
        return text
    return f"{color}{text}{Colors.RESET}"

def success(text):
    return _color(f"  ✓ {text}", Colors.GREEN)

def info(text):
    return _color(f"  ℹ {text}", Colors.CYAN)

def warning(text):
    return _color(f"  ⚠ {text}", Colors.YELLOW)

def error(text):
    return _color(f"  ✗ {text}", Colors.RED)

def header(text):
    return _color(text, Colors.BOLD)


async def enable_extensions(verbose=False):
    """Enable required PostgreSQL extensions (e.g. pgvector)."""
    async with engine.begin() as conn:
        if verbose:
            print(info("Enabling PostgreSQL extensions..."))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    print(success("PostgreSQL extensions enabled (vector)"))


async def drop_all_tables():
    """Drop all tables managed by Base metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print(success("All tables dropped successfully"))


async def create_all_tables(verbose=False):
    """Create all tables registered in Base.metadata."""
    async with engine.begin() as conn:
        if verbose:
            print(info("Executing CREATE ALL TABLES..."))
        await conn.run_sync(Base.metadata.create_all)
    print(success("All tables created successfully"))


async def verify_tables(verbose=False):
    """Verify all expected tables exist in the database."""

    def _get_tables(sync_conn):
        insp = inspect(sync_conn)
        return insp.get_table_names()

    existing_tables = set()
    async with engine.begin() as conn:
        existing_tables = set(await conn.run_sync(_get_tables))

    expected_tables = set()
    for model in Base.registry.mappers:
        table = model.class_.__table__
        expected_tables.add(table.name)

    missing = expected_tables - existing_tables
    present = expected_tables & existing_tables

    print(f"\n{header('Table Verification Report')}")
    print(f"{'=' * 60}")
    print(f"  Expected tables: {len(expected_tables)}")
    print(f"  Created tables:  {len(present)}")
    print(f"  Missing tables:  {len(missing)}")
    print(f"{'=' * 60}")

    if present:
        print(f"\n{header('Existing Tables:')}")
        for table in sorted(present):
            print(success(table))

    if missing:
        print(f"\n{header('Missing Tables:')}")
        for table in sorted(missing):
            print(error(table))
        return False

    print(f"\n{success('All tables verified successfully!')}")
    return True


async def get_table_stats():
    """Get row count for each table."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from database import AsyncSessionLocal

    table_counts = {}
    async with AsyncSessionLocal() as session:
        for model in Base.registry.mappers:
            table_name = model.class_.__table__.name
            try:
                result = await session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = result.scalar()
                table_counts[table_name] = count
            except Exception:
                table_counts[table_name] = 0

    return table_counts


async def seed_demo_data():
    """Insert demo/seed data for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from database import AsyncSessionLocal
    from routes.auth import hash_password

    print(f"\n{header('Seeding Demo Data...')}")
    print(f"{'-' * 60}")

    async with AsyncSessionLocal() as session:
        try:
            # Check if demo user already exists
            result = await session.execute(
                text('SELECT COUNT(*) FROM "User" WHERE email = \'demo@example.com\'')
            )
            if result.scalar() > 0:
                print(warning("Demo user already exists, skipping..."))
                return

            # Create demo user
            hashed_pw = hash_password("demo123")
            await session.execute(
                text("""
                    INSERT INTO "User" (email, name, hash_password, phone, gender, role, created_at)
                    VALUES (:email, :name, :password, :phone, :gender, :role, NOW())
                """),
                {
                    "email": "demo@example.com",
                    "name": "Demo User",
                    "password": hashed_pw,
                    "phone": None,
                    "gender": 0,
                    "role": "user",
                }
            )
            print(success("Created demo user (demo@example.com / demo123)"))

            # Create demo school info
            await session.execute(
                text("""
                    INSERT INTO school_info
                    (id, city, region, school_code, school_name, college_code, college_name,
                     major_code, major_name, direction_code, direction_name, adjustment_count, create_time)
                    VALUES
                    ('demo_001', 'Beijing', 1, '10001', 'Demo University',
                     'C001', 'Computer Science', 'M001', 'Software Engineering',
                     'D001', 'AI Direction', 5, NOW())
                """)
            )
            print(success("Created demo school info"))

            # Create demo knowledge points
            await session.execute(
                text("""
                    INSERT INTO knowledge_points (name, subject, parent_id, difficulty, description, is_active, created_at, updated_at)
                    VALUES
                    ('Mathematics', 'Math', NULL, 3, 'General Mathematics', true, NOW(), NOW()),
                    ('Algebra', 'Math', 1, 3, 'Algebra fundamentals', true, NOW(), NOW()),
                    ('Geometry', 'Math', 1, 3, 'Geometry fundamentals', true, NOW(), NOW())
                """)
            )
            print(success("Created demo knowledge points"))

            await session.commit()
            print(f"{'-' * 60}")
            print(success("Demo data seeded successfully!"))

        except Exception as e:
            await session.rollback()
            print(error(f"Failed to seed demo data: {e}"))
            raise


async def main():
    """Main initialization function."""
    # Parse arguments
    args = sys.argv[1:]
    verbose = "--verbose" in args
    seed = "--seed" in args
    drop_first = "--drop" in args
    non_interactive = "--yes" in args

    print(f"\n{header('=' * 60)}")
    print(f"{header('  YanZhuShou Database Initialization')}")
    print(f"{header('=' * 60)}\n")

    # Show what will happen
    model_count = len(list(Base.registry.mappers))
    print(info(f"Registered models: {model_count}"))

    if drop_first:
        print(warning("Will DROP all existing tables before creation"))
    if seed:
        print(info("Will seed demo data after table creation"))
    print()

    # Interactive confirmation
    if not non_interactive and not drop_first and not seed:
        response = input("Proceed with database initialization? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Initialization cancelled.")
            sys.exit(0)
    elif drop_first and not non_interactive:
        response = input(warning("This will DELETE all existing data. Continue? (yes/no): "))
        if response.lower() not in ["yes", "y"]:
            print("Initialization cancelled.")
            sys.exit(0)

    try:
        total_steps = 5 if drop_first else 4
        step = 0

        # Step 1: Enable PostgreSQL extensions
        step += 1
        print(f"\n{header(f'Step {step}/{total_steps}: Enabling extensions...')}")
        await enable_extensions(verbose)

        # Step 2: Drop tables if requested
        if drop_first:
            step += 1
            print(f"\n{header(f'Step {step}/{total_steps}: Dropping existing tables...')}")
            await drop_all_tables()

        # Step 3: Create tables
        step += 1
        print(f"\n{header(f'Step {step}/{total_steps}: Creating tables...')}")
        await create_all_tables(verbose)

        # Step 4: Verify tables
        step += 1
        print(f"\n{header(f'Step {step}/{total_steps}: Verifying tables...')}")
        verified = await verify_tables(verbose)

        if not verified:
            print(error("\nTable verification failed! Some tables are missing."))
            sys.exit(1)

        # Step 5: Show stats
        step += 1
        print(f"\n{header(f'Step {step}/{total_steps}: Checking table stats...')}")
        stats = await get_table_stats()
        empty_tables = [name for name, count in sorted(stats.items()) if count == 0]
        if empty_tables:
            print(info(f"Empty tables (ready for data): {len(empty_tables)}"))
        else:
            print(info("All tables contain data"))

        # Optional: Seed demo data
        if seed:
            await seed_demo_data()

        # Final summary
        print(f"\n{header('=' * 60)}")
        print(success("Database initialization completed successfully!"))
        print(f"{header('=' * 60)}\n")

    except Exception as e:
        print(f"\n{error(f'Initialization failed: {e}')}")
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
