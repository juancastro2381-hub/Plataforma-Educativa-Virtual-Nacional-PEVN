# PEVN — RBAC-AUDIT-02: Cross-Role Navigation, Interface Coherence, Permission Alignment, and End-to-End Acceptance

**Audit ID:** PEVN-RBAC-AUDIT-02  
**Date:** 2026-10-12  
**Revision:** R2 — Territorial Acceptance Recorded & Institutional Validation Active  
**Platform:** Plataforma Educativa Virtual Nacional (PEVN)  
**Implementation Agent:** Antigravity  
**Certification Status:** `CONDITIONAL PASS — TERRITORIAL ACCEPTANCE RECORDED; INSTITUTIONAL VALIDATION PENDING`

---

## 1. Executive Summary and Scope

An end-to-end, forensic audit of role-specific interfaces, routing guards, territorial isolation, and navigation coherence was executed across the Plataforma Educativa Virtual Nacional (PEVN).

The audit was triggered by an operator report stating that clicking **"Académica"** and **"Aulas Virtuales"** produced unexpected views, specifically displaying the institutional management view at `/admin/institutions?contextRequired=true` with the municipal supervision catalog. The operator initially described the user as `DEPARTMENT_ADMIN`.

### Core Scope
1. **Forensic Reconciliation:** Investigate the identity, canonical role, territorial scope, and token payload from the supplied screenshots vs. the operator's description (`DEPARTMENT_ADMIN` vs. `municipality_admin`).
2. **Independent Forensic Diagnosis:** Trace the complete execution flows for both `DEPARTMENT_ADMIN` and `MUNICIPALITY_ADMIN` regarding the "Académica" and "Aulas Virtuales" modules.
3. **Canonical Role Audit:** Audit all 10 roles in PEVN (`SUPER_ADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`, `RECTOR`, `COORDINATOR`, `TEACHER`, `STUDENT`, `GUARDIAN`, `AUDITOR`).
4. **Role-to-Interface Matrix:** Build a comprehensive matrix covering menu items, routes, components, permissions, APIs, and scope boundaries.
5. **Minimal Surgical Remediation:** Correct confirmed routing, context persistence, and navigation defects without altering security boundaries, tenant isolation, or unrelated business logic.
6. **Automated Verification & Manual Acceptance Matrix:** Execute unit, component, and backend security test suites, record human operator acceptance, and deliver a structured continuation plan for cross-role browser acceptance.

---

## 2. Initial Repository and Working-Tree Status

Prior to executing any modifications, the local working tree was inspected. Pre-existing changes from prior audit and stabilization phases (NTA-10-R8, RBAC-AUDIT-01, etc.) were identified and strictly preserved:

- `frontend/src/components/student/StudentTaskDetailModal.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/academic/GuardiansView.tsx`
- `frontend/src/pages/academic/StudentsView.tsx`
- `frontend/src/pages/operations/TenantDiagnosticsView.tsx`
- `frontend/src/test/Academic.test.tsx`
- `frontend/src/test/RoleNavigationFunctional.test.tsx`
- `frontend/src/test/StudentPortal.test.tsx`
- Untracked reports and test files under `docs/reports/` and `frontend/src/test/`

All existing database records, migrations, and git histories were preserved with zero resets, stashes, or commits.

---

## 3. Screenshot Forensic Analysis: The Role Discrepancy

### 3.1 Operator Statement vs. Visual Evidence
- **Operator Statement:** The operator reported that the affected user was a `DEPARTMENT_ADMIN`.
- **Screenshot Evidence:** The supplied screenshots (`media_1791842433581.png`) clearly show:
  - User name: **Luis Soto**
  - Canonical Role displayed in header/badge: `municipality_admin`
  - Hierarchy Level: **70**
  - Territorial Jurisdiction: **Puerto Carreño** (Vichada)
  - URL in address bar: `http://localhost:3000/admin/institutions?contextRequired=true`
  - Page Title: **"Supervisión Municipal de Instituciones Educativas"**
  - Badge: **"Nivel Municipal • Secretaría de Educación Municipal (Territorial)"**

### 3.2 Forensic Identity Tracing in Database
A database inspection of the active accounts in PostgreSQL confirmed:
1. **Luis Soto Account:**
   - User ID: `cb56d190-075b-4f7d-bb3c-6ca0fefa924e`
   - Email: `lsoto@ptocarreno.co`
   - Canonical Role: `municipality_admin` (Hierarchy Level 70)
   - Scope: `municipality_id = "MUN-99001"` (Puerto Carreño), `department_id = "DEP-99"` (Vichada), `institution_id = NULL`.
2. **Department Administrator Account:**
   - User ID: `9dd0e4ad-fa6c-4b10-85f0-629ee944e662`
   - User Name: **Jesus Gomez**
   - Email: `jesus@vichada.co`
   - Canonical Role: `department_admin` (Hierarchy Level 80)
   - Scope: `department_id = "DEP-99"` (Vichada), `municipality_id = NULL`, `institution_id = NULL`.

### 3.3 Mandatory Forensic Finding
The screenshots provided by the operator depict **Luis Soto**, who is definitively a **`municipality_admin`** (Level 70), **not** a `DEPARTMENT_ADMIN` (Level 80).  
However, the audit independently investigated both roles to ensure that neither departmental nor municipal administrators experience unexpected routing failures.

---

## 4. Forensic Request & Navigation Traces

### 4.1 The PEVN Multi-Tenant Architecture & Institutional Context
In PEVN's multi-tenant architecture:
- School-level modules (such as **"Gestión Académica"** `/academic` and **"Aulas Virtuales"** `/virtual-classrooms`) operate strictly on **tenant-scoped** data (`institution_id`). An institution has specific academic years, periods, grades, subjects, groups, and classrooms.
- Institutional roles (`rector`, `coordinator`, `teacher`, `student`, `guardian`) have a permanent `institution_id` in their user profile and JWT claims.
- Territorial administrators (`department_admin`, `municipality_admin`) and global administrators (`national_admin`, `superadmin`) supervise **multiple** institutions. Their JWT tokens intentionally have `institution_id: null`.
- Consequently, when a territorial supervisor enters an institution-specific module (`/academic` or `/virtual-classrooms`), the frontend requires an **active institutional context** (`activeInstitutionId`), which specifies which school is currently under inspection.

### 4.2 Forensic Trace 1: `DEPARTMENT_ADMIN` Flow
1. **Authenticated User:** Jesus Gomez (`jesus@vichada.co`), role `department_admin`.
2. **Clicking "Académica" (`/academic`):**
   - Route guard: `<RequireAuth roles={['rector', 'coordinator', 'superadmin', 'department_admin', ...]} requireInstitutionContext>`
   - Evaluation: Jesus Gomez has the `department_admin` role, but `user.scope.institution_id` is null and `activeInstitutionId` is null.
   - Guard Behavior: Redirects to `/admin/institutions?contextRequired=true`.
3. **Destination Screen:** Renders `InstitutionsView` showing departmental supervision.
4. **Identified Defect:**
   - The redirect stripped the intended destination (`returnTo=/academic`).
   - `InstitutionsView` defaulted to the official MEN/DANE catalog (`activeTab = 'catalog'`), where unprovisioned schools do not have context buttons.
   - When the administrator selected `🏛️ Contexto` on an active school, `activeInstitutionId` was stored in `localStorage`, but the user remained on `/admin/institutions` rather than continuing to `/academic`.
   - On page refresh or silent token re-hydration (`initAuth`), `AuthContext` wiped `activeInstitutionId` because `user.institution_id` was null.

### 4.3 Forensic Trace 2: `MUNICIPALITY_ADMIN` Flow
1. **Authenticated User:** Luis Soto (`lsoto@ptocarreno.co`), role `municipality_admin`.
2. **Clicking "Académica" (`/academic`):**
   - Route guard in `App.tsx`: `<RequireAuth roles={['rector', 'coordinator', 'superadmin', 'department_admin']}`.
   - **Severe Defect:** `municipality_admin` was **omitted** from the `roles` array of `/academic` in `App.tsx`!
   - Result: Even if Luis Soto had selected an active school context, `RequireAuth` denied access and booted him to `/dashboard`.
   - Before context selection, `requireInstitutionContext` redirected him to `/admin/institutions?contextRequired=true`.
3. **Clicking "Aulas Virtuales" (`/virtual-classrooms`):**
   - Route guard in `App.tsx`: `<RequireAuth permissions={['virtual_classrooms:read']} requireInstitutionContext>`.
   - Evaluation: `municipality_admin` has permission `virtual_classrooms:read`. Without active context, redirected to `/admin/institutions?contextRequired=true`.
4. **Identified Defect:**
   - Same context selection loop as department admin, plus the hard block on `/academic`.

---

## 5. Canonical Role Registry & Permission Sources

The PEVN role hierarchy is stored canonically in PostgreSQL table `roles` with numeric levels:

| Canonical Role | DB Hierarchy Level | Supported Aliases | Primary Scope Boundaries |
|---|---|---|---|
| `superadmin` | 100 | `super_admin` | Global Platform (All tenants and territories) |
| `national_admin` | 90 | `national` | Country-wide educational catalog and governance |
| `department_admin` | 80 | `secretaria_departamental` | Assigned Department (`department_id`) |
| `municipality_admin`| 70 | `secretaria_municipal` | Assigned Municipality (`municipality_id`) |
| `rector` | 60 | `institution_admin`, `directivo`| Assigned Institution (`institution_id`) |
| `coordinator` | 50 | `academic_coordinator` | Assigned Institution (`institution_id`) |
| `teacher` | 30 | `docente` | Assigned academic assignments & groups |
| `student` | 10 | `estudiante`, `alumno` | Own student profile, enrollments & activities |
| `guardian` | 10 | `acudiente`, `padre` | Linked students under authorized custody |
| `auditor` | N/A | None | Conceptual/unimplemented (Inactive in DB) |

---

## 6. Complete Role-to-Interface Matrix

| Module / Route | SUPER_ADMIN | NATIONAL_ADMIN | DEPARTMENT_ADMIN | MUNICIPALITY_ADMIN | RECTOR | COORDINATOR | TEACHER | STUDENT | GUARDIAN | AUDITOR |
|---|---|---|---|---|---|---|---|---|---|---|
| **Dashboard** (`/dashboard`) | `ALLOWED` (Global KPIs) | `ALLOWED` (National KPIs) | `ALLOWED` (Dept KPIs) | `ALLOWED` (Muni KPIs) | `ALLOWED` (Inst KPIs) | `ALLOWED` (Coord KPIs) | `ALLOWED` (Classes) | `ALLOWED` (Grades) | `ALLOWED` (Family) | `NOT_APPLICABLE` |
| **Territorial Institutions** (`/admin/institutions`) | `ALLOWED` (All) | `ALLOWED` (National) | `ALLOWED` (Dept Scope) | `ALLOWED` (Muni Scope) | `ALLOWED` (Own School) | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **User Directory** (`/admin/users`) | `ALLOWED` (Global) | `ALLOWED` (National) | `ALLOWED` (Dept Scope) | `ALLOWED` (Muni Scope) | `ALLOWED` (Inst Staff) | `ALLOWED` (If delegated) | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Academic Hub** (`/academic`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Academic Years** (`/academic/years`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Academic Periods** (`/academic/periods`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Subjects** (`/academic/subjects`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Groups & Classes** (`/academic/groups`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `READ_ONLY` (Assigned) | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Students Registry** (`/academic/students`)| `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `READ_ONLY` (Assigned) | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Guardians Registry** (`/academic/guardians`)| `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `READ_ONLY` (Assigned) | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Virtual Classrooms** (`/virtual-classrooms`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `ALLOWED` (Own Classes) | `ALLOWED` (Own Classes) | `DENIED` | `NOT_APPLICABLE` |
| **Evaluation & SIEE** (`/evaluations/management`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Coexistence** (`/coexistence`) | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `CONTEXT_REQUIRED` | `ALLOWED` | `ALLOWED` | `ALLOWED` (Report) | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Territorial Analytics** (`/analytics/territorial`) | `ALLOWED` | `ALLOWED` | `ALLOWED` (Dept Scope) | `ALLOWED` (Muni Scope) | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Tenant Diagnostics** (`/operations/tenant-diagnostics`) | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |
| **Technical Health** (`/operations/health`) | `ALLOWED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `DENIED` | `NOT_APPLICABLE` |

---

## 7. Root Cause Analysis

| Finding ID | Severity | Component | Root Cause | Impact |
|---|---|---|---|---|
| **F-01** | High | `frontend/src/App.tsx` | Missing `'municipality_admin'` in `RequireAuth` roles for `/academic`. | Municipality admins were blocked with a 403 redirect to `/dashboard` even when an institutional context was set. |
| **F-02** | High | `frontend/src/components/auth/RequireAuth.tsx` | Redirection to `/admin/institutions?contextRequired=true` did not pass the target URL (`returnTo`). | The platform suffered "destination amnesia": the user did not know which screen required context and was not auto-navigated upon selection. |
| **F-03** | Medium | `frontend/src/pages/admin/InstitutionsView.tsx` | View defaulted to official MEN/DANE catalog (`activeTab = 'catalog'`) when `contextRequired=true`. | Territorial admins saw unprovisioned DANE schools without context buttons instead of active operational tenants. |
| **F-04** | High | `frontend/src/pages/admin/InstitutionsView.tsx` | Clicking `🏛️ Contexto` set context state but did not navigate to the preserved `returnTo` destination. | The administrator was stranded on the institutions page after clicking context. |
| **F-05** | High | `frontend/src/context/AuthContext.tsx` | Silent session refresh (`initAuth`) cleared active context for territorial users because `user.institution_id` is null. | Refreshing any page in `/academic` or `/virtual-classrooms` instantly kicked territorial admins back to `/admin/institutions`. |
| **F-06** | Low | `frontend/src/layouts/RootLayout.tsx` | Sidebar visibility for "Gestión Académica" checked `canAccessAcademic` using an ad-hoc role list without explicit `municipality_admin`. | Inconsistent sidebar item display for municipal administrators. |

---

## 8. Minimal Corrective Implementation

### 8.1 File Changes Summary
The following surgical, non-destructive edits were applied:

1. **`frontend/src/App.tsx`**:
   - Added `'municipality_admin'` to the allowed roles for `/academic`:
     ```tsx
     roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator', 'superadmin', 'super_admin', 'department_admin', 'municipality_admin']}
     ```
2. **`frontend/src/components/auth/RequireAuth.tsx`**:
   - Preserved destination route in query parameters:
     ```tsx
     const returnTo = encodeURIComponent(location.pathname + location.search)
     return <Navigate to={`/admin/institutions?contextRequired=true&returnTo=${returnTo}`} replace />
     ```
3. **`frontend/src/pages/admin/InstitutionsView.tsx`**:
   - Added Anti-Open-Redirect sanitized `returnTo` handling:
     ```tsx
     const rawReturnTo = searchParams.get('returnTo')
     const returnTo = rawReturnTo && rawReturnTo.startsWith('/') && !rawReturnTo.startsWith('//') ? rawReturnTo : null
     ```
   - Automatically defaulted `activeTab` to `'tenants'` when `isContextRequired` is true.
   - Enhanced context required alert banner to display the exact destination module.
   - On clicking `🏛️ Contexto`, automatically navigated to `returnTo`:
     ```tsx
     setActiveInstitutionContext(inst.id, inst.name)
     setSuccessMsg(`Contexto institucional establecido en "${inst.name}". Ahora puede acceder a Gestión Académica y Aulas Virtuales para esta institución.`)
     if (returnTo) {
       navigate(returnTo)
     }
     ```
4. **`frontend/src/context/AuthContext.tsx`**:
   - Updated `syncInstitutionalContext` so that territorial (`department_admin`, `municipality_admin`) and global (`superadmin`, `national_admin`) administrators retain their manually chosen `pevn_active_institution_id` across silent session refreshes (`initAuth`).
5. **`frontend/src/layouts/RootLayout.tsx`**:
   - Explicitly added `municipality_admin` to `canAccessAcademic` in the navigation bar.

---

## 9. Backend Authorization, Territorial Scope, and Anti-IDOR Assessment

The backend authorization layer was verified across all affected endpoints:

1. **Territorial Catalog Isolation:**
   - `GET /api/v1/institutions`:
     - When queried by a `department_admin`, the query applies `effective_department_id = user.scope.department_id`.
     - When queried by a `municipality_admin`, the query applies `effective_municipality_id = user.scope.municipality_id`.
     - Attempting to pass a foreign `municipality_id` in query parameters is intercepted and rejected with HTTP 403 `PERMISSION_DENIED`.
2. **Context Selection Security:**
   - Setting `activeInstitutionId` in the frontend client does not grant extra backend permissions. Every API call made under an institutional context verifies that the user's territorial scope contains the institution's municipality and department.
3. **IDOR & Boundary Protection:**
   - Backend tests (`test_guardian_tenant_isolation.py`, `test_teacher_academic_scope.py`, `test_municipality_admin_rbac.py`) verified that crossing institutional or territorial boundaries returns HTTP 403/404.

---

## 10. Automated Test Results

### 10.1 Frontend Automated Suites
- **New Audit Test Suite:** `frontend/src/test/CrossRoleNavigationAudit.test.tsx`
  - Command: `npm run test -- CrossRoleNavigationAudit.test.tsx`
  - Result: **9 / 9 PASSED** (100%)
- **Complete Frontend Regression Suite:**
  - Command: `npm run test`
  - Result: **27 / 27 test files PASSED, 184 / 184 tests PASSED** (100%)
- **TypeScript Static Verification:**
  - Command: `npx tsc --noEmit`
  - Result: **0 errors** (Clean compilation)
- **Production Bundle Build Check:**
  - Command: `npm run build`
  - Result: **0 errors, built in 6.44s**

### 10.2 Backend Automated Suites
- **Backend Authorization & Security Isolation Tests:**
  - Command: `pytest tests/test_authorization.py tests/test_municipality_admin_rbac.py tests/test_guardian_tenant_isolation.py tests/test_teacher_academic_scope.py`
  - Result: **27 / 27 PASSED** (100%)

---

## 11. Human Operator Manual Acceptance Tracking

Per Mandatory Constraints 5 and 6, zero browser automation was used; human execution is strictly required for platform acceptance.

### 11.1 Accepted Navigation Workflows (Operator Confirmed — 2026-10-12)

The human platform operator manually verified and certified the two corrected core navigation flows:

| Scenario ID | Navigation Workflow | Preconditions & Execution | Expected & Verified Result | Operator Certification Status |
|---|---|---|---|---|
| **ACC-NAV-01** | **Gestión Académica Navigation & Context Flow** | Authenticated as a territorial administrator without active institutional context. Click **“Académica”** in top navigation. | System displays context-selection banner on `/admin/institutions?contextRequired=true&returnTo=%2Facademic` displaying provisioned schools. Clicking **“🏛️ Contexto”** on an eligible school activates the context and auto-navigates to `/academic` (Academic Hub). | **`PASS — OPERATOR CONFIRMED`** (2026-10-12) |
| **ACC-NAV-02** | **Aulas Virtuales Navigation & Context Flow** | Authenticated as a territorial administrator without active institutional context. Click **“Aulas Virtuales”** in top navigation. | System displays context-selection banner on `/admin/institutions?contextRequired=true&returnTo=%2Fvirtual-classrooms`. Clicking **“🏛️ Contexto”** on an eligible school activates the context and auto-navigates directly to `/virtual-classrooms`. | **`PASS — OPERATOR CONFIRMED`** (2026-10-12) |

---

### 11.2 Confirmed Territorial Administrator Scenarios (Operator Confirmed — 2026-10-12)

The human platform operator executed and certified the full block of territorial scenarios (`SEQ-01` through `SEQ-06`):

| Scenario ID | Role | Test Action | Expected Behavior | Operator Result | Date Accepted |
|---|---|---|---|---|---|
| **SEQ-01** | `DEPARTMENT_ADMIN` (`jesus@vichada.co`) | Inspect header badge, level, and scope. Open `/admin/institutions`. | Badge reads "Nivel Departamental (VICHADA)". Role hierarchy level is 80. Catalog lists only institutions in department 99 (Vichada). | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |
| **SEQ-02** | `DEPARTMENT_ADMIN` | Attempt direct URL or parameter tampering to an institution outside Vichada (e.g., Meta `DEP-50`). | Access is denied with HTTP 403 or safe redirect. Zero cross-department data exposure. | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |
| **SEQ-03** | `DEPARTMENT_ADMIN` | Select active institutional context, navigate to `/academic`, and execute page refresh (`F5`). | Active institution name remains pinned in top banner; `/academic` remains active without re-prompting context. | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |
| **SEQ-04** | `MUNICIPALITY_ADMIN` (`lsoto@ptocarreno.co`) | Inspect header badge, level, and scope. Open `/admin/institutions`. | Badge reads "Nivel Municipal • Puerto Carreño". Role hierarchy level is 70. Catalog lists only Puerto Carreño institutions (99001). | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |
| **SEQ-05** | `MUNICIPALITY_ADMIN` | Attempt direct URL or access to an institution in another municipality of Vichada (e.g. Cumaribo `MUN-99773`). | Access is denied; cannot select context or inspect data outside Puerto Carreño. Anti-IDOR barrier enforced. | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |
| **SEQ-06** | `MUNICIPALITY_ADMIN` | Access User Management (`/admin/users`). Verify user creation and inspection boundaries. | Can inspect and manage local municipal staff; cannot modify departmental, national, or SuperAdmin accounts. | **`PASS — OPERATOR CONFIRMED`** | 2026-10-12 |

> **Scope of Confirmed Acceptance:**  
> The operator's manual confirmation covers 8 scenarios: `ACC-NAV-01`, `ACC-NAV-02`, and `SEQ-01` through `SEQ-06`. This confirms that territorial administration (both Departmental and Municipal) respects jurisdiction boundaries, properly maintains active school context across browser refreshes, and prevents unauthorized cross-territory data access. Remaining institutional, pedagogical, national/global, and session-switch scenarios remain pending.

---

## 12. Active Manual Acceptance Sequence: Institutional Role Validation Block

The operator must next execute and document the institutional management sequence (`SEQ-07` through `SEQ-11`) for the **Rector** and **Coordinator** roles.

### 12.1 Practical Browser Acceptance Checklist (For Human Operator)

| Scenario ID | Target Account & Role | Test Action | Expected Behavior | Operator Checklist Status |
|---|---|---|---|---|
| **SEQ-07** | **Rector** (Institutional Lead) | Log in as Rector of an assigned school. Click **"Académica"** in navigation bar. | Direct load of `/academic` (Academic Hub) for the assigned institution. **No prerequisite context prompt** is shown because the Rector's token is pre-scoped to their school. Top banner shows school name and DANE code. | `[ ] PENDING` |
| **SEQ-08** | **Rector** | Navigate to `/admin/institutions` (Rector Institutional Portal). In "Delegación Operativa", toggle the Coordinator Delegation switch. | Setting updates successfully with confirmation message. When enabled, coordinators are authorized to manage staff/students; when disabled, coordinator creation rights are revoked. | `[ ] PENDING` |
| **SEQ-09** | **Rector** | Attempt direct URL ID tampering (e.g., `/academic/groups?institution_id=<foreign_id>` or direct API invocation). | Access is denied with HTTP 403. Tenant isolation barrier prevents any inspection or modification of other institutions. | `[ ] PENDING` |
| **SEQ-10** | **Coordinator** (Academic Lead) | Log in as Coordinator. Access `/academic`. Verify academic entity management and test user management with delegation enabled vs disabled. | Full access to academic configurations (periods, grades, groups, subjects, assignments). Student/teacher management is permitted **only** when Rector delegation is enabled. | `[ ] PENDING` |
| **SEQ-11** | **Coordinator** | Attempt direct navigation to unauthorized administrative routes: `/operations/health`, `/operations/tenant-diagnostics`, or `/admin/institutions`. | Access is denied; user is safely redirected to `/dashboard`. Administrative portals are not visible or accessible. | `[ ] PENDING` |

---

### 12.2 Subsequent Acceptance Blocks (Pending Completion of Block 12.1)

#### Pedagogical & Community Roles (`TEACHER`, `STUDENT`, `GUARDIAN`)

| Scenario ID | Role | Test Action | Expected Verification | Current Status |
|---|---|---|---|---|
| **SEQ-12** | `TEACHER` | Log in as Teacher. Inspect sidebar navigation and `/teacher` portal. | Sees only assigned groups, subjects, and students. "Gestión Académica" administrative modules are not present in menu. | `PENDING` |
| **SEQ-13** | `TEACHER` | Attempt direct URL to `/academic/years` or `/admin/institutions`. | Denied; redirected to `/dashboard`. | `PENDING` |
| **SEQ-14** | `STUDENT` | Log in as Student. Inspect portal (`/student`). | Sees only own registered classes, tasks, submissions, and grades. No administrative tools visible. | `PENDING` |
| **SEQ-15** | `STUDENT` | Attempt direct URL to `/academic` or another student's task submission. | Denied; redirected safely with zero data exposure. | `PENDING` |
| **SEQ-16** | `GUARDIAN` | Log in as Guardian. Inspect family portal (`/guardian`). | Displays only authorized linked student(s). No access to unlinked students or institution configuration. | `PENDING` |
| **SEQ-17** | `GUARDIAN` | Attempt direct URL to `/admin/users` or `/virtual-classrooms`. | Denied; redirected to guardian home. | `PENDING` |

#### National & Global Technical Roles (`NATIONAL_ADMIN`, `SUPER_ADMIN`, `AUDITOR`)

| Scenario ID | Role | Test Action | Expected Verification | Current Status |
|---|---|---|---|---|
| **SEQ-18** | `NATIONAL_ADMIN` | Log in as National Admin. Inspect `/admin/institutions` and Onboarding wizard. | Full country-wide MEN/DANE catalog explorer visible. Catalog sync button active. Cannot access SuperAdmin technical health console. | `PENDING` |
| **SEQ-19** | `SUPER_ADMIN` | Log in as Super Admin. Access `/operations/health` and `/operations/tenant-diagnostics`. | Global Technical Operations Console and Tenant Diagnostics load properly. DANE search succeeds. | `PENDING` |
| **SEQ-20** | `AUDITOR` | Inspect role status in database / UI. | Conceptual/unimplemented role. No active auditor credentials in registry. Attempting invalid auditor role tokens rejects with 401. | `PENDING` |

#### Cross-Session Security & Context Sanitization

| Scenario ID | Role | Test Action | Expected Verification | Current Status |
|---|---|---|---|---|
| **SEQ-21** | Session Switch | Log out from `MUNICIPALITY_ADMIN` (with active context) and log in as `STUDENT`. | All territorial context state (`pevn_active_institution_id`, `pevn_active_institution_name`) is wiped. Student sees only student portal with zero territorial traces. | `PENDING` |
| **SEQ-22** | Session Switch | Log out from `RECTOR` and log in as `TEACHER`. | Institutional administrative options disappear immediately from sidebar. | `PENDING` |

---

## 13. Regression Risks and Rollback Instructions

### 13.1 Regression Risk Assessment
- **Risk:** Low. The changes strictly preserve existing route guards, enhance state persistence during silent token refresh, and add destination restoration. No database schemas, migrations, or backend API contracts were altered.
- **Isolation:** Multi-tenant boundaries and anti-IDOR filters remain strictly enforced at both backend and frontend layers.

### 13.2 Rollback Instructions
If rollback is required, only the 5 modified files in the frontend need to be restored:
```bash
git checkout origin/main -- frontend/src/App.tsx frontend/src/components/auth/RequireAuth.tsx frontend/src/pages/admin/InstitutionsView.tsx frontend/src/context/AuthContext.tsx frontend/src/layouts/RootLayout.tsx
rm frontend/src/test/CrossRoleNavigationAudit.test.tsx
```
*Note: Do NOT execute `git reset --hard` or `git clean -fd`, as this would erase uncommitted work from concurrent audit and stabilization tasks.*

---

## 14. Final Git Status

```
Changes not staged for commit:
	modified:   frontend/src/App.tsx
	modified:   frontend/src/components/auth/RequireAuth.tsx
	modified:   frontend/src/components/student/StudentTaskDetailModal.tsx
	modified:   frontend/src/context/AuthContext.tsx
	modified:   frontend/src/layouts/RootLayout.tsx
	modified:   frontend/src/pages/Dashboard.tsx
	modified:   frontend/src/pages/academic/GuardiansView.tsx
	modified:   frontend/src/pages/academic/StudentsView.tsx
	modified:   frontend/src/pages/admin/InstitutionsView.tsx
	modified:   frontend/src/pages/operations/TenantDiagnosticsView.tsx
	modified:   frontend/src/test/Academic.test.tsx
	modified:   frontend/src/test/RoleNavigationFunctional.test.tsx
	modified:   frontend/src/test/StudentPortal.test.tsx
	modified:   frontend/tsconfig.tsbuildinfo

Untracked files:
	docs/reports/PEVN_NTA10_R8_TENANT_DIAGNOSTICS_DANE_SEARCH_FIX.md
	docs/reports/PEVN_RBAC_AUDIT_01_CROSS_ROLE_FUNCTIONAL_COHERENCE.md
	docs/reports/PEVN_RBAC_AUDIT_02_CROSS_ROLE_NAVIGATION_AND_INTERFACE_COHERENCE.md
	frontend/src/test/CrossRoleNavigationAudit.test.tsx
	frontend/src/test/TenantDiagnosticsSearch.test.tsx
```

---

## 15. Certification Gate Decision

**Final Status:**  
`CONDITIONAL PASS — TERRITORIAL ACCEPTANCE RECORDED; INSTITUTIONAL VALIDATION PENDING`

**Justification:**  
- **Automated Validation:** 100% verified (184/184 frontend tests passed, 27/27 backend security tests passed, TypeScript clean with 0 errors, production build completed in 6.44s).
- **Manual Acceptance Completed:** The operator has manually verified and certified 8 scenarios:
  - `ACC-NAV-01` (Académica context auto-continuation workflow)
  - `ACC-NAV-02` (Aulas Virtuales context auto-continuation workflow)
  - `SEQ-01` (DEPARTMENT_ADMIN identity, level 80, Vichada departmental scope)
  - `SEQ-02` (DEPARTMENT_ADMIN cross-department access prevention)
  - `SEQ-03` (DEPARTMENT_ADMIN active context persistence across page refresh)
  - `SEQ-04` (MUNICIPALITY_ADMIN identity, level 70, Puerto Carreño municipal scope)
  - `SEQ-05` (MUNICIPALITY_ADMIN cross-municipality access prevention)
  - `SEQ-06` (MUNICIPALITY_ADMIN municipal user-management scope restrictions)
- **Pending Checks:** Scenarios `SEQ-07` through `SEQ-22` (covering `RECTOR`, `COORDINATOR`, `TEACHER`, `STUDENT`, `GUARDIAN`, `NATIONAL_ADMIN`, `SUPER_ADMIN`, and cross-session security) remain `PENDING` awaiting operator execution.
- Final platform certification (`PASS`) will only be awarded once all cross-role scenarios have been executed and certified by the human operator.

---

## 16. Audit Extension Note (RBAC-AUDIT-02-R3)

For the forensic diagnosis, targeted remediation, and regression verification of Student/Guardian performance, cross-session isolation, and canonical scope label correction (`COORDINATOR` -> `Institucional`, `MUNICIPALITY_ADMIN` -> `Territorial`), see the companion report:  
👉 [`docs/reports/PEVN_RBAC_AUDIT_02_R3_STUDENT_GUARDIAN_PERFORMANCE_SESSION_ISOLATION_AND_SCOPE_LABELS.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PEVN_RBAC_AUDIT_02_R3_STUDENT_GUARDIAN_PERFORMANCE_SESSION_ISOLATION_AND_SCOPE_LABELS.md)
