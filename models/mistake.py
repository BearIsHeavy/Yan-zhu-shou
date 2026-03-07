"""
SQLAlchemy models and helpers for Mistake Notebook feature.

This module provides helpers for the Mistake Notebook feature,
which uses the existing `user_question_logs` table to track wrong questions.

Wrong questions are identified by filtering `user_question_logs` where 
`is_correct = False`.

Database Schema Reference: docs/数据库设计.sql
"""

# Re-export UserQuestionLog from log module
# The actual model is defined in models/log.py
from models.log import UserQuestionLog

__all__ = ["UserQuestionLog"]
