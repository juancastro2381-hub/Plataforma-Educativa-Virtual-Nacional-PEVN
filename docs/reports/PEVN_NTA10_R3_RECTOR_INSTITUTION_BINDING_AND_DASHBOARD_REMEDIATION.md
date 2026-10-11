# PEVN — NTA-10-R3: Rector Institution Binding, Tenant Context Reconciliation, and Institutional Dashboard Remediation Report

**Standard:** AI Software Factory Standard v1.2  
**Author / Execution Agent:** Antigravity  
**Date:** October 10, 2026  
**Status:** `CONDITIONAL PASS — CODE VERIFIED, MANUAL ACCEPTANCE PENDING`  
**Target Institution:** `I.E VALPARAISO` (DANE: `118860001293`, Tenant ID: `44c67aeb-f016-4667-9835-96642dba5a08`)  
**Target User:** `miguel.villa@colegio.edu.co` (Rector, User ID: `4b4de8d5-02ca-4a83-9bdc-113b0e21b6d7`)

---

## 1. Executive Summary

Under **PEVN — NTA-10-R3**, we performed a forensic diagnosis and implemented systemic remediation for the Rector user experience following successful account activation under NTA-10-R2. 

While the Rector invitation redemption and account activation services functioned as designed, the Rector encountered two key barriers in their operational session:
1. **Navigating to `/admin/institutions` threw an authorization error:** `"Se requiere alcance territorial o nacional para consultar el catálogo de instituciones"`.
2. **The institutional dashboard and navbar lacked contextual resolution of the Rector's assigned establishment:** The dashboard rendered only a raw UUID without displaying the official institution name (`I.E VALPARAISO`), official DANE code (`118860001293`), or its official registered campus (`SEDE PRINCIPAL - I.E VALPARAISO`).

Our forensic analysis determined that **the database association was already 100% canonically persisted and intact**: user `miguel.villa@colegio.edu.co` was correctly bound to `institution_id = 44c67aeb-f016-4667-9835-96642dba5a08` in both `users` and `user_roles`. No synthetic database repairs or mutations were necessary.

The defects were isolated to **runtime contract gaps and view routing assumptions**:
- `GET /api/v1/institutions/me` was querying the table without enriching rector metadata (`_enrich_rector_status()`), reporting `has_active_rector=False`.
- `AuthContext.tsx` in the frontend did not automatically synchronize `activeInstitutionId` or resolve `activeInstitutionName` on session initialization (`initAuth`) or login.
- `InstitutionsView.tsx` unconditionally invoked territorial discovery endpoints (`/api/v1/institutions/catalog-explorer` and `/api/v1/institutions`) which strictly require territorial scope (`is_municipality`, `is_department`, `is_national`), thus rejecting the Rector with a 403 Forbidden.
- The UI had no Rector-scoped view for `/admin/institutions`.

We implemented a comprehensive, backward-compatible remediation across the backend and frontend, created a dedicated 11-scenario integration test suite (`test_nta10_r3_rector_binding.py`), verified zero TypeScript errors, and proved strict tenant isolation and territorial boundary enforcement.

---

## 2. Confirmed Root Cause & Forensic Diagnosis

### Forensic Evidence (PostgreSQL Live Database Query)

```sql
SELECT u.id, u.email, u.institution_id, r.name as role_name, ur.institution_id as ur_inst_id, ur.is_active as ur_active
FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id
WHERE u.email = 'miguel.villa@colegio.edu.co';
```

**Query Result:**
- **User ID:** `4b4de8d5-02ca-4a83-9bdc-113b0e21b6d7`
- **Email:** `miguel.villa@colegio.edu.co`
- **`u.institution_id`:** `44c67aeb-f016-4667-9835-96642dba5a08`
- **Role:** `rector`
- **`ur.institution_id`:** `44c67aeb-f016-4667-9835-96642dba5a08`
- **`ur.is_active`:** `True`

**Target Institution Record:**
- **ID:** `44c67aeb-f016-4667-9835-96642dba5a08`
- **Name:** `I.E VALPARAISO`
- **DANE Code:** `118860001293`
- **Municipality ID:** `2a8b6c9e-29c7-446c-85ea-6c8e19063774` (Valparaíso, Caquetá)
- **Campuses:** `SEDE PRINCIPAL - I.E VALPARAISO` (DANE Sede: `118860001293`, ID: `4a1de9b7-c43e-42ae-9130-43d7791ea8dd`)

### Root Cause Analysis

1. **`GET /api/v1/institutions/me` Omission of Service Enrichment:**
   In `backend/app/api/v1/endpoints/institutions.py`, `GET /me` performed a direct database select that bypassed `InstitutionService.get_institution_by_id()`. Consequently, rector status enrichment was omitted, leading to `has_active_rector=False` and incomplete tenant context.
2. **Missing Institutional Context Hydration in Frontend Session:**
   In `frontend/src/context/AuthContext.tsx`, `initAuth()` and `login()` extracted the `User` object, but never initialized `activeInstitutionId` from `user.institution_id` or fetched the institution's official name via `getMyInstitution()`. As a result, `activeInstitutionId` and `activeInstitutionName` remained `null` on fresh page loads and login.
3. **Territorial Catalog Route Misdirection:**
   `InstitutionsView.tsx` unconditionally dispatched calls to `fetchOfficialCatalog()` (`GET /api/v1/institutions/catalog-explorer`) and `fetchInstitutions()` (`GET /api/v1/institutions`). Under PEVN RBAC, these endpoints strictly enforce territorial jurisdiction:
   ```python
   if not (auth.is_national() or auth.is_department() or auth.is_municipality()):
       raise AuthorizationError(
           message="Se requiere alcance territorial o nacional para consultar el catálogo de instituciones.",
           code=ErrorCode.PERMISSION_DENIED,
       )
   ```
   A Rector possesses institutional scope (`institutions:read`), not territorial scope. The endpoint correctly threw HTTP 403, but the frontend lacked a role-specific view branch to display the Rector's assigned institution.
4. **Dashboard Scope Display Deficiency:**
   `Dashboard.tsx` had a card for "Alcance Institucional" that simply printed the raw UUID string (`44c67aeb-f016-4667-9835-96642dba5a08`) without querying the institution profile.

---

## 3. Before / After Verification

| Capability / Check | Before NTA-10-R3 | After NTA-10-R3 |
| :--- | :--- | :--- |
| **Persisted DB User Binding** | `users.institution_id` & `user_roles.institution_id` valid | Verified intact; zero database mutation needed |
| **`GET /api/v1/institutions/me`** | Inline select, `has_active_rector=False`, no scope resolution | Uses `InstitutionService`, resolves `auth.scope.institution_id`, enriches active rector & campuses |
| **AuthContext Initialization** | `activeInstitutionId = null`, `activeInstitutionName = null` | Auto-syncs `activeInstitutionId` & resolves official institution name from API |
| **Navbar for Rector** | Displayed generic "Instituciones" linking to territorial catalog | Displays `🏛️ Mi Institución` linking to institutional portal |
| **Navigation to `/admin/institutions`** | Threw 403: *"Se requiere alcance territorial o nacional..."* | Dynamically renders **Portal del Rector** with institution details, campuses, and settings |
| **Rector Dashboard View** | Showed only raw UUID `44c67aeb-...` | Shows `I.E VALPARAISO`, DANE `118860001293`, Estado Activa, Rector titular, Sedes registradas |
| **Cross-Tenant Access (`/{other_id}`)** | Throws 403 Forbidden | Throws 403 Forbidden (verified by integration tests) |
| **Catalog Explorer Access** | Throws 403 Forbidden for Rector | Continues to throw 403 for Rector; remains 100% accessible to territorial admins |

---

## 4. Relevant Database Entities & Canonical Architecture

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : defines
    INSTITUTIONS ||--o{ CAMPUSES : contains
    INSTITUTIONS ||--o{ USERS : binds
    INSTITUTIONS ||--o{ USER_ROLES : scopes
    MUNICIPALITIES ||--o{ INSTITUTIONS : encompasses
    OFFICIAL_INSTITUTION_CATALOG ||--o{ INSTITUTIONS : provisions

    USERS {
        uuid id PK
        string email
        uuid institution_id FK "Canonical Institution Tenant"
        boolean is_active
    }
    USER_ROLES {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
        uuid institution_id FK "Canonical Institutional Scope"
        boolean is_active
    }
    INSTITUTIONS {
        uuid id PK
        string dane_code "118860001293"
        string name "I.E VALPARAISO"
        uuid municipality_id FK
        boolean is_active
        boolean coordinator_delegation_enabled
    }
    CAMPUSES {
        uuid id PK
        uuid institution_id FK
        string dane_sede_code "118860001293"
        string name "SEDE PRINCIPAL - I.E VALPARAISO"
        boolean is_active
    }
```

---

## 5. Implementation Details & Files Changed

### Backend

#### 1. `backend/app/api/v1/endpoints/institutions.py`
- Refactored `GET /api/v1/institutions/me` to accept `auth: AuthContextDep`.
- Resolves effective institution ID with fallback: `current_user.institution_id` or `auth.scope.institution_id`.
- If no institution is associated, safely fails closed with 404 (`"El usuario no tiene una institución educativa asociada."`).
- Invokes `service.get_institution_by_id(effective_inst_id)` to ensure full `InstitutionResponse` enrichment, including:
  - Official DANE code and name.
  - Active rector metadata (`has_active_rector=True`, `active_rector_name="Miguel Villa"`, `active_rector_email="miguel.villa@colegio.edu.co"`).
  - List of registered campuses (`dane_sede_code`, `name`, `is_active`).
  - Coordinator delegation status (`coordinator_delegation_enabled`).

### Frontend

#### 2. `frontend/src/context/AuthContext.tsx`
- Added `syncInstitutionalContext(userObj)` helper.
- When an authenticated user possesses `user.institution_id`:
  - Automatically initializes `activeInstitutionId` to match `user.institution_id`.
  - In the background, calls `institutionApi.getMyInstitution()` to populate `activeInstitutionName`.
  - Stores institutional context in session storage.
- Integrated into `initAuth`, `login`, and `refreshUser`.

#### 3. `frontend/src/layouts/RootLayout.tsx`
- Updated navigation bar for users with the `rector` role:
  - Label updated from `"Instituciones"` to `🏛️ Mi Institución`.
  - Hover tooltip indicates `"Mi Institución Educativa"`.

#### 4. `frontend/src/pages/Dashboard.tsx`
- Added state and effect to fetch the Rector's assigned institution details via `institutionApi.getMyInstitution()`.
- Enhanced the `Alcance Institucional` card for Rector:
  - Displays official establishment name: `I.E VALPARAISO`.
  - Displays official DANE code: `118860001293`.
  - Displays operational status badge: `● Estado: Activa`.
  - Lists registered campuses: `SEDE PRINCIPAL - I.E VALPARAISO` (`118860001293`).
  - Displays assigned Rector titular name.
  - Provides direct deep links to:
    - `🏛️ Ver Perfil y Sedes` (`/admin/institutions`)
    - `👥 Gestión de Personal` (`/admin/users`)

#### 5. `frontend/src/pages/admin/InstitutionsView.tsx`
- Added role distinction: `isRector = hasRole(['rector', 'institution_admin']) && !isTerritorialAdmin`.
- In `useEffect`, if `isRector` is `true`, bypasses territorial catalog calls and invokes `fetchRectorInstitution()` (`institutionApi.getMyInstitution()`).
- Implemented **Portal del Rector** view containing:
  - **Institutional Header Banner:** Displays official institution name, DANE code, status, and navigation shortcuts.
  - **Tab 1: Información y Sedes (`profile`):**
    - Technical specification card: DANE code, Rector titular name, official email, phone, address, and Tenant UUID.
    - Official registered campuses grid displaying campus name, DANE Sede code, and active badge.
  - **Tab 2: Delegación Operativa (`settings`):**
    - Operational switch for NTA-10-R1 coordinator delegation (`coordinator_delegation_enabled`) allowing the Rector to grant or restrict user management permissions to coordinators.
  - **Tab 3: Accesos Académicos (`academic`):**
    - Direct access cards for institutional user administration (`/admin/users`) and institutional dashboard (`/dashboard`).
  - **Diagnostic Error Handling:** If the institution cannot be loaded, renders an actionable diagnostic card with user/tenant IDs and a retry button.

---

## 6. RBAC and Tenant-Isolation Verification

We verified all RBAC boundaries and tenant isolation constraints:

1. **Derived Scope:** The Rector's institutional scope is derived from the authenticated server-side JWT and canonical database records. Client-supplied IDs are never trusted.
2. **Access to Own Institution:** `GET /api/v1/institutions/{own_id}` -> `200 OK`.
3. **Cross-Tenant Substitution Rejection:** `GET /api/v1/institutions/{other_id}` -> `403 Forbidden`.
4. **Territorial Catalog Shielding:** `GET /api/v1/institutions/catalog-explorer` -> `403 Forbidden` for Rector.
5. **General Master List Shielding:** `GET /api/v1/institutions` -> `403 Forbidden` for Rector.
6. **Orphan Rector Safety:** Users with the Rector role but missing institutional association fail closed on `/me` with `404 Not Found`.
7. **Territorial Administrators Retain Full Authority:** Municipal administrators continue to query their municipal catalog, and National/Departmental administrators retain supervisory catalog queries.

---

## 7. Automated Test Suite Results

### Targeted NTA-10-R3 Integration Test Suite (`test_nta10_r3_rector_binding.py`)

Command:
```bash
pytest tests/test_nta10_r3_rector_binding.py -v
```

**Results: 11 passed in 30.11s (100% PASS)**

| # | Test Name | Result | Verification Focus |
| :- | :--- | :---: | :--- |
| 1 | `test_01_rector_invitation_redemption_persists_canonical_binding` | **PASSED** | Redeeming invitation persists `institution_id` in `users` and `user_roles`. |
| 2 | `test_02_rector_login_returns_institutional_context` | **PASSED** | Login returns `access_token` and `user.institution_id`. |
| 3 | `test_03_rector_dashboard_institution_me_summary` | **PASSED** | `GET /institutions/me` returns `I.E VALPARAISO`, DANE `118860001293`, campuses, active rector. |
| 4 | `test_04_rector_can_read_own_institution_detail` | **PASSED** | `GET /institutions/{own_id}` returns 200 OK for assigned establishment. |
| 5 | `test_05_rector_cannot_access_other_institution` | **PASSED** | `GET /institutions/{other_id}` fails with 403 Forbidden. |
| 6 | `test_06_rector_rejected_from_territorial_catalog_explorer` | **PASSED** | Rector cannot query territorial catalog explorer (403 Forbidden). |
| 7 | `test_07_rector_rejected_from_general_institutions_list` | **PASSED** | Rector cannot query general institutions master list (403 Forbidden). |
| 8 | `test_08_municipal_admin_retains_authorized_catalog_access` | **PASSED** | Municipal administrator retains catalog access for their municipality (200 OK). |
| 9 | `test_09_department_and_national_admins_retain_supervisory_access` | **PASSED** | Department and National admins retain supervisory catalog access (200 OK). |
| 10 | `test_10_orphan_rector_without_institution_fails_safely` | **PASSED** | Rector without institution fails closed on `/me` with 404 (no leak). |
| 11 | `test_11_rector_anti_duplication_prevent_second_active_rector` | **PASSED** | Anti-duplication prevents inviting second active rector (409 Conflict). |

### Full Regression Suite Run

Command:
```bash
pytest tests/test_nta10_r3_rector_binding.py tests/test_nta10_r2_catalog_and_urls.py tests/test_rector_succession.py tests/test_rbac_governance_and_rector_invitation.py tests/test_nta09_municipality_admin_provisioning.py tests/test_department_admin_invitation.py -v
```

**Results: 94 passed in 238.15s (100% PASS)**

### Frontend Typecheck

Command:
```bash
npm run typecheck
```

**Result: `tsc --noEmit` exited with code 0 (Zero TypeScript errors).**

---

## 8. Manual Acceptance Scenario Checklist

Antigravity standard strictly prohibits claiming manual browser acceptance without user confirmation. Please execute the following acceptance scenario in your browser:

- [ ] **Step 1: Rector Login**  
  Log in with Rector account: `miguel.villa@colegio.edu.co`.
- [ ] **Step 2: Rector Dashboard Verification**  
  Confirm the dashboard card "Alcance Institucional" displays:
  - Official institution name: `I.E VALPARAISO`
  - Official DANE code: `118860001293`
  - Operational status: `● Estado: Activa`
  - Registered campuses: `SEDE PRINCIPAL - I.E VALPARAISO`
  - Rector Titular: `Miguel Villa`
- [ ] **Step 3: Rector Navigation**  
  Click on `🏛️ Mi Institución` in the top navigation bar or navigate to `/admin/institutions`.
  - Confirm the page renders the **Portal del Rector** without any 403 authorization error.
  - Verify technical specifications (DANE code, email, phone, Tenant ID).
  - Verify registered campuses section shows `SEDE PRINCIPAL - I.E VALPARAISO`.
- [ ] **Step 4: Operational Delegation Toggle**  
  Navigate to the `⚙️ Delegación Operativa` tab in the Rector portal.
  - Test toggling coordinator delegation on and off.
  - Confirm the feedback banner updates correctly.
- [ ] **Step 5: Session Persistence & Refresh**  
  Refresh the browser (`F5` or `Ctrl+R`).
  - Confirm the Rector remains logged in and `I.E VALPARAISO` is immediately visible.
  - Log out and log back in; confirm the institutional context is preserved.
- [ ] **Step 6: Territorial Isolation Verification**  
  Verify the Rector is NOT shown the territorial catalog explorer search, department/municipality selectors, or provisioning buttons for other institutions.
- [ ] **Step 7: Municipal Administrator Verification**  
  Log in as the Municipal Administrator for Valparaíso (`admin.valparaiso@pevn.gov.co`).
  - Navigate to `/admin/institutions`.
  - Confirm the municipal administrator can still view all 7 official establishments and 49 campuses in Valparaíso.
- [ ] **Step 8: Tenant Anti-Duplication Verification**  
  Confirm no duplicate tenants or duplicate Rector accounts were created for `I.E VALPARAISO`.

---

## 9. Git Working Tree Status

- **Branch:** `main`
- **Commit Policy:** Clean working tree maintained; zero commits or pushes created per AI Software Factory Standard v1.2 change control guidelines.
- **Modified Project Code Files:**
  - `backend/app/api/v1/endpoints/institutions.py`
  - `frontend/src/context/AuthContext.tsx`
  - `frontend/src/layouts/RootLayout.tsx`
  - `frontend/src/pages/Dashboard.tsx`
  - `frontend/src/pages/admin/InstitutionsView.tsx`
  - `backend/tests/test_nta10_r3_rector_binding.py` (New targeted test suite)

---

## 10. Exit Gate Certification

**Status:** `CONDITIONAL PASS — CODE VERIFIED, MANUAL ACCEPTANCE PENDING`

*Antigravity has verified all backend endpoints, data bindings, frontend routing components, and regression test suites. Manual acceptance by the operator is pending.*
