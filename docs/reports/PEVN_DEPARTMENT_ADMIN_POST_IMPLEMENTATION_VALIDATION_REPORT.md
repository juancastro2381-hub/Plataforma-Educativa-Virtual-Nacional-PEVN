# PEVN — DEPARTMENT_ADMIN LIFECYCLE
## POST-IMPLEMENTATION DATA HYGIENE & KPI VALIDATION REPORT
**AI Software Factory v1.2**  
**Date:** 2026-10-05  
**Status:** COMPLETED & CERTIFIED  
**Priority:** HIGH  
**Scope:** VALIDATION / DATA HYGIENE / UX CORRECTION ONLY  

---

## EXECUTIVE SUMMARY

A post-implementation audit and forensic validation was performed on the `DEPARTMENT_ADMIN` lifecycle subsystem following the certification of the 17 security test scenarios and 25 regression test scenarios.

This intervention resolved:
1. **Mathematical KPI Inconsistency:** Replaced client-side page-slice calculations with authoritative server-side aggregation, restoring the mathematical invariant `Total = Activos + Inactivos`.
2. **Synthetic Test Data Contamination:** Audited and purged 15 ephemeral test accounts created during automated test execution, while strictly protecting all legitimate administrators and system audit logs.
3. **Department Coverage Presentation:** Corrected the national coverage KPI from `"3 de 3 departamentos canónicos"` to `"3 de 33 entidades territoriales canónicas"`, reflecting that 3 departments currently have provisioned administrators out of Colombia's 33 canonical territorial entities.
4. **Automated Teardown & Hygiene Hardening:** Enhanced `verify_department_admin_lifecycle.py` with an automated teardown routine to ensure future automated test runs do not pollute the operational database.
5. **Zero Security / RBAC Regression:** All 17 mandatory lifecycle security tests and all 25 RBAC governance regression tests passed with 100% success. The certified 17 atomic read permissions and zero-wildcard baseline for `DEPARTMENT_ADMIN` remain completely intact.

---

## 1. KPI INVESTIGATION

Prior to remediation, the Department Administrator management screen displayed:
- **TOTAL ADMINISTRADORES:** `29`
- **ACTIVOS:** `9`
- **INACTIVOS:** `1`

This display was mathematically inconsistent ($9 + 1 = 10 \neq 29$) and raised immediate data integrity concerns.

A database and code-level investigation revealed two compounding root causes:

### 1.1 Frontend Aggregation Defect
In `frontend/src/pages/admin/DepartmentAdminsView.tsx`, the KPI counts were calculated via `useMemo` as follows:
```typescript
const kpis = useMemo(() => {
  const totalCount = total // Server total count (29)
  const activeCount = admins.filter((a) => a.is_active).length // Counted on page array (10 items)
  const inactiveCount = admins.filter((a) => !a.is_active).length // Counted on page array (10 items)
  const assignedDeptCount = new Set(admins.map((a) => a.department_id)).size
  return {
    total: totalCount,
    active: activeCount,
    inactive: inactiveCount,
    departments: assignedDeptCount,
  }
}, [admins, total])
```
Because the table pagination pageSize is 10, the `admins` array contained only the 10 rows of the current page. On page 1, exactly 9 records were active and 1 record was inactive ($9 + 1 = 10$). However, `total` was taken from the server-side total count (29). This created the apparent paradox where the total was derived from the global dataset while active/inactive were derived from a single paginated slice.

### 1.2 Backend Query Over-Counting Defect
In `backend/app/services/department_admin_service.py` (`list_department_admins`), the `count_stmt` was defined as:
```python
count_stmt = (
    select(func.count(func.distinct(User.id)))
    .join(UserRole, User.id == UserRole.user_id)
    .join(Role, UserRole.role_id == Role.id)
    .where(Role.name == SystemRole.DEPARTMENT_ADMIN.value)
)
```
While the item transformation loop (`items.append(...)`) explicitly skipped accounts without an assigned `department_id`, the `count_stmt` did **not** filter by `UserRole.department_id.isnot(None)`. Consequently, 13 legacy accounts created in August 2026 prior to migration `024` (which had `department_id IS NULL`) were counted in `total` even though they were omitted from the returned administrator list.

---

## 2. ROOT CAUSE OF KPI DISCREPANCY

| Component | Defect | Impact |
| :--- | :--- | :--- |
| **Frontend** (`DepartmentAdminsView.tsx`) | Computed `active` and `inactive` from the 10-item `admins` page slice instead of global server counts. | Caused `active (9) + inactive (1) = 10`, creating discrepancy with `total = 29`. |
| **Frontend** (`DepartmentAdminsView.tsx`) | Computed `departments` from the 10-item `admins` page slice instead of global distinct departments. | Corrupted department coverage calculation when users navigated across pages. |
| **Backend** (`department_admin_service.py`) | `count_stmt` lacked `UserRole.department_id.isnot(None)`. | Counted 13 legacy pre-migration orphaned accounts that have no territorial assignment. |

---

## 3. FINAL AUTHORITATIVE COUNTS

Both backend and frontend were refactored to calculate KPIs server-side across the entire population of valid departmental administrators:
- A new endpoint `GET /api/v1/department-admins/kpis` was implemented.
- `DepartmentAdminListResponse` was extended to include authoritative `kpis: DepartmentAdminKPIs`.
- The query strictly enforces `UserRole.department_id.isnot(None)` in both data selection, pagination counting, and KPI aggregation.

### Certified Database State:
$$\text{Total Administradores} = \text{Activos} + \text{Inactivos}$$
$$3 = 3 + 0$$

- **Total Administradores:** `3`
- **Activos:** `3`
- **Inactivos:** `0`
- **Departamentos con Cobertura:** `3` de `33` ($9.09\%$ national coverage)

*(Note: When an administrator is deactivated via the UI, the invariant dynamically updates to $3 = 2 + 1$, maintaining strict mathematical consistency at all times).*

---

## 4. DEPARTMENT COVERAGE COUNTS

The Colombian national territorial catalog contains **33 canonical entities** (32 departments + Bogotá Capital District).

Prior to this fix, the UI displayed:
> `Dptos. con Cobertura: 3 / De 3 departamentos canónicos`

This was misleading because it evaluated against `GET /api/v1/departments`, which in the local development database only has seed rows for Atlántico, Bogotá, and Cundinamarca, creating the false impression that Colombia has only 3 departments.

### Remediation Applied:
The presentation was updated in `DepartmentAdminsView.tsx` to:
- **Card Title:** `Departamentos con Cobertura`
- **Metric Value:** `{kpis.departments_covered} de {kpis.total_canonical_departments || 33}` $\rightarrow$ **`3 de 33`**
- **Subtext:** `Entidades territoriales canónicas`

### Breakdown by Territorial Entity:
| DANE Code | Department Name | Provisioned Admin Username | Status | Scope Confinement |
| :---: | :--- | :--- | :---: | :---: |
| **08** | ATLÁNTICO | `Eduardo_Admin_Departamental` | Active | Strict (Anti-IDOR Verified) |
| **11** | CAPITAL BOGOTÁ, D.C. | `department_admin` | Active | Strict (Anti-IDOR Verified) |
| **25** | CUNDINAMARCA | `admin_cundinamarca` | Active | Strict (Anti-IDOR Verified) |

The remaining 30 Colombian departments are unprovisioned, as expected.

---

## 5. TEST-ACCOUNT INVENTORY

A forensic query identified 15 synthetic test accounts generated across four executions of `verify_department_admin_lifecycle.py`:

| # | User UUID | Username | Full Name | Email | Assigned DANE | Created At |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | `14205105-15e9-484a-ab53-f3aabb6e1771` | `admin.bogota.b2f2db` | AdminBogota Test01 | `admin.bogota.f13ae4@pevn.edu.co` | 11 | 2026-10-05 21:11:56 |
| 2 | `a57b0494-211e-4617-b437-1459bb1aed24` | `admin.bogota.06be65` | AdminBogota Test01 | `admin.bogota.f0c397@pevn.edu.co` | 11 | 2026-10-05 21:12:32 |
| 3 | `bc86e15e-1166-4bf3-bdb8-fd83af1abaa5` | `admin.bogota.b7bbb4` | AdminBogota Test01 | `admin.bogota.9da16b@pevn.edu.co` | 25 | 2026-10-05 21:13:04 |
| 4 | `0630ab6f-9be9-43c3-9b04-59b992655c35` | `admin.atlantico.4c8b60` | AdminAtlantico Test02 | `admin.atlantico.486a35@pevn.edu.co` | 08 | 2026-10-05 21:13:04 |
| 5 | `db510e94-7bd7-496e-a246-8441f5c5d304` | `admin.cundinamarca.0af333` | AdminCundinamarca Test03 | `admin.cundinamarca.d77fb2@pevn.edu.co` | 25 | 2026-10-05 21:13:06 |
| 6 | `b9a0d0d2-d7a2-4823-b7ed-27e1c0993d30` | `spoofed.ade6cd` | Spoofed Role | `spoofed.ade6cd@pevn.edu.co` | 08 | 2026-10-05 21:13:10 |
| 7 | `e5398e64-1223-4efd-894e-e979bfd87ea6` | `admin.bogota.7f1d8e` | AdminBogota Test01 | `admin.bogota.aaa3fb@pevn.edu.co` | 11 | 2026-10-05 21:13:57 |
| 8 | `b96682d1-dea0-4728-ae2c-7bebc639abc9` | `admin.bogota.a464aa` | AdminBogota Test01 | `admin.bogota.7fc315@pevn.edu.co` | 25 | 2026-10-05 21:15:08 |
| 9 | `caf9749d-f061-4a16-9b8a-d24529ffab2f` | `admin.atlantico.7f7213` | AdminAtlantico Test02 | `admin.atlantico.f18bf5@pevn.edu.co` | 08 | 2026-10-05 21:15:09 |
| 10 | `70fe4535-8a67-4fc4-8201-1301ef966ae5` | `admin.cundinamarca.78579f` | AdminCundinamarca Test03 | `admin.cundinamarca.49c94c@pevn.edu.co` | 25 | 2026-10-05 21:15:09 |
| 11 | `c4260e6d-36c7-499e-9af2-6cccd5e252a6` | `spoofed.777f9e` | Spoofed Role | `spoofed.777f9e@pevn.edu.co` | 08 | 2026-10-05 21:15:10 |
| 12 | `ca2bdc63-1d6e-41bf-b873-3521470dfcfd` | `admin.bogota.334b11` | AdminBogota Test01 | `admin.bogota.b5c6ba@pevn.edu.co` | 25 | 2026-10-05 21:15:40 |
| 13 | `86f8ad8e-23c4-4923-bccf-8e34576749be` | `admin.atlantico.8a9382` | AdminAtlantico Test02 | `admin.atlantico.0f45af@pevn.edu.co` | 08 | 2026-10-05 21:15:40 |
| 14 | `e600454f-8170-4023-9e7d-b5d1b527ad9b` | `admin.cundinamarca.0bf613` | AdminCundinamarca Test03 | `admin.cundinamarca.9df2ce@pevn.edu.co` | 25 | 2026-10-05 21:15:40 |
| 15 | `0522bc90-20d7-4499-9ce6-8e7d652709cd` | `spoofed.14e252` | Spoofed Role | `spoofed.14e252@pevn.edu.co` | 08 | 2026-10-05 21:15:41 |

All 15 accounts were conclusively identified as test artifacts by their naming structure (`AdminBogota Test01`, `AdminAtlantico Test02`, `AdminCundinamarca Test03`, `Spoofed Role`), email domain, and creation timestamps matching test runs.

---

## 6. CLEANUP PERFORMED

### 6.1 Safety Verification & Pre-conditions
- **Environment Confirmation:** Verified `ENVIRONMENT=development` in `backend/.env`.
- **Preservation Whitelist:** Explicit protection enforced for `department_admin`, `Eduardo_Admin_Departamental`, `admin_cundinamarca`, `admin_nacional`, and `superadmin`.
- **Audit Architecture Protection:** Foreign key references in `audit_logs` had `actor_id` set to `NULL` prior to deletion (`ondelete="SET NULL"`), ensuring zero audit record corruption.

### 6.2 Execution Summary
Executed via `backend/scratch/cleanup_test_department_admins.py --execute`:
- **Deleted Refresh Tokens:** 3
- **Deleted User Roles:** 15
- **Nullified Audit Actors:** 7
- **Deleted Users:** 15
- **Status:** COMMITTED TRANSACTION (Zero errors, zero orphaned rows).

### 6.3 Automated Teardown Hardening
To prevent future contamination, `backend/scratch/verify_department_admin_lifecycle.py` was updated with a teardown block that deletes the 4 synthetic test accounts created during the run immediately after all 17 assertions complete. Subsequent executions confirm the database remains 100% clean after test runs.

---

## 7. FILES MODIFIED

### Backend
1. `backend/app/schemas/department_admin.py`:
   - Added `DepartmentAdminKPIs` schema model.
   - Added `kpis: DepartmentAdminKPIs | None = None` to `DepartmentAdminListResponse`.
2. `backend/app/services/department_admin_service.py`:
   - Updated `list_department_admins()` query and `count_stmt` to filter by `UserRole.department_id.isnot(None)`.
   - Added `get_kpis()` method returning authoritative server-side counts enforcing `total = active + inactive`.
   - Updated `list_department_admins()` return tuple to `(items, total, kpis)`.
3. `backend/app/api/v1/endpoints/department_admins.py`:
   - Registered `GET /api/v1/department-admins/kpis` endpoint before `/{user_id}` route.
   - Updated `GET /api/v1/department-admins` handler to populate and return `kpis`.
4. `backend/scratch/cleanup_test_department_admins.py`:
   - Controlled cleanup script with `--execute` safeguard.
5. `backend/scratch/provision_cundinamarca_admin.py`:
   - Provisioned dedicated manual test administrator for Cundinamarca DANE 25.
6. `backend/scratch/verify_department_admin_lifecycle.py`:
   - Added automated teardown block for created test identities.
7. `backend/scratch/verify_post_implementation_manual_checks.py`:
   - Automated regression script for Section 9 verification.

### Frontend
1. `frontend/src/types/departmentAdmin.ts`:
   - Exported `DepartmentAdminKPIs` interface.
   - Added `kpis?: DepartmentAdminKPIs` to `DepartmentAdminListResponse`.
2. `frontend/src/services/departmentAdmin.ts`:
   - Added `getKPIs(): Promise<DepartmentAdminKPIs>` method.
3. `frontend/src/pages/admin/DepartmentAdminsView.tsx`:
   - Initialized `kpis` state from server data.
   - Set `kpis` from `res.kpis` on list retrieval.
   - Removed defective client-side `useMemo` calculation.
   - Updated Card 2 to display `"Departamentos con Cobertura: 3 de 33"`.
   - Added accessible pagination navigation bar at the bottom of the table using `Button` (`variant="secondary"`).

---

## 8. SECURITY REGRESSION RESULTS

### 8.1 Mandatory Lifecycle Security Suite
**Command:** `python scratch/verify_department_admin_lifecycle.py`
- **Result:** **17/17 PASS (100% SUCCESS)**
- **Teardown Execution:** `PASS` (Database hygiene preserved)

| Test ID | Scenario | Result |
| :---: | :--- | :---: |
| TEST 01 | SUPER_ADMIN creates DEPARTMENT_ADMIN for Bogotá (DANE 11) | **PASS** |
| TEST 02 | NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Atlántico (DANE 08) | **PASS** |
| TEST 03 | NATIONAL_ADMIN creates DEPARTMENT_ADMIN for Cundinamarca (DANE 25) | **PASS** |
| TEST 04 | DEPARTMENT_ADMIN attempts to create another administrator (HTTP 403) | **PASS** |
| TEST 05 | DEPARTMENT_ADMIN attempts to change their own department (HTTP 403) | **PASS** |
| TEST 06 | DEPARTMENT_ADMIN Bogotá attempts to modify Atlántico admin (HTTP 403) | **PASS** |
| TEST 07 | NATIONAL_ADMIN reassigns admin from Bogotá to Cundinamarca (Audit verified) | **PASS** |
| TEST 08 | Attempt to create admin with nonexistent department UUID (HTTP 404) | **PASS** |
| TEST 09 | Attempt to create admin with malformed UUID payload (HTTP 422) | **PASS** |
| TEST 10 | Client attempts role spoofing (`role="superadmin"` in body $\rightarrow$ enforced `department_admin`) | **PASS** |
| TEST 11 | Authenticate Atlántico admin $\rightarrow$ territorial scope resolution | **PASS** |
| TEST 12 | Atlántico admin requests Bogotá institution (HTTP 403 Anti-IDOR) | **PASS** |
| TEST 13 | Atlántico admin requests Bogotá user (HTTP 403 Anti-IDOR) | **PASS** |
| TEST 14 | Atlántico admin requests territorial analytics (Scoped to Atlántico only) | **PASS** |
| TEST 15 | Deactivate DEPARTMENT_ADMIN $\rightarrow$ login immediately blocked (HTTP 401) | **PASS** |
| TEST 16 | Reassigned admin resolves new Cundinamarca scope, old Bogotá scope revoked | **PASS** |
| TEST 17 | Certified Bogotá admin maintains exactly 17 permissions, zero wildcards | **PASS** |

### 8.2 RBAC Governance & Rector Invitation Regression Suite
**Command:** `pytest tests/test_rbac_governance_and_rector_invitation.py`
- **Result:** **25/25 PASS (100% SUCCESS in 49.51s)**
- Zero regressions across rector onboarding, token hashing, role boundary validation, and institutional isolation.

---

## 9. MANUAL VALIDATION RESULTS

Executed via `backend/scratch/verify_post_implementation_manual_checks.py`:

| Role / Actor | Action | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :---: |
| **SUPER / NATIONAL ADMIN** | Open Department Admin View | Authoritative global KPIs | `Total: 3, Act: 3, Inact: 0` | **PASS** |
| **SUPER / NATIONAL ADMIN** | Inspect Coverage Card | 3 provisioned of 33 national entities | `3 de 33` | **PASS** |
| **SUPER / NATIONAL ADMIN** | Verify Administrator List | Only legitimate admins shown | Atlántico, Bogotá, Cundinamarca | **PASS** |
| **SUPER / NATIONAL ADMIN** | Filter Atlántico | Single Atlántico admin | `Eduardo_Admin_Departamental` | **PASS** |
| **SUPER / NATIONAL ADMIN** | Filter Bogotá | Single Bogotá admin | `department_admin` | **PASS** |
| **SUPER / NATIONAL ADMIN** | Filter Cundinamarca | Single Cundinamarca admin | `admin_cundinamarca` | **PASS** |
| **SUPER / NATIONAL ADMIN** | Filter Active | 3 active accounts | 3 accounts returned | **PASS** |
| **SUPER / NATIONAL ADMIN** | Filter Inactive | 0 inactive accounts | 0 accounts returned | **PASS** |
| **SUPER / NATIONAL ADMIN** | Search by name (`Eduardo`) | Matches Carlos Aduardo | 1 record returned | **PASS** |
| **SUPER / NATIONAL ADMIN** | Search by username (`admin_cundinamarca`) | Matches Cundinamarca admin | 1 record returned | **PASS** |
| **SUPER / NATIONAL ADMIN** | Search by email (`department_admin@pevn.edu.co`) | Matches Bogotá admin | 1 record returned | **PASS** |
| **DEPARTMENT_ADMIN Atlántico** | Check Scope (`/api/v1/auth/me`) | Departmental, ATLÁNTICO | `is_department=True`, `dept_code=08` | **PASS** |
| **DEPARTMENT_ADMIN Atlántico** | Access Bogotá Institution (`e9f740be...`) | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| **DEPARTMENT_ADMIN Bogotá** | Check Scope (`/api/v1/auth/me`) | Departmental, BOGOTÁ D.C. | `is_department=True`, `dept_code=11` | **PASS** |
| **DEPARTMENT_ADMIN Bogotá** | Access Territorial Analytics | Confined to Bogotá D.C. | `jurisdiction=CAPITAL BOGOTÁ, D.C.` | **PASS** |
| **DEPARTMENT_ADMIN Cundinamarca** | Check Scope (`/api/v1/auth/me`) | Departmental, CUNDINAMARCA | `is_department=True`, `dept_code=25` | **PASS** |
| **DEPARTMENT_ADMIN Cundinamarca** | Access Bogotá Institution (`e9f740be...`) | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |

---

## 10. REMAINING LIMITATIONS

1. **Initial Credential Distribution:**
   Currently, administrator provisioning requires the creator (SUPER_ADMIN or NATIONAL_ADMIN) to provide an initial password or let the system generate a raw token.
2. **Operational Seed Coverage:**
   The development database currently contains canonical table rows for 3 departments (`08`, `11`, `25`). The remaining 30 departments exist in canonical Colombian reference datasets but have not been provisioned into the operational `departments` table (as instructed).

---

## 11. RECOMMENDED NEXT PHASE

### Secure One-Time Token Invitation Workflow (NEXT PHASE)
Per instruction Section 10, the secure one-time invitation flow was **not** implemented in this phase.
For the upcoming phase, it is recommended to adopt the Rector invitation pattern (`RectorInvitation` / `invitation_service`):
1. Create a `DepartmentAdminInvitation` entity with a cryptographically secure 256-bit token (SHA-256 hash persisted in database).
2. Transmit an invitation URL via email: `https://pevn.edu.co/auth/accept-department-admin-invitation?token=...`.
3. Inactive account activation upon password setup by the invited administrator, eliminating cleartext password sharing during provisioning.

---

## 12. FINAL ACCEPTANCE VERIFICATION

| Requirement | Evaluation Criteria | Result |
| :--- | :--- | :---: |
| Mathematical Invariant | $\text{Total} = \text{Activos} + \text{Inactivos}$ ($3 = 3 + 0$) | **PASS** |
| Authoritative Population | Server-side calculation via `GET /api/v1/department-admins/kpis` | **PASS** |
| Department Coverage | Displays distinct provisioned departments ($3$ de $33$) | **PASS** |
| Canonical Territorial Entities | 33 canonical Colombian entities preserved as denominator | **PASS** |
| Protection of Legitimate Admins | Zero legitimate accounts deleted (`dd44ceb4`, `a485f067`, `b56cba5b`) | **PASS** |
| Test Data Hygiene | 15 synthetic test accounts purged; teardown added to test script | **PASS** |
| Security Architecture Integrity | No permissions added/removed; Anti-IDOR strictly preserved | **PASS** |
| Mandatory Security Test Suite | `verify_department_admin_lifecycle.py` | **17/17 PASS** |
| Regression Test Suite | `test_rbac_governance_and_rector_invitation.py` | **25/25 PASS** |
| Permission Integrity | Exactly 17 atomic read permissions for `DEPARTMENT_ADMIN` | **PASS** |
| Zero Wildcards | `*:*` wildcard strictly absent for `DEPARTMENT_ADMIN` | **PASS** |
| Cross-Department Anti-IDOR | Strict HTTP 403 on cross-department institution/user reads | **PASS** |
| Documentation Deliverable | Comprehensive validation report created | **PASS** |

**OVERALL STATUS: GATE PASS — CERTIFIED READY FOR PRODUCTION / DEMO**
