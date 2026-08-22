# PEVN Operations Guide

**Plataforma Educativa Virtual Nacional**  
**Phase:** 1 — Foundation  
**Last Updated:** 2026-08-21

---

## 1. Service Management

### 1.1 Start All Services

```bash
# Start in background
docker compose up -d

# Start and follow logs
docker compose up

# Start specific service
docker compose up -d backend
```

### 1.2 Stop Services

```bash
# Stop without removing containers
docker compose stop

# Stop and remove containers (keeps volumes)
docker compose down

# Stop and remove everything including volumes (DESTROYS DATA)
docker compose down -v
```

### 1.3 View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f db
docker compose logs -f redis

# Last N lines
docker compose logs --tail=100 backend
```

### 1.4 Service Status

```bash
docker compose ps
```

---

## 2. Health Monitoring

### 2.1 Application Health

```bash
# Check backend liveness
curl http://localhost:8000/api/v1/health

# Check backend readiness (all dependencies)
curl http://localhost:8000/api/v1/ready
```

Expected responses:

**Health (liveness):**
```json
{"status": "ok", "service": "pevn-backend"}
```

**Ready (all services up):**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**Not ready (dependency down):**
```json
{
  "status": "not_ready",
  "checks": {
    "database": "error",
    "redis": "ok"
  }
}
```

### 2.2 Database Health

```bash
# Check PostgreSQL from host
pg_isready -h localhost -p 5432 -U pevn_admin -d pevn_db

# Check from inside container
docker compose exec db pg_isready -U pevn_admin -d pevn_db
```

### 2.3 Redis Health

```bash
# Check Redis from host
redis-cli -h localhost ping

# Check from inside container
docker compose exec redis redis-cli ping
```

---

## 3. Database Operations

### 3.1 Connect to Database

```bash
# Admin user (for migrations and schema management)
docker compose exec db psql -U pevn_admin -d pevn_db

# Application user (for application-level queries)
docker compose exec db psql -U pevn_app -d pevn_db
```

### 3.2 Run Migrations

```bash
# Apply pending migrations
docker compose exec backend alembic upgrade head

# Check current migration version
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Downgrade one migration
docker compose exec backend alembic downgrade -1
```

### 3.3 Backup and Restore (Development)

```bash
# Backup
docker compose exec db pg_dump -U pevn_admin pevn_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
cat backup_YYYYMMDD_HHMMSS.sql | docker compose exec -T db psql -U pevn_admin -d pevn_db
```

> **Production backup:** Must use automated, encrypted, off-site backup solution. See docs/DEPLOYMENT.md for production guidance.

---

## 4. Common Operations

### 4.1 Restart a Service

```bash
docker compose restart backend
docker compose restart frontend
```

### 4.2 Rebuild a Service (after code changes)

```bash
# Rebuild and restart
docker compose up -d --build backend

# Rebuild frontend
docker compose up -d --build frontend
```

### 4.3 Open a Shell in a Container

```bash
# Backend
docker compose exec backend bash

# Database
docker compose exec db bash

# Redis
docker compose exec redis sh
```

### 4.4 View Container Resource Usage

```bash
docker stats
```

---

## 5. Troubleshooting

### 5.1 Backend Won't Start

**Symptoms:** Container exits immediately or health check fails.

**Checklist:**
1. Check environment variables: `docker compose exec backend env | grep DATABASE_URL`
2. Check logs: `docker compose logs backend`
3. Verify database is healthy: `docker compose ps db`
4. Test database connectivity: `curl http://localhost:8000/api/v1/ready`
5. Run migrations: `docker compose exec backend alembic upgrade head`

### 5.2 Database Connection Errors

**Symptoms:** Readiness check shows `database: error`.

**Checklist:**
1. Verify PostgreSQL is running: `docker compose ps db`
2. Check if PostgreSQL initialized correctly: `docker compose logs db`
3. Verify `DATABASE_URL` in `.env` uses the `pevn_app` user and correct password
4. Test direct connection: `docker compose exec db psql -U pevn_app -d pevn_db -c "SELECT 1"`

### 5.3 Frontend Won't Load

**Symptoms:** `http://localhost:3000` shows error or blank page.

**Checklist:**
1. Check frontend logs: `docker compose logs frontend`
2. Verify Node dependencies: `docker compose exec frontend npm list`
3. Check if `VITE_API_BASE_URL` is correct in `.env`

### 5.4 Migration Errors

**Symptoms:** `alembic upgrade head` fails.

**Checklist:**
1. Verify database connectivity first
2. Check `pevn_admin` user has schema modification rights
3. Check `alembic current` to see current state
4. Review migration file for syntax errors

---

## 6. Logging

### 6.1 Log Format

**Development (console format):**
Human-readable colored output for local development.

**Production (JSON format):**
Machine-readable JSON for log aggregation (ELK, Cloud Logging, etc.):
```json
{
  "event": "Request completed",
  "level": "info",
  "timestamp": "2026-08-21T20:00:00Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/v1/health",
  "status_code": 200,
  "duration_ms": 2.3
}
```

### 6.2 Setting Log Level

```bash
# In .env
LOG_LEVEL=DEBUG    # Most verbose
LOG_LEVEL=INFO     # Default
LOG_LEVEL=WARNING  # Warnings and above
LOG_LEVEL=ERROR    # Errors only
```

### 6.3 Sensitive Information Policy

Logs must NEVER contain:
- Passwords or credentials
- JWT tokens or session identifiers
- Authorization header values
- Database connection strings with passwords
- Personal identification data (cédulas, etc.) unless strictly necessary

This policy is enforced by the logging sanitization processor.
