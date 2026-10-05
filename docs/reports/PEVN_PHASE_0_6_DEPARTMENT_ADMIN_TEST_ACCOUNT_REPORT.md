# PEVN — Dedicated DEPARTMENT_ADMIN Manual-Test Account Report
## Phase 0.6 — Territorial Administration & Supervision Manual Validation Gate

**Document ID:** `PEVN-REPORT-PHASE-0.6-DEPARTMENT-ADMIN-001`  
**Governing Baseline:** Phase 0.5/0.6 Certified RBAC Model (`docs/reports/PEVN_PHASE_0_5_RBAC_IMPLEMENTATION_REPORT.md`)  
**Provisioning Date:** 2026-10-05  
**Author:** Antigravity AI Agent (Pair Programming with Product Owner)  
**Final Status:** `PASS — TEST ACCOUNT PROVISIONED AND TECHNICALLY VERIFIED`

---

## 1. Executive Summary

In execution of the controlled manual validation runbook for the **9 canonical roles** of PEVN, a dedicated, isolated development manual-test account has been successfully provisioned for the **`DEPARTMENT_ADMIN`** role (`Administrador Departamental`).

The provisioning strictly adhered to all non-negotiable safety constraints:
- **Zero changes to RBAC logic or canonical role definitions:** The RBAC architecture, hierarchy levels, and permissions were not modified.
- **Pre-flight collision verification:** Confirmed that neither `department_admin` nor `department_admin@pevn.edu.co` existed in the database.
- **Isolated role assignment:** The user is assigned strictly to `department_admin` (Level 80) with exactly **17 atomic permissions**.
- **No Wildcard:** Verified that `*:*` is completely absent.
- **Preservation of Existing Accounts:** The existing `admin_nacional` (`superadmin`, Level 100) and `national_admin` (`national_admin`, Level 90) test accounts remain 100% untouched.

---

## 2. Pre-Flight Findings

Prior to inserting any record, a read-only audit of the development database (`pevn_db`) was performed:

| Pre-Flight Check | Result | Verification Details |
|---|---|---|
| **Canonical Role Existence** | **CONFIRMED** | `roles.name = 'department_admin'` |
| **Role UUID** | `b47d20c8-0dd4-4ae6-b328-13774ccbdde1` | Matches canonical database catalog |
| **Display Name** | Administrador Departamental | Human-readable role description |
| **Hierarchy Level** | **80** | Subordinate to `SUPERADMIN` (100) and `NATIONAL_ADMIN` (90) |
| **Atomic Permission Count** | **17** | Exactly matches Phase 0.4R / 0.5 specification |
| **Universal Wildcard (`*:*`)** | **ABSENT** | Verified `*:*` is not in `role_permissions` |
| **Account Collision Check** | **ZERO COLLISIONS** | Query for `department_admin` / `department_admin@pevn.edu.co` returned 0 records |
| **Synthetic Document Check** | **ZERO COLLISIONS** | Document `CC 1000000003` was completely unassigned |
| **Valid Department Catalog** | **CONFIRMED** | Department Code `11` (`CAPITAL BOGOTÁ, D.C.`, UUID `7b774116-56f1-4199-ac63-ff646e7e327b`) exists and is active |

---

## 3. Created Test Account

The test account was provisioned using the dedicated CLI tool [`backend/app/cli/create_department_admin.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/create_department_admin.py) with standard RFC 9106 Argon2id password hashing:

| Field | Value | Source Table / Schema |
|---|---|---|
| **User ID** | `dd44ceb4-f5ca-4b5c-a801-0b4490125258` | `users.id` |
| **Username** | `department_admin` | `users.username` |
| **Email** | `department_admin@pevn.edu.co` | `users.email` |
| **Full Name** | Administrador Departamental — Manual Test | `users.first_name`, `users.last_name` |
| **Document Type / Number** | `CC` `1000000003` | `users.document_type`, `users.document_number` |
| **Active Status** | `True` | `users.is_active` |
| **Verification Status** | `True` | `users.is_verified` |
| **Institution ID** | `None` (Territorial Scope) | `users.institution_id` |
| **Password Storage** | Cryptographic hash with Argon2id | `users.hashed_password` (Salted, RFC 9106) |
| **Created At** | `2026-10-05 18:48:26.904657+00:00` | `users.created_at` |

---

## 4. Persisted Role Verification

A join between `users`, `user_roles`, and `roles` confirmed that the user is linked exclusively to the single canonical role:

* **Assigned Role Count:** Exactly `1`
* **Role Identifier (UUID):** `b47d20c8-0dd4-4ae6-b328-13774ccbdde1`
* **Canonical Role Name:** `department_admin`
* **Role Hierarchy Level:** `80`
* **Active Status:** `is_active = True`
* **Assigned Scoping Columns:** `institution_id = NULL`, `campus_id = NULL`

---

## 5. Territorial Scope Verification

In Colombian educational governance and the certified PEVN domain architecture:
1. **Relational Schema Representation:** Subnational territorial entities are defined in `departments` and `municipalities`. The `users` and `user_roles` tables maintain institutional and campus references (`institution_id`, `campus_id`), with `NULL` denoting non-institutional (territorial or national) administrative scope.
2. **Assigned Territorial Entity:** Department Code **`11`** (`CAPITAL BOGOTÁ, D.C.`, Department UUID: `7b774116-56f1-4199-ac63-ff646e7e327b`).
3. **Application & Service Scoping:**
   - In `TerritorialAnalyticsService`, query telemetry and DANE indicators resolve jurisdiction via `_resolve_department_code_from_scope(scope)`.
   - The user's metadata in the audit log explicitly records `{"department_code": "11", "department_name": "CAPITAL BOGOTÁ, D.C."}`.

---

## 6. Permission Verification

A direct SQL query to `role_permissions` joined with `permissions` confirmed that the user resolves exactly **17 atomic permissions** (and zero extra permissions):

| # | Permission String | Module / Resource | Action | Purpose in Departmental Supervision |
|---|---|---|---|---|
| 01 | `academic_assignments:read` | `academic_assignments` | `read` | Read-only inspection of institutional academic workloads |
| 02 | `academic_periods:read` | `academic_periods` | `read` | Read-only inspection of school calendar periods |
| 03 | `academic_years:read` | `academic_years` | `read` | Read-only inspection of academic years and active vigencias |
| 04 | `communications:read` | `communications` | `read` | Read-only monitoring of institutional and territorial notices |
| 05 | `enrollments:read` | `enrollments` | `read` | Read-only inspection of official SIMAT student enrollments |
| 06 | `grades:read` | `grades` | `read` | Read-only inspection of official curricular evaluation grades |
| 07 | `groups:read` | `groups` | `read` | Read-only inspection of classroom groups and seating capacity |
| 08 | `guardians:read` | `guardians` | `read` | Read-only verification of family linkages |
| 09 | `incidents:read` | `incidents` | `read` | Macro-supervision of school coexistence incident metrics |
| 10 | `institutions:read` | `institutions` | `read` | Read-only inspection of DANE institutional catalog |
| 11 | `news:read` | `news` | `read` | Read-only viewing of educational community news |
| 12 | `recordings:read` | `recordings` | `read` | Telemetry audit of virtual classroom sessions |
| 13 | `students:read` | `students` | `read` | Read-only oversight of student census and inclusion data |
| 14 | `subjects:read` | `subjects` | `read` | Read-only review of departmental curricular study plans |
| 15 | `teachers:read` | `teachers` | `read` | Inspection of appointed teaching staff |
| 16 | `users:read` | `users` | `read` | Read-only verification of user accounts within jurisdiction |
| 17 | `virtual_classrooms:read` | `virtual_classrooms` | `read` | Tele-audit of virtual room connectivity and usage |

---

## 7. Wildcard Verification

- **Wildcard Permission `*:*`:** **ABSENT**
- **Partial Wildcards (`*` in any permission string):** **ABSENT**
- The account has no universal bypass capabilities and is strictly bounded by FastAPI's `require_permission` dependency.

---

## 8. Existing Account Integrity Check

A direct read-only query to `users` and `user_roles` confirmed that no existing accounts were altered:

1. **`admin_nacional` (SUPER_ADMIN):**
   - User ID: `dab63ad2-bf47-4efd-9111-2011864c80e1`
   - Role: `superadmin` (Level 100)
   - Wildcard: `*:*` retained
   - Active: `True`
2. **`national_admin` (NATIONAL_ADMIN):**
   - User ID: `165eab38-8643-4ecc-9dc8-afcbe4265e9e`
   - Role: `national_admin` (Level 90)
   - Atomic Permissions: Exactly 30
   - Active: `True`
3. **Institutional Users (Rectores, Teachers, Students, Guardians):**
   - All pre-existing test fixtures and accounts remain completely intact.

---

## 9. Audit Record

The creation event was captured in the immutable audit log table (`audit_logs`) via `app.audit.service.audit_service`:

* **Audit Log ID:** `654479f2-08f0-4598-8f7e-2292e1bb9ee6`
* **Event Type:** `user.created` (`AuditEventType.USER_CREATED`)
* **Actor ID:** `dd44ceb4-f5ca-4b5c-a801-0b4490125258`
* **Target ID:** `dd44ceb4-f5ca-4b5c-a801-0b4490125258`
* **Target Type:** `user`
* **Success:** `True`
* **Metadata:**
  ```json
  {
    "role": "department_admin",
    "department_code": "11",
    "department_name": "CAPITAL BOGOTÁ, D.C.",
    "source": "cli"
  }
  ```

---

## 10. Manual Testing Instructions

The account is immediately available for browser-based manual validation:

* **Login URL:** [http://localhost:3000/login](http://localhost:3000/login)
* **Username:** `department_admin` (or `department_admin@pevn.edu.co`)
* **Password:** `PevnDepartment2026!*`

---

## 11. Exact Expected RBAC Behavior

| Area / Feature | Expected Frontend / Backend Behavior |
|---|---|
| **Header Badge** | Displays `Roles asignados: department_admin` |
| **Permissions Count** | Displays `Permisos atómicos (17)` (No `*:*` wildcard) |
| **Territorial Card** | Renders **"Supervisión Territorial • Secretaría de Educación"** card linking to `/analytics/territorial` |
| **National Provisioning Card** | **HIDDEN:** The card `/admin/institutions` is hidden (reserved for `SUPER_ADMIN` and `NATIONAL_ADMIN`) |
| **Institutional Directive Cards** | **HIDDEN:** The 8 directive cards (Años Lectivos, Grupos, Matrículas, etc.) in `/dashboard` are hidden |
| **Direct Route `/academic`** | Redirects to `/dashboard` unless an active institution context is selected for read-only inspection |
| **Operational Mutations (403)** | Any attempt to call `POST /api/v1/groups`, `POST /api/v1/evaluations/grades`, or `POST /api/v1/incidents` is rejected with `403 Forbidden` |

---

## 12. Artifacts & Database Changes

### Files Added / Modified
* **Added:** [`backend/app/cli/create_department_admin.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/create_department_admin.py) (Dedicated CLI utility following repository conventions)
* **Added:** [`docs/reports/PEVN_PHASE_0_6_DEPARTMENT_ADMIN_TEST_ACCOUNT_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PEVN_PHASE_0_6_DEPARTMENT_ADMIN_TEST_ACCOUNT_REPORT.md) (This report)

### Database Records Inserted
* `users`: 1 record (`id = 'dd44ceb4-f5ca-4b5c-a801-0b4490125258'`, `username = 'department_admin'`)
* `user_roles`: 1 record linking user `dd44ceb4-...` to role `b47d20c8-...` (`department_admin`)
* `audit_logs`: 1 record (`id = '654479f2-08f0-4598-8f7e-2292e1bb9ee6'`, `event_type = 'user.created'`)

---

## 13. Final Gate Status

$$\mathbf{PASS\ —\ TEST\ ACCOUNT\ PROVISIONED\ AND\ TECHNICALLY\ VERIFIED}$$

*The dedicated `DEPARTMENT_ADMIN` test identity is fully established, verified against the database and authorization service, and ready for human manual browser validation. No further provisioning tasks were executed.*
