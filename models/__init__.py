"""
SQLAlchemy ORM models.

This module exports all model classes for easy importing:
    from models import User, QuestionBank, QBQuestion, UserQuestionLog, ...
"""

from database import Base

# Import all models to ensure they are registered with Base
from models.user import User
from models.question import QuestionBank, QBQuestion, StemText, AnswerText
from models.log import UserQuestionLog, SecurityLog
from models.feedback import Feedback, FeedbackVote, FeedbackNotification, FeedbackCategory, FeedbackStatus
from models.blog import Blog, BlogLike, BlogComment
from models.school_info import SchoolInfo
from models.user_school_mapping import UserSchoolMapping
from books.models.user_book import UserBook
from knowledge.models.knowledge_point import KnowledgePoint
from knowledge.models.question_knowledge import QuestionKnowledge
from reports.models.analysis_report import AnalysisReport

# Export all models
__all__ = [
    "Base",
    "User",
    "QuestionBank",
    "QBQuestion",
    "StemText",
    "AnswerText",
    "UserQuestionLog",
    "SecurityLog",
    "Feedback",
    "FeedbackVote",
    "FeedbackNotification",
    "FeedbackCategory",
    "FeedbackStatus",
    "Blog",
    "BlogLike",
    "BlogComment",
    "SchoolInfo",
    "UserSchoolMapping",
    "UserBook",
    "KnowledgePoint",
    "QuestionKnowledge",
    "AnalysisReport",
]
