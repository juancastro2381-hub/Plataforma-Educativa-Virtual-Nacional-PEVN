# PHASE 3B — FORMAL CLOSURE REPORT
## Academic Management Domain Implementation & Verification

**Domain:** Academic Management (Gestión Académica e Institucional)  
**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Status:** COMPLETE / VERIFIED / DOCUMENTED  
**Security Baseline:** FROZEN & FULLY PRESERVED  
**Date of Formal Closure:** 2026-08-23  

---

## 1. Executive Summary

Phase 3B of the Plataforma Educativa Virtual Nacional (PEVN) has completed its full engineering, integration, and verification lifecycle. This phase delivered the core academic backbone of the national educational platform, enabling multi-tenant administration of academic calendars, classrooms with capacity locking, student identification via national SIMAT standards, legal guardians with decoupled civil contact records, teaching appointments, atomic classroom transfers with immutable audit trails, and single-active-teacher workload allocations.

All 8 implementation steps (Steps 1 through 7) have been rigorously validated. The security, authentication, authorization, and multi-tenant isolation foundations established in Phase 2 remain completely intact, frozen, and proven across 103 automated tests (84 backend pytest integration/E2E tests and 19 frontend Vitest component tests).

---

## 2. Phase 3B Scope

Phase 3B encompassed the end-to-end implementation of the academic domain model approved in Phase 3A/3A.1:
- **Foundational Catalogs & Calendars:** MEN National Grade catalog, Knowledge Areas, Academic Subjects, and Academic Years.
- **Academic Actors & Classrooms:** Groups/Salones with hard capacity bounds, Student profiles with inclusion metadata, Teacher statutory appointments, and Guardian civil records.
- **Academic Lifecycle:** Pre-enrollment, activation, withdrawal, and graduation transitions.
- **Integrity Invariants:** Single active academic year, non-overlapping student enrollments, locked group capacity enforcement, atomic classroom transfers with historical audit trails, and single-active-instructor workload assignments.
- **Full-Stack Delivery:** Async SQLAlchemy domain models, transactional domain service layer, FastAPI REST endpoints, TypeScript domain types, Axios API client, and React component views inside a central Academic Management Hub.

---

## 3. Completed Implementation Steps

### Step 1: Database & Academic Foundation
- **Models:** `AcademicYear`, `AcademicPeriod`, `Grade`, `KnowledgeArea`, `Subject`.
- **Database Migration:** Alembic revision `002_academic_foundation`.
- **Invariants:** Foreign key integrity, date range ordering (`start_date < end_date`), unique grade codes.

### Step 2: Groups & Actors
- **Models:** `Group`, `Teacher`, `Student`, `Guardian`, `StudentGuardian`.
- **Database Migration:** Alembic revision `003_groups_and_actors`.
- **Invariants:** Multi-tenant scoping per institution, unique SIMAT code per institution, decoupled civil identity for guardians with optional email ([OPEN-DECISION-3A-01]).

### Step 3: Enrollments, Assignments & Integrity Indexes
- **Models:** `Enrollment`, `GroupTransferHistory`, `AcademicAssignment`.
- **Database Migration:** Alembic revision `004_enrollments_and_assignments`.
- **Partial Indexes:** Partial unique index enforcing at most one `ACTIVE` enrollment per student per academic year, and at most one `ACTIVE` teacher assignment per group and subject.

### Step 4: Domain Services Layer
- **Architecture:** 8 domain services encapsulated under `backend/app/services/`:
  1. `AcademicYearService`
  2. `GroupService`
  3. `StudentService`
  4. `TeacherService`
  5. `GuardianService`
  6. `EnrollmentService`
  7. `TransferService`
  8. `AcademicAssignmentService`
- **Domain Exceptions:** Strict hierarchy inheriting from `DomainException` with HTTP status code mappings.

### Step 5: REST Controllers & API
- **Endpoints:** 8 REST routers under `backend/app/api/v1/endpoints/` aggregated into `router.py`.
- **Pydantic Schemas:** Complete request and response models in `backend/app/schemas/academic.py`.
- **Testing:** Integration test suite in `tests/test_academic_api.py` validating authentication, permissions, and tenant filtering.

### Step 6: Frontend Academic Views & UI Integration
- **Contracts:** TypeScript domain models in `frontend/src/types/academic.ts`.
- **API Client:** Strongly typed service methods in `frontend/src/services/academic.ts`.
- **UI Views:** `AcademicHub`, `AcademicYearsView`, `GroupsView`, `StudentsView`, `TeachersView`, `GuardiansView`, `EnrollmentsView`, `TransfersView`, and `AcademicAssignmentsView`.
- **Navigation:** Integrated into `RootLayout.tsx`, `App.tsx`, and `Dashboard.tsx`.

### Step 7: End-to-End Testing & Integration Validation
- **Integration Test Suite:** `backend/tests/test_academic_e2e_integration.py` validating the complete academic lifecycle, multi-tenant isolation barriers (blind 404), and atomic transfer operations.
- **Frontend Test Suite:** `frontend/src/test/Academic.test.tsx` expanded to 9 component integration tests (19 total across frontend).
- **Quality Baseline:** 100% PASS across all backend and frontend quality checkers.

---

## 4. Academic Management Architecture

The academic architecture strictly adheres to a 5-layer separation of concerns:

```
+-----------------------------------------------------------------------+
| 1. User Interface & Presentation Layer (React + Vanilla CSS)          |
|    - AcademicHub, AcademicYearsView, GroupsView, EnrollmentsView, etc. |
|    - Reusable UI Components: Modal, Badge, Card, Tabs, Alert           |
+-----------------------------------------------------------------------+
                                  |
+-----------------------------------------------------------------------+
| 2. Frontend API & State Client Layer                                  |
|    - services/academic.ts, types/academic.ts                          |
|    - In-Memory Access Token Bearer Interceptor & X-Correlation-ID      |
+-----------------------------------------------------------------------+
                                  |  (HTTPS JSON REST)
+-----------------------------------------------------------------------+
| 3. REST Controller & API Gateway Layer (FastAPI)                      |
|    - api/v1/endpoints/ academic routers                               |
|    - Pydantic Request Validation & Domain Exception -> HTTP Mapping   |
|    - Dependency-injected CentralizedAuthorizationService & TenantScope|
+-----------------------------------------------------------------------+
                                  |
+-----------------------------------------------------------------------+
| 4. Authoritative Domain Services Layer (Pure Business Logic)          |
|    - services/ academic domain services                               |
|    - Invariant Enforcement, Capacity Locking, Atomic Transactions     |
+-----------------------------------------------------------------------+
                                  |
+-----------------------------------------------------------------------+
| 5. Persistence & Relational Data Layer (PostgreSQL 16)                |
|    - SQLAlchemy Async ORM Entities                                    |
|    - PostgreSQL Partial Unique Indexes, Check Constraints, Foreign Keys|
+-----------------------------------------------------------------------+
```

---

## 5. Validated Academic Modules

1. **Academic Years (`AcademicYearsView` / `AcademicYearService` / `/academic-years`):**
   - Manages institutional school calendars (`CALENDAR_A`, `CALENDAR_B`).
   - Strict state machine: `PLANNING` $\rightarrow$ `ACTIVE` $\rightarrow$ `CLOSED`.
   - Single active year rule enforced at domain service and database constraint levels.

2. **Groups / Salones (`GroupsView` / `GroupService` / `/groups`):**
   - School classroom management across campus, grade, and shift (`MANANA`, `TARDE`, `NOCHE`, `UNICA`, `SABATINA`).
   - Group capacity limits with row-locked real-time queries (`/groups/{id}/capacity`).
   - Group Director teacher appointment.

3. **Students (`StudentsView` / `StudentService` / `/students`):**
   - National SIMAT identification tracking.
   - Socio-demographic metadata: birth date, gender, blood type, stratum (1–6), EPS provider.
   - Inclusion metadata: disability indicators and classification.

4. **Teachers (`TeachersView` / `TeacherService` / `/teachers`):**
   - Statutory appointment tracking (`PROPIEDAD`, `PERIODO_PRUEBA`, `PROVISIONAL`, `TEMPORAL`, `HORA_CATEDRA`).
   - National escalafón grades (Decreto 1278 / 2277).
   - Real-time assignment eligibility checking.

5. **Guardians (`GuardiansView` / `GuardianService` / `/guardians`):**
   - Decoupled civil registry identity with optional email ([OPEN-DECISION-3A-01]).
   - Student association with emergency primary contact and authorized pickup flags.

6. **Enrollments (`EnrollmentsView` / `EnrollmentService` / `/enrollments`):**
   - Full student enrollment book.
   - States: `PRE_ENROLLED`, `ACTIVE`, `WITHDRAWN`, `GRADUATED`.
   - Capacity slot consumption upon active enrollment; automatic over-capacity blocking (`GROUP_CAPACITY_EXCEEDED`).

7. **Transfers (`TransfersView` / `TransferService` / `/transfers`):**
   - Atomic classroom reassignments within the same academic year and grade.
   - Row-locked target group capacity verification.
   - Instant release of origin group capacity.
   - Immutable audit logging in `GroupTransferHistory`.

8. **Workload Assignments (`AcademicAssignmentsView` / `AcademicAssignmentService` / `/academic-assignments`):**
   - Allocation of weekly teaching hours per teacher, group, and subject.
   - Single-active-teacher invariant enforced via partial unique index (`uq_active_assignment_per_subject_group`).
   - Atomic teacher replacement (`/replace-teacher`).

9. **Academic Management Hub (`AcademicHub` / `/academic`):**
   - Master portal coordinating sub-module tab transitions, institutional context headers, and authenticated navigation.

---

## 6. Core Business Invariants

| Invariant Code | Rule Description | Enforcement Layer |
| :--- | :--- | :--- |
| `INV-ACAD-001` | An institution can have at most one `ACTIVE` academic year concurrently. | Domain Service + Database Partial Index |
| `INV-ACAD-002` | Academic years must satisfy `start_date < end_date`. | Pydantic Schema + Database Check Constraint |
| `INV-ACAD-003` | Group enrollment count cannot exceed `capacity_limit`. | Domain Service (`SELECT FOR UPDATE`) |
| `INV-ACAD-004` | SIMAT code must be unique within an institution. | Database Unique Constraint (`uq_student_institution_simat`) |
| `INV-ACAD-005` | A student can have at most one `ACTIVE` enrollment per academic year. | Database Partial Unique Index (`uq_active_enrollment_per_student_year`) |
| `INV-ACAD-006` | Transfers can only occur between groups of the same academic year and grade. | Domain Service Verification |
| `INV-ACAD-007` | Each subject in a group can have at most one `ACTIVE` teacher assigned. | Database Partial Unique Index (`uq_active_assignment_per_subject_group`) |
| `INV-ACAD-008` | Closed academic years reject new enrollments and state changes. | Domain Service Verification |

---

## 7. Transactional & Atomic Operations

All state-mutating academic workflows execute within explicit ACID transaction boundaries:
1. **Enrollment Creation & Activation:** Locks the group row (`with_for_update()`), recalculates active enrollments, and commits only if available slots $> 0$.
2. **Classroom Transfer:** In a single atomic transaction:
   - Locks target group row and validates available capacity.
   - Updates `Enrollment.group_id` to target group.
   - Inserts audit record into `GroupTransferHistory`.
   - Releases slot in source group and occupies slot in target group.
3. **Teacher Replacement:** In a single atomic transaction:
   - Deactivates the incumbent assignment (`is_active = False`).
   - Creates a new active assignment for the replacement teacher.
   - Guarantees zero downtime in course delivery while satisfying `INV-ACAD-007`.

---

## 8. Authentication Model

- **JWT Structure:** Asymmetric/HMAC-signed short-lived (15-minute) Bearer access tokens containing `sub`, `username`, `roles`, `permissions`, `institution_id`, `jti`, and `exp`.
- **Client Storage:** Strictly **in-memory** (`inMemoryAccessToken`). Tokens are never persisted to `localStorage` or `sessionStorage`.
- **Silent Background Refresh:** Automatic token refresh via secure, HttpOnly, SameSite=Lax, cookie-backed refresh tokens (`pevn_refresh_token`) with rotation and breach detection.
- **Correlation ID:** All frontend requests attach `X-Correlation-ID: crypto.randomUUID()` for full distributed tracing.

---

## 9. RBAC Model

Fine-grained resource-action permission model enforced centrally via `CentralizedAuthorizationService`:

| System Role | Typical Academic Permissions |
| :--- | :--- |
| **SuperAdmin** | Full system bypass (`*`), can manage any institution via `?institution_id=`. |
| **Rector** | `academic_years:*`, `groups:*`, `students:*`, `teachers:*`, `guardians:*`, `enrollments:*`, `academic_assignments:*`. |
| **Academic Coordinator** | `groups:read`, `groups:update`, `students:*`, `teachers:read`, `guardians:*`, `enrollments:*`, `academic_assignments:*`. |
| **Teacher** | `students:read`, `guardians:read`, `academic_assignments:read`, `groups:read`. |
| **Student** | `students:read` (self profile), `academic_assignments:read` (own group). |

---

## 10. Multi-Tenant Isolation Model

- **Tenant Boundaries:** All academic entities (`AcademicYear`, `Group`, `Student`, `Teacher`, `Guardian`, `Enrollment`, `GroupTransferHistory`, `AcademicAssignment`) are strictly partitioned by `institution_id`.
- **Blind 404 Protection:** Attempted access to another tenant's academic resource using a known UUID returns **`HTTP 404 Not Found`** rather than `403 Forbidden`, preventing resource existence probing.
- **No Client Tenant Spoofing:** Institutional users cannot override their assigned institution via query parameters or payload manipulation.

---

## 11. Security Guarantees

1. **Frozen Phase 2 Controls:** Argon2id password hashing, JWT token rotation, replay breach detection, account lockout, rate limiting, and HttpOnly cookie protections remain 100% intact.
2. **Zero Security Compromises:** No security checks were bypassed, relaxed, or mocked in production paths.
3. **Defense-in-Depth:** Frontend route guards (`RequireAuth`, `RequirePermission`, `RequireRole`) provide intuitive UX feedback, while backend controllers and domain services independently enforce strict authorization.

---

## 12. Frontend Architecture & Directory Layout

```
frontend/src/
├── types/
│   ├── academic.ts               # Complete TypeScript types matching backend schemas
│   └── index.ts                  # Re-exporting academic and common error types
├── services/
│   ├── academic.ts               # Typed API client for all 8 academic modules
│   └── api/client.ts             # Axios instance with in-memory JWT & correlation headers
├── components/
│   └── ui/                       # Reusable UI component design system
│       ├── Badge.tsx             # Status badge component
│       ├── Modal.tsx             # Accessible dialog with ESC dismissal
│       ├── Alert.tsx             # Alert component with correlation ID support
│       ├── Card.tsx              # Content container card
│       ├── Tabs.tsx              # Tab navigation component
│       └── EmptyState.tsx        # Empty state visual placeholder
├── pages/
│   ├── Dashboard.tsx             # Dashboard with Academic Portal launch card
│   └── academic/
│       ├── AcademicHub.tsx       # Master hub coordinating academic modules
│       ├── AcademicYearsView.tsx # Academic year lifecycle views
│       ├── GroupsView.tsx        # Classroom management & capacity inspections
│       ├── StudentsView.tsx      # Student SIMAT profiles & guardians drawer
│       ├── TeachersView.tsx      # Teacher appointments & eligibility validation
│       ├── GuardiansView.tsx     # Civil registry & family linking views
│       ├── EnrollmentsView.tsx   # Enrollment book & lifecycle actions
│       ├── TransfersView.tsx     # Atomic transfer workflows & history audit log
│       └── AcademicAssignmentsView.tsx # Workload allocations & teacher replacements
└── test/
    ├── Academic.test.tsx         # 9 Component integration tests for academic views
    ├── App.test.tsx              # Router & layout tests
    └── Auth.test.tsx             # Authentication & guard tests
```

---

## 13. Backend Architecture & Directory Layout

```
backend/app/
├── models/                       # SQLAlchemy Async ORM Entities
│   ├── academic_year.py          # AcademicYear, AcademicPeriod
│   ├── grade.py                  # Grade (Transición - Undécimo)
│   ├── subject.py                # KnowledgeArea, Subject
│   ├── group.py                  # Group
│   ├── student.py                # Student, StudentGuardian
│   ├── teacher.py                # Teacher
│   ├── guardian.py               # Guardian
│   └── enrollment.py             # Enrollment, GroupTransferHistory, AcademicAssignment
├── schemas/
│   └── academic.py               # Pydantic v2 schemas for all academic domains
├── services/                     # Authoritative Domain Services Layer
│   ├── academic_year_service.py
│   ├── group_service.py
│   ├── student_service.py
│   ├── teacher_service.py
│   ├── guardian_service.py
│   ├── enrollment_service.py
│   ├── transfer_service.py
│   └── academic_assignment_service.py
├── api/v1/endpoints/             # REST API Controllers
│   ├── academic_years.py
│   ├── groups.py
│   ├── students.py
│   ├── teachers.py
│   ├── guardians.py
│   ├── enrollments.py
│   ├── transfers.py
│   └── academic_assignments.py
└── core/
    ├── exceptions.py             # Domain exception hierarchy
    └── security/                 # Frozen Phase 2 Security Architecture
```

---

## 14. API Integration Summary

| Endpoint Route | Method | Purpose | Authorization Gate |
| :--- | :--- | :--- | :--- |
| `/api/v1/academic-years` | `GET` | List academic years (filtered by status) | `academic_years:read` |
| `/api/v1/academic-years` | `POST` | Create new academic year in `PLANNING` | `academic_years:create` |
| `/api/v1/academic-years/{id}/activate` | `POST` | Activate academic year | `academic_years:update` |
| `/api/v1/academic-years/{id}/close` | `POST` | Formal closure of academic year | `academic_years:close` |
| `/api/v1/groups` | `GET` | List classroom groups with filters | `groups:read` |
| `/api/v1/groups` | `POST` | Create classroom group with capacity limit | `groups:create` |
| `/api/v1/groups/{id}/capacity` | `GET` | Query locked real-time slot availability | `groups:read` |
| `/api/v1/groups/{id}/assign-director` | `POST` | Assign group director teacher | `groups:assign_director` |
| `/api/v1/students` | `GET` | List students (SIMAT search) | `students:read` |
| `/api/v1/students` | `POST` | Register student profile | `students:create` |
| `/api/v1/students/{id}/guardians` | `GET` | List linked legal guardians | `students:read` |
| `/api/v1/teachers` | `GET` | List institutional teachers | `teachers:read` |
| `/api/v1/teachers` | `POST` | Register teacher appointment | `teachers:create` |
| `/api/v1/teachers/{id}/eligibility` | `GET` | Query assignment eligibility | `teachers:read` |
| `/api/v1/guardians` | `GET` | List guardians (document search) | `guardians:read` |
| `/api/v1/guardians` | `POST` | Register civil guardian record | `guardians:create` |
| `/api/v1/guardians/{id}/students/{sid}` | `POST` | Associate guardian to student | `guardians:link_student` |
| `/api/v1/enrollments` | `GET` | List enrollments (status filter) | `enrollments:read` |
| `/api/v1/enrollments` | `POST` | Create pre-enrollment or active enrollment | `enrollments:create` |
| `/api/v1/enrollments/{id}/activate` | `POST` | Activate pre-enrollment | `enrollments:create` |
| `/api/v1/enrollments/{id}/withdraw` | `POST` | Withdraw student enrollment | `enrollments:withdraw` |
| `/api/v1/enrollments/{id}/graduate` | `POST` | Graduate student enrollment | `enrollments:withdraw` |
| `/api/v1/transfers` | `POST` | Execute atomic classroom transfer | `enrollments:transfer` |
| `/api/v1/transfers/enrollments/{id}/history` | `GET` | Query transfer audit history | `enrollments:read` |
| `/api/v1/academic-assignments` | `GET` | List teaching workload allocations | `academic_assignments:read` |
| `/api/v1/academic-assignments` | `POST` | Assign teacher to subject and group | `academic_assignments:create` |
| `/api/v1/academic-assignments/{id}/deactivate` | `POST` | Deactivate workload assignment | `academic_assignments:update` |
| `/api/v1/academic-assignments/{id}/replace-teacher` | `POST` | Atomic teacher replacement | `academic_assignments:update` |

---

## 15. Database Integrity

- **PostgreSQL Migrations Applied:**
  - `001_initial_schema.py`: Tenancy, Users, Roles, Permissions, Auth tokens.
  - `002_academic_foundation.py`: Grades, Knowledge Areas, Subjects, Academic Years.
  - `003_groups_and_actors.py`: Groups, Teachers, Students, Guardians, StudentGuardians.
  - `004_enrollments_and_assignments.py`: Enrollments, GroupTransferHistory, AcademicAssignments, Partial Unique Indexes.
- **Integrity Validation:** Tested and verified with 0 constraint conflicts or orphan records.

---

## 16. Test Coverage

- **Backend Pytest Suite:** **84/84 PASS (100%)**
  - `tests/test_academic_e2e_integration.py`: 2 E2E suites (Full lifecycle + Multi-tenant/RBAC boundaries).
  - `tests/test_academic_api.py`: 6 REST integration test suites.
  - `tests/test_domain_services.py`: 5 Domain service test suites.
  - `tests/test_auth_endpoints.py`: 10 Authentication endpoint suites.
  - `tests/test_tenancy.py`: 10 Multi-tenancy isolation suites.
  - `tests/test_tokens.py`, `test_security.py`, `test_models.py`, `test_config.py`: 51 Core foundation suites.
- **Frontend Vitest Suite:** **19/19 PASS (100%)**
  - `frontend/src/test/Academic.test.tsx`: 9 Component integration test suites.
  - `frontend/src/test/Auth.test.tsx`: 6 Authentication & Guard test suites.
  - `frontend/src/test/App.test.tsx`: 4 Routing & Layout test suites.

---

## 17. Final Quality Baseline

```
========================================================================================
                          OFFICIAL PHASE 3B QUALITY BASELINE
========================================================================================
[PASS] Frontend TypeScript (tsc --noEmit)            : 0 errors
[PASS] Frontend Linter (eslint . --max-warnings 0)   : 0 errors, 0 warnings
[PASS] Frontend Vitest Suite (vitest run)            : 19/19 passed (100%)
[PASS] Frontend Production Bundle (vite build)       : Success (PWA + Service Worker)
[PASS] Backend Pytest Suite (pytest -v)              : 84/84 passed (100%)
[PASS] Backend Formatter (black --check backend)     : 94 files clean
[PASS] Backend Linter (ruff check backend)           : 0 issues
[PASS] Backend Static Typecheck (mypy backend)       : 0 errors (98 source files clean)
[PASS] JWT & In-Memory Token Security                : FROZEN & VERIFIED
[PASS] Multi-Tenant Isolation (Blind 404)            : FROZEN & VERIFIED
[PASS] RBAC & Granular Permission Matching           : FROZEN & VERIFIED
[PASS] PostgreSQL Invariants & Capacity Locks        : FROZEN & VERIFIED
========================================================================================
```

---

## 18. Known Decisions & Architectural Records

- **`[OPEN-DECISION-3A-01]` Guardian Decoupled Civil Identity:** Legal guardians do not require active user accounts or mandatory email addresses. Phone and document number are authoritative civil contact channels.
- **`[OPEN-DECISION-3A-02]` SIMAT Tenant Scope:** SIMAT code uniqueness is enforced strictly per institution (`institution_id`, `code_simat`).
- **`[OPEN-DECISION-3A-03]` Single Active Instructor Rule:** Each subject in a group allows at most one active instructor concurrently. Substitutions must execute through `/replace-teacher`.
- **`[OPEN-DECISION-3A-04]` Immutable Transfer Audit:** Student transfers between classrooms do not overwrite previous enrollment records destructively; transfer history is recorded in `GroupTransferHistory`.

---

## 19. Deferred Work (Non-Defects)

The following items are deferred by architecture and design to subsequent phases:
- **Phase 4:** Virtual Classroom & Video Conferencing integration (BigBlueButton API, breakout rooms, meeting recordings).
- **Phase 5:** Evaluation, Grading & Academic Rubrics (Períodos Académicos evaluation weights, Boletines de Calificaciones, Desempeños MEN).
- **Phase 6:** Institutional Attendance & Daily Tracking.

---

## 20. Regression Protection Rules

Future phases modifying the codebase must strictly adhere to the following rules:
1. **Never alter Phase 2 Security:** Do not modify JWT claims, in-memory token handling, HttpOnly cookie lifecycle, or `CentralizedAuthorizationService`.
2. **Never weaken Multi-Tenant Isolation:** Institutional queries must always filter by `institution_id`. Cross-tenant queries must always return `404 Not Found`.
3. **Never calculate capacity on the client:** Always query `/api/v1/groups/{id}/capacity` or execute row-locked database operations.
4. **Never bypass atomic operations:** Teacher replacements and group transfers must use their respective transactional endpoints.

---

## 21. Future Development Constraints

- New controllers in future phases must remain pure REST boundaries and delegate all business logic to domain services.
- Database migrations must include corresponding down-revisions and maintain foreign key integrity.
- Frontend views must strictly consume the REST API and normalize errors through `client.ts` displaying correlation IDs.

---

## 22. Phase 3B Closure Statement

```
========================================================================================
                             PHASE 3B — FORMALLY CLOSED
========================================================================================

STATUS:
COMPLETE / VERIFIED / DOCUMENTED

SECURITY BASELINE:
FROZEN & PRESERVED

REGRESSION BASELINE:
PRESERVED (84/84 Backend Pytest PASS, 19/19 Frontend Vitest PASS, 0 Lint/Typecheck Errors)

NEXT ACTION:
WAIT FOR AUTHORIZATION FOR THE NEXT PHASE (PHASE 4)
========================================================================================
```
