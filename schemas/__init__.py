"""
Pydantic schemas for API validation and serialization.

This module exports all schema classes for easy importing:
    from schemas import UserCreate, UserResponse, QuestionBankCreate, ...
"""

from schemas.user import (
    UserBase,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserResponse,
    UserLogin,
    BioFileResponse,
)
from schemas.token import Token, TokenData
from schemas.question import (
    QuestionBankBase,
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankResponse,
    QBQuestionBase,
    QBQuestionCreate,
    QBQuestionUpdate,
    QBQuestionResponse,
    QBQuestionItem,
)
from schemas.text import (
    StemTextBase,
    StemTextCreate,
    StemTextUpdate,
    StemTextResponse,
    StemTextItem,
    AnswerTextBase,
    AnswerTextCreate,
    AnswerTextUpdate,
    AnswerTextResponse,
)
from schemas.log import (
    UserQuestionLogBase,
    UserQuestionLogCreate,
    UserQuestionLogUpdate,
    UserQuestionLogResponse,
    SecurityLogBase,
    SecurityLogCreate,
    SecurityLogUpdate,
    SecurityLogResponse,
)
from schemas.mistake import (
    # Enums
    QuestionStatusEnum,
    QuestionTypeEnum,
    ErrorReasonEnum,
    # Wrong Question
    WrongQuestionBase,
    WrongQuestionResponse,
    WrongQuestionListResponse,
    WrongQuestionUpdate,
    WrongQuestionBatchUpdate,
    # Stats
    MistakeNotebookStats,
    # Answer Submission
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    PracticeSessionCreate,
    PracticeQuestion,
    PracticeSessionResponse,
)
from schemas.blog import (
    ContentTypeEnum,
    BlogCreate,
    BlogUpdate,
    BlogUserResponse,
    BlogResponse,
    BlogListItem,
    BlogListResponse,
    BlogCommentCreate,
    BlogCommentUpdate,
    BlogCommentResponse,
    BlogCommentListResponse,
    BlogLikeResponse,
    BlogStats,
    BlogSubmissionStatus,
    BlogTagResponse,
    BlogTagCreate,
    BlogTagListResponse,
    BlogContentResponse,
)
from schemas.school_info import (
    SchoolInfoBase,
    SchoolInfoCreate,
    SchoolInfoResponse,
    SchoolInfoUpdate,
    SchoolInfoListResponse,
    FetchTaskCreate,
    FetchTaskResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "BioFileResponse",
    # Token
    "Token",
    "TokenData",
    # QuestionBank
    "QuestionBankBase",
    "QuestionBankCreate",
    "QuestionBankUpdate",
    "QuestionBankResponse",
    # QBQuestion
    "QBQuestionBase",
    "QBQuestionCreate",
    "QBQuestionUpdate",
    "QBQuestionResponse",
    "QBQuestionItem",
    # StemText & AnswerText
    "StemTextBase",
    "StemTextCreate",
    "StemTextUpdate",
    "StemTextResponse",
    "StemTextItem",
    "AnswerTextBase",
    "AnswerTextCreate",
    "AnswerTextUpdate",
    "AnswerTextResponse",
    # Logs
    "UserQuestionLogBase",
    "UserQuestionLogCreate",
    "UserQuestionLogUpdate",
    "UserQuestionLogResponse",
    "SecurityLogBase",
    "SecurityLogCreate",
    "SecurityLogUpdate",
    "SecurityLogResponse",
    # Mistake Notebook Enums
    "QuestionStatusEnum",
    "QuestionTypeEnum",
    "ErrorReasonEnum",
    # Wrong Question
    "WrongQuestionBase",
    "WrongQuestionResponse",
    "WrongQuestionListResponse",
    "WrongQuestionUpdate",
    "WrongQuestionBatchUpdate",
    # Stats
    "MistakeNotebookStats",
    # Answer Submission
    "AnswerSubmitRequest",
    "AnswerSubmitResponse",
    "PracticeSessionCreate",
    "PracticeQuestion",
    "PracticeSessionResponse",
    # Blog
    "ContentTypeEnum",
    "BlogCreate",
    "BlogUpdate",
    "BlogUserResponse",
    "BlogResponse",
    "BlogListItem",
    "BlogListResponse",
    "BlogCommentCreate",
    "BlogCommentUpdate",
    "BlogCommentResponse",
    "BlogCommentListResponse",
    "BlogLikeResponse",
    "BlogStats",
    "BlogSubmissionStatus",
    "BlogTagResponse",
    "BlogTagCreate",
    "BlogTagListResponse",
    "BlogContentResponse",
    # School Info
    "SchoolInfoBase",
    "SchoolInfoCreate",
    "SchoolInfoResponse",
    "SchoolInfoUpdate",
    "SchoolInfoListResponse",
    "FetchTaskCreate",
    "FetchTaskResponse",
]
