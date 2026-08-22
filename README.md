# Plataforma Educativa Virtual Nacional — PEVN

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-~0.115-009688?logo=fastapi)](backend/requirements/base.txt)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](frontend/package.json)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)](frontend/tsconfig.json)

> **Sistema educativo virtual para las instituciones educativas públicas de Colombia.**

---

## ⚠️ Phase 1 — Foundation

This repository contains **Phase 1** of the PEVN platform: the technical foundation.

Phase 1 establishes the infrastructure, security architecture, and development environment. **Authentication is NOT yet implemented.** This platform must not be exposed to the public internet until Phase 2 is complete.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design |
| [SECURITY.md](docs/SECURITY.md) | Security policy and controls |
| [DATABASE.md](docs/DATABASE.md) | Database design and migration guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Local development and deployment |
| [OPERATIONS.md](docs/OPERATIONS.md) | Service management and troubleshooting |
| [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) | Third-party dependency licenses |
| [ADR-001](docs/ADR/ADR-001-foundation-architecture.md) | Foundation architecture decisions |

---

## Quick Start

### Prerequisites
- Docker Desktop >= 4.0
- Docker Compose >= 2.0

### Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env — replace ALL placeholder values with real ones
# (See .env.example for documentation of each variable)

# 3. Start all services
docker compose up -d

# 4. Apply database migrations
docker compose exec backend alembic upgrade head

# 5. Verify services are healthy
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

**Service URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

## Project Structure

```
PEVN/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── audit/             # Audit service
│   │   ├── core/              # Config, logging, security
│   │   ├── db/                # Database session, models
│   │   ├── exceptions/        # Error hierarchy + handlers
│   │   ├── middleware/        # HTTP middleware stack
│   │   └── main.py            # Application factory
│   ├── migrations/            # Alembic migrations
│   ├── tests/                 # Pytest test suite
│   ├── requirements/          # Pinned dependencies
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── config/            # Environment configuration
│   │   ├── hooks/             # React hooks
│   │   ├── layouts/           # Page layouts
│   │   ├── pages/             # Route components
│   │   ├── services/          # API client
│   │   ├── styles/            # Global CSS + design system
│   │   ├── types/             # TypeScript types
│   │   └── utils/             # Utility functions
│   ├── Dockerfile
│   └── package.json
├── infrastructure/             # Infrastructure configuration
│   ├── docker/
│   │   └── postgres/          # DB initialization scripts
│   └── scripts/               # Operational scripts
├── docs/                       # Documentation
│   ├── ADR/                   # Architecture Decision Records
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   └── OPERATIONS.md
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI
├── docker-compose.yml
├── .env.example
├── .gitignore
└── LICENSE
```

---

## Development

### Backend

```bash
cd backend
pip install -r requirements/development.txt
pytest -v                       # Run tests
black .                         # Format code
ruff check .                    # Lint
mypy app/                       # Type check
```

### Frontend

```bash
cd frontend
npm install
npm test                        # Run tests
npm run lint                    # Lint
npm run format                  # Format
npm run typecheck               # Type check
```

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python + FastAPI | 3.12 / ~0.115 |
| ORM | SQLAlchemy (async) | ~2.0 |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Frontend | React + TypeScript | 18 / 5 |
| Build | Vite | 6 |
| Styling | Tailwind CSS | 3 |
| Containers | Docker + Compose | — |
| CI | GitHub Actions | — |

---

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the complete security policy.

**Key controls:**
- Security by Design — security embedded from Phase 1
- Least privilege database user for the application
- HTTP security headers on all responses (OWASP Secure Headers)
- Strict CORS configuration (no wildcards in production)
- Trusted host validation
- Sensitive data never logged
- Production configuration validates security constraints at startup

---

## License

Licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.

For third-party dependency licenses, see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

## Contributing

This platform is being developed for donation to the Colombian Government. Development follows security-first principles and government software engineering standards.

Before contributing, review:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — understand the design
- [docs/SECURITY.md](docs/SECURITY.md) — security requirements are mandatory
- [docs/ADR/](docs/ADR/) — understand why decisions were made
