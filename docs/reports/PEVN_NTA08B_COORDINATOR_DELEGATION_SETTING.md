# PEVN — NTA-08B ADDENDUM: RECTOR-CONTROLLED COORDINATOR DELEGATION
## Implementation and Certification Report
### AI Software Factory Standard v1.2

```
================================================================================
MILESTONE:             NTA-08B ADDENDUM
CLASSIFICATION:        AUTHORIZED IMPLEMENTATION & SECURITY HARDENING
TARGET GATE:           CERTIFICATION PASS
SOURCE REQUIREMENT:    PO ADDENDUM — RECTOR-CONTROLLED COORDINATOR DELEGATION
AUTHORITY MODEL:       INSTITUTION-LEVEL FEATURE FLAG & SHARED BACKEND POLICY
================================================================================
```

---

## 1. Executive Summary

In response to the Product Owner Addendum refining **Option B** for Coordinator operational delegation, the permission for Coordinators to create and manage Teachers, Students, and Guardians has been transitioned from an unconditional institution-wide capability to an **institution-level, Rector-controlled feature flag**.

The setting is formally titled:
> **"Permitir a Coordinadores gestionar Docentes, Estudiantes y Acudientes"**  
> *(Allow Coordinators to manage Teachers, Students, and Guardians)*

### Key Architecture Pillars:
1. **Rector-Controlled Isolation:** The setting is configurable strictly by an authenticated `RECTOR` authorized for their own institution (`current_user.institution_id`) or emergency platform `SUPERADMIN`. Cross-institution modification attempts are rejected with HTTP 403 `PERMISSION_DENIED`.
2. **Secure Default (`false`):** Defaults to `false` (disabled) for all newly provisioned institutions and existing institutions via safe Alembic schema migration `030_institution_coordinator_delegation.py`.
3. **Shared Server-Side Policy Enforcement:** Implemented a unified dependency policy check `assert_coordinator_delegation_allowed()` enforced across all Teacher, Student, and Guardian provisioning, password resetting, account status updates, and family linkage endpoints.
4. **Rector Immunity & Non-Destructive Protection:** Rectors maintain unconditional provisioning capabilities regardless of flag state. Disabling the setting immediately denies subsequent Coordinator management attempts without deleting any user accounts, academic records, or existing guardian relationships.
5. **Auditable Lifecycle:** All updates emit `institution.coordinator_delegation.updated` audit events capturing actor, institution, previous value, new value, timestamp, and client IP without leaking sensitive credentials.
6. **Accessible Directivo UI:** Developed and integrated `InstitutionSettingsView.tsx` within the Rector's `AcademicHub.tsx` (`settings` tab), providing clear security boundaries, persisted state, and reactive feedback.

---

## 2. Authorization and Enforcement Matrix

| Actor Role | Institution Setting State | Operation Attempted | Target Entity | Server Authorization Response | Enforcement Mechanism |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **RECTOR** | Disabled (`False`) | Create / Manage | Teacher, Student, Guardian | **HTTP 200 / 201 (Allowed)** | Rector bypasses delegation check |
| **RECTOR** | Enabled (`True`) | Create / Manage | Teacher, Student, Guardian | **HTTP 200 / 201 (Allowed)** | Rector bypasses delegation check |
| **COORDINATOR** | Disabled (`False`) | Create / Provision / Reset | Teacher | **HTTP 403 Forbidden** (`COORDINATOR_DELEGATION_DISABLED`) | `assert_coordinator_delegation_allowed` |
| **COORDINATOR** | Disabled (`False`) | Create / Provision / Reset | Student | **HTTP 403 Forbidden** (`COORDINATOR_DELEGATION_DISABLED`) | `assert_coordinator_delegation_allowed` |
| **COORDINATOR** | Disabled (`False`) | Create / Provision / Link | Guardian | **HTTP 403 Forbidden** (`COORDINATOR_DELEGATION_DISABLED`) | `assert_coordinator_delegation_allowed` |
| **COORDINATOR** | Enabled (`True`) | Create / Provision / Reset | Teacher (Same Institution) | **HTTP 200 / 201 (Allowed)** | Enforces tenant match & active flag |
| **COORDINATOR** | Enabled (`True`) | Create / Provision / Reset | Student (Same Institution) | **HTTP 200 / 201 (Allowed)** | Enforces tenant match & active flag |
| **COORDINATOR** | Enabled (`True`) | Create / Provision / Link | Guardian (Same Institution) | **HTTP 200 / 201 (Allowed)** | Enforces student institution match |
| **COORDINATOR** | Enabled (`True`) | Create | Rector / Coordinator / Admin | **HTTP 403 Forbidden** | RBAC permission matrix barrier |
| **COORDINATOR** | Any | View / Modify Setting | Institution Flag | **HTTP 403 Forbidden** | `assert_can_manage_coordinator_delegation` |
| **TEACHER** | Any | View / Modify Setting | Institution Flag | **HTTP 403 Forbidden** | Strict Rector / Superadmin policy check |
| **STUDENT** | Any | View / Modify Setting | Institution Flag | **HTTP 403 Forbidden** | Strict Rector / Superadmin policy check |
| **INSTITUTION_ADMIN**| Any | View / Modify Setting | Institution Flag | **HTTP 403 Forbidden** | Non-Rector role restriction |
| **STUDENT** | Any | Create / Link | Guardian | **HTTP 403 Forbidden** | RBAC permission matrix barrier |
| **RECTOR (Inst A)** | Any | Modify Setting Inst B | Institution Flag | **HTTP 403 Forbidden** (`PERMISSION_DENIED`) | Anti-IDOR tenant boundary check |
| **SUPERADMIN** | Any | View / Modify Setting | Institution Flag | **HTTP 200 OK** | Platform emergency override |

---

## 3. Data Model & Migration Specification

### 3.1 Model Changes
- **Model:** `backend/app/models/institution.py` -> `Institution`
- **Field:** `coordinator_delegation_enabled: Mapped[bool]`
- **Column Definition:** `Boolean, default=False, server_default=text("false"), nullable=False`
- **Safe Persistence:** Value is stored directly in the `institutions` table, ensuring sub-millisecond query performance on auth checks without join overhead.

### 3.2 Schema Contracts
- **`InstitutionResponse`** (`backend/app/schemas/institution.py`):
  ```python
  coordinator_delegation_enabled: bool = False
  ```
- **`CoordinatorDelegationSettingUpdateRequest`**:
  ```python
  class CoordinatorDelegationSettingUpdateRequest(BaseModel):
      coordinator_delegation_enabled: bool = Field(..., description="Enable or disable operational delegation for institutional coordinators")
  ```
- **`CoordinatorDelegationSettingResponse`**:
  ```python
  class CoordinatorDelegationSettingResponse(BaseModel):
      institution_id: uuid.UUID
      coordinator_delegation_enabled: bool
      updated_at: datetime
  ```

### 3.3 Database Migration
- **File:** `backend/migrations/versions/030_institution_coordinator_delegation.py`
- **Revision ID:** `030` (Child of `029`)
- **Forward Migration:**
  ```python
  def upgrade() -> None:
      op.add_column(
          "institutions",
          sa.Column(
              "coordinator_delegation_enabled",
              sa.Boolean(),
              server_default=sa.text("false"),
              nullable=False,
          ),
      )
  ```
- **Rollback Migration:**
  ```python
  def downgrade() -> None:
      op.drop_column("institutions", "coordinator_delegation_enabled")
  ```

---

## 4. Server-Side Policy Implementation

### 4.1 Shared Enforcement Dependency (`backend/app/api/deps.py`)
```python
async def assert_coordinator_delegation_allowed(
    db: AsyncSession,
    auth: AuthContext,
    institution_id: uuid.UUID | None,
) -> None:
    """
    NTA-08B Addendum — Shared policy enforcement for Coordinator operational delegation.
    Verifies:
      1. If actor is Rector (or Superadmin / National Admin): ALWAYS PERMITTED.
      2. If actor is Coordinator / Academic Coordinator:
         - Target institution_id must match auth.institution_id (Tenant isolation).
         - Institution.coordinator_delegation_enabled MUST be True.
         - If False, raises HTTPException(403, error_code="COORDINATOR_DELEGATION_DISABLED").
    """
```

### 4.2 Protected Endpoints
The shared dependency is strictly called across all mutation entry points:
1. `backend/app/api/v1/endpoints/teachers.py`:
   - `POST /api/v1/teachers` (`create_teacher`)
   - `POST /api/v1/teachers/provision` (`provision_teacher_account`)
   - `PATCH /api/v1/teachers/{id}/status` (`update_teacher_account_status`)
   - `POST /api/v1/teachers/{id}/reset-password` (`reset_teacher_password`)
2. `backend/app/api/v1/endpoints/students.py`:
   - `POST /api/v1/students` (`create_student`)
   - `POST /api/v1/students/provision` (`provision_student_account`)
   - `PATCH /api/v1/students/{id}/status` (`update_student_account_status`)
   - `POST /api/v1/students/{id}/reset-password` (`reset_student_password`)
   - `POST /api/v1/students/{id}/guardians` (`associate_guardian_to_student_from_student`)
   - `DELETE /api/v1/students/{id}/guardians/{guardian_id}` (`dissociate_guardian_from_student_from_student`)
3. `backend/app/api/v1/endpoints/guardians.py`:
   - `POST /api/v1/guardians` (`create_guardian`)
   - `POST /api/v1/guardians/provision` (`provision_guardian_account`)
   - `PATCH /api/v1/guardians/{id}/status` (`update_guardian_account_status`)
   - `POST /api/v1/guardians/{id}/reset-password` (`reset_guardian_password`)
   - `POST /api/v1/guardians/{id}/students/{student_id}` (`associate_guardian_to_student`)
   - `DELETE /api/v1/guardians/{id}/students/{student_id}` (`dissociate_guardian_from_student`)

### 4.3 Rector Settings API (`backend/app/api/v1/endpoints/institutions.py`)
- `GET /api/v1/institutions/{institution_id}/settings/coordinator-delegation`
- `PATCH /api/v1/institutions/{institution_id}/settings/coordinator-delegation`
  - Validates `assert_can_manage_coordinator_delegation(auth, institution_id)`:
    - Binds authorization to `auth.institution_id == institution_id` for Rectors.
    - Permits `SUPERADMIN` platform override.
    - Rejects any other role or cross-institution tampering with HTTP 403 `PERMISSION_DENIED`.

---

## 5. Audit Logging Architecture

Setting mutations are recorded via `institution_service.update_coordinator_delegation_setting`:
- **Event Type:** `AuditEventType.COORDINATOR_DELEGATION_SETTING_UPDATED` (`"institution.coordinator_delegation.updated"`)
- **Action:** `"update_coordinator_delegation_setting"`
- **Target ID:** `institution.id`
- **Institution ID:** `institution.id`
- **Actor ID:** `actor.user_id`
- **Metadata Payload:**
  ```json
  {
    "previous_value": false,
    "new_value": true,
    "institution_name": "Colegio Distrital Barranquilla",
    "updated_by": "0f63b2a1-..."
  }
  ```
- **Security Check:** Zero credentials, passwords, or tokens logged.

---

## 6. Rector User Interface Integration

### 6.1 View Component (`frontend/src/pages/academic/InstitutionSettingsView.tsx`)
- Displays persisted state with responsive status badge:
  - `HABILITADA` (`Badge variant="success"`)
  - `INHABILITADA` (`Badge variant="neutral"`)
- Explains institutional security boundaries and invariants:
  - Multi-tenant boundary isolation.
  - Prohibition of Coordinator privilege escalation.
  - Non-destructive revocation protection.
  - Unconditional Rector governance.
- Interactive toggle button:
  - "Habilitar Facultades a Coordinadores" (`Button variant="primary"`)
  - "Inhabilitar Facultades a Coordinadores" (`Button variant="danger"`)
- Disables controls and displays explanatory warning if viewed by non-rector directivos.

### 6.2 Portal Integration (`frontend/src/pages/academic/AcademicHub.tsx`)
- Registered as tab:
  ```typescript
  { id: 'settings', label: 'Configuración Institucional', icon: '⚙️', permission: 'coordinators:create' }
  ```
- Rendered via `case 'settings': return <InstitutionSettingsView />`.
- Visibility restricted by existing RBAC permission `coordinators:create` (held only by `rector`, `superadmin`, and `institution_admin`).

---

## 7. Verifiable Regression Evidence

All 30 automated tests in `test_nta08_authority_chain.py` plus all related territorial and rector succession suites were executed against the test database.

### 7.1 Authority Chain & Delegation Test Suite Execution
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

======================== 30 passed in 67.21s (0:01:07) ========================
```

### 7.2 Territorial Municipality Admin RBAC Suite Execution
```
Command: pytest tests/test_municipality_admin_rbac.py -v
============================== 2 passed in 2.48s ==============================
```

### 7.3 Rector Succession & Revocation Suite Execution
```
Command: pytest tests/test_rector_succession.py -v
======================= 10 passed, 2 warnings in 35.06s =======================
```

### 7.4 Frontend TypeScript Verification
```
Command: npm run typecheck (tsc --noEmit)
Exit Code: 0 (Zero errors)
```

---

## 8. Rollback Considerations and Operational Continuity

1. **Rollback Safety:** If schema migration 030 is rolled back (`alembic downgrade -1`), the column `coordinator_delegation_enabled` is dropped safely. In that scenario, the backend fallback defaults to `assert_coordinator_delegation_allowed` checking `getattr(inst, "coordinator_delegation_enabled", False)` ensuring graceful fail-closed behavior.
2. **Data Preservation:** Revoking delegation never deletes teacher assignments, student SIMAT registrations, grades, evaluations, or guardian parentage records.
3. **Account Integrity:** Disabling the setting does not revoke, lock, or deactivate Coordinator accounts. Coordinators retain full read-only visibility into academic rosters, classrooms, and schedules.

---

## 9. Final Certification Gate

```
================================================================================
                    FINAL CERTIFICATION DECISION: CERTIFICATION PASS
================================================================================
[x] Institution-level feature flag configurable only by Rector/Superadmin.
[x] Safe migration with secure default 'false' across existing and new institutions.
[x] Strict multi-tenant isolation and anti-IDOR validation.
[x] Server-side policy check (assert_coordinator_delegation_allowed) across all ops.
[x] Unconditional Rector provisioning capabilities preserved.
[x] Coordinators blocked from provisioning higher roles or cross-tenant users.
[x] Non-destructive revocation verified through automated tests.
[x] Setting changes recorded in AuditLog with actor and previous/new values.
[x] Responsive directivo UI component integrated in AcademicHub.
[x] Frontend TypeScript type-check passed with 0 errors.
[x] 100% automated regression tests passing (30/30 in authority chain, 42/42 total).
================================================================================
```
