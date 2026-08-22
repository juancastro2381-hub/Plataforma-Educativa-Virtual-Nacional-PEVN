# ============================================================
# PEVN Backend — Dockerfile
# ============================================================
# Multi-stage build:
#   Stage 1 (builder): Install dependencies with build tools
#   Stage 2 (final):   Minimal runtime image, non-root user
#
# Production usage:
#   docker build -t pevn-backend .
#   docker run -p 8000:8000 --env-file .env pevn-backend
#
# Development (via docker-compose):
#   Source is mounted as a volume, --reload is added by compose override
# ============================================================

# ---- Stage 1: Build -------------------------------------------------------
FROM python:3.12.8-slim AS builder

WORKDIR /build

# Install build-time system dependencies
# (build-essential needed for some Python packages with C extensions)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer cache optimization
COPY requirements/production.txt requirements/production.txt

# Install Python dependencies to a prefix directory
RUN pip install --no-cache-dir --prefix=/install -r requirements/production.txt


# ---- Stage 2: Final runtime image -----------------------------------------
FROM python:3.12.8-slim AS final

# Security: Install only minimal runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Security: Create a dedicated non-root user for the application
# The application must never run as root.
RUN groupadd --gid 1001 pevn \
    && useradd \
        --uid 1001 \
        --gid pevn \
        --no-create-home \
        --shell /usr/sbin/nologin \
        pevn

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .
COPY pyproject.toml .

# Set ownership to the non-root user
RUN chown -R pevn:pevn /app

# Switch to non-root user
USER pevn

# Expose the application port
EXPOSE 8000

# Container health check
# Calls the /health endpoint — does not require DB connectivity (liveness only)
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=10s \
    --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command: production uvicorn server
# For development, docker-compose overrides this with --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
