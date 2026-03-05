#!/bin/bash

# =============================================================================
# PostgreSQL Database Reset Script
# This script stops containers, removes old data, and reinitializes the database
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
POSTGRES_CONTAINER="backend_postgres"
POSTGRES_USER="api"
POSTGRES_PASSWORD="api"
POSTGRES_DB="fastapi_db"

echo -e "${YELLOW}=== PostgreSQL Database Reset Script ===${NC}"
echo ""

# Step 1: Stop running containers
echo -e "${YELLOW}[1/5] Stopping containers...${NC}"
docker compose -f "$COMPOSE_FILE" stop postgres 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 2: Remove old PostgreSQL volume data
echo -e "${YELLOW}[2/5] Removing old PostgreSQL data volume...${NC}"
docker compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
echo -e "${GREEN}✓ Old data removed${NC}"
echo ""

# Step 3: Start fresh PostgreSQL container
echo -e "${YELLOW}[3/5] Starting fresh PostgreSQL container...${NC}"
docker compose -f "$COMPOSE_FILE" up -d postgres
echo -e "${GREEN}✓ PostgreSQL container started${NC}"
echo ""

# Step 4: Wait for PostgreSQL to be ready
echo -e "${YELLOW}[4/5] Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Check if PostgreSQL is ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Waiting... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}✗ PostgreSQL failed to start${NC}"
    exit 1
fi
echo ""

# Step 5: Create tables using SQLAlchemy
echo -e "${YELLOW}[5/5] Creating database tables...${NC}"

# Activate virtual environment and run table creation
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    source ../.venv/bin/activate
fi

# Create a temporary Python script to initialize tables
cat << 'PYTHON_SCRIPT' > /tmp/init_db.py
import asyncio
from database import engine, Base
from models import User, QuestionBank, QBQuestion, StemText, AnswerText, UserQuestionLog, SecurityLog

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

asyncio.run(init_db())
PYTHON_SCRIPT

python ./init_db.py
rm ./init_db.py

echo -e "${GREEN}✓ Database tables created${NC}"
echo ""

# Summary
echo -e "${GREEN}=== Database Reset Complete ===${NC}"
echo ""
echo "PostgreSQL Connection Details:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  User:     $POSTGRES_USER"
echo "  Password: $POSTGRES_PASSWORD"
echo "  Database: $POSTGRES_DB"
echo ""
echo -e "${GREEN}Ready to use!${NC}"
