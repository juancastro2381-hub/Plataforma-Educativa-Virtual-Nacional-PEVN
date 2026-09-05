# PEvN — Phase 12B Functional Acceptance Matrix
## Unified Real Teacher Provisioning & Lifecycle Closure

---

### Acceptance Criteria Matrix

| Criterion # | Acceptance Requirement | Implementation / Enforcement Mechanism | Validation Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **AC-01** | Open "Registrar Perfil Docente" | Modal component rendered in `TeachersView.tsx` with zero blocking errors. | Verified in Vitest & integration tests. | **PASS** |
| **AC-02** | Search for non-existent document (e.g. `20202020`) | Querying `GET /api/v1/users?search=20202020` returns 0 items without errors. | Verified in Vitest & `audit_phase12b_teacher_provisioning.py`. | **PASS** |
| **AC-03** | Display "No existe cuenta institucional" message | Modal renders clear, friendly alert indicating that no matching account was found. | Verified in Vitest. | **PASS** |
| **AC-04** | Action `+ Registrar como nuevo docente en la institución` | Button dynamically switches modal into inline civil identity entry mode without leaving the screen. | Verified in Vitest (`RoleNavigationFunctional.test.tsx`). | **PASS** |
| **AC-05** | Civil identity fields entry | Modal provides inputs for *Nombres, Apellidos, Tipo Doc, Número Doc, Correo Institucional, Teléfono*. | Verified in Vitest. | **PASS** |
| **AC-06** | Professional appointment fields entry | Modal provides inputs for *Área de Especialidad, Tipo de Nombramiento, Grado Escalafón*. | Verified in Vitest & backend API. | **PASS** |
| **AC-07** | Single atomic submission | Submitting form sends a single unified payload to `POST /api/v1/teachers` executing in one database transaction. | Verified in backend integration tests & audit script. | **PASS** |
| **AC-08** | Institutional User + Teacher profile creation | Backend creates both `User` row and `Teacher` row linked via `user_id`. | Verified in database assertions (`audit_phase12b_teacher_provisioning.py`). | **PASS** |
| **AC-09** | Teacher canonical role assignment | `UserRole` record with `Role('teacher')` linked to the new user within the institutional tenant. | Verified via direct DB inspection in test assertions. | **PASS** |
| **AC-10** | Zero UUID exposure | Administrator never sees, types, copies, or handles technical UUIDs. | Verified across all UI forms and schemas. | **PASS** |
| **AC-11** | Cross-tenant isolation barrier | `institution_id` extracted exclusively from caller token context; cross-tenant references rejected with 403. | Verified in test `test_cross_tenant_isolation_barrier`. | **PASS** |
| **AC-12** | Duplicate document & email prevention | Duplicate attempts return HTTP 409 `IDENTITY_CONFLICT` with generic privacy-preserving error messages. | Verified in test `test_provision_new_teacher_duplicate_prevention_api`. | **PASS** |
| **AC-13** | ACID consistency & rollback on failure | Any failure during profile or audit creation rolls back user creation; 0 orphaned users remain. | Verified by SQLAlchemy transaction isolation and exception handling. | **PASS** |
| **AC-14** | Mode 1 backward compatibility | Linking an already-existing institutional user via `user_id` continues to function with 100% fidelity. | Verified in test `test_teachers_and_groups_api`. | **PASS** |
| **AC-15** | Security state preservation | New user is created with `is_active=True`, `is_verified=False`, `must_change_password=True`, and Argon2id hash. | Verified in direct DB queries in audit script. | **PASS** |

---

### Test Suite Execution Summary

```text
==================================================
BACKEND PYTEST SUITE
==================================================
Total Tests: 306
Passed: 306
Failed: 0
Execution Time: ~4m 43s
Result: 100% PASS

==================================================
FRONTEND VITEST SUITE
==================================================
Total Tests: 44
Passed: 44
Failed: 0
Test Files: 8
Execution Time: ~35s
Result: 100% PASS

==================================================
TYPESCRIPT STRICT TYPECHECK
==================================================
Command: tsc --noEmit
Errors: 0
Result: 100% PASS

==================================================
PHASE 12B LIFECYCLE AUDIT SCRIPT
==================================================
Suites: 6
Passed: 6
Failed: 0
Result: 100% PASS
```
