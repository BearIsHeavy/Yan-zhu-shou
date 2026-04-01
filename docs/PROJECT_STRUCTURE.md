# 📁 Project Structure

Detailed overview of the YanZhuShou codebase organization.

## Directory Tree

```
YanZhuShou/
├── 📂 models/                 # Database models
│   ├── __init__.py
│   ├── user.py               # User model
│   ├── question.py           # QuestionBank, QBQuestion, StemText, AnswerText models
│   ├── mistake.py            # MistakeNotebook model
│   ├── feedback.py           # Feedback model
│   └── log.py                # SecurityLog model
│
├── 📂 routes/                 # API endpoints
│   ├── __init__.py
│   ├── auth.py               # Authentication utilities (JWT)
│   ├── users.py              # User registration, login endpoints
│   ├── question_banks.py     # Question bank CRUD endpoints
│   ├── questions.py          # Question upload endpoints (CSV/XML/Single)
│   ├── mistake.py            # Mistake notebook endpoints
│   └── feedback.py           # Feedback system endpoints
│
├── 📂 schemas/                # Pydantic models (if created)
│   ├── __init__.py
│   ├── user.py               # User schemas
│   ├── question.py           # Question bank & question schemas
│   ├── token.py              # Token schemas
│   └── text.py               # StemText & AnswerText schemas
│
├── 📂 test_api/               # API test scripts
│   ├── test_user.py          # User API tests
│   └── test_question_apis.py # Question API tests
│
├── 📂 db_scripts/             # Database scripts
│   ├── init_db.py            # Database initialization
│   └── clear_database.py     # Database cleanup
│
├── 📂 logs/                   # Application logs
│
├── 📂 docs/                   # Documentation
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── DATABASE_SCHEMA.md    # Database schema details
│   └── API_USAGE.md          # API usage guide
│
├── 📄 Core Files
├── database.py                # Database configuration & session management
├── dependencies.py            # Dependency injection (auth, db, redis)
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── cache_manager.py           # Redis cache management
│
└── 📝 Configuration
    ├── .env                   # Environment variables (git-ignored)
    ├── .env.example           # Environment template
    └── README.md              # Main documentation
```

## Core Directories

### `models/`
SQLAlchemy database models defining the schema structure.

| File | Model | Description |
|------|-------|-------------|
| `user.py` | `User` | User accounts and authentication |
| `question.py` | `QuestionBank`, `QBQuestion`, `StemText`, `AnswerText` | Question bank management |
| `mistake.py` | `MistakeNotebook` | User mistake tracking |
| `feedback.py` | `Feedback` | User feedback system |
| `log.py` | `SecurityLog` | Security audit logging |

### `routes/`
FastAPI router modules for API endpoints.

| File | Prefix | Description |
|------|--------|-------------|
| `users.py` | `/users` | User registration, login, profile |
| `question_banks.py` | `/question_banks` | Question bank CRUD operations |
| `questions.py` | `/upload` | Question import (CSV/XML/Single) |
| `mistake.py` | (root) | Mistake notebook operations |
| `feedback.py` | `/api/feedback` | Feedback submission and management |
| `auth.py` | - | Authentication utilities (internal) |

### `db_scripts/`
Database management scripts.

| File | Purpose |
|------|---------|
| `init_db.py` | Create all database tables |
| `clear_database.py` | Drop all tables (development only) |

### `test_api/`
API integration tests.

| File | Tests |
|------|-------|
| `test_user.py` | User registration, login, authentication |
| `test_question_apis.py` | Question bank and question operations |

## Core Modules

### `database.py`
- Async SQLAlchemy engine configuration
- Redis client initialization
- Session factory setup
- Database dependencies

### `dependencies.py`
- `get_current_user()`: JWT token validation
- `get_db()`: Database session dependency
- `get_redis()`: Redis client dependency

### `main.py`
- FastAPI application initialization
- CORS middleware configuration
- Router registration

### `cache_manager.py`
- Redis caching utilities
- Cache key management
- TTL handling

## Related Documentation

- [Database Schema](DATABASE_SCHEMA.md) - Detailed ER diagrams and table descriptions
- [API Usage](API_USAGE.md) - Complete API reference with examples
- [README](../README.md) - Quick start and setup guide
