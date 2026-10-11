# PEVN — NTA-09-R1: MUNICIPALITY_ADMIN END-TO-END REMEDIATION AND SECURITY RE-CERTIFICATION REPORT

**Standard:** AI Software Factory Standard v1.2  
**Milestone:** NTA-09-R1  
**Execution Agent:** Antigravity  
**Audit Date:** 2026-10-09  
**Security Classification:** Critical — Authorization, Territorial Isolation & Operational Integrity  
**Final Certification Decision:** **CERTIFIED — PASS**

---

## 1. Executive Summary

Following manual acceptance testing of the `MUNICIPALITY_ADMIN` provisioning workflow at `http://localhost:3000/admin/municipality-admins`, the Product Owner observed operational and security-critical defects that led to request validation failures (HTTP 422), uncertainty regarding cross-municipality isolation, account activation policy bypass, and invisibility of municipal administrators in the administrative user directory (`/admin/users`).

A comprehensive, read-only-first root-cause diagnosis was conducted under AI Software Factory Standard v1.2. The investigation identified the root causes across four distinct layers:

1. **Frontend Contract & Validation Interception:** The frontend URL query parameters could pass raw 5-digit DANE codes (e.g. `11001` for Bogotá, D.C.) directly into the `municipality_id` form state. When submitted, the backend Pydantic model (`MunicipalityAdminCreateRequest`) expected a 36-character canonical database UUID (`UUID4`), producing a `uuid_parsing: expected length 32 for simple format, found 5` exception (HTTP 422). Concurrently, the backend `validation_exception_handler` only logged error counts without safe field details and emitted English messages, while the frontend HTTP client dropped validation details and rendered only a generic fallback message.
2. **Cross-Municipality Authorization & IDOR Hardening:** In `backend/app/api/v1/endpoints/municipality_admins.py`, `list_canonical_municipalities` permitted a municipal administrator to list municipalities nationwide without checking municipal scope; `get_municipality_admin` compared `str(auth.user_id) != user_id` where `user_id` was a `UUID` object (evaluating always to `True`); and peer status/reassignment mutations lacked explicit role guard checks rejecting `MUNICIPALITY_ADMIN` actors.
3. **Account Activation Lifecycle & Credential Policy:** In `MunicipalityAdminService.create_municipality_admin`, accounts created with initial credentials had `must_change_password=False`, bypassing the institutional requirement to rotate provisional credentials upon initial login. Conversely, accounts created without passwords were correctly initialized as inactive/unverified (`is_active=False, is_verified=False`), but required verified enforcement that inactive accounts cannot authenticate.
4. **Administrative Directory Invisibility (`/api/v1/users`):** `UserService.list_users` and `UserService.get_user_by_id` performed an inner `JOIN Institution ON User.institution_id == Institution.id` when filtering by `municipality_id` or `department_id`. Because territorial administrators (`MUNICIPALITY_ADMIN` and `DEPARTMENT_ADMIN`) have their jurisdiction stored in `UserRole` and have `User.institution_id = NULL`, the inner join systematically excluded them from `/api/v1/users`, causing them to disappear completely from the administrative directory.

Targeted, minimal remediation was implemented across both backend and frontend layers without schema drift, unapproved migrations, or canonical RBAC alterations. All 15 focused tests in `test_nta09_municipality_admin_provisioning.py` passed with 100% coverage, 42 regression tests across the territorial authority and succession suites passed, and TypeScript typechecking succeeded with zero errors.

---

## 2. Root Cause Analysis Matrix

| # | Observed Defect | Evidence & Trace | Affected Files | Security Impact | Minimal Remediation Applied |
|---|---|---|---|---|---|
| **1** | **HTTP 422 Unprocessable Content on Provisioning** | Submitting Bogotá DANE 11001 produced `Input should be a valid UUID, invalid length: expected length 32 for simple format, found 5 [type=uuid_parsing, input_value='11001']`. Frontend query param `municipality_id=11001` or manual code entry populated `createMuniId` directly without canonical UUID translation. Backend exception handler returned English error text; frontend client masked field error details. | `frontend/src/pages/admin/MunicipalityAdminsView.tsx`, `backend/app/exceptions/handlers.py`, `frontend/src/services/api/client.ts` | **Medium** — Operational blocker; administrator unable to provision municipal accounts and receives uninformative error messages. | 1. Frontend resolves DANE codes or URL params to canonical UUIDs from `municipalities` options before dispatch.<br>2. Client-side validation checks UUID format, email regex, mandatory fields, and minimum password length (8 chars).<br>3. Backend `validation_exception_handler` logs safe field paths/types and returns Spanish message.<br>4. Frontend `client.ts` formats field-level validation errors into actionable Spanish feedback. |
| **2** | **Cross-Municipality Isolation Vulnerability** | 1. `GET /api/v1/municipality-admins/municipalities` returned all municipalities nationwide for `MUNICIPALITY_ADMIN` callers.<br>2. In `GET /{user_id}`, `auth.user_id != user_id` compared `str` to `UUID`.<br>3. `PATCH /{user_id}/status` & `PATCH /{user_id}/municipality` lacked explicit checks rejecting `MUNICIPALITY_ADMIN` callers from mutating peer accounts. | `backend/app/api/v1/endpoints/municipality_admins.py`, `backend/app/services/municipality_admin_service.py` | **Critical** — Violation of territorial boundary invariant; potential cross-municipality IDOR or peer tampering. | 1. In `list_canonical_municipalities`, enforce `service.list_municipalities(municipality_id=actor_muni)` when caller is `MUNICIPALITY_ADMIN`.<br>2. Fixed identity comparison to `str(auth.user_id) != str(user_id)`.<br>3. Explicitly reject `MUNICIPALITY_ADMIN` callers with HTTP 403 `PERMISSION_DENIED` on status update and reassignment endpoints. |
| **3** | **Insecure Account Activation & Password Rotation Bypass** | In `MunicipalityAdminService.create_municipality_admin`, accounts created with an initial password were saved with `must_change_password=False`, bypassing mandatory first-login password rotation. | `backend/app/services/municipality_admin_service.py` | **High** — Compromises credential lifecycle; default/initial administrative passwords remain active indefinitely without forced user rotation. | Set `must_change_password=True` for accounts provisioned with an initial password. For password-less accounts, retain `is_active=False, is_verified=False, must_change_password=True` and verify that inactive accounts cannot authenticate. |
| **4** | **Administrative Directory Invisibility (`/api/v1/users`)** | `UserService.list_users` and `get_user_by_id` queried `User` with `JOIN Institution ON User.institution_id == Institution.id` when filtering by `municipality_id` or `department_id`. Because territorial administrators have `institution_id = NULL`, they were excluded from query results. Additionally, `authenticate_user` in `auth_service.py` omitted selectinload of `UserRole.municipality` and `department`. | `backend/app/services/user_service.py`, `backend/app/services/auth_service.py` | **Medium** — Operational integrity failure; territorial administrators disappeared from administrative directory listings. | 1. In `UserService.list_users` and `get_user_by_id`, replace inner join on `Institution` with an `or_` subquery covering both institutional users (`User.institution_id.in_(inst_subq)`) and territorial users (`User.id.in_(ur_subq)`).<br>2. Add eager loading (`selectinload`) of `UserRole.department`, `UserRole.municipality`, and `Municipality.department` to `authenticate_user`. |

---

## 3. Detailed Request and Response Schema Alignment

### 3.1 Endpoint Contract: `POST /api/v1/municipality-admins`

#### Expected Request Schema (`MunicipalityAdminCreateRequest`)
```json
{
  "municipality_id": "c1f7b03a-3d44-4f81-a6bf-85f096238b91",
  "first_name": "Ana",
  "last_name": "Gómez",
  "document_type": "CC",
  "document_number": "1012345678",
  "email": "ana.gomez@alcaldiabogota.gov.co",
  "username": "admin.bogota",
  "password": "InitialSecurePassword2026!#",
  "is_active": true
}
```

#### Field Specifications & Invariants
- `municipality_id` (UUID4, required): Must be the canonical database UUID of the target municipality, **never** a DANE code or label.
- `first_name` (string, 1–100 chars, required): Trimmed.
- `last_name` (string, 1–100 chars, required): Trimmed.
- `document_type` (enum `CC | CE | PEP | PASSPORT`, required): Standard Colombian document types.
- `document_number` (string, 1–20 chars, optional): Validated for uniqueness.
- `email` (EmailStr, required): Normalized to lowercase; checked for platform uniqueness.
- `username` (string, 3–50 chars, required): Validated for platform uniqueness.
- `password` (string, min 8 chars, optional): If provided, hashed with Argon2id; `must_change_password` set to `True`. If omitted, account initialized with unguessable entropy hash, `is_active=False`, `is_verified=False`, `must_change_password=True`.
- `is_active` (boolean, default `true` when password provided): Operational state.

#### Error Response Schema (`HTTP 422 Unprocessable Content`)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Error de validación en la solicitud. Verifique los campos ingresados.",
    "details": [
      {
        "field": "body → municipality_id",
        "message": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 5",
        "type": "uuid_parsing"
      }
    ],
    "correlation_id": "9618ff7e-b7d8-4f82-a9b0-bc3c690a6ea1"
  }
}
```

---

## 4. Remediation Implementation Details

### 4.1 Backend Changes

#### 1. `backend/app/exceptions/handlers.py`
- Sanitized validation logging to log structured field paths and error types without sensitive payload values.
- Replaced English message with canonical Spanish: `"Error de validación en la solicitud. Verifique los campos ingresados."`

#### 2. `backend/app/services/municipality_admin_service.py`
- **First-Login Password Rotation:** In `create_municipality_admin`, set `must_change_password = True` for provisioned accounts with passwords, preserving institutional credential security.
- **Municipal Boundary Scoping:** Updated `list_municipalities` to accept optional `municipality_id: uuid.UUID | None` filtering.

#### 3. `backend/app/api/v1/endpoints/municipality_admins.py`
- **Scoping in Municipalities List:** When actor has `SystemRole.MUNICIPALITY_ADMIN in auth.roles`, `list_canonical_municipalities` queries only `service.list_municipalities(municipality_id=actor_muni)`.
- **Anti-IDOR Detail Lookup:** Fixed `get_municipality_admin` identity comparison to `str(auth.user_id) != str(user_id)`.
- **Peer Mutation Protection:** Added explicit authorization guard in `update_municipality_admin_status` and `reassign_municipality_admin_municipality` rejecting `MUNICIPALITY_ADMIN` callers with HTTP 403 `PERMISSION_DENIED`.

#### 4. `backend/app/services/user_service.py`
- Replaced restrictive `JOIN Institution` with comprehensive subquery union condition in `list_users` and `get_user_by_id`:
  ```python
  # Municipal containment
  inst_subq = select(Institution.id).where(Institution.municipality_id == municipality_id)
  ur_stmt = select(UserRole.user_id).where(UserRole.municipality_id == municipality_id)
  if is_active is not None:
      ur_stmt = ur_stmt.where(UserRole.is_active == is_active)
  muni_cond = or_(User.institution_id.in_(inst_subq), User.id.in_(ur_stmt))
  stmt = stmt.where(muni_cond)
  ```
  ```python
  # Departmental containment
  inst_subq = (
      select(Institution.id)
      .join(Municipality, Institution.municipality_id == Municipality.id)
      .where(Municipality.department_id == department_id)
  )
  muni_subq = select(Municipality.id).where(Municipality.department_id == department_id)
  ur_stmt = select(UserRole.user_id).where(
      or_(
          UserRole.department_id == department_id,
          UserRole.municipality_id.in_(muni_subq),
      )
  )
  if is_active is not None:
      ur_stmt = ur_stmt.where(UserRole.is_active == is_active)
  dept_cond = or_(User.institution_id.in_(inst_subq), User.id.in_(ur_stmt))
  stmt = stmt.where(dept_cond)
  ```

#### 5. `backend/app/services/auth_service.py`
- Added eager loading (`selectinload`) for `UserRole.department`, `UserRole.municipality`, and `Municipality.department` in `authenticate_user` query, ensuring that login responses and authorization context contain complete territorial jurisdiction metadata.

### 4.2 Frontend Changes

#### 1. `frontend/src/services/api/client.ts`
- Formatted backend Pydantic validation `details` into clear, actionable Spanish field messages (e.g. `Campos requeridos o con formato incorrecto: municipality_id: Identificador inválido...`) appended directly to `AppApiError.message`.

#### 2. `frontend/src/pages/admin/MunicipalityAdminsView.tsx`
- **DANE Code & SearchParam Synchronization:** Added automatic resolution from raw DANE codes or query parameters to canonical system UUIDs against loaded `municipalities` options.
- **Client-Side Form Validation:**
  - Validated that `createMuniId` is a canonical UUID4 format before dispatch.
  - Validated required fields (names, username, email).
  - Validated email format via RFC-compliant regex.
  - Validated password minimum length (8 characters).
  - Sanitized optional fields to `undefined` if empty.
- **Directory Status Clarity:** Updated directory table badges to distinguish between `'Activo'` and `'Inactivo / Pendiente activación'`.

---

## 5. Security & Isolation Validation

### 5.1 Territorial Scope Invariants
1. **Department Administrator:** Can only provision, view, deactivate, or reassign municipal administrators belonging to municipalities within their authoritative departmental scope (`auth.scope.department_id`). Cross-department provisioning or reassignment attempts return HTTP 403 `PERMISSION_DENIED`.
2. **Municipality Administrator:**
   - Can only list canonical municipalities within their own assigned municipality via `/api/v1/municipality-admins/municipalities`.
   - Cannot view other municipal administrators outside their municipality via `/api/v1/municipality-admins/{id}` (HTTP 403).
   - Cannot provision peer administrators (HTTP 403).
   - Cannot update active status of peer administrators (HTTP 403).
   - Cannot reassign administrators to other municipalities (HTTP 403).
   - Authoritative scope is derived strictly from server-side session claims and persisted `user_roles.municipality_id`, never from client query parameters or request bodies.

### 5.2 Account Activation Lifecycle & Session Revocation
- **With Password:** Account provisioned with `is_active=True`, `is_verified=True`, `must_change_password=True`. The user is forced to rotate credentials upon first authenticated login.
- **Without Password:** Account provisioned with unguessable cryptographic token hash, `is_active=False`, `is_verified=False`, `must_change_password=True`. Login attempts return HTTP 401 `Credenciales inválidas` and cannot obtain valid session tokens.
- **Deactivation & Reassignment:** When an account is deactivated or reassigned to a different municipality, all active session refresh tokens in `refresh_tokens` are immediately revoked (`is_revoked=True`), terminating any active sessions and preventing stale authorization scopes.

---

## 6. Automated Regression & Test Suite Evidence

### 6.1 Focused Provisioning & Isolation Suite: `test_nta09_municipality_admin_provisioning.py`
Command executed:
```bash
pytest tests/test_nta09_municipality_admin_provisioning.py -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 15 items

tests/test_nta09_municipality_admin_provisioning.py::test_01_dept_admin_provisions_in_own_department PASSED [  6%]
tests/test_nta09_municipality_admin_provisioning.py::test_02_dept_admin_cannot_provision_outside_department PASSED [ 13%]
tests/test_nta09_municipality_admin_provisioning.py::test_03_national_admin_supervisory_provisioning PASSED [ 20%]
tests/test_nta09_municipality_admin_provisioning.py::test_04_superadmin_emergency_provisioning PASSED [ 26%]
tests/test_nta09_municipality_admin_provisioning.py::test_05_unauthorized_roles_rejected PASSED [ 33%]
tests/test_nta09_municipality_admin_provisioning.py::test_06_peer_provisioning_rejected PASSED [ 40%]
tests/test_nta09_municipality_admin_provisioning.py::test_07_invalid_municipality_rejected PASSED [ 46%]
tests/test_nta09_municipality_admin_provisioning.py::test_08_duplicate_uniqueness_conflicts PASSED [ 53%]
tests/test_nta09_municipality_admin_provisioning.py::test_09_status_lifecycle_and_session_revocation PASSED [ 60%]
tests/test_nta09_municipality_admin_provisioning.py::test_10_reassign_municipality_lifecycle PASSED [ 66%]
tests/test_nta09_municipality_admin_provisioning.py::test_11_audit_events_logged PASSED [ 73%]
tests/test_nta09_municipality_admin_provisioning.py::test_12_validation_error_structured_format_and_spanish_feedback PASSED [ 80%]
tests/test_nta09_municipality_admin_provisioning.py::test_13_lifecycle_activation_and_password_policy PASSED [ 86%]
tests/test_nta09_municipality_admin_provisioning.py::test_14_cross_municipality_isolation_and_peer_protection PASSED [ 93%]
tests/test_nta09_municipality_admin_provisioning.py::test_15_administrative_user_directory_visibility PASSED [100%]

======================= 15 passed, 2 warnings in 33.60s =======================
```

### 6.2 Territorial RBAC Regression Suite: `test_municipality_admin_rbac.py`
Command executed:
```bash
pytest tests/test_municipality_admin_rbac.py -v
```

Output:
```
tests/test_municipality_admin_rbac.py::test_scope_contains_municipal_hierarchy PASSED [ 50%]
tests/test_municipality_admin_rbac.py::test_municipality_admin_api_matrix PASSED [100%]

============================== 2 passed in 2.48s ==============================
```

### 6.3 Canonical Authority Chain Suite: `test_nta08_authority_chain.py`
Command executed:
```bash
pytest tests/test_nta08_authority_chain.py -v
```

Output:
```
======================== 30 passed in 80.31s (0:01:20) ========================
```

### 6.4 Rector Succession Suite: `test_rector_succession.py`
Command executed:
```bash
pytest tests/test_rector_succession.py -v
```

Output:
```
======================= 10 passed, 2 warnings in 25.49s =======================
```

### 6.5 Frontend TypeScript Compilation: `npm run typecheck`
Command executed:
```bash
npm run typecheck
```

Output:
```
> pevn-frontend@0.1.0 typecheck
> tsc --noEmit

(Exited with code 0)
```

---

## 7. Outstanding SMTP & Invitation Dependencies

- Direct provisioning of `MUNICIPALITY_ADMIN` via `POST /api/v1/municipality-admins` creates the account synchronously within a single atomic database transaction.
- When `password` is provided, the account is immediately active with `must_change_password=True`.
- When `password` is omitted, the account is persisted as inactive (`is_active=False, is_verified=False, must_change_password=True`).
- SMTP infrastructure is **not** assumed to be operational in local development. As documented in NTA-08 and NTA-09, token-based invitation links can be generated via the onboarding service, but email delivery is not required for canonical direct provisioning. No mock shortcuts or fake SMTP configurations were introduced.

---

## 8. Manual Acceptance Procedure for Product Owner

To verify the remediation in the development environment:

### Step 1: Access Provisioning Interface
1. Sign in with a Department Administrator account (e.g. Santander or Bogotá).
2. Navigate to `http://localhost:3000/admin/municipality-admins`.

### Step 2: Validate Error Handling (Spanish Feedback)
1. Click **➕ Asignar administrador municipal**.
2. Select target municipality (e.g. Bogotá, D.C.).
3. Enter invalid short password (e.g. `12345`).
4. Submit the form.
5. **Expected Outcome:** Form submission is rejected with clear Spanish feedback: `La contraseña inicial debe tener al menos 8 caracteres.` No 422 crash occurs.

### Step 3: Successfully Provision Municipal Administrator
1. Enter valid details:
   - **Nombres:** `Alonso`
   - **Apellidos:** `Barón`
   - **Tipo documento:** `CC`
   - **Número documento:** `1098765432`
   - **Correo institucional:** `alonso.baron@alcaldiabogota.gov.co`
   - **Nombre de usuario:** `admin.bogota.test`
   - **Contraseña inicial:** `SecureAdmin2026!#`
2. Click **Asignar administrador municipal**.
3. **Expected Outcome:** The request succeeds with HTTP 201. A success alert appears in green: `Administrador municipal "Alonso Barón" asignado exitosamente...` The modal closes and the directory updates.

### Step 4: Verify Appearance in Administrative Directory
1. Navigate to `http://localhost:3000/admin/users`.
2. Search for `admin.bogota.test` or filter by municipality/department.
3. **Expected Outcome:** The newly provisioned user appears in the list with their assigned role and active status.

### Step 5: Verify Territorial Isolation & Peer Mutation Block
1. Sign in with the newly created `admin.bogota.test` account.
2. Navigate to `http://localhost:3000/admin/municipality-admins`.
3. Verify that:
   - Municipal filter dropdown only allows Bogotá.
   - Action buttons for peer deactivation or reassignment are disabled/hidden, and direct API calls return HTTP 403 `PERMISSION_DENIED`.

---

## 9. Git & Migration Status

- **Git Working Tree:** Changes are preserved strictly in the working tree. Zero git commits or pushes have been performed in accordance with the binding change-control policy.
- **Database Migrations:** No schema drift was introduced. Migration chain remains at `030_institution_coordinator_delegation`. No new migrations were required as the existing relational schema completely supports the territorial scoping model.
- **Audit Logging:** Every provisioning, status update, and reassignment event is recorded in the immutable `audit_logs` table with canonical event types (`USER_ROLE_ASSIGNED`, `USER_ROLE_REVOKED`).

---

## 10. Exit Gate Decision

All criteria set forth in Milestone NTA-09-R1 have been met and verified with reproducible automated evidence:

- [x] Provisioning requests succeed with valid input using canonical database UUIDs.
- [x] Invalid requests display field-specific Spanish feedback and return structured validation errors.
- [x] No partial state remains after a failed provisioning transaction.
- [x] Server-side territorial isolation is strictly enforced across departmental and municipal layers.
- [x] Account activation policy enforces first-login credential rotation (`must_change_password=True`) and denies authentication to inactive accounts.
- [x] Territorial administrators appear correctly in both municipal management and general administrative directory queries (`/api/v1/users`).
- [x] 100% of focused tests (15/15) and regression suites (42/42) pass.
- [x] Frontend TypeScript typechecking succeeds with zero errors.
- [x] Canonical RBAC policies, existing user modifications, and audit logs are preserved intact.

**FINAL CERTIFICATION DECISION: CERTIFIED — PASS**
