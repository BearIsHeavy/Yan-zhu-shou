# ==============================================================================
# YanZhuShou Docker Makefile
# Common Docker commands for development and production
# ==============================================================================

.PHONY: help build up down restart logs shell db-init db-reset clean

# Default target
help:
	@echo "YanZhuShou Docker Commands"
	@echo "=========================="
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build       Build Docker images"
	@echo "  up          Start all services (detached)"
	@echo "  up-dev      Start all services (foreground, for debugging)"
	@echo "  down        Stop and remove all containers"
	@echo "  restart     Restart all services"
	@echo "  logs        View logs (follow mode)"
	@echo "  logs-app    View only application logs"
	@echo "  logs-db     View only database logs"
	@echo "  shell       Open shell in application container"
	@echo "  db-init     Manually initialize database tables"
	@echo "  db-reset    Drop and recreate all database tables (WARNING: destroys data)"
	@echo "  clean       Remove containers, images, and volumes"
	@echo "  test        Run tests in container"
	@echo ""

# Build Docker images
build:
	docker-compose build

# Start all services in detached mode
up:
	docker-compose up -d

# Start all services in foreground (for debugging)
up-dev:
	docker-compose up

# Stop and remove all containers
down:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View logs from all services
logs:
	docker-compose logs -f

# View only application logs
logs-app:
	docker-compose logs -f app

# View only database logs
logs-db:
	docker-compose logs -f postgres

# View only Redis logs
logs-redis:
	docker-compose logs -f redis

# Open shell in application container
shell:
	docker-compose exec app /bin/bash

# Initialize database tables (manual)
db-init:
	docker-compose exec -T app python db_scripts/init_db.py

# Reset database (WARNING: destroys all data)
db-reset:
	@echo "WARNING: This will destroy all database content!"
	@echo "Type 'yes' to confirm:"
	@read confirm && [ "$$confirm" = "yes" ] && \
	docker-compose exec app python db_scripts/clear_database.py && \
	docker-compose exec app python db_scripts/init_db.py || \
	echo "Cancelled"

# Run tests
test:
	docker-compose exec app python -m pytest test_api/ -v

# Remove containers, networks, and volumes
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --rmi local --remove-orphans
	docker-compose rm -f
	@echo "Cleanup complete!"

# Production build (optimized)
build-prod:
	docker-compose -f docker-compose.yml build --no-cache

# Scale application workers (if needed)
scale:
	docker-compose up -d --scale app=3

# Health check
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Application: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
