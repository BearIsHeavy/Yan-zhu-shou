# 📚 YanZhuShou - Question Bank Management System

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-3776AB?style=for-the-badge&logo=sqlalchemy&logoColor=white)

**A powerful RESTful API for managing educational question banks with bulk import capabilities**

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [Database Schema](#-database-schema) • [Testing](#-testing)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Testing](#-testing)
- [Configuration](#-configuration)
- [Contributing](#-contributing)

---

## 🎯 Overview

**YanZhuShou** is a comprehensive Question Bank Management System built with FastAPI and PostgreSQL. It provides educators and institutions with a robust platform to create, organize, and manage educational question banks with support for multiple question types and bulk import capabilities.

### Key Use Cases
- 📝 Create and manage question banks for different subjects
- 📤 Bulk import questions via CSV or XML files
- ✏️ Add individual questions manually
- 🔐 Secure user authentication with JWT tokens
- 📊 Track question statistics (correct/incorrect attempts)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **User Authentication** | Secure JWT-based authentication with password hashing |
| 📚 **Question Banks** | Create and manage multiple question banks (books) |
| 📤 **CSV Import** | Bulk upload questions from CSV files |
| 📄 **XML Import** | Bulk upload questions from XML files |
| ✏️ **Single Upload** | Add questions one at a time via API |
| 🎨 **Multiple Question Types** | Support for Essay, Single-choice, Multiple-choice, and Fill-in questions |
| 📝 **Rich Content** | Store full question text, answers, and explanations |
| 🖼️ **Image Support** | Attach images to questions via URL |
| 📊 **Statistics Tracking** | Track correct and incorrect answer counts |
| 🔒 **Data Isolation** | Users can only access their own question banks |

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- **Database**: [PostgreSQL](https://www.postgresql.org/) - Relational database
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- **Async**: [asyncpg](https://magicstack.github.io/asyncpg/) - Fast PostgreSQL driver
- **Validation**: [Pydantic](https://docs.pydantic.dev/) - Data validation

### Authentication
- **JWT**: [python-jose](https://python-jose.readthedocs.io/) - JWT handling
- **Password**: [passlib](https://passlib.readthedocs.io/) - Password hashing with bcrypt

### Infrastructure
- **Server**: [Uvicorn](https://www.uvicorn.org/) - ASGI server
- **Container**: Docker & Docker Compose
- **Environment**: python-dotenv for configuration

---

## 📁 Project Structure

```
YanZhuShou/
├── 📂 models/                 # Database models
│   ├── __init__.py
│   ├── user.py               # User model
│   ├── question.py           # QuestionBank, QBQuestion, StemText, AnswerText models
│   └── log.py                # SecurityLog model
├── 📂 routes/                 # API endpoints
│   ├── __init__.py
│   ├── auth.py               # Authentication utilities
│   ├── users.py              # User registration, login endpoints
│   ├── question_banks.py     # Question bank CRUD endpoints
│   ├── questions.py          # Question upload endpoints (CSV/XML/Single)
│   └── security_logs.py      # Security logging endpoints
├── 📂 schemas/                # Pydantic models
│   ├── __init__.py
│   ├── user.py               # User schemas
│   ├── question.py           # Question bank & question schemas
│   ├── token.py              # Token schemas
│   └── text.py               # StemText & AnswerText schemas
├── 📂 test_api/               # API test scripts
│   ├── test_user.py          # User API tests
│   └── test_question_apis.py # Question API tests
├── 📂 db_scripts/             # Database scripts
│   ├── init_db.py            # Database initialization
│   └── clear_database.py     # Database cleanup
├── 📂 docs/                   # Documentation
│   └── API_USAGE.md          # API usage guide
├── database.py                # Database configuration
├── dependencies.py            # Dependency injection
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker configuration
├── .env                       # Environment variables
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker (optional, for containerized deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/YanZhuShou.git
cd YanZhuShou
```

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://api:api@localhost:5432/fastapi_db
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Start PostgreSQL (Docker)

```bash
docker-compose up -d postgres
```

### 6. Initialize Database

```bash
python db_scripts/init_db.py
```

### 7. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Access the API

- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 📡 API Documentation

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Database

    Client->>API: POST /users/register
    API->>Database: Create user
    Database-->>API: User created
    API-->>Client: User data

    Client->>API: POST /users/login
    API->>Database: Verify credentials
    Database-->>API: User found
    API->>API: Generate JWT token
    API-->>Client: Access token

    Client->>API: POST /question_banks/book (with token)
    API->>API: Validate token
    API->>Database: Create question bank
    Database-->>API: Bank created
    API-->>Client: Question bank data
```

### Endpoints Overview

#### 🔐 Authentication & Users

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/users/register` | Register new user | ❌ |
| POST | `/users/login` | Login and get token | ❌ |
| GET | `/users/me` | Get current user info | ✅ |
| PUT | `/users/me` | Update current user | ✅ |

#### 📚 Question Banks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/question_banks/book` | Create new question bank | ✅ |

#### 📤 Question Upload

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/upload/csv` | Bulk import from CSV | ✅ |
| POST | `/upload/xml` | Bulk import from XML | ✅ |
| POST | `/upload/question` | Upload single question | ✅ |

### Example Requests

#### Register a User

```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teacher@example.com",
    "name": "John Teacher",
    "password": "securepass123",
    "phone": "13800138000",
    "gender": 1
  }'
```

#### Login

```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher@example.com&password=securepass123"
```

#### Create Question Bank

```bash
curl -X POST "http://localhost:8000/question_banks/book" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mathematics 101",
    "is_public": false,
    "description": "Basic mathematics questions"
  }'
```

#### Upload CSV

```bash
curl -X POST "http://localhost:8000/upload/csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "bank_id=1" \
  -F "file=@questions.csv"
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ QuestionBank : owns
    User ||--o{ SecurityLog : generates
    QuestionBank ||--o{ QBQuestion : contains
    QBQuestion ||--|| StemText : has
    QBQuestion ||--|| AnswerText : has

    User {
        int user_id PK
        string email UK
        string name
        string hash_password
        string phone UK
        int gender
        datetime created_at
    }

    QuestionBank {
        int bank_id PK
        string name
        int user_id FK
        bool is_public
        text description
        datetime created_at
    }

    QBQuestion {
        int No PK
        int bank_id FK
        string category
        string stem
        int qus_type
        string options
        string correct_ans_summary
        int correct_num
        int uncorrect_num
        bool is_public
        int user_id FK
        datetime created_at
    }

    StemText {
        int id PK
        int question_no FK
        text full_text
        string image_url
    }

    AnswerText {
        int id PK
        int question_no FK
        text full_answer
        text explanation
    }

    SecurityLog {
        int log_id PK
        int user_id FK
        string action
        datetime timestamp
        string details
    }
```

### Table Descriptions

#### `User`
Stores user account information including authentication credentials.

#### `QuestionBank`
Represents a collection of questions (like a textbook or course).

#### `QBQuestion`
Individual questions within a question bank with metadata.

#### `StemText`
Extended question content including full text and images.

#### `AnswerText`
Correct answers and explanations for questions.

#### `SecurityLog`
Audit trail of user actions for security monitoring.

---

## 🧪 Testing

### Run All Tests

```bash
# Start the server first
uvicorn main:app --reload &

# Run user API tests
python test_api/test_user.py

# Run question API tests
python test_api/test_question_apis.py
```

### Test Coverage

The test suite covers:
- ✅ User registration and login
- ✅ Question bank creation
- ✅ CSV file upload and parsing
- ✅ XML file upload and parsing
- ✅ Single question upload
- ✅ Authentication validation
- ✅ Authorization (access control)
- ✅ Error handling

### Sample Test Output

```
############################################################
# Starting Question Bank API Tests
# Base URL: http://127.0.0.1:8000
############################################################

============================================================
SETUP: Register and Login
============================================================
✓ Logged in successfully. Token: eyJhbGciOiJIUzI1NiIs...

============================================================
TEST: POST /question_banks/book - Create question bank
============================================================
✓ Question bank created with ID: 8

============================================================
TEST: POST /upload/csv - Upload CSV file
============================================================
✓ CSV upload successful. 3 questions added.

============================================================
ALL TESTS PASSED ✓✓✓
============================================================
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://api:api@localhost:5432/fastapi_db` |
| `SECRET_KEY` | JWT signing secret | `your-secret-key-change-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |

### Docker Configuration

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: api
      POSTGRES_PASSWORD: api
      POSTGRES_DB: fastapi_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for public functions
- Add tests for new features

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

For issues and questions:
- 🐛 Report bugs via GitHub Issues
- 💬 Ask questions via GitHub Discussions
- 📧 Contact: support@example.com

---

<div align="center">

**Made with ❤️ by the YanZhuShou Team**

![Stars](https://img.shields.io/github/stars/yourusername/YanZhuShou?style=social)
![Forks](https://img.shields.io/github/forks/yourusername/YanZhuShou?style=social)

</div>
