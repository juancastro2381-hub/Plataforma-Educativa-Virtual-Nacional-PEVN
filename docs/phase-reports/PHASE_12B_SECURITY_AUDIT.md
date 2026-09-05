# PEvN — Phase 12B Security & RBAC Governance Audit
## Threat Modeling, Tenant Isolation, and RBAC Invariant Verification

---

### 1. RBAC Model & Permission Governance

| Invariant | Status | Verification & Evidence |
| :--- | :--- | :--- |
| **Canonical Role Catalog Unchanged** | **PRESERVED** | The 11 canonical system roles (`superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `institution_admin`, `coordinator`, `academic_coordinator`, `teacher`, `student`, `guardian`) remain unmodified. |
| **Permission Taxonomy Unchanged** | **PRESERVED** | The 59 atomic permissions and their mappings in `ROLE_PERMISSIONS_CONFIG` remain strictly unchanged. |
| **No Broadening of Permissions** | **PRESERVED** | The unified provisioning workflow reuses existing, already-assigned permissions `teachers:create` and `users:create` possessed by `rector`, `institution_admin`, `national_admin`, and `superadmin`. |
| **Role Hierarchy Invariant** | **PRESERVED** | Hierarchy levels (Superadmin: 100 → Student: 10) are fully preserved. |

---

### 2. Multi-Tenant Containment & Isolation

1. **Server-Side Context Resolution**:
   - `institution_id` is never trusted from client-provided JSON bodies.
   - It is resolved exclusively from the verified JWT claims (`current_user.institution_id` / `auth.scope.institution_id`).
   - Only national administrators (`superadmin`, `national_admin`) can specify a query override (`institution_id`), strictly validated server-side.
2. **Cross-Tenant Privacy Preservation**:
   - When duplicate checks detect a document or email collision with a user in another institutional tenant, the API responds with a generic `IDENTITY_CONFLICT` message (`"El documento o correo electrónico ya se encuentra registrado en el sistema."`).
   - No external tenant names, IDs, usernames, or demographic data are leaked in error payloads.
3. **Cross-Tenant Linking Prevention**:
   - Any attempt to link an existing user from another institution raises a `CrossTenantMismatchError` (HTTP 403 / 404).

---

### 3. Credential Management & Security Lifecycle

1. **Cryptographic Password Hashing**:
   - Newly provisioned users are initialized with a cryptographically secure random token (`generate_raw_token(16)`) hashed using **Argon2id**.
   - No plaintext passwords are ever returned in API responses, stored in database columns, or logged in audit trails.
2. **Account State Differentiation**:
   - Newly provisioned users are created with:
     - `is_active = True`: Account is ready for platform interactions upon credential establishment.
     - `is_verified = False`: The account is **NOT** marked as email-verified merely because an administrator entered the data.
     - `must_change_password = True`: Forces the user to establish their private credential upon first access.
3. **Audit Trail Completeness**:
   - Every on-the-fly teacher provisioning records:
     - `AuditEventType.USER_CREATED` (target: `User.id`, metadata: document type, document number, email, role).
     - `AuditEventType.TEACHER_CREATED` (target: `Teacher.id`, metadata: appointment type, escalafón, specialty).

---

### 4. Zero Technical ID / UUID Exposure

- All search and selection interfaces use human-readable civil attributes:
  - Document Number (e.g. `20202020`)
  - Full Name (First Name, Last Name)
  - Institutional Email Address
- Technical database primary keys (PostgreSQL UUIDv4) are kept internal to the backend data layer and never exposed as required input fields in administrative forms.
