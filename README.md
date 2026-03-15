# 📚 YanZhuShou - Question Bank Management System

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A powerful RESTful API for managing educational question banks with bulk import capabilities**

[Quick Start](#-quick-start) • [Docker Deployment](#-docker-deployment) • [API Docs](#-api-access) • [Documentation](#-documentation)

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

- **Docker** 20.10+ and **Docker Compose** 2.0+ (Recommended)
- OR **Python 3.12+** and **PostgreSQL 16+** (Local development)

---

## 🐳 Docker Deployment (Recommended)

### 1️⃣ Clone and Configure

```bash
git clone https://github.com/yourusername/YanZhuShou.git
cd YanZhuShou/Server
cp .env.example .env
```

### 2️⃣ Build and Start

```bash
# Build Docker images
docker-compose build

# Start all services (PostgreSQL, Redis, FastAPI)
docker-compose up -d
```

### 3️⃣ Initialize Database

```bash
docker-compose exec app python db_scripts/init_db.py
```

### 4️⃣ Verify & Access

```bash
# Check service status
docker-compose ps

# View application logs
docker-compose logs -f app
```

**Access the API:**
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000

---

### Using Make (Optional)

If you have `make` installed, use these convenient commands:

```bash
make build      # Build images
make up         # Start services
make db-init    # Initialize database
make logs       # View logs
make down       # Stop services
make help       # Show all commands
```

---

## 💻 Local Development (Without Docker)

### 1️⃣ Set Up Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Start PostgreSQL

```bash
# Using Docker (recommended for local dev)
docker-compose up -d postgres redis

# OR install PostgreSQL locally and start the service
```

### 3️⃣ Configure Environment

Edit `.env` file with local settings:

```env
DATABASE_URL=postgresql+asyncpg://api:api@localhost:5432/fastapi_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-development-secret-key
```

### 4️⃣ Initialize Database

```bash
python db_scripts/init_db.py
```

### 5️⃣ Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Access

### Interactive Documentation

Once running, access the auto-generated API docs:

| Documentation | URL |
|--------------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

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

---

## 📚 Documentation

| Topic | Description |
|-------|-------------|
| [🐳 Docker Guide](DOCKER.md) | Complete Docker deployment instructions |
| [📁 Project Structure](docs/PROJECT_STRUCTURE.md) | Code organization and file purposes |
| [🗄️ Database Schema](docs/DATABASE_SCHEMA.md) | ER diagrams and table descriptions |
| [📡 API Usage](docs/API_USAGE.md) | API endpoints with examples |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI |
| **Database** | PostgreSQL 16 |
| **ORM** | SQLAlchemy (Async) |
| **Cache** | Redis |
| **Auth** | JWT (python-jose) + bcrypt |
| **Container** | Docker + Docker Compose |

---

## ⚙️ Configuration

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://api:api@postgres:5432/fastapi_db` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT signing key | **⚠️ Change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |

### Generate Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🧪 Testing

```bash
# Run tests (in Docker container)
docker-compose exec app python -m pytest test_api/ -v

# Or locally (with server running)
python test_api/test_user.py
python test_api/test_question_apis.py
```

---

## 🧹 Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Application only
docker-compose logs -f app

# Database only
docker-compose logs -f postgres
```

### Stop Services

```bash
docker-compose down
```

### Clean Everything (⚠️ Destroys Data)

```bash
docker-compose down -v --rmi local --remove-orphans
```

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

[Documentation](docs/PROJECT_STRUCTURE.md) • [API Docs](http://localhost:8000/docs) • [Docker Guide](DOCKER.md)

</div>
