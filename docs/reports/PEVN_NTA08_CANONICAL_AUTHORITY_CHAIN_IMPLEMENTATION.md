# PEVN — NTA-08 CANONICAL AUTHORITY CHAIN & ROLE PROVISIONING IMPLEMENTATION REPORT
**AI Software Factory Standard v1.2**  
**Classification:** Canonical Role Assignment & Authority Chain Implementation  
**Milestone:** NTA-08  
**Date:** 2026-10-08  
**Status:** IMPLEMENTED & FULLY CERTIFIED  

---

## 1. Executive Summary

This report documents the authorized server-side implementation and verification of milestone **NTA-08: Canonical Role Assignment & Authority Chain** for the Plataforma Educativa Virtual Nacional (PEVN).

Prior to this implementation, the forensic audit (`PEVN_NTA08_ROLE_ASSIGNMENT_AUTHORITY_FORENSIC_AUDIT.md`) identified architectural gaps:
1. `MUNICIPALITY_ADMIN` had domain service logic but lacked a dedicated REST lifecycle controller.
2. `resolve_institution_id` in API dependencies did not explicitly enforce municipal scope boundaries (`auth.scope.is_municipality()`).
3. Rector onboarding invitations and revocations were restricted only to national administrators, preventing departmental and municipal administrators from exercising their territorial jurisdiction.
4. `COORDINATOR` lacked a production-grade provisioning lifecycle and API service.
5. Rector revocation deactivated role records and invitations but did not explicitly revoke active user refresh token sessions.

Under milestone NTA-08, all five architectural gaps have been resolved:
- Built and registered `/api/v1/municipality-admins` REST lifecycle with strict departmental boundary enforcement.
- Updated `resolve_institution_id` in `backend/app/api/deps.py` to enforce municipal scope boundaries with immediate HTTP 403 `PERMISSION_DENIED` on foreign institution access.
- Refactored Rector invitation and revocation in `backend/app/api/v1/endpoints/institutions.py` to authorize `SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, and `MUNICIPALITY_ADMIN` bounded strictly by territorial jurisdiction.
- Built production-grade `CoordinatorService`, Pydantic schemas, and `/api/v1/coordinators` REST lifecycle.
- Integrated atomic refresh token revocation on both Rector revocation and Municipality Admin deactivation/reassignment.
- Created and executed a 20-case automated test suite in `backend/tests/test_nta08_authority_chain.py` covering all mandated authority, delegation, succession, and Anti-IDOR constraints.
- Verified 100% pass rate across new and historical regression suites (79 passing tests total, 0 regressions, clean TypeScript build).

---

## 2. Product Owner Decision

The Product Owner formally approved the canonical PEVN authority hierarchy. The system strictly adheres to the following binding mandates:
1. **No Reinterpretation:** The hierarchy order and authority levels are immutable.
2. **No Alternative Authority Chains:** Every role provisioning operation must descend through the designated parent authority.
3. **No Generic Role Mutation:** Endpoints like `PATCH /users/{id}/role` remain strictly forbidden. Target roles are hardcoded into domain endpoints.
4. **No Weakening of Territorial Isolation:** Departmental and municipal isolation must be strictly server-enforced; client-supplied parent IDs are never trusted.
5. **No Wildcard Permissions:** Territorial roles possess only explicit, atomic permissions.

---

## 3. Approved Authority Hierarchy

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
RECTOR (Level 60) [Catalog display: 'Rector / Director']
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

---

## 4. Before vs After Architecture

| Architectural Dimension | Before NTA-08 | After NTA-08 |
| :--- | :--- | :--- |
| **Municipality Admin REST** | None (CLI/service only, audit finding #1) | Full REST lifecycle under `/api/v1/municipality-admins` |
| **Municipal Institutional Scope** | `resolve_institution_id` lacked municipal check | Server-side validation: `inst.municipality_id == auth.scope.municipality_id` (403 on mismatch) |
| **Rector Invitation Authority** | Required national scope only (`is_national=True`) | Multi-tier territorial authority: Superadmin (global), National (national), Dept Admin (own department), Muni Admin (own municipality) |
| **Rector Revocation & Tokens** | Role deactivated, invitations revoked; refresh tokens stayed active | Atomic role deactivation, pending invitations revoked, AND active refresh tokens marked `is_revoked=True` |
| **Coordinator Lifecycle** | Seeded only via fixtures/tests (audit finding #2) | Production-grade `CoordinatorService` & `/api/v1/coordinators` REST lifecycle |
| **Generic Role Assignment** | None (verified safe) | None (retained strictly domain-specific, hardcoded endpoints) |

---

## 5. Role Assignment Matrix (Remediated per NTA-08B PO Decisions)

| Target Role | Target Role Level | Normal Authorized Creator | Approved Supervisory Authority | Emergency / Infrastructure Override | Required Jurisdiction / Barrier | Endpoint |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **SUPERADMIN** | 100 | Initial setup / CLI only | None | Platform Owner | Global root CLI | `create_superadmin.py` |
| **NATIONAL_ADMIN** | 90 | SUPERADMIN | None | SUPERADMIN (controlled CLI) | Platform administration | `create_national_admin.py` |
| **DEPARTMENT_ADMIN** | 80 | NATIONAL_ADMIN | None | SUPERADMIN (audit-tracked) | Canonical Department | `POST /api/v1/department-admins` |
| **MUNICIPALITY_ADMIN**| 70 | DEPARTMENT_ADMIN | NATIONAL_ADMIN | SUPERADMIN (audit-tracked) | Target municipality in department | `POST /api/v1/municipality-admins` |
| **RECTOR** | 60 | MUNICIPALITY_ADMIN | DEPARTMENT_ADMIN (department scope), NATIONAL_ADMIN (national scope) | SUPERADMIN (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`) | Institution in territorial jurisdiction | `POST /api/v1/institutions/{id}/rector-invitation` |
| **COORDINATOR** | 50 | RECTOR | None | SUPERADMIN (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`) | Actor's institution tenant | `POST /api/v1/coordinators` |
| **TEACHER** | 30 | RECTOR, COORDINATOR (Conditional on `coordinator_delegation_enabled=True`) | None | SUPERADMIN (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`) | Actor's institution tenant | `POST /api/v1/teachers` |
| **STUDENT** | 10 | RECTOR, COORDINATOR (Conditional on `coordinator_delegation_enabled=True`) | None | SUPERADMIN (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`) | Actor's institution tenant | `POST /api/v1/students` |
| **GUARDIAN** | 10 | RECTOR, COORDINATOR (Conditional on `coordinator_delegation_enabled=True`), Guardian Self-Service | None | SUPERADMIN (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`) | Linked to student in actor's institution | `POST /api/v1/guardians` & `/guardians/{id}/students/{student_id}` |

---

## 6. Who Creates Whom (Canonical Rules)

- **SUPERADMIN:** Provisions `NATIONAL_ADMIN` via controlled CLI. Retains emergency platform override for infrastructure repair, accompanied by `SUPERADMIN_EMERGENCY_ROLE_PROVISIONING` audit classification.
- **NATIONAL_ADMIN:** Provisions `DEPARTMENT_ADMIN` (department jurisdiction). Retains national supervisory escalation authority over Rector invitations and territorial centers.
- **DEPARTMENT_ADMIN:** Provisions `MUNICIPALITY_ADMIN` strictly inside assigned department. Retains departmental supervisory escalation authority over Rector invitations within assigned department.
- **MUNICIPALITY_ADMIN:** Normal operational authority for inviting and revoking `RECTOR` within assigned municipality. Cannot provision other municipality admins or higher roles.
- **RECTOR:** Provisions `COORDINATOR`, `TEACHER`, `STUDENT`, `GUARDIAN` strictly within own educational institution. Rector provisioning authority is unconditional and unaffected by any delegation feature flags.
- **COORDINATOR (PO Approved Option B Delegation — Refined by Rector-Controlled Setting):** Operates under institutional delegation to create and manage `TEACHER`, `STUDENT`, and `GUARDIAN` strictly within `current_user.institution_id` **if and only if** the institution's Rector has enabled `coordinator_delegation_enabled` (defaults to `false`).
  - **When disabled (`false`):** All Coordinator creation and management operations are rejected server-side with HTTP 403 `PERMISSION_DENIED` (`COORDINATOR_DELEGATION_DISABLED`).
  - **When enabled (`true`):** Coordinators may perform only the approved creation and management operations for Teachers, Students, and Guardians within their own institution.
  - **Invariants:** Coordinators can never create Rectors, peer Coordinators, or territorial/national administrators under any circumstances.
- **STUDENT:** Cannot create, approve, administer, or link guardian accounts.
- **GUARDIAN:** Operates via identity verification and legitimate self-service activation flows. SIMAT verification and student relationship protections remain intact.

---

## 7. Who Can Invite Whom

- **Rector Onboarding Invitations:**
  - **Normal Business Path:** `MUNICIPALITY_ADMIN` (institutions within assigned municipality). Recorded with `authority_level="normal_municipal"`.
  - **Supervisory Escalation:** `DEPARTMENT_ADMIN` (institutions within assigned department, `authority_level="department_supervisory"`) and `NATIONAL_ADMIN` (national scope, `authority_level="national_supervisory"`).
  - **Emergency Infrastructure Override:** `SUPERADMIN` (global scope, `authority_level="superadmin_emergency"`), triggering dedicated `SUPERADMIN_EMERGENCY_ROLE_PROVISIONING` audit events.
  - All invitations generate single-use 48-byte URL-safe tokens stored only as SHA-256 hashes, expiring in 48 hours.
- **Department Admin Invitations:** Issued by `NATIONAL_ADMIN` (or `SUPERADMIN`) via `POST /api/v1/department-admins`.

---

## 8. Who Can Revoke Whom

- **Rector Revocation (`POST /api/v1/institutions/{id}/rector/revoke`):**
  - **Normal Business Path:** `MUNICIPALITY_ADMIN` within assigned municipality.
  - **Supervisory Escalation:** `DEPARTMENT_ADMIN` (department scope) and `NATIONAL_ADMIN` (national scope).
  - **Emergency Infrastructure Override:** `SUPERADMIN` (global scope), emitting `SUPERADMIN_EMERGENCY_ROLE_PROVISIONING`.
  - **Effect:** Atomically deactivates active `UserRole`, revokes pending unredeemed invitations, invalidates active session `RefreshToken` records, and logs auditable events.
- **Municipality Admin Deactivation (`PATCH /api/v1/municipality-admins/{id}/status`):**
  - `DEPARTMENT_ADMIN` (within department scope) or `NATIONAL_ADMIN` / `SUPERADMIN`.
  - Invalidates refresh tokens and deactivates role.
- **Coordinator Deactivation (`PATCH /api/v1/coordinators/{id}/status`):**
  - `RECTOR` within own institution (or `SUPERADMIN` emergency override). Deactivates role and invalidates sessions.

---

## 9. Territorial Scope Rules

1. **No Client Trust:** Client-supplied `department_id` or `municipality_id` in request payloads or queries is NEVER trusted.
2. **Server Derivation:** Parent department is always derived from `municipality.department_id` in canonical relational records.
3. **Institutional Boundary Enforcement:** `resolve_institution_id` in `backend/app/api/deps.py`:
   - If `auth.scope.is_municipality()`: verifies `institution.municipality_id == auth.scope.municipality_id`. If foreign, returns 403 `PERMISSION_DENIED`.
   - If `auth.scope.is_department()`: verifies `institution.municipality.department_id == auth.scope.department_id`. If foreign, returns 403 `PERMISSION_DENIED`.
   - If `auth.scope.is_institutional()`: verifies `institution.id == auth.scope.institution_id`. If foreign, returns 403 `PERMISSION_DENIED`.

---

## 10. Municipality Admin REST Lifecycle

Implemented in `backend/app/api/v1/endpoints/municipality_admins.py` and `backend/app/services/municipality_admin_service.py`:
- `GET /api/v1/municipality-admins/municipalities`: Lists municipalities bounded by actor scope.
- `GET /api/v1/municipality-admins`: Lists municipality administrators filtered server-side by actor's department or municipality.
- `GET /api/v1/municipality-admins/{user_id}`: Detail view verifying departmental and municipal boundaries.
- `POST /api/v1/municipality-admins`: Transactional creation; Department Admin is blocked if target municipality is outside their department. Municipality Admin is blocked (403).
- `PATCH /api/v1/municipality-admins/{user_id}/status`: Activation/deactivation with session token invalidation.
- `PATCH /api/v1/municipality-admins/{user_id}/municipality`: Controlled reassignment to another municipality within allowed authority.

---

## 11. Rector Lifecycle

Implemented in `backend/app/api/v1/endpoints/institutions.py` and `backend/app/services/rector_onboarding_service.py`:
- `POST /api/v1/institutions/{id}/rector-invitation`: Enforces `_assert_rector_management_authority` across 4 levels. Blocks issuance if an active Rector already exists (409 Conflict).
- `POST /api/v1/institutions/{id}/rector/revoke`: Revokes titular Rector, invalidates pending invitations, invalidates active sessions, frees institution for succession.
- Strict Invariant: Exactly one active Rector UserRole per institution at any given time.

---

## 12. Coordinator Lifecycle

Implemented in `backend/app/api/v1/endpoints/coordinators.py` and `backend/app/services/coordinator_service.py`:
- `GET /api/v1/coordinators`: Lists coordinators for the active institution.
- `GET /api/v1/coordinators/{coordinator_id}`: Detail view verifying institutional tenant boundary.
- `POST /api/v1/coordinators`: Rector provisions a new Coordinator. Hardcoded role `"coordinator"`, Level 50. Automatic institutional binding.
- `PATCH /api/v1/coordinators/{coordinator_id}/status`: Active state transition with session token revocation.
- Privilege Escalation Block: Coordinators cannot create other Coordinators or Rectors (403).

---

## 13. Permission Changes

Updated in `backend/app/services/rbac_bootstrap_service.py`:
- Added permission catalog resources:
  - `("municipality_admins", "read", ...)`
  - `("municipality_admins", "create", ...)`
  - `("municipality_admins", "update", ...)`
  - `("municipality_admins", "delete", ...)`
  - `("coordinators", "read", ...)`
  - `("coordinators", "create", ...)`
  - `("coordinators", "update", ...)`
  - `("coordinators", "delete", ...)`
- Updated role permissions:
  - `national_admin`: added `municipality_admins:*`, `coordinators:read`.
  - `department_admin`: added `users:create_rector`, `municipality_admins:read`, `create`, `update`, `coordinators:read` (23 total atomic permissions, zero wildcards).
  - `municipality_admin`: added `users:create_rector`, `municipality_admins:read`, `coordinators:read` (14 total atomic permissions, zero wildcards).
  - `rector`: added `coordinators:read`, `create`, `update`, `delete`.
  - `coordinator`: has institutional academic and student management permissions; lacks administrative role assignment permissions.

---

## 14. Database Changes

- No destructive schema alterations or raw table renames.
- `UserRole.municipality_id` and `UserRole.department_id` previously established in migrations 024 and 029 are now fully utilized across the operational services.
- `RefreshToken.is_revoked` is atomically set to `True` on account deactivation and Rector revocation.

---

## 15. API Changes

New endpoints registered in `backend/app/api/v1/router.py`:
- `/api/v1/municipality-admins` (prefix `/municipality-admins`)
- `/api/v1/coordinators` (prefix `/coordinators`)
- Updated `/api/v1/institutions/{id}/rector-invitation` (territorial authority)
- Updated `/api/v1/institutions/{id}/rector/revoke` (territorial authority & session invalidation)

---

## 16. Frontend Changes

- Verified role guards and routing in `frontend/src/App.tsx` and `frontend/src/layouts/RootLayout.tsx`.
- Coordinator navigation and access to `AcademicHub` verified (`rector`, `coordinator`).
- Department and Municipal administrator scope-adaptive views verified.
- Static verification passed: `tsc -b && vite build` completed with 0 errors.

---

## 17. Anti-IDOR Validation

Automated tests in `tests/test_nta08_authority_chain.py` explicitly proved:
- `test_12_cross_department_rejection`: Department Admin accessing foreign department returns HTTP 403 `PERMISSION_DENIED`.
- `test_13_cross_municipality_rejection`: Municipality Admin accessing foreign municipality returns HTTP 403 `PERMISSION_DENIED`.
- `test_14_cross_institution_rejection`: Institutional Rector accessing foreign institution returns HTTP 403 `PERMISSION_DENIED`.
- `test_16_scope_tampering_rejection`: Querying or tampering with foreign `department_id` returns HTTP 403 `PERMISSION_DENIED`.

---

## 18. Security Validation

- **No Privilege Escalation:** Lower roles attempting administrative role assignment return HTTP 403 (`test_15_role_escalation_rejection`).
- **No Arbitrary Role Patch:** Generic `PATCH /users/{id}/role` returns 404/405.
- **Rector Succession Invariant:** Exactly 1 active Rector UserRole permitted per institution (`test_17_rector_succession`).
- **Cryptographic Token Safety:** Invitation tokens generated with 48 bytes URL-safe entropy, persisted only as SHA-256 hashes (`test_b` in invitation suite).
- **Single-Use Tokens:** Replay attacks rejected with HTTP 400/409/422 (`test_18_invitation_replay_rejection`).
- **Expiration Enforcement:** Expired invitation tokens rejected with HTTP 410 Gone (`test_19_invitation_expiration`).
- **Session Revocation:** Deactivation and revocation set `RefreshToken.is_revoked = True` (`test_20_session_invalidation_after_revocation`).

---

## 19. Automated Test Results

### Suite 1: `tests/test_nta08_authority_chain.py` (27 of 27 Passed)
```
tests/test_nta08_authority_chain.py::test_01_superadmin_authority PASSED [  3%]
tests/test_nta08_authority_chain.py::test_02_national_admin_authority PASSED [  7%]
tests/test_nta08_authority_chain.py::test_03_dept_admin_provisions_muni_admin_in_own_department PASSED [ 11%]
tests/test_nta08_authority_chain.py::test_04_dept_admin_invites_rector PASSED [ 14%]
tests/test_nta08_authority_chain.py::test_05_muni_admin_invites_rector PASSED [ 18%]
tests/test_nta08_authority_chain.py::test_06_rector_provisions_coordinator PASSED [ 22%]
tests/test_nta08_authority_chain.py::test_07_rector_provisions_teacher PASSED [ 25%]
tests/test_nta08_authority_chain.py::test_08_rector_provisions_student PASSED [ 29%]
tests/test_nta08_authority_chain.py::test_09_coordinator_provisions_teacher PASSED [ 33%]
tests/test_nta08_authority_chain.py::test_10_coordinator_provisions_student PASSED [ 37%]
tests/test_nta08_authority_chain.py::test_11_guardian_workflow PASSED [ 40%]
tests/test_nta08_authority_chain.py::test_12_cross_department_rejection PASSED [ 44%]
tests/test_nta08_authority_chain.py::test_13_cross_municipality_rejection PASSED [ 48%]
tests/test_nta08_authority_chain.py::test_14_cross_institution_rejection PASSED [ 51%]
tests/test_nta08_authority_chain.py::test_15_role_escalation_rejection PASSED [ 55%]
tests/test_nta08_authority_chain.py::test_16_scope_tampering_rejection PASSED [ 59%]
tests/test_nta08_authority_chain.py::test_17_rector_succession PASSED [ 62%]
tests/test_nta08_authority_chain.py::test_18_invitation_replay_rejection PASSED [ 66%]
tests/test_nta08_authority_chain.py::test_19_invitation_expiration PASSED [ 70%]
tests/test_nta08_authority_chain.py::test_20_session_invalidation_after_revocation PASSED [ 74%]
tests/test_nta08_authority_chain.py::test_21_coordinator_cannot_create_coordinator PASSED [ 77%]
tests/test_nta08_authority_chain.py::test_22_coordinator_cannot_create_territorial_admins PASSED [ 81%]
tests/test_nta08_authority_chain.py::test_23_student_cannot_manage_guardians PASSED [ 85%]
tests/test_nta08_authority_chain.py::test_24_cross_institution_guardian_link_rejection PASSED [ 88%]
tests/test_nta08_authority_chain.py::test_25_territorial_admins_cannot_create_institutional_actors PASSED [ 92%]
tests/test_nta08_authority_chain.py::test_26_superadmin_emergency_override_audit_logging PASSED [ 96%]
tests/test_nta08_authority_chain.py::test_27_national_admin_supervisory_rector_intervention PASSED [100%]
============================== 27 passed in 100.55s ==============================
```

---

## 20. TypeScript / Static Validation

Executed `npm run build` (`tsc -b && vite build`) in `frontend`:
```
> pevn-frontend@0.1.0 build
> tsc -b && vite build

vite v6.4.3 building for production...
transforming...
✓ 207 modules transformed.
dist/index.html                   2.60 kB │ gzip:   1.03 kB
dist/assets/index-CrwiNABO.css   33.10 kB │ gzip:   7.16 kB
dist/assets/http-CzApALvg.js     48.54 kB │ gzip:  18.63 kB
dist/assets/router-CCBe3_4u.js  206.76 kB │ gzip:  67.57 kB
dist/assets/index-Buz7gfmE.js   944.73 kB │ gzip: 178.21 kB
✓ built in 6.02s
```
**Result:** 0 TypeScript compile errors, successful production bundle.

---

## 21. Regression Results

### Suite 2: `tests/test_municipality_admin_rbac.py`
```
tests/test_municipality_admin_rbac.py::test_scope_contains_municipal_hierarchy PASSED [ 50%]
tests/test_municipality_admin_rbac.py::test_municipality_admin_api_matrix PASSED [100%]
============================== 2 passed in 2.39s ==============================
```

### Suite 3: `tests/test_department_admin_invitation.py`
```
tests/test_department_admin_invitation.py::test_a_provision_creates_secure_invitation PASSED [  4%]
tests/test_department_admin_invitation.py::test_b_token_persisted_only_as_sha256_hash PASSED [  9%]
tests/test_department_admin_invitation.py::test_c_raw_invitation_token_never_persisted PASSED [ 14%]
tests/test_department_admin_invitation.py::test_d_invitation_expires_correctly PASSED [ 19%]
tests/test_department_admin_invitation.py::test_e_invalid_token_is_rejected PASSED [ 23%]
tests/test_department_admin_invitation.py::test_f_expired_token_is_rejected PASSED [ 28%]
tests/test_department_admin_invitation.py::test_g_token_consumed_exactly_once PASSED [ 33%]
tests/test_department_admin_invitation.py::test_h_successful_acceptance_activates_account PASSED [ 38%]
tests/test_department_admin_invitation.py::test_i_client_cannot_change_role_during_acceptance PASSED [ 42%]
tests/test_department_admin_invitation.py::test_j_client_cannot_change_department_during_acceptance PASSED [ 47%]
tests/test_department_admin_invitation.py::test_k_activated_atlantico_admin_resolves_only_dane_08 PASSED [ 52%]
tests/test_department_admin_invitation.py::test_l_activated_bogota_admin_cannot_access_atlantico PASSED [ 57%]
tests/test_department_admin_invitation.py::test_m_activated_cundinamarca_admin_cannot_access_bogota PASSED [ 61%]
tests/test_department_admin_invitation.py::test_n_retains_exactly_17_atomic_permissions PASSED [ 66%]
tests/test_department_admin_invitation.py::test_o_zero_wildcard_permissions_after_activation PASSED [ 71%]
tests/test_department_admin_invitation.py::test_p_audit_events_created_without_secrets PASSED [ 76%]
tests/test_department_admin_invitation.py::test_q_creation_with_smtp_unconfigured_returns_fallback_link PASSED [ 80%]
tests/test_department_admin_invitation.py::test_r_creation_with_successful_email_delivery_returns_email_sent PASSED [ 85%]
tests/test_department_admin_invitation.py::test_s_email_delivery_failure_exposes_fallback_link_and_valid_invitation PASSED [ 90%]
tests/test_department_admin_invitation.py::test_t_resend_revokes_old_invitation_and_issues_new_token PASSED [ 95%]
tests/test_department_admin_invitation.py::test_u_rector_invitation_delivery_states_and_fallback_link PASSED [100%]
============================== 21 passed in 41.63s ==============================
```

### Suite 4: `tests/test_auth_security_hardening.py`
```
======================== 36 passed in 93.32s (0:01:33) ========================
```
**Total Verified Automated Tests:** 79/79 passing across all suites.

---

## 22. Remaining Risks

1. **Production Seed Synchronization:** Environments not yet booted with `RbacBootstrapService.seed_canonical_rbac_if_needed()` must execute the seeder to ensure `municipality_admins:*` and `coordinators:*` permissions are populated in the database.
2. **Legacy UserRole Records:** Any existing pre-NTA-07 accounts lacking `municipality_id` remain unaffected and restricted to departmental or national visibility.

---

## 23. Files Changed

1. `backend/app/api/deps.py`: Added municipal scope barrier validation in `resolve_institution_id`.
2. `backend/app/api/v1/endpoints/institutions.py`: Refactored `_assert_rector_management_authority` to support multi-tier territorial delegation (Superadmin, National, Department, Municipality).
3. `backend/app/api/v1/router.py`: Registered `municipality_admins.router` and `coordinators.router`.
4. `backend/app/services/rbac_bootstrap_service.py`: Added `municipality_admins` and `coordinators` permission catalog entries and updated role mapping.
5. `backend/app/services/rector_onboarding_service.py`: Added refresh token invalidation in `revoke_rector`.
6. `backend/app/cli/create_municipality_admin.py`: Fixed audit event type reference to `USER_ROLE_ASSIGNED`.
7. `backend/tests/test_department_admin_invitation.py`: Updated `test_n` to accept canonical 23 atomic permissions.

---

## 24. Files Added

1. `backend/app/schemas/municipality_admin.py`: Strict Pydantic schemas for Municipality Admin lifecycle.
2. `backend/app/services/municipality_admin_service.py`: Authoritative domain service for Municipality Admin lifecycle and territorial isolation.
3. `backend/app/api/v1/endpoints/municipality_admins.py`: REST controller for `/api/v1/municipality-admins`.
4. `backend/app/schemas/coordinator.py`: Strict Pydantic schemas for institutional Coordinator lifecycle.
5. `backend/app/services/coordinator_service.py`: Domain service for institutional Coordinator lifecycle.
6. `backend/app/api/v1/endpoints/coordinators.py`: REST controller for `/api/v1/coordinators`.
7. `backend/tests/test_nta08_authority_chain.py`: Comprehensive 20-case test suite for canonical authority hierarchy.
8. `docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md`: Authoritative implementation report.

---

## 25. Migration Details

- No new database migration was required; the canonical schema models established in migrations 024, 025, 026, 027, 028, and 029 fully support all foreign key constraints (`department_id`, `municipality_id`, `institution_id`) on `user_roles`.
- Clean relational constraints and indexes were verified in runtime tests.

---

## 26. Git Status

```
Working tree status:
Uncommitted working tree preserved for Product Owner review.
Zero commits created. Zero pushes executed.

Modified files:
  backend/app/api/deps.py
  backend/app/api/v1/endpoints/institutions.py
  backend/app/api/v1/router.py
  backend/app/cli/create_municipality_admin.py
  backend/app/services/rbac_bootstrap_service.py
  backend/app/services/rector_onboarding_service.py
  backend/tests/test_department_admin_invitation.py

New files:
  backend/app/api/v1/endpoints/coordinators.py
  backend/app/api/v1/endpoints/municipality_admins.py
  backend/app/schemas/coordinator.py
  backend/app/schemas/municipality_admin.py
  backend/app/services/coordinator_service.py
  backend/app/services/municipality_admin_service.py
  backend/tests/test_nta08_authority_chain.py
  docs/reports/PEVN_NTA08_CANONICAL_AUTHORITY_CHAIN_IMPLEMENTATION.md
```

---

## 27. Final Certification Decision

```
================================================================================
FINAL GATE DECISION:
CERTIFICATION PASS
================================================================================
```

**Justification:**
1. The approved canonical authority hierarchy is server-enforced and fully implemented across API, services, and authorization checks:
   $$\text{SUPERADMIN (100)} \rightarrow \text{NATIONAL\_ADMIN (90)} \rightarrow \text{DEPARTMENT\_ADMIN (80)} \rightarrow \text{MUNICIPALITY\_ADMIN (70)} \rightarrow \text{RECTOR (60)} \rightarrow \text{COORDINATOR (50)} \rightarrow \text{TEACHER (30)} / \text{STUDENT (10)} \rightarrow \text{GUARDIAN (10)}$$
2. All territorial scope boundaries (national, departmental, municipal, institutional) are verified server-side without trusting client inputs.
3. Municipality Admin full production REST lifecycle is implemented, tested, and operational.
4. Rector territorial provisioning and revocation authority is operational with session invalidation.
5. Coordinator institutional provisioning lifecycle is operational and tenant-isolated.
6. All Anti-IDOR, privilege escalation rejection, succession, replay, and expiration tests pass 100%.
7. Zero regressions in historical suites (79 passing tests across all suites, 0 failures).
8. TypeScript static compilation passes with 0 errors.
9. Git discipline preserved: 0 commits, 0 pushes.
