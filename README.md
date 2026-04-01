# 📚 YanZhuShou - Educational Platform API

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

**A comprehensive RESTful API for educational question banks, blogs, and user management**

[Quick Start](#-quick-start) • [API Docs](http://localhost:8000/docs) • [Documentation](docs/)

</div>

---

## 🎯 What is YanZhuShou?

YanZhuShou is a modern educational platform backend built with FastAPI and PostgreSQL. It provides:

- 📚 **Question Bank Management** - Create, import, and manage educational questions
- 📝 **Blog System** - Share knowledge with markdown/HTML blog posts and tags
- 👤 **User Profiles** - Self-introduction with markdown bio files
- 🔐 **Secure Authentication** - JWT-based auth with Redis caching
- 💬 **Interactive Features** - Comments, likes, and feedback system

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- PostgreSQL 16+
- Redis (optional)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/YanZhuShou.git
cd YanZhuShou/Server
```

### 2. Setup Environment with uv

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Required: Update SECRET_KEY for production
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Key Configuration:**

| Variable | Description | Example                                                    |
|----------|-------------|------------------------------------------------------------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://user:password@localhost:5432/dbname` |
| `REDIS_URL` | Redis connection (optional) | `redis://localhost:6379/0`                                 |
| `SECRET_KEY` | JWT signing key | **Generate unique key for each deployment**                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | `30`                                                       |

### 4. Start Database Services

```bash
# Using Docker (recommended)
docker run -d --name postgres \
  -e POSTGRES_USER=api \
  -e POSTGRES_PASSWORD=api \
  -e POSTGRES_DB=fastapi_db \
  -p 5432:5432 postgres:16-alpine

docker run -d --name redis -p 6379:6379 redis:7.2-alpine

# Or use your local PostgreSQL and Redis installations
```

### 5. Initialize Database

```bash
# Create all database tables
python db_scripts/init_db.py
```

### 6. Run Server

```bash
# Development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (multiple workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Access API

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000

---

## 📁 Project Structure

```
Server/
├── main.py                 # FastAPI app entry point
├── database.py             # Database connection
├── dependencies.py         # Auth and DB dependencies
├── models/                 # SQLAlchemy ORM models
│   ├── user.py            # User model
│   ├── blog.py            # Blog, BlogLike, BlogComment
│   ├── question.py        # QuestionBank, QBQuestion
│   └── feedback.py        # Feedback system
├── schemas/                # Pydantic schemas
├── routes/                 # API endpoints
├── services/               # Business logic
├── utils/                  # Utilities (file storage)
├── db_scripts/             # Database scripts
└── docs/                   # Documentation
```

---

## 🧪 Testing

```bash
# Start server
uvicorn main:app --reload &

# Run tests
python test_api/test_user.py
python test_api/test_question_apis.py
python test_api/test_blog_apis.py
```
## 📡 API Overview

### Key Endpoints

| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| **Users** | `/users/register` | POST | Register new user |
| | `/users/login` | POST | Login and get token |
| | `/users/me` | GET | Get current user info |
| | `/users/bio` | POST/GET/DELETE | Manage self-introduction |
| **Question Banks** | `/question_banks` | GET/POST | List/create question banks |
| | `/upload` | POST | Bulk import questions |
| **Blogs** | `/blogs` | GET/POST | List/create blog posts |
| | `/blogs/{id}` | GET/PUT/DELETE | Manage blog post |
| | `/blogs/tags` | GET/POST | List/create tags |
| | `/blogs/{id}/like` | POST | Like/unlike blog |
| | `/blogs/{id}/comments` | GET/POST | List/add comments |
| **Feedback** | `/api/feedback` | GET/POST | Submit/view feedback |

---

## 📚 Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Code organization and file purposes |
| [Database Schema](docs/DATABASE_SCHEMA.md) | ER diagrams and table relationships |
| [API Usage](docs/API_USAGE.md) | Detailed API examples |

### Feature Documentation

| Feature | Documentation |
|---------|---------------|
| **Blog System** | [Blog API](docs/BLOG_API.md) • [Tags](docs/BLOG_TAGS_API.md) • [File Storage](docs/BLOG_FILE_STORAGE.md) |
| **User Bio** | [Bio File API](docs/BIO_FILE_API.md) |

### Deployment Documentation

| Document | Description |
|----------|-------------|
| [Docker Setup](docs/DOCKER_DB_INIT.md) | Database auto-initialization |
| [Docker Verification](docs/DOCKER_FINAL_VERIFICATION.md) | Configuration checklist |

### Technical Documentation

| Document | Description |
|----------|-------------|
| [Transaction Fix](docs/TRANSACTION_COMMIT_FIX.md) | Database transaction handling |

---



---

<div align="center">

**Made with ❤️ by the YanZhuShou Team**

[Documentation](docs/) • [API Docs](http://localhost:8000/docs) • [Docker Guide](docs/DOCKER.md)

</div>
