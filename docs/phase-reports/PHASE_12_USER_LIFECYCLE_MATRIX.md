# PEvN — Phase 12 User Lifecycle Matrix
## End-to-End Functional Lifecycle Status across All 11 Canonical Roles

---

| # | Role | Provisioning Path | User Association | Login / Auth | Session Restore (`/auth/me`) | Dashboard Rendering | Navigation Tree | Authorized Operations | Negative Gates (HTTP 403) | Direct URL Guard | Tenant Isolation | Lifecycle Status |
| :-: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `superadmin` | Platform Bootstrap | Pre-seeded root user | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **2** | `national_admin` | Superadmin Creation | `national_admin` role | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **3** | `department_admin` | National Admin | Department Scope | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **4** | `municipality_admin` | Department Admin | Municipality Scope | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **5** | `rector` | Rector Invitation | Token Onboarding | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **6** | `institution_admin` | Rector Provisioning | Inst User in Tenant | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **7** | `coordinator` | Rector / Inst Admin | Inst User in Tenant | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **8** | `academic_coordinator` | Rector / Inst Admin | Inst User in Tenant | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **9** | `teacher` | Rector ("8788" flow) | 1:1 Teacher Profile | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **10** | `student` | Rector / Admin / Coord | 1:1 Student (SIMAT) | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| **11** | `guardian` | Civil profile + Link | Activation Token | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |

---

### Detailed Lifecycle Trajectory Summaries

#### 1. Rector Lifecycle
- **Creation**: Emitted via `POST /api/v1/institutions/{id}/rector-invitation` by National Admin.
- **Onboarding**: Token verified via `POST /api/v1/auth/rector-onboarding`, establishing encrypted credentials.
- **Session & Navigation**: Logs in, receives access token, `/auth/me` resolves institutional context (`institution_id`).
- **Academic Governance**: Proposes academic years, periods, groups, provisions teachers using the tenant-safe search ("8788" flow), and registers students.

#### 2. Teacher Lifecycle ("8788" Flow)
- **Selection**: Rector opens modal, searches `"8788"`, selects matching institutional user without seeing raw UUID.
- **Creation**: Form submits `{ user_id: "<canonical-uuid>", specialty_area, contract_type, escalafon_grade }` to `POST /api/v1/teachers` (HTTP 201).
- **Authentication**: Teacher logs in, accesses Teacher Dashboard, hosts virtual classrooms, records student grades.
- **Security Guarding**: Administrative actions (e.g. creating teachers or closing years) return HTTP 403 Forbidden.

#### 3. Student Lifecycle
- **Selection**: Administrator searches user by document/name, selects user, enters SIMAT code.
- **Creation**: `POST /api/v1/students` creates 1:1 student profile linked to active institution.
- **Participation**: Student logs in, views course schedule, joins authorized virtual classrooms.
- **Security Guarding**: Academic management routes and administrative mutations return HTTP 403 Forbidden.

#### 4. Guardian Lifecycle
- **Registration**: Created via `POST /api/v1/guardians` with civil document and contact information.
- **Linkage**: Associated to student via `associate_guardian_to_student` with relationship type and pickup authorization.
- **Activation**: One-time token activation via `POST /api/v1/auth/guardian-activation`.
- **Follow-up**: Guardian accesses Family Monitoring dashboard to review ward's academic status.
