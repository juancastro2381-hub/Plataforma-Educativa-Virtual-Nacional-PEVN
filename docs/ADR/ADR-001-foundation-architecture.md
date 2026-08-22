# ADR-001: Foundation Architecture Decision

**Status:** Accepted  
**Date:** 2026-08-21  
**Authors:** PEVN Development Team  
**Phase:** 1 — Foundation

---

## Context

The Plataforma Educativa Virtual Nacional (PEVN) requires a technical foundation that:

1. Will eventually serve the entire Colombian public education system at national scale
2. Must meet government-grade security requirements
3. Will be donated to the Colombian Government for national operation
4. Must be maintainable and extensible by future development teams
5. Must support students and teachers on low-end devices with limited connectivity
6. Must eventually integrate BigBlueButton for virtual classrooms

This ADR documents the architectural decisions made for Phase 1 (Foundation) and the rationale behind each choice.

---

## Decisions

### 1. Separation of Frontend and Backend

**Decision:** Maintain a strict frontend/backend separation with a RESTful JSON API as the contract.

**Rationale:**
- Allows independent scaling of frontend (CDN/static hosting) and backend (horizontal worker scaling)
- Enables future native mobile applications to consume the same API
- Clear separation of concerns between UI rendering and business logic
- Supports frontend caching strategies independently of backend logic
- Aligns with modern government platform architecture patterns

**Alternatives considered:**
- Server-side rendering (SSR/full-stack): Rejected — tighter coupling, harder to scale independently
- GraphQL: Rejected for Phase 1 — adds complexity without clear benefit at this stage

---

### 2. Backend: Python + FastAPI

**Decision:** Use Python 3.12 with FastAPI as the backend web framework.

**Rationale:**
- FastAPI provides native async support via asyncio — critical for handling concurrent virtual classroom sessions
- Automatic OpenAPI documentation generation from type hints reduces maintenance burden
- Pydantic v2 provides compile-time-like validation with excellent performance
- Python has a strong ecosystem for data processing, which will be needed for academic analytics (Phase 5+)
- FastAPI's dependency injection system enables clean, testable code
- Strong community and long-term maintenance trajectory

**Alternatives considered:**
- Django: Considered — rich ecosystem, but heavier and async support more complex
- Node.js/Express: Rejected — team preference and Python ecosystem alignment
- Go: Rejected — less ecosystem for academic/government integration needs

---

### 3. ORM: SQLAlchemy 2.0 (Async)

**Decision:** Use SQLAlchemy 2.0 with async engine and asyncpg driver.

**Rationale:**
- Industry-standard Python ORM with excellent maintainability
- SQLAlchemy 2.0 provides a modern, type-safe API
- Async support prevents event loop blocking during database operations
- asyncpg is the highest-performance async PostgreSQL driver available for Python
- Clear abstraction prevents vendor lock-in and direct SQL exposure
- All queries through ORM or parameterized text() — no string concatenation

---

### 4. Database: PostgreSQL 16

**Decision:** Use PostgreSQL as the primary database.

**Rationale:**
- Industry standard for government/enterprise transactional data
- Superior support for complex queries, JSONB, and advanced indexing
- Strong ACID compliance for academic record integrity
- Row-level security (future) for fine-grained institutional data isolation
- Colombian government institutions are familiar with PostgreSQL
- Excellent replication, backup, and high availability ecosystem

**Alternatives considered:**
- MySQL/MariaDB: Rejected — weaker JSON support, less advanced feature set
- MongoDB: Rejected — educational records require strong schema consistency

---

### 5. Database Migrations: Alembic

**Decision:** Use Alembic for database schema migrations.

**Rationale:**
- Native SQLAlchemy migration tool — tight integration
- Version-controlled schema changes with rollback support
- Autogenerate capability from SQLAlchemy models reduces human error
- Supports async migration via async_engine_from_config

---

### 6. Frontend: React 18 + TypeScript 5 + Vite 6

**Decision:** Use React with TypeScript and Vite as the build tool.

**Rationale:**
- React: Large talent pool, strong ecosystem, component model fits educational UI
- TypeScript: Mandatory for a maintainable codebase at scale — catches errors at development time
- Vite: Fastest development server startup, native ESM, excellent PWA plugin support
- This stack is the most widely used in Colombian government technology teams

**Alternatives considered:**
- Next.js: Considered — rejected for Phase 1 as SSR adds complexity without benefit yet
- Vue.js: Rejected — smaller talent pool in Colombia
- Angular: Rejected — heavy framework overhead, slower development velocity

---

### 7. Styling: Tailwind CSS v3

**Decision:** Use Tailwind CSS v3 for styling.

**Rationale:**
- Utility-first approach enables rapid, consistent UI development
- No unused CSS in production (PurgeCSS built in)
- Works well with design token approach used in the PEVN design system
- Strong mobile-first responsive design support
- Version 3 is stable and widely supported; v4 considered but not yet production-stable at time of decision

---

### 8. Containerization: Docker + Docker Compose

**Decision:** Use Docker for service containerization with Docker Compose for local development orchestration.

**Rationale:**
- Reproducible environments eliminate "works on my machine" problems
- Defines exact PostgreSQL and Redis versions in code
- Enables future migration to Kubernetes or other orchestration platforms
- Standard in Colombian government IT infrastructure planning
- Multi-stage builds minimize production image size and attack surface

---

### 9. Cache / Session Backend: Redis

**Decision:** Include Redis in the infrastructure foundation.

**Rationale:**
- Required for multi-worker session management (Phase 2 authentication)
- Required for distributed rate limiting (Phase 2)
- Required for async job queuing (Phase 3+, e.g., notification delivery)
- Avoids architectural rework later by establishing it now

---

### 10. Security by Design

**Decision:** Apply security controls from the first commit. No "add security later" approach.

**Specific decisions:**
- Separate application database user with least-privilege permissions
- Security headers middleware on all responses
- Explicit CORS configuration (no wildcard)
- Trusted host middleware to prevent Host header injection
- Correlation IDs for complete request tracing
- Centralized exception handlers that never expose internal details
- Production configuration validation that rejects unsafe settings at startup
- Authentication and authorization are defined as interfaces, not placeholder implementations

**Rationale:**
- Retrofitting security into an existing system is exponentially more expensive
- Government-grade systems require security audit compliance from day one
- The cost of a security incident in an educational platform affects minors

---

### 11. Authorization Model Design

**Decision:** Design for Role + Permission + Scope + Business Rules from the start, even though full implementation comes in Phase 2.

**Rationale:**
- A simple `if user.role == "admin"` check spread throughout code creates unmaintainable authorization logic
- The PEVN platform has a complex 10-level organizational hierarchy
- Institutional isolation (Institution A cannot see Institution B's data) requires scope-based checks
- Centralizing authorization in a service allows future audit, policy updates, and testing

---

### 12. Audit Architecture

**Decision:** Define the audit service interface in Phase 1, with NoOpAuditService as the Phase 1 implementation.

**Rationale:**
- Audit requirements for a government educational platform are extensive and legally significant
- Defining the interface now ensures all future code routes through the correct abstraction
- Phase 2 will implement persistent audit logging with an append-only database table

---

### 13. BigBlueButton Integration Strategy

**Decision:** Do NOT integrate BigBlueButton in Phase 1. Define the `IMeetingProvider` abstraction.

**Rationale:**
- Premature integration couples the educational platform to a specific meeting provider
- The abstraction allows future replacement or multi-provider support
- BigBlueButton requires stable authentication and user management (Phase 2) before integration makes sense

Architecture target:
```
Educational Platform
↓
Meeting Service (domain interface)
↓
Meeting Provider Adapter (IMeetingProvider)
↓
BigBlueButton API
```

---

### 14. Progressive Web App Foundation

**Decision:** Configure PWA foundations in Phase 1 (manifest, service worker strategy, icon structure).

**Rationale:**
- Colombia's education infrastructure includes many students with low-bandwidth or intermittent connectivity
- PWA installation enables faster startup and some offline capabilities for static resources
- Setting up PWA later requires cache strategy redesign

---

### 15. License: Apache-2.0

**Decision:** License the platform under Apache License 2.0.

**Rationale:**
- Permissive license suitable for government contribution and donation
- Includes explicit patent protection (important for government software reuse)
- Compatible with GPL (allows incorporating GPL components if needed)
- Widely recognized by government legal departments
- Enables commercial support vendors to contribute without licensing friction

---

## Consequences

**Positive:**
- Clean, testable, modular architecture ready for Phase 2 implementation
- Security controls embedded from the start reduce audit remediation cost
- Technology stack aligns with Colombian government digital transformation strategy
- All team members can contribute independently to backend or frontend
- Container-based deployment is portable to any government infrastructure

**Negative:**
- Higher initial complexity than a simple monolithic approach
- TypeScript adds compile-time overhead (acceptable for maintainability gains)
- Async Python requires careful understanding of event loop behavior

**Risks:**
- Team must maintain discipline to route all authorization through the central service
- Audit implementation must be completed before processing real student data
- Real-world BigBlueButton server capacity planning needed for Phase 3

---

## Review Schedule

This ADR should be reviewed at the end of Phase 2 to assess whether the architecture requires adjustment based on lessons learned.
