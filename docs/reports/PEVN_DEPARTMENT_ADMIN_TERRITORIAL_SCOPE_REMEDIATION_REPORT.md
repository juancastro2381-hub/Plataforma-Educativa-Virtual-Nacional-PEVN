# PEVN — CERTIFIED TERRITORIAL SCOPE REMEDIATION REPORT
## DEPARTMENT_ADMIN — DANE 11 — BOGOTÁ D.C.

**Document ID:** `PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_REMEDIATION_REPORT.md`  
**Execution Date:** 2026-10-05  
**Evaluation Mode:** Minimum Technical Remediation Verified & Certified  
**Target Actor:** `department_admin` (`department_admin@pevn.edu.co`)  
**Target Jurisdiction:** DANE 11 — CAPITAL BOGOTÁ, D.C. (`7b774116-56f1-4199-ac63-ff646e7e327b`)  
**Gate Status:** **PASS**  

---

## 1. Executive Summary & Root Cause

### 1.1 Root Cause Analysis (Pre-Remediation)
The territorial scope audit (`PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_AUDIT.md`) established a critical multi-tenancy vulnerability resulting in a **FAIL** gate:
- The `department_admin` user was provisioned for DANE Department 11, but the territorial assignment was recorded exclusively in JSON audit metadata (`audit_logs.metadata`).
- The relational data model lacked a column linking `user_roles` to `departments.id`.
- Because departmental administrators are territorial (not institutional), `user.institution_id` was `None`.
- Consequently, `AuthService.build_auth_context()` defaulted both `department_id` and `institution_id` to `None`.
- In `OrganizationalScope`, `department_id=None` and `institution_id=None` caused `scope.is_national()` to evaluate to `True`.
- This conferred unintended national read access on `department_admin`, allowing cross-department enumeration of institutions, users, and national metrics.

### 1.2 Remediation Objective & Architectural Constraints
Without altering the certified RBAC model (role hierarchy levels, canonical permissions, or the 17 read-only permissions of `DEPARTMENT_ADMIN`), the minimum technical remediation was authorized and executed:
1. **Database Relational Persistence:** Persisted `department_id` on `user_roles` with a foreign key to `departments.id`.
2. **Idempotent Provisioning:** Bound `department_admin` to DANE 11 (`7b774116-56f1-4199-ac63-ff646e7e327b`).
3. **Server-Side Auth Context Resolution:** Constructed `OrganizationalScope` with `is_national=False`, `is_department=True`, and `department_id=<UUID>`.
4. **Authorization Boundary Hardening:** Hardened `scope_contains()` to prevent departmental actors from matching targets outside their jurisdiction.
5. **Endpoint Hardening:** Enforced departmental constraints on `GET /institutions`, `GET /institutions/{id}`, `GET /users`, `GET /users/{id}`, and Territorial Analytics endpoints.
6. **Zero Token Bloat:** Maintained server-side database authoritative evaluation without modifying JWT claims.

---

## 2. Database Schema Changes & Migration

### 2.1 Alembic Migration
- **Migration Script:** `backend/migrations/versions/024_user_roles_department_scope.py`
- **Revises:** `023_rector_invitations_and_roles`
- **Target Table:** `user_roles`
- **Column Added:**
  ```sql
  ALTER TABLE user_roles ADD COLUMN department_id UUID NULL REFERENCES departments(id) ON DELETE SET NULL;
  CREATE INDEX ix_user_roles_department_id ON user_roles (department_id);
  ```
- **Migration Properties:**
  - Fully backward compatible and non-destructive.
  - Nullable for roles without departmental scope (e.g., national, superadmin, institutional roles).
  - Preserves referential integrity with foreign key to `departments.id`.
  - Added index `ix_user_roles_department_id` for fast auth context resolution.

### 2.2 SQLAlchemy Model Update
- **File Modified:** `backend/app/models/role.py`
- **Model:** `UserRole`
- **Fields Added:**
  - `department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)`
  - `department = relationship("Department", foreign_keys=[department_id], lazy="selectin")`

---

## 3. Idempotent Provisioning & Test Account Update

### 3.1 Provisioning Flow Update
- **File Modified:** `backend/app/cli/create_department_admin.py`
- **Logic:**
  1. Resolves `department_code = "11"` against `departments.code` to retrieve `departments.id`.
  2. If `user_roles` record already exists, updates `user_role.department_id = department.id` idempotently.
  3. If not present, creates the role assignment with `department_id = department.id`.
  4. Records structured audit logs (`action="cli.create_department_admin"` or `"cli.update_department_admin"`).

### 3.2 Database Verification of `department_admin`
Executed direct database verification query:
```sql
SELECT u.username, r.name as role_name, ur.department_id, d.code as dept_code, d.name as dept_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN departments d ON ur.department_id = d.id
WHERE u.username = 'department_admin';
```
**Result:**
- `username`: `department_admin`
- `role_name`: `department_admin`
- `department_id`: `7b774116-56f1-4199-ac63-ff646e7e327b`
- `dept_code`: `11`
- `dept_name`: `CAPITAL BOGOTÁ, D.C.`
- Active role assignments: Exactly 1.
- Wildcards: 0 (`*:*` absent).
- Permissions: Exactly 17 read-only permissions.

---

## 4. Auth Context & Scope Resolution Changes

### 4.1 Schema Update
- **File Modified:** `backend/app/schemas/auth.py`
- **Class:** `ScopeResponse`
  - Added `is_department: bool = False`
  - Added `jurisdiction_name: str | None = None`

### 4.2 Auth Service Resolution
- **File Modified:** `backend/app/services/auth_service.py`
- **Methods:**
  - `build_auth_context(user)`:
    - Traverses active user roles to find `ur.department_id`.
    - If `department_id` is present and role is departmental:
      ```python
      scope = OrganizationalScope(
          country_code="CO",
          department_id=department_id_str,
          municipality_id=None,
          institution_id=None,
          campus_id=None,
      )
      ```
    - `scope.is_national()` evaluates to `False`.
    - `scope.is_department()` evaluates to `True`.
  - `build_user_me_response(user, auth_context)`:
    - Includes `is_department=True` and `jurisdiction_name="CAPITAL BOGOTÁ, D.C."` in the API response.

### 4.3 Eager Loading in Dependency Injection
- **File Modified:** `backend/app/api/deps.py`
- **Function:** `get_current_user`:
  - Updated loader options to eagerly load `selectinload(UserRole.department)` alongside `UserRole.role`.
  - Guarantees async thread safety and prevents lazy-loading greenlet errors during `/auth/me` context building.

---

## 5. Authorization Boundary & Endpoint Hardening

### 5.1 Authorization Core (`scope_contains`)
- **File Modified:** `backend/app/core/security/authorization.py`
- **Function:** `scope_contains(actor_scope, target_scope)`
  - Hardened: If `actor_scope.is_department()`:
    - Verifies `target_scope.department_id is not None` and `str(actor_scope.department_id) == str(target_scope.department_id)`.
    - If `target_scope.department_id` does not match, returns `False`.
    - Departmental actors cannot contain national scopes, foreign department scopes, or institutions in other departments.

### 5.2 Institutions Endpoint Hardening
- **File Modified:** `backend/app/api/v1/endpoints/institutions.py`
- **`GET /api/v1/institutions`:**
  - If `auth.scope.is_department()`:
    - If client provides `department_id` query parameter that differs from actor's jurisdiction, endpoint immediately rejects request with `403 Forbidden` (`PERMISSION_DENIED`).
    - Server-side enforces `effective_department_id = actor_dept_uuid`.
    - Client cannot escape territorial boundary by tampering with query parameters.
- **`GET /api/v1/institutions/{id}`:**
  - Anti-IDOR Enforcement: Resolves institution's municipality and department.
  - Builds `target_scope = OrganizationalScope(department_id=str(institution.municipality.department_id), ...)`.
  - Calls `authorization_service.require(..., target_scope=target_scope)`.
  - Direct object access to institutions in other departments (e.g. Cundinamarca DANE 25) is denied with `403 Forbidden`.

### 5.3 Users Endpoint & Domain Service Hardening
- **Files Modified:**
  - `backend/app/services/user_service.py`
  - `backend/app/api/v1/endpoints/users.py`
- **`UserService.list_users`:**
  - Added support for `department_id` parameter.
  - Performs SQL join: `User -> Institution -> Municipality.department_id`.
  - Filters strictly to users within the specified department.
- **`GET /api/v1/users`:**
  - If `auth.scope.is_department()`:
    - If client requests specific `institution_id`, verifies that institution belongs to the actor's department; otherwise raises `403 Forbidden`.
    - Sets `target_department_id = actor_dept_uuid`.
    - Total users returned is strictly isolated to the department (149 active users in Bogotá vs 190 users nationally).
- **`GET /api/v1/users/{id}`:**
  - Verifies target user's institution belongs to the actor's department; otherwise raises `403 Forbidden`.

### 5.4 Territorial Analytics Hardening
- **File Modified:** `backend/app/services/territorial_analytics_service.py`
- **`GET /api/v1/analytics/territorial/summary`:**
  - Bounded by `OrganizationalScope`.
  - Accurately reports: `scope_level="DEPARTMENT"`, `jurisdiction_name="CAPITAL BOGOTÁ, D.C."`, `total_departments=1`, and metrics restricted to Bogotá (1876 catalog institutions, 29 provisioned).
- **`GET /api/v1/analytics/territorial/departments`:**
  - If `auth.scope.is_department()`: filters query to `dept_code_filter = "11"`.
  - Returns `total_count=1` containing only Bogotá D.C.
  - No unauthorized national department enumeration is permitted.
  - For `NATIONAL_ADMIN`, returns all 33 departments in Colombia.

---

## 6. Frontend Alignment
- **Files Modified:**
  - `frontend/src/types/auth.ts`: Added `is_department?: boolean` and `jurisdiction_name?: string | null` to `ScopeResponse`.
  - `frontend/src/pages/Dashboard.tsx`: Displays:
    - **Nivel de Alcance:** `Departamental`
    - **Jurisdicción:** `CAPITAL BOGOTÁ, D.C.`
  - Consumes dynamic authoritative backend scope without hardcoded values.

---

## 7. Security Test Matrix — Direct Execution Results

All 13 mandatory security test scenarios from Phase 10 were implemented and executed directly against the live backend and database via `backend/scratch/verify_territorial_remediation.py`.

| Test ID | Test Scenario | HTTP Method & Target | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST 1** | Read institutions inside DANE 11 | `GET /api/v1/institutions?department_id=7b774116-...` | 200 OK (32 records) | 200 OK (32 records) | **PASS** |
| **TEST 2** | Read institutions in Cundinamarca (DANE 25) | `GET /api/v1/institutions?department_id=9aea113f-...` | 403 Forbidden (`PERMISSION_DENIED`) | 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 3** | Read institutions outside DANE 11 (tampered UUID) | `GET /api/v1/institutions?department_id=<Random-UUID>` | 403 Forbidden (`PERMISSION_DENIED`) | 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 4** | List institutions without query filter | `GET /api/v1/institutions` | 200 OK (Strictly 32 Bogotá records) | 200 OK (Strictly 32 Bogotá records) | **PASS** |
| **TEST 5** | Tamper query parameter with foreign department | `GET /api/v1/institutions?department_id=9aea113f-...` | 403 Forbidden (Cannot escape boundary) | 403 Forbidden (Cannot escape boundary) | **PASS** |
| **TEST 6A**| Direct read own institution by ID | `GET /api/v1/institutions/2dcc7e47-...` (Bogotá) | 200 OK | 200 OK (`Colegio Departamental B`) | **PASS** |
| **TEST 6B**| Direct read foreign institution by ID (Anti-IDOR) | `GET /api/v1/institutions/1fb1a84a-...` (Cundinamarca)| 403 Forbidden (`PERMISSION_DENIED`) | 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 7** | List users within territorial boundary | `GET /api/v1/users` | 200 OK (149 active Dept 11 users; 0 foreign) | 200 OK (149 Dept 11 users returned) | **PASS** |
| **TEST 8** | Territorial Analytics Summary | `GET /api/v1/analytics/territorial/summary` | `DEPARTMENT`, `CAPITAL BOGOTÁ, D.C.`, 1 Dept | `DEPARTMENT`, `CAPITAL BOGOTÁ, D.C.`, 1 Dept | **PASS** |
| **TEST 9** | Territorial Analytics Department Distribution | `GET /api/v1/analytics/territorial/departments` | `total_count: 1`, `items: ['11']` | `total_count: 1`, `items: ['11']` | **PASS** |
| **TEST 10**| Attempt mutation outside DANE 11 | `PATCH /api/v1/institutions/1fb1a84a-.../status` | 403 Forbidden (`PERMISSION_DENIED`) | 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 11**| Attempt mutation inside DANE 11 | `PATCH /api/v1/institutions/2dcc7e47-.../status` | 403 Forbidden (Read-only role) | 403 Forbidden (Read-only role) | **PASS** |
| **TEST 12**| Verify NATIONAL_ADMIN capabilities | `GET /institutions`, `/analytics/*` | 200 OK, 33 institutions, 33 departments | 200 OK, 33 institutions, 33 departments | **PASS** |
| **TEST 13**| Verify SUPER_ADMIN capabilities | `GET /institutions`, `GET /auth/me` | 200 OK, `roles=['superadmin']`, `perms=['*:*']`| 200 OK, `roles=['superadmin']`, `perms=['*:*']`| **PASS** |

**Summary Result:** 13 of 13 tests passed (100% success rate).

---

## 8. Regression Safety & RBAC Invariance Confirmations

1. **RBAC Model Invariance:**
   - Role definitions, role hierarchy levels, permission definitions, and role-permission mappings were **NOT modified**.
   - No permissions were added to or removed from any canonical role.
2. **SUPER_ADMIN Status:**
   - User `admin_nacional` continues resolving canonical role `superadmin` with wildcard permission `*:*` and unconstrained national authority.
3. **NATIONAL_ADMIN Status:**
   - User `national_admin` continues resolving canonical role `national_admin` with exactly 30 permissions, 0 wildcard permissions, and full national scope across all 33 departments.
4. **DEPARTMENT_ADMIN Status:**
   - User `department_admin` resolves canonical role `department_admin` with exactly 17 read-only permissions and 0 wildcard permissions.
   - Read permissions cannot be used to leak data outside DANE 11.
   - All mutation attempts continue to be rejected with `403 Forbidden`.
5. **Institutional Roles Status:**
   - Institutional users (`rector`, `coordinador`, `docente`, `estudiante`, `acudiente`) continue resolving institutional scopes without regression.
   - Existing pytest test suite `test_rbac_governance_and_rector_invitation.py` passed with 25/25 tests passing (100%).

---

## 9. Controlled Git State

The implementation was performed under strict change control. No commits and no pushes to remote were executed.

### Modified Files:
- `backend/app/api/deps.py`
- `backend/app/api/v1/endpoints/institutions.py`
- `backend/app/api/v1/endpoints/users.py`
- `backend/app/cli/create_department_admin.py`
- `backend/app/core/security/authorization.py`
- `backend/app/models/role.py`
- `backend/app/schemas/auth.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/territorial_analytics_service.py`
- `backend/app/services/user_service.py`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/types/auth.ts`

### Untracked Files (New Assets):
- `backend/migrations/versions/024_user_roles_department_scope.py` (Alembic migration)
- `backend/scratch/verify_territorial_remediation.py` (Automated verification suite)
- `docs/reports/PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_AUDIT.md` (Pre-remediation audit)
- `docs/reports/PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_REMEDIATION_REPORT.md` (This document)

---

## 10. Final Gate Determination

```
================================================================================
GATE STATUS: PASS
================================================================================
```

- **Root Cause Elimination:** Complete. `department_id` is persisted relationally in `user_roles`.
- **Scope Resolution:** Complete. `OrganizationalScope.is_national() == False`, `OrganizationalScope.is_department() == True`.
- **Multi-Tenancy & Anti-IDOR:** Complete. Department boundary is server-side enforced against query tampering and direct object access.
- **RBAC & Regression Integrity:** Complete. 0 modifications to RBAC rules; SUPER_ADMIN, NATIONAL_ADMIN, and institutional roles completely intact.
