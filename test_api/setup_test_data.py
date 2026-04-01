"""
Test Data Setup and Cleanup Script.

Creates test data for core API test modules (Blog, Feedback, Question Bank, Mistake Notebook),
then cleans up after testing.

Note: This script does NOT include AI-related modules (Knowledge, Books, Reports, School Info).

Usage:
    python test_api/setup_test_data.py           # Setup test data
    python test_api/setup_test_data.py --cleanup # Cleanup test data
    python test_api/setup_test_data.py --both    # Setup, then cleanup

Note: Requires database connection configured in .env
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete, text

# Import models (core modules only)
from models.user import User
from models.blog import Blog, BlogLike, BlogComment
from models.feedback import Feedback, FeedbackVote, FeedbackNotification
from models.question import QuestionBank, QBQuestion
from models.log import UserQuestionLog

# Database URL from environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://api:api@localhost:5432/fastapi_db")

# Create async engine and session
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class TestDataGenerator:
    """Generate test data for core modules only."""
    
    # Test data identifiers (for easy cleanup)
    TEST_USER_EMAIL = "test@example.com"
    
    def __init__(self):
        self.created_ids = {
            'blogs': [],
            'feedbacks': [],
            'question_banks': [],
            'questions': [],
        }
    
    async def get_test_user(self, session: AsyncSession) -> User:
        """Get test user."""
        result = await session.execute(
            select(User).where(User.email == self.TEST_USER_EMAIL)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"⚠️  Test user {self.TEST_USER_EMAIL} not found in database!")
            print("   Please create the user first.")
            raise ValueError(f"Test user {self.TEST_USER_EMAIL} not found")
        
        return user
    
    async def create_blogs(self, session: AsyncSession, user: User):
        """Create test blogs."""
        print("  Creating test blogs...")
        
        blogs_data = [
            {
                "title": "Test Blog - Introduction to Python",
                "content_file_path": "uploads/blogs/1/test_blog_1.md",
                "content_type": "markdown",
                "tags": "python,programming,test",
                "is_published": True,
            },
            {
                "title": "Test Blog - Database Design Patterns",
                "content_file_path": "uploads/blogs/1/test_blog_2.md",
                "content_type": "markdown",
                "tags": "database,design,test",
                "is_published": True,
            },
            {
                "title": "Test Blog - Draft Article",
                "content_file_path": "uploads/blogs/1/test_blog_3.md",
                "content_type": "markdown",
                "tags": "draft,test",
                "is_published": False,
            },
        ]
        
        for blog_data in blogs_data:
            blog = Blog(user_id=user.user_id, **blog_data)
            session.add(blog)
            await session.flush()
            # Refresh to get the blog_id
            await session.refresh(blog)
            self.created_ids['blogs'].append(blog.blog_id)
            print(f"    ✓ Created blog: {blog.title}")
        
        # Create some likes
        for blog_id in self.created_ids['blogs'][:2]:
            like = BlogLike(blog_id=blog_id, user_id=user.user_id)
            session.add(like)
        
        # Create some comments
        comment = BlogComment(
            blog_id=self.created_ids['blogs'][0],
            user_id=user.user_id,
            content="Test comment on blog post",
            is_deleted=False
        )
        session.add(comment)
        
        await session.flush()
        print(f"    ✓ Created {len(self.created_ids['blogs'])} blogs with likes and comments")
    
    async def create_feedbacks(self, session: AsyncSession, user: User):
        """Create test feedbacks."""
        print("  Creating test feedbacks...")
        
        feedbacks_data = [
            {
                "content": "Test feedback: The app crashes when uploading large files.",
                "category": "bug",
                "status": "pending",
            },
            {
                "content": "Test feedback: Please add dark mode support.",
                "category": "feature",
                "status": "in_progress",
            },
            {
                "content": "Test feedback: The UI looks great on mobile!",
                "category": "ui",
                "status": "completed",
            },
        ]
        
        for fb_data in feedbacks_data:
            feedback = Feedback(user_id=user.user_id, **fb_data)
            session.add(feedback)
            await session.flush()
            self.created_ids['feedbacks'].append(feedback.id)
            print(f"    ✓ Created feedback: {fb_data['category']} - {fb_data['content'][:50]}...")
        
        # Create some votes
        for feedback_id in self.created_ids['feedbacks'][:2]:
            vote = FeedbackVote(feedback_id=feedback_id, user_id=user.user_id)
            session.add(vote)
        
        # Create notification
        notification = FeedbackNotification(
            feedback_id=self.created_ids['feedbacks'][0],
            recipient_user_id=user.user_id,
            notification_channel="in_app",
            notification_type="threshold_reached",
            notification_content="Your feedback has received attention",
            is_sent=1,
            is_read=0
        )
        session.add(notification)
        
        await session.flush()
        print(f"    ✓ Created {len(self.created_ids['feedbacks'])} feedbacks with votes")
    
    async def create_question_banks(self, session: AsyncSession, user: User):
        """Create test question banks and questions."""
        print("  Creating test question banks...")
        
        banks_data = [
            {
                "name": "Test Question Bank - Mathematics",
                "description": "Test mathematics questions",
                "is_public": True,
            },
            {
                "name": "Test Question Bank - Physics",
                "description": "Test physics questions",
                "is_public": False,
            },
        ]
        
        for bank_data in banks_data:
            bank = QuestionBank(user_id=user.user_id, **bank_data)
            session.add(bank)
            await session.flush()
            self.created_ids['question_banks'].append(bank.bank_id)
            print(f"    ✓ Created question bank: {bank.name}")
        
        # Create questions for each bank
        questions_data = [
            {
                "bank_id": self.created_ids['question_banks'][0],
                "category": "Algebra",
                "stem": "Solve for x: x² - 5x + 6 = 0",
                "qus_type": 1,  # Single choice
                "options": '{"A": "x=2", "B": "x=3", "C": "x=2 or x=3", "D": "x=1"}',
                "correct_ans_summary": "C",
                "is_public": True,
                "user_id": user.user_id,
            },
            {
                "bank_id": self.created_ids['question_banks'][0],
                "category": "Geometry",
                "stem": "What is the area of a circle with radius 5?",
                "qus_type": 1,
                "options": '{"A": "25π", "B": "10π", "C": "5π", "D": "50π"}',
                "correct_ans_summary": "A",
                "is_public": True,
                "user_id": user.user_id,
            },
            {
                "bank_id": self.created_ids['question_banks'][1],
                "category": "Mechanics",
                "stem": "What is Newton's second law?",
                "qus_type": 1,
                "options": '{"A": "F=ma", "B": "E=mc²", "C": "v=at", "D": "p=mv"}',
                "correct_ans_summary": "A",
                "is_public": True,
                "user_id": user.user_id,
            },
        ]
        
        for q_data in questions_data:
            question = QBQuestion(**q_data)
            session.add(question)
            await session.flush()
            self.created_ids['questions'].append(question.No)
            print(f"    ✓ Created question: {question.stem[:50]}...")
        
        print(f"    ✓ Created {len(self.created_ids['questions'])} questions")
    
    async def create_mistake_logs(self, session: AsyncSession, user: User):
        """Create test mistake notebook entries."""
        print("  Creating test mistake notebook entries...")
        
        if not self.created_ids['questions']:
            print("    ⚠️  No questions created, skipping mistake logs")
            return
        
        # Create some wrong answer logs
        for question_no in self.created_ids['questions'][:2]:
            log = UserQuestionLog(
                user_id=user.user_id,
                question_no=question_no,
                user_answer="A",
                is_correct=False,
                attempt_time=datetime.utcnow() - timedelta(days=5),
                is_mastered=False
            )
            session.add(log)
        
        # Create one correct answer log
        if len(self.created_ids['questions']) > 2:
            log = UserQuestionLog(
                user_id=user.user_id,
                question_no=self.created_ids['questions'][2],
                user_answer="A",
                is_correct=True,
                attempt_time=datetime.utcnow() - timedelta(days=2),
                is_mastered=True
            )
            session.add(log)
        
        await session.flush()
        print("    ✓ Created mistake notebook entries")
    
    async def setup_all(self):
        """Setup all test data."""
        print("\n" + "="*60)
        print("  Setting up test data")
        print("="*60 + "\n")
        
        async with AsyncSessionLocal() as session:
            try:
                # First, drop view_count column if it exists (not in model anymore)
                try:
                    await session.execute(
                        text('ALTER TABLE blogs DROP COLUMN IF EXISTS view_count')
                    )
                    await session.commit()
                    print("  ✓ Dropped view_count column from blogs table\n")
                except Exception as e:
                    print(f"  ⚠️  Could not drop view_count: {e}\n")
                    await session.rollback()
                
                # Get test user
                user = await self.get_test_user(session)
                print(f"  ✓ Found test user: {user.email}\n")
                
                # Create test data (core modules only)
                await self.create_blogs(session, user)
                print()
                
                await self.create_feedbacks(session, user)
                print()
                
                await self.create_question_banks(session, user)
                print()
                
                await self.create_mistake_logs(session, user)
                print()
                
                # Commit all changes
                await session.commit()
                
                print("\n" + "="*60)
                print("  Test data setup completed!")
                print("="*60)
                print(f"\n  Created:")
                for table, ids in self.created_ids.items():
                    print(f"    - {table}: {len(ids)} records")
                print()
                
            except Exception as e:
                await session.rollback()
                print(f"\n✗ Error setting up test data: {e}")
                raise
    
    async def cleanup_all(self):
        """Cleanup all test data."""
        print("\n" + "="*60)
        print("  Cleaning up test data")
        print("="*60 + "\n")
        
        async with AsyncSessionLocal() as session:
            try:
                user = await self.get_test_user(session)
                
                # Delete in reverse order (respecting foreign keys)
                
                # Delete feedback notifications, votes
                if self.created_ids['feedbacks']:
                    await session.execute(
                        delete(FeedbackNotification).where(
                            FeedbackNotification.feedback_id.in_(self.created_ids['feedbacks'])
                        )
                    )
                    await session.execute(
                        delete(FeedbackVote).where(
                            FeedbackVote.feedback_id.in_(self.created_ids['feedbacks'])
                        )
                    )
                
                # Delete feedbacks
                if self.created_ids['feedbacks']:
                    await session.execute(
                        delete(Feedback).where(Feedback.id.in_(self.created_ids['feedbacks']))
                    )
                    print(f"  ✓ Deleted {len(self.created_ids['feedbacks'])} feedbacks")
                
                # Delete blog comments, likes
                if self.created_ids['blogs']:
                    await session.execute(
                        delete(BlogComment).where(
                            BlogComment.blog_id.in_(self.created_ids['blogs'])
                        )
                    )
                    await session.execute(
                        delete(BlogLike).where(
                            BlogLike.blog_id.in_(self.created_ids['blogs'])
                        )
                    )
                
                # Delete blogs
                if self.created_ids['blogs']:
                    await session.execute(
                        delete(Blog).where(Blog.blog_id.in_(self.created_ids['blogs']))
                    )
                    print(f"  ✓ Deleted {len(self.created_ids['blogs'])} blogs")
                
                # Delete mistake logs
                await session.execute(
                    delete(UserQuestionLog).where(UserQuestionLog.user_id == user.user_id)
                )
                print("  ✓ Deleted mistake notebook entries")
                
                # Delete questions
                if self.created_ids['questions']:
                    await session.execute(
                        delete(QBQuestion).where(QBQuestion.No.in_(self.created_ids['questions']))
                    )
                    print(f"  ✓ Deleted {len(self.created_ids['questions'])} questions")
                
                # Delete question banks
                if self.created_ids['question_banks']:
                    await session.execute(
                        delete(QuestionBank).where(QuestionBank.bank_id.in_(self.created_ids['question_banks']))
                    )
                    print(f"  ✓ Deleted {len(self.created_ids['question_banks'])} question banks")
                
                await session.commit()
                
                print("\n" + "="*60)
                print("  Test data cleanup completed!")
                print("="*60 + "\n")
                
            except Exception as e:
                await session.rollback()
                print(f"\n✗ Error cleaning up test data: {e}")
                raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test data setup and cleanup")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup test data only"
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Setup then cleanup (for testing)"
    )
    
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    
    if args.cleanup:
        await generator.cleanup_all()
    elif args.both:
        await generator.setup_all()
        await asyncio.sleep(2)  # Wait a bit
        await generator.cleanup_all()
    else:
        await generator.setup_all()


if __name__ == "__main__":
    asyncio.run(main())
