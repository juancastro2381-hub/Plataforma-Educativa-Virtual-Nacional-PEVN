# Phase 3B — Step 5: REST Controllers & API Architecture

**Document ID:** PEVN-DOC-P3B-STEP5-API  
**Version:** 1.0.0  
**Phase:** 3B — Step 5 (Academic Management REST Controllers & API)  
**Status:** COMPLETED & VERIFIED  

---

## 1. Overview & Architecture

Phase 3B Step 5 exposes the academic management domain functionality implemented across Steps 1 through 4 via a secure, tenant-isolated, OpenAPI-compliant REST API layer.

The REST layer adheres strictly to the separation of concerns:
- **Application Boundary Only:** Controllers (`app/api/v1/endpoints/`) perform request deserialization, dependency injection, authentication/authorization enforcement, correlation tracking, and transactional commit/rollback.
- **Authoritative Business Services:** All domain validation, pessimistic locks (`SELECT ... FOR UPDATE`), partial index invariant checks, state transitions, and audit trail generation are delegated to `app/services/` domain services.
- **Deterministic Error Mapping:** Domain exceptions inherit from `PEVNException` with explicit HTTP status codes (400, 403, 404, 409), handled centrally by `pevn_exception_handler` in `app/core/errors/handlers.py` without stack trace leakage.

---

## 2. Implemented Controller Modules & Endpoints

| Resource Prefix | Controller Module | HTTP Method | Endpoint Path | Status Code | Required Permission | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/academic-years` | [`academic_years.py`](file:///backend/app/api/v1/endpoints/academic_years.py) | `POST` | `/` | `201 Created` | `academic_years:create` | Creates a new academic year in `PLANNING` status. |
| | | `GET` | `/{year_id}` | `200 OK` | `academic_years:read` | Retrieves an academic year by ID. |
| | | `GET` | `/` | `200 OK` | `academic_years:read` | Lists academic years with optional status filter. |
| | | `POST` | `/{year_id}/activate` | `200 OK` | `academic_years:update` | Transitions status `PLANNING -> ACTIVE`. |
| | | `POST` | `/{year_id}/close` | `200 OK` | `academic_years:close` | Transitions status `ACTIVE -> CLOSED`. |
| `/api/v1/groups` | [`groups.py`](file:///backend/app/api/v1/endpoints/groups.py) | `POST` | `/` | `201 Created` | `groups:create` | Creates a classroom group with physical capacity limit. |
| | | `GET` | `/{group_id}` | `200 OK` | `groups:read` | Retrieves group details. |
| | | `GET` | `/` | `200 OK` | `groups:read` | Lists groups with campus, year, and grade filters. |
| | | `GET` | `/{group_id}/capacity` | `200 OK` | `groups:read` | Real-time capacity computation and slot availability. |
| | | `POST` | `/{group_id}/assign-director` | `200 OK` | `groups:assign_director` | Assigns an institutional teacher as group director. |
| `/api/v1/students` | [`students.py`](file:///backend/app/api/v1/endpoints/students.py) | `POST` | `/` | `201 Created` | `students:create` | Creates a student profile linked 1:1 to a User account. |
| | | `GET` | `/{student_id}` | `200 OK` | `students:read` | Retrieves student profile by ID. |
| | | `GET` | `/` | `200 OK` | `students:read` | Lists students with SIMAT filter. |
| | | `GET` | `/{student_id}/guardians` | `200 OK` | `students:read` | Lists guardians linked to the student. |
| `/api/v1/teachers` | [`teachers.py`](file:///backend/app/api/v1/endpoints/teachers.py) | `POST` | `/` | `201 Created` | `teachers:create` | Creates a teacher profile linked 1:1 to a User account. |
| | | `GET` | `/{teacher_id}` | `200 OK` | `teachers:read` | Retrieves teacher profile by ID. |
| | | `GET` | `/` | `200 OK` | `teachers:read` | Lists teachers with appointment type filters. |
| | | `GET` | `/{teacher_id}/eligibility` | `200 OK` | `teachers:read` | Validates teacher eligibility for workload assignment. |
| `/api/v1/guardians` | [`guardians.py`](file:///backend/app/api/v1/endpoints/guardians.py) | `POST` | `/` | `201 Created` | `guardians:create` | Registers a civil guardian ([OPEN-DECISION-3A-01]). |
| | | `GET` | `/{guardian_id}` | `200 OK` | `guardians:read` | Retrieves guardian civil record. |
| | | `GET` | `/` | `200 OK` | `guardians:read` | Lists guardians by document number. |
| | | `POST` | `/{guardian_id}/students/{student_id}` | `201 Created` | `guardians:link_student` | Links guardian to student with pickup authorizations. |
| `/api/v1/enrollments` | [`enrollments.py`](file:///backend/app/api/v1/endpoints/enrollments.py) | `POST` | `/` | `201 Created` | `enrollments:create` | Creates enrollment with row-locked capacity validation. |
| | | `GET` | `/{enrollment_id}` | `200 OK` | `enrollments:read` | Retrieves enrollment record. |
| | | `GET` | `/` | `200 OK` | `enrollments:read` | Lists enrollments with student, group, year, status filters. |
| | | `POST` | `/{enrollment_id}/activate` | `200 OK` | `enrollments:create` | Activates `PRE_ENROLLED` enrollment. |
| | | `POST` | `/{enrollment_id}/withdraw` | `200 OK` | `enrollments:withdraw` | Transitions active enrollment to `WITHDRAWN`. |
| | | `POST` | `/{enrollment_id}/graduate` | `200 OK` | `enrollments:withdraw` | Transitions active enrollment to `GRADUATED`. |
| `/api/v1/transfers` | [`transfers.py`](file:///backend/app/api/v1/endpoints/transfers.py) | `POST` | `/` | `200 OK` | `enrollments:transfer` | Executes atomic classroom transfer with capacity lock. |
| | | `GET` | `/enrollments/{enrollment_id}/history` | `200 OK` | `enrollments:read` | Lists audit trail of group transfers. |
| `/api/v1/academic-assignments` | [`academic_assignments.py`](file:///backend/app/api/v1/endpoints/academic_assignments.py) | `POST` | `/` | `201 Created` | `academic_assignments:create` | Creates subject assignment enforcing single active teacher. |
| | | `GET` | `/{assignment_id}` | `200 OK` | `academic_assignments:read` | Retrieves academic workload assignment. |
| | | `GET` | `/` | `200 OK` | `academic_assignments:read` | Lists assignments with filters (teacher, group, subject, year). |
| | | `POST` | `/{assignment_id}/deactivate` | `200 OK` | `academic_assignments:update` | Deactivates active assignment. |
| | | `POST` | `/{assignment_id}/replace-teacher` | `200 OK` | `academic_assignments:update` | Atomically replaces titular teacher with audit tracking. |

---

## 3. Tenant Context & Security Resolution

Every controller utilizes the tenant resolution pattern:
```python
def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    if SystemRole.SUPERADMIN in auth.roles and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")
```
1. Requests lacking valid Bearer tokens fail immediately with `401 Unauthorized`.
2. Requests with valid tokens but insufficient permissions fail with `403 Forbidden`.
3. Requests attempting to read or modify entities outside the user's institution scope fail with `404 Not Found` or `403 Forbidden` (`CrossTenantMismatchError`).
4. SuperAdmins can supply explicit `institution_id` query overrides for cross-tenant operations.

---

## 4. Centralized Domain Exception to HTTP Status Mapping

All academic domain exceptions inherit from `PEVNException` in [`backend/app/core/exceptions.py`](file:///backend/app/core/exceptions.py):

| Domain Exception | HTTP Status | Error Code | Example Trigger |
| :--- | :--- | :--- | :--- |
| `StudentAlreadyEnrolledActiveError` | `409 Conflict` | `STUDENT_ALREADY_ENROLLED_ACTIVE` | Student already has active enrollment in the academic year. |
| `GroupCapacityExceededError` | `409 Conflict` | `GROUP_CAPACITY_EXCEEDED` | Target classroom has reached maximum capacity. |
| `DuplicateActiveAssignmentError` | `409 Conflict` | `DUPLICATE_ACTIVE_ASSIGNMENT` | Subject already has an active teacher assigned in the group/year. |
| `AcademicYearLifecycleError` | `409 Conflict` | `ACADEMIC_YEAR_LIFECYCLE_ERROR` | Attempting to activate already active or closed year. |
| `InvalidTransferError` | `409 Conflict` | `INVALID_TRANSFER_ERROR` | Transferring to the same group or incompatible grade level. |
| `AcademicYearNotFoundError` | `404 Not Found` | `ACADEMIC_YEAR_NOT_FOUND` | Academic year does not exist in the tenant scope. |
| `GroupNotFoundError` | `404 Not Found` | `GROUP_NOT_FOUND` | Group does not exist in the tenant scope. |
| `StudentNotFoundError` | `404 Not Found` | `STUDENT_NOT_FOUND` | Student does not exist in the tenant scope. |
| `TeacherNotFoundError` | `404 Not Found` | `TEACHER_NOT_FOUND` | Teacher does not exist in the tenant scope. |
| `GuardianNotFoundError` | `404 Not Found` | `GUARDIAN_NOT_FOUND` | Guardian does not exist. |
| `EnrollmentNotFoundError` | `404 Not Found` | `ENROLLMENT_NOT_FOUND` | Enrollment does not exist in the tenant scope. |
| `AcademicAssignmentNotFoundError` | `404 Not Found` | `ACADEMIC_ASSIGNMENT_NOT_FOUND` | Assignment does not exist in the tenant scope. |
| `CrossTenantMismatchError` | `403 Forbidden` | `CROSS_TENANT_MISMATCH` | Cross-institutional entity coupling attempt. |
| `AcademicDomainError` | `400 Bad Request` | `ACADEMIC_DOMAIN_ERROR` | General domain validation violation. |

---

## 5. Automated Validation Results

- **Backend Pytest Suite:** 82/82 PASS (100%)
- **Static Type Analysis (Mypy):** Clean (0 errors across 77 source files)
- **Code Style (Black & Ruff):** Clean (0 warnings, 0 format discrepancies)
- **Frontend Vitest & Build:** TypeScript clean, ESLint clean, Production bundle built successfully.
