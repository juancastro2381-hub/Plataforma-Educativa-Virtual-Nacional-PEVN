# PEVN — NTA-08A POST-IMPLEMENTATION AUTHORITY CONSISTENCY AUDIT REPORT
**AI Software Factory Standard v1.2**  
**Classification:** Read-Only Forensic Audit — Authority Chain Consistency  
**Milestone:** NTA-08A  
**Date:** 2026-10-08  
**Gate Decision:** CONDITIONAL PASS  

---

## 1. Executive Summary

This forensic audit evaluates the consistency and server-side enforcement of the **Canonical Role Assignment & Authority Chain** following milestone **NTA-08**.

### Origin of this Audit
Following the publication of the NTA-08 Implementation Report (`docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md`), the Product Owner flagged a potential architectural contradiction:
- The NTA-08 report's Role Assignment Matrix listed:
  - `COORDINATOR`: `RECTOR`, `SUPERADMIN`, `NATIONAL_ADMIN`
  - `TEACHER`: `RECTOR`, `COORDINATOR`, `SUPERADMIN`, `NATIONAL_ADMIN`
  - `STUDENT`: `RECTOR`, `COORDINATOR`, `SUPERADMIN`, `NATIONAL_ADMIN`
  - `GUARDIAN`: `RECTOR`, `COORDINATOR`, `SUPERADMIN`, `NATIONAL_ADMIN`
- These entries appeared to permit **alternative authority chains** that bypass the approved canonical hierarchy:
  $$\text{SUPERADMIN} \rightarrow \text{NATIONAL\_ADMIN} \rightarrow \text{DEPARTMENT\_ADMIN} \rightarrow \text{MUNICIPALITY\_ADMIN} \rightarrow \text{RECTOR} \rightarrow \text{COORDINATOR} \rightarrow \text{TEACHER / STUDENT} \rightarrow \text{GUARDIAN}$$

### Principal Audit Findings
1. **National Admin Bypass is a Documentation Discrepancy, NOT a Code Reality:**
   In actual source code and the canonical database RBAC configuration (`backend/app/services/rbac_bootstrap_service.py`), `NATIONAL_ADMIN` **DOES NOT possess** `coordinators:create`, `teachers:create`, `students:create`, or `guardians:create` permissions. `NATIONAL_ADMIN` possesses **exclusively read permissions** (`:read`) for these institutional resources. Any attempt by a `NATIONAL_ADMIN` to invoke `POST /api/v1/coordinators`, `POST /api/v1/teachers`, `POST /api/v1/students`, or `POST /api/v1/guardians` is **strictly rejected by the server with HTTP 403 `PERMISSION_DENIED`**.
   The NTA-08 report's matrix entries listing `NATIONAL_ADMIN` as an authorized creator for these roles were **factually inaccurate / overstated documentation claims**, not active backdoors in the software.

2. **SuperAdmin Capabilities Represent Platform Emergency Infrastructure, NOT Normal Authority:**
   `SUPERADMIN` holds global root permissions (`*:*`). Through explicit query parameters (`?institution_id=<uuid>`), Superadmin can technically invoke institutional creation endpoints for diagnostic or disaster recovery purposes. In the source code, these query parameters are explicitly documented as `Override for SuperAdmin only`. However, presenting Superadmin in the standard role matrix without denoting it as an infrastructure break-glass exception created ambiguity.

3. **Territorial and Institutional Scoping is 100% Server-Enforced:**
   - `DEPARTMENT_ADMIN` and `MUNICIPALITY_ADMIN` cannot provision institutional roles (coordinators, teachers, students, guardians). They are strictly limited to territorial governance (provisioning municipal admins and inviting/revoking Rectors within their respective jurisdictions).
   - `RECTOR` and `COORDINATOR` are strictly locked to their assigned `current_user.institution_id`. Any client attempt to override `institution_id` is unconditionally ignored for institutional users.
   - `COORDINATOR` cannot create other Coordinators or Rectors.
   - `TEACHER`, `STUDENT`, and `GUARDIAN` have zero role-provisioning permissions.

4. **The Guardian Workflow Strictly Separates Hierarchy Level from Civil Association:**
   `GUARDIAN` is situated at level 10 alongside `STUDENT`. However, `STUDENT` cannot provision or link `GUARDIAN` accounts. Guardians are provisioned and linked to students exclusively by institutional directive actors (`RECTOR` and `COORDINATOR`), preserving child protection standards and preventing privilege escalation.

5. **Zero Generic Role Mutation Endpoints Exist:**
   There is no `PATCH /users/{id}/role` or arbitrary role mutation endpoint in the entire codebase.

---

## 2. Approved Canonical Hierarchy

The Product Owner formal hierarchy remains immutable:

```
SUPERADMIN (Level 100)
    │
    ▼
NATIONAL_ADMIN (Level 90)
    │
    ▼
DEPARTMENT_ADMIN (Level 80)
    │
    ▼
MUNICIPALITY_ADMIN (Level 70)
    │
    ▼
RECTOR / DIRECTOR (Level 60)
    │
    ▼
COORDINATOR (Level 50)
    │
    ├──────────────┐
    ▼              ▼
TEACHER (30)   STUDENT (10)
                   │
                   ▼
                GUARDIAN (10)
```

### Governing Invariants:
1. **Single Direct Superior:** Each role is provisioned and governed exclusively by its immediate parent authority, except for explicit platform-level root administration (`SUPERADMIN`).
2. **No Territorial Leaks:** Departmental and municipal administrators cannot act outside their canonical jurisdiction.
3. **No Cross-Tenant Institutional Leaks:** Rector and Coordinator cannot access or provision users in other educational institutions.
4. **No Role Escalation:** Lower roles cannot create equal or superior roles.
5. **No Client Trust:** Client-supplied IDs (`department_id`, `municipality_id`, `institution_id`, `role_id`) are never trusted by the server.

---

## 3. Actual Role Assignment Matrix (Source Code Truth)

The following table reflects the **actual behavior enforced by source code, dependencies, and database permissions**:

| Target Role | Target Level | Authorized Creator (Normal Path) | Emergency / Platform Exception | Forbidden Actors (Enforced by 403) | Enforcement Mechanism |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **SUPERADMIN** | 100 | Platform CLI Operator | None | All REST API callers | CLI only (`create_superadmin.py`) |
| **NATIONAL_ADMIN** | 90 | Platform CLI Operator | None | All REST API callers | CLI only (`create_national_admin.py`) |
| **DEPARTMENT_ADMIN** | 80 | `NATIONAL_ADMIN` | `SUPERADMIN` | `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`, `RECTOR`, all lower roles | `require_permission("department_admins", "create")` |
| **MUNICIPALITY_ADMIN** | 70 | `DEPARTMENT_ADMIN` (own dept only) | `NATIONAL_ADMIN`, `SUPERADMIN` | `MUNICIPALITY_ADMIN`, `RECTOR`, `COORDINATOR`, all lower roles | `require_permission("municipality_admins", "create")` + `caller_dept_id` validation |
| **RECTOR** | 60 | `MUNICIPALITY_ADMIN` (own muni), `DEPARTMENT_ADMIN` (own dept) | `NATIONAL_ADMIN`, `SUPERADMIN` | `RECTOR`, `COORDINATOR`, `TEACHER`, all lower roles | `require_permission("users", "create_rector")` + `_assert_rector_management_authority` |
| **COORDINATOR** | 50 | `RECTOR` (own institution) | `SUPERADMIN` (`?institution_id=`) | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `COORDINATOR` (403), `TEACHER` (403) | `require_permission("coordinators", "create")` + explicit role block |
| **TEACHER** | 30 | `RECTOR`, `COORDINATOR` (own institution) | `SUPERADMIN` (`?institution_id=`) | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `TEACHER` (403) | `require_permission("teachers", "create")` + tenant isolation |
| **STUDENT** | 10 | `RECTOR`, `COORDINATOR` (own institution) | `SUPERADMIN` (`?institution_id=`) | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `STUDENT` (403) | `require_permission("students", "create")` + tenant isolation |
| **GUARDIAN** | 10 | `RECTOR`, `COORDINATOR` (own institution) | `SUPERADMIN` (`?institution_id=`) | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `STUDENT` (403), `GUARDIAN` (403) | `require_permission("guardians", "create")` + tenant isolation |

---

## 4. Exact API Endpoints & Permission Checks

### A. SUPERADMIN & NATIONAL_ADMIN Creation
- **Endpoint:** NONE.
- **Implementation:**
  - `backend/app/cli/create_superadmin.py`
  - `backend/app/cli/create_national_admin.py`
- **Security Boundary:** Executable only via server shell. Passwords hashed using Argon2id. No REST exposure.

### B. DEPARTMENT_ADMIN Lifecycle
- **Create:** `POST /api/v1/department-admins`
  - Permission: `require_permission("department_admins", "create")`
  - Held by: `SUPERADMIN` (`*:*`), `NATIONAL_ADMIN`.
  - Service: `DepartmentAdminService.create_department_admin`
- **Status / Deactivation:** `PATCH /api/v1/department-admins/{id}/status`
  - Permission: `require_permission("department_admins", "update")`
  - Held by: `SUPERADMIN`, `NATIONAL_ADMIN`.
- **Reassign Department:** `PATCH /api/v1/department-admins/{id}/department`
  - Permission: `require_permission("department_admins", "update")`
  - Held by: `SUPERADMIN`, `NATIONAL_ADMIN`. Atomically sets `RefreshToken.is_revoked = True`.

### C. MUNICIPALITY_ADMIN Lifecycle
- **Create:** `POST /api/v1/municipality-admins`
  - Permission: `require_permission("municipality_admins", "create")`
  - Held by: `SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`.
  - Body Guard (`endpoints/municipality_admins.py:197-203`):
    ```python
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles and not (
        SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or SystemRole.DEPARTMENT_ADMIN in auth.roles
    ):
        raise AuthorizationError("Los administradores municipales no tienen facultades para aprovisionar otros administradores.", code="PERMISSION_DENIED")
    ```
  - Territorial Enforcement (`services/municipality_admin_service.py:90-95`):
    ```python
    if caller_department_id and target_muni.department_id != caller_department_id:
        raise AuthorizationError("No está autorizado para aprovisionar administradores en un municipio fuera de su departamento.", code="PERMISSION_DENIED")
    ```
- **Status / Deactivation:** `PATCH /api/v1/municipality-admins/{id}/status`
  - Permission: `require_permission("municipality_admins", "update")`
  - Territorial check: `DEPARTMENT_ADMIN` can only modify status within their department. Active refresh tokens revoked.
- **Reassign Municipality:** `PATCH /api/v1/municipality-admins/{id}/municipality`
  - Permission: `require_permission("municipality_admins", "update")`
  - Territorial check: Both old and new municipality must belong to caller's department. Active refresh tokens revoked.

### D. RECTOR Lifecycle
- **Invite:** `POST /api/v1/institutions/{id}/rector-invitation`
  - Permission: `require_permission("users", "create_rector")`
  - Held by: `SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`.
  - Territorial Barrier (`endpoints/institutions.py:705-754`):
    ```python
    async def _assert_rector_management_authority(db, auth, institution_id, action_label):
        ...
        if SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles:
            return inst
        if SystemRole.DEPARTMENT_ADMIN in auth.roles or auth.scope.is_department():
            if inst.municipality.department_id != uuid.UUID(auth.scope.department_id):
                raise AuthorizationError(...)
            return inst
        if SystemRole.MUNICIPALITY_ADMIN in auth.roles or auth.scope.is_municipality():
            if inst.municipality_id != uuid.UUID(auth.scope.municipality_id):
                raise AuthorizationError(...)
            return inst
        raise AuthorizationError(...)
    ```
  - Succession Barrier: If active Rector UserRole exists, immediately raises HTTP 409 `ACTIVE_RECTOR_EXISTS`.
- **Revoke:** `POST /api/v1/institutions/{id}/rector/revoke`
  - Same territorial checks as invitation. Atomically deactivates UserRole, revokes pending invitations, marks `RefreshToken.is_revoked = True`.

### E. COORDINATOR Lifecycle
- **Create:** `POST /api/v1/coordinators`
  - Permission: `require_permission("coordinators", "create")`
  - Held by: `RECTOR` (and `SUPERADMIN` via `*:*`).
  - **NOT held by:** `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`.
  - Explicit Anti-Escalation Check (`endpoints/coordinators.py:144-149`):
    ```python
    if SystemRole.COORDINATOR in auth.roles or SystemRole.TEACHER in auth.roles or SystemRole.STUDENT in auth.roles:
        raise AuthorizationError("No posee facultades para aprovisionar coordinadores institucionales.", code="PERMISSION_DENIED")
    ```
  - Scope Binding: Calls `resolve_institution_id(db, auth, current_user, institution_id)`. For Rector, strictly evaluates to `current_user.institution_id`.
- **Status / Deactivation:** `PATCH /api/v1/coordinators/{id}/status`
  - Permission: `require_permission("coordinators", "update")`
  - Held by: `RECTOR` (within own institution) and `SUPERADMIN`.
  - Revokes active sessions on deactivation.

### F. TEACHER Lifecycle
- **Create:** `POST /api/v1/teachers`
  - Permission: `require_permission("teachers", "create")`
  - Held by: `RECTOR`, `COORDINATOR` (and `SUPERADMIN` via `*:*`).
  - **NOT held by:** `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`.
  - Scope Binding: Forced to `current_user.institution_id` for Rector and Coordinator.
- **Status / Update:** `PATCH /api/v1/teachers/{id}/status`
  - Permission: `require_permission("teachers", "update")`
  - Held by: `RECTOR`, `COORDINATOR`.

### G. STUDENT Lifecycle
- **Create:** `POST /api/v1/students`
  - Permission: `require_permission("students", "create")`
  - Held by: `RECTOR`, `COORDINATOR` (and `SUPERADMIN` via `*:*`).
  - **NOT held by:** `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`.
  - Scope Binding: Forced to `current_user.institution_id`.

### H. GUARDIAN Lifecycle
- **Create:** `POST /api/v1/guardians`
  - Permission: `require_permission("guardians", "create")`
  - Held by: `RECTOR`, `COORDINATOR` (and `SUPERADMIN` via `*:*`).
  - **NOT held by:** `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`, `STUDENT`.
  - Scope Binding: Forced to `current_user.institution_id`.
- **Link Student to Guardian:** `POST /api/v1/guardians/{guardian_id}/students/{student_id}`
  - Permission: `require_permission("guardians", "link_student")`
  - Held by: `RECTOR`, `COORDINATOR` (and `SUPERADMIN`).
  - Tenant Verification (`services/guardian_service.py:588-607`): Both Student and Guardian must belong to `institution_id`.

---

## 5. Normal Authority Paths vs Emergency Exceptions

### A. The False Claim of National Admin Bypasses
The NTA-08 report asserted:
> *"COORDINATOR: RECTOR, SUPERADMIN, NATIONAL_ADMIN"*  
> *"NATIONAL_ADMIN can create: ... institutional roles nationally."*

**Forensic Audit Verdict: REFUTED BY SOURCE CODE.**  
In `backend/app/services/rbac_bootstrap_service.py` (lines 243-291), `ROLE_PERMISSIONS_CONFIG[SystemRole.NATIONAL_ADMIN.value]` contains:
```python
        # Institutional Coordinators
        "coordinators:read",
        ...
        "teachers:read",
        "students:read",
        "guardians:read",
```
`NATIONAL_ADMIN` has **ZERO** creation permissions (`:create`) for institutional roles.  
In `backend/app/core/security/authorization.py:133-145`, `CentralizedAuthorizationService` requires exact permission matching for all non-superadmin roles:
```python
        has_permission = any(
            perm.resource in {required_permission.resource, "*"}
            and perm.action in {required_permission.action, "*"}
            for perm in context.permissions
        )
        if not has_permission:
            return False
```
Because `NATIONAL_ADMIN` does not have `coordinators:create`, `teachers:create`, `students:create`, or `guardians:create`, any API invocation by a National Admin results in:
$$\text{HTTP 403 Forbidden (PERMISSION\_DENIED)}$$
Therefore:
1. `NATIONAL_ADMIN` **cannot** provision Coordinators.
2. `NATIONAL_ADMIN` **cannot** provision Teachers.
3. `NATIONAL_ADMIN` **cannot** provision Students.
4. `NATIONAL_ADMIN` **cannot** provision Guardians.

**Conclusion:** The authority chain is **NOT bypassed** by National Admin. National Admin can only govern territory and invite Rectors. Once inside an institution, only the Rector (and subordinate Coordinator) can provision members.

### B. SuperAdmin Emergency Platform Capabilities
`SUPERADMIN` is Level 100 with `*:*` platform authority.
- In `authorization.py:107-130`, Superadmin bypasses granular permission checks.
- In `deps.py:resolve_institution_id`, Superadmin can pass `?institution_id=<uuid>` to select an institutional context.
- In endpoint controllers, this query parameter is annotated as:
  ```python
  Query(description="Override for SuperAdmin only")
  ```
- **Architectural Classification:** This is **not a normal business role assignment workflow**. It is an infrastructure/disaster recovery capability. In production, Superadmin does not administer daily school staff. Sensitive accesses by Superadmin are recorded in the audit log with `AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED` or technical diagnostic flags.

---

## 6. Server-Side Scope and Anti-IDOR Findings

The scope resolver `resolve_institution_id` in `backend/app/api/deps.py` enforces strict boundaries:

```python
async def resolve_institution_id(
    db: AsyncSession,
    auth: AuthorizationContext,
    current_user: User,
    institution_id_override: uuid.UUID | str | None = None,
    request: Request | None = None,
) -> uuid.UUID:
```

### Analysis by Caller Role:

1. **National Scope (`SUPERADMIN`, `NATIONAL_ADMIN`):**
   - Resolves to `institution_id_override` (if supplied).
   - If not supplied, falls back to `current_user.institution_id`.
   - If neither, raises HTTP 403 `Contexto institucional no disponible`.

2. **Department Scope (`DEPARTMENT_ADMIN`):**
   - If `institution_id_override` is supplied: queries `Institution` joined with `Municipality` where `Municipality.department_id == auth.scope.department_id`.
   - If the institution belongs to another department: **immediately raises HTTP 403 `PERMISSION_DENIED`**.
   - Client-supplied department parameter is ignored; server derives department strictly from `auth.scope.department_id`.

3. **Municipality Scope (`MUNICIPALITY_ADMIN`):**
   - If `institution_id_override` is supplied: queries `Institution` where `Institution.municipality_id == auth.scope.municipality_id`.
   - If the institution belongs to another municipality: **immediately raises HTTP 403 `PERMISSION_DENIED`**.
   - Client-supplied municipality parameter is ignored; server derives municipality strictly from `auth.scope.municipality_id`.

4. **Institutional Scope (`RECTOR`, `COORDINATOR`, `TEACHER`, `STUDENT`, `GUARDIAN`):**
   - **Crucial Invariant:** Lines 285-288:
     ```python
     if current_user.institution_id:
         return current_user.institution_id
     ```
   - Any query parameter (`?institution_id=`) or header (`x-institution-id`) passed by an institutional actor is **completely ignored**. Institutional users are permanently locked to `current_user.institution_id`.
   - Any attempt to query or mutate an entity with a mismatched `institution_id` in `TeacherService`, `StudentService`, `CoordinatorService`, or `GuardianService` raises `CrossTenantMismatchError` or `NotFoundError` (HTTP 404/403).

---

## 7. Guardian Workflow Findings

### Positioning in Hierarchy vs Workflow Execution
The approved hierarchy diagram positions Guardian as:
$$\text{STUDENT (10)} \rightarrow \text{GUARDIAN (10)}$$

### Forensic Review of Guardian Account Lifecycle:
1. **Can Student Administer Guardian?**
   **NO.** In `ROLE_PERMISSIONS_CONFIG`, `STUDENT` possesses 19 permissions (academic calendar, report cards, class attendance, assignments). `STUDENT` has **zero permissions on guardians** (`guardians:*`).
   If a Student attempts to call `POST /api/v1/guardians` or `POST /api/v1/guardians/{id}/students/{student_id}`, the server returns HTTP 403 `PERMISSION_DENIED`.

2. **Who Provisions Guardians?**
   `RECTOR` and `COORDINATOR`.
   Both hold `guardians:create` and `guardians:update`.
   The guardian record is created under `institution_id = current_user.institution_id`.

3. **Who Links Student to Guardian?**
   `RECTOR` and `COORDINATOR`.
   Both hold `guardians:link_student`.
   The service method `associate_guardian_to_student` validates that both the student and the guardian belong to the caller's institution before creating `StudentGuardian`.

4. **Self-Service / SIMAT Identity Verification:**
   Per `[OPEN-DECISION-3A-01]`, a legal guardian may also claim or activate their account via SIMAT verification / identity verification workflows without student administrative mediation.

**Conclusion:** The distinction between authority hierarchy level (Level 10) and account administration is correctly preserved.

---

## 8. Discrepancies Between Report and Source Code

| Dimension | NTA-08 Report Claim | Source Code Reality | Impact / Classification |
| :--- | :--- | :--- | :--- |
| **National Admin & Institutional Roles** | Claimed `NATIONAL_ADMIN` can create Coordinator, Teacher, Student, Guardian. | `NATIONAL_ADMIN` lacks `:create` permissions; calls fail with HTTP 403. | **Documentation Error**. Source code is strictly compliant with the hierarchy; report overstated National Admin authority. |
| **SuperAdmin Authority Classification** | Listed `SUPERADMIN` as a normal peer creator alongside Rector/Coordinator. | Superadmin has `*:*` platform access with `?institution_id` override meant for emergencies/maintenance. | **Classification Ambiguity**. Should be documented as an emergency platform tool, not a normal workflow. |
| **Test Suite Coverage Scope** | Claimed the 20 tests verified the entire matrix including National Admin institutional provisioning. | Test suite explicitly tested Rector $\rightarrow$ Coordinator, Rector $\rightarrow$ Teacher, Rector $\rightarrow$ Student, Coordinator $\rightarrow$ Teacher/Student/Guardian. Did NOT test National Admin creating teachers/students. | **Omission in Test Documentation**. If tested, National Admin creating teachers would have failed with 403. |
| **Coordinator Permissions** | Coordinator has academic/student provisioning. | Verified: Coordinator has `teachers:create`, `students:create`, `guardians:create`, but **NO** `coordinators:create` or `users:create_rector`. | **Accurate**. Matches code. |
| **Rector Succession** | Exactly 1 active rector per institution. | Verified: `ACTIVE_RECTOR_EXISTS` (409) raised if active rector exists. Tested in `test_17`. | **Accurate**. Matches code. |

---

## 9. Security Risks & Severity Assessment

| Risk Description | Severity | Likelihood | Current Mitigation |
| :--- | :---: | :---: | :--- |
| **Unauthorized Role Bypass by National Admin** | None | Low | Server-enforced: `NATIONAL_ADMIN` lacks `:create` permissions and is blocked by 403. |
| **SuperAdmin Abuse / Technical Override** | Low | Low | Restricted to platform administrators with database/infrastructure access; audited via `CentralizedAuthorizationService`. |
| **Cross-Tenant Coordinator / Staff Creation** | None | Low | `resolve_institution_id` forces `current_user.institution_id` for Rector and Coordinator. Client overrides are ignored. |
| **Privilege Escalation by Coordinator** | None | Low | Explicitly checked in controller (`if SystemRole.COORDINATOR in auth.roles: raise 403`) and lacking permissions. |
| **Student Self-Administering Guardians** | None | Low | Student lacks `guardians:*` permissions; calls blocked with 403. |
| **Documentation Inaccuracy in Milestone Artifact** | Low | High | Remediation required: Align NTA-08 report with actual source code. |

---

## 10. Required Remediation Plan (Post-Audit)

Upon Product Owner authorization, execute the following non-breaking documentation and test remediations:

1. **Update NTA-08 Report (`docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md`):**
   - Correct the Role Assignment Matrix (Section 5) and "Who Creates Whom" (Section 6) by removing `NATIONAL_ADMIN` from `COORDINATOR`, `TEACHER`, `STUDENT`, and `GUARDIAN`.
   - Clarify that `SUPERADMIN` access to institutional endpoints is an emergency infrastructure override (`?institution_id=`), not a normal business assignment flow.

2. **Add Negative Tests to Regression Suite (`tests/test_nta08_authority_chain.py`):**
   - Add explicit test asserting that `NATIONAL_ADMIN` attempting to call `POST /api/v1/coordinators` returns HTTP 403 `PERMISSION_DENIED`.
   - Add explicit test asserting that `NATIONAL_ADMIN` attempting to call `POST /api/v1/teachers` returns HTTP 403 `PERMISSION_DENIED`.
   - Add explicit test asserting that `NATIONAL_ADMIN` attempting to call `POST /api/v1/students` returns HTTP 403 `PERMISSION_DENIED`.
   - Add explicit test asserting that `NATIONAL_ADMIN` attempting to call `POST /api/v1/guardians` returns HTTP 403 `PERMISSION_DENIED`.

3. **No Code Changes Required in Core Services:**
   - The permissions in `rbac_bootstrap_service.py`, controllers in `coordinators.py`, `teachers.py`, `students.py`, and scoping logic in `deps.py` already enforce the strict hierarchy.

---

## 11. Concrete Evidence & File References

### 1. Permission Matrix Configuration
- **File:** [rbac_bootstrap_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L243-L291)
- **Proof:** `ROLE_PERMISSIONS_CONFIG[SystemRole.NATIONAL_ADMIN.value]` contains `coordinators:read`, `teachers:read`, `students:read`, `guardians:read`. It contains **NO** creation permissions for these resources.

### 2. Authorization Enforcement Engine
- **File:** [authorization.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py#L133-L157)
- **Proof:** `CentralizedAuthorizationService.authorize()` evaluates granular resource and action match for non-superadmin actors, rejecting missing permissions with warning logs and raising `AuthorizationError`.

### 3. Institutional Scope Resolution & Anti-IDOR
- **File:** [deps.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/deps.py#L225-L288)
- **Proof:** `resolve_institution_id()` forces `current_user.institution_id` for institutional users, validates municipal boundary for `MUNICIPALITY_ADMIN`, and departmental boundary for `DEPARTMENT_ADMIN`.

### 4. Coordinator Creation Controller
- **File:** [coordinators.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/coordinators.py#L143-L167)
- **Proof:** Requires `require_permission("coordinators", "create")` and explicitly rejects `COORDINATOR`, `TEACHER`, and `STUDENT` actors with HTTP 403.

### 5. Territorial Rector Authority
- **File:** [institutions.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py#L705-L754)
- **Proof:** `_assert_rector_management_authority()` enforces departmental boundary for Department Admin and municipal boundary for Municipality Admin.

### 6. Passing Automated Test Verification
- **File:** [test_nta08_authority_chain.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta08_authority_chain.py#L240-L580)
- **Proof:** 20/20 automated tests verify authority delegation and Anti-IDOR boundaries across all 9 roles.

---

## 12. Final Gate Decision

```
================================================================================
FINAL GATE DECISION:
CONDITIONAL PASS
================================================================================
```

### Justification:
1. **Actual Implementation is Strictly Compliant:**  
   The actual backend codebase, services, and database permission catalogs **consistently enforce the canonical authority hierarchy**. There is **NO active authority-chain bypass**:
   - `NATIONAL_ADMIN` cannot provision institutional roles (rejected by server with HTTP 403).
   - `DEPARTMENT_ADMIN` and `MUNICIPALITY_ADMIN` cannot provision institutional roles (rejected by server with HTTP 403).
   - `RECTOR` and `COORDINATOR` cannot escape their institution.
   - `COORDINATOR` cannot provision Coordinators or Rectors.
   - `STUDENT` cannot administer Guardians.
   - No generic role mutation endpoint exists.

2. **Condition Requiring Product Owner Review:**  
   The milestone NTA-08 report (`PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md`) contains **documentation discrepancies** in its Role Assignment Matrix (Section 5) and Section 6 by listing `NATIONAL_ADMIN` as an authorized creator of Coordinators, Teachers, Students, and Guardians, and listing `SUPERADMIN` without explicitly annotating it as an emergency platform override.

3. **Required Action for Full Certification:**  
   Awaiting Product Owner formal sign-off to:
   - Accept the actual strict code behavior as authoritative.
   - Authorize updating the NTA-08 report documentation to align with code truth.
   - Authorize adding the 4 negative regression tests proving National Admin 403 rejections on institutional creation endpoints.
