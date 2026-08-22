# PEVN Deployment Guide

**Plataforma Educativa Virtual Nacional**  
**Phase:** 1 — Foundation  
**Last Updated:** 2026-08-21

---

> [!CAUTION]
> **Phase 1 is NOT ready for public internet exposure.**
> The application has NO authentication in Phase 1.
> Only deploy Phase 1 in isolated development/staging environments.
> Phase 2 must be complete before any public deployment.

---

## 1. Local Development Environment

### 1.1 Prerequisites

- Docker Desktop >= 4.0
- Docker Compose >= 2.0
- Git
- (Optional) Python 3.12 for running backend locally without Docker
- (Optional) Node.js 20 for running frontend locally without Docker

### 1.2 Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd pevn

# 2. Copy environment configuration
cp .env.example .env

# 3. Edit .env — replace ALL placeholder values
# See .env.example for documentation of each variable
nano .env

# 4. (Optional) Validate environment configuration
chmod +x infrastructure/scripts/check_env.sh
./infrastructure/scripts/check_env.sh

# 5. Start all services
docker compose up -d

# 6. Check service health
docker compose ps
docker compose logs -f

# 7. Run database migrations
docker compose exec backend alembic upgrade head
```

### 1.3 Service URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Backend OpenAPI Docs | http://localhost:8000/docs |
| Backend Redoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/health |
| Readiness Check | http://localhost:8000/api/v1/ready |

### 1.4 Running Without Docker (Backend)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements/development.txt

# Set environment variables (or create .env in backend/)
export ENVIRONMENT=development
export DATABASE_URL=postgresql+asyncpg://pevn_app:password@localhost:5432/pevn_db
export REDIS_URL=redis://localhost:6379/0
# ... (other required variables)

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.5 Running Without Docker (Frontend)

```bash
cd frontend

# Install dependencies
npm install

# Copy and edit environment
cp .env.example .env.local

# Start development server
npm run dev
```

---

## 2. Running Tests

### 2.1 Backend Tests

```bash
cd backend
pip install -r requirements/development.txt

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests (no DB required)
pytest -m "not integration" -v

# Run specific test file
pytest tests/test_health.py -v
```

### 2.2 Frontend Tests

```bash
cd frontend
npm install

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### 2.3 Database Migrations

```bash
# Apply migrations
docker compose exec backend alembic upgrade head

# Check current state
docker compose exec backend alembic current

# Create new migration (after adding models)
docker compose exec backend alembic revision --autogenerate -m "add_users_table"
```

---

## 3. Production Deployment (Phase 2+ Only)

> **These instructions will be expanded in Phase 2.**
> Production deployment requires authentication to be implemented first.

### 3.1 Production Checklist (Reference)

- [ ] Authentication implemented (Phase 2)
- [ ] All environment variables set via secret management system
- [ ] `ENVIRONMENT=production` 
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` set to actual production domain
- [ ] `ALLOWED_HOSTS` set to actual production domain
- [ ] `LOG_FORMAT=json` for log aggregation
- [ ] TLS termination configured at reverse proxy
- [ ] PostgreSQL SSL mode enabled
- [ ] Database running on private network (not public internet)
- [ ] Redis running on private network with authentication
- [ ] Docker images built from pinned dependencies
- [ ] Health and readiness checks verified
- [ ] Database migrations applied
- [ ] Backup procedures tested

### 3.2 Production Architecture Target

```
[Internet]
    │
[WAF / DDoS Protection]
    │
[Load Balancer / Reverse Proxy (nginx/caddy)]
    │            │
[Backend ×N]  [Frontend (static CDN)]
    │
[PostgreSQL (primary + read replica)]
[Redis Cluster]
```

---

## 4. Environment Variables Reference

See `.env.example` for the complete reference with documentation for every variable.

**Required variables:**
- `ENVIRONMENT` — Runtime environment
- `SECRET_KEY` — Cryptographic secret (generate with `python -c "import secrets; print(secrets.token_hex(64))"`)
- `DATABASE_URL` — PostgreSQL connection string
- `POSTGRES_*` — Database credentials for Docker
- `REDIS_URL` — Redis connection URL
- `CORS_ORIGINS` — Allowed browser origins
- `ALLOWED_HOSTS` — Allowed Host header values
