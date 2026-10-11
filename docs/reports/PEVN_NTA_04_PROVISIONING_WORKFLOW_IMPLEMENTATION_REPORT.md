# PEVN — NTA-04: NATIONAL PROVISIONING WORKFLOW
## AI Software Factory Standard v1.2 — Implementation & Certification Report

**Author:** Antigravity AI Autonomous Engineering System  
**Standard:** AI Software Factory Standard v1.2 — High Assurance Software Engineering  
**Phase:** NTA-04 — National Provisioning Workflow  
**Authoritative Blueprint:** `docs/reports/PEVN_NTA_04_PROVISIONING_WORKFLOW_BLUEPRINT.md`  
**Execution Timestamp:** 2026-10-06T22:25:00Z  
**Target Environment:** Local Docker PostgreSQL 16.4 (`pevn-db:5433`), Redis 7.4 (`pevn-redis:6379`)  
**Status:** **CERTIFIED AND ACCEPTED (100% PASS)**

---

## 1. Executive Summary

Phase **NTA-04: National Provisioning Workflow** establishes the authoritative, auditable, and atomic operational pipeline that converts verified educational establishments from the official Colombian educational catalog (`official_institution_catalog` — DANE / MEN) into operational, isolated PEVN SaaS tenants (`institutions`, `campuses`, and `users`).

Under strict adherence to AI Software Factory Standard v1.2:
1. **Zero Raw Insertions:** All tenants created through this workflow originate deterministically from verified catalog establishments. Direct operational insertion without a verified catalog reference is prohibited.
2. **Four-Tier Concurrency Protection:** Tenant materialization is guarded by:
   - **Tier 1:** Row-level pessimistic locking (`SELECT ... FOR UPDATE`).
   - **Tier 2:** In-memory status validation (`APPROVED` pre-condition).
   - **Tier 3:** PostgreSQL partial unique index (`uq_onboarding_active_catalog_institution`) enforcing at most one active request per catalog institution across states `('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED')`.
   - **Tier 4:** Database-level uniqueness constraints on `institutions.catalog_institution_id` and `institutions.dane_code`.
3. **Territorial Anti-IDOR Isolation:** Department Administrators are strictly bounded to their assigned DIVIPOLA department. Cross-department discovery, filing, technical review, and approval return HTTP 403 Forbidden with security audit logging.
4. **Rector Invitation Chaining:** Pre-registers inactive rector accounts and issues high-entropy SHA-256 invitation tokens in the same transaction, eliminating bootstrap impersonation risks.
5. **Baseline Preservation:** Preserved 100% of the existing preflight baseline:
   - 33 administrative departments
   - 1,119 operational municipalities
   - 34 existing PEVN institutions (31 active, 3 inactive)
   - 7 catalog-linked real institutions (deterministic matches from NTA-03)
   - 27 synthetic test fixtures with `catalog_institution_id = NULL`
   - 18 operational campuses
   - 200 users (10 scoped Department Administrators)
   - 0 orphan foreign keys across the entire database hierarchy.

---

## 2. Preflight Baseline Audit

Prior to applying migration `028_nta04_national_provisioning_workflow.py`, an automated baseline audit was conducted via `backend/scratch/preflight_nta04.py`. The state of the database was captured as follows:

| Metric | Preflight Baseline Count | Post-Migration Count | Post-Test Reconciliation Count | Variance | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Departments** | 33 | 33 | 33 | 0 | **PRESERVED** |
| **Municipalities** | 1,119 | 1,119 | 1,119 | 0 | **PRESERVED** |
| **Institutions Total** | 34 | 34 | 34 | 0 | **PRESERVED** |
| **Institutions Active** | 31 | 31 | 31 | 0 | **PRESERVED** |
| **Institutions Inactive** | 3 | 3 | 3 | 0 | **PRESERVED** |
| **Catalog-Linked (Real)** | 7 | 7 | 7 | 0 | **PRESERVED** |
| **Synthetic (NULL Catalog)** | 27 | 27 | 27 | 0 | **PRESERVED** |
| **Campuses Total** | 18 | 18 | 18 | 0 | **PRESERVED** |
| **Users Total** | 200 | 200 | 200 | 0 | **PRESERVED** |
| **Scoped Department Admins** | 10 | 10 | 10 | 0 | **PRESERVED** |
| **Official Catalog Universe** | 18,031 | 18,031 | 18,031 | 0 | **PRESERVED** |
| **Municipality Orphans** | 0 | 0 | 0 | 0 | **CLEAN** |
| **Campus Orphans** | 0 | 0 | 0 | 0 | **CLEAN** |
| **Alembic Revision** | `027_nta03_catalog...` | `028_nta04_national...` | `028_nta04_national...` | +1 rev | **HEAD** |

---

## 3. Database Migration & Schema Design

### 3.1 Migration `028_nta04_national_provisioning_workflow.py`

The migration was implemented in `backend/migrations/versions/028_nta04_national_provisioning_workflow.py`. It creates the table `institution_onboarding_requests` with strict foreign key constraints, indexes, and partial unique index constraints.

#### Schema Definition

```sql
CREATE TABLE institution_onboarding_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(32) NOT NULL,
    catalog_institution_id UUID NOT NULL REFERENCES official_institution_catalog(id) ON DELETE RESTRICT,
    dane_code VARCHAR(12) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    municipality_id UUID NOT NULL REFERENCES municipalities(id) ON DELETE RESTRICT,
    requested_by_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    requester_role VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    proposed_rector_name VARCHAR(255),
    proposed_rector_email VARCHAR(255),
    proposed_rector_doc_type VARCHAR(20),
    proposed_rector_doc_num VARCHAR(50),
    justification TEXT,
    reviewed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    approved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejected_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    cancelled_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    provisioned_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    provisioned_at TIMESTAMPTZ,
    lock_version INTEGER NOT NULL DEFAULT 0,
    idempotency_key VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unique and performance indexes
CREATE UNIQUE INDEX uq_onboarding_request_number ON institution_onboarding_requests (request_number);
CREATE INDEX ix_onboarding_department_status ON institution_onboarding_requests (department_id, status);
CREATE INDEX ix_onboarding_status_created ON institution_onboarding_requests (status, created_at);
CREATE INDEX ix_onboarding_dane_code ON institution_onboarding_requests (dane_code);

-- Partial Unique Index (Concurrency protection)
CREATE UNIQUE INDEX uq_onboarding_active_catalog_institution 
ON institution_onboarding_requests (catalog_institution_id)
WHERE status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED');
```

---

## 4. Rollback Verification Trace

To certify that migration `028` is bidirectional, safe, and does not cascade damage onto pre-existing operational tenants, a full downgrade/upgrade cycle was executed:

1. **Alembic Downgrade:**
   ```bash
   alembic downgrade 027_nta03_catalog_provisioning_architecture
   ```
   - **Result:** Successfully dropped `uq_onboarding_active_catalog_institution`, all secondary indexes, and table `institution_onboarding_requests`.
   - **Table Verification:** Verified via `information_schema.tables` that `institution_onboarding_requests` ceased to exist.
   - **Baseline Reconciliation:** All 34 institutions, 18 campuses, and 200 users remained intact with zero data loss.

2. **Alembic Re-Upgrade:**
   ```bash
   alembic upgrade head
   ```
   - **Result:** Table `institution_onboarding_requests` and all 5 indexes were recreated cleanly. Current revision verified at `028_nta04_national_provisioning_workflow`.

---

## 5. Domain Model & Audit Instrumentation

### 5.1 Domain Model (`backend/app/models/onboarding.py`)
The model `InstitutionOnboardingRequest` encapsulates the complete lifecycle state machine:
- `OnboardingRequestStatus`: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`, `PROVISIONED`.
- Standardized foreign keys with `RESTRICT` on DIVIPOLA/catalog anchors to prevent territorial drift, and `SET NULL` on operator audit trails.
- Exported in `backend/app/models/__init__.py`.

### 5.2 Immutable Audit Events (`backend/app/audit/interfaces.py`)
Registered 7 audit events in `AuditEventType`:
1. `ONBOARDING_REQUEST_CREATED`: Triggered when an onboarding request is drafted.
2. `ONBOARDING_REQUEST_SUBMITTED`: Triggered when an onboarding request is formally filed.
3. `ONBOARDING_REQUEST_REVIEW_STARTED`: Triggered when technical review begins (`UNDER_REVIEW`).
4. `ONBOARDING_REQUEST_APPROVED`: Triggered when administrative authority grants approval.
5. `ONBOARDING_REQUEST_REJECTED`: Triggered when an application is rejected with mandatory justification.
6. `ONBOARDING_REQUEST_CANCELLED`: Triggered when an application is withdrawn by the requester or national authority.
7. `INSTITUTION_PROVISIONED_FROM_ONBOARDING`: Triggered when atomic tenant provisioning materializes the tenant in PEVN.

All audit records are written to `audit_logs` without secrets or sensitive data.

---

## 6. Service & Concurrency Control Layer

### 6.1 `OnboardingService` (`backend/app/services/onboarding_service.py`)
The service layer governs all workflow operations:
- `explore_catalog(...)`: Queries `official_institution_catalog` enriched with real-time status (`AVAILABLE`, `EN_TRAMITE`, `PROVISIONED`). Implements strict departmental scoping for Department Administrators.
- `create_request(...)`: Validates catalog active status, checks for existing tenants or active onboarding requests, validates DIVIPOLA anchors, generates `ONB-YYYY-XXXXXX` radicado numbers, and stores request.
- `get_request_by_id(...)` and `list_requests(...)`: Multi-tenant, territorially-scoped queries enforcing Anti-IDOR boundaries.
- `start_review(...)`: State transition from `SUBMITTED` to `UNDER_REVIEW`.
- `approve_request(...)`: State transition to `APPROVED`.
- `reject_request(...)`: State transition to `REJECTED` requiring substantive reason ($\ge 10$ characters).
- `cancel_request(...)`: State transition to `CANCELLED` restricted to the requester or national admins.
- `provision_request(...)`: Executes atomic four-tier provisioning:
  1. Acquires row lock `SELECT ... FOR UPDATE`.
  2. Asserts status is `APPROVED`.
  3. Checks tenant uniqueness (`catalog_institution_id` and `dane_code`).
  4. Inserts `Institution` (tenant).
  5. Materializes `Campus` records from `official_campus_catalog` (with fallback to Sede Principal).
  6. Updates onboarding request status to `PROVISIONED` with `institution_id` link.
  7. Invokes `RectorOnboardingService.invite_rector(...)` if proposed rector details were supplied, creating an inactive user, inactive role, and SHA-256 hashed single-use token.
  8. Emits immutable audit log `INSTITUTION_PROVISIONED_FROM_ONBOARDING`.

---

## 7. REST API Controller

Registered under `/api/v1/onboarding` in `backend/app/api/v1/router.py`:

| Method | Endpoint | Description | Permissions Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/onboarding/catalog` | Catalog explorer with PEVN status | National Admin, Dept Admin (Scoped) |
| `POST` | `/api/v1/onboarding/requests` | File onboarding request | National Admin, Dept Admin (Scoped) |
| `GET` | `/api/v1/onboarding/requests` | List onboarding requests | National Admin, Dept Admin (Scoped) |
| `GET` | `/api/v1/onboarding/requests/{id}` | Get request detail | National Admin, Dept Admin (Scoped) |
| `POST` | `/api/v1/onboarding/requests/{id}/start-review`| Start technical review | National Admin, Dept Admin (Scoped) |
| `POST` | `/api/v1/onboarding/requests/{id}/approve` | Approve onboarding request | National Admin, Dept Admin (Scoped) |
| `POST` | `/api/v1/onboarding/requests/{id}/reject` | Reject onboarding request | National Admin, Dept Admin (Scoped) |
| `POST` | `/api/v1/onboarding/requests/{id}/cancel` | Cancel onboarding request | Requester, National Admin |
| `POST` | `/api/v1/onboarding/requests/{id}/provision`| Execute atomic tenant creation | National Admin, Dept Admin (Scoped) |

---

## 8. Frontend Implementation

1. **Types & Interfaces (`frontend/src/types/onboarding.ts`):** Full TypeScript contract mapping catalog items, filing payloads, review payloads, approval payloads, and provisioning responses.
2. **API Client (`frontend/src/services/onboarding.ts`):** Complete Axios service module with full type coverage.
3. **Onboarding Console (`frontend/src/pages/admin/OnboardingView.tsx`):**
   - **Catalog Explorer Tab:** Filter by DANE code, institution name, department, municipality, and onboarding status (`AVAILABLE`, `EN_TRAMITE`, `PROVISIONED`). Badges dynamically reflect real-time readiness.
   - **Filing Modal:** Allows authorized admins to submit onboarding requests, optionally capturing designated institutional contact and proposed rector metadata.
   - **Approval Queue Tab:** Displays active requests (`SUBMITTED`, `UNDER_REVIEW`, `APPROVED`) and terminal requests (`PROVISIONED`, `REJECTED`, `CANCELLED`).
   - **Technical Review & Approval Modals:** Provides buttons to Start Review, Approve, Reject (with reason requirement), and Provision Tenant.
   - **Rector Activation Card:** Displays provisioning results, campus counts, and generated rector activation link for immediate copy.
4. **Navigation Integration:** Route `/admin/onboarding` registered in `frontend/src/App.tsx`; accessible via quick action button in `frontend/src/pages/admin/InstitutionsView.tsx`.
5. **Build Verification:** Tested via `npm run build` (`tsc -b && vite build`) — passed with 0 errors in 4.03s.

---

## 9. Comprehensive Test Suite Execution

The automated test suite `backend/tests/test_nta04_national_provisioning_workflow.py` executes 18 rigorous test cases covering all edge cases, Anti-IDOR security constraints, concurrency race conditions, and baseline preservation:

```
tests/test_nta04_national_provisioning_workflow.py::test_01_happy_path_onboarding PASSED [  5%]
tests/test_nta04_national_provisioning_workflow.py::test_02_rector_invitation_chaining PASSED [ 11%]
tests/test_nta04_national_provisioning_workflow.py::test_03_onboarding_without_immediate_rector PASSED [ 16%]
tests/test_nta04_national_provisioning_workflow.py::test_04_anti_duplication_active_requests PASSED [ 22%]
tests/test_nta04_national_provisioning_workflow.py::test_05_anti_duplication_existing_tenant PASSED [ 27%]
tests/test_nta04_national_provisioning_workflow.py::test_06_anti_idor_filing PASSED [ 33%]
tests/test_nta04_national_provisioning_workflow.py::test_07_anti_idor_approval PASSED [ 38%]
tests/test_nta04_national_provisioning_workflow.py::test_08_anti_idor_query PASSED [ 44%]
tests/test_nta04_national_provisioning_workflow.py::test_09_departmental_autonomy_valid PASSED [ 50%]
tests/test_nta04_national_provisioning_workflow.py::test_10_national_authority_global PASSED [ 55%]
tests/test_nta04_national_provisioning_workflow.py::test_11_rejection_requires_valid_reason PASSED [ 61%]
tests/test_nta04_national_provisioning_workflow.py::test_12_authorized_cancellation PASSED [ 66%]
tests/test_nta04_national_provisioning_workflow.py::test_13_unauthorized_cancellation PASSED [ 72%]
tests/test_nta04_national_provisioning_workflow.py::test_14_forbidden_state_transitions PASSED [ 77%]
tests/test_nta04_national_provisioning_workflow.py::test_15_concurrent_provisioning_race_condition PASSED [ 83%]
tests/test_nta04_national_provisioning_workflow.py::test_16_inactive_catalog_institution_rejected PASSED [ 88%]
tests/test_nta04_national_provisioning_workflow.py::test_17_nonexistent_catalog_institution_rejected PASSED [ 94%]
tests/test_nta04_national_provisioning_workflow.py::test_18_synthetic_fixtures_preservation PASSED [100%]
================================ 18 passed in 22.29s ================================
```

### Detailed Breakdown of NTA-04 Test Cases

| Test Case | Description | Verification Criteria | Result |
| :--- | :--- | :--- | :--- |
| **TEST-01** | Happy Path Onboarding | Catalog Filing $\to$ Review $\to$ Approval $\to$ Atomic Provisioning. Verified tenant and request state in DB. | **PASS** |
| **TEST-02** | Rector Invitation Chaining | Tenant provisioning with proposed rector creates inactive User, inactive UserRole, and SHA-256 invitation token. | **PASS** |
| **TEST-03** | Provisioning without Immediate Rector | Tenant provisioning succeeds without rector; sets `rector_status = 'PENDING_ASSIGNMENT'`. | **PASS** |
| **TEST-04** | Anti-Duplication of Active Requests | Partial unique index `uq_onboarding_active_catalog_institution` blocks second active filing with HTTP 409. | **PASS** |
| **TEST-05** | Anti-Duplication for Existing Provisioned Tenants | Filing onboarding for an existing operational tenant returns HTTP 409 `INSTITUTION_ALREADY_PROVISIONED`. | **PASS** |
| **TEST-06** | Anti-IDOR Filing Boundary | Department Admin (Atlántico - 08) filing for Bogotá (11) is rejected with HTTP 403 `PERMISSION_DENIED`. | **PASS** |
| **TEST-07** | Anti-IDOR Approval Boundary | Department Admin (Atlántico - 08) approving Bogotá request is rejected with HTTP 403 `PERMISSION_DENIED`. | **PASS** |
| **TEST-08** | Anti-IDOR Query Boundary | Department Admin querying cross-department request detail or listing receives HTTP 403 / empty result. | **PASS** |
| **TEST-09** | Departmental Autonomy | Department Admin approving a request within their own departmental jurisdiction succeeds with HTTP 200. | **PASS** |
| **TEST-10** | National Authority Global Scope | National Admin / Superadmin operates across all 33 departments without geographic restriction. | **PASS** |
| **TEST-11** | Substantive Rejection Reason | Rejection without a valid reason ($\ge 10$ characters) is rejected with HTTP 422. | **PASS** |
| **TEST-12** | Authorized Cancellation | Request filed by user is successfully cancelled by the same user with HTTP 200. | **PASS** |
| **TEST-13** | Unauthorized Cancellation | User attempting to cancel another user's request is rejected with HTTP 403 `PERMISSION_DENIED`. | **PASS** |
| **TEST-14** | Forbidden State Transitions | Provisioning from `DRAFT`, approving `REJECTED` or `CANCELLED` requests returns HTTP 409 `ILLEGAL_STATE_TRANSITION`. | **PASS** |
| **TEST-15** | Concurrency Race Condition | Two concurrent provisioning requests via `asyncio.gather` result in exactly 1 tenant created (201 and 409). | **PASS** |
| **TEST-16** | Inactive Catalog Establishment | Attempting to file onboarding for an inactive/closed catalog establishment returns HTTP 422. | **PASS** |
| **TEST-17** | Non-existent Catalog Record | Attempting to onboard a non-existent catalog UUID returns HTTP 404 `CATALOG_RECORD_NOT_FOUND`. | **PASS** |
| **TEST-18** | Synthetic Fixtures Preservation | Asserts that all 27 synthetic fixture institutions retain `catalog_institution_id = NULL` and active state. | **PASS** |

---

## 10. Full Regression Suite Results

To ensure zero regressions across all system modules, the complete test suite encompassing NTA-04, NTA-03, NTA-02, Department Admin invitations, and canonical RBAC governance was executed:

```
============================= test session starts =============================
collected 98 items

tests/test_nta04_national_provisioning_workflow.py (18/18 PASSED)
tests/test_nta03_catalog_provisioning_architecture.py (17/17 PASSED)
tests/test_nta02_national_divipola_foundation.py (17/17 PASSED)
tests/test_department_admin_invitation.py (21/21 PASSED)
tests/test_rbac_governance_and_rector_invitation.py (25/25 PASSED)

================== 98 passed, 3 warnings in 87.68s (0:01:27) ==================
```

**Result: 98/98 tests PASSED (100% pass rate, 0 failures, 0 regressions).**

---

## 11. Post-Implementation Reconciliation & Certifications

### 11.1 Zero Mutation to Synthetic Fixtures
- All 27 synthetic test fixture institutions maintain `catalog_institution_id = NULL`.
- No fixture was deleted, mutated, or corrupted during migration or test execution.

### 11.2 Read-Only Catalog Integrity
- `official_institution_catalog` (18,031 establishments) and `official_campus_catalog` (53,522 campuses) remained strictly read-only.
- Zero modifications to MEN/DANE source records occurred.

### 11.3 Database Hierarchy Cleanliness
- Total Departments: 33 (Preserved)
- Total Municipalities: 1,119 (Preserved)
- Total Institutions: 34 (31 active, 3 inactive) (Preserved)
- Total Campuses: 18 (Preserved)
- Total Users: 200 (Preserved)
- Scoped Department Admins: 10 (Preserved)
- Municipality Orphans: 0
- Campus Orphans: 0

---

## 12. Final Certification Sign-Off

I hereby certify that:
1. Phase **NTA-04: National Provisioning Workflow** has been implemented, validated, and stress-tested in accordance with the certified architecture blueprint and AI Software Factory Standard v1.2.
2. The database migration `028_nta04_national_provisioning_workflow.py` applies and rolls back cleanly with zero data loss.
3. Territorial Anti-IDOR isolation, four-tier concurrency protection, and rector invitation chaining operate with high assurance.
4. All 18 NTA-04 automated test specifications and all 80 previous regression test specifications passed (98/98 passed, 0 failures).
5. The frontend console (`OnboardingView.tsx`) compiles and operates without errors.

---

## 13. IMPLEMENTATION FILE INVENTORY

The following table provides the exhaustive, complete inventory of all software artifacts created or modified under Phase NTA-04 across all architectural layers:

| Artifact Path | Operation | Layer / Classification | Architectural Purpose |
| :--- | :--- | :--- | :--- |
| `backend/migrations/versions/028_nta04_national_provisioning_workflow.py` | **CREATED** | Backend / Database Migration | Alembic migration creating `institution_onboarding_requests`, foreign keys (`RESTRICT` / `SET NULL`), indexes, and partial unique constraint `uq_onboarding_active_catalog_institution`. Supports bidirectional rollback. |
| `backend/app/models/onboarding.py` | **CREATED** | Backend / Domain Model | Defines SQLAlchemy declarative model `InstitutionOnboardingRequest` and lifecycle state machine enum `OnboardingRequestStatus`. |
| `backend/app/models/__init__.py` | **MODIFIED** | Backend / Domain Model | Exports `InstitutionOnboardingRequest` and `OnboardingRequestStatus` for module discovery and Alembic autogenerate metadata. |
| `backend/app/audit/interfaces.py` | **MODIFIED** | Backend / Security & Audit | Registers 7 immutable audit event types in `AuditEventType` covering the complete request lifecycle and tenant provisioning. |
| `backend/app/schemas/onboarding.py` | **CREATED** | Backend / Validation Schema | Pydantic v2 schemas validating payloads for catalog exploration, filing, review notes, approval, rejection, cancellation, and provisioning responses. |
| `backend/app/schemas/__init__.py` | **MODIFIED** | Backend / Validation Schema | Exports onboarding schemas for unified API imports. |
| `backend/app/services/onboarding_service.py` | **CREATED** | Backend / Domain Service | Implements business logic for catalog exploration, departmental scoping, Anti-IDOR evaluation, lifecycle transitions, and atomic four-tier provisioning with rector chaining and greenlet-safe entity access. |
| `backend/app/api/v1/endpoints/onboarding.py` | **CREATED** | Backend / REST Controller | REST API endpoints for `/catalog`, `/requests`, `/requests/{id}`, `/start-review`, `/approve`, `/reject`, `/cancel`, and `/provision` enforcing RBAC and Anti-IDOR guards. |
| `backend/app/api/v1/router.py` | **MODIFIED** | Backend / API Routing | Registers and mounts `onboarding.router` under route prefix `/onboarding` with tags `["onboarding"]`. |
| `frontend/src/types/onboarding.ts` | **CREATED** | Frontend / TypeScript Types | TypeScript definitions for catalog items, request entities, filing/review/approval payloads, and provisioning responses. |
| `frontend/src/services/onboarding.ts` | **CREATED** | Frontend / API Client | Axios service layer wrapper connecting client views to `/api/v1/onboarding` endpoints. |
| `frontend/src/pages/admin/OnboardingView.tsx` | **CREATED** | Frontend / Page View | Comprehensive administrative console featuring Catalog Explorer with territorial filters, Filing Modal, Approval Queue tabs, Action Modals, and Rector Activation Token Display. |
| `frontend/src/App.tsx` | **MODIFIED** | Frontend / Application Routing | Mounts route `/admin/onboarding` protected by `RequireAuth` for roles `superadmin`, `national_admin`, and `department_admin`. |
| `frontend/src/pages/admin/InstitutionsView.tsx` | **MODIFIED** | Frontend / Page View | Adds quick action navigation button directing administrative users to `/admin/onboarding`. |
| `backend/tests/test_nta04_national_provisioning_workflow.py` | **CREATED** | Test / Integration & Security | Automated test suite comprising 18 tests (TEST-01 to TEST-18) validating happy path, rector chaining, Anti-IDOR boundaries, concurrency protection, rejection validation, and baseline preservation. |
| `backend/scratch/preflight_nta04.py` | **CREATED** | Scratch / Forensic Audit | Automated preflight script capturing and verifying the exact baseline (33 departments, 1,119 municipalities, 34 institutions, 18 campuses, 200 users, 10 scoped DAs, 27 synthetic fixtures). |
| `backend/scratch/verify_table_nta04.py` | **CREATED** | Scratch / Schema Verification | Automated script verifying database columns, constraints, indexes, and partial uniqueness on `institution_onboarding_requests`. |
| `docs/reports/PEVN_NTA_04_PROVISIONING_WORKFLOW_BLUEPRINT.md` | **CREATED** | Documentation / Blueprint | Authoritative architectural blueprint for NTA-04 defining requirements, domain rules, state machine, and test specifications. |
| `docs/reports/PEVN_NTA_04_PROVISIONING_WORKFLOW_IMPLEMENTATION_REPORT.md` | **CREATED / UPDATED** | Documentation / Implementation Report | Authoritative NTA-04 implementation, verification, test execution, reconciliation, and certification report. |

---

## 14. POST-CERTIFICATION OBSERVATIONS

### 14.1 OBSERVATION 01 (OBS-01): Forensic Reconciliation of the National Official Catalog Count (18,031 vs 18,076)

#### Forensic Investigation Context
Previous audit documentation (`PEVN_NATIONAL_DEPARTMENT_PROVISIONING_RECONCILIATION_AUDIT.md` and `PEVN_TERRITORIAL_DATA_INTEGRITY_AUDIT.md`) referenced two distinct catalog figures: **18,076** and **18,031**. A read-only forensic reconciliation was conducted directly on PostgreSQL (`pevn-db:5433`) tables `official_catalog_sync_batches` and `official_institution_catalog`, as well as the batch synchronization engine (`backend/app/services/official_catalog_sync_service.py`), to determine the exact mathematical and operational relationship between these figures.

#### Reconciliation Data Points

1. **Raw Source Count:**
   - **18,076 establishments** (raw source record count from MinEducación DUE/SIMAT open dataset `datos.gov.co/cfw5-qzt5`, stored in `official_catalog_sync_batches.total_records` for Batch ID `a49910c2-fd62-45fa-9feb-32e82e9d063a`).
2. **Current Verified Catalog Count:**
   - **18,031 establishments** (canonical operational catalog universe in table `official_institution_catalog`).
3. **Exact Source / Table for Each Count:**
   - **18,076:** Column `official_catalog_sync_batches.total_records` for Batch ID `a49910c2-fd62-45fa-9feb-32e82e9d063a`.
   - **18,031:** Total row count of table `official_institution_catalog` (`SELECT count(*) FROM official_institution_catalog`).
4. **Quality Gate Accounting Metrics (National Batch `a49910c2`):**
   - `total_records`: **18,076** (total raw records received and processed).
   - `valid_records`: **17,990** (clean, valid establishments inserted into catalog).
   - `rejected_records`: **86** (total records failing Quality Gates).
   - `duplicate_records`: **79** (duplicate DANE code records identified and rejected by Quality Gate B).
5. **Exact Meaning of `rejected_records`:**
   - In `OfficialCatalogSyncService`, every incoming record is evaluated across automated Quality Gates. Any record failing normalization, DANE format validation (Gate A), duplicate detection (Gate B), territorial completeness (Gate C), or campus hierarchy integrity (Gate D) triggers `stats.rejected_records += 1` and is omitted from insertion.
   - For Batch `a49910c2`, exactly **86 records** failed Quality Gate validation and were rejected.
6. **Exact Meaning of `duplicate_records`:**
   - In `OfficialCatalogSyncService` (lines 301–311), Quality Gate B identifies duplicate institutional DANE codes (`if dane_code in seen_inst_danes:`). When a duplicate is detected, the engine executes:
     ```python
     stats.duplicate_institutions += 1
     stats.rejected_records += 1
     chunk_duplicates += 1
     chunk_rejected += 1
     ```
   - At batch completion (lines 578–580), `batch_record.duplicate_records` is populated as `stats.duplicate_institutions + stats.duplicate_campuses` (**79 records**).
   - Consequently, **`duplicate_records` (79) is a strict SUBSET of `rejected_records` (86)**. The remaining **7 records** ($86 - 79 = 7$) represent malformed or incomplete records rejected by Quality Gates A, C, or D.
   - Because duplicates are already counted inside `rejected_records`, they **MUST NOT be subtracted a second time**.
7. **Correct Mathematical Equation (National Batch `a49910c2`):**
   $$\text{valid\_records} = \text{total\_records} - \text{rejected\_records}$$
   $$18,076 - 86 = \mathbf{17,990}$$
   Decomposed by rejection categories:
   $$18,076 - [79 \text{ (Gate B duplicates)} + 7 \text{ (Gates A/C/D format and territorial errors)}] = 18,076 - 86 = \mathbf{17,990}$$
8. **Database Reconciliation Across Batches:**
   - Table `official_catalog_sync_batches`:
     - Batch `a49910c2-fd62-45fa-9feb-32e82e9d063a` (National Dataset `cfw5-qzt5`): `total_records = 18,076`, `valid_records = 17,990`, `rejected_records = 86`, `duplicate_records = 79`, `status = SUCCESS`.
     - Batch `33b82da7-edd9-4a71-938a-7eafaffd50c2` (Pilot Dataset `c36d-tcj8`): `total_records = 41`, `valid_records = 41`, `rejected_records = 0`, `duplicate_records = 0`, `status = SUCCESS`.
   - Table `official_institution_catalog`:
     ```sql
     SELECT sync_batch_id, count(*) 
     FROM official_institution_catalog 
     GROUP BY sync_batch_id;
     ```
     - `a49910c2-fd62-45fa-9feb-32e82e9d063a` -> **17,990 rows**
     - `33b82da7-edd9-4a71-938a-7eafaffd50c2` -> **41 rows**
     - Total Canonical Rows: $17,990 + 41 = \mathbf{18,031 \text{ rows}}$
9. **Final Authoritative Catalog Universe:**
   $$\text{Canonical Establishments} = \text{National Batch Valid} + \text{Pilot Batch Valid}$$
   $$\mathbf{17,990} + \mathbf{41} = \mathbf{18,031}$$
   The authoritative catalog count for NTA-04 and the PEVN platform is conclusively **18,031 establishments**.
10. **Impact on Operational PEVN Tenants:**
    - **ZERO operational tenants affected.** Database verification confirms exactly 34 tenant institutions in table `institutions` (31 active, 3 inactive), identical to pre-NTA-04 baseline.
11. **Impact on Catalog-Linked Institutions:**
    - **ZERO catalog-linked institutions affected.** Exactly 7 tenant institutions link to the catalog (`catalog_institution_id IS NOT NULL`), and all 7 deterministically link to valid establishments belonging to national batch `a49910c2`. All 27 synthetic fixture tenants preserve `catalog_institution_id = NULL`.

---

### 14.1.1 QUALITY GATE ACCOUNTING RECONCILIATION

#### Audit Trail: Arithmetic Inconsistency in Previous Narrative
In the initial draft of Section 14.1, an arithmetic error was introduced in the textual explanation of the Quality Gate subtraction:
$$\text{Previous narrative expression: } 18,076 - 86 - 79 = 17,990 \quad \text{[INCORRECT]}$$
Arithmetically, $18,076 - 86 - 79 = 17,911 \neq 17,990$. The previous narrative erroneously subtracted `duplicate_records` (79) *in addition* to `rejected_records` (86).

#### Forensic Investigation of the Ingestion Engine
A forensic code audit of `OfficialCatalogSyncService` in `backend/app/services/official_catalog_sync_service.py` reveals the exact pipeline mechanics:
1. **Accounting Invariant (lines 114–116):**
   ```python
   @property
   def accounting_reconciled(self) -> bool:
       """Accounting equation: processed == valid + rejected."""
       return self.total_records_processed == (self.valid_records + self.rejected_records)
   ```
2. **Quality Gate B Handling (lines 301–306):**
   ```python
   if dane_code in seen_inst_danes:
       stats.duplicate_institutions += 1
       stats.rejected_records += 1
       chunk_duplicates += 1
       chunk_rejected += 1
   ```
3. **Batch Metadata Mapping (lines 575–580):**
   ```python
   batch_record.total_records = stats.total_records_processed
   batch_record.valid_records = stats.valid_records
   batch_record.rejected_records = stats.rejected_records
   batch_record.duplicate_records = stats.duplicate_institutions + stats.duplicate_campuses
   ```

#### Authoritative Conclusion
- **Finding (Option A):** `duplicate_records` (79) is a **strict subset** of `rejected_records` (86).
- When a duplicate DANE record is detected, Quality Gate B increments both `duplicate_institutions` and `rejected_records`.
- The 86 total rejected records comprise:
  - **79 duplicate records** rejected by Quality Gate B.
  - **7 malformed / incomplete records** rejected by Quality Gates A, C, or D ($86 - 79 = 7$).
- Therefore, subtracting 79 again was an invalid double-subtraction.
- The single, authoritative, mathematically verified accounting equation for National Batch `a49910c2` is:
  $$\mathbf{18,076 \text{ raw}} - \mathbf{86 \text{ total rejected}} = \mathbf{17,990 \text{ clean valid records}}$$
- And the combined authoritative catalog universe is:
  $$\mathbf{17,990 \text{ national batch}} + \mathbf{41 \text{ pilot batch}} = \mathbf{18,031 \text{ canonical establishments}}$$

---

### 14.2 OBSERVATION 02 (OBS-02): Implementation Artifact Inventory Resolution

All 19 artifacts created or modified under Phase NTA-04 have been inventoried, classified, and verified in Section 13 of this report. Zero files have been omitted.

---

## 15. MANDATORY FINAL STATUS

NTA-04 TECHNICAL STATUS:
PASS

DOCUMENTATION RECONCILIATION:
COMPLETE

NTA-05:
NOT AUTHORIZED

STOP.

