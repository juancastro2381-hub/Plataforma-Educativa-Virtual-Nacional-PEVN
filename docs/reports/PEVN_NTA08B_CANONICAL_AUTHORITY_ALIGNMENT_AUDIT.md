# PEVN — NTA-08B: CANONICAL AUTHORITY ALIGNMENT & CERTIFICATION REMEDIATION REPORT
**AI Software Factory Standard v1.2**  
**Task Classification:** Read-Only Forensic Alignment & Remediation Planning  
**Milestone:** NTA-08B  
**Date:** 2026-10-08  
**Current Gate:** CONDITIONAL PASS  
**Target Gate:** CONDITIONAL PASS (Awaiting PO Authorization for Remediation Execution)  

---

## 1. Executive Summary

This forensic audit evaluates the alignment between the **Product Owner's Approved Canonical Authority Chain** and the current implementation across the Plataforma Educativa Virtual Nacional (PEVN).

### Origin and Context
Following the implementation of milestone **NTA-08** and the subsequent forensic audit **NTA-08A**, the Product Owner established an authoritative decision regarding the canonical user assignment and invitation hierarchy:
$$\text{SUPERADMIN} \rightarrow \text{NATIONAL\_ADMIN} \rightarrow \text{DEPARTMENT\_ADMIN} \rightarrow \text{MUNICIPALITY\_ADMIN} \rightarrow \text{RECTOR} \rightarrow \text{COORDINATOR} \rightarrow \text{TEACHER / STUDENT} \rightarrow \text{GUARDIAN}$$

The Product Owner explicitly decreed the **normal assignment and invitation flow**:
1. `SUPERADMIN` provisions `NATIONAL_ADMIN`.
2. `NATIONAL_ADMIN` invites/provisions `DEPARTMENT_ADMIN`.
3. `DEPARTMENT_ADMIN` invites/provisions `MUNICIPALITY_ADMIN` within the assigned department.
4. `MUNICIPALITY_ADMIN` invites/provisions `RECTOR` within the assigned municipality.
5. `RECTOR` invites/provisions `COORDINATOR`, `TEACHER`, `STUDENT`, and `GUARDIAN` within the Rector's own institution.
6. `COORDINATOR` may manage academic activities and perform authorized operational tasks, but **must not become an alternative authority for assigning institutional roles** unless explicitly approved by the Product Owner.
7. `GUARDIAN` self-service identity verification (SIMAT / decoupled national identity) remains available as an identity verification workflow, but `STUDENT` must never administer, provision, or link `GUARDIAN` accounts.
8. `SUPERADMIN` global access represents platform infrastructure and disaster recovery exceptions, not a normal business invitation path.

### Core Audit Discoveries
1. **Critical Discrepancy — Coordinator Institutional Role Provisioning:**
   In the active codebase (`backend/app/services/rbac_bootstrap_service.py:551-560`), `COORDINATOR` currently holds `teachers:create`, `teachers:update`, `students:create`, `students:update`, `guardians:create`, `guardians:update`, and `guardians:link_student`. In `backend/tests/test_nta08_authority_chain.py`, tests 9, 10, and 11 explicitly assert that Coordinator can provision Teachers, Students, and Guardians.  
   **This directly conflicts with PO Flow #5 and #6**, which designate `RECTOR` as the exclusive normal assigning authority and forbid `COORDINATOR` from acting as an alternative role provisioning authority.

2. **Resolution of National Admin Discrepancy:**
   As verified in NTA-08A, `NATIONAL_ADMIN` in the actual codebase **cannot** provision Coordinators, Teachers, Students, or Guardians because it lacks creation permissions (`:create`) and receives HTTP 403 `PERMISSION_DENIED`. The NTA-08 report's table listing National Admin for these roles was a documentation inaccuracy. However, explicit negative regression tests in `tests/test_nta08_authority_chain.py` are currently missing.

3. **Multi-Tier Rector Authority vs Single-Parent Flow:**
   In the active codebase (`backend/app/api/v1/endpoints/institutions.py:705-754`), Rector invitation and revocation can be invoked by `SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN` (for institutions in own department), and `MUNICIPALITY_ADMIN` (for institutions in own municipality).  
   Under PO Flow #4, Municipality Admin is the designated normal authority for Rector provisioning. Higher-tier access (`DEPARTMENT_ADMIN`, `NATIONAL_ADMIN`, `SUPERADMIN`) acts as supervisory or emergency escalation, which requires formal PO policy classification.

4. **Security & Boundary Invariants:**
   All territorial and institutional boundaries are 100% server-enforced:
   - No generic role mutation (`PATCH /users/{id}/role`) exists.
   - Institutional users (`rector`, `coordinator`, `teacher`, `student`, `guardian`) are locked to `current_user.institution_id`. Client parameter overrides are unconditionally ignored.
   - `STUDENT` has zero permissions on `guardians:*` and cannot create or link guardians.
   - Rector revocation atomically deactivates UserRole, revokes pending invitations, and invalidates active refresh tokens.

---

## 2. Approved Canonical Authority Hierarchy

```
SUPERADMIN (Level 100)
    │  [Platform Infrastructure & Break-Glass Exception]
    ▼
NATIONAL_ADMIN (Level 90)
    │  [Provisions Department Admins; National Governance]
    ▼
DEPARTMENT_ADMIN (Level 80)
    │  [Provisions Municipality Admins within Assigned Department]
    ▼
MUNICIPALITY_ADMIN (Level 70)
    │  [Invites/Provisions Rectors within Assigned Municipality]
    ▼
RECTOR / DIRECTOR (Level 60)
    │  [Sole Normal Assigning Authority for Institutional Roles]
    ├──────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼
COORDINATOR    TEACHER        STUDENT        GUARDIAN
 (Level 50)     (Level 30)     (Level 10)     (Level 10)
    │
    ▼ (Academic Ops & Telemetry ONLY; No Role Provisioning)
```

### Governing Invariants:
1. **Single Direct Superior (Normal Flow):** Normal role assignment must descend strictly through the immediate parent tier.
2. **Exclusivity of Rector Authority:** The Rector is the sole normal assigning authority for institutional staff and students.
3. **No Alternative Institutional Authority:** Coordinator must not provision Teachers, Students, or Guardians.
4. **Territorial Isolation:** Administrative authority cannot cross departmental or municipal boundaries.
5. **Multi-Tenant Isolation:** Institutional authority cannot cross educational institution boundaries.
6. **No Client Trust:** Client-supplied identifiers are never trusted to establish authority.

---

## 3. Mandatory Authority Matrix (Source Code Truth)

The following matrix documents the actual authorization checks, endpoints, services, permissions, and compliance status for every role in the PEVN architecture:

| Target Role | Target Level | Approved Normal Authority (PO Decision) | Actual Authorized Callers in Code | Relevant Endpoint & Service | Required Permission | Scope Barrier | Activation & Token Mechanism | Unauthorized Callers & Expected HTTP Status | Compliance Status | Exact Code References |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **SUPERADMIN** | 100 | Server Shell Operator | CLI Script Only | CLI: `app/cli/create_superadmin.py` | Platform root | Global | Direct Argon2id hash | All REST callers (404 - No endpoint exists) | **PASS** | [`create_superadmin.py:49-160`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/create_superadmin.py#L49-L160) |
| **NATIONAL_ADMIN** | 90 | Server Shell Operator | CLI Script Only | CLI: `app/cli/create_national_admin.py` | Platform root | National | Direct Argon2id hash | All REST callers (404 - No endpoint exists) | **PASS** | [`create_national_admin.py:47-155`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/create_national_admin.py#L47-L155) |
| **DEPARTMENT_ADMIN** | 80 | `NATIONAL_ADMIN` | `NATIONAL_ADMIN`, `SUPERADMIN` | `POST /api/v1/department-admins` <br> `DepartmentAdminService` | `department_admins:create` | National $\rightarrow$ Department | Inactive until token accepted or direct creation with password | `DEPARTMENT_ADMIN` (403), `MUNI_ADMIN` (403), `RECTOR` (403), lower roles (403) | **PASS** | [`department_admins.py:158-189`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/department_admins.py#L158-L189) <br> [`rbac_bootstrap_service.py:254`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L254) |
| **MUNICIPALITY_ADMIN** | 70 | `DEPARTMENT_ADMIN` (own dept) | `DEPARTMENT_ADMIN` (own dept), `NATIONAL_ADMIN`, `SUPERADMIN` | `POST /api/v1/municipality-admins` <br> `MunicipalityAdminService` | `municipality_admins:create` | Target municipality must belong to caller's `department_id` | Direct password hash or unverified account | `MUNI_ADMIN` (403), Foreign `DEPT_ADMIN` (403), `RECTOR` (403), lower roles (403) | **PASS** | [`municipality_admins.py:180-221`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/municipality_admins.py#L180-L221) <br> [`municipality_admin_service.py:238-243`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/municipality_admin_service.py#L238-L243) |
| **RECTOR** | 60 | `MUNICIPALITY_ADMIN` (own muni) | `MUNICIPALITY_ADMIN` (own muni), `DEPARTMENT_ADMIN` (own dept), `NATIONAL_ADMIN`, `SUPERADMIN` | `POST /api/v1/institutions/{id}/rector-invitation` <br> `RectorOnboardingService` | `users:create_rector` | Institution must belong to caller's territorial scope | Single-use 48-byte URL-safe cryptographic token (SHA-256 hash match) | Foreign `MUNI_ADMIN` (403), Foreign `DEPT_ADMIN` (403), `RECTOR` (403), `COORDINATOR` (403), lower roles (403) | **CONDITIONAL PASS** (Multi-tier supervisory escalation requires PO classification) | [`institutions.py:705-807`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py#L705-L807) <br> [`rector_onboarding_service.py:107-161`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py#L107-L161) |
| **COORDINATOR** | 50 | `RECTOR` (own institution) | `RECTOR` (own institution), `SUPERADMIN` (`?institution_id=`) | `POST /api/v1/coordinators` <br> `CoordinatorService` | `coordinators:create` | Locked to `current_user.institution_id` | Direct password hash or single-use raw token generation | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `COORDINATOR` (403), `TEACHER` (403) | **PASS** | [`coordinators.py:124-167`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/coordinators.py#L124-L167) <br> [`coordinator_service.py:76-175`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/coordinator_service.py#L76-L175) |
| **TEACHER** | 30 | `RECTOR` (own institution) | `RECTOR` (own inst), `COORDINATOR` (own inst), `SUPERADMIN` (`?institution_id=`) | `POST /api/v1/teachers` <br> `TeacherService` | `teachers:create` | Locked to `current_user.institution_id` | Direct provision or password reset token | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `TEACHER` (403), `STUDENT` (403) | **FAIL** (`COORDINATOR` has `teachers:create` violating PO Flow #5 & #6) | [`teachers.py:61-134`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teachers.py#L61-L134) <br> [`rbac_bootstrap_service.py:552`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L552) |
| **STUDENT** | 10 | `RECTOR` (own institution) | `RECTOR` (own inst), `COORDINATOR` (own inst), `SUPERADMIN` (`?institution_id=`) | `POST /api/v1/students` <br> `StudentService` | `students:create` | Locked to `current_user.institution_id` | User creation with SIMAT binding | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `STUDENT` (403) | **FAIL** (`COORDINATOR` has `students:create` violating PO Flow #5 & #6) | [`students.py:57-98`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/students.py#L57-L98) <br> [`rbac_bootstrap_service.py:555`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L555) |
| **GUARDIAN** | 10 | `RECTOR` (own institution) | `RECTOR` (own inst), `COORDINATOR` (own inst), `SUPERADMIN` (`?institution_id=`) | `POST /api/v1/guardians` <br> `GuardianService` | `guardians:create`, `guardians:link_student` | Locked to `current_user.institution_id` | Decoupled identity, optional password reset | `NATIONAL_ADMIN` (403), `DEPT_ADMIN` (403), `MUNI_ADMIN` (403), `STUDENT` (403), `GUARDIAN` (403) | **FAIL** (`COORDINATOR` has `guardians:create` & `link_student` violating PO Flow #5 & #6) | [`guardians.py:57-99`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/guardians.py#L57-L99) <br> [`rbac_bootstrap_service.py:558-560`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L558-L560) |

---

## 4. Discrepancy-by-Discrepancy Analysis

### Discrepancy 1: COORDINATOR Holds Role Creation & Linking Permissions (MATERIAL CONFLICT)
- **Approved Behavior (PO Decision):**  
  Flow 5 dictates: *"RECTOR invites/provisions COORDINATOR, TEACHER, STUDENT, and GUARDIAN within the Rector's own institution."*  
  Flow 6 dictates: *"COORDINATOR may manage academic activities and perform the specific operational tasks explicitly authorized for that role, but must not become an alternative authority for assigning institutional roles unless the Product Owner explicitly approves such an exception."*
- **Current Source Code Reality:**  
  In [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L551-L560) (and lines 636-646 for `academic_coordinator`):
  `"coordinator"` possesses:
  - `"teachers:create"`, `"teachers:update"`
  - `"students:create"`, `"students:update"`
  - `"guardians:create"`, `"guardians:update"`, `"guardians:link_student"`
- **Test Suite Reality:**  
  In [`backend/tests/test_nta08_authority_chain.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta08_authority_chain.py#L474-L580):
  - `test_09_coordinator_provisions_teacher` (asserts coordinator CAN create teacher)
  - `test_10_coordinator_provisions_student` (asserts coordinator CAN create student)
  - `test_11_guardian_workflow` (asserts coordinator CAN create guardian and link to student)
- **Classification:** **Permission-Catalog Defect / Authority Chain Violation.**
- **Remediation Required:** Remove creation/linking permissions (`teachers:create`, `students:create`, `guardians:create`, `guardians:link_student`) from `coordinator` and `academic_coordinator`. Convert tests 9, 10, 11 into negative tests asserting HTTP 403 `PERMISSION_DENIED`.

---

### Discrepancy 2: Multi-Tier Rector Provisioning vs Single-Parent Municipal Authority
- **Approved Behavior (PO Decision):**  
  Flow 4 dictates: *"MUNICIPALITY_ADMIN invites/provisions RECTOR within the assigned municipality."*
- **Current Source Code Reality:**  
  In [`backend/app/api/v1/endpoints/institutions.py:705-754`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py#L705-L754):
  `_assert_rector_management_authority` authorizes:
  1. `SUPERADMIN` (global platform emergency)
  2. `NATIONAL_ADMIN` (national governance)
  3. `DEPARTMENT_ADMIN` (institutions within administrator's department)
  4. `MUNICIPALITY_ADMIN` (institutions within administrator's municipality)
  In [`rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L250):
  `"users:create_rector"` is granted to `national_admin`, `department_admin`, and `municipality_admin`.
- **Classification:** **Product Owner Decision Required.**  
  If the PO requires strict sequential descent (`DEPARTMENT_ADMIN` only creates `MUNICIPALITY_ADMIN`, and only `MUNICIPALITY_ADMIN` can invite `RECTOR`), then Department Admin and National Admin must be stripped of `users:create_rector`. If Department Admin retains supervisory escalation (e.g. for uncertified municipalities), this must be formally ratified as an authorized exception.

---

### Discrepancy 3: NTA-08 Implementation Report Overstated National Admin Capabilities
- **Approved Behavior (PO Decision):**  
  `NATIONAL_ADMIN` governs national territory and provisions Department Admins, but cannot ordinarily provision institutional roles.
- **Current Source Code Reality:**  
  In the code, `NATIONAL_ADMIN` already lacks `coordinators:create`, `teachers:create`, `students:create`, `guardians:create` and is rejected with HTTP 403.
- **Report Inaccuracy:**  
  In `docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md` (Sections 5 & 6), `NATIONAL_ADMIN` was erroneously documented as an authorized creator for all institutional roles.
- **Classification:** **Documentation-Only Correction.**

---

### Discrepancy 4: Missing Automated Negative Regression Tests for Higher-Tier Bypasses
- **Approved Behavior (PO Decision):**  
  Higher-tier roles cannot bypass lower tiers to provision institutional roles.
- **Current Test Suite Reality:**  
  `backend/tests/test_nta08_authority_chain.py` contains 20 tests, but **lacks explicit negative tests asserting HTTP 403** when:
  1. `NATIONAL_ADMIN` calls `POST /api/v1/coordinators`
  2. `NATIONAL_ADMIN` calls `POST /api/v1/teachers`
  3. `NATIONAL_ADMIN` calls `POST /api/v1/students`
  4. `NATIONAL_ADMIN` calls `POST /api/v1/guardians`
  5. `DEPARTMENT_ADMIN` calls `POST /api/v1/coordinators`
  6. `MUNICIPALITY_ADMIN` calls `POST /api/v1/coordinators`
- **Classification:** **Missing Regression-Test Coverage.**

---

### Discrepancy 5: SuperAdmin Institutional Override Audit Classification
- **Approved Behavior (PO Decision):**  
  Superadmin platform infrastructure access must be explicitly identified, appropriately audited, and kept separate from ordinary user assignment workflows.
- **Current Source Code Reality:**  
  In [`backend/app/core/security/authorization.py:107-130`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py#L107-L130), Superadmin accesses are audited only for sensitive educational read resources (`incidents`, `evaluations`, `report_cards`). Institutional role creations by Superadmin generate standard `USER_CREATED` / `TEACHER_CREATED` audit events without a dedicated `SUPERADMIN_EMERGENCY_OVERRIDE` event classification.
- **Classification:** **Audit / Separation Enhancement.**

---

## 5. Security and Tenant-Isolation Findings

1. **Absolute Multi-Tenant Containment for Institutional Roles:**  
   In [`backend/app/api/deps.py:285-288`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/deps.py#L285-L288):
   ```python
   if current_user.institution_id:
       return current_user.institution_id
   ```
   For any actor whose active role is institutional (`rector`, `coordinator`, `teacher`, `student`, `guardian`), the server unconditionally binds the request to `current_user.institution_id`. Any client attempt to provide an `institution_id` query parameter or `x-institution-id` header is silently ignored.

2. **Server-Derivation of Territorial Scope:**  
   In [`backend/app/services/municipality_admin_service.py:328-335`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/municipality_admin_service.py#L328-L335), when a Municipality Admin is created, the parent department is resolved strictly from `municipality.department_id` in canonical database records. A client cannot assign a Municipality Admin to a mismatching department.

3. **Absence of Generic Arbitrary Role Mutation:**  
   Every role creation endpoint is strictly domain-typed:
   - `POST /api/v1/department-admins` $\rightarrow$ hardcodes role `department_admin`
   - `POST /api/v1/municipality-admins` $\rightarrow$ hardcodes role `municipality_admin`
   - `POST /api/v1/institutions/{id}/rector-invitation` $\rightarrow$ hardcodes role `rector`
   - `POST /api/v1/coordinators` $\rightarrow$ hardcodes role `coordinator`
   - `POST /api/v1/teachers` $\rightarrow$ hardcodes role `teacher`
   - `POST /api/v1/students` $\rightarrow$ hardcodes role `student`
   - `POST /api/v1/guardians` $\rightarrow$ hardcodes role `guardian`
   There is **no** `PATCH /users/{id}/role` or arbitrary role assignment endpoint in the backend.

4. **Session Invalidation on Reassignment & Revocation:**  
   - Rector revocation atomically marks `RefreshToken.is_revoked = True` for the revoked user.
   - Municipality Admin deactivation and reassignment atomically marks `RefreshToken.is_revoked = True`.
   - Department Admin deactivation and reassignment atomically marks `RefreshToken.is_revoked = True`.

---

## 6. Invitation and Account-Activation Flow Findings

1. **Rector Invitation Token Cryptographic Security:**  
   In [`backend/app/services/rector_onboarding_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py#L107-L113):
   - Generates 48-byte URL-safe cryptographic raw token (`secrets.token_urlsafe(48)`).
   - Raw token is returned **only once** for invitation link generation.
   - Database persists **only the SHA-256 hash** (`token_hash = hash_token(raw_token)`).
   - Plaintext credentials and raw tokens are never persisted in database columns or server logs.

2. **Single-Use and Expiration Enforcement:**  
   - Replay protection: Attempting to accept a consumed token (`is_used == True`) immediately fails with HTTP 409 Conflict.
   - Revocation protection: If replaced by a successor invitation (`is_revoked == True`), redemption fails with HTTP 409 Conflict.
   - Expiration: Tokens expire after configured TTL (default 7 days). Expired tokens are rejected with HTTP 410 Gone.

3. **Guardian Self-Service Activation:**  
   Per `[OPEN-DECISION-3A-01]`, a legal guardian may claim their account via verified national document identification / SIMAT record matching. This workflow is completely decoupled from student user permissions:
   - `STUDENT` cannot initiate, approve, or modify guardian activations.
   - `STUDENT` has zero access to guardian linkage endpoints.

---

## 7. Existing Test Coverage & Missing Regression Tests

### Existing Verified Coverage (`backend/tests/test_nta08_authority_chain.py`):
- `test_01`: SuperAdmin authority
- `test_02`: National Admin authority
- `test_03`: Department Admin provisions Municipality Admin in own department
- `test_04`: Department Admin invites Rector in own department
- `test_05`: Municipality Admin invites Rector in own municipality
- `test_06`: Rector provisions Coordinator
- `test_07`: Rector provisions Teacher
- `test_08`: Rector provisions Student
- `test_12`: Cross-department rejection (Anti-IDOR 403)
- `test_13`: Cross-municipality rejection (Anti-IDOR 403)
- `test_14`: Cross-institution rejection (Anti-IDOR 403)
- `test_15`: Role escalation rejection (403/404)
- `test_16`: Scope tampering rejection (403)
- `test_17`: Rector succession invariant (exactly 1 active rector)
- `test_18`: Invitation replay rejection (409)
- `test_19`: Invitation expiration rejection (410)
- `test_20`: Session invalidation after revocation

### Flawed Existing Tests (Need Inversion):
- `test_09_coordinator_provisions_teacher`: Currently passes because Coordinator has `teachers:create`. **Must be inverted to assert HTTP 403 `PERMISSION_DENIED`**.
- `test_10_coordinator_provisions_student`: Currently passes because Coordinator has `students:create`. **Must be inverted to assert HTTP 403 `PERMISSION_DENIED`**.
- `test_11_guardian_workflow`: Currently uses Coordinator to provision Guardian and link to Student. **Must be refactored so Rector provisions Guardian and links to Student, and Coordinator is asserted to receive HTTP 403**.

### Missing Negative Regression Tests to Add:
1. `test_nat_admin_cannot_provision_coordinator`: National Admin $\rightarrow$ `POST /api/v1/coordinators` $\rightarrow$ 403.
2. `test_nat_admin_cannot_provision_teacher`: National Admin $\rightarrow$ `POST /api/v1/teachers` $\rightarrow$ 403.
3. `test_nat_admin_cannot_provision_student`: National Admin $\rightarrow$ `POST /api/v1/students` $\rightarrow$ 403.
4. `test_nat_admin_cannot_provision_guardian`: National Admin $\rightarrow$ `POST /api/v1/guardians` $\rightarrow$ 403.
5. `test_dept_admin_cannot_provision_institutional_roles`: Dept Admin $\rightarrow$ `POST /api/v1/coordinators` $\rightarrow$ 403.
6. `test_muni_admin_cannot_provision_institutional_roles`: Muni Admin $\rightarrow$ `POST /api/v1/coordinators` $\rightarrow$ 403.
7. `test_student_cannot_link_guardian`: Student $\rightarrow$ `POST /api/v1/guardians/{id}/students/{id}` $\rightarrow$ 403.

---

## 8. Ordered Remediation Plan (Execution Blueprint)

*NO CODE OR DATABASE MUTATIONS ARE EXECUTED DURING THIS PHASE. THE FOLLOWING BLUEPRINT AWAITS EXPLICIT PRODUCT OWNER APPROVAL.*

### Phase 1: Product Owner Formal Decision Gate
- [ ] PO Decision 1: Confirm removal of `teachers:create`, `students:create`, `guardians:create`, `guardians:link_student` from `COORDINATOR` and `ACADEMIC_COORDINATOR`.
- [ ] PO Decision 2: Confirm whether `DEPARTMENT_ADMIN` and `NATIONAL_ADMIN` retain supervisory Rector invitation authority (`users:create_rector`) or if Rector invitation is exclusively restricted to `MUNICIPALITY_ADMIN`.

### Phase 2: RBAC Catalog Alignment (`backend/app/services/rbac_bootstrap_service.py`)
- [ ] Strip institutional role assignment permissions from `ROLE_PERMISSIONS_CONFIG["coordinator"]`:
  - Remove `"teachers:create"`
  - Remove `"students:create"`
  - Remove `"guardians:create"`
  - Remove `"guardians:link_student"`
- [ ] Strip identical permissions from `ROLE_PERMISSIONS_CONFIG[SystemRole.ACADEMIC_COORDINATOR.value]`.
- [ ] Verify `rector` retains full institutional management permissions (`coordinators:*`, `teachers:*`, `students:*`, `guardians:*`).
- [ ] If PO Decision 2 mandates single-parent Rector invitation: Remove `"users:create_rector"` from `national_admin` and `department_admin`.

### Phase 3: Controller & Endpoint Alignment
- [ ] In `backend/app/api/v1/endpoints/teachers.py`: Ensure `teachers:create` remains strictly enforced via `require_permission`.
- [ ] In `backend/app/api/v1/endpoints/students.py`: Ensure `students:create` remains strictly enforced via `require_permission`.
- [ ] In `backend/app/api/v1/endpoints/guardians.py`: Ensure `guardians:create` and `guardians:link_student` remain strictly enforced via `require_permission`.
- [ ] In `backend/app/api/v1/endpoints/institutions.py`: If PO Decision 2 mandates, align `_assert_rector_management_authority` to disallow Department Admin or National Admin direct invitations.
- [ ] Add explicit audit event tagging for Superadmin overrides (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`).

### Phase 4: Automated Regression Suite Alignment (`backend/tests/test_nta08_authority_chain.py`)
- [ ] Invert `test_09` to verify `COORDINATOR` calling `POST /api/v1/teachers` receives HTTP 403 `PERMISSION_DENIED`.
- [ ] Invert `test_10` to verify `COORDINATOR` calling `POST /api/v1/students` receives HTTP 403 `PERMISSION_DENIED`.
- [ ] Update `test_11` so `RECTOR` provisions Guardian and links Student, and add check verifying `COORDINATOR` receives HTTP 403 when attempting both actions.
- [ ] Add the 4 negative regression tests for `NATIONAL_ADMIN` attempting institutional role provisioning.
- [ ] Add negative regression tests for `DEPARTMENT_ADMIN` and `MUNICIPALITY_ADMIN` attempting institutional role provisioning.

### Phase 5: Documentation Synchronization
- [ ] Update `docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md`:
  - Correct Section 5 Role Assignment Matrix: remove `NATIONAL_ADMIN` from institutional rows; remove `COORDINATOR` from creator columns; annotate `SUPERADMIN` as emergency platform override.
  - Correct Section 6 "Who Creates Whom".
  - Update final certification summary.

---

## 9. Product Owner Decisions Required

Before implementing the remediation plan, the Product Owner must formally decide on the following two architectural questions:

### Decision Item 1: Coordinator Role Provisioning Rights
- **Option A (Strict PO Canonical Alignment — Recommended):**  
  Strip `teachers:create`, `students:create`, `guardians:create`, and `guardians:link_student` from `COORDINATOR`. Only `RECTOR` can provision institutional users. Coordinator manages academic schedules, classes, evaluations, and incidents.
- **Option B (Operational Delegation Exception):**  
  Formally ratify an approved exception allowing Coordinator to provision Teachers, Students, and Guardians under Rector delegation within the same institution.

### Decision Item 2: Multi-Tier Rector Invitation Authority
- **Option A (Supervisory Escalation Model — Recommended):**  
  Maintain current implementation where `MUNICIPALITY_ADMIN` is the normal local authority, but `DEPARTMENT_ADMIN` (within department) and `NATIONAL_ADMIN` (national) retain supervisory authority to invite/revoke Rectors (e.g. for uncertified municipalities or state intervention).
- **Option B (Strict Single-Parent Chain):**  
  Strip `users:create_rector` from `department_admin` and `national_admin`. Only `MUNICIPALITY_ADMIN` can invite Rectors. Department Admin must provision a Municipality Admin first.

---

## 10. Exact Evidence & Repository References

| Component | Repository Path | Line References | Key Implementation Detail |
| :--- | :--- | :--- | :--- |
| **Coordinator Permissions** | [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L551-L560) | Lines 551–560, 636–646 | Coordinator currently assigned `teachers:create`, `students:create`, `guardians:create`, `guardians:link_student`. |
| **National Admin Permissions** | [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py#L261-L272) | Lines 261, 270–272 | National Admin assigned only `:read` permissions for coordinators, teachers, students, guardians. |
| **SuperAdmin Wildcard Bypass** | [`backend/app/core/security/authorization.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py#L107-L130) | Lines 107–130 | `if SystemRole.SUPERADMIN in context.roles: return True`. Bypasses granular checks. |
| **Institutional Tenant Lock** | [`backend/app/api/deps.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/deps.py#L285-L288) | Lines 285–288 | Institutional users forced to `current_user.institution_id`; client overrides are ignored. |
| **Rector Management Authority** | [`backend/app/api/v1/endpoints/institutions.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py#L705-L754) | Lines 705–754 | `_assert_rector_management_authority` authorizes Superadmin, National Admin, Dept Admin (department-bounded), and Muni Admin (municipality-bounded). |
| **Rector Succession Invariant** | [`backend/app/services/rector_onboarding_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py#L146-L161) | Lines 146–161 | Rejects invitation with HTTP 409 `RECTOR_ALREADY_EXISTS` if active Rector UserRole exists. |
| **Rector Session Invalidation** | [`backend/app/services/rector_onboarding_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py#L568-L575) | Lines 568–575 | Revocation marks `RefreshToken.is_revoked = True` for revoked Rector user. |
| **Department Admin Scope** | [`backend/app/services/municipality_admin_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/municipality_admin_service.py#L238-L243) | Lines 238–243 | Verifies target municipality belongs to caller's `department_id`. |
| **Coordinator Provisioning Block** | [`backend/app/api/v1/endpoints/coordinators.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/coordinators.py#L144-L149) | Lines 144–149 | Explicitly rejects `COORDINATOR`, `TEACHER`, and `STUDENT` callers with HTTP 403. |
| **Guardian Linkage Isolation** | [`backend/app/services/guardian_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/guardian_service.py#L588-L607) | Lines 588–607 | Both Student and Guardian validated under caller's `institution_id` before linkage. |
| **Flawed Existing Tests** | [`backend/tests/test_nta08_authority_chain.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta08_authority_chain.py#L474-L580) | Lines 474–580 | Tests 9, 10, 11 assert Coordinator can provision Teacher, Student, Guardian. |

---

## 11. Final Gate Decision

```
================================================================================
FINAL GATE DECISION:
CONDITIONAL PASS
================================================================================
```

### Gate Justification:
1. **Security & Territorial Core is Intact:**  
   The platform's underlying security architecture preserves strict territorial isolation (Department Admin and Municipality Admin), tenant isolation (`current_user.institution_id`), single active Rector succession, Anti-IDOR enforcement, and hashed single-use cryptographic invitation tokens. No arbitrary role patching (`PATCH /users/{id}/role`) exists.
2. **Material Discrepancy Prevents Full Certification Pass:**  
   The `COORDINATOR` role currently possesses `teachers:create`, `students:create`, and `guardians:create` permissions, and automated tests 9, 10, and 11 currently validate that capability. This directly contradicts the Product Owner's canonical flow (#5 and #6), which dictates that `RECTOR` is the exclusive normal provisioning authority and `COORDINATOR` must not act as an alternative authority for assigning institutional roles.
3. **Product Owner Action Required:**  
   The gate cannot transition to **`CERTIFICATION PASS`** until the Product Owner resolves Decision Item 1 (stripping Coordinator creation permissions vs ratifying an exception) and Decision Item 2 (multi-tier Rector supervisory authority), followed by executing the Phase 2–5 remediation blueprint.

**STOP CONDITION HONORED:** Zero source code, database, permission, or test modifications were performed during this read-only audit. Execution is paused pending Product Owner authorization.
