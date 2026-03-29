# Docker Database Auto-Initialization

## Overview

The Docker configuration now includes automatic database initialization. When you start the services, the database tables will be created automatically before the application starts.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                           │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │ db-init  │───▶│ postgres │    │   redis  │    │  app  │ │
│  │ (init)   │    │  :5432   │    │  :6379   │    │ :8000 │ │
│  └────┬─────┘    └──────────┘    └──────────┘    └───┬───┘ │
│       │                                               │     │
│       └───────────────────┬───────────────────────────┘     │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                     Waits for completion
```

## Services

| Service | Purpose | Runs When |
|---------|---------|-----------|
| `db-init` | Database initialization | Once, before app starts |
| `app` | FastAPI application | After db-init completes |
| `postgres` | PostgreSQL database | Always |
| `redis` | Redis cache | Always |

## Startup Sequence

1. **PostgreSQL** starts and becomes healthy
2. **Redis** starts and becomes healthy
3. **db-init** runs `init_db.py` to create tables
4. **app** starts after db-init completes successfully

## Usage

### Start Services (Auto-Initialize Database)

```bash
# Build and start all services
docker-compose build
docker-compose up -d

# Or using make
make build
make up
```

### View Initialization Logs

```bash
# View database initialization logs
docker-compose logs db-init

# Or using make
make logs-db-init

# Follow application logs
docker-compose logs -f app

# Or using make
make logs-app
```

### Expected Output

```
# db-init service logs
📦 Initializing database...
2026-03-29 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2026-03-29 INFO sqlalchemy.engine.Engine CREATE TABLE blogs (...)
2026-03-29 INFO sqlalchemy.engine.Engine CREATE TABLE blog_tags ...
Tables created successfully!
✅ Database initialized successfully

# app service logs
🚀 Starting YanZhuShou Application...
⏳ Waiting for PostgreSQL...
✅ PostgreSQL is ready
⏳ Waiting for Redis...
✅ Redis is ready
✅ All dependencies ready
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Manual Database Initialization

If you need to manually re-initialize the database:

```bash
# Run db-init service manually
docker-compose run --rm db-init

# Or using make
make db-init
```

## Reset Database (WARNING: Destroys Data)

```bash
# Clear all tables and recreate
make db-reset

# Or manually
docker-compose exec app python db_scripts/clear_database.py
docker-compose run --rm db-init
```

## Troubleshooting

### db-init Fails

**Symptom**: db-init service exits with error

**Check logs**:
```bash
docker-compose logs db-init
```

**Common issues**:
1. PostgreSQL not ready - wait for health check
2. Connection error - check DATABASE_URL
3. Permission error - check PostgreSQL user credentials

### App Starts Before db-init Completes

**Symptom**: Application errors about missing tables

**Solution**: Check that app depends_on db-init with `service_completed_successfully`:

```yaml
app:
  depends_on:
    db-init:
      condition: service_completed_successfully
```

### Database Tables Missing

**Symptom**: API returns 500 errors about missing tables

**Solution**:
```bash
# Stop services
docker-compose down

# Remove volumes (optional, destroys data)
docker-compose down -v

# Rebuild and start
docker-compose build
docker-compose up -d

# Check initialization logs
docker-compose logs db-init
```

## Configuration

### Environment Variables

The db-init service uses the same environment variables as the app:

```yaml
db-init:
  environment:
    DATABASE_URL: postgresql+asyncpg://api:api@postgres:5432/fastapi_db
    REDIS_URL: redis://redis:6379/0
```

### Volumes

```yaml
db-init:
  volumes:
    - ./logs:/app/logs  # For initialization logs
```

## Production Considerations

1. **Run db-init once**: The service runs once per deployment
2. **Use migrations**: For schema changes, use migration scripts
3. **Backup first**: Always backup before running initialization
4. **Health checks**: App waits for db-init to complete

## Migration Strategy

For production deployments with existing data:

1. **Don't use db-init** for existing deployments
2. **Use migration scripts** in `db_scripts/migrations/`
3. **Run migrations manually**:
   ```bash
   docker-compose exec app python db_scripts/migrations/001_xxx.py
   ```

## Files Modified

| File | Change |
|------|--------|
| `docker-compose.yml` | Added db-init service |
| `docker-entrypoint.sh` | Removed db initialization (handled by db-init service) |
| `Makefile` | Added logs-db-init command, updated db-init command |
| `DOCKER.md` | Updated documentation |

## Benefits

1. ✅ **Automatic initialization** - No manual steps required
2. ✅ **Consistent state** - Database always initialized before app starts
3. ✅ **Clear logs** - Separate logs for initialization
4. ✅ **Failure handling** - App won't start if init fails
5. ✅ **Idempotent** - Safe to run multiple times (tables already exist)
