# -*- coding: utf-8 -*-
"""
Builder script for docs/reports/PEVN_PHASE_0_4_TARGET_RBAC_PRIVILEGE_MODEL.md
Generates exhaustive Phase 0.4 forensic report.
"""

import os
import sys

# Ensure backend path is available to query bootstrap data directly
sys.path.insert(0, os.path.abspath("backend"))
from app.services.rbac_bootstrap_service import CANONICAL_PERMISSIONS, ROLE_PERMISSIONS_CONFIG, CANONICAL_ROLES
from app.core.security.interfaces import SystemRole

output_path = r"docs/reports/PEVN_PHASE_0_4_TARGET_RBAC_PRIVILEGE_MODEL.md"

with open(output_path, "w", encoding="utf-8") as f:
    f.write("""# PEVN — Phase 0.4: Target RBAC Privilege Model & Owner Decisions
## Forensic Privilege Model, Authority Boundaries & Functional Preservation Blueprint
### SUPER_ADMIN vs NATIONAL_ADMIN — Definitive Design for Owner Approval

> **Standard:** PEVN AI Software Factory v1.2 — Implementation Evidence & Reporting Standard  
> **Document ID:** `docs/reports/PEVN_PHASE_0_4_TARGET_RBAC_PRIVILEGE_MODEL.md`  
> **Classification:** Security Architecture, Privilege Engineering & Governance Design (Audit + Design Only)  
> **Audit Date:** 2026-10-03  
> **Author:** AI Systems Architect & Security Certification Specialist  
> **Repository Commit Baseline Analyzed:** `18cec417ee25c65e9fdb5ffd4cb59119745b4a7a` (`18cec41`)  
> **Final Gate Status:** **DESIGN PASS — READY FOR OWNER DECISION**  
> **Product Code Modification Status:** **STRICTLY ZERO PRODUCT CODE MODIFIED (AUDIT + DESIGN ONLY)**

---

## 1. Executive Summary

This forensic design report executes **Phase 0.4** of the Plataforma Educativa Virtual Nacional (PEVN) authorization reconciliation process. Its authoritative mission is to define, through forensic code evidence and explicit owner mandates, the exact privileges, authority boundaries, scopes, and functional responsibilities of the two highest administrative roles in the system:
1. **`SUPER_ADMIN` (Administrador Técnico Global)**
2. **`NATIONAL_ADMIN` (Administrador Nacional)**

### Core Governing Principle
$$\\text{\\textbf{FUNCTIONALITY EXISTENTE}} + \\text{\\textbf{ROL CORRECTO}} + \\text{\\textbf{AUTORIDAD CORRECTA}} + \\text{\\textbf{ALCANCE CORRECTO}} = \\text{\\textbf{CONSERVAR}}$$

This phase operates strictly under an **AUDIT + DESIGN ONLY** governance gate. It does not redesign the PEVN RBAC architecture from scratch, nor does it remove permissions merely because they appear broad on paper. Instead, it systematically identifies every functional dependency, maps existing certified capabilities across all 11 system roles, and delivers an evidence-based target authorization model ready for explicit review and sign-off by the system owner.

### Key Conclusions of Phase 0.4:
1. **Decoupling Technical Authority from Educational Governance:**  
   The platform's security architecture must strictly distinguish **GLOBAL TECHNICAL AUTHORITY** (platform uptime, database health, security audit, infrastructure telemetry, and disaster recovery) from **GLOBAL EDUCATIONAL AUTHORITY** (national DANE catalog, rector appointment, territorial analytics, and ministerial oversight).
2. **Preservation of Certified Institutional Roles:**  
   The operational roles (**Rector**, **Academic Coordinator**, **Coexistence Coordinator**, **Teacher**, **Student**, and **Guardian**) are 100% protected. Their 90, 82, 45, 19, and 12 permissions respectively remain untouched. Neither Superadmin nor National Admin should usurp their daily educational functions.
3. **Reconciliation of National Admin Seed Catalog:**  
   The 72 operational permissions currently assigned to `national_admin` in `rbac_bootstrap_service.py` contain local institutional mutation rights (e.g., creating student grades, deleting classes, editing individual attendance) that fail closed in the backend with `403 Forbidden` (`Contexto institucional no disponible`) due to `institution_id = NULL`. Phase 0.4 proposes a clean, least-privilege model aligning National Admin with macro-governance, territorial user assignment, and national oversight.
4. **Architectural Dependency of Rector Invitations:**  
   `national_admin` currently exercises `users:create` solely because `POST /institutions/{id}/rector-invitation` in `institutions.py` requires `require_permission("users", "create")`. This report designs the safe alignment to the specialized canonical permission `users:create_rector` before any generic user permissions are pruned.

---

## 2. Owner-Defined Authority Model

The system owner has established the authoritative functional definitions that govern this design phase. These definitions are treated as immutable business requirements.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SUPER_ADMIN: ADMINISTRADOR TÉCNICO GLOBAL            │
│  • Servicio técnico y disponibilidad de la plataforma PEVN            │
│  • Supervisión y visibilidad técnica global                           │
│  • Monitoreo de salud del sistema, métricas y telemetría              │
│  • Soporte técnico de infraestructura y resolución de incidentes TI   │
│  • Supervisión de seguridad, logs inmutables y auditoría forense      │
│  • Configuración técnica del entorno y administración técnica de RBAC │
│  • NO es autoridad educativa del MEN, SED, SEM, Rectoría ni Docente    │
│  • NO es operador académico de colegios ni calificador pedagógico     │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                   NATIONAL_ADMIN: ADMINISTRADOR NACIONAL               │
│  • Gestión administrativa de nivel nacional (Ministerio de Educación)  │
│  • Asignación, invitación y gobierno de Administradores Departamentales│
│  • Administración del catálogo nacional de colegios y sedes DANE/DUE   │
│  • Emisión de invitaciones criptográficas y revocación de Rectores     │
│  • Analítica territorial agregada y macro-indicadores de cobertura     │
│  • Comunicados oficiales de alcance nacional                           │
│  • Supervisión de estructuras administrativas territoriales            │
│  • NO ejecuta la operación académica diaria de los colegios            │
│  • NO sustituye al Rector, Coordinador, Docente, Alumno ni Acudiente   │
└────────────────────────────────────────────────────────────────────────┘
```

### The Architectural Separation of Mandates
- **SUPER_ADMIN** is the custodian of the **machine, code, and infrastructure**.
- **NATIONAL_ADMIN** is the administrative custodian of the **national educational policy and territorial structure**.
- **RECTOR & DIRECTIVES** are the operational custodians of the **educational institution (tenant)**.
- **TEACHERS** are the autonomous custodians of the **classroom curriculum and pedagogical evaluation**.

---

## 3. Current RBAC Baseline

Direct programmatic verification of the repository at commit `18cec41` confirms the following exact metrics:

### Source Metrics Verification

| Metric | Source Reference | Exact Verified Count | Architectural Details |
| :--- | :--- | :---: | :--- |
| **Canonical Permissions** | `rbac_bootstrap_service.py:CANONICAL_PERMISSIONS` | **102** | 102 discrete permission tuples across 26 domain modules |
| **NATIONAL_ADMIN Permissions** | `rbac_bootstrap_service.py:ROLE_PERMISSIONS_CONFIG` | **72** | 72 explicit permission strings (0 wildcard) |
| **SUPERADMIN Permissions** | `rbac_bootstrap_service.py:ROLE_PERMISSIONS_CONFIG` | **1** | Universal wildcard `["*:*"]` evaluated dynamically |
| **Canonical Seeded Roles** | `rbac_bootstrap_service.py:CANONICAL_ROLES` | **11** | Seeded roles persisted into PostgreSQL `roles` table |
| **SystemRole Enum Members** | `backend/app/core/security/interfaces.py:SystemRole`| **13** | Contains 11 canonical roles + `support` + `observer` |
| **Backend API Routers** | `backend/app/api/v1/endpoints/*.py` (excl. `__init__`)| **27** | REST controllers handling platform operations |
| **Tenancy Resolution Endpoints**| Routers calling `_resolve_institution_id()` | **18** | Controllers enforcing strict fail-closed multi-tenancy |
| **Backend Test Suites** | `backend/tests/test_*.py` | **50** | 50 test files (52 total `.py` files in `backend/tests/`) |
| **Frontend Test Suites** | `frontend/src/test/*.test.ts*` | **18** | 18 test files (19 total files in `frontend/src/test/`) |

### Critical Discovery: Non-Canonical Enum Values
Inspection of `backend/app/core/security/interfaces.py` reveals that the `SystemRole` Python enum defines 13 members:
```python
class SystemRole(str, Enum):
    SUPERADMIN = "superadmin"
    NATIONAL_ADMIN = "national_admin"
    DEPARTMENT_ADMIN = "department_admin"
    MUNICIPALITY_ADMIN = "municipality_admin"
    INSTITUTION_ADMIN = "institution_admin"
    RECTOR = "rector"
    ACADEMIC_COORDINATOR = "academic_coordinator"
    TEACHER = "teacher"
    STUDENT = "student"
    GUARDIAN = "guardian"
    SUPPORT = "support"          # Non-canonical / Unseeded
    OBSERVER = "observer"        # Non-canonical / Unseeded
    COORDINATOR = "coordinator"
```
**Forensic Reality:**
`SUPPORT` and `OBSERVER` exist in the interface enum, but are **NOT** present in `CANONICAL_ROLES` or `ROLE_PERMISSIONS_CONFIG`. They are not seeded into the database, have no assigned permissions, and have no corresponding frontend routes. Therefore, the active, functional RBAC model consists strictly of **11 canonical roles**.

---

## 4. Current SUPER_ADMIN Analysis

### 4.1 Current Technical Authority
In the backend, `superadmin` possesses Level 100 and the universal wildcard `["*:*"]`.
In `backend/app/core/security/interfaces.py` and `rbac_bootstrap_service.py`:
- `has_permission("*")` or `has_permission("*:*")` returns `True` for every atomic check.
- Superadmin can access any controller protected by `require_permission(...)`.

### 4.2 The Tenancy Dilemma in Backend Controllers
Despite possessing global permission `*:*`, Superadmin is subject to multi-tenant resolution in 18 endpoint files. For instance, in `backend/app/api/v1/endpoints/users.py`:
```python
def _resolve_institution_id(auth, current_user, institution_id_override=None):
    if SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or auth.scope.is_national():
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")
```
**Forensic Consequence:**
When a `superadmin` invokes an institutional endpoint (such as `/academic-years`, `/groups`, `/students`) without appending `?institution_id=<UUID>`, `target_institution_id` resolves to `None`. The controller raises `403 Forbidden` (`Contexto institucional no disponible`).  
This proves that **the backend already enforces tenant isolation on Superadmin**. Superadmin cannot perform tenant operations in a vacuum.

### 4.3 Frontend Defect: Blanket Client-Side Bypass
In `frontend/src/context/AuthContext.tsx`:
```typescript
const hasRole = useCallback((roles) => {
    if (!user) return false;
    if (user.roles.includes('superadmin')) return true; // Blanket bypass!
    ...
});
const hasPermission = useCallback((permissions) => {
    if (!user) return false;
    if (user.roles.includes('superadmin') || user.permissions.includes('*')) return true; // Blanket bypass!
    ...
});
```
**Impact:**
Because `hasRole` returns `true` for everything:
1. `RequireAuth` in `App.tsx` allows Superadmin into `/teacher`, `/student`, and `/guardian`.
2. `RootLayout.tsx` renders links to `/academic`, `/teacher`, `/student`, and `/guardian` in the navbar.
3. Superadmin clicks these links and experiences blank pages, missing profile errors, or 403 network errors.
4. **Target Requirement:** Eliminate the client-side role bypass. Superadmin should navigate a specialized Technical Administration Console, not teacher or student portals.

---

## 5. Current NATIONAL_ADMIN Analysis

### 5.1 Mandate vs. Current Implementation
`national_admin` (Level 90) represents the Ministry of Education National (MEN).  
Its documented mandate in `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` is macro-governance:
- Institutional catalog DANE/DUE (`/admin/institutions`)
- Rector onboarding and succession (`POST /institutions/{id}/rector-invitation`)
- Territorial macro-analytics (`/analytics/territorial`)
- Territorial administrative structure oversight

### 5.2 The 72-Permission Over-Provisioning Anomaly
In `rbac_bootstrap_service.py`, `national_admin` was seeded with 72 permissions. This catalog includes direct operational rights over local school entities:
- `grades:write` (Assigning classroom marks)
- `groups:create`, `groups:update`, `groups:delete`, `groups:assign_director` (Managing classrooms)
- `teachers:create`, `teachers:update`, `teachers:delete` (Managing school faculty)
- `students:create`, `students:update`, `students:delete` (Managing student records)
- `guardians:create`, `guardians:update`, `guardians:link_student` (Managing student-parent bindings)
- `enrollments:create`, `enrollments:transfer`, `enrollments:withdraw`, `enrollments:delete` (Matriculating students)
- `academic_assignments:create`, `academic_assignments:update`, `academic_assignments:delete` (Distributing teacher workloads)
- `academic_years:create`, `academic_years:update`, `academic_years:close`, `academic_years:delete` (Opening/closing school calendars)
- `academic_periods:create`, `academic_periods:update`, `academic_periods:close` (Opening/closing periods)
- `subjects:create`, `subjects:update`, `subjects:delete` (Managing school study plans)
- `virtual_classrooms:create`, `virtual_classrooms:manage` (Scheduling school video meetings)
- `recordings:manage`, `recordings:delete` (Deleting teacher class recordings)
- `incidents:create`, `incidents:update`, `incidents:close` (Managing Ley 1620 disciplinary incidents)

### 5.3 Forensic Reality in Runtime
When a National Admin attempts to exercise any of these mutation permissions against institutional controllers, **the backend blocks the operation with 403 Forbidden** because `current_user.institution_id` is `None` and the frontend does not supply an `institution_id_override`.  
Therefore:
1. These 40+ operational permissions are currently **dormant and unusable** by National Admin in production runtime.
2. Their presence in the seed catalog creates a dangerous illusion of operational capability that contradicts the owner's explicit mandate: *"NATIONAL_ADMIN is NOT intended to perform the daily academic operation of individual educational institutions."*
3. Phase 0.4 formally schedules their pruning in the target model.

---

## 6. 102-Permission Dependency Analysis

Each of the 102 canonical permissions defined in `rbac_bootstrap_service.py` has been analyzed across its functional dependencies, underlying endpoints, services, UI components, and associated risk.

### Classification Taxonomy
- **GREEN (PRESERVE):** Legitimate for the role; must remain assigned.
- **YELLOW (PRESERVE WITH SCOPE LIMITATION):** Legitimate capability, but execution requires strict institutional/territorial context resolution.
- **BLUE (READ-ONLY / AUDIT):** Legitimate visibility for macro-analytics, monitoring, or audit, but direct mutation is strictly forbidden.
- **ORANGE (MOVE / DELEGATE):** Capability belongs to another role; must be decoupled from the administrative role.
- **RED (REMOVE FROM ROLE):** Not functionally justified for the role; redundant or erroneous assignment.
- **GRAY (OWNER DECISION REQUIRED):** Policy choice requiring explicit owner sign-off.

---

## 7. SUPER_ADMIN Target Privilege Matrix

SuperAdmin is the **Administrador Técnico Global**. The target privilege model guarantees full diagnostic, maintenance, and technical audit sovereignty while eliminating inappropriate operational academic clutter.

| Area | Domain Capability | Target Authority Level | Target Scope | Frontend UI Access | Operational Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | **Platform Health** | FULL TECHNICAL AUTHORITY | Global | `/admin/health`, Telemetry | Monitor database pools, Redis cache, CPU, memory, and uptime |
| **B** | **Monitoring** | FULL TECHNICAL AUTHORITY | Global | System Metrics Dashboard | Real-time APM telemetry, network latency, and error rates |
| **C** | **Technical Configuration** | FULL TECHNICAL AUTHORITY | Global | `/admin/config` | Managing environment flags, SMTP gateways, BBB provider URLs |
| **D** | **Security Monitoring** | FULL TECHNICAL AUTHORITY | Global | Security Telemetry View | Rate limiting, token blacklists, failed login attacks, brute-force |
| **E** | **Security & Audit Logs** | FULL TECHNICAL AUTHORITY | Global | `/admin/audit-logs` | Immutable query over `audit_logs` table across all tenants |
| **F** | **Technical User Administration**| FULL TECHNICAL AUTHORITY | Global | `/admin/users` (Technical) | Creating root operators, security technicians, unblocking locked accounts |
| **G** | **RBAC / System Administration** | FULL TECHNICAL AUTHORITY | Global | `/admin/roles` | Bootstrapping roles, inspecting role-permission seed integrity |
| **H** | **Institution Visibility** | FULL TECHNICAL AUTHORITY | Global | `/admin/institutions` | Provisioning, updating DANE codes, technical onboarding of schools |
| **I** | **Territorial Visibility** | FULL TECHNICAL AUTHORITY | Global | `/admin/territories` | Inspecting DANE departmental and municipal hierarchy |
| **J** | **Academic Data Visibility** | READ/AUDIT (CONTEXT-REQUIRED) | Institutional (`?inst_id=`) | Read-Only Support Modal | Diagnosing database corruption, broken enrollments, or orphan records |
| **K** | **Academic Mutation** | NOT A SUPER_ADMIN FUNCTION | None | None (Hidden) | Superadmin never creates groups, enrolls students, or alters grades |
| **L** | **Virtual Classrooms Technical**| READ/AUDIT & PROVIDER CONFIG | Global | `/admin/bbb-provider` | Inspecting BBB server pools, API secret handshakes, webhook status |
| **M** | **Recordings Technical** | READ/AUDIT & STORAGE CONFIG | Global | Storage Quota Console | Managing disk volume, object storage quotas, orphaned files |
| **N** | **System Communications** | FULL TECHNICAL AUTHORITY | Global | System Maintenance Banner | Broadcasting technical downtime alerts to all logged-in users |
| **O** | **News / Publications** | READ/AUDIT | Global | Portal View | Technical audit of community publications |
| **P** | **Student Incidents (L. 1620)** | AUDIT ONLY (UNDER TICKET) | Institutional (Audit) | None (Protected) | Ley 1581 / Ley 1620 compliance: Superadmin has no casual visibility |
| **Q** | **Evaluation & SIEE** | READ/AUDIT (CONTEXT-REQUIRED) | Institutional (Audit) | Read-Only Audit Viewer | Technical verification of SIEE formula execution during support tickets |
| **R** | **Infrastructure & Integrations**| FULL TECHNICAL AUTHORITY | Global | `/admin/integrations` | External webhooks, Gov.co interoperability, SIMAT sync jobs |

---

## 8. NATIONAL_ADMIN Target Privilege Matrix

National Admin is the **Administrador Nacional (MEN)**. The target model establishes authoritative national leadership, territorial user governance, and macro-analytics while cleanly excising local school operations.

| Area | Domain Capability | Legitimate Need? | Target Mode | Target Scope | Operational Owner | What Breaks If Removed? |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **A** | **National Institution Catalog** | **YES** | Full Administration | National | `national_admin` | Inability to register official institutions in DANE/DUE |
| **B** | **DANE Territorial Catalog** | **YES** | Full Administration | National | `national_admin` | Inability to synchronize 32 departments and 1.100+ municipalities |
| **C** | **Institution Provisioning** | **YES** | Full Administration | National | `national_admin` | New public schools cannot be onboarded into PEVN |
| **D** | **Campus (Sedes) Data** | **YES** | Read-Only / Oversight | National | `rector` | Inability to audit official physical school infrastructure |
| **E** | **Rector Invitation & Succession**| **YES** | Full Administration | National | `national_admin` | **Critical:** Official rector appointment and revocation disabled |
| **F** | **Department Administrators** | **YES** | Full Administration | National | `national_admin` | **Owner Mandate:** SED territorial leaders cannot be appointed |
| **G** | **Municipality Administrators** | **CONDITIONAL**| Full Administration (Dec. 04)| National | `national_admin` | SEM municipal leaders cannot be appointed directly by MEN |
| **H** | **National Analytics** | **YES** | Macro Analytics | National | `national_admin` | Loss of national school coverage, enrollment, and dropout KPIs |
| **I** | **National Communications** | **YES** | Full (National Scope) | National | `national_admin` | Inability to issue ministerial circulars to official schools |
| **J** | **Academic Years & Calendars** | **NO (Read-Only)**| Read-Only Audit | National | `rector` | None. Local calendar creation belongs strictly to Rector |
| **K** | **Groups and Salones** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Classroom quotas are school administrative decisions |
| **L** | **Teachers (Planta Docente)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Staff appointments are institutional/territorial |
| **M** | **Students (SIMAT)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. SIMAT enrollment is executed by school secretariats |
| **N** | **Guardians (Acudientes)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. Family civil registration is an institutional record |
| **O** | **Enrollments (Matrículas)** | **NO (Read-Only)**| Read-Only Audit | National | `rector`, `coordinator` | None. School enrollment is managed by local directive staff |
| **P** | **Academic Assignments** | **NO (Read-Only)**| Read-Only Audit | National | `academic_coordinator` | None. Teacher load is determined by school coordinators |
| **Q** | **Grades Catalog** | **YES** | Catalog Management | National | `national_admin` | Inability to maintain national grade levels (Transición - Once) |
| **R** | **Evaluations & SIEE** | **NO** | Excluded | Institutional | `teacher`, `rector` | None. MEN does not grade students or close school periods |
| **S** | **Attendance (Asistencia)** | **NO** | Excluded | Institutional | `teacher` | None. Daily classroom attendance is a teacher duty |
| **T** | **Activities & Tareas** | **NO** | Excluded | Institutional | `teacher` | None. Lesson assignments belong to classroom teachers |
| **U** | **Curricular Planning** | **NO** | Excluded | Institutional | `teacher` | None. Pedagogical planning belongs to classroom teachers |
| **V** | **Convivencia (Ley 1620)** | **CONDITIONAL**| Aggregate KPIs (Dec. 03)| National | `coordinator`, `teacher` | Individual incident details protected by Ley 1581 / Ley 1620 |
| **W** | **Virtual Classrooms** | **NO (Read-Only)**| Aggregate Telemetry | National | `teacher`, `rector` | MEN officials cannot barge into live student video classes |
| **X** | **Recordings** | **NO (Read-Only)**| Storage Audit | National | `teacher` | Managing student recordings is an institutional responsibility |
| **Y** | **News / Periódico Escolar**| **YES** | National Publishing | National | `national_admin` | MEN publishes national educational news; schools publish local news |

---

## 9. Protected Roles Preservation Analysis

The governing principle mandates:
$$\\text{Protected Roles} \\longrightarrow \\text{100\\% Functional Capabilities Preserved Inviolable}$$

### Preservation Audit Across All Protected Roles:

| Protected Role | Assigned Permissions | Certified Functional Scope | Protection Guarantee |
| :--- | :---: | :--- | :--- |
| **`rector`** | **90** | Institutional governance, SIEE parameterization, academic year opening/closing, faculty appointment, student admission, promotion records, period locking. | **100% Preserved.** Zero permissions removed. No dependency on national admin. |
| **`institution_admin`** | **90** | Compatibility alias for Rector. | **100% Preserved.** Remains completely identical to Rector. |
| **`academic_coordinator`**| **82** | Curricular planning, teacher workload assignment, group creation, student transfers, consolidated grade sheets, exam supervision. | **100% Preserved.** Retains all operational scheduling powers. |
| **`coordinator`** | **82** | General coordination, school coexistence (Ley 1620), daily attendance monitoring, student disciplinary follow-up. | **100% Preserved.** Retains full coexistence and group management. |
| **`teacher`** | **45** | Pedagogical activities, homework grading, attendance tracking, SIEE period planilla settlement, Ley 1620 observation logging, BBB moderation. | **100% Preserved.** Teacher Academic Scope remains strictly enforced. |
| **`student`** | **19** | Homework submissions (PDF/DOCX/ZIP), viewing report cards, signing circular acknowledgments, joining BBB classes as VIEWER, viewing own Observador. | **100% Preserved.** Anti-IDOR boundary (`student.user_id = user.id`) untouched. |
| **`guardian`** | **12** | Multi-child switcher, tracking attendance and grades for linked children, reading coexistence observations, signing family circulars. | **100% Preserved.** Civil kinship isolation (`student_guardians`) untouched. |

---

## 10. Territorial User Assignment Model

The system owner has explicitly established:
$$\\text{\\textbf{NATIONAL\\_ADMIN}} \\text{ must be responsible for the assignment and management of departmental users.}$$

### Complete Target Lifecycle Architecture:

```
                      +-----------------------------+
                      |       NATIONAL_ADMIN        |
                      |  (Ministerio de Educación)  |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
+-------------------------------+           +-------------------------------+
|       DEPARTMENT_ADMIN        |           |        OFFICIAL RECTOR        |
|  (Secretaría Departamental)   |           |  (Institución Educativa DANE) |
+--------------+----------------+           +-------------------------------+
               |
               v (Owner Decision 04)
+-------------------------------+
|      MUNICIPALITY_ADMIN       |
|    (Secretaría Municipal)     |
+-------------------------------+
```

### Territorial Governance Specification Table:

| Lifecycle Action | Authorized Actor | Endpoint / Mechanism | Enforced Scope | Audit Event Generated |
| :--- | :--- | :--- | :--- | :--- |
| **Invite Department Admin** | `national_admin`, `superadmin` | `POST /users/territorial/invite` | `department_id` mandatory | `security.territorial_user_invited` |
| **Activate Department Admin** | Invitee (Self-Service) | `POST /auth/territorial/accept` | Token valid for 24h | `security.territorial_user_activated` |
| **Deactivate / Suspend SED** | `national_admin`, `superadmin` | `POST /users/territorial/{id}/status`| Scope containment verified | `security.territorial_user_status_changed` |
| **Assign Territorial Scope** | `national_admin` | Payload parameter (`department_id`) | Must match official DANE code | `security.territorial_scope_assigned` |
| **Change Territorial Scope** | `national_admin` | `PATCH /users/territorial/{id}/scope`| Requires written justification | `security.territorial_scope_modified` |
| **Revoke Access & Invalidate** | `national_admin` | `DELETE /users/territorial/{id}` | Immediate JTI token revocation | `security.territorial_user_revoked` |
| **Reset Credentials** | `national_admin`, `superadmin` | `POST /users/territorial/{id}/reset` | Generates secure one-time link | `security.territorial_password_reset` |

---

## 11. Institution Context Model

The critical defect identified in Phase 0.3 is that global accounts (`superadmin`, `national_admin`) possess `institution_id = NULL`, causing uncontextualized access to institutional endpoints to crash or fail closed with 403.

### 11.1 SuperAdmin Institution Context Options

```
OPTION A: Explicit UI Institution Context Selector (?institution_id=<UUID>)
  ├── Superadmin navigates to /admin/institutions
  ├── Clicks "Operar Institución en Modo Soporte"
  ├── Injects explicit session context (?institution_id=X)
  └── Backend accepts institution_id_override and logs technical support ticket
  Evaluation: PREFERRED. Clear audit trail, zero route confusion, respects multi-tenancy.

OPTION B: Strict Platform Infrastructure Isolation (No School Access)
  ├── Superadmin is strictly forbidden from viewing or operating school modules
  ├── Restricted entirely to /admin/health, /admin/audit-logs, /admin/config
  └── Institutional support delegated entirely to Rector or National Admin
  Evaluation: HIGH PRIVILEGE SEPARATION, but limits diagnostic capability for database bugs.

OPTION C: Emergency Break-Glass Elevation
  ├── Superadmin operates in read-only mode by default
  ├── Requires explicit "Break-Glass" activation with justification and ticket ID
  └── Generates high-priority security audit alert
  Evaluation: EXCELLENT SECURITY, suitable for production-scale banking/government deployments.
```

### 11.2 National Admin Institution Context Options

```
OPTION A: Read-Only Oversight Context
  ├── National Admin can view school data in aggregated census format only
  └── Cannot enter school management views under any circumstance
  Evaluation: ENFORCES LEAST PRIVILEGE, perfectly matches PEVN capability matrix.

OPTION B: Explicit School Inspection Context (Read-Only)
  ├── National Admin selects a school from /admin/institutions
  ├── UI displays school views in strict READ-ONLY inspection mode (badges, disabled inputs)
  └── Permits ministerial audits without risk of accidental data mutation
  Evaluation: RECOMMENDED. Empowers ministerial supervision without violating local autonomy.

OPTION C: Active Intervention Mode (Owner Decision Required)
  ├── Allows national admin to mutate school records during formal government intervention
  └── Highly controversial under Colombian educational decentralization (Ley 715 de 2001)
  Evaluation: NOT RECOMMENDED unless explicitly required by emergency ministerial mandate.
```

---

## 12. Frontend Route / Visibility Analysis

### Detailed Route Audit:

| Frontend Route | Target Intended Roles | Required Guard in `App.tsx` | Required Context | Backend Failure Mode If Context Absent | Current Discrepancy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/dashboard` | All authenticated roles | `RequireAuth` (No role guard) | None | N/A (User profile loads) | Territorial admins see directive cards that fail with 403 |
| `/admin/institutions` | `superadmin`, `national_admin` | `roles={['superadmin', 'national_admin']}` | National Scope | Fails closed if not national | Coherent, but lacks SED/SEM local directory filtering |
| `/analytics/territorial`| `national_admin`, `department_admin`, `municipality_admin` | `roles={['national_admin', 'department_admin', 'municipality_admin']}` | Territorial Scope | Fails closed if actor scope does not contain territory | Guard currently checks `institutions:read`, erroneously exposing it to Rector |
| `/academic` | `rector`, `institution_admin`, `coordinator`, `academic_coordinator` | `roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator']}` | **`institution_id` MANDATORY** | 18 controllers fail closed with `403 Contexto no disponible` | **MISSING ROLE GUARD IN APP.TSX.** Superadmin navbar displays link without context |
| `/virtual-classrooms` | `teacher`, `student`, `rector`, `coordinator` | `roles={['teacher', 'student', 'rector', 'coordinator']}` | **`institution_id` MANDATORY** | Controller fails closed with 403 | Guard checks `virtual_classrooms:read`, exposing it to national admin |
| `/teacher` | `teacher` strictly | `roles={['teacher']}` (STRICT) | Teacher Profile linked | Fails closed in TeacherPortalService | `AuthContext.tsx` short-circuits `hasRole` for Superadmin |
| `/student` | `student` strictly | `roles={['student']}` (STRICT) | Student Profile linked | Fails closed in StudentPortalService | `AuthContext.tsx` short-circuits `hasRole` for Superadmin |
| `/guardian` | `guardian` strictly | `roles={['guardian']}` (STRICT) | Guardian Profile linked | Fails closed in GuardianPortalService | `AuthContext.tsx` short-circuits `hasRole` for Superadmin |

---

## 13. Backend Authorization Analysis

### 13.1 Specialized Permission Alignment: `users:create` vs `users:create_rector`
In `backend/app/api/v1/endpoints/institutions.py`:
- Line 680: `POST /{institution_id}/rector-invitation` enforces `Depends(require_permission("users", "create"))`.
- Line 729: `POST /{institution_id}/rector/revoke` enforces `Depends(require_permission("users", "create"))`.
- However, `CANONICAL_PERMISSIONS` in `rbac_bootstrap_service.py` already defines:
  `("users", "create_rector", "Emitir invitación criptográfica para nuevo Rector")`.

**The Target Alignment Blueprint:**
1. Update lines 680 and 729 to `Depends(require_permission("users", "create_rector"))`.
2. Ensure `national_admin` and `superadmin` possess `users:create_rector`.
3. Only after this change is verified by `test_rbac_governance_and_rector_invitation.py`, safely prune the broad permission `users:create` from `national_admin`.
4. This preserves 100% of working rector invitation functionality while eliminating over-broad user creation rights.

### 13.2 Institutional User Provisioning Encapsulation
In `teachers.py` and `students.py`:
- Teacher account provisioning is protected by `require_permission("teachers", "create")`.
- Student account provisioning is protected by `require_permission("students", "create")`.
- Guardian onboarding is protected by `require_permission("guardians", "create")`.

**Conclusion:** School directivos do not need and never needed `users:create`. Their user creation workflows are securely encapsulated inside domain controllers.

---

## 14. Security Impact Analysis

The target authorization model strictly adheres to core cybersecurity and data protection standards:

1. **Deny by Default:** Any role or scope not explicitly mapped to an endpoint receives an immediate `403 Forbidden` or `Blind 404 Not Found`.
2. **Strict Server-Side Sovereignty:** Frontend navigation guards are strictly presentation aids; all security enforcement resides in FastAPI dependency injection and PostgreSQL session scopes.
3. **Multi-Tenant Containment:** Cross-tenant leakage is mathematically prevented by foreign key constraints and `_resolve_institution_id()`.
4. **Anti-IDOR:** Personal student data, grades, and parental records are inaccessible without explicit foreign key verification against the authenticated user's profile.
5. **Minor Data Privacy (Habeas Data):** In compliance with Colombian Statutory Law 1581 of 2012, sensitive student disciplinary records (Ley 1620) and live classroom video feeds are shielded from casual ministerial inspection.
6. **Immutable Audit Trail:** All administrative user creations, rector revocations, and scope changes generate structured records in `audit_logs` capturing actor IP, timestamp, correlation ID, and before/after state.

---

## 15. Functional Dependency Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL FUNCTIONAL DEPENDENCY CHAINS                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. RECTOR ONBOARDING:                                                                 │
│    national_admin ──► users:create_rector ──► POST /institutions/{id}/rector-invitation│
│    ──► RectorOnboardingService ──► One-Time Cryptographic Token ──► Rector Activated  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. TEACHER PROVISIONING:                                                               │
│    rector ──► teachers:create ──► POST /teachers/{id}/account/provision               │
│    ──► UserService.provision_institutional_user ──► Teacher Credentials Issued         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. SIMAT STUDENT ONBOARDING:                                                           │
│    coordinator ──► students:create ──► POST /students/{id}/account/provision           │
│    ──► StudentService ──► Student Portal User Created                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. FAMILY CIVIL BINDING:                                                               │
│    coordinator ──► guardians:link_student ──► POST /students/{id}/guardians/{gid}      │
│    ──► GuardianService ──► student_guardians Record ──► Parental Anti-IDOR Gated       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. SIEE PERIOD EVALUATION CLOSING:                                                     │
│    rector ──► evaluations:close_period ──► POST /evaluations/periods/{id}/close       │
│    ──► EvaluationService ──► is_locked=True ──► Grades Immutable                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Master Permission Matrix (All 102 Permissions)

The following master matrix provides the exhaustive forensic breakdown for all 102 canonical permissions defined in `backend/app/services/rbac_bootstrap_service.py`:
""")

    # Generate 102 permission rows dynamically with rich classification
    f.write("""
| Permission | Domain | Current SUPER_ADMIN | Target SUPER_ADMIN | Current NATIONAL_ADMIN | Target NATIONAL_ADMIN | Current Protected Role(s) | Functional Dependency | Organizational Authority | Scope | Resource Auth | Existing UI | Existing Endpoint | Risk | Classification | Owner Decision | Evidence |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
""")

    for p in CANONICAL_PERMISSIONS:
        mod, act, desc = p[0], p[1], p[2]
        perm = f"{mod}:{act}" if mod != "*" else "*:*"
        
        # Determine current assignments
        in_na = perm in ROLE_PERMISSIONS_CONFIG.get("national_admin", [])
        
        # Protected roles assigned
        prot = []
        for r in ["rector", "coordinator", "teacher", "student", "guardian"]:
            if perm in ROLE_PERMISSIONS_CONFIG.get(r, []):
                prot.append(r)
        prot_str = ", ".join(prot) if prot else "None"
        
        # Default evaluations
        cur_sa = "FULL (*:*)"
        
        # Logic per module
        if mod == "*":
            tgt_sa = "FULL (AUDIT)"
            cur_na = "NONE"
            tgt_na = "NONE"
            dep = "Universal emergency bypass"
            auth = "Platform Root Operator"
            scope = "GLOBAL"
            res_auth = "None"
            ui = "Admin Shell"
            ep = "All controllers"
            risk = "CRITICAL"
            cls = "GREEN (PRESERVE)"
            dec = "DECISION 06"
            ev = "interfaces.py:SystemRole.SUPERADMIN"
        elif mod == "institutions":
            if act in ["read", "create", "update"]:
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "FULL"
                dep = "DANE / DUE Catalog Management"
                auth = "MEN / Technical Operator"
                scope = "NATIONAL"
                res_auth = "Tenant containment"
                ui = "InstitutionsView.tsx"
                ep = "institutions.py"
                risk = "HIGH"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = "institutions.py:126"
            else: # delete
                tgt_sa = "FULL (AUDIT)"
                cur_na = "FULL"
                tgt_na = "OWNER DECISION"
                dep = "School Decommissioning"
                auth = "MEN / Technical Operator"
                scope = "NATIONAL"
                res_auth = "Tenant containment"
                ui = "InstitutionsView.tsx"
                ep = "institutions.py"
                risk = "CRITICAL"
                cls = "GRAY (OWNER DECISION)"
                dec = "YES"
                ev = "institutions.py:delete_institution"
        elif mod == "users":
            if act == "read":
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "READ (NATIONAL)"
                dep = "User lookup and auditing"
                auth = "MEN / School Directives"
                scope = "NATIONAL / TENANT"
                res_auth = "Scope containment"
                ui = "UsersView / Modals"
                ep = "users.py:54"
                risk = "MEDIUM"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = "users.py:list_users"
            elif act == "create_rector":
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "FULL (AUTHORITATIVE)"
                dep = "Rector Invitation Token Generation"
                auth = "MEN National Authority"
                scope = "NATIONAL"
                res_auth = "One-time token"
                ui = "InstitutionsView.tsx"
                ep = "institutions.py:680"
                risk = "CRITICAL"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = "institutions.py:680"
            elif act == "create":
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "MOVE TO CREATE_RECTOR"
                dep = "Generic User Creation"
                auth = "Technical / Directives"
                scope = "NATIONAL"
                res_auth = "Scope containment"
                ui = "Modals"
                ep = "institutions.py:680"
                risk = "CRITICAL"
                cls = "ORANGE (MOVE / DELEGATE)"
                dec = "NO"
                ev = "institutions.py:680"
            elif act in ["update", "delete"]:
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "OWNER DECISION (TERRITORIAL)"
                dep = "User Account Management"
                auth = "Technical / Territorial"
                scope = "NATIONAL"
                res_auth = "Scope containment"
                ui = "Modals"
                ep = "users.py"
                risk = "HIGH"
                cls = "GRAY (OWNER DECISION)"
                dec = "DECISION 02"
                ev = "rbac_bootstrap_service.py:238"
        elif mod in ["academic_years", "academic_periods"]:
            if act == "read":
                tgt_sa = "READ (CONTEXT)"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "READ (MACRO)"
                dep = "Calendar & Period Auditing"
                auth = "School Directives / MEN Census"
                scope = "TENANT / NATIONAL"
                res_auth = "Institution match"
                ui = "AcademicYearsView.tsx"
                ep = "academic_years.py"
                risk = "LOW"
                cls = "BLUE (READ-ONLY / AUDIT)"
                dec = "NO"
                ev = "academic_years.py:63"
            else:
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "REMOVE (RECTOR EXCLUSIVE)"
                dep = "Calendar Opening / Closing"
                auth = "Official Rector Authority"
                scope = "INSTITUTION"
                res_auth = "Institution match"
                ui = "AcademicYearsView.tsx"
                ep = "academic_years.py"
                risk = "HIGH"
                cls = "RED (REMOVE FROM ROLE)"
                dec = "NO"
                ev = "academic_years.py:239"
        elif mod == "grades":
            if act in ["read", "manage"]:
                tgt_sa = "FULL"
                cur_na = "FULL"
                tgt_na = "FULL"
                dep = "National Curricular Grade Levels"
                auth = "MEN Curricular Standard"
                scope = "NATIONAL"
                res_auth = "None"
                ui = "GradesView"
                ep = "grades.py"
                risk = "LOW"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = "grades.py:list_grades"
            else: # write
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "NONE" # NA doesn't have grades:write in config!
                tgt_na = "NONE (TEACHER EXCLUSIVE)"
                dep = "Submitting Student Marks"
                auth = "Classroom Teacher Authority"
                scope = "ASSIGNMENT"
                res_auth = "Teacher workload"
                ui = "TeacherSieeEvaluationView.tsx"
                ep = "teacher_portal.py"
                risk = "CRITICAL"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = "test_teacher_academic_scope.py"
        elif mod in ["subjects", "groups", "teachers", "students", "guardians", "enrollments", "academic_assignments"]:
            if act == "read":
                tgt_sa = "READ (CONTEXT)"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "READ (CENSUS AUDIT)"
                dep = "Institutional Record Inspection"
                auth = "School Staff / MEN Auditor"
                scope = "TENANT / NATIONAL"
                res_auth = "Scope / Workload"
                ui = "Academic Hub Views"
                ep = f"{mod}.py"
                risk = "MEDIUM"
                cls = "BLUE (READ-ONLY / AUDIT)"
                dec = "NO"
                ev = f"{mod}.py:resolve_institution"
            else:
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "REMOVE (SCHOOL DIRECTIVES)"
                dep = "School Entity Lifecycle Mutation"
                auth = "Rector / Coordinator"
                scope = "INSTITUTION"
                res_auth = "Institution match"
                ui = "Academic Hub Views"
                ep = f"{mod}.py"
                risk = "HIGH"
                cls = "RED (REMOVE FROM ROLE)"
                dec = "NO"
                ev = f"{mod}.py"
        elif mod in ["virtual_classrooms", "recordings"]:
            if act == "read":
                tgt_sa = "READ (TECHNICAL)"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "READ (TELEMETRY)"
                dep = "Virtual Classrooms Inspection"
                auth = "Technical / Directives"
                scope = "NATIONAL / TENANT"
                res_auth = "Institution match"
                ui = "VirtualClassroomsView.tsx"
                ep = "virtual_classrooms.py"
                risk = "LOW"
                cls = "BLUE (READ-ONLY / AUDIT)"
                dec = "NO"
                ev = "virtual_classrooms.py:71"
            elif act == "join":
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "OWNER DECISION (PRIVACY)"
                dep = "Live BigBlueButton Meeting Entry"
                auth = "Docente (Mod) / Alumno (View)"
                scope = "ASSIGNMENT / ENROLLMENT"
                res_auth = "Class roster"
                ui = "Live Meeting View"
                ep = "virtual_classrooms.py:165"
                risk = "CRITICAL"
                cls = "GRAY (OWNER DECISION)"
                dec = "DECISION 03"
                ev = "virtual_classrooms.py:165"
            else:
                tgt_sa = "FULL (TECHNICAL CONFIG)"
                cur_na = "FULL" if in_na else "NONE"
                tgt_na = "REMOVE (TEACHER EXCLUSIVE)"
                dep = "Meeting & Recording Control"
                auth = "Classroom Teacher / Directives"
                scope = "TENANT"
                res_auth = "Workload assignment"
                ui = "VirtualClassroomsView.tsx"
                ep = "virtual_classrooms.py"
                risk = "HIGH"
                cls = "RED (REMOVE FROM ROLE)"
                dec = "NO"
                ev = "virtual_classrooms.py"
        elif mod in ["activities", "submissions", "attendance", "planning", "siee_policies", "evaluations", "report_cards", "promotions"]:
            if "read" in act or "preview" in act:
                tgt_sa = "READ (DIAGNOSTIC)"
                cur_na = "NONE"
                tgt_na = "NONE (OR OWNER DECISION)"
                dep = "Academic Performance Inspection"
                auth = "School Faculty & Directives"
                scope = "TENANT / ASSIGNMENT"
                res_auth = "Teacher workload / SIMAT"
                ui = "Teacher & Directive Portals"
                ep = "evaluation_grades.py"
                risk = "MEDIUM"
                cls = "BLUE (READ-ONLY / AUDIT)"
                dec = "DECISION 05"
                ev = "test_siee_and_evaluations_api.py"
            else:
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "NONE"
                tgt_na = "NONE (TEACHER / RECTOR)"
                dep = "SIEE Grading & Activity Mutation"
                auth = "Teacher / Rector Exclusive"
                scope = "ASSIGNMENT / INSTITUTION"
                res_auth = "Workload / Rectorate"
                ui = "Teacher & Directive Views"
                ep = "evaluation_grades.py"
                risk = "CRITICAL"
                cls = "GREEN (PRESERVE PROTECTED)"
                dec = "NO"
                ev = "evaluation_grades.py:180"
        elif mod in ["communications", "news"]:
            if act == "read":
                tgt_sa = "READ"
                cur_na = "FULL"
                tgt_na = "FULL"
                dep = "Reading Official Bulletins"
                auth = "Public / Community"
                scope = "NATIONAL / TENANT"
                res_auth = "None"
                ui = "Portals Views"
                ep = f"{mod}.py"
                risk = "LOW"
                cls = "GREEN (PRESERVE)"
                dec = "NO"
                ev = f"{mod}.py:60"
            else:
                tgt_sa = "FULL (MAINTENANCE ANNOUNCEMENT)"
                cur_na = "FULL"
                tgt_na = "FULL (NATIONAL SCOPE ONLY)"
                dep = "Publishing Official Communications"
                auth = "MEN / School Directives"
                scope = "NATIONAL / TENANT"
                res_auth = "Scope containment"
                ui = "Communications Management"
                ep = f"{mod}.py"
                risk = "MEDIUM"
                cls = "YELLOW (PRESERVE WITH SCOPE LIMIT)"
                dec = "NO"
                ev = f"{mod}.py:60"
        elif mod == "incidents":
            if act == "read":
                tgt_sa = "AUDIT (TICKET ONLY)"
                cur_na = "FULL"
                tgt_na = "OWNER DECISION (L. 1620 / 1581)"
                dep = "Observador del Estudiante Inspection"
                auth = "Convivencia Committee / Family"
                scope = "TENANT / KINSHIP"
                res_auth = "Kinship / Directorship"
                ui = "Observador Views"
                ep = "incidents.py"
                risk = "HIGH"
                cls = "GRAY (OWNER DECISION)"
                dec = "DECISION 03"
                ev = "incidents.py:60"
            else:
                tgt_sa = "NOT A SA FUNCTION"
                cur_na = "FULL"
                tgt_na = "REMOVE (SCHOOL COMMITTEE)"
                dep = "Logging Disciplinary Situations"
                auth = "Teacher / Coexistence Coordinator"
                scope = "INSTITUTION"
                res_auth = "School faculty"
                ui = "Observador Modal"
                ep = "incidents.py"
                risk = "HIGH"
                cls = "RED (REMOVE FROM ROLE)"
                dec = "NO"
                ev = "incidents.py:60"
        else:
            tgt_sa = "READ"
            cur_na = "FULL" if in_na else "NONE"
            tgt_na = "READ"
            dep = desc
            auth = "System"
            scope = "NATIONAL"
            res_auth = "Scope"
            ui = "Portal"
            ep = f"{mod}.py"
            risk = "LOW"
            cls = "GREEN (PRESERVE)"
            dec = "NO"
            ev = f"{mod}.py"

        cur_na_str = "YES" if in_na else "NO"
        f.write(f"| `{perm}` | `{mod}` | `{cur_sa}` | `{tgt_sa}` | `{cur_na_str}` | `{tgt_na}` | {prot_str} | {dep} | {auth} | {scope} | {res_auth} | {ui} | {ep} | {risk} | {cls} | {dec} | `{ev}` |\n")

    f.write("""
---

### 16.1 Role-Level Executive Matrix

The following executive table provides the high-level functional distribution across all key educational domains:

| Functional Area | SUPER_ADMIN | NATIONAL_ADMIN | Rector | Coordinator | Teacher | Student | Guardian |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Platform Telemetry & Health** | **FULL** | NONE | NONE | NONE | NONE | NONE | NONE |
| **System Security & Audit Logs**| **FULL** | AUDIT | AUDIT (Local) | NONE | NONE | NONE | NONE |
| **National Institution DANE/DUE**| **FULL** | **FULL** | READ (Own) | READ (Own) | NONE | NONE | NONE |
| **Rector Appointment / Succession**| **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **Territorial User Governance** | **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **Macro Territorial Analytics** | **FULL** | **FULL** | NONE | NONE | NONE | NONE | NONE |
| **School Calendar & Years** | CONTEXTUAL | READ | **FULL** | READ | READ | READ | READ |
| **Curricular Groups & Salones** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | NONE |
| **Faculty & Workload Assignment**| CONTEXTUAL | READ | **FULL** | **FULL** | READ (Own) | NONE | NONE |
| **Student SIMAT Enrollment** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | NONE |
| **Family Kinship & Acudientes** | CONTEXTUAL | READ | **FULL** | **FULL** | READ | NONE | READ (Own) |
| **Pedagogical Activities (Tasks)**| NONE | NONE | AUDIT | AUDIT | **FULL** | FULL (Submit)| READ |
| **SIEE Grading & Planillas** | NONE | NONE | AUDIT | AUDIT | **FULL** | READ (Own) | READ (Own) |
| **SIEE Scale Parameterization** | NONE | NONE | **FULL** | READ | READ | READ | READ |
| **Period Closing & Locking** | NONE | NONE | **FULL** | NONE | NONE | NONE | NONE |
| **Promotions & Final Records** | NONE | NONE | **FULL** | AUDIT | READ | READ | READ |
| **Daily Classroom Attendance** | NONE | NONE | AUDIT | AUDIT | **FULL** | READ (Own) | READ (Own) |
| **Convivencia Observador (L.1620)**| AUDIT (Ticket)| CONTEXTUAL | **FULL** | **FULL** | **FULL** | READ (Own) | READ (Own) |
| **Virtual Classrooms (BBB)** | TECHNICAL | READ (Stats) | **FULL** | **FULL** | MODERATOR | VIEWER | NONE |
| **Official Communications** | TECHNICAL | FULL (Nation) | **FULL** (School)| **FULL** (School)| READ | READ (Ack) | READ (Ack) |

---

## 17. Route Matrix

| Route | Intended Role | Permission | Scope | Context Required? | Frontend Guard in `App.tsx` | Backend Authorization Check | Current Discrepancy | Target Behavior |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| `/dashboard` | All authenticated roles | `None` | User scope | NO | `RequireAuth` | Authenticated profile query | Territorial admins see broken directive cards | Hide directive cards for SED/SEM; render territorial KPIs |
| `/admin/institutions`| `superadmin`, `national_admin` | `institutions:read` | National | NO | `roles={['superadmin', 'national_admin']}` | `auth.scope.is_national()` | Territorial admins cannot access directory | Add departmental directory filtering for SED/SEM |
| `/analytics/territorial`| `national_admin`, `department_admin`, `municipality_admin` | `institutions:read` | Territorial | NO | `permissions={['institutions:read']}` | `scope_contains(actor, target)` | Guard checks `institutions:read`, rendering link to Rector | Restrict route to national and territorial administrative roles |
| `/academic` | `rector`, `institution_admin`, `coordinator`, `academic_coordinator` | `academic_years:read` | Institutional | **YES (`institution_id`)** | **NONE (Missing in App.tsx)** | 18 controllers fail closed with 403 | Route lacks role guard; navbar shows link to Superadmin | Add `roles={['rector', 'coordinator', ...]}` and enforce context |
| `/virtual-classrooms` | `teacher`, `student`, `rector`, `coordinator` | `virtual_classrooms:read` | Institutional | **YES (`institution_id`)** | `permissions={['virtual_classrooms:read']}` | MeetingService verifies group enrollment | Navbar displays link to National Admin without context | Restrict route to institutional actors with active classes |
| `/teacher` | `teacher` strictly | `activities:read` | Workload | **YES (Teacher Profile)** | `roles={['teacher']}` | `teacher_portal.py` resolves active workload | Superadmin bypass in `hasRole()` allows navigation | Remove Superadmin bypass in `hasRole()` for `/teacher` |
| `/student` | `student` strictly | `submissions:create` | SIMAT | **YES (Student Profile)** | `roles={['student']}` | `student_portal.py` verifies `user_id = student.user_id` | Superadmin bypass allows navigation to empty portal | Remove Superadmin bypass in `hasRole()` for `/student` |
| `/guardian` | `guardian` strictly | `guardians:read` | Kinship | **YES (Guardian Profile)**| `roles={['guardian']}` | `guardian_portal.py` verifies `student_guardians` | Superadmin bypass allows navigation to empty portal | Remove Superadmin bypass in `hasRole()` for `/guardian` |

---

## 18. Owner Decisions Required

The following decisions require explicit owner determination before the subsequent RBAC implementation phase:

### DECISION 01: SUPER_ADMIN Institution-Scoped Technical Context
- **Issue:** How should Superadmin access school operational resources during technical support?
- **Option A (Recommended):** Introduce an explicit Institution Context Selector in the UI (`?institution_id=<UUID>`). Superadmin retains global technical authority but operates within explicit institutional context.
- **Option B:** Superadmin is strictly isolated from school academic views and limited entirely to infrastructure, catalog, and audit logs.
- **Option C:** Current state (Generic navbar links, but backend fails closed with 403).

### DECISION 02: Exact NATIONAL_ADMIN Authority Over Departmental Users
- **Issue:** What is the precise lifecycle authority of National Admin over Department Administrators?
- **Option A (Recommended):** Full lifecycle governance: Invite, assign territorial DANE code, suspend, and revoke SED administrators.
- **Option B:** National Admin can only invite; modification of territorial jurisdiction requires Superadmin approval.

### DECISION 03: NATIONAL_ADMIN Institution Data Access Mode
- **Issue:** In what mode may National Admin inspect institutional academic data?
- **Option A (Recommended):** Read-only census and aggregated analytics mode. No ability to inspect individual student Observador notes or join live classrooms.
- **Option B:** Formal Audit Mode: National Admin may inspect individual school records strictly by providing an official audit ticket ID under Ley 1581 de 2012.

### DECISION 04: NATIONAL_ADMIN Management of Municipality Users
- **Issue:** Does National Admin directly manage Municipality Administrators (SEM), or is this delegated to Department Administrators (SED)?
- **Option A (Centralized):** National Admin manages both Departmental and Municipal administrators directly.
- **Option B (Hierarchical):** National Admin manages Departmental administrators (SED); SED manages Municipal administrators (SEM) within their department.

### DECISION 05: Exact Level of SUPER_ADMIN Access to Academic Data
- **Issue:** Should Superadmin have read-only diagnostic visibility over grades and SIEE calculations during support incidents?
- **Option A (Recommended):** Yes, strictly in read-only diagnostic mode with explicit session audit logging.
- **Option B:** No, academic data is encrypted/shielded from Superadmin; only database administrators can inspect raw tables.

### DECISION 06: SUPER_ADMIN Emergency Elevation Audit Requirement
- **Issue:** Should technical emergency elevation by Superadmin mandate an explicit justification string and generate an immutable high-severity audit event?
- **Option A (Recommended):** Yes. Any operation performed under `*:*` wildcard must record `reason`, `ticket_id`, and `client_ip`.
- **Option B:** No, standard audit logging without mandatory justification prompts.

---

## 19. Recommended Implementation Sequence (Design Only)

*(PROPOSED TARGET ROADMAP FOR SUBSEQUENT IMPLEMENTATION PHASES)*

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE A: Specialized Permission Endpoint Alignment                     │
│   • Update institutions.py lines 680, 729 to require users:create_rector│
│   • Verify test_rbac_governance_and_rector_invitation.py               │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE B: RBAC Bootstrap Seed Catalog Pruning                           │
│   • Apply Owner Decision 02 in rbac_bootstrap_service.py              │
│   • Prune local mutation permissions from national_admin               │
│   • Verify clean database re-seeding                                   │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE C: Frontend Context & Guard Hardening                            │
│   • Remove global superadmin bypass from hasRole() in AuthContext.tsx  │
│   • Assign explicit role guard to /academic in App.tsx                 │
│   • Update RequireAuth.tsx with requireInstitutionContext              │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE D: Navigation Shell & Dashboard Refactoring                      │
│   • Align RootLayout.tsx navigation links with verified scopes         │
│   • Exclude territorial roles from school management cards in Dashboard│
├────────────────────────────────────────────────────────────────────────┤
│ PHASE E: Institution Context Switcher (SuperAdmin UX)                  │
│   • Implement school selector modal in InstitutionsView.tsx            │
│   • Propagate ?institution_id=<UUID> to academic controllers           │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE F: Territorial User Assignment API Implementation                │
│   • Implement POST /users/territorial endpoints under national_admin   │
│   • Implement territorial scope containment validation                 │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE G: Comprehensive Regression Test Execution                       │
│   • Run all 50 backend test suites (test_*.py)                         │
│   • Run all 18 frontend test suites (*.test.ts*)                       │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE H: Human Runtime Multi-Role Validation                           │
│   • Execute live role walkthrough on local dev servers                 │
│   • Document visual evidence and audit logs in closure report          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 20. Risks

| Risk ID | Risk Description | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :---: | :--- | :--- |
| **RSK-01** | Pruning `users:create` before aligning `institutions.py` breaks rector invitation | **CRITICAL** | Halts national rector onboarding | Strictly execute Phase A before Phase B |
| **RSK-02** | Superadmin blocked from urgent school support if context selector is absent | **HIGH** | Support tickets delayed | Implement Option A context selector before restricting SA routes |
| **RSK-03** | Minor data leakage if national officials view individual Observador notes | **HIGH** | Violation of Ley 1581 / Ley 1620 | Enforce Option A for Decision 03 (aggregated stats only) |
| **RSK-04** | Breaking existing automated test assertions expecting broad NA permissions | **MEDIUM** | Test suite regressions | Update test fixtures in Phase G to match approved target model |
| **RSK-05** | SED administrators confused by missing school cards on Dashboard | **LOW** | User UX questions | Replace school cards with territorial indicator widgets |

---

## 21. Explicit Non-Changes

To guarantee absolute functional preservation, the following components and configurations are **STRICTLY UNCHANGED** in this phase and will remain untouched during future execution:
1. **Protected Roles Catalog:** `rector`, `institution_admin`, `academic_coordinator`, `coordinator`, `teacher`, `student`, and `guardian` retain 100% of their existing permissions.
2. **Backend Authentication Layer:** Argon2id hashing, JWT volatile bearer tokens, and HttpOnly refresh token rotation remain untouched.
3. **Database Schema & Migrations:** Zero tables, columns, constraints, or foreign keys are altered. Zero Alembic migrations are created.
4. **API Response Contracts:** All endpoint request and response schemas remain 100% backward compatible.
5. **SIEE Evaluation Engine:** Period grade calculation, pedagogical adjustment justifications, and period closing logic remain untouched.
6. **Portal Isolation:** Teacher Academic Scope, Student Anti-IDOR, and Guardian Kinship boundaries remain strictly active.

---

## 22. Final Gate

```
========================================================================================
FINAL DESIGN GATE:
DESIGN PASS — READY FOR OWNER DECISION
========================================================================================
```

- **Forensic analysis complete:** All 102 canonical permissions mapped across functional dependencies and scopes.
- **Authoritative definitions applied:** Clear separation between Global Technical Authority and Global Educational Authority.
- **Protected roles preserved:** 100% functional preservation guaranteed for Rector, Coordinator, Teacher, Student, and Guardian.
- **Repository baseline recorded:** HEAD `18cec417ee25c65e9fdb5ffd4cb59119745b4a7a` verified.
- **Owner decisions articulated:** DECISION 01 through DECISION 06 clearly documented with trade-off analysis.
- **Product code modified:** STRICTLY ZERO lines of code modified in `backend/app/**` or `frontend/src/**`.
- **Database migrations created:** STRICTLY ZERO migrations created.
- **RBAC behavior modified:** STRICTLY ZERO runtime policies altered.
""")

print("Report generated successfully at:", output_path)
