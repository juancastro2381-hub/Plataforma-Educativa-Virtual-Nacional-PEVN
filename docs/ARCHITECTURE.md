# PEVN Architecture Documentation

**Plataforma Educativa Virtual Nacional**  
**Phase:** 1 — Foundation  
**Last Updated:** 2026-08-21

---

## 1. System Overview

PEVN is a national virtual educational platform for Colombian public schools. It provides institutional management, academic coordination, and virtual classroom services to:

- **Students** across Colombia's public education system
- **Teachers** and academic staff
- **Principals (Rectores)** and Academic Coordinators
- **Institutional Administrators**
- **Territorial Administrators** (Municipal, Departmental, National)

---

## 2. Organizational Hierarchy

```
Colombia
  └── Department (Departamento)
       └── Municipality (Municipio)
            └── Educational Institution (Institución Educativa)
                 └── Campus (Sede)
                      └── Academic Structure
                           ├── Grade Levels
                           ├── Courses/Groups
                           ├── Subjects (Materias)
                           ├── Teachers
                           └── Students
```

### 2.1 Institutional Role Hierarchy

```
National/Departmental/Municipal Admin (gobierno)
  └── Rector / Principal
        └── Academic Coordinator
              └── Teacher (Docente)
                    └── Student (Estudiante)
```

---

## 3. High-Level Architecture

```
                    ┌─────────────────────────────────┐
                    │         PEVN Platform            │
                    └───────────────┬─────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                       │
    ┌─────────▼──────┐   ┌──────────▼──────┐   ┌──────────▼──────┐
    │   Frontend     │   │   Backend API   │   │   Background    │
    │  React/Vite    │◄──┤   FastAPI       │   │   Workers       │
    │  TypeScript    │   │   Python 3.12   │   │   (Phase 3+)    │
    └────────────────┘   └────────┬────────┘   └─────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                    │
    ┌─────────▼──────┐  ┌────────▼────────┐  ┌───────▼────────┐
    │  PostgreSQL 16 │  │    Redis 7      │  │  BigBlueButton │
    │  (Primary DB)  │  │  (Cache/Queue)  │  │  (Phase 3+)    │
    └────────────────┘  └─────────────────┘  └────────────────┘
```

---

## 4. Backend Architecture

### 4.1 Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # FastAPI dependencies
│   │   └── v1/
│   │       ├── router.py        # API v1 router
│   │       └── endpoints/
│   │           ├── health.py    # GET /api/v1/health
│   │           └── ready.py     # GET /api/v1/ready
│   ├── audit/
│   │   └── interfaces.py        # IAuditService, AuditEvent, NoOpAuditService
│   ├── core/
│   │   ├── config.py            # Application settings (pydantic-settings)
│   │   ├── logging.py           # Structured logging (structlog)
│   │   └── security/
│   │       ├── interfaces.py    # Auth/authz abstractions
│   │       └── headers.py       # HTTP security header builder
│   ├── db/
│   │   ├── base.py              # SQLAlchemy declarative base
│   │   ├── session.py           # Async engine + session factory
│   │   └── health.py            # Database connectivity check
│   ├── exceptions/
│   │   ├── errors.py            # Application error hierarchy
│   │   └── handlers.py          # FastAPI exception handlers
│   ├── middleware/
│   │   ├── correlation.py       # Request correlation ID
│   │   ├── logging_middleware.py # Request/response logging
│   │   └── security.py          # Security headers middleware
│   └── main.py                  # FastAPI application factory
├── migrations/                  # Alembic migrations
├── tests/                       # Pytest test suite
└── requirements/                # Pinned Python dependencies
```

### 4.2 Request Processing Pipeline

```
Request
  → TrustedHostMiddleware (rejects bad Host headers)
  → CORSMiddleware (applies CORS headers)
  → SecurityHeadersMiddleware (adds security headers)
  → CorrelationIDMiddleware (assigns request ID)
  → RequestLoggingMiddleware (logs request/response)
  → Route Handler
  → Exception Handlers (if error)
→ Response
```

### 4.3 Authorization Model (Phase 2+)

The final authorization model combines:

```
ALLOW IF:
  user has required Role (SystemRole)
  AND user has required Permission (resource:action)
  AND user's OrganizationalScope includes the target resource
  AND Business Rules do not deny access
```

This is implemented via the centralized `IAuthorizationService` interface.

---

## 5. Frontend Architecture

### 5.1 Directory Structure

```
frontend/src/
├── components/
│   ├── ErrorBoundary.tsx        # React error boundary
│   └── ui/
│       ├── Button.tsx           # Accessible button component
│       └── LoadingSpinner.tsx   # Loading indicators
├── config/
│   └── index.ts                 # Environment-based configuration
├── hooks/
│   └── useApi.ts                # API state management hook
├── layouts/
│   └── RootLayout.tsx           # Application shell
├── pages/
│   ├── ComingSoon.tsx           # Phase 1 landing page
│   └── NotFound.tsx             # 404 page
├── services/
│   └── api/
│       ├── client.ts            # Axios instance + interceptors
│       └── types.ts             # API service functions
├── styles/
│   └── globals.css              # Design system CSS
├── types/
│   └── index.ts                 # Shared TypeScript types
├── utils/
│   └── index.ts                 # Utility functions
├── App.tsx                      # Router + error boundary
└── main.tsx                     # React 18 entry point
```

### 5.2 Design System

**PEVN Color Palette:**
| Token | Hex | Usage |
|-------|-----|-------|
| `pevn-blue` | `#010066` | Primary brand, navigation, headings |
| `pevn-red` | `#C2343A` | Alerts, CTAs, error states |
| `pevn-deep-red` | `#950418` | Red hover states |
| `pevn-gold` | `#EDA83A` | Highlights, achievements |
| `pevn-white` | `#FCFBFA` | Backgrounds |

**Typography:** Inter (Google Fonts) — clean, readable at all sizes on low-DPI screens.

---

## 6. Data Flow

### 6.1 API Request Flow

```
Browser
  → HTTPS (production) / HTTP (development)
  → [Reverse Proxy] (production)
  → FastAPI ASGI Server
  → Middleware Stack
  → Route Handler
  → Service Layer (Phase 2+)
  → Repository Layer (Phase 2+)
  → SQLAlchemy ORM
  → PostgreSQL
```

### 6.2 Authentication Flow (Phase 2+)

```
Client → POST /api/v1/auth/login
  → IAuthenticationService.authenticate()
  → IPasswordHasher.verify()
  → ITokenService.create_access_token()
  → IAuditService.record(USER_LOGIN_SUCCESS)
  → { access_token, refresh_token }
```

---

## 7. Future BigBlueButton Architecture

The meeting abstraction is designed to avoid coupling the educational domain to BigBlueButton:

```
Educational Platform Domain
  ↓ (calls)
Meeting Service (IMeetingService)
  ↓ (delegates to)
Meeting Provider Adapter (IMeetingProvider)
  ↓ (calls)
BigBlueButton API
```

This allows future support for alternative meeting providers without changing the educational domain logic.

---

## 8. Scalability Design

The architecture is designed for future horizontal scaling:

```
[Load Balancer]
      │
 ┌────┴────────┐
 │   Backend   │ × N (multiple uvicorn workers)
 └─────┬───────┘
       │
  ┌────┴────────────────┐
  │                     │
  ▼                     ▼
[PostgreSQL]        [Redis]
(primary +         (shared state:
 replicas)          sessions, cache,
                    rate limits, queues)
```

**Key horizontal scaling considerations:**
- All shared state in PostgreSQL or Redis (not in-process)
- Correlation IDs for distributed request tracing
- Stateless authentication (JWT — Phase 2)
- Session data in Redis (not in-process memory)

---

## 9. Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend Language | Python | 3.12 |
| Web Framework | FastAPI | ~0.115 |
| ORM | SQLAlchemy (async) | ~2.0 |
| Migrations | Alembic | ~1.14 |
| Validation | Pydantic v2 | ~2.10 |
| ASGI Server | uvicorn / gunicorn | latest stable |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Frontend Framework | React | 18 |
| Frontend Language | TypeScript | 5 |
| Build Tool | Vite | 6 |
| Styling | Tailwind CSS | 3 |
| Containerization | Docker + Compose | v3 |
| CI | GitHub Actions | — |

---

## 10. Architecture Decision Records

See `docs/ADR/` for detailed decision records.

- [ADR-001](ADR/ADR-001-foundation-architecture.md) — Foundation Architecture
