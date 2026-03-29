# Multi-stage Dockerfile for YanZhuShou FastAPI Application
# Optimized for production: small image size, security, and caching
# Uses Chinese mirror for faster package downloads in China

# ==============================================================================
# Stage 1: Build dependencies
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Configure pip to use Chinese mirror (Aliyun)
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv with Chinese mirror
RUN uv pip install --system --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r pyproject.toml

# ==============================================================================
# Stage 2: Runtime image
# ==============================================================================
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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
