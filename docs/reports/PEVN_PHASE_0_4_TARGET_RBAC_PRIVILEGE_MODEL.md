# PEVN — Phase 0.4R: Target RBAC Privilege Model & Owner Decisions
## Forensic Privilege Model, Authority Boundaries & Functional Preservation Blueprint
### SUPER_ADMIN vs NATIONAL_ADMIN — Evidence Reconciliation & Target Model for Owner Decision

> **Standard:** PEVN AI Software Factory v1.2 — Implementation Evidence & Reporting Standard  
> **Document ID:** `docs/reports/PEVN_PHASE_0_4_TARGET_RBAC_PRIVILEGE_MODEL.md`  
> **Classification:** Security Architecture, Privilege Engineering & Governance Design (Audit & Documentation Reconciliation Only)  
> **Audit Date:** 2026-10-03  
> **Author:** AI Systems Architect & Security Certification Specialist  
> **Repository Commit Baseline Analyzed:** `9025d3d14e1f421bbd0eff62c64487003a52a06a` (`9025d3d`)  
> **Prior Reviewed Baseline:** `18cec417ee25c65e9fdb5ffd4cb59119745b4a7a` (`18cec41`)  
> **Final Gate Status:** **DESIGN PASS — EVIDENCE RECONCILED — OWNER DECISION REQUIRED**  
> **Product Code Modification Status:** **STRICTLY ZERO PRODUCT CODE MODIFIED (AUDIT & DOCUMENTATION RECONCILIATION ONLY)**

---

## 1. Executive Summary

This forensic report constitutes the **Phase 0.4R Evidence Reconciliation and Documentation Correction** for the Plataforma Educativa Virtual Nacional (PEVN). Its primary mandate is to correct evidence references, terminology, and source-versus-target distinctions in the Phase 0.4 target authorization model before any system owner decisions or code implementations are authorized.

### Core Governing Principle
$$\text{\textbf{FUNCTIONALITY}} + \text{\textbf{CORRECT ROLE}} + \text{\textbf{CORRECT SCOPE}} = \text{\textbf{PRESERVE}}$$

Enterprise authorization refactoring must not disrupt working capabilities. This report enforces a rigorous distinction across seven independent layers of the platform architecture:
1. **Technical Role:** The technical identity classification assigned to the user token (`SystemRole`).
2. **Organizational Authority:** The legal, administrative, or statutory mandate within the Colombian educational system.
3. **Permission:** The atomic action key evaluated by the authorization engine (`resource:action`).
4. **Tenant / Institution Scope:** The geographic or DANE institutional boundary within which an action may legally operate.
5. **Resource-Level Authorization:** Specific record-level constraints (Anti-IDOR, teacher workload assignment, student enrollment, civil kinship).
6. **UI Visibility:** Presentation-layer rendering of links, buttons, and views in the client application.
7. **Backend Authorization:** Server-side enforcement executed via FastAPI dependency injection and database session queries.

A UI visibility defect does not imply that the underlying backend permission is erroneous. Furthermore, holding a permission in a technical role does not confer automatic statutory authority, and national scope does not grant automatic license to execute tenant-scoped operations without explicit institutional context.

### Core Findings of Phase 0.4R:
1. **Separation of Platform Access from Government Authority:**  
   PEVN manages platform digital accounts; it does not issue official government decrees. For example, issuing a cryptographic Rector onboarding invitation (`POST /institutions/{id}/rector-invitation`) is a platform credential workflow, distinct from statutory ministerial appointment under Colombian administrative law (Decreto 1278 de 2002 / Ley 715 de 2001).
2. **Decoupling Technical Global Authority from Educational Administration:**  
   `SUPER_ADMIN` is the technical custodian of platform uptime, database health, APM telemetry, security monitoring, and configuration. SuperAdmin is not an educational authority and must not become the routine operational administrator of school records.
3. **Accurate Assessment of National Admin Runtime Behavior:**  
   Correction of preliminary wording: `national_admin` operational capabilities are not \"unusable in production\" (PEVN is not nationally deployed). In current/local runtime, the backend *does* support cross-institution operations by National Admin when `institution_id_override` is supplied. The runtime failures observed in local testing occur because the current frontend views do not supply an **Institution Context Selector**, passing `None` as the override.
4. **Preservation of Certified Operational Roles:**  
   The current capabilities of the protected operational roles (**Rector**, **Academic Coordinator**, **Coexistence Coordinator**, **Teacher**, **Student**, and **Guardian**) are fully verified by repository tests and domain services, and must remain preserved without functional reduction.
5. **Mandatory Owner Decision Gate:**  
   All governance and privilege boundary choices are formulated as neutral options marked **OWNER DECISION REQUIRED** with **Final Owner Decision: PENDING**.

---

## 2. Scope and Non-Scope

### 2.1 In-Scope (Documentation & Forensic Design Only)
- Forensic verification of all 102 canonical permissions defined in `backend/app/services/rbac_bootstrap_service.py`.
- Source analysis of role configurations in `ROLE_PERMISSIONS_CONFIG` and `CANONICAL_ROLES`.
- Analysis of tenancy resolution across all 18 endpoint files implementing `_resolve_institution_id()`.
- Audit of client-side navigation guards and route declarations in `App.tsx`, `RequireAuth.tsx`, `AuthContext.tsx`, `RootLayout.tsx`, and `Dashboard.tsx`.
- Formulation of neutral architectural options for system owner decisions.

### 2.2 Strict Non-Scope (Zero Product Implementation)
- **Zero product source code modifications** across `backend/app/**` and `frontend/src/**`.
- **Zero database schema changes, migrations, or Alembic revisions.**
- **Zero alterations to runtime RBAC seed tables or configurations.**
- **Zero modifications to existing automated tests.**
- **Zero Git commits or pushes.**

---

## 3. Evidence Baseline

Direct inspection of repository source code at commit `9025d3d` establishes the following verified baseline:

| Metric | Source Reference | Verified Source Count | Forensic Notes |
| :--- | :--- | :---: | :--- |
| **Canonical Permissions** | `rbac_bootstrap_service.py:CANONICAL_PERMISSIONS` | **102** | 102 discrete atomic tuples across 26 domain modules |
| **NATIONAL_ADMIN Permissions** | `rbac_bootstrap_service.py:ROLE_PERMISSIONS_CONFIG` | **72** | 72 explicit permission strings (0 wildcard) |
| **SUPERADMIN Permissions** | `rbac_bootstrap_service.py:ROLE_PERMISSIONS_CONFIG` | **1** | Universal wildcard `["*:*"]` evaluated dynamically |
| **Canonical Seeded Roles** | `rbac_bootstrap_service.py:CANONICAL_ROLES` | **11** | Seeded roles persisted into PostgreSQL `roles` table |
| **SystemRole Enum Members** | `backend/app/core/security/interfaces.py:SystemRole`| **13** | 11 canonical roles + `support` + `observer` (unseeded) |
| **Backend Endpoint Routers** | `backend/app/api/v1/endpoints/*.py` (excl. `__init__`)| **27** | REST controllers handling platform operations |
| **Tenancy Resolution Endpoints**| Routers implementing `_resolve_institution_id()` | **18** | Endpoints enforcing fail-closed multi-tenant scoping |
| **Backend Test Suites** | `backend/tests/test_*.py` | **50** | 50 test files (52 total `.py` files in `backend/tests/`) |
| **Frontend Test Suites** | `frontend/src/test/*.test.ts*` | **18** | 18 test files (19 total files in `frontend/src/test/`) |

### Repository Distinction: Canonical Seeded Roles vs. Enum Values
In `backend/app/core/security/interfaces.py`, the `SystemRole` enum defines 13 values:
```python
class SystemRole(str, Enum):
    SUPERADMIN = "superadmin"
    NATIONAL_ADMIN = "national_admin"
    DEPARTMENT_ADMIN = "department_admin"
    MUNICIPALITY_ADMIN = "municipality_admin"
    INSTITUTION_ADMIN = "institution_admin"
    RECTOR = "rector"
    ACADEMIC_COORDINATOR = "academic_coordinator"
    TEACHER = "teacher"
    STUDENT = "student"
    GUARDIAN = "guardian"
    SUPPORT = "support"          # Non-canonical / Unseeded
    OBSERVER = "observer"        # Non-canonical / Unseeded
    COORDINATOR = "coordinator"
```
**Forensic Reality:**
`SUPPORT` and `OBSERVER` exist only as enum definitions in Python code; they are **NOT** present in `CANONICAL_ROLES` or `ROLE_PERMISSIONS_CONFIG`, are not seeded into the database, have no assigned permissions, and have no corresponding frontend routes. Therefore, the active, functional RBAC model consists strictly of **11 canonical roles**.

---

## 4. Current RBAC Architecture

PEVN implements a 5-layer authorization pipeline evaluated on each incoming API request:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. AUTHENTICATION                               │
│  Validates identity via JWT volatile Bearer token & HttpOnly refresh   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                        2. SYSTEM ROLE & LEVEL                          │
│  Identifies actor type: SystemRole with numeric hierarchy (10 - 100)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                   3. TENANT / ORGANIZATIONAL SCOPE                     │
│  Enforces geographic boundary: National, Territorial, or Institutional │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                     4. ATOMIC PERMISSION CHECK                         │
│  Granular resource:action evaluated against canonical role mappings    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                   5. RESOURCE-LEVEL AUTHORIZATION                      │
│  Anti-IDOR: Verified Workload, SIMAT Enrollment, or Civil Kinship      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Role vs Authority vs Permission vs Scope

To prevent architectural ambiguity, the platform defines clear conceptual boundaries across seven dimensions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE SEVEN LAYERS                                       │
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│ 1. Technical Role        │ Identity category in JWT (`rector`, `national_admin`, etc.) │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 2. Organizational Mandate│ Statutory or legal authority in the Colombian school system │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 3. Permission            │ Atomic authorization gate (`institutions:create`, etc.)     │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 4. Organizational Scope  │ Geographic / DANE boundary (`institution_id`, `department`) │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 5. Resource Authorization│ Specific ownership / kinship check (student profile, etc.)  │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 6. UI Visibility         │ Whether client code renders a navigation link or button     │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 7. Backend Authorization │ Sovereign server-side enforcement that fails closed (403)   │
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

### Critical Distinctions:
- **UI Visibility is NOT Backend Authorization:** The fact that a link appears in the navbar (or is missing) does not determine whether the actor is authorized. The backend authorization layer evaluates security independently of client rendering.
- **Platform Access Management is NOT Official Government Authority:** Registering a user account, generating a token, or assigning a role in PEVN constitutes application security administration. It does not replace official decrees, administrative acts, or statutory gazette appointments required by Colombian law.

---

## 6. SUPER_ADMIN Current State

### 6.1 Technical Authority
In the backend, `superadmin` possesses Level 100 and the universal wildcard `["*:*"]`.
In `interfaces.py` and `rbac_bootstrap_service.py`, `has_permission("*")` evaluates to `True` for every atomic check.

### 6.2 Tenancy Scoping in Local Runtime
In `backend/app/api/v1/endpoints/` (18 files), `_resolve_institution_id()` strictly gates institutional requests. When a `superadmin` makes an institutional API call without supplying `institution_id_override`, the backend raises `403 Forbidden` (`Contexto institucional no disponible`).  
This proves that **the backend already constrains SuperAdmin by tenant isolation**. Superadmin cannot execute institutional operations in a vacuum.

### 6.3 Separation of Technical from Educational Authority
SuperAdmin is the **Administrador Técnico Global** (infrastructure, database health, APM telemetry, security monitoring). SuperAdmin is not an educational authority and has no statutory mandate to administer school curriculum, grade students, or configure local SIEE rules.

### 6.4 Client-Side Bypass [CURRENT LIMITATION]
In `frontend/src/context/AuthContext.tsx`, `hasRole` contains an unconditional bypass:
```typescript
if (user.roles.includes('superadmin')) return true;
```
This causes client-side route guards in `App.tsx` to permit SuperAdmin to navigate to actor-specific portals (`/teacher`, `/student`, `/guardian`), where no underlying teacher or student profile exists, resulting in empty views or runtime network errors.

---

## 7. NATIONAL_ADMIN Current State

### 7.1 Ministerial Mandate vs. Current Implementation
`national_admin` (Level 90) represents the Ministry of Education National (MEN).  
Its documented mandate is macro-governance:
- Institutional catalog DANE/DUE (`/admin/institutions`)
- Rector onboarding platform invitations (`POST /institutions/{id}/rector-invitation`)
- Territorial macro-analytics (`/analytics/territorial`)
- Territorial administrative structure oversight

### 7.2 The 72-Permission Seed Mapping
In `rbac_bootstrap_service.py`, `national_admin` is currently seeded with 72 permissions, including local school operational actions:
- `groups:create`, `groups:update`, `groups:delete`, `groups:assign_director`
- `teachers:create`, `teachers:update`, `teachers:delete`
- `students:create`, `students:update`, `students:delete`
- `guardians:create`, `guardians:update`, `guardians:link_student`
- `enrollments:create`, `enrollments:transfer`, `enrollments:withdraw`, `enrollments:delete`
- `academic_assignments:create`, `academic_assignments:update`, `academic_assignments:delete`
- `academic_years:create`, `academic_years:update`, `academic_years:close`, `academic_years:delete`
- `academic_periods:create`, `academic_periods:update`, `academic_periods:close`
- `subjects:create`, `subjects:update`, `subjects:delete`
- `virtual_classrooms:create`, `virtual_classrooms:manage`
- `recordings:manage`, `recordings:delete`
- `incidents:create`, `incidents:update`, `incidents:close`

### 7.3 Accurate Runtime Behavior Analysis
- **Correction of Previous Description:** In previous documentation drafts, these capabilities were described as \"dormant/unusable in production\". This wording was technically inaccurate (PEVN is not in production deployment).
- **Actual Runtime State:** The backend code in all 18 institutional endpoints **already explicitly supports** National Admin cross-institution operations if an `institution_id_override` parameter is provided.
- **The True Operational Bottleneck:** When a National Admin attempts these operations from the current web frontend, the call fails closed with `403 Forbidden` (`Contexto institucional no disponible`) because **the current frontend UI does not provide an Institution Context Selector** to supply the `institution_id_override`.
- **Architectural Policy Question:** Does the Ministry of Education legitimately intend for National Administrators to perform local school mutations (e.g. creating classroom groups or enrolling students), or was this broad permission seed an early scaffolding artifact? This question requires an explicit owner decision.

---

## 8. Tenant/Institution Context Behavior

### Forensic Evidence from Backend Endpoints
Inspection of all 18 endpoint files in `backend/app/api/v1/endpoints/*.py` that resolve tenancy reveals an identical, uniform implementation:
```python
def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID | None:
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override

    if current_user.institution_id:
        return current_user.institution_id

    raise AuthorizationError("Contexto institucional no disponible.")
```

### Findings:
1. **Backend Capability is Present:** The backend authorization layer was intentionally engineered to allow both `SUPERADMIN` and `NATIONAL_ADMIN` to operate on tenant resources when `institution_id_override` is provided.
2. **Frontend Context Delivery is Missing:** The current user interface has no mechanism for a national user to select an institution and pass `?institution_id=<UUID>`.
3. **Fail-Closed Protection:** Because the override is `None` and national accounts have `current_user.institution_id = None`, the backend safely aborts execution with `AuthorizationError`. Multi-tenant isolation remains unbreached.

---

## 9. Frontend Visibility Findings

| Component / Route | Current Implementation State | Classification | Forensic Finding |
| :--- | :--- | :---: | :--- |
| `/dashboard` | Direct card rendering in `Dashboard.tsx` | `[CURRENT LIMITATION]` | `isDirective` includes territorial administrators, displaying school management cards that fail with 403 when clicked |
| `/admin/institutions`| Rendered for national roles in `RootLayout.tsx` | `[EXISTING]` | Coherent for national administrators; lacks territorial directory filtering for SED/SEM |
| `/analytics/territorial`| Rendered via `hasPermission('institutions:read')` | `[CURRENT LIMITATION]` | Because `rector` has `institutions:read`, the macro-analytics link is erroneously exposed to school rectors |
| `/academic` | Rendered without role guard in `App.tsx` | `[CURRENT LIMITATION]` | Route lacks a role guard wrapper; navbar renders link to Superadmin; backend controllers fail closed |
| `/virtual-classrooms` | Rendered via `virtual_classrooms:read` | `[CURRENT LIMITATION]` | Exposed to National Admin without institution context; fails closed in MeetingService |
| `/teacher` | Protected by `roles={['teacher']}` in `App.tsx` | `[CURRENT LIMITATION]` | `hasRole` short-circuit in `AuthContext.tsx` allows SuperAdmin to bypass guard into empty portal |
| `/student` | Protected by `roles={['student']}` in `App.tsx` | `[CURRENT LIMITATION]` | SuperAdmin bypass allows navigation to student portal; fails closed in StudentPortalService |
| `/guardian` | Protected by `roles={['guardian']}` in `App.tsx` | `[CURRENT LIMITATION]` | SuperAdmin bypass allows navigation to guardian portal; fails closed in GuardianPortalService |

---

## 10. Backend Authorization Findings

### 10.1 The Rector Invitation Dependency Chain
In `backend/app/api/v1/endpoints/institutions.py`:
- Line 680: `POST /{institution_id}/rector-invitation` enforces `Depends(require_permission("users", "create"))`.
- Line 729: `POST /{institution_id}/rector/revoke` enforces `Depends(require_permission("users", "create"))`.
- However, `CANONICAL_PERMISSIONS` in `rbac_bootstrap_service.py` already defines:
  `("users", "create_rector", "Emitir invitación criptográfica para nuevo Rector")`.

**Functional Preservation Dependency:**
Removing `users:create` from `national_admin` before updating lines 680 and 729 to `users:create_rector` would immediately break working Rector invitations in the platform.

### 10.2 Independent Institutional User Provisioning
In `teachers.py` and `students.py`:
- Teacher account provisioning is protected by `require_permission("teachers", "create")`.
- Student account provisioning is protected by `require_permission("students", "create")`.
- Guardian onboarding is protected by `require_permission("guardians", "create")`.

**Conclusion:** School directivos do not depend on the broad permission `users:create`. Their user provisioning capabilities are cleanly encapsulated under domain-specific permissions.

---

## 11. Permission Inventory

### Methodology Qualification:
*All 102 canonical permissions were inventoried and classified against available repository source evidence. Where direct endpoint dependencies or automated tests exist (e.g., `users:create` in `institutions.py`, `teachers:create` in `teachers.py`), they are identified. Where explicit endpoint-level enforcement has not been independently mapped in test suites, the matrix notes 'Requires endpoint-level verification before implementation'. The matrix serves as an architectural design baseline, not proof of runtime authorization behavior.*

### Classification Categories:
- **GREEN (PRESERVE):** Legitimate for the role; must remain assigned.
- **YELLOW (PRESERVE WITH SCOPE LIMITATION):** Legitimate capability, but execution requires strict institutional/territorial context resolution.
- **BLUE (READ-ONLY / AUDIT):** Legitimate visibility for macro-analytics, monitoring, or audit, but direct mutation is strictly forbidden.
- **ORANGE (MOVE / DELEGATE):** Capability belongs to another role; must be decoupled from the administrative role.
- **RED (REMOVE FROM ROLE):** Not functionally justified for the role; redundant or erroneous assignment.
- **GRAY (OWNER DECISION REQUIRED):** Policy choice requiring explicit owner sign-off.

| Permission | Domain | Current SUPER_ADMIN | Target SUPER_ADMIN | Current NATIONAL_ADMIN | Target NATIONAL_ADMIN | Current Protected Role(s) | Functional Dependency | Organizational Authority | Scope | Resource Auth | Existing UI | Existing Endpoint | Risk | Classification | Owner Decision | Evidence Reference |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `*:*` | `*` | `FULL (*:*)` | `FULL (AUDIT)` | `NO` | `NONE` | None | Universal emergency bypass | Platform Technical Operator | GLOBAL | None | Admin Shell [EXISTING] | All controllers | CRITICAL | GREEN (PRESERVE) | DECISION 06 | `interfaces.py:SystemRole.SUPERADMIN` |
| `institutions:read` | `institutions` | `FULL (*:*)` | `FULL (TECH)` | `YES` | `FULL (CATALOG)` | rector, coordinator | DANE / DUE Catalog Management | MEN / Technical Operator | NATIONAL | Tenant containment | InstitutionsView.tsx [EXISTING] | institutions.py | HIGH | GREEN (PRESERVE) | NO | `institutions.py:126` |
| `institutions:create` | `institutions` | `FULL (*:*)` | `FULL (TECH)` | `YES` | `FULL (CATALOG)` | None | DANE / DUE Catalog Management | MEN / Technical Operator | NATIONAL | Tenant containment | InstitutionsView.tsx [EXISTING] | institutions.py | HIGH | GREEN (PRESERVE) | NO | `institutions.py:126` |
| `institutions:update` | `institutions` | `FULL (*:*)` | `FULL (TECH)` | `YES` | `FULL (CATALOG)` | None | DANE / DUE Catalog Management | MEN / Technical Operator | NATIONAL | Tenant containment | InstitutionsView.tsx [EXISTING] | institutions.py | HIGH | GREEN (PRESERVE) | NO | `institutions.py:126` |
| `institutions:delete` | `institutions` | `FULL (*:*)` | `OWNER DECISION` | `YES` | `OWNER DECISION` | None | School Record Decommissioning | MEN / Technical Operator | NATIONAL | Tenant containment | InstitutionsView.tsx [EXISTING] | institutions.py | CRITICAL | GRAY (OWNER DECISION) | DECISION 01 | `institutions.py:delete_institution` |
| `users:read` | `users` | `FULL (*:*)` | `FULL` | `YES` | `READ (NATIONAL)` | rector, coordinator | User lookup and auditing | MEN / Directives | NATIONAL / TENANT | Scope containment | UsersView / Modals [EXISTING] | users.py:54 | MEDIUM | GREEN (PRESERVE) | NO | `users.py:list_users` |
| `users:create` | `users` | `FULL (*:*)` | `FULL` | `YES` | `ALIGN TO CREATE_RECTOR` | None | Generic User Account Creation | Technical / Directives | NATIONAL | Scope containment | Modals [EXISTING] | institutions.py:680 | CRITICAL | ORANGE (MOVE / DELEGATE) | NO | `institutions.py:680` |
| `users:create_rector` | `users` | `FULL (*:*)` | `FULL` | `YES` | `FULL (PLATFORM INVITATION)` | None | Rector Invitation Token Generation | MEN Platform Governance | NATIONAL | One-time token | InstitutionsView.tsx [EXISTING] | institutions.py:680 | CRITICAL | GREEN (PRESERVE) | NO | `institutions.py:680` |
| `users:update` | `users` | `FULL (*:*)` | `FULL` | `YES` | `OWNER DECISION (TERRITORIAL)` | None | User Account Status Management | Technical / Territorial | NATIONAL | Scope containment | Modals [EXISTING] | users.py | HIGH | GRAY (OWNER DECISION) | DECISION 02 | `rbac_bootstrap_service.py:238` |
| `users:delete` | `users` | `FULL (*:*)` | `FULL` | `YES` | `OWNER DECISION (TERRITORIAL)` | None | User Account Status Management | Technical / Territorial | NATIONAL | Scope containment | Modals [EXISTING] | users.py | HIGH | GRAY (OWNER DECISION) | DECISION 02 | `rbac_bootstrap_service.py:238` |
| `academic_years:read` | `academic_years` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (MACRO CENSUS)` | rector, coordinator, teacher, student, guardian | Calendar & Period Inspection | School Directives / MEN Census | TENANT / NATIONAL | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | LOW | BLUE (READ-ONLY / AUDIT) | NO | `academic_years.py:63` |
| `academic_years:create` | `academic_years` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_years:update` | `academic_years` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_years:close` | `academic_years` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_years:delete` | `academic_years` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_periods:read` | `academic_periods` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (MACRO CENSUS)` | rector, coordinator, teacher | Calendar & Period Inspection | School Directives / MEN Census | TENANT / NATIONAL | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | LOW | BLUE (READ-ONLY / AUDIT) | NO | `academic_years.py:63` |
| `academic_periods:create` | `academic_periods` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_periods:update` | `academic_periods` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `academic_periods:close` | `academic_periods` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | Calendar Opening / Closing | Rector Official Mandate | INSTITUTION | Institution match | AcademicYearsView.tsx [EXISTING] | academic_years.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_years.py:239` |
| `grades:read` | `grades` | `FULL (*:*)` | `FULL` | `YES` | `FULL` | rector, coordinator, teacher, student, guardian | National Curricular Grade Scale | MEN Curricular Standard | NATIONAL | None | GradesView [EXISTING] | grades.py | LOW | GREEN (PRESERVE) | NO | `grades.py:list_grades` |
| `grades:write` | `grades` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `NONE (TEACHER EXCLUSIVE)` | rector, coordinator, teacher | Submitting Classroom Student Marks | Classroom Teacher Mandate | ASSIGNMENT | Teacher workload | TeacherSieeEvaluationView.tsx [EXISTING] | teacher_portal.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `test_teacher_academic_scope.py` |
| `grades:manage` | `grades` | `FULL (*:*)` | `FULL` | `YES` | `FULL` | None | National Curricular Grade Scale | MEN Curricular Standard | NATIONAL | None | GradesView [EXISTING] | grades.py | LOW | GREEN (PRESERVE) | NO | `grades.py:list_grades` |
| `subjects:read` | `subjects` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher, student | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | subjects.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `subjects.py:resolve_institution` |
| `subjects:create` | `subjects` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | subjects.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `subjects.py` |
| `subjects:update` | `subjects` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | subjects.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `subjects.py` |
| `subjects:delete` | `subjects` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | subjects.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `subjects.py` |
| `groups:read` | `groups` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | groups.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `groups.py:resolve_institution` |
| `groups:create` | `groups` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | groups.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `groups.py` |
| `groups:update` | `groups` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | groups.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `groups.py` |
| `groups:delete` | `groups` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | groups.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `groups.py` |
| `groups:assign_director` | `groups` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | groups.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `groups.py` |
| `teachers:read` | `teachers` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | teachers.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `teachers.py:resolve_institution` |
| `teachers:create` | `teachers` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | teachers.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `teachers.py` |
| `teachers:update` | `teachers` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | teachers.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `teachers.py` |
| `teachers:delete` | `teachers` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | teachers.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `teachers.py` |
| `students:read` | `students` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher, student, guardian | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | students.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `students.py:resolve_institution` |
| `students:create` | `students` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | students.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `students.py` |
| `students:update` | `students` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | students.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `students.py` |
| `students:delete` | `students` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | students.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `students.py` |
| `guardians:read` | `guardians` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, guardian | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | guardians.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `guardians.py:resolve_institution` |
| `guardians:create` | `guardians` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | guardians.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `guardians.py` |
| `guardians:update` | `guardians` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | guardians.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `guardians.py` |
| `guardians:link_student` | `guardians` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | guardians.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `guardians.py` |
| `enrollments:read` | `enrollments` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher, student, guardian | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | enrollments.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `enrollments.py:resolve_institution` |
| `enrollments:create` | `enrollments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | enrollments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `enrollments.py` |
| `enrollments:transfer` | `enrollments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | enrollments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `enrollments.py` |
| `enrollments:withdraw` | `enrollments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | enrollments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `enrollments.py` |
| `enrollments:delete` | `enrollments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | enrollments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `enrollments.py` |
| `academic_assignments:read` | `academic_assignments` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `YES` | `READ (CENSUS AUDIT)` | rector, coordinator, teacher, student, guardian | Institutional Record Inspection | School Staff / MEN Auditor | TENANT / NATIONAL | Scope / Workload | Academic Hub Views [EXISTING] | academic_assignments.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | NO | `academic_assignments.py:resolve_institution` |
| `academic_assignments:create` | `academic_assignments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | academic_assignments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_assignments.py` |
| `academic_assignments:update` | `academic_assignments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | academic_assignments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_assignments.py` |
| `academic_assignments:delete` | `academic_assignments` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | School Entity Lifecycle Mutation | Rector / Coordinator | INSTITUTION | Institution match | Academic Hub Views [EXISTING] | academic_assignments.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `academic_assignments.py` |
| `virtual_classrooms:read` | `virtual_classrooms` | `FULL (*:*)` | `READ (TECHNICAL)` | `YES` | `READ (TELEMETRY)` | rector, coordinator, teacher, student | Virtual Classrooms Inspection | Technical / Directives | NATIONAL / TENANT | Institution match | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | LOW | BLUE (READ-ONLY / AUDIT) | NO | `virtual_classrooms.py:71` |
| `virtual_classrooms:create` | `virtual_classrooms` | `FULL (*:*)` | `FULL (PROVIDER CONFIG)` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Meeting & Recording Control | Teacher / Directives | TENANT | Workload assignment | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `virtual_classrooms.py` |
| `virtual_classrooms:join` | `virtual_classrooms` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION (PRIVACY)` | rector, coordinator, teacher, student | Live Video Class Entry | Teacher (Mod) / Student (View) | ASSIGNMENT / ENROLLMENT | Class roster | Live Meeting View [EXISTING] | virtual_classrooms.py:165 | CRITICAL | GRAY (OWNER DECISION) | DECISION 03 | `virtual_classrooms.py:165` |
| `virtual_classrooms:manage` | `virtual_classrooms` | `FULL (*:*)` | `FULL (PROVIDER CONFIG)` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Meeting & Recording Control | Teacher / Directives | TENANT | Workload assignment | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `virtual_classrooms.py` |
| `recordings:read` | `recordings` | `FULL (*:*)` | `READ (TECHNICAL)` | `YES` | `READ (TELEMETRY)` | rector, coordinator, teacher, student | Virtual Classrooms Inspection | Technical / Directives | NATIONAL / TENANT | Institution match | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | LOW | BLUE (READ-ONLY / AUDIT) | NO | `virtual_classrooms.py:71` |
| `recordings:manage` | `recordings` | `FULL (*:*)` | `FULL (PROVIDER CONFIG)` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Meeting & Recording Control | Teacher / Directives | TENANT | Workload assignment | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `virtual_classrooms.py` |
| `recordings:delete` | `recordings` | `FULL (*:*)` | `FULL (PROVIDER CONFIG)` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Meeting & Recording Control | Teacher / Directives | TENANT | Workload assignment | VirtualClassroomsView.tsx [EXISTING] | virtual_classrooms.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `virtual_classrooms.py` |
| `activities:read` | `activities` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher, student, guardian | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `activities:create` | `activities` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `activities:update` | `activities` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `activities:publish` | `activities` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `activities:close` | `activities` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `activities:delete` | `activities` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `submissions:read` | `submissions` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher, student | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `submissions:create` | `submissions` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | student | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `submissions:update` | `submissions` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | student | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `submissions:return` | `submissions` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `attendance:read` | `attendance` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher, student, guardian | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `attendance:write` | `attendance` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `planning:read` | `planning` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher, student | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `planning:create` | `planning` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `planning:update` | `planning` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `planning:delete` | `planning` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `communications:read` | `communications` | `FULL (*:*)` | `READ` | `YES` | `FULL` | rector, coordinator, teacher, student, guardian | Reading Official Bulletins | Public / Community | NATIONAL / TENANT | None | Portals Views [EXISTING] | communications.py | LOW | GREEN (PRESERVE) | NO | `communications.py:60` |
| `communications:create` | `communications` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | communications.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `communications.py:60` |
| `communications:update` | `communications` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | communications.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `communications.py:60` |
| `communications:publish` | `communications` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | communications.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `communications.py:60` |
| `communications:delete` | `communications` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | communications.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `communications.py:60` |
| `news:read` | `news` | `FULL (*:*)` | `READ` | `YES` | `FULL` | rector, coordinator, teacher, student, guardian | Reading Official Bulletins | Public / Community | NATIONAL / TENANT | None | Portals Views [EXISTING] | news.py | LOW | GREEN (PRESERVE) | NO | `news.py:60` |
| `news:create` | `news` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | news.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `news.py:60` |
| `news:update` | `news` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | news.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `news.py:60` |
| `news:publish` | `news` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | news.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `news.py:60` |
| `news:delete` | `news` | `FULL (*:*)` | `FULL (SYSTEM ALERT)` | `YES` | `FULL (NATIONAL SCOPE ONLY)` | rector, coordinator | Publishing Official Communications | MEN / Directives | NATIONAL / TENANT | Scope containment | Communications Views [EXISTING] | news.py | MEDIUM | YELLOW (PRESERVE WITH SCOPE LIMIT) | NO | `news.py:60` |
| `incidents:read` | `incidents` | `FULL (*:*)` | `AUDIT (TICKET ONLY)` | `YES` | `OWNER DECISION (L. 1620 / 1581)` | rector, coordinator, teacher, student, guardian | Observador del Estudiante Inspection | Convivencia Committee / Family | TENANT / KINSHIP | Kinship / Directorship | Observador Views [EXISTING] | incidents.py | HIGH | GRAY (OWNER DECISION) | DECISION 03 | `incidents.py:60` |
| `incidents:create` | `incidents` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Logging Disciplinary Situations | Teacher / Coexistence Coordinator | INSTITUTION | School faculty | Observador Modal [EXISTING] | incidents.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `incidents.py:60` |
| `incidents:update` | `incidents` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator, teacher | Logging Disciplinary Situations | Teacher / Coexistence Coordinator | INSTITUTION | School faculty | Observador Modal [EXISTING] | incidents.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `incidents.py:60` |
| `incidents:close` | `incidents` | `FULL (*:*)` | `NOT A SA FUNCTION` | `YES` | `OWNER DECISION / REMOVE` | rector, coordinator | Logging Disciplinary Situations | Teacher / Coexistence Coordinator | INSTITUTION | School faculty | Observador Modal [EXISTING] | incidents.py | HIGH | RED (REMOVE FROM ROLE) | DECISION 03 | `incidents.py:60` |
| `siee_policies:read` | `siee_policies` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `siee_policies:manage` | `siee_policies` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `evaluations:read` | `evaluations` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `evaluations:grade` | `evaluations` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `evaluations:adjust` | `evaluations` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `evaluations:close_period` | `evaluations` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `evaluations:reopen_period` | `evaluations` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `evaluations:recovery` | `evaluations` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator, teacher | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `report_cards:read` | `report_cards` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher, student, guardian | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `report_cards:read_group` | `report_cards` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `promotions:preview` | `promotions` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |
| `promotions:execute` | `promotions` | `FULL (*:*)` | `NOT A SA FUNCTION` | `NO` | `NONE (TEACHER / RECTOR)` | rector, coordinator | SIEE Grading & Activity Mutation | Teacher / Rector Exclusive | ASSIGNMENT / INSTITUTION | Workload / Rectorate | Teacher & Directive Views [EXISTING] | evaluation_grades.py | CRITICAL | GREEN (PRESERVE PROTECTED) | NO | `evaluation_grades.py:180` |
| `promotions:read` | `promotions` | `FULL (*:*)` | `READ (DIAGNOSTIC)` | `NO` | `NONE` | rector, coordinator, teacher | Academic Performance Inspection | School Faculty & Directives | TENANT / ASSIGNMENT | Teacher workload / SIMAT | Teacher & Directive Portals [EXISTING] | evaluation_grades.py | MEDIUM | BLUE (READ-ONLY / AUDIT) | DECISION 05 | `test_siee_and_evaluations_api.py` |

---

## 12. Functional Dependency Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL FUNCTIONAL DEPENDENCY CHAINS                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. RECTOR PLATFORM ONBOARDING:                                                         │
│    national_admin ──► users:create_rector ──► POST /institutions/{id}/rector-invitation│
│    ──► RectorOnboardingService ──► One-Time Token ──► Rector Account Created           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. TEACHER ACCOUNT PROVISIONING:                                                       │
│    rector ──► teachers:create ──► POST /teachers/{id}/account/provision               │
│    ──► UserService.provision_institutional_user ──► Teacher Credentials Issued         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. SIMAT STUDENT ACCOUNT PROVISIONING:                                                 │
│    coordinator ──► students:create ──► POST /students/{id}/account/provision           │
│    ──► StudentService ──► Student Portal User Created                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. FAMILY CIVIL KINSHIP BINDING:                                                       │
│    coordinator ──► guardians:link_student ──► POST /students/{id}/guardians/{gid}      │
│    ──► GuardianService ──► student_guardians Record ──► Parental Anti-IDOR Barrier     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. SIEE PERIOD EVALUATION CLOSURE:                                                     │
│    rector ──► evaluations:close_period ──► POST /evaluations/periods/{id}/close       │
│    ──► EvaluationService ──► is_locked=True ──► Grades Immutable                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Existing vs Target vs Future Matrix

To ensure absolute clarity regarding what exists in source versus proposed future functionality, every system route and capability is explicitly categorized:

| Route / Capability | Code / UI Path | Status Category | Operational Notes |
| :--- | :--- | :---: | :--- |
| **Public Landing Page** | `/` (`ComingSoon.tsx`) | `[EXISTING]` | Public informational portal with accurate certified roadmap |
| **Authentication & Login**| `/login` (`Login.tsx`) | `[EXISTING]` | Argon2id verification, JWT issuance, HttpOnly refresh cookie |
| **Password Recovery** | `/auth/forgot-password`, `/auth/reset-password` | `[EXISTING]` | One-time cryptographic recovery tokens with anti-enumeration |
| **Rector Invitation Accept**| `/auth/accept-invitation` | `[EXISTING]` | Verifies single-use cryptographic token and sets password |
| **Guardian Self-Activation**| `/guardian/activate`, `/auth/guardian-activation` | `[EXISTING]` | Public family identity verification against civil record |
| **User Dashboard** | `/dashboard` (`Dashboard.tsx`) | `[EXISTING]` | Role-specific summary and module access cards |
| **Institution Catalog** | `/admin/institutions` (`InstitutionsView.tsx`) | `[EXISTING]` | DANE/DUE institution search, provisioning, and rector invites |
| **Academic Hub** | `/academic` (`AcademicHub.tsx`) | `[EXISTING]` | 8 tabs (Years, Groups, Students, Teachers, Enrollments, etc.) |
| **Teacher Portal** | `/teacher` (`TeacherPortal.tsx`) | `[EXISTING]` | Pedagogical activities, SIEE planilla, attendance, planning |
| **Student Portal** | `/student` (`StudentPortal.tsx`) | `[EXISTING]` | Tasks, submissions, grade review, circular acknowledgments |
| **Guardian Portal** | `/guardian` (`GuardianPortal.tsx`) | `[EXISTING]` | Multi-child switcher, family attendance, report card review |
| **Virtual Classrooms** | `/virtual-classrooms` (`VirtualClassroomsView.tsx`) | `[EXISTING]` | Synchronous meeting management and recordings playback |
| **Territorial Analytics** | `/analytics/territorial` (`TerritorialAnalyticsView.tsx`)| `[EXISTING]` | Macro census and coverage charts for territorial leaders |
| **Missing Academic Guard** | `/academic` in `App.tsx` | `[CURRENT LIMITATION]` | Route lacks explicit role guard in router configuration |
| **Territorial Dashboard Clutter**| `isDirective` in `Dashboard.tsx` | `[CURRENT LIMITATION]` | Exposes school management cards to SED/SEM administrators |
| **SuperAdmin Client Bypass**| `hasRole` in `AuthContext.tsx` | `[CURRENT LIMITATION]` | Short-circuits role checks, permitting navigation to portals |
| **Missing Context Selector**| Frontend Academic & Classrooms Views | `[CURRENT LIMITATION]` | UI lacks school picker to pass `institution_id_override` |
| **System Health Console** | `/admin/health` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed dedicated UI for database pools, Redis, and APM |
| **Technical Config Console**| `/admin/config` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for platform environment flags and gateways |
| **Audit Logs Viewer** | `/admin/audit-logs` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for querying immutable `audit_logs` records |
| **Technical Users Console** | `/admin/users` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for managing root and support technician accounts |
| **RBAC Roles Console** | `/admin/roles` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for inspecting role-permission seed integrity |
| **Territorial Structure** | `/admin/territories` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for managing DANE departmental boundaries |
| **BBB Provider Console** | `/admin/bbb-provider` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for BigBlueButton server cluster telemetry |
| **Integrations Console** | `/admin/integrations` | `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Proposed UI for external interoperability webhooks |

---

## 14. SUPER_ADMIN Target Model

### 14.1 Technical Authority vs. Educational Administration
The target model firmly separates technical platform custody from educational administration:
- **TECHNICAL GLOBAL AUTHORITY:** Retained in full. Superadmin manages machine health, database integrity, APM metrics, token blacklists, and immutable audit logs.
- **EDUCATIONAL ADMINISTRATIVE AUTHORITY:** Not a SuperAdmin mandate. Superadmin does not assign classroom teachers, modify SIEE formulas, or create school courses.
- **SUPPORT ACCESS TO SCHOOL DATA:** Evaluated as an explicit technical option requiring explicit institution context and audit logging.

### 14.2 Domain-by-Domain Analysis (A through R):

| Area | Domain Capability | Target Authority Classification | Target Scope | Proposed UI Access | Technical Rationale & Trade-offs |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | **Platform Health** | FULL TECHNICAL AUTHORITY | Global | `/admin/health` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Real-time monitoring of database pools, Redis cache, and CPU |
| **B** | **Monitoring & Metrics** | FULL TECHNICAL AUTHORITY | Global | Metrics Console `[TARGET — NOT CURRENTLY IMPLEMENTED]` | APM error rates, HTTP latency, and system memory |
| **C** | **Technical Configuration** | FULL TECHNICAL AUTHORITY | Global | `/admin/config` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Environment flags, SMTP server settings, BBB shared secrets |
| **D** | **Security Telemetry** | FULL TECHNICAL AUTHORITY | Global | Security Console `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Rate limit tracking, brute-force alerts, revoked token audits |
| **E** | **Security & Audit Logs** | FULL TECHNICAL AUTHORITY | Global | `/admin/audit-logs` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Read query over PostgreSQL `audit_logs` table |
| **F** | **Technical User Admin** | FULL TECHNICAL AUTHORITY | Global | `/admin/users` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Creating root technicians and unlocking administrative logins |
| **G** | **RBAC / System Admin** | FULL TECHNICAL AUTHORITY | Global | `/admin/roles` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Inspecting database role tables and seed configuration |
| **H** | **Institution Directory** | TECHNICAL CATALOG / AUDIT | Global | `/admin/institutions` `[EXISTING]` | Technical provisioning and DANE code verification |
| **I** | **Territorial Structure** | TECHNICAL CATALOG / AUDIT | Global | `/admin/territories` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Validating DANE geographic code tables |
| **J** | **Academic Data Visibility** | READ/AUDIT (CONTEXT-REQUIRED) | Institutional (`?inst_id=`) | Read-Only Support Modal | Diagnosing database corruption or orphan student records |
| **K** | **Academic Mutation** | NOT A SUPER_ADMIN FUNCTION | None | None (Hidden) | Superadmin never creates groups, enrolls students, or alters grades |
| **L** | **Virtual Classrooms Tech** | READ/AUDIT & PROVIDER CONFIG | Global | `/admin/bbb-provider` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | BigBlueButton cluster health, secret handshake, webhooks |
| **M** | **Recordings Technical** | READ/AUDIT & STORAGE CONFIG | Global | Storage Quota Console `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Disk partition monitoring and object storage retention |
| **N** | **System Communications** | FULL TECHNICAL AUTHORITY | Global | Maintenance Broadcast | Emitting platform-wide scheduled maintenance announcements |
| **O** | **News / Publications** | READ/AUDIT | Global | Portal View `[EXISTING]` | Technical audit of community publications |
| **P** | **Student Incidents (L. 1620)** | AUDIT ONLY (UNDER TICKET) | Institutional (Audit) | None (Protected) | Ley 1581 / Ley 1620 compliance: Superadmin has no casual visibility |
| **Q** | **Evaluation & SIEE** | READ/AUDIT (CONTEXT-REQUIRED) | Institutional (Audit) | Read-Only Audit Viewer | Technical verification of SIEE formula execution during support tickets |
| **R** | **Infrastructure Webhooks** | FULL TECHNICAL AUTHORITY | Global | `/admin/integrations` `[TARGET — NOT CURRENTLY IMPLEMENTED]` | Gov.co interoperability, external webhooks, SIMAT ingestion |

---

## 15. NATIONAL_ADMIN Target Model

### Domain-by-Domain Analysis (A through Y):

| Area | Domain Capability | Legitimate Need? | Target Mode | Target Scope | Operational Owner | What Breaks If Removed? |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **A** | **National Institution Catalog** | **YES** | Full Administration | National | `national_admin` | Inability to maintain DANE/DUE school directory |
| **B** | **DANE Territorial Catalog** | **YES** | Full Administration | National | `national_admin` | Inability to map 32 departments and 1.100+ municipalities |
| **C** | **Institution Provisioning** | **YES** | Full Administration | National | `national_admin` | New institutions cannot be registered in PEVN |
| **D** | **Campus (Sedes) Data** | **YES** | Read-Only / Oversight | National | `rector` | Inability to audit physical school facilities |
| **E** | **Rector Invitation Platform Token**| **YES** | Full Administration | National | `national_admin` | **Critical:** Official rector platform onboarding disabled |
| **F** | **Department Administrators** | **YES** | Full Administration | National | `national_admin` | SED territorial leaders cannot be appointed in platform |
| **G** | **Municipality Administrators** | **CONDITIONAL**| Full Administration (Dec. 04)| National | `national_admin` | SEM municipal leaders cannot be appointed directly by MEN |
| **H** | **National Macro Analytics** | **YES** | Macro Analytics | National | `national_admin` | Loss of national enrollment, coverage, and dropout KPIs |
| **I** | **National Communications** | **YES** | Full (National Scope) | National | `national_admin` | Inability to publish ministerial notices to official schools |
| **J** | **Academic Years & Calendars** | **NO (Read-Only)**| Read-Only Audit | National | `rector` | None. Calendar creation belongs strictly to local Rector |
| **K** | **Groups and Salones** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Classroom quotas are school administrative decisions |
| **L** | **Teachers (Planta Docente)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. School staff records are managed by local directives |
| **M** | **Students (SIMAT)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Student admissions are handled by school secretariats |
| **N** | **Guardians (Acudientes)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Family civil registration is a local school record |
| **O** | **Enrollments (Matrículas)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Student enrollment is managed by local directive staff |
| **P** | **Academic Assignments** | **NO (Read-Only)**| Read-Only Audit | National | `academic_coordinator` | None. Teacher load is determined by school coordinators |
| **Q** | **Grades Catalog** | **YES** | Catalog Management | National | `national_admin` | Inability to maintain national grade levels (Transición - Once) |
| **R** | **Evaluations & SIEE** | **NO** | Excluded | Institutional | `teacher`, `rector` | None. MEN does not grade students or close school periods |
| **S** | **Attendance (Asistencia)** | **NO** | Excluded | Institutional | `teacher` | None. Daily classroom attendance is a teacher duty |
| **T** | **Activities & Tareas** | **NO** | Excluded | Institutional | `teacher` | None. Lesson assignments belong to classroom teachers |
| **U** | **Curricular Planning** | **NO** | Excluded | Institutional | `teacher` | None. Pedagogical planning belongs to classroom teachers |
| **V** | **Convivencia (Ley 1620)** | **CONDITIONAL**| Aggregate KPIs (Dec. 03)| National | `coordinator`, `teacher` | Individual incident details protected by Ley 1581 / Ley 1620 |
| **W** | **Virtual Classrooms** | **NO (Read-Only)**| Aggregate Telemetry | National | `teacher`, `rector` | National officials cannot enter live student video classes |
| **X** | **Recordings** | **NO (Read-Only)**| Storage Audit | National | `teacher` | Managing student recordings is an institutional responsibility |
| **Y** | **News / Periódico Escolar**| **YES** | National Publishing | National | `national_admin` | MEN publishes national educational news; schools publish local |

---

## 16. Protected Operational Roles

### 16.1 Source Evidence on `rector` vs `institution_admin`
Inspection of `backend/app/services/rbac_bootstrap_service.py` (line 57) reveals the explicit source-level annotation:
```python
"name": SystemRole.INSTITUTION_ADMIN.value,  # "institution_admin" (alias/compatibility)
```
and in `CANONICAL_ROLES`:
```python
{"name": "institution_admin", "display_name": "Administrador Institucional", "level": 60, "description": "Alias de compatibilidad institucional para Rector."}
```
**Forensic Reality:**
In the active implementation, `rector` and `institution_admin` possess identical permission sets (exactly 90 permissions each). The role `institution_admin` was established as an architectural compatibility moniker. Whether this alias should be unified or retained as an alias is documented under **Implementation Preconditions**.

### 16.2 Evidence-Based Protection Guarantee
The current functional capabilities of the protected operational roles are verified by automated test suites and domain services, and must be preserved without reduction:
- **`rector` (90 permissions):** Retains school calendar management, SIEE scale approval, academic year closures, promotion acts, and faculty management (`test_academic_api.py`, `test_siee_and_evaluations_api.py`, `test_promotion_governance.py`).
- **`coordinator` / `academic_coordinator` (82 permissions):** Retains teacher workload assignment, group creation, student transfers, daily attendance monitoring, and Ley 1620 coexistence tracking (`test_enrollments_and_assignments.py`, `test_coexistence_incidents_api.py`).
- **`teacher` (45 permissions):** Retains autonomous pedagogical task publishing, SIEE period planilla settlement, attendance tracking, and BigBlueButton class moderation (`test_teacher_portal_api.py`, `test_student_submissions_api.py`, `test_teacher_academic_scope.py`).
- **`student` (19 permissions):** Retains Anti-IDOR homework submission lifecycle, grade review, and BigBlueButton viewer attendance (`test_student_portal_api.py`, `test_activity_resources_and_storage.py`).
- **`guardian` (12 permissions):** Retains multi-child kinship switcher, parental grade monitoring, and attendance alert tracking (`test_guardian_tenant_isolation.py`, `test_identity_family_lifecycle.py`).

### 16.3 Executive Role-Level Functional Matrix:

| Functional Area | SUPER_ADMIN | NATIONAL_ADMIN | Rector | Coordinator | Teacher | Student | Guardian |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Platform Telemetry & Health** | **FULL** | NONE | NONE | NONE | NONE | NONE | NONE |
| **System Security & Audit Logs**| **FULL** | AUDIT | AUDIT (Local) | NONE | NONE | NONE | NONE |
| **National Institution DANE/DUE**| **FULL** | **FULL** | READ (Own) | READ (Own) | NONE | NONE | NONE |
| **Rector Platform Invitation** | **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **Territorial User Governance** | **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **Macro Territorial Analytics** | **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **School Calendar & Years** | CONTEXTUAL | READ | **FULL** | READ | READ | READ | READ |
| **Curricular Groups & Salones** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | NONE |
| **Faculty & Workload Assignment**| CONTEXTUAL | READ | **FULL** | **FULL** | READ (Own) | NONE | NONE |
| **Student SIMAT Enrollment** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | NONE |
| **Family Kinship & Acudientes** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | READ (Own) |
| **Pedagogical Activities (Tasks)**| NONE | NONE | AUDIT | AUDIT | **FULL** | FULL (Submit)| READ |
| **SIEE Grading & Planillas** | NONE | NONE | AUDIT | AUDIT | **FULL** | READ (Own) | READ (Own) |
| **SIEE Scale Parameterization** | NONE | NONE | **FULL** | READ | READ | READ | READ |
| **Period Closing & Locking** | NONE | NONE | **FULL** | NONE | NONE | NONE | NONE |
| **Promotions & Final Records** | NONE | NONE | **FULL** | AUDIT | READ | READ | READ |
| **Daily Classroom Attendance** | NONE | NONE | AUDIT | AUDIT | **FULL** | READ (Own) | READ (Own) |
| **Convivencia Observador (L.1620)**| AUDIT (Ticket)| CONTEXTUAL | **FULL** | **FULL** | **FULL** | READ (Own) | READ (Own) |
| **Virtual Classrooms (BBB)** | TECHNICAL | READ (Stats) | **FULL** | **FULL** | MODERATOR | VIEWER | NONE |
| **Official Communications** | TECHNICAL | FULL (Nation) | **FULL** (School)| **FULL** (School)| READ | READ (Ack) | READ (Ack) |

---

## 17. Owner Decisions Required

The following decisions require explicit owner determination before the subsequent RBAC implementation phase:

### DECISION 01: SUPER_ADMIN Institution-Scoped Technical Context
- **Decision:** How should SuperAdmin access school operational resources during technical support?
- **Current Evidence:** `_resolve_institution_id` in 18 controllers supports `institution_id_override`, but the current UI lacks a context selector.
- **Security Implication:** Without an explicit context, global bypasses lead to ambiguous session states.
- **Functional Implication:** Technical diagnostics require inspecting specific tenant records without granting casual operational editing.
- **Implementation Implication:** Requires implementing an Institution Context Selector modal in `InstitutionsView.tsx` passing `?institution_id=<UUID>`.
- **Technical Options:**
  - *Option A:* Introduce an explicit Institution Context Selector in the UI (`?institution_id=<UUID>`). Superadmin retains global technical authority but operates within explicit institutional context.
  - *Option B:* Superadmin is strictly isolated from school academic views and limited entirely to infrastructure, catalog, and audit logs.
  - *Option C:* Retain current state (Navbar displays links, but backend fails closed with 403).
- **Final Owner Decision:** PENDING

### DECISION 02: Exact NATIONAL_ADMIN Authority Over Departmental Users
- **Decision:** What is the precise lifecycle authority of National Admin over Department Administrators?
- **Current Evidence:** `ROLE_PERMISSIONS_CONFIG['national_admin']` includes `users:create` and `users:update`, but no dedicated `/users/territorial` endpoint currently exists.
- **Security Implication:** Enforces accountability for who can onboard departmental secretariats.
- **Functional Implication:** Establishes whether National Admin can assign and modify DANE departmental jurisdictions.
- **Implementation Implication:** Requires implementing dedicated territorial user management endpoints.
- **Technical Options:**
  - *Option A:* Full lifecycle governance: Invite, assign territorial DANE code, suspend, and revoke SED administrators.
  - *Option B:* National Admin can only invite; modification of territorial jurisdiction requires Superadmin approval.
- **Final Owner Decision:** PENDING

### DECISION 03: NATIONAL_ADMIN Institution Data Access Mode
- **Decision:** In what mode may National Admin inspect institutional academic data?
- **Current Evidence:** 18 backend controllers support `institution_id_override`, but national accounts have `institution_id = NULL`.
- **Security Implication:** Directly affects student data privacy under Statutory Law 1581 of 2012 and Ley 1620 of 2013.
- **Functional Implication:** Governs whether national supervisors can inspect individual classroom planillas or only aggregated statistics.
- **Implementation Implication:** Affects whether school views render read-only inspection badges for national accounts.
- **Technical Options:**
  - *Option A:* Read-only census and aggregated analytics mode. No ability to inspect individual student Observador notes or join live classrooms.
  - *Option B:* Formal Audit Mode: National Admin may inspect individual school records strictly by providing an official audit ticket ID under Ley 1581 de 2012.
- **Final Owner Decision:** PENDING

### DECISION 04: NATIONAL_ADMIN Management of Municipality Users
- **Decision:** Does National Admin directly manage Municipality Administrators (SEM), or is this delegated to Department Administrators (SED)?
- **Current Evidence:** `municipality_admin` exists in `CANONICAL_ROLES`, but no endpoint currently provisions municipal users.
- **Security Implication:** Defines the vertical delegation boundary between national, departmental, and municipal tiers.
- **Functional Implication:** Determines whether MEN or SED is the administrative authority for municipal education secretariats.
- **Implementation Implication:** Dictates the authorization scope checks on municipal invitation controllers.
- **Technical Options:**
  - *Option A (Centralized):* National Admin manages both Departmental and Municipal administrators directly.
  - *Option B (Hierarchical):* National Admin manages Departmental administrators (SED); SED manages Municipal administrators (SEM) within their department.
- **Final Owner Decision:** PENDING

### DECISION 05: Exact Level of SUPER_ADMIN Access to Academic Data
- **Decision:** Should Superadmin have read-only diagnostic visibility over grades and SIEE calculations during technical support incidents?
- **Current Evidence:** Superadmin has `*:*` in backend, but `AuthContext.tsx` short-circuits client checks.
- **Security Implication:** Evaluates access to confidential academic marks by technical infrastructure personnel.
- **Functional Implication:** Allows technicians to diagnose calculation discrepancies or database corruption.
- **Implementation Implication:** Determines whether diagnostic views require elevated audit justification.
- **Technical Options:**
  - *Option A:* Yes, strictly in read-only diagnostic mode with explicit session audit logging.
  - *Option B:* No, academic data is shielded from Superadmin UI; diagnostics occur via database sanitization scripts.
- **Final Owner Decision:** PENDING

### DECISION 06: SUPER_ADMIN Emergency Elevation Audit Requirement
- **Decision:** Should technical emergency elevation by Superadmin mandate an explicit justification string and generate an immutable high-severity audit event?
- **Current Evidence:** Superadmin wildcard `*:*` executes transparently without prompt.
- **Security Implication:** Enforces non-repudiation and traceability for root-level interventions.
- **Functional Implication:** Adds an audit prompt prior to executing sensitive administrative mutations.
- **Implementation Implication:** Requires an audit modal interceptor on emergency technical actions.
- **Technical Options:**
  - *Option A:* Yes. Any operation performed under `*:*` wildcard must record `reason`, `ticket_id`, and `client_ip`.
  - *Option B:* No, standard audit logging without mandatory justification prompts.
- **Final Owner Decision:** PENDING

---

## 18. Risks

| Risk ID | Risk Category | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :--- | :--- |
| **RSK-01** | Dependency Regression | **CRITICAL** | Stripping `users:create` before updating `institutions.py` breaks Rector onboarding | Execute Phase A endpoint alignment before Phase B seed pruning |
| **RSK-02** | Multi-Tenant Confusion | **HIGH** | Superadmin operating schools without context selector triggers 403 errors | Implement Option A context selector before altering route guards |
| **RSK-03** | Minor Data Exposure | **HIGH** | Casual inspection of student Observador records violates Statutory Law 1581 of 2012 | Enforce Option A for Decision 03 (aggregated statistics only) |
| **RSK-04** | Test Assertion Drift | **MEDIUM** | Pruning National Admin permissions may fail outdated test fixtures expecting broad CRUD | Update test assertions to match approved target model in Phase G |
| **RSK-05** | UI Presentation Drift | **LOW** | SED/SEM administrators confused by missing school management cards | Replace school cards with territorial indicator widgets on Dashboard |

---

## 19. Implementation Preconditions

Before any product code or RBAC seed changes are executed in subsequent phases, the following preconditions must be fulfilled:
1. **Explicit Owner Determination:** All 6 Owner Decisions (01 through 06) must have a recorded determination signed off by the system owner.
2. **Endpoint Dependency Alignment Precondition:** `backend/app/api/v1/endpoints/institutions.py` lines 680 and 729 must be refactored to require `users:create_rector` and verified via `test_rbac_governance_and_rector_invitation.py` prior to removing `users:create` from `national_admin`.
3. **No Unilateral Deprecations:** The operational roles (Rector, Coordinator, Teacher, Student, Guardian) must not be refactored or simplified.
4. **Clean Baseline Guarantee:** Working tree must be pristine with 0 modified product files prior to launching implementation phases.

---

## 20. Recommended Future Phases (Staged Roadmap — Design Only)

*(PROPOSED TARGET ROADMAP FOR APPROVED FUTURE IMPLEMENTATION)*

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE A: Specialized Permission Endpoint Alignment                     │
│   • Update institutions.py lines 680, 729 to require users:create_rector│
│   • Verify test_rbac_governance_and_rector_invitation.py               │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE B: RBAC Bootstrap Seed Catalog Reconciliation                    │
│   • Apply Owner Decision determinations in rbac_bootstrap_service.py   │
│   • Prune local operational mutations from national_admin              │
│   • Re-seed test database and verify role-permission matrices          │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE C: Frontend Context & Guard Hardening                            │
│   • Remove global superadmin bypass from hasRole() in AuthContext.tsx  │
│   • Assign explicit role guard to /academic in App.tsx                 │
│   • Update RequireAuth.tsx with requireInstitutionContext              │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE D: Navigation Shell & Dashboard Refactoring                      │
│   • Align RootLayout.tsx navigation links with verified scopes         │
│   • Exclude territorial roles from school management cards in Dashboard│
├────────────────────────────────────────────────────────────────────────┤
│ PHASE E: Institution Context Switcher (SuperAdmin UX)                  │
│   • Implement school selector modal in InstitutionsView.tsx            │
│   • Propagate ?institution_id=<UUID> to academic controllers           │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE F: Territorial User Assignment API Implementation                │
│   • Implement POST /users/territorial endpoints under national_admin   │
│   • Enforce DANE departmental scope containment                        │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE G: Comprehensive Regression Test Execution                       │
│   • Run all 50 backend test suites (test_*.py)                         │
│   • Run all 18 frontend test suites (*.test.ts*)                       │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE H: Human Runtime Multi-Role Validation                           │
│   • Execute live role walkthrough on local dev servers                 │
│   • Document visual evidence and audit logs in closure report          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 21. Evidence Limitations

The findings in this report are based strictly on static code analysis, existing test suite execution, and documented architecture. The following limitations apply:
1. **Static Analysis vs. Runtime Execution:** The 102-permission master matrix maps declared dependencies; endpoints that do not have dedicated automated integration tests require runtime verification before production deployment.
2. **Environment Context:** All findings reflect the **current/local runtime environment**. PEVN is not currently deployed to national production infrastructure.
3. **Territorial API Absence:** The territorial user assignment model is a target architectural design; backend endpoints for `POST /users/territorial` do not yet exist in source code.

---

## 22. Final Gate

```
========================================================================================
FINAL DESIGN GATE:
DESIGN PASS — EVIDENCE RECONCILED — OWNER DECISION REQUIRED
========================================================================================
```

- **Permission counts verified:** Exactly 102 canonical permissions verified from source.
- **National Admin count verified:** Exactly 72 permissions verified from source.
- **Role counts verified:** Exactly 11 canonical roles verified from source (13 enum values).
- **Terminology corrected:** \"Production runtime\" and \"unusable\" terminology removed; current/local runtime accurately documented.
- **Context behavior documented:** Backend capability for `institution_id_override` reconciled with frontend context selector limitation.
- **SuperAdmin authority reconciled:** Technical platform authority decoupled from educational school administration.
- **Owner decisions neutral:** Decisions 01 through 06 formulated with PENDING status and zero premature recommendations.
- **Existing vs. Target explicit:** Non-existent admin screens explicitly labeled `[TARGET — NOT CURRENTLY IMPLEMENTED]`.
- **Product code modified:** STRICTLY ZERO lines of code modified across `backend/app/**` and `frontend/src/**`.
- **Database migrations created:** STRICTLY ZERO migrations created.
- **RBAC behavior modified:** STRICTLY ZERO runtime policies altered.
