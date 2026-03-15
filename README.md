# 📚 YanZhuShou - Question Bank Management System

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

**A powerful RESTful API for managing educational question banks with bulk import capabilities**

[Quick Start](#-quick-start) • [API Docs](#-api-access) • [Documentation](#-documentation)

</div>

---

## 🎯 What is YanZhuShou?

YanZhuShou is a RESTful API service for managing educational question banks. Built with FastAPI and PostgreSQL, it enables educators to:

- 📚 Create and manage question banks
- 📤 Bulk import questions via CSV/XML
- ✏️ Add individual questions manually
- 🔐 Secure authentication with JWT
- 📊 Track question statistics

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 16+**

---

## 💻 Setup & Run

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/YanZhuShou.git
cd YanZhuShou/Server
```

### 2️⃣ Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Start PostgreSQL and Redis

```bash
# Option 1: Using Docker (quick setup)
docker run -d --name postgres -e POSTGRES_USER=api -e POSTGRES_PASSWORD=api \
  -e POSTGRES_DB=fastapi_db -p 5432:5432 postgres:16-alpine

docker run -d --name redis -p 6379:6379 redis:7.2-alpine
```

### 5️⃣ Configure Environment

The `.env` file is already configured with default settings:

```env
DATABASE_URL=postgresql+asyncpg://api:api@localhost:5432/fastapi_db
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379/0
```

**For production, update `SECRET_KEY`:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6️⃣ Initialize Database

```bash
python db_scripts/init_db.py
```

### 7️⃣ Run the Server

```bash
# Development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 8️⃣ Access the API

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000

---

## 📡 API Access

### Quick Test with cURL

```bash
# Register a new user
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123"
  }'

# Login and get token
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

### Using the Interactive Docs

Open http://localhost:8000/docs in your browser to:
- Explore all available endpoints
- Test API calls directly
- View request/response schemas

---

## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [📁 Project Structure](docs/PROJECT_STRUCTURE.md) | Code organization and file purposes |
| [🗄️ Database Schema](docs/DATABASE_SCHEMA.md) | ER diagrams and table descriptions |
| [📡 API Usage](docs/API_USAGE.md) | API endpoints with detailed examples |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI |
| **Database** | PostgreSQL 16 |
| **ORM** | SQLAlchemy (Async) |
| **Cache** | Redis |
| **Auth** | JWT (python-jose) + bcrypt |
| **Validation** | Pydantic v2 |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://api:api@localhost:5432/fastapi_db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key | **⚠️ Change in production** |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `REDIS_CACHE_TTL` | Cache TTL (seconds) | `300` |

### Redis (Optional)

Redis is used for caching user data. If Redis is not available, the application will continue to work without caching.

```bash
# Start Redis (optional)
docker run -d --name redis -p 6379:6379 redis:7.2-alpine
```

---

## 🧪 Testing

```bash
# Ensure server is running
uvicorn main:app --reload &

# Run user API tests
python test_api/test_user.py

# Run question API tests
python test_api/test_question_apis.py
```

---

## 🗄️ Database Scripts

| Script | Purpose |
|--------|---------|
| `db_scripts/init_db.py` | Create all database tables |
| `db_scripts/clear_database.py` | Drop all tables (development only) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

- 🐛 **Bug Reports**: GitHub Issues
- 💬 **Questions**: GitHub Discussions

---

<div align="center">

**Made with ❤️ by the YanZhuShou Team**

[Documentation](docs/PROJECT_STRUCTURE.md) • [API Docs](http://localhost:8000/docs) • [Database Schema](docs/DATABASE_SCHEMA.md)

</div>
