# PEVN — DEPARTMENT ADMINISTRATOR SECURITY TEST REPORT
**Document Reference:** `docs/reports/PEVN_DEPARTMENT_ADMIN_SECURITY_TEST_REPORT.md`  
**Standard:** AI Software Factory v1.2 / Territorial RBAC Governance Suite  
**Scope:** DEPARTMENT_ADMIN Lifecycle & Territorial Isolation Verification  
**Evaluation Status:** PASS (17 / 17 Tests Succeeded — 100% Assertion Rate)  
**Date:** 2026-10-05  

---

## 1. Executive Summary

This security audit report provides authoritative forensic evidence of the validation of all 17 mandatory security test scenarios specified in the **PEVN Department Administrator Lifecycle & Territorial Provisioning Specification**. 

Testing was performed programmatically against the running FastAPI ASGI core with a PostgreSQL database and live Argon2id password verification, without browser emulation. All identity, scoping, Anti-IDOR, role boundaries, audit generation, and session revocation mechanics were rigorously verified.

---

## 2. Test Execution Environment

| Parameter | Value |
|---|---|
| **API Engine** | FastAPI ASGI Core (`backend/app/main.py`) |
| **Database** | PostgreSQL 16.1 (`localhost:5433/pevn_db`) |
| **Authentication** | HS256 JWT (Access) + SHA-256 Hashed Opaque Refresh Tokens |
| **Password Hashing** | Argon2id (`app/core/security/password.py`) |
| **Authorization Engine** | `CentralizedAuthorizationService` (`app/core/security/authorization.py`) |
| **Test Runner** | `backend/scratch/verify_department_admin_lifecycle.py` |
| **HTTP Transport** | `httpx.ASGITransport(app=app, base_url="http://localhost")` |

---

## 3. Mandatory Security Test Matrix (TEST 01 – TEST 17)

| Test ID | Scenario Description | Expected Result | Actual Result | Status |
|---|---|---|---|:---:|
| **TEST 01** | `SUPER_ADMIN` creates `DEPARTMENT_ADMIN` for Bogotá D.C. (DANE 11) | HTTP 201, role = `department_admin`, dept = DANE 11 | HTTP 201 Created, `user_roles.department_id` persisted | **PASS** |
| **TEST 02** | `NATIONAL_ADMIN` creates `DEPARTMENT_ADMIN` for Atlántico (DANE 08) | HTTP 201, role = `department_admin`, dept = DANE 08 | HTTP 201 Created, canonical DANE 08 linked | **PASS** |
| **TEST 03** | `NATIONAL_ADMIN` creates `DEPARTMENT_ADMIN` for Cundinamarca (DANE 25) | HTTP 201, role = `department_admin`, dept = DANE 25 | HTTP 201 Created, canonical DANE 25 linked | **PASS** |
| **TEST 04** | `DEPARTMENT_ADMIN` attempts to create another `DEPARTMENT_ADMIN` | HTTP 403 Forbidden | HTTP 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 05** | `DEPARTMENT_ADMIN` attempts to change their own department | HTTP 403 Forbidden | HTTP 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 06** | `DEPARTMENT_ADMIN` Bogotá attempts to modify Atlántico administrator | HTTP 403 Forbidden | HTTP 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 07** | `NATIONAL_ADMIN` reassigns Bogotá admin to Cundinamarca | HTTP 200, audit event created, next scope = DANE 25 | HTTP 200, Audit `department_admin.department_changed` logged | **PASS** |
| **TEST 08** | Attempt to create `DEPARTMENT_ADMIN` with nonexistent `department_id` | HTTP 404/400, zero database mutation | HTTP 404 (`DEPARTMENT_NOT_FOUND`), DB unchanged | **PASS** |
| **TEST 09** | Attempt to create `DEPARTMENT_ADMIN` with malformed `department_id` | HTTP 422 / Validation Error | HTTP 422 Unprocessable Entity (UUID parser) | **PASS** |
| **TEST 10** | Attempt to create `DEPARTMENT_ADMIN` with client-supplied `role="superadmin"` | Client role ignored; server enforces `department_admin` | HTTP 201; DB persisted role is `department_admin` only | **PASS** |
| **TEST 11** | Authenticate Atlántico administrator & inspect `/api/v1/auth/me` | `is_national=False`, `is_department=True`, dept = Atlántico UUID | Exact match: `is_department: True`, Atlántico UUID resolved | **PASS** |
| **TEST 12** | Atlántico `DEPARTMENT_ADMIN` requests Bogotá institution | HTTP 403 Forbidden (Cross-department Anti-IDOR) | HTTP 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 13** | Atlántico `DEPARTMENT_ADMIN` requests Bogotá user | HTTP 403 Forbidden (Cross-department Anti-IDOR) | HTTP 403 Forbidden (`PERMISSION_DENIED`) | **PASS** |
| **TEST 14** | Atlántico `DEPARTMENT_ADMIN` requests national analytics summary | Scoped strictly to Atlántico (`total_departments=1`) | HTTP 200; `scope_level: DEPARTMENT`, 1 department only | **PASS** |
| **TEST 15** | Deactivate `DEPARTMENT_ADMIN` and attempt authentication | HTTP 200 on status patch; subsequent login rejected (401) | HTTP 200 deactivation; login fails with HTTP 401 | **PASS** |
| **TEST 16** | Verify reassigned administrator resolves new scope and loses old | Reassigned to Cundinamarca; Bogotá institution returns 403 | HTTP 200 login; Cundinamarca scope active; Bogotá 403 | **PASS** |
| **TEST 17** | Verify certified Bogotá `DEPARTMENT_ADMIN` baseline remains intact | Exactly 17 read-only permissions, 0 wildcards, DANE 11 | 17 permissions verified, 0 wildcards, DANE 11 intact | **PASS** |

---

## 4. In-Depth Scenario Evidence & Telemetry

### TEST 01 – TEST 03: Administrative Provisioning with Canonical Department Binding
- **Endpoint:** `POST /api/v1/department-admins`
- **Actors Tested:** `admin_nacional` (`superadmin`, level 100), `national_admin` (`national_admin`, level 90)
- **Persisted Role Verification:**
  - Query: `SELECT r.name, r.level, ur.department_id FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE ur.user_id = :uid;`
  - Results:
    - Bogotá Admin: `role = department_admin`, `level = 80`, `department_id = 7b774116-56f1-4199-ac63-ff646e7e327b`
    - Atlántico Admin: `role = department_admin`, `level = 80`, `department_id = caf3cc3f-a895-4fcd-b4b9-17405f3edf76`
    - Cundinamarca Admin: `role = department_admin`, `level = 80`, `department_id = 9aea113f-54e2-4345-8cc6-46970a91c7c6`
  - Audit Events: Logged `department_admin.created` with complete actor and canonical target metadata.

### TEST 04 – TEST 06: Privilege Escalation & Cross-Department Mutation Blocking
- **Actor:** `department_admin` (DANE 11, level 80)
- **Actions Attempted:**
  - Creation of a new departmental administrator: Denied with HTTP 403 (`required_permission=department_admins:create`).
  - Modification of own departmental jurisdiction: Denied with HTTP 403 (`required_permission=department_admins:update`).
  - Modification of Atlántico administrator profile: Denied with HTTP 403 (`required_permission=department_admins:update`).
- **Telemetry Record:**
  ```text
  [warning] Permission check failed required_permission=department_admins:create user_id=dd44ceb4-f5ca-4b5c-a801-0b4490125258
  [warning] Client error error_code=PERMISSION_DENIED path=/api/v1/department-admins status_code=403
  ```

### TEST 07 & TEST 16: Controlled Department Reassignment and Scope Rotation
- **Actor:** `national_admin`
- **Target User:** `admin.bogota.b7bbb4`
- **Reassignment Payload:** `{"new_department_id": "9aea113f-54e2-4345-8cc6-46970a91c7c6"}` (Cundinamarca)
- **Audit Verification:**
  ```sql
  SELECT event_type, metadata FROM audit_logs WHERE target_id = 'bc86e15e-1166-4bf3-bdb8-fd83af1abaa5' ORDER BY created_at DESC LIMIT 1;
  ```
  Result:
  ```json
  {
    "event_type": "department_admin.department_changed",
    "metadata": {
      "actor_user_id": "165eab38-8643-4ecc-9dc8-afcbe4265e9e",
      "target_user_id": "bc86e15e-1166-4bf3-bdb8-fd83af1abaa5",
      "previous_department_code": "11",
      "previous_department_id": "7b774116-56f1-4199-ac63-ff646e7e327b",
      "new_department_code": "25",
      "new_department_id": "9aea113f-54e2-4345-8cc6-46970a91c7c6"
    }
  }
  ```
- **Post-Reassignment Token Behavior:**
  - Login returns access token.
  - Calling `GET /api/v1/auth/me` resolves:
    `scope.department_id = "9aea113f-54e2-4345-8cc6-46970a91c7c6"` (`jurisdiction_name: "CUNDINAMARCA"`).
  - Attempting to access Bogotá institution `e9f740be-3806-4060-a808-9d02c8bf29af` results in immediate HTTP 403 Forbidden.

### TEST 08 – TEST 10: Input Validation, Anti-Tamper & Role Spoofing Prevention
- **Invalid UUID (`00000000-...`):** Returns HTTP 404 `DEPARTMENT_NOT_FOUND`. Database integrity verified: 0 user records created.
- **Malformed UUID (`"not-a-valid-uuid"`):** Returns HTTP 422 `Request validation failed`.
- **Role Spoofing Attempt:** Client sent `{"role": "superadmin", "roles": ["superadmin"]}` in body. Server ignored client fields and bound `SystemRole.DEPARTMENT_ADMIN`. Database inspection confirmed only `department_admin` was stored in `user_roles`.

### TEST 11 – TEST 14: Anti-IDOR & Territorial Containment Enforcement
- **Target Actor:** Atlántico Department Administrator (`caf3cc3f-a895-4fcd-b4b9-17405f3edf76`)
- **Institution Barrier (`GET /api/v1/institutions/{bogota_inst_id}`):**
  - Actor scope: `department_id = caf3cc3f-...`
  - Target institution scope: `department_id = 7b774116-...`
  - Result: `Scope check failed (cross-tenant access attempt) -> HTTP 403 Forbidden`.
- **User Barrier (`GET /api/v1/users?institution_id={bogota_inst_id}`):**
  - Verification query rejected target institution -> HTTP 403 Forbidden.
- **Analytics Barrier (`GET /api/v1/analytics/territorial/summary`):**
  - Result: `scope_level = "DEPARTMENT"`, `jurisdiction_name = "ATLÁNTICO"`, `total_departments = 1`. No national statistics leaked.

### TEST 15: Controlled Account Deactivation
- **Endpoint:** `PATCH /api/v1/department-admins/{id}/status` with `{"is_active": false}`
- **Database Status:** `users.is_active = false`, `user_roles.is_active = false`.
- **Active Refresh Tokens:** All revoked (`RefreshToken.is_revoked = true`).
- **Subsequent Authentication Attempt:** `POST /api/v1/auth/login` fails with HTTP 401 Unauthorized (`AUTHENTICATION_FAILED`).

### TEST 17: Certified Baseline Non-Regression
- **Target User:** `department_admin` (Bogotá, user ID `dd44ceb4-f5ca-4b5c-a801-0b4490125258`).
- **Role:** `department_admin` (Level 80).
- **Assigned Department:** `7b774116-56f1-4199-ac63-ff646e7e327b` (DANE 11 — CAPITAL BOGOTÁ, D.C.).
- **Permissions Count:** Exactly 17 canonical read-only permissions.
- **Wildcard Presence:** `False` (zero `*:*` wildcard permissions).
- **Live `/api/v1/auth/me` Response:** Confirms `is_national: False`, `is_department: True`, `department_id: "7b774116-56f1-4199-ac63-ff646e7e327b"`.

---

## 5. Security Verdict

```text
================================================================================
FINAL SECURITY VERDICT: CERTIFIED PASS
ALL 17 MANDATORY SECURITY TEST SCENARIOS PASSED WITH ZERO FAILURES.
ZERO PERMISSION LEAKS, ZERO WILD-CARD PERMISSIONS, STRICT TERRITORIAL ANTI-IDOR.
================================================================================
```
