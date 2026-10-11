# PEVN — NTA-10-R8: Academic Coordinator Role, Institutional Assignment, and Invitation Flow — End-to-End Audit

**Standard:** AI Software Factory Standard v1.2  
**Auditor / Agent:** Antigravity  
**Date:** 2026-10-10  
**Priority:** High  
**Classification:** Forensics, RBAC & Provisioning Audit  
**Target Repository:** Plataforma Educativa Virtual Nacional (PEVN)  

---

## 1. Executive Summary & Certification Status

### Final Status: `BLOCKED — ROLE, ASSIGNMENT, INVITATION, OR AUTHORIZATION GAP UNRESOLVED`

An exhaustive, evidence-based architectural and forensic audit was conducted across the backend codebase, relational schema (PostgreSQL), security/RBAC engine, and frontend application to determine whether the `ACADEMIC_COORDINATOR` role is implemented end-to-end and to resolve why the institutional operator (Rector) cannot identify a Coordinator role assignment or invitation function in the Rector Portal.

### High-Level Findings Summary:
1. **Canonical Role & Security Engine (Implemented):**  
   The canonical role exists under both identifiers (`academic_coordinator` and alias `coordinator` at hierarchy level 50) in [interfaces.py](file:///backend/app/core/security/interfaces.py) and [rbac_bootstrap_service.py](file:///backend/app/services/rbac_bootstrap_service.py). Permissions for academic management are fully configured.
2. **Backend Coordinator Provisioning Endpoint (Backend Only / Partial):**  
   A dedicated endpoint [POST /api/v1/coordinators](file:///backend/app/api/v1/endpoints/coordinators.py) exists and is protected by `coordinators:create` and `role:rector`. It allows a Rector to create a user and assign the `coordinator` role bound to their `institution_id`.
3. **Invitation Lifecycle & Security Architecture (CRITICAL DEFECT — NOT IMPLEMENTED):**  
   Unlike `RectorInvitation`, `DepartmentAdminInvitation`, `MunicipalityAdminInvitation`, and `GuardianInvitation` in [invitation.py](file:///backend/app/models/invitation.py), **no `CoordinatorInvitation` entity or database table exists**.  
   The existing backend creation flow bypasses the invitation workflow entirely: it requires the Rector to submit a raw password (`CoordinatorCreateRequest.password`), creates an immediately active user (`is_active=True`), generates zero cryptographic invitation tokens, sends zero emails, and does not integrate with [POST /api/v1/auth/accept-invitation](file:///backend/app/api/v1/endpoints/auth.py).
4. **Campus-Level Assignment (CRITICAL GAP — NOT IMPLEMENTED):**  
   While [UserRole](file:///backend/app/models/role.py) supports `campus_id`, [CoordinatorCreateRequest](file:///backend/app/schemas/coordinator.py) does not accept `campus_id`. Sede/campus-level scoping is therefore unavailable at creation time.
5. **Frontend Rector Portal (CRITICAL DEFECT — FRONTEND GAP):**  
   In the frontend, **no UI screen, dialog, action menu, or API client exists** for Coordinators. [AcademicHub.tsx](file:///frontend/src/pages/academic/AcademicHub.tsx) implements tabs for 13 academic entities (years, periods, grades, subjects, groups, students, teachers, guardians, enrollments, transfers, assignments, evaluations, settings), but has **zero** tab or modal for Coordinators. No `coordinator.ts` service exists in `frontend/src/services/`.

Because the invitation lifecycle is structurally missing in the database/backend and the user management UI is completely absent in the frontend, the exit gate is certified as **BLOCKED**.

---

## 2. Canonical Role and Permission Evidence

### 2.1 Role Definitions and Aliasing
In [backend/app/core/security/interfaces.py](file:///backend/app/core/security/interfaces.py):
```python
class SystemRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    NATIONAL_ADMIN = "national_admin"
    DEPARTMENT_ADMIN = "department_admin"
    MUNICIPALITY_ADMIN = "municipality_admin"
    RECTOR = "rector"
    COORDINATOR = "coordinator"
    ACADEMIC_COORDINATOR = "academic_coordinator"  # Level 50
    TEACHER = "teacher"
    STUDENT = "student"
    GUARDIAN = "guardian"
```

In [backend/app/services/rbac_bootstrap_service.py](file:///backend/app/services/rbac_bootstrap_service.py):
- `coordinator`: Display name *"Coordinador Académico / Sede"*, Level: 50.
- `academic_coordinator`: Display name *"Coordinador Académico"*, Level: 50.
- Both roles have canonical mappings to identical academic permission sets:
  - `academic:*` (read, create, update, delete for years, periods, grades, subjects, groups)
  - `students:*`, `teachers:*`, `enrollments:*`, `evaluations:*`
  - `coordinators:read` (read-only self/peer context)
- Rectors hold authority permissions: `coordinators:read`, `coordinators:create`, `coordinators:update`, `coordinators:delete`.

### 2.2 Institution Delegation Control
Under migration `030_institution_coordinator_delegation.py`, the `institutions` table has column:
- `coordinator_delegation_enabled` (BOOLEAN, default `FALSE`).
- Enforced in backend via [coordinator_service.py](file:///backend/app/services/coordinator_service.py) and [authorization.py](file:///backend/app/core/security/authorization.py):
  When `coordinator_delegation_enabled == False`, coordinators attempting academic mutations receive HTTP 403 (`COORDINATOR_DELEGATION_DISABLED`).

---

## 3. Frontend-to-Backend-to-Database Trace

The following matrix traces each sequential step of the target Rector-to-Coordinator onboarding workflow:

| Step | Target Workflow Action | Existing Frontend Screen / UI Component | Existing Service / API Client | Backend Endpoint & Method | Required Permissions & Auth Dependencies | Service & Database Operation | Status & Classification |
|---|---|---|---|---|---|---|---|
| **1** | Rector navigates to Institutional Personnel Management | None (`AcademicHub.tsx` has tabs for teachers, students, guardians, but no coordinator tab) | None | N/A | `role:rector`, `coordinators:read` | N/A | **FRONTEND GAP** |
| **2** | Create/Select Coordinator form / action button | None | None | N/A | `role:rector`, `coordinators:create` | N/A | **FRONTEND GAP** |
| **3** | Submit Coordinator creation payload | None | None | `POST /api/v1/coordinators` | `current_active_user`, `role:rector`, `coordinators:create` | `CoordinatorService.create_coordinator()` creates `User` & `UserRole(role="coordinator", institution_id=...)` | **BACKEND ONLY / FRONTEND GAP** |
| **4** | Assign Campus Scope (`campus_id`) | None | None | None (`CoordinatorCreateRequest` has no `campus_id`) | N/A | None (`UserRole.campus_id` remains NULL) | **NOT IMPLEMENTED** |
| **5** | Generate Cryptographic Invitation Token | None | None | None (No coordinator invitation generation endpoint) | N/A | None (No `CoordinatorInvitation` record created) | **NOT IMPLEMENTED** |
| **6** | Deliver or Copy Secure Invitation Link | None | None | None | N/A | None (No email sent; no dev link returned) | **NOT IMPLEMENTED** |
| **7** | Accept Invitation (`/auth/accept-invitation`) | `AcceptInvitation.tsx` exists for Rector/Territorial Admins | `auth.ts` | `POST /api/v1/auth/accept-invitation` | Public endpoint | Rejects token (accept-invitation only checks `RectorInvitation`, `DepartmentAdminInvitation`, `MunicipalityAdminInvitation`) | **NOT IMPLEMENTED FOR COORDINATOR** |
| **8** | Account Activation | None (Directly active on POST) | None | N/A | N/A | Direct `user.is_active = True` at creation | **BACKEND ONLY / BYPASSES INVITATION** |
| **9** | Authenticate (Login as Coordinator) | `LoginView.tsx` | `auth.ts: login()` | `POST /api/v1/auth/token` | Public OAuth2 password request | Verifies bcrypt password, issues JWT access & refresh cookies | **IMPLEMENTED** |
| **10** | Resolve Permissions & Tenant Scope | `AuthContext.tsx` | `auth.ts: getCurrentUser()` | `GET /api/v1/auth/me` | `current_active_user` | Loads `UserRole`, resolves `institution_id`, `role="coordinator"` | **IMPLEMENTED** |
| **11** | Coordinator Portal Access | `RootLayout.tsx`, `Dashboard.tsx`, `AcademicHub.tsx` | `academic.ts` | Academic endpoints | `role:coordinator`, institutional tenant match, delegation check | Allows reading and managing academic entities if delegation is active | **IMPLEMENTED** |

---

## 4. Location of Existing Coordinator Implementation vs. Gaps

### 4.1 Backend Implementation Details
1. **API Router Mounting:**  
   [backend/app/api/v1/router.py](file:///backend/app/api/v1/router.py#L36):
   ```python
   api_router.include_router(coordinators.router, prefix="/coordinators", tags=["coordinators"])
   ```
2. **Endpoints in [backend/app/api/v1/endpoints/coordinators.py](file:///backend/app/api/v1/endpoints/coordinators.py):**
   - `GET /api/v1/coordinators`: Lists coordinators for current user's institution.
   - `GET /api/v1/coordinators/{coordinator_id}`: Retrieves single coordinator.
   - `POST /api/v1/coordinators`: Creates coordinator. Requires `CoordinatorCreateRequest`.
   - `PATCH /api/v1/coordinators/{coordinator_id}/status`: Updates `is_active`.
3. **Payload Structure in [backend/app/schemas/coordinator.py](file:///backend/app/schemas/coordinator.py):**
   ```python
   class CoordinatorCreateRequest(BaseModel):
       email: EmailStr
       first_name: str
       last_name: str
       document_type: str
       document_number: str
       phone: Optional[str] = None
       password: str  # Direct password entry required
       institution_id: Optional[UUID] = None
   ```
   *Defects identified in schema:*
   - Requires explicit initial password from Rector (insecure pattern; contradicts invitation workflow).
   - Lacks `campus_id` parameter.

### 4.2 Frontend Absence (Why Operator Cannot Find the Feature)
1. **No Navigation or Hub Tab:**  
   [frontend/src/pages/academic/AcademicHub.tsx](file:///frontend/src/pages/academic/AcademicHub.tsx) defines the following 13 tabs:
   `years`, `periods`, `grades`, `subjects`, `groups`, `students`, `teachers`, `guardians`, `enrollments`, `transfers`, `assignments`, `evaluations`, `settings`.  
   There is **no `coordinators` tab**.
2. **No Frontend Service or Type:**  
   - `frontend/src/services/` contains `teacher.ts`, `student.ts`, `academic.ts`, `departmentAdmin.ts`, `municipalityAdmin.ts`, `onboarding.ts`. **No `coordinator.ts` exists.**
   - `frontend/src/types/` contains no coordinator model.
3. **Settings Tab Only Displays Toggle:**  
   In [frontend/src/pages/academic/InstitutionSettingsView.tsx](file:///frontend/src/pages/academic/InstitutionSettingsView.tsx), the Rector can toggle `coordinator_delegation_enabled` ON/OFF, but cannot view, create, or invite coordinators.

---

## 5. Implemented vs. Missing Functionality Matrix

| Architectural Capability | Backend Status | Database Status | Frontend Status | Overall Certification |
|---|---|---|---|---|
| **Canonical Role Definition (`COORDINATOR` / `ACADEMIC_COORDINATOR`)** | Full (Level 50) | Full (in `roles` table) | Full (Enum in frontend types) | **CERTIFIED** |
| **Academic Permission Mapping** | Full (30+ permissions) | Full (in `role_permissions`) | Full (Route guards recognize role) | **CERTIFIED** |
| **Institution Coordinator Delegation Flag** | Full (Enforced in services) | Full (`coordinator_delegation_enabled`) | Partial (Toggle UI in settings tab) | **CERTIFIED** |
| **Coordinator User Creation Endpoint** | Full (`POST /coordinators`) | Full (Writes `users` & `user_roles`) | None (Zero UI calls this endpoint) | **FRONTEND GAP** |
| **Campus Scope Assignment (`campus_id`)** | Missing in schema | Supported in `user_roles` column | None | **NOT IMPLEMENTED** |
| **Cryptographic Invitation Tokens & Model** | Missing (`0` records/tables) | Missing (`coordinator_invitations` table absent) | None | **NOT IMPLEMENTED** |
| **Secure Token Acceptance & Account Activation** | Missing in `/auth/accept-invitation` | N/A | Missing | **NOT IMPLEMENTED** |
| **Coordinator Academic Hub Access** | Full (Backend authorization allows) | N/A | Full (`AcademicHub` accessible when logged in) | **CERTIFIED** |

---

## 6. Institution/Campus Scope and Tenant-Isolation Findings

1. **Institutional Isolation:**  
   In `CoordinatorService.create_coordinator()`:
   ```python
   institution_id = current_user_role.institution_id
   ```
   A Rector can only provision a coordinator within their own `institution_id`. Anti-IDOR boundary prevents a Rector from passing another institution's ID.
2. **Privilege Escalation Protection:**  
   Coordinators cannot create other coordinators, Rectors, or territorial admins.
   Tested and verified in [test_nta08_authority_chain.py](file:///backend/tests/test_nta08_authority_chain.py#L324-L352):
   - `test_21_coordinator_cannot_create_coordinator` -> Returns 403 Forbidden.
   - `test_22_coordinator_cannot_create_territorial_admins` -> Returns 403 Forbidden.
3. **Campus-Level Scoping Gap:**  
   In PEVN institutions with multiple sedes/campuses, a Coordinator assigned to a specific campus should have their `UserRole.campus_id` populated. Because `CoordinatorCreateRequest` omits `campus_id`, all coordinators are currently bound to the institution root (`campus_id = NULL`), leaving campus-scoped coordination unsupported at creation.

---

## 7. Invitation Lifecycle and Security Findings

| Invitation Security Requirement | Status | Technical Reality in PEVN |
|---|---|---|
| **Cryptographically secure token** | **NOT IMPLEMENTED** | No coordinator token is generated; creation uses plaintext initial password. |
| **Token expiration & single-use** | **NOT IMPLEMENTED** | No invitation record exists to track `expires_at` or `is_used`. |
| **Token hashing (SHA-256)** | **NOT IMPLEMENTED** | No table stores hashed tokens. |
| **Invitation URL generation** | **NOT IMPLEMENTED** | No invitation URL helper exists for coordinators (unlike `generate_invitation_link` for territorial admins/rectors). |
| **Development-only safe invitation link** | **NOT IMPLEMENTED** | No dev link returned in coordinator response. |
| **Self-activation via acceptance** | **NOT IMPLEMENTED** | Coordinators are immediately marked `is_active=True` upon creation. |

---

## 8. Coordinator Portal and Module Access Matrix

When a Coordinator account is provisioned directly in the backend and logs in, their access to frontend modules is as follows:

| Module / Screen | URL Path | Backend Authorization | Frontend Guard | Actual Experience |
|---|---|---|---|---|
| **Dashboard** | `/admin/dashboard` | 200 OK | Allowed (`rector`, `coordinator`, `super_admin`) | **FUNCTIONAL** (Institutional KPI cards displayed) |
| **Academic Hub** | `/academic` | 200 OK | Allowed | **FUNCTIONAL** |
| **Academic Years** | `/academic#years` | 200 OK | Allowed | **FUNCTIONAL** (Read/Write if delegation enabled) |
| **Academic Periods** | `/academic#periods` | 200 OK | Allowed | **FUNCTIONAL** (Read/Write if delegation enabled) |
| **Grades & Subjects** | `/academic#grades` | 200 OK | Allowed | **FUNCTIONAL** |
| **Teachers** | `/academic#teachers` | 200 OK | Allowed | **FUNCTIONAL** (Can provision teachers) |
| **Students & Enrollments** | `/academic#students` | 200 OK | Allowed | **FUNCTIONAL** (Can provision students) |
| **Institution Settings** | `/academic#settings` | 403 Forbidden | Rector only | **BLOCKED** (Correctly restricted) |
| **Territorial Centers** | `/admin/territorial` | 403 Forbidden | Hidden | **BLOCKED** (Correctly restricted) |

---

## 9. Reproduced Defects and Root Cause Analysis

### Defect 1: Operator Cannot Find Coordinator Assignment in Rector Portal
- **Symptom:** Rector logs in, opens Academic Hub or Admin menus, but finds no button or tab to manage or invite Coordinators.
- **Root Cause:** [AcademicHub.tsx](file:///frontend/src/pages/academic/AcademicHub.tsx) lacks a tab and view component for Coordinators. No frontend client calls `GET/POST /api/v1/coordinators`.
- **Classification:** `FRONTEND GAP`.

### Defect 2: Coordinator Creation Bypasses Invitation Security Standard
- **Symptom:** Coordinator onboarding does not follow the secure single-use invitation pattern implemented for Rectors, Department Admins, and Municipality Admins.
- **Root Cause:** No `CoordinatorInvitation` model exists. `CoordinatorService.create_coordinator()` requires the Rector to supply a raw password directly.
- **Classification:** `SECURITY ARCHITECTURE / INVITATION LIFECYCLE DEFECT`.

### Defect 3: Inability to Assign Campus Scope
- **Symptom:** Rector cannot designate which sede/campus a coordinator manages.
- **Root Cause:** `CoordinatorCreateRequest` schema lacks `campus_id` field.
- **Classification:** `BACKEND SCHEMA DEFECT`.

---

## 10. Test Commands, Actual Results, and Coverage Evidence

### 10.1 Targeted Coordinator Backend Tests
```bash
pytest tests/test_nta08_authority_chain.py -k "coordinator" -v
```
**Actual Result:**
```
tests/test_nta08_authority_chain.py::test_06_rector_provisions_coordinator PASSED [ 16%]
tests/test_nta08_authority_chain.py::test_09_coordinator_provisions_teacher PASSED [ 33%]
tests/test_nta08_authority_chain.py::test_10_coordinator_provisions_student PASSED [ 50%]
tests/test_nta08_authority_chain.py::test_21_coordinator_cannot_create_coordinator PASSED [ 66%]
tests/test_nta08_authority_chain.py::test_22_coordinator_cannot_create_territorial_admins PASSED [ 83%]
tests/test_nta08_authority_chain.py::test_29_coordinator_management_operations_blocked_when_delegation_disabled PASSED [100%]

====================== 6 passed, 24 deselected in 15.97s ======================
```

### 10.2 Regression Suite (Academic Period Templates & Invitation URLs)
```bash
pytest tests/test_nta10_r7_academic_period_templates.py tests/test_nta10_r6_invitation_urls.py tests/test_academic_workflows_rector.py -v
```
**Actual Result:**
```
============================= 27 passed in 47.60s =============================
```

### 10.3 Frontend Role Navigation Test
```bash
npm run test:run -- src/test/RoleNavigationFunctional.test.tsx
```
**Actual Result:**
```
✓ renders Academic Management cards for Rector & Coordinator
Test Files  1 passed (1)
Tests  1 passed (1)
```

---

## 11. Proposed Implementation Roadmap (To Unblock Flow)

To transition from `BLOCKED` to `PASS`, the following minimal implementation plan is submitted for operator authorization:

1. **Database Migration (`032_coordinator_invitations.py`):**
   - Create table `coordinator_invitations` with:
     `id (UUID)`, `email`, `first_name`, `last_name`, `institution_id`, `campus_id (nullable)`, `token_hash`, `expires_at`, `is_used`, `created_at`.
2. **Backend Service & API Alignment:**
   - Extend `CoordinatorInvitation` model in [invitation.py](file:///backend/app/models/invitation.py).
   - Update [POST /api/v1/coordinators](file:///backend/app/api/v1/endpoints/coordinators.py) to issue an invitation token (SHA-256 hashed), supporting `campus_id`, returning safe invitation link in development.
   - Update `POST /api/v1/auth/verify-invitation` and `POST /api/v1/auth/accept-invitation` to accept coordinator tokens and create user with `role="coordinator"`, `institution_id`, and `campus_id`.
3. **Frontend Implementation:**
   - Create `frontend/src/services/coordinator.ts` and `frontend/src/types/coordinator.ts`.
   - Add `"coordinators"` tab in [AcademicHub.tsx](file:///frontend/src/pages/academic/AcademicHub.tsx).
   - Create `CoordinatorsView.tsx` with:
     - Coordinator list table (name, email, campus, status, actions).
     - "Invitar Coordinador" modal (email, first name, last name, document, optional campus selector).
     - Secure invitation link dialog (copy link in development).

---

## 12. Manual Acceptance Checklist (For Operator)

- [ ] Confirm Rector can log in and view Academic Hub.
- [ ] Confirm presence of `coordinator_delegation_enabled` toggle in Academic Hub -> Settings.
- [ ] Confirm Coordinator cannot modify institutional settings or access territorial admin views.
- [ ] Review and approve Proposed Implementation Roadmap to unblock Coordinator Invitation Flow.

---

## 13. Files Changed, Rollback & Git Status

### Files Changed in this Audit:
- `docs/reports/PEVN_NTA10_R8_ACADEMIC_COORDINATOR_ROLE_AND_INVITATION_AUDIT.md` (Created).

### Git Status Confirmation:
- Zero commits performed.
- Zero git pushes performed.
- All untracked and modified files from previous tasks remain completely preserved.

---

## Certification Exit Gate: `BLOCKED`
**Justification:** The `ACADEMIC_COORDINATOR` role and its operational permissions are fully defined in the backend RBAC core, but the Rector-facing management interface is missing from the frontend, and the secure invitation lifecycle (`coordinator_invitations` table, token hashing, and self-activation) has not been implemented. Operator authorization is required to proceed with the proposed implementation plan.
