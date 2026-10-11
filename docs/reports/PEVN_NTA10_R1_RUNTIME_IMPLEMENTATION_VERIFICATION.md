# PEVN — NTA-10-R1: Runtime Implementation Verification and Rector Invitation UI Remediation Report

**Standard:** AI Software Factory Standard v1.2  
**Execution Agent:** Antigravity exclusively  
**Date:** 2026-10-10  
**Target Milestone:** NTA-10-R1 (Rector Provisioning & Invitation UI Remediation)  
**Corpus / Repository:** `Plataforma Educativa Virtual Nacional PEVN`  
**Exit Gate Status:** `CONDITIONAL PASS — MANUAL VALIDATION REQUIRED`

---

## 1. Executive Summary

Following the initial delivery of **NTA-10 (Secure Rector Provisioning and Invitation Lifecycle)**, the Product Owner observed that during manual testing, the expected Rector invitation actions were either unavailable or did not behave as specified in the live application.

Antigravity conducted an exhaustive forensic investigation across the active runtime stack (backend PID 23712 on `http://127.0.0.1:8000`, frontend PID 10212 on `http://localhost:3000`, and PostgreSQL on port 5433). Rather than rewriting services or introducing duplicate abstractions, this audit established the exact runtime truth, uncovered three interdependent root causes, and executed a minimal, surgical remediation:

1. **Schema Contract Gap:** The backend `InstitutionResponse` model omitted the Rector status fields (`has_active_rector`, `active_rector_name`, `active_rector_email`, and `has_pending_invitation`). The frontend had no data indicating whether an institution was vacant, had an active rector, or had an invitation awaiting redemption.
2. **UI State & Action Button Defect:** The frontend `InstitutionsView.tsx` unconditionally rendered both "✉️ Invitar Rector" and "🔄 Reenviar" on all active institutions. Attempting to invite a rector for an institution with an active rector yielded a `409 Conflict`, while users had zero visibility into why or who the incumbent rector was.
3. **Territorial Catalog Emptiness:** When testing with municipal administrators such as `Admin_Municip_ValParaiso` (Valparaíso, Caquetá), the database contained zero institutions in DANE municipality `18860`. The UI faithfully enforced territorial isolation and rendered an empty table ("No se encontraron instituciones"), giving the appearance that the feature was absent.

A minimal safe correction was implemented:
- Enriched `InstitutionResponse` with Rector status flags and batch-resolved incumbent/invitation state in `institution_service.py`.
- Updated `InstitutionsView.tsx` with a dedicated "Rector" column displaying visual status badges (`✓ Titular Activo`, `⏳ Invitación Pendiente`, `⚠️ Sin Rector`) and context-aware action buttons that prevent duplicate invitations while cleanly exposing invitation creation and resending.
- Seeded official DANE-registered test institutions for Valparaíso (`118860001293`) and Barranquilla (`108001000018`).
- Validated end-to-end runtime lifecycle via automated scripts, 93 regression tests, and zero-error TypeScript typechecking.

---

## 2. Actual Root Cause and Supporting Evidence

### Root Cause 1: Response Contract Missing Rector Status

**Evidence:**
Inspection of `backend/app/schemas/institution.py` and `frontend/src/types/institution.ts` revealed that `InstitutionResponse` only exposed:
```python
id, dane_code, name, department_code, department_name, municipality_code, municipality_name,
address, phone, email, is_active, created_at, updated_at
```
Neither `has_active_rector`, `active_rector_name`, `active_rector_email`, nor `has_pending_invitation` were included in the schema or populated by `InstitutionService.list_institutions()`. Consequently, the frontend `InstitutionsView.tsx` was blind to whether an institution was eligible for invitation.

### Root Cause 2: Frontend Unconditional Action Rendering and Lack of Status

**Evidence:**
In `frontend/src/pages/admin/InstitutionsView.tsx`:
```tsx
{inst.is_active && (
  <>
    <button onClick={() => handleOpenInvite(inst)}>✉️ Invitar Rector</button>
    <button onClick={() => handleResendInvite(inst)}>🔄 Reenviar</button>
  </>
)}
```
Both buttons were rendered side-by-side for every active institution regardless of state:
- Clicking "Invitar Rector" on an institution with an active rector triggered `POST /api/v1/onboarding/rector/invite`, which returned `409 Conflict: DUPLICATE_ACTIVE_RECTOR`.
- Clicking "Reenviar" on an institution without any pending invitation triggered `POST /api/v1/onboarding/rector/resend`, returning `404 Not Found: NO_PENDING_INVITATION`.
- The user received no feedback about current rector incumbency or pending invitation state.

### Root Cause 3: Empty State Under Territorial Isolation

**Evidence:**
Forensic query of the `institutions` table revealed:
```sql
SELECT id, dane_code, name, municipality_code FROM institutions;
```
Results showed only 3 institutions:
- DANE `108001000017`: Barranquilla (`08001`), with active rector `juancjj@colegio.edu.co`.
- DANE `111001000011`: Bogotá (`11001`).
- DANE `111001000012`: Bogotá (`11001`).

When the Product Owner authenticated as `Admin_Municip_ValParaiso` (`municipality_code = 18860`), the backend correctly executed territorial scoping (`SELECT ... WHERE municipality_code = '18860'`) and returned `[]`. The frontend rendered an empty table with no rows and no actions.

---

## 3. Runtime Instance Verification

Antigravity verified that active processes were running the exact current project code:

| Component | Target / URL | Process / State | Evidence |
|---|---|---|---|
| **Backend API** | `http://127.0.0.1:8000` | PID 23712 (`uvicorn app.main:app --reload`) | Verified active via socket connection; hot-reload triggered on edits |
| **Frontend Dev** | `http://localhost:3000` | PID 10212 (`vite --port 3000`) | Vite dev server running in HMR mode; changes immediately reflected |
| **Database** | `postgresql://postgres:***@localhost:5433/pevn_db` | Active PostgreSQL 16 | Verified direct DB connection and schema alignment |
| **Frontend API Base** | `/api/v1` (proxied to `http://127.0.0.1:8000/api/v1`) | `frontend/src/services/api/client.ts` | Validated proxy routing; requests route to backend endpoints |

No stale artifacts or uncommitted rogue branches were executing.

---

## 4. Exact Files Changed and Reasons

### 1. `backend/app/schemas/institution.py`
- **Reason:** Extended `InstitutionResponse` with:
  ```python
  has_active_rector: bool = False
  active_rector_name: Optional[str] = None
  active_rector_email: Optional[str] = None
  has_pending_invitation: bool = False
  ```
- **Safety:** Defaults preserve 100% backwards compatibility with existing consumers.

### 2. `backend/app/services/institution_service.py`
- **Reason:** Implemented helper method `_enrich_rector_status(db, institutions)`:
  - Performs batch queries against `UserRole` (`role_name='RECTOR', is_active=True`) and `OnboardingInvitation` (`role_code='RECTOR', is_revoked=False, accepted_at IS NULL, expires_at > now()`).
  - Sets `has_active_rector`, rector name, masked/sanitized email, and `has_pending_invitation`.
  - Integrated into `list_institutions`, `get_institution_by_id`, and `get_institution_by_dane`.

### 3. `frontend/src/types/institution.ts`
- **Reason:** Added matching TypeScript fields to `Institution` interface:
  ```typescript
  has_active_rector?: boolean;
  active_rector_name?: string;
  active_rector_email?: string;
  has_pending_invitation?: boolean;
  ```

### 4. `frontend/src/pages/admin/InstitutionsView.tsx`
- **Reason:**
  - Added dedicated **Rector** table column:
    - If `has_active_rector`: displays green badge `✓ Titular Activo` and rector name/email.
    - If `has_pending_invitation`: displays amber badge `⏳ Invitación Pendiente`.
    - If vacant: displays muted badge `⚠️ Sin Rector`.
  - Conditional Actions column:
    - If vacant (`!has_active_rector && !has_pending_invitation`): renders `✉️ Invitar Rector`.
    - If pending (`has_pending_invitation`): renders `🔄 Reenviar` (resends invitation and invalidates previous token).
    - If active (`has_active_rector`): renders disabled button `✓ Titular Asignado` (prevents duplicate invite attempts).
  - Reactive state update: when an invitation is created or resent, `institutions` state updates immediately without requiring a full page refresh.
  - Neutralized modal security note from "Como Administrador Nacional..." to "Como operador administrativo autorizado...".

### 5. `backend/scratch/provision_test_institutions.py`
- **Reason:** Provisioned canonical institutions from the official DANE catalog:
  - Valparaíso (`18860`): `118860001293` (I.E VALPARAISO)
  - Barranquilla (`08001`): `108001000018` (INSTITUCION EDUCATIVA DISTRITAL LAS AMERICAS)

---

## 5. Before-and-After Behavior

| Dimension | Before Remediation | After Remediation |
|---|---|---|
| **Rector Incumbency Visibility** | Unknown. Table had no rector column. | Clear status column with badges: `✓ Titular Activo`, `⏳ Invitación Pendiente`, `⚠️ Sin Rector`. |
| **Rector Actions for Vacant Institution** | Rendered both "Invitar" and "Reenviar". | Exclusively renders "✉️ Invitar Rector". |
| **Rector Actions for Pending Institution** | Rendered both "Invitar" and "Reenviar". Clicking "Invitar" failed with 409. | Exclusively renders "🔄 Reenviar". |
| **Rector Actions for Occupied Institution** | Rendered both buttons. Clicking "Invitar" failed with 409 error modal. | Renders disabled `✓ Titular Asignado`. Duplicate creation is physically blocked in UI. |
| **Valparaíso Testing Experience** | Empty table (`[]`). Feature appeared non-existent. | I.E VALPARAISO visible with "✉️ Invitar Rector" ready for testing. |
| **Post-Invitation State** | Required manual page reload to notice changes. | Reactive local state transition to `⏳ Invitación Pendiente` with dev link dialog. |

---

## 6. Effective Role and Permission Verification

Audit of database `roles` and `permissions` confirmed:
- `MUNICIPALITY_ADMIN` role ID: `4`
- Associated permissions:
  - `institutions:read`
  - `users:read`
  - `users:create_rector`
- Code validation in `backend/app/core/authorization/rules.py`:
  - `CAN_PROVISION_RECTOR = {"superadmin", "SUPERADMIN", "NATIONAL_ADMIN", "DEPARTMENT_ADMIN", "MUNICIPALITY_ADMIN"}`
- Territorial isolation in `RectorOnboardingService._assert_rector_management_authority`:
  - `MUNICIPALITY_ADMIN` may manage rectors **only** if `institution.municipality_code == operator.municipality_code`.
  - Attempting to manage an institution in another municipality raises `403 Forbidden: CROSS_MUNICIPALITY_UNAUTHORIZED`.

---

## 7. Endpoint and Response Contract Verification

### Endpoints Verified:
1. `GET /api/v1/institutions`:
   - Returns institutions filtered by the caller's territorial scope.
   - Now includes `has_active_rector`, `active_rector_name`, `active_rector_email`, and `has_pending_invitation`.
2. `POST /api/v1/onboarding/rector/invite`:
   - Payload: `{ "institution_id": "...", "email": "...", "first_name": "...", "last_name": "...", "document_type": "...", "document_number": "...", "phone": "..." }`.
   - Prohibits password or direct active flags in payload.
   - In development (`settings.is_development = True`), returns `raw_invitation_token` and `invitation_url`. In production, these fields are omitted.
3. `POST /api/v1/onboarding/rector/resend`:
   - Payload: `{ "institution_id": "..." }`.
   - Revokes prior pending token immediately (`is_revoked = True`).
   - Issues replacement token with fresh expiration.
4. `POST /api/v1/onboarding/verify-token`:
   - Verifies valid SHA-256 token hash. Rejects revoked (`409`), expired (`410`), or consumed tokens.
5. `POST /api/v1/onboarding/accept-invitation`:
   - Validates user-entered password against security policy.
   - Atomically marks invitation as consumed (`accepted_at = now()`), activates user account (`is_active = True`), and activates `RECTOR` role assignment.

---

## 8. Security Invariants and Territorial Isolation

The remediation preserved all security guarantees without compromise:
1. **Zero Operator Passwords:** Operator enters only identity metadata. Password setting occurs solely on `/auth/accept-invitation`.
2. **High-Entropy Tokens & Hash Storage:** Tokens generated with `secrets.token_urlsafe(32)`; persisted strictly as SHA-256 hashes (`token_hash`).
3. **Environment Isolation:** Raw tokens are never returned in production or staging responses, logs, or audit records.
4. **Single-Use & Invalidation on Resend:** Resending an invitation invalidates prior tokens immediately. Re-submitting an invalidated token returns `409 Conflict`.
5. **Double Activation Prevention:** Atomic verification and database transactions guarantee no race condition can redeem an invitation twice.
6. **Strict Territorial Boundaries:** Frontend buttons and state are strictly validated on the backend. Any forged API payload targeting an institution outside the administrator's territory is rejected with `403 Forbidden`.

---

## 9. Automated Test Results and Runtime Evidence

### Backend Pytest Suite
Executed command:
```powershell
python -m pytest tests/test_nta10_rector_provisioning.py tests/test_rector_succession.py tests/test_rbac_governance_and_rector_invitation.py tests/test_nta09_municipality_admin_provisioning.py tests/test_department_admin_invitation.py -v
```
**Result:** **93 passed, 0 failed, 11 warnings in 229.76s**

Test breakdown:
- `test_nta10_rector_provisioning.py`: 15 passed
- `test_rector_succession.py`: 8 passed
- `test_rbac_governance_and_rector_invitation.py`: 18 passed
- `test_nta09_municipality_admin_provisioning.py`: 23 passed
- `test_department_admin_invitation.py`: 29 passed

### Frontend TypeScript Verification
Executed command:
```powershell
npm run typecheck
```
**Result:** **0 errors (exited with code 0)**

### E2E Runtime Lifecycle Execution (`test_full_lifecycle_e2e.py`)
Executed full live API workflow against `http://127.0.0.1:8000`:
- Step 1: Login as `Admin_Municip_BAQ` → Token received.
- Step 2: Query institutions → Found Las Américas (vacant).
- Step 3: Issue Rector invitation → `201 Created`, token generated.
- Step 4: Verify institution status → `has_pending_invitation = True`.
- Step 5: Resend invitation → `200 OK`, new token generated.
- Step 6: Test old token verification → `409 Conflict: INVITATION_REVOKED` (correctly invalidated).
- Step 7: Test new token verification → `200 OK`.
- Step 8: Accept invitation with password `RectorSecure2026!` → `200 OK`, account activated.
- Step 9: Re-verify institution status → `has_active_rector = True`.
- Step 10: Attempt duplicate invite → `409 Conflict: DUPLICATE_ACTIVE_RECTOR` (correctly blocked).
- Step 11: Login as new Rector → `200 OK`.
- Step 12: Clean up test accounts and restore baseline state.

---

## 10. Manual Acceptance Runbook for the Product Owner

The Product Owner can perform acceptance testing directly in the browser using the running application (`http://localhost:3000`):

### Scenario 1: Municipal Administrator in Valparaíso (Vacant Institution)
1. Open browser at `http://localhost:3000/login`.
2. Login with credentials:
   - **Username / Email:** `admin_valparaiso@pevn.gov.co` (or `Admin_Municip_ValParaiso`)
   - **Password:** `AdminSecure2026!`
3. Navigate to **Instituciones** (`/admin/institutions`).
4. Observe the catalog:
   - Only institutions in Valparaíso are visible: **I.E VALPARAISO** (DANE `118860001293`).
   - The **Rector** column displays badge: `⚠️ Sin Rector`.
   - The **Acciones** column displays: `✉️ Invitar Rector`.
5. Click **Invitar Rector**:
   - The invitation modal opens.
   - Confirm **no password field** is present.
   - Complete rector details (e.g., Name: `Carlos`, Last Name: `Mendoza`, Email: `rector.valparaiso@pevn-test.edu.co`, Document: `CC 1098765432`).
   - Click **Enviar Invitación**.
6. Observe results:
   - Success modal appears displaying status and development activation link (`/auth/accept-invitation?token=...`).
   - Copy the activation link.
   - Close modal.
   - The table row dynamically updates to badge: `⏳ Invitación Pendiente`, and action becomes: `🔄 Reenviar`.

### Scenario 2: Resending an Invitation
1. In the same view, click `🔄 Reenviar` on the pending institution.
2. Observe modal displaying the new replacement activation link.
3. Attempting to use the previous link in a browser tab returns an error indicating the token was revoked.

### Scenario 3: Redeeming the Invitation and Activating the Rector
1. Open a new Incognito / Private browser window.
2. Paste the latest activation link (`http://localhost:3000/auth/accept-invitation?token=...`).
3. Confirm that the institution name (**I.E VALPARAISO**) and masked email are presented.
4. Set a strong password (e.g., `RectorValparaiso2026!`).
5. Click **Activar Cuenta**.
6. Confirm successful redirection to login or welcome view.
7. Log in as the new Rector using the newly established password.

### Scenario 4: Institution with Active Rector (Duplicate Protection)
1. Return to the municipal administrator session at `/admin/institutions`.
2. Refresh the page.
3. Observe that **I.E VALPARAISO** now displays badge: `✓ Titular Activo: Carlos Mendoza` and action button: `✓ Titular Asignado` (disabled).
4. Duplicate invitations are prohibited.

---

## 11. Git Working-Tree Status

In compliance with AI Software Factory Standard v1.2:
- **No Git commits were created.**
- **No changes were pushed to any remote.**
- **Branch:** `main`
- **Working tree:** Clean of unintended artifacts, preserving existing user workspace modifications.

---

## 12. Final Exit Gate

```
================================================================================
FINAL EXIT GATE: CONDITIONAL PASS — MANUAL VALIDATION REQUIRED
================================================================================
```

**Justification:**
1. **Diagnosis Completed:** All three root causes (response contract, UI action rendering, and territorial catalog empty state) were identified with hard evidence and remediated safely.
2. **Automated Verification Passed:**
   - 93 unit, integration, and security regression tests passed with zero failures.
   - Frontend TypeScript check (`npm run typecheck`) passed with zero errors.
   - Full live E2E lifecycle script executed and verified in runtime.
3. **Manual Validation Queued:** Because AI Software Factory Standard v1.2 strictly prohibits claiming browser manual tests have passed without direct observation by the Product Owner in their environment, this milestone is certified as **CONDITIONAL PASS**, pending Product Owner execution of the manual acceptance runbook provided in Section 10.
