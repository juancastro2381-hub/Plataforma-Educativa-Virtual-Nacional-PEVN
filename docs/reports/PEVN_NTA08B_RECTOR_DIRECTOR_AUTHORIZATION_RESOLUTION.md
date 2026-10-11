# PEVN NTA-08B — RECTOR/DIRECTOR AUTHORIZATION DISCREPANCY RESOLUTION
## AI Software Factory Standard v1.2

```
================================================================================
MILESTONE:             NTA-08B FOCUSED VERIFICATION
CLASSIFICATION:        ROLE TAXONOMY & AUTHORIZATION RECONCILIATION
TARGET GATE:           CERTIFICATION PASS
SOURCE MANDATE:        PO RECTOR/DIRECTOR AUTHORIZATION DISCREPANCY RESOLUTION
AUTHORITY MODEL:       CANONICAL SYSTEMROLE.RECTOR & SUPERADMIN PLATFORM OVERRIDE
================================================================================
```

---

## 1. Executive Summary

This focused verification resolves the discrepancy regarding the `director` role in the **Rector-Controlled Coordinator Delegation** setting under AI Software Factory Standard v1.2.

### Forensic Finding:
1. **Taxonomy & Schema Source of Truth:**
   - In `backend/app/core/security/interfaces.py` (`SystemRole`) and `backend/app/services/rbac_bootstrap_service.py` (`CANONICAL_ROLES`), the sole canonical system role at Level 60 is:
     ```python
     SystemRole.RECTOR = "rector"
     ```
   - Its human-facing display title in the catalog is:
     ```python
     "display_name": "Rector / Director"
     ```
     reflecting Colombian institutional terminology (Ley 115 de 1994, Decreto 1860 de 1994, Decreto 1278 de 2002) where educational institutions (Instituciones Educativas) are led by a **Rector**, and rural/primary educational centers (Centros Educativos) are led by a **Director**.
   - **There is no distinct database role, enum member, or schema entity named `director`.**
2. **Product Owner Decision Precedence:**
   - The Product Owner's binding decisions explicitly restrict the delegation setting:
     > *"Only the authorized Rector for the institution may normally change its delegation setting. `SUPERADMIN` may use the explicitly approved platform override."*
   - Previous implementation code had loosely included `"director"` as a hypothetical role string in sets like `{"rector", "director"}` and `['rector', 'director', 'superadmin']`.
3. **Resolution Applied (Action 6):**
   - In accordance with Action 6 of the mission mandate, the extraneous `"director"` string was completely removed from all backend authorization guards, API endpoints, frontend tab visibility filters, and view-level components.
   - Authorization is now strictly and uniformly enforced for:
     - `rector` (`SystemRole.RECTOR.value`) bound to `current_user.institution_id`.
     - `superadmin` (`SystemRole.SUPERADMIN.value`) for platform infrastructure emergencies.
   - All other roles (`institution_admin`, `coordinator`, `teacher`, `student`, and territorial administrators) receive HTTP 403 `PERMISSION_DENIED`.

---

## 2. Files Inspected and Reconciled

| Layer | File Path | Previous State | Reconciled State | Verification |
| :--- | :--- | :--- | :--- | :---: |
| **Backend API** | `backend/app/api/v1/endpoints/institutions.py` (Line 882) | `is_rector = bool({"rector", "director"} & role_names)` on `GET` | `is_rector = "rector" in role_names` | Restricted to Rector and Superadmin |
| **Backend API** | `backend/app/api/v1/endpoints/institutions.py` (Line 925) | `is_rector = bool({"rector", "director"} & role_names)` on `PATCH` | `is_rector = "rector" in role_names` | Restricted to Rector and Superadmin |
| **Backend Policy** | `backend/app/api/deps.py` (Line 306) | `{"rector", "director", "superadmin", "national_admin"}` | `{"rector", "superadmin", "national_admin"}` | Aligned to canonical roles in `SystemRole` |
| **Frontend Portal**| `frontend/src/pages/academic/AcademicHub.tsx` (Line 67) | `roles: ['rector', 'director', 'superadmin']` | `roles: ['rector', 'superadmin']` | Tab visibility restricted strictly |
| **Frontend View**  | `frontend/src/pages/academic/InstitutionSettingsView.tsx` (Line 31) | `const isRector = hasRole(['rector', 'director', 'superadmin'])` | `const isRector = hasRole(['rector', 'superadmin'])` | Actionable controls restricted strictly |
| **Test Suite**     | `backend/tests/test_nta08_authority_chain.py` (`test_28`) | Only tested coordinator, teacher, student | Added explicit assertions rejecting `institution_admin`, territorial admins, and cross-institution attempts | 100% automated pass |

---

## 3. Strict Authorization Enforcement Policy

### 3.1 Backend Endpoints
- **`GET /api/v1/institutions/{institution_id}/settings/coordinator-delegation`**
  ```python
  role_names = {r.value if isinstance(r, SystemRole) else str(r).lower() for r in auth.roles}
  is_superadmin = "superadmin" in role_names
  is_rector = "rector" in role_names

  if not is_superadmin:
      if is_rector:
          if not current_user.institution_id or current_user.institution_id != institution_id:
              raise AuthorizationError("No está autorizado para consultar la configuración de otra institución educativa.", code="PERMISSION_DENIED")
      else:
          raise AuthorizationError("Solo el Rector de la institución educativa o SuperAdmin puede consultar la configuración de delegación operativa.", code="PERMISSION_DENIED")
  ```
- **`PATCH /api/v1/institutions/{institution_id}/settings/coordinator-delegation`**
  ```python
  role_names = {r.value if isinstance(r, SystemRole) else str(r).lower() for r in auth.roles}
  is_superadmin = "superadmin" in role_names
  is_rector = "rector" in role_names

  if not (is_superadmin or is_rector):
      raise AuthorizationError("Solo el Rector de la institución educativa o SuperAdmin puede modificar la delegación operativa para coordinadores.", code="PERMISSION_DENIED")
  ```

### 3.2 Frontend Access Control
- In `AcademicHub.tsx`, the tab is visible only if the user holds `'rector'` or `'superadmin'`.
- In `InstitutionSettingsView.tsx`, the view requires `'rector'` or `'superadmin'` to display actionable controls; otherwise, controls are hidden and a warning alert is presented.
- Direct API tampering is rejected server-side with HTTP 403 `PERMISSION_DENIED`.

---

## 4. Focused Test Execution & Verifiable Evidence

All 30 automated tests in `test_nta08_authority_chain.py` were executed against the test database:

```
Command: pytest tests/test_nta08_authority_chain.py -v
Platform: Windows (Python 3.14.2, pytest-9.0.2)

tests/test_nta08_authority_chain.py::test_01_superadmin_authority PASSED [  3%]
tests/test_nta08_authority_chain.py::test_02_national_admin_authority PASSED [  6%]
tests/test_nta08_authority_chain.py::test_03_dept_admin_provisions_muni_admin_in_own_department PASSED [ 10%]
tests/test_nta08_authority_chain.py::test_04_dept_admin_invites_rector PASSED [ 13%]
tests/test_nta08_authority_chain.py::test_05_muni_admin_invites_rector PASSED [ 16%]
tests/test_nta08_authority_chain.py::test_06_rector_provisions_coordinator PASSED [ 20%]
tests/test_nta08_authority_chain.py::test_07_rector_provisions_teacher PASSED [ 23%]
tests/test_nta08_authority_chain.py::test_08_rector_provisions_student PASSED [ 26%]
tests/test_nta08_authority_chain.py::test_09_coordinator_provisions_teacher PASSED [ 30%]
tests/test_nta08_authority_chain.py::test_10_coordinator_provisions_student PASSED [ 33%]
tests/test_nta08_authority_chain.py::test_11_guardian_workflow PASSED    [ 36%]
tests/test_nta08_authority_chain.py::test_12_cross_department_rejection PASSED [ 40%]
tests/test_nta08_authority_chain.py::test_13_cross_municipality_rejection PASSED [ 43%]
tests/test_nta08_authority_chain.py::test_14_cross_institution_rejection PASSED [ 46%]
tests/test_nta08_authority_chain.py::test_15_role_escalation_rejection PASSED [ 50%]
tests/test_nta08_authority_chain.py::test_16_scope_tampering_rejection PASSED [ 53%]
tests/test_nta08_authority_chain.py::test_17_rector_succession PASSED    [ 56%]
tests/test_nta08_authority_chain.py::test_18_invitation_replay_rejection PASSED [ 60%]
tests/test_nta08_authority_chain.py::test_19_invitation_expiration PASSED [ 63%]
tests/test_nta08_authority_chain.py::test_20_session_invalidation_after_revocation PASSED [ 66%]
tests/test_nta08_authority_chain.py::test_21_coordinator_cannot_create_coordinator PASSED [ 70%]
tests/test_nta08_authority_chain.py::test_22_coordinator_cannot_create_territorial_admins PASSED [ 73%]
tests/test_nta08_authority_chain.py::test_23_student_cannot_manage_guardians PASSED [ 76%]
tests/test_nta08_authority_chain.py::test_24_cross_institution_guardian_link_rejection PASSED [ 80%]
tests/test_nta08_authority_chain.py::test_25_territorial_admins_cannot_create_institutional_actors PASSED [ 83%]
tests/test_nta08_authority_chain.py::test_26_superadmin_emergency_override_audit_logging PASSED [ 86%]
tests/test_nta08_authority_chain.py::test_27_national_admin_supervisory_rector_intervention PASSED [ 90%]
tests/test_nta08_authority_chain.py::test_28_delegation_setting_lifecycle_and_isolation PASSED [ 93%]
tests/test_nta08_authority_chain.py::test_29_coordinator_management_operations_blocked_when_delegation_disabled PASSED [ 96%]
tests/test_nta08_authority_chain.py::test_30_disabling_delegation_preserves_existing_data PASSED [100%]

======================== 30 passed in 62.88s (0:01:02) ========================
```

### Specific Test Coverage in `test_28`:
- [x] **Rector (own institution):** Reads and modifies setting successfully (HTTP 200).
- [x] **SuperAdmin Platform Override:** Reads and modifies setting successfully (HTTP 200).
- [x] **Cross-Institution Tampering:** Rector cannot read or modify another institution's setting (HTTP 403 `PERMISSION_DENIED`).
- [x] **Coordinator Rejection:** Blocked from both `GET` and `PATCH` (HTTP 403 `PERMISSION_DENIED`).
- [x] **Teacher Rejection:** Blocked from both `GET` and `PATCH` (HTTP 403 `PERMISSION_DENIED`).
- [x] **Student Rejection:** Blocked from both `GET` and `PATCH` (HTTP 403 `PERMISSION_DENIED`).
- [x] **Institution Admin Rejection:** Blocked from both `GET` and `PATCH` (HTTP 403 `PERMISSION_DENIED`).
- [x] **Territorial Admins Rejection:** National, Department, and Municipality Admins blocked from both `GET` and `PATCH` (HTTP 403 `PERMISSION_DENIED`).
- [x] **Audit Trail Verification:** Validated `COORDINATOR_DELEGATION_SETTING_UPDATED` audit log recorded with `outcome="success"`.

---

## 5. Frontend Static Typecheck
```
Command: npm run typecheck (tsc --noEmit)
Exit Code: 0 (Zero errors)
```

---

## 6. Exit Gate

```
================================================================================
                    FINAL CERTIFICATION DECISION: CERTIFICATION PASS
================================================================================
[x] Role taxonomy verified: SystemRole.RECTOR ("rector") is the sole Level 60 canonical role.
[x] "director" was an informal display title alias ("Rector / Director") and not a system role.
[x] Extraneous "director" string removed from backend and frontend authorization guards.
[x] Only authenticated Rector for own institution and Superadmin can access setting.
[x] All unauthorized institutional and territorial roles rejected with HTTP 403.
[x] All 30 tests in authority chain suite passing (100%).
[x] Zero TypeScript errors in frontend.
[x] Zero commits and zero pushes executed.
================================================================================
```
