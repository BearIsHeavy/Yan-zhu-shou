# 🐳 Docker Deployment Guide

Complete guide for deploying YanZhuShou with Docker.

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)

## 🚀 Quick Start

### Option 1: Using Make (Recommended)

```bash
# Build and start all services
make build
make up

# Initialize database
make db-init

# View logs
make logs

# Stop services
make down
```

### Option 2: Using Docker Compose Directly

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec app python db_scripts/init_db.py

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                           │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   FastAPI    │───▶│  PostgreSQL  │  │     Redis    │  │
│  │   App:8000   │    │  :5432       │  │   :6379      │  │
│  └──────┬───────┘    └──────────────┘  └──────────────┘  │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
    Host:8000
```

## 📦 Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| `app` | `yanzhushou_app` | 8000 | FastAPI application |
| `postgres` | `yanzhushou_postgres` | 5432 | PostgreSQL database |
| `redis` | `yanzhushou_redis` | 6379 | Redis cache |

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://api:api@postgres:5432/fastapi_db` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT signing key | **CHANGE IN PRODUCTION** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |

### Generate Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🛠️ Common Operations

### Build Images

```bash
# Standard build
make build

# Production build (no cache)
make build-prod
```

### Start/Stop Services

```bash
# Start (detached)
make up

# Start (foreground, for debugging)
make up-dev

# Stop
make down

# Restart
make restart
```

### View Logs

```bash
# All services
make logs

# Application only
make logs-app

# Database only
make logs-db
```

### Database Operations

```bash
# Initialize database
make db-init

# Reset database (WARNING: destroys data)
make db-reset

# Run migrations (if any)
docker-compose exec app python db_scripts/init_db.py
```

### Access Container

```bash
# Open shell in app container
make shell

# Run Python commands
docker-compose exec app python
```

### Health Check

```bash
# Check service status
make health

# Manual check
curl http://localhost:8000/docs
```

## 🧪 Testing

```bash
# Run tests in container
make test

# Or directly
docker-compose exec app python -m pytest test_api/ -v
```

## 🧹 Cleanup

```bash
# Remove containers, networks, volumes
make clean

# Or manually
docker-compose down -v --rmi local --remove-orphans
```

## 🔐 Security Best Practices

1. **Change SECRET_KEY**: Generate a new key for production
2. **Use .env file**: Never commit secrets to version control
3. **Non-root user**: Application runs as non-root user inside container
4. **Health checks**: All services have health checks configured
5. **Network isolation**: Services communicate via internal network

## 📊 Production Considerations

### Scaling

```bash
# Scale application workers
make scale

# Or manually
docker-compose up -d --scale app=3
```

### Persistent Storage

Data is persisted in Docker volumes:

- `postgres_data`: PostgreSQL database
- `redis_data`: Redis cache

### Monitoring

Check service health:

```bash
docker-compose ps
```

View resource usage:

```bash
docker stats yanzhushou_app yanzhushou_postgres yanzhushou_redis
```

## 🐛 Troubleshooting

### Application won't start

```bash
# Check logs
make logs-app

# Verify database is ready
docker-compose exec postgres pg_isready -U api -d fastapi_db

# Verify Redis is ready
docker-compose exec redis redis-cli ping
```

### Database connection errors

1. Ensure PostgreSQL is healthy: `docker-compose ps postgres`
2. Check DATABASE_URL in `.env`
3. Verify network connectivity: `docker-compose exec app ping postgres`

### Port conflicts

If port 8000/5432/6379 is already in use:

1. Edit `docker-compose.yml` and change the port mapping
2. Or stop the conflicting service

### Rebuild after code changes

```bash
# If using volume mount (development)
docker-compose restart app

# If not using volume mount (production)
make build
make up
```

## 📝 Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Build Docker images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart services |
| `make logs` | View all logs |
| `make logs-app` | View app logs |
| `make shell` | Open shell in app container |
| `make db-init` | Initialize database |
| `make db-reset` | Reset database |
| `make test` | Run tests |
| `make clean` | Clean up resources |
| `make health` | Check service health |

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)

## 🆘 Support

For issues:
1. Check logs: `make logs`
2. Verify health: `make health`
3. Review `.env` configuration
4. Ensure Docker daemon is running
