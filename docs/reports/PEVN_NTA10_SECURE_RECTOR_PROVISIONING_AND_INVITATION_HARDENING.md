# PEVN — NTA-10: Secure Rector Provisioning & Invitation Hardening Report

**Standard:** AI Software Factory Standard v1.2  
**Execution Agent:** Antigravity exclusively  
**Execution Date:** 2026-10-09  
**Classification:** High — Authorization, Institutional Ownership, and Account Security  
**Exit Gate:** `CONDITIONAL PASS — MANUAL VALIDATION REQUIRED`  

---

## 1. Executive Summary

This report certifies the implementation and automated verification of **NTA-10: Secure Rector Provisioning and Invitation Lifecycle**.

Prior to this hardening, institutional Rector onboarding in PEVN exhibited key gaps:
1. The administrator interface in `InstitutionsView.tsx` gated the invitation button exclusively on `isNationalAdmin`, preventing legitimate `MUNICIPALITY_ADMIN` and `DEPARTMENT_ADMIN` operators from inviting Rectors in their respective jurisdictions.
2. In the backend `invite_rector_endpoint`, raw invitation tokens and activation URLs were disclosed unconditionally in response payloads, violating environment disclosure boundaries for non-development environments.
3. The public onboarding redemption in `RectorOnboardingService.accept_invitation` lacked an atomic concurrency claim, exposing the single-use token to race conditions under concurrent requests.
4. Pre-registered accounts were instantiated with `must_change_password=False` instead of enforcing mandatory password establishment upon invitation redemption.
5. `RectorOnboardingService` lacked a dedicated, auditable `resend_invitation` mechanism with automatic invalidation of stale pending tokens.

All vulnerabilities and functional gaps have been fully remediated, verified via 15 dedicated automated test cases in `backend/tests/test_nta10_rector_provisioning.py`, and confirmed against 78 regression tests across municipal admin provisioning, department admin invitations, and rector succession governance. Frontend TypeScript compilation was validated with zero errors (`npm run typecheck`).

---

## 2. Preflight Findings & Architecture Decisions

1. **Model Reuse Without Schema Drift:**
   The domain model `RectorInvitation` (`rector_invitations` table) in `backend/app/models/invitation.py` already includes `institution_id`, `user_id`, `token_hash` (SHA-256), `expires_at` (48 hours), `is_used`, `is_revoked`, and audit timestamps. Reusing this existing domain model avoided introducing redundant tables or schema migrations.

2. **Strict Territorial Isolation & Supervisory Authority:**
   Authority resolution in `_assert_rector_management_authority` (`backend/app/api/v1/endpoints/institutions.py`) validates:
   - `MUNICIPALITY_ADMIN`: Must match `institution.municipality_id == auth.scope.municipality_id`.
   - `DEPARTMENT_ADMIN`: Must match `institution.municipality.department_id == auth.scope.department_id`.
   - `NATIONAL_ADMIN` / `SUPERADMIN`: Supervisory platform-wide authority.
   Cross-territorial attempts are rejected with `403 Forbidden` (`PERMISSION_DENIED`).

3. **Succession Invariants:**
   Institutions may have only one active Rector. If an institution already possesses an active Rector (`UserRole.is_active == True`), any attempt to invite a new Rector is rejected with `409 Conflict` (`RECTOR_ALREADY_EXISTS`). Successive appointments require prior revocation via `POST /api/v1/institutions/{id}/rector/revoke`.

4. **Canonical URL Alignment:**
   Normalized all activation URL templates to `/auth/accept-invitation?token={raw_token}`, matching the canonical frontend routing in `App.tsx` and established in NTA-08/09.

---

## 3. Remediation Details & Code Modifications

### 3.1 Backend Service (`backend/app/services/rector_onboarding_service.py`)
- **Account Inactivity & Credential Invariants:** Pre-registered users are created with `is_active=False`, `is_verified=False`, `must_change_password=True`, and an unusable random Argon2id initial hash.
- **Atomic Single-Use Claim:** In `accept_invitation`, an atomic conditional SQL `UPDATE ... WHERE id = :id AND is_used = False AND is_revoked = False RETURNING id` was introduced. Only the first concurrent request claims the token; subsequent concurrent requests receive `409 Conflict` (`INVITATION_ALREADY_USED`).
- **Resend Method:** Implemented `resend_invitation(institution_id, ...)`:
  - Validates institution is active.
  - Rejects if institution already has an active Rector (`409 Conflict: ACCOUNT_ALREADY_ACTIVATED`).
  - Finds pending unverified Rector association (`is_active=False`).
  - Revokes all prior pending tokens.
  - Generates a new 48-byte URL-safe token (SHA-256 in DB, 48-hour expiration).
  - Dispatches email notification and logs `rector.invitation_resent` audit event.

### 3.2 Backend Endpoints (`backend/app/api/v1/endpoints/institutions.py`)
- **Environment-Gated Disclosure:** Gated `raw_invitation_token` and `invitation_url` behind `settings.is_development`. In staging and production, both attributes evaluate to `None`.
- **Resend Endpoint:** Added `POST /api/v1/institutions/{institution_id}/rector-invitation/resend` enforcing `_assert_rector_management_authority` and `users:create_rector` permission.

### 3.3 Audit Taxonomy (`backend/app/audit/interfaces.py`)
- Added `RECTOR_INVITATION_RESENT = "rector.invitation_resent"` to `AuditEventType`.

### 3.4 Frontend Client & UI
- **`frontend/src/services/institution.ts`:** Added `resendRectorInvitation(institutionId: string): Promise<RectorInvitationResponse>`.
- **`frontend/src/pages/admin/InstitutionsView.tsx`:**
  - Expanded Rector action availability: `const canManageRectors = isNationalAdmin || isDepartmentAdmin || isMunicipalityAdmin`.
  - Added "✉️ Invitar Rector" and "🔄 Reenviar" buttons for eligible institutions.
  - Added `handleResendInvite` handler with feedback alerts.
  - Aligned modal activation URL fallback to `/auth/accept-invitation?token=...`.

---

## 4. Complete List of Modified and Created Files

| File | Change Type | Description |
| :--- | :--- | :--- |
| `backend/app/audit/interfaces.py` | Modified | Added `RECTOR_INVITATION_RESENT` to `AuditEventType`. |
| `backend/app/services/rector_onboarding_service.py` | Modified | Added atomic claim, `must_change_password` lifecycle, canonical activation URL, and `resend_invitation`. |
| `backend/app/api/v1/endpoints/institutions.py` | Modified | Gated token disclosure behind `is_development`, added `POST /{id}/rector-invitation/resend`. |
| `frontend/src/services/institution.ts` | Modified | Added `resendRectorInvitation` API method. |
| `frontend/src/pages/admin/InstitutionsView.tsx` | Modified | Enabled Municipal & Department Admins to invite/resend rectors, aligned invitation links. |
| `backend/tests/test_nta10_rector_provisioning.py` | Created | 15 comprehensive automated test scenarios. |
| `docs/reports/PEVN_NTA10_PREFLIGHT_RECTOR_PROVISIONING_AUDIT.md` | Created | Preflight inspection and architectural decision report. |
| `docs/reports/PEVN_NTA10_SECURE_RECTOR_PROVISIONING_AND_INVITATION_HARDENING.md` | Created | Final hardening and certification report. |

---

## 5. Automated Validation & Test Execution Results

### 5.1 Focused NTA-10 Test Suite (`test_nta10_rector_provisioning.py`)
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_nta10_rector_provisioning.py -v
```
**Results:**
```
tests/test_nta10_rector_provisioning.py::test_01_muni_admin_can_invite_rector_in_own_municipality PASSED [  6%]
tests/test_nta10_rector_provisioning.py::test_02_muni_admin_cross_municipality_attempt_rejected PASSED [ 13%]
tests/test_nta10_rector_provisioning.py::test_03_muni_admin_cross_department_attempt_rejected PASSED [ 20%]
tests/test_nta10_rector_provisioning.py::test_04_dept_admin_supervisory_authority_and_cross_department_boundary PASSED [ 26%]
tests/test_nta10_rector_provisioning.py::test_05_national_admin_and_superadmin_supervisory_authority PASSED [ 33%]
tests/test_nta10_rector_provisioning.py::test_06_unauthorized_roles_and_unauthenticated_rejected PASSED [ 40%]
tests/test_nta10_rector_provisioning.py::test_07_inactive_institution_rejected PASSED [ 46%]
tests/test_nta10_rector_provisioning.py::test_08_password_and_is_active_injection_rejected PASSED [ 53%]
tests/test_nta10_rector_provisioning.py::test_09_unactivated_rector_cannot_login PASSED [ 60%]
tests/test_nta10_rector_provisioning.py::test_10_verify_and_accept_invitation_lifecycle PASSED [ 66%]
tests/test_nta10_rector_provisioning.py::test_11_duplicate_active_rector_rejected_until_revoked PASSED [ 73%]
tests/test_nta10_rector_provisioning.py::test_12_resend_rector_invitation_workflow PASSED [ 80%]
tests/test_nta10_rector_provisioning.py::test_13_expired_invitation_token_rejected PASSED [ 86%]
tests/test_nta10_rector_provisioning.py::test_14_production_environment_omits_raw_token PASSED [ 93%]
tests/test_nta10_rector_provisioning.py::test_15_audit_events_recorded_without_secrets PASSED [100%]

======================= 15 passed, 2 warnings in 50.82s =======================
```

### 5.2 NTA-09 Municipal Admin Regression Suite (`test_nta09_municipality_admin_provisioning.py`)
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_nta09_municipality_admin_provisioning.py -v
```
**Results:** `22 passed in 53.02s` (100% pass rate).

### 5.3 Rector Succession & RBAC Governance Suite (`test_rector_succession.py`, `test_rbac_governance_and_rector_invitation.py`)
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_rector_succession.py tests/test_rbac_governance_and_rector_invitation.py -v
```
**Results:** `35 passed in 138.02s` (100% pass rate).

### 5.4 Department Admin Invitation Suite (`test_department_admin_invitation.py`)
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_department_admin_invitation.py -v
```
**Results:** `21 passed in 48.66s` (100% pass rate).

### 5.5 Frontend Type Check
```bash
npm run typecheck
```
**Results:** `0 errors` (Process exited with code 0).

---

## 6. Security Analysis & Invariant Verification Matrix

| Security Invariant | Status | Enforcement Mechanism |
| :--- | :---: | :--- |
| **No Operator Password Setting** | VERIFIED | `RectorInvitationCreateRequest` has `ConfigDict(extra="forbid")`; injecting `password` returns `422 Unprocessable Content`. |
| **Inactive / Unverified Pre-Registration** | VERIFIED | `User(is_active=False, is_verified=False, must_change_password=True)` with unusable hash; login denied prior to activation. |
| **48-byte Single-Use Cryptographic Token** | VERIFIED | High-entropy 48-byte URL-safe string; only SHA-256 stored in DB; 48-hour expiration. |
| **Atomic Concurrency Claim** | VERIFIED | Conditional SQL UPDATE returning ID blocks double-redemption race conditions; returns `409 Conflict`. |
| **Territorial Isolation Barrier** | VERIFIED | Municipal Admin cannot invite rectors outside their municipality (`403 Forbidden`). |
| **Supervisory Authority Preserved** | VERIFIED | Department, National, and Superadmins retain jurisdictional rights. |
| **Rector Succession Governance** | VERIFIED | Rejecting second active rector (`409 Conflict`); revocation detaches incumbent and invalidates pending tokens. |
| **Staging/Production Secrecy** | VERIFIED | Non-development environments strictly return `raw_invitation_token=None` and `invitation_url=None`. |
| **Audit Hygiene** | VERIFIED | Audit logs record events (`rector.invited`, `rector.invitation_resent`, `rector.onboarding.completed`, `rector.revoked`) without exposing passwords or raw tokens. |

---

## 7. Manual Acceptance Procedure for Product Owner

Follow these step-by-step instructions in the browser to validate manual acceptance:

1. **Sign in as an Authorized Municipal Administrator:**
   - URL: `http://localhost:3000/login`
   - Use municipal admin credentials for an authorized municipality (e.g., `Admin_municipio_Juan` or provisioned test admin).
2. **Navigate to Institutions View:**
   - Select **"Instituciones Educativas"** from the navigation sidebar (`/admin/institutions`).
   - Confirm that the catalog lists only institutions belonging to your assigned municipality.
3. **Trigger Rector Invitation:**
   - Locate an active institution that currently does not have an active Rector.
   - Click the **"✉️ Invitar Rector"** button.
   - Confirm that the modal dialog contains fields for First Name, Last Name, Document Type, Document Number, Official Email, and Phone Number.
   - **Crucial Security Check:** Confirm there is **no password input field** anywhere in the modal.
4. **Submit Invitation:**
   - Submit the completed form.
   - Confirm the success notification appears.
   - Verify that the development-only modal opens with the copyable activation link (`/auth/accept-invitation?token=...`) and notes that SMTP is unconfigured.
   - Click **"Copiar enlace"** and save the link.
5. **Verify Account Remains Inactive:**
   - Attempt to log in with the invited Rector's email and any password.
   - Confirm that authentication is rejected.
6. **Redeem Invitation:**
   - Open a private/incognito browser window.
   - Navigate to the copied activation link (`/auth/accept-invitation?token=...`).
   - Confirm that the onboarding page displays the institution name, masked email, and password definition form.
   - Enter a secure password (minimum 8 characters) and confirm it.
   - Submit the form.
   - Confirm the success screen appears indicating that the account is activated.
7. **Verify Post-Activation Access:**
   - Log in with the newly established Rector credentials.
   - Confirm successful login, receipt of JWT session, and institutional access restricted to the assigned institution.
8. **Verify Single-Use Token Protection:**
   - Attempt to visit the invitation link again.
   - Confirm that the system displays an error explaining that the invitation link has already been used.
9. **Verify Territorial Isolation:**
   - Attempt to access an institution outside your municipality via URL or API.
   - Confirm that access is rejected with `403 Forbidden`.

---

## 8. Git Working Tree & Change Control

- **Git Commits/Pushes:** None. Working-tree modifications have been preserved.
- **Untracked Test/Report Files:** Kept localized to `backend/tests/` and `docs/reports/`.

---

## 9. Exit Gate Certification

```
=================================================================================
EXIT GATE STATUS: CONDITIONAL PASS — MANUAL VALIDATION REQUIRED
=================================================================================
Automated Backend Tests: 15 / 15 PASSED (test_nta10_rector_provisioning.py)
Regression Tests:        78 / 78 PASSED (NTA-09, succession, department admin)
Frontend Typecheck:      0 ERRORS (npm run typecheck)
Manual PO Acceptance:    PENDING BROWSER VERIFICATION (Section 7)
=================================================================================
```
