# Multi-stage Dockerfile for YanZhuShou FastAPI Application
# Optimized for production: small image size, security, and caching

# ==============================================================================
# Stage 1: Build dependencies
# ==============================================================================
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Runtime image
# ==============================================================================
FROM python:3.12-slim as runtime

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create uploads directory for user-generated content (blogs, bios)
RUN mkdir -p /app/uploads/blogs /app/uploads/bios && \
    chown -R appuser:appgroup /app/uploads

# Copy application code
COPY --chown=appuser:appgroup . .

# Copy and setup entrypoint script
COPY --chown=appuser:appgroup docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check endpoint (FastAPI auto-generates /docs, but we check root)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

# Set entrypoint and run the application with uvicorn in production mode
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
