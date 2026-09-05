# PEvN — Phase 12 Canonical Role Provisioning Matrix
## Authoritative Provisioning Mechanisms & Lifecycle Trajectories for All 11 Roles

---

| # | Canonical Role | Role Level | Authorized Provisioner | Canonical Provisioning Path & Protocol | Scope Boundary | Duplicate / Collision Protection |
| :-: | :--- | :---: | :--- | :--- | :--- | :--- |
| **1** | `superadmin` | Level 1 (Global) | Platform Bootstrap | Seeded during database initialization / deployment bootstrap. | Global (`is_national=True`) | System unique username & email constraint. |
| **2** | `national_admin` | Level 2 (National) | Superadmin | User creation endpoint with `national_admin` role assignment. | National (`is_national=True`) | Unique email & username across national directory. |
| **3** | `department_admin` | Level 3 (Territorial) | National Admin / Superadmin | Provisioned with departmental territorial boundary (`department_id`). | Departmental | Bound to specific `department_id`. |
| **4** | `municipality_admin` | Level 4 (Territorial) | Department / National Admin | Provisioned with municipal territorial boundary (`municipality_id`). | Municipal | Bound to specific `municipality_id`. |
| **5** | `rector` | Level 5 (Institutional) | National Admin / Superadmin | `POST /institutions/{id}/rector-invitation` -> One-time cryptographic onboarding token -> `POST /auth/rector-onboarding`. | Institution Tenant (`institution_id`) | Only one active Rector invitation per institution. |
| **6** | `institution_admin` | Level 6 (Institutional) | Rector | Provisioned within institution by Rector with `institution_admin` role assignment. | Institution Tenant (`institution_id`) | Tenant-scoped uniqueness. |
| **7** | `coordinator` | Level 7 (Campus) | Rector / Institution Admin | Provisioned within institution by Rector/Admin with `coordinator` role assignment. | Institution / Campus | Tenant-scoped uniqueness. |
| **8** | `academic_coordinator` | Level 8 (Campus) | Rector / Institution Admin | Provisioned within institution by Rector/Admin with `academic_coordinator` role assignment. | Institution / Campus | Tenant-scoped uniqueness. |
| **9** | `teacher` | Level 9 (Classroom) | Rector / Institution Admin | Institutional User search/selection ("8788" flow) -> `POST /api/v1/teachers` with appointment metadata. | Institution Tenant (`institution_id`) | 1:1 Unique Constraint (`teachers.user_id` unique). |
| **10** | `student` | Level 10 (Individual) | Rector / Institution Admin / Coordinator | Institutional User search/selection -> `POST /api/v1/students` with SIMAT code & inclusion metadata. | Institution Tenant (`institution_id`) | 1:1 Unique User Constraint + Unique National SIMAT code. |
| **11** | `guardian` | Level 11 (Individual) | Rector / Institution Admin | `POST /guardians` (civil profile) -> `POST /guardians/{id}/students/{id}` -> `POST /auth/guardian-activation`. | Family / Student Linkage in Tenant | Unique Document Type + Number constraint. |

---

### Provisioning Invariants & Governance Rules

1. **Hierarchy Integrity**: No role may provision another role of equal or higher level.
2. **Tenant Containment**: All institutional roles (`rector`, `institution_admin`, `coordinator`, `academic_coordinator`, `teacher`, `student`, `guardian`) are strictly bound to their parent `institution_id`.
3. **No Direct Raw UUID Entry**: All UI provisioning flows resolve human identification criteria (Name, Document, Email) to internal UUIDs via tenant-isolated queries.
