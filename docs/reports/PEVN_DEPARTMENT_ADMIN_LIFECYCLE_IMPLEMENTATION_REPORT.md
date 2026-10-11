# PEVN — DEPARTMENT ADMINISTRATOR LIFECYCLE & TERRITORIAL PROVISIONING
## Technical Implementation & Governance Reconciliation Report

**Document Reference:** `docs/reports/PEVN_DEPARTMENT_ADMIN_LIFECYCLE_IMPLEMENTATION_REPORT.md`  
**Standard:** AI Software Factory v1.2 / Territorial RBAC Governance Suite  
**Scope:** DEPARTMENT_ADMIN Lifecycle & Territorial Provisioning Architecture  
**Status:** IMPLEMENTATION COMPLETE & VERIFIED  
**Date:** 2026-10-05  

---

## 1. Executive Summary

In compliance with the **PEVN Department Administrator Lifecycle & Territorial Provisioning Specification**, the complete, secure, auditable lifecycle and territorial provisioning subsystem for `DEPARTMENT_ADMIN` users has been implemented, validated, and reconciled.

Higher-level administrators (`SUPER_ADMIN` and `NATIONAL_ADMIN`) are now equipped with full, controlled administrative capabilities to:
1. Provision new `DEPARTMENT_ADMIN` accounts bound to a canonical Colombian department from the `departments` table.
2. Select Colombian departments dynamically via backend APIs without hardcoding department datasets in React.
3. Edit administrator identity and profile attributes under strict validation rules.
4. Perform controlled, auditable department reassignments with automatic active session token invalidation.
5. Execute operational status transitions (activation and deactivation) with instant access revocation.
6. Search and filter departmental administrators across departments and operational statuses.
7. Enforce strict Anti-IDOR and territorial isolation boundaries across institutions, users, and analytics.

The certified baseline RBAC model for `DEPARTMENT_ADMIN` (exactly 17 read-only atomic permissions, zero wildcards, level 80) and higher roles (`SUPER_ADMIN` level 100 with `*:*`, `NATIONAL_ADMIN` level 90 with 30 canonical permissions + 3 lifecycle permissions) remains intact and certified.

---

## 2. Existing Architecture Inspected

Prior to implementation, the architecture and data model were comprehensively audited:
- **Territorial Scope Persistence:** Migration `024_user_roles_department_scope.py` introduced `user_roles.department_id` with foreign key `fk_user_roles_department_id_departments` referencing `departments.id`.
- **Identity & Role Resolution:** `AuthService.build_auth_context(user)` dynamically inspects `user.user_roles` where `role.name == "department_admin"` and resolves `OrganizationalScope(department_id=str(ur.department_id))`.
- **Dynamic Scope Resolution:** `deps.get_current_user` loads `User` with relationships `user_roles.role` and `user_roles.department` live from PostgreSQL on every request. Therefore, database changes to `user_roles.department_id` instantly reflect on subsequent authenticated requests.
- **Session Tracking:** Active sessions maintain opaque refresh tokens in `refresh_tokens`. Setting `RefreshToken.is_revoked = True` prevents token renewal under former territorial scopes.
- **Catalog vs Operational Data Distinction:** Official reference data in `official_institution_catalog` and `official_campus_catalog` remains distinct from provisioned tenants in `departments`, `municipalities`, `institutions`, and `campuses`.

---

## 3. Files Modified

| File Path | Description of Changes |
|---|---|
| [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py) | Added canonical atomic permissions `("department_admins", "read")`, `("department_admins", "create")`, `("department_admins", "update")` and linked them to `NATIONAL_ADMIN`. |
| [`backend/app/audit/interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py) | Added audit event types: `DEPARTMENT_ADMIN_CREATED`, `UPDATED`, `DEPARTMENT_CHANGED`, `ACTIVATED`, `DEACTIVATED`. |
| [`backend/app/api/v1/router.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/router.py) | Registered `/api/v1/department-admins` router and `/api/v1/departments` canonical catalog alias router. |
| [`frontend/src/types/index.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/types/index.ts) | Exported department administrator TypeScript type contracts. |
| [`frontend/src/App.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/App.tsx) | Registered `/admin/department-admins` protected route guarded by `<RequireAuth roles={['superadmin', 'national_admin']}>`. |
| [`frontend/src/layouts/RootLayout.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/layouts/RootLayout.tsx) | Added navigation link `Admin Dptal.` visible strictly to `superadmin` and `national_admin`. |

---

## 4. Files Created

| File Path | Description of Component |
|---|---|
| [`backend/app/schemas/department_admin.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/schemas/department_admin.py) | Pydantic validation schemas for Department Admin creation, update, reassignment, status toggle, and response serializing. |
| [`backend/app/services/department_admin_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/app/services/department_admin_service.py) | Domain service encapsulating transaction management, Argon2id credential hashing, canonical department validation, session revocation, and audit logging. |
| [`backend/app/api/v1/endpoints/department_admins.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa PEVN/Plataforma Educativa Virtual Nacional PEVN/backend/app/api/v1/endpoints/department_admins.py) | REST controller implementing `GET /departments`, `GET /department-admins`, `POST /department-admins`, `PATCH /{id}`, `PATCH /{id}/department`, and `PATCH /{id}/status`. |
| [`frontend/src/types/departmentAdmin.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa PEVN/Plataforma Educativa Virtual Nacional PEVN/frontend/src/types/departmentAdmin.ts) | TypeScript interfaces matching backend response models. |
| [`frontend/src/services/departmentAdmin.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa PEVN/Plataforma Educativa Virtual Nacional PEVN/frontend/src/services/departmentAdmin.ts) | Axios API client for departmental administrative operations. |
| [`frontend/src/pages/admin/DepartmentAdminsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa PEVN/Plataforma Educativa Virtual Nacional PEVN/frontend/src/pages/admin/DepartmentAdminsView.tsx) | Professional React administration interface with real-time KPI cards, dynamic department selector, search, filters, and modal workflows. |
| [`backend/scratch/verify_department_admin_lifecycle.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa PEVN/Plataforma Educativa Virtual Nacional PEVN/backend/scratch/verify_department_admin_lifecycle.py) | Complete automated test suite covering all 17 mandatory security test scenarios against the FastAPI ASGI app. |

---

## 5. Files Not Modified and Rationale

- **`backend/app/core/security/authorization.py`**: Not modified. The certified `CentralizedAuthorizationService` already correctly compares `actor_scope.department_id` against `target_scope.department_id` and blocks cross-department requests.
- **`backend/app/models/role.py`**: Not modified. The `UserRole.department_id` foreign key column and relationship were previously established by migration `024`.
- **`backend/app/cli/create_department_admin.py`**: Preserved as CLI fallback without alterations.
- **DEPARTMENT_ADMIN certified permissions list**: Not modified. `DEPARTMENT_ADMIN` retains exactly 17 read-only permissions with zero wildcard permissions.

---

## 6. Database and Migration Policy

- **No Unnecessary Migrations Created:** Database schema inspection confirmed migration `024_user_roles_department_scope.py` already provisions:
  - Column: `user_roles.department_id` (`UUID`, nullable, foreign key referencing `departments.id`).
  - Index: `ix_user_roles_department_id` on `user_roles(department_id)`.
- **Canonical Department Catalog:** Operates on the existing `departments` table (33 canonical entities, DANE codes `05` through `99`).
- **Multiple Administrators Supported:** No artificial single-admin constraint is placed on departments. Multiple administrators (e.g. `admin.atlantico.01`, `admin.atlantico.02`) can be provisioned for the same departmental jurisdiction.

---

## 7. API Endpoints Specification

### 1. `GET /api/v1/departments` (and `/api/v1/department-admins/departments`)
- **Summary:** List active canonical Colombian departments for UI selectors.
- **Authorization:** Authenticated user with `department_admins:read` or national scope.
- **Response:** List of `{ id: UUID, code: str, name: str, display_label: str }`.

### 2. `GET /api/v1/department-admins`
- **Summary:** List departmental administrators with filtering and pagination.
- **Query Params:** `department_id`, `is_active`, `search`, `page`, `page_size`.
- **Authorization:** `require_permission("department_admins", "read")` (`SUPER_ADMIN`, `NATIONAL_ADMIN`).

### 3. `GET /api/v1/department-admins/{user_id}`
- **Summary:** Retrieve single departmental administrator detail.
- **Authorization:** `require_permission("department_admins", "read")`.

### 4. `POST /api/v1/department-admins`
- **Summary:** Provision a new `DEPARTMENT_ADMIN` user with transactional territorial binding.
- **Request Body:**
  ```json
  {
    "first_name": "string",
    "last_name": "string",
    "email": "user@sed.gov.co",
    "username": "admin.username",
    "password": "optional_initial_password",
    "department_id": "UUID"
  }
  ```
- **Security:** Ignores any client-supplied `role` field; enforces `SystemRole.DEPARTMENT_ADMIN` server-side.
- **Authorization:** `require_permission("department_admins", "create")`.

### 5. `PATCH /api/v1/department-admins/{user_id}`
- **Summary:** Update profile details (`first_name`, `last_name`, `email`, `document_number`, `is_active`).
- **Authorization:** `require_permission("department_admins", "update")`.

### 6. `PATCH /api/v1/department-admins/{user_id}/department`
- **Summary:** Explicitly reassign the administrator to another Colombian department.
- **Request Body:** `{"new_department_id": "UUID", "reason": "optional_string"}`.
- **Security:** Validates target department existence; rebinds `user_roles.department_id`; revokes active refresh tokens.
- **Authorization:** `require_permission("department_admins", "update")`.

### 7. `PATCH /api/v1/department-admins/{user_id}/status`
- **Summary:** Activate or deactivate a departmental administrator account.
- **Request Body:** `{"is_active": false, "reason": "optional_string"}`.
- **Security:** On deactivation, updates `users.is_active` and `user_roles.is_active` and revokes all active session refresh tokens.
- **Authorization:** `require_permission("department_admins", "update")`.

---

## 8. Authorization Model & Ownership Matrix

| Actor | List Admins | Create Admin | Edit Profile | Reassign Dept | Toggle Status | Access Cross-Dept Data |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`SUPER_ADMIN`** (Level 100) | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed (National Scope) |
| **`NATIONAL_ADMIN`** (Level 90) | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed (National Scope) |
| **`DEPARTMENT_ADMIN`** (Level 80) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | **BLOCKED (403)** |
| **Institutional Roles** (Rector, Docente, etc.) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | **BLOCKED (403)** |

---

## 9. Department Assignment Mechanism

- The frontend department selector is populated strictly from `GET /api/v1/departments`.
- The user interface displays human-readable names: `[ 08 — ATLÁNTICO ]`.
- Only canonical department UUIDs are submitted to the backend API.
- The backend validates department existence via `select(Department.id).where(Department.id == dept_id)`.
- The relationship is stored authoritatively as:
  ```text
  users.id <--- user_roles.user_id
                 user_roles.role_id (role: department_admin)
                 user_roles.department_id ---> departments.id
  ```
- Territorial scope resolution in `AuthService`:
  ```python
  if ur.department_id and ur.role and ur.role.name == "department_admin":
      scope = OrganizationalScope(
          country_code="CO",
          department_id=str(ur.department_id),
          municipality_id=None,
          institution_id=None,
      )
  ```

---

## 10. Audit Trail Implementation

All sensitive lifecycle events are logged to the PostgreSQL `audit_logs` table via `IAuditService`:
- `department_admin.created`: Logs actor ID, target user ID, username, email, department UUID, DANE code, and canonical name.
- `department_admin.updated`: Logs actor ID, target user ID, modified fields.
- `department_admin.department_changed`: Logs actor ID, target user ID, `previous_department_id`, `previous_department_code`, `new_department_id`, `new_department_code`, and justification reason.
- `department_admin.activated` & `department_admin.deactivated`: Logs actor ID, target user ID, status, and reason.

Credentials, passwords, and tokens are permanently sanitized before database insertion (`***REDACTED***`).

---

## 11. Frontend Implementation

- **View:** `frontend/src/pages/admin/DepartmentAdminsView.tsx`.
- **Route:** `/admin/department-admins`, integrated into `frontend/src/App.tsx`.
- **Navigation:** Added to `frontend/src/layouts/RootLayout.tsx` for `superadmin` and `national_admin`.
- **Design:**
  - KPI Cards: Total Administradores, Departamentos con Cobertura, Activos, Inactivos.
  - Search Input: By full name, username, or email.
  - Department Selector Filter: Populated dynamically from backend API.
  - Status Filter: All / Active / Inactive.
  - Interactive Table: Full Name, Username, Institutional Email, Department (DANE Badge), Status Badge, Action Buttons.
  - Action Modals: Provisioning modal, Edit Profile modal, Department Reassignment modal (with security warning), Status Confirmation modal.
- **Validation:** Frontend build passed with zero TypeScript errors (`tsc -b && vite build` built in 5.04s).

---

## 12. Session & Token Consistency After Reassignment

1. When a `DEPARTMENT_ADMIN` is reassigned to another department or deactivated:
   ```python
   await self._session.execute(
       update(RefreshToken)
       .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
       .values(is_revoked=True)
       .execution_options(synchronize_session=False)
   )
   ```
2. The user's active refresh tokens are immediately revoked.
3. Because `deps.get_current_user` reloads `User` and `UserRole.department` live from PostgreSQL on every authenticated request, subsequent requests instantly resolve the new department scope without relying on JWT claim regeneration.
4. Attempted access to institutions from the former department is blocked immediately with HTTP 403 Forbidden.

---

## 13. Security Test Results Summary

All 17 mandatory security test scenarios from Section 14 were executed by `backend/scratch/verify_department_admin_lifecycle.py`:
- **TEST 01:** PASS (Superadmin creates Bogotá admin, 201).
- **TEST 02:** PASS (NationalAdmin creates Atlántico admin, 201).
- **TEST 03:** PASS (NationalAdmin creates Cundinamarca admin, 201).
- **TEST 04:** PASS (DepartmentAdmin creating DepartmentAdmin rejected with 403).
- **TEST 05:** PASS (DepartmentAdmin changing own department rejected with 403).
- **TEST 06:** PASS (DepartmentAdmin Bogotá modifying Atlántico admin rejected with 403).
- **TEST 07:** PASS (NationalAdmin reassigns department Bogotá -> Cundinamarca, audit logged).
- **TEST 08:** PASS (Nonexistent department_id rejected with 404, no DB mutation).
- **TEST 09:** PASS (Malformed department_id rejected with 422 validation error).
- **TEST 10:** PASS (Pretending to be superadmin in body ignored; server enforces department_admin).
- **TEST 11:** PASS (Atlántico admin resolves `is_department=True`, Atlántico UUID).
- **TEST 12:** PASS (Atlántico admin requesting Bogotá institution blocked with 403).
- **TEST 13:** PASS (Atlántico admin requesting Bogotá user blocked with 403).
- **TEST 14:** PASS (Atlántico admin analytics strictly scoped to Atlántico, 0 leakage).
- **TEST 15:** PASS (Deactivated admin login fails with 401).
- **TEST 16:** PASS (Reassigned admin has Cundinamarca scope; Bogotá institution returns 403).
- **TEST 17:** PASS (Existing certified Bogotá admin has 17 perms, 0 wildcards, DANE 11).

**Result: 17 / 17 Tests Passed (100% Pass Rate).**

---

## 14. Regression Test Results

- Executed `pytest tests/test_rbac_governance_and_rector_invitation.py`.
- **Result:** 25 passed in 109.11s.
- **Verification:** Canonical Rector invitations, institutional containment, teacher virtual classrooms, coordinator limits, and national authority remain completely functional with zero regressions.

---

## 15. Manual Acceptance Checklist

- [x] SUPER_ADMIN can create DEPARTMENT_ADMIN.
- [x] NATIONAL_ADMIN can create DEPARTMENT_ADMIN.
- [x] Department is selected from canonical backend data (`GET /api/v1/departments`).
- [x] `department_id` is persisted in `user_roles`.
- [x] DEPARTMENT_ADMIN receives exactly the existing certified role (`department_admin`, level 80).
- [x] DEPARTMENT_ADMIN retains 17 read-only permissions.
- [x] No wildcard permission is introduced.
- [x] DEPARTMENT_ADMIN cannot create another DEPARTMENT_ADMIN.
- [x] DEPARTMENT_ADMIN cannot change their own department.
- [x] Department reassignment requires higher-level authorization (`SUPER_ADMIN` or `NATIONAL_ADMIN`).
- [x] All sensitive operations are audited (`created`, `updated`, `department_changed`, `activated`, `deactivated`).
- [x] Deactivation works and immediately revokes active sessions.
- [x] React UI does not hardcode departments.
- [x] New administrator receives correct territorial scope after login (`is_department=True`, `is_national=False`).
- [x] Cross-department access remains blocked with HTTP 403.
- [x] Existing Bogotá DEPARTMENT_ADMIN behavior remains secure and intact.
- [x] No regression is introduced in NATIONAL_ADMIN.
- [x] No regression is introduced in SUPER_ADMIN.
- [x] No duplicate authorization mechanism was introduced.
- [x] No unnecessary database migration was created.

---

## 16. Known Limitations & Next Phase Recommendations

1. **Self-Service Password Reset for Departmental Admins:** Currently, an initial password is generated or supplied by the national administrator. Future iterations can integrate the single-use cryptographic invitation workflow (identical to the rector invitation system) so departmental administrators set their own credentials.
2. **Bulk Territorial Provisioning:** Future phases can support batch provisioning of all 33 Colombian departmental secretariats via signed administrative batches.
