# PEVN — RBAC Functional Preservation & Reconciliation Audit
## Phase 0.3: Functional Authorization Reconciliation & Baseline Protection Audit
### Comprehensive Forensic Mapping of Existing Capabilities, Dependencies, Scopes & Preservation Blueprint

> **Standard:** PEVN AI Software Factory v1.2 — Implementation Evidence & Reporting Standard  
> **Document ID:** `docs/reports/PEVN_RBAC_FUNCTIONAL_PRESERVATION_RECONCILIATION_AUDIT.md`  
> **Classification:** Security, Architecture & Functional Preservation Audit (Documentation-Only Reconciliation)  
> **Audit Date:** 2026-10-03  
> **Author:** AI Systems Architect & Security Certification Specialist  
> **Repository Commit Baseline:** `bbd2ed9c0559fbe64e157a45c4b9130b2685b2da` (`bbd2ed9`)  
> **Prior Reviewed Baseline:** `7fb83fb14bc21d675d580511068f2c866de18654` (`7fb83fb`)  
> **Final Gate Status:** **AUDIT PASS — DOCUMENTATION BASELINE CORRECTED — OWNER DECISIONS REQUIRED**  
> **Product Modification Status:** **STRICTLY ZERO PRODUCT CODE MODIFIED (AUDIT & DOCUMENTATION RECONCILIATION ONLY)**

---

## 1. Executive Summary

This forensic audit was executed under **Phase 0.3** of the Plataforma Educativa Virtual Nacional (PEVN). Its primary mandate is to establish an authoritative, numerically verified **Functional Preservation Baseline** before any RBAC or visibility implementation changes are performed in subsequent project phases.

### Core Principle
$$\text{\textbf{FUNCTIONALITY EXISTENTE}} + \text{\textbf{ROL CORRECTO}} + \text{\textbf{ALCANCE CORRECTO}} = \text{\textbf{CONSERVAR}}$$

Refactoring enterprise authorization layers carries the severe operational risk of inadvertently stripping permissions or access paths upon which working business logic depends. A common pitfall in enterprise authorization refactoring is the indiscriminate pruning of permissions that appear "excessive" or "too broad" in a static spreadsheet, without first verifying why they were granted, what controllers enforce them, or which user onboarding and operational lifecycles depend on them.

This documentary reconciliation corrects previous preliminary estimations and establishes the exact repository baseline:
1. **Verified Canonical Permission Catalog (102 Atomic Permissions):**  
   Independent programmatic verification of `backend/app/services/rbac_bootstrap_service.py` (`CANONICAL_PERMISSIONS`) reveals exactly **102 canonical atomic permissions** across 26 functional domains (including the universal technical wildcard `*:*`), superseding the preliminary count of 73.
2. **Verified National Admin Permissions (72 Permissions):**  
   The initial seed configuration `ROLE_PERMISSIONS_CONFIG[SystemRole.NATIONAL_ADMIN.value]` contains exactly **72 permissions**, superseding the preliminary count of 48.
3. **Critical User-Management Dependencies:**  
   `national_admin` currently holds `users:create` because the **Rector Invitation** (`POST /api/v1/institutions/{id}/rector-invitation`) and **Rector Succession/Revocation** (`POST /api/v1/institutions/{id}/rector/revoke`) endpoints in `backend/app/api/v1/endpoints/institutions.py` explicitly mandate `require_permission("users", "create")`. Deleting `users:create` from `national_admin` prior to aligning these controllers to the specialized permission `users:create_rector` would immediately break national rector onboarding and succession.
4. **Autonomous School User Provisioning:**  
   School directives (`rector`, `coordinator`) do not require the global `users:create` permission to provision operational staff. In `teachers.py`, teacher registration relies on `teachers:create`, which internally calls `UserService.provision_institutional_user()`. Similarly, `students.py` uses `students:create` and `students:update` for student onboarding and status toggling.
5. **Backend Multi-Tenant Isolation Fails Closed:**  
   All 18 institutional domain controllers gate tenancy via `_resolve_institution_id()`. Failures observed during local testing when national accounts access school modules (`PERMISSION_DENIED: Contexto institucional no disponible`) are presentation-layer mismatches caused by the frontend shell exposing tenant-scoped routes to accounts with `institution_id = NULL` without an **Institution Context Selector**. The backend authorization layer correctly blocks tenantless execution.
6. **Preservation of Certified Portals:**  
   The Teacher Portal (`/teacher`), Student Portal (`/student`), and Guardian Portal (`/guardian`) incorporate verified Anti-IDOR protections, academic scope boundaries, and civil kinship validations that must remain strictly preserved during future reconciliation phases.

---

## 2. Audit Objective

The objective of this Phase 0.3 forensic audit is to establish an exact, indisputable baseline of repository evidence and functional dependencies, reconciling all prior documentary discrepancies.

The purpose is **NOT** to unilaterally decide or implement the final RBAC model. Rather, it is to ensure that every metric, table, and conclusion in the Phase 0.3 baseline is supported by actual repository source code.

This audit establishes clarity across the five core authorization layers:
1. **ROLE:** Identifies the technical category of the actor (e.g., `national_admin`, `rector`, `teacher`).
2. **ORGANIZATIONAL AUTHORITY:** Identifies the legal or functional mandate within the Colombian educational system (e.g., Ministry of Education, School Directive, Classroom Teacher).
3. **PERMISSION:** Identifies the atomic resource-action gate evaluated by the authorization engine (e.g., `institutions:create`, `evaluations:grade`).
4. **TENANT / ORGANIZATIONAL SCOPE:** Identifies the geographic or institutional boundary within which an action may execute (`institution_id`, `department_id`, `municipality_id`, or national).
5. **RESOURCE-LEVEL AUTHORIZATION:** Identifies whether a specific individual record is accessible based on workload assignments, homeroom directorship, or verified civil kinship.

All five layers must remain coherent. A permission does not constitute organizational authority; a national scope does not grant automatic license to mutate local institutional records; and frontend UI visibility does not equate to backend authorization.

---

## 3. Scope

This audit conducted a comprehensive, read-only analysis of the PEVN codebase:
- **11 Canonical System Roles:** `superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `institution_admin`, `academic_coordinator`, `coordinator`, `teacher`, `student`, `guardian`.
- **102 Canonical Atomic Permissions:** Defined in `CANONICAL_PERMISSIONS` in `rbac_bootstrap_service.py`.
- **27 API Endpoint Routers:** All routers in `backend/app/api/v1/endpoints/*.py` (28 files total including `__init__.py`), with 18 controllers implementing `_resolve_institution_id()`.
- **50 Backend Test Suites:** All `test_*.py` test files in `backend/tests/` (52 files total including `conftest.py` and `__init__.py`).
- **18 Frontend Test Suites:** Vitest suites matching `*.test.ts*` in `frontend/src/test/` (19 files total including `setup.ts`).
- **Frontend Presentation Shell:** `frontend/src/App.tsx`, `RootLayout.tsx`, `Dashboard.tsx`, `AuthContext.tsx`, `RequireAuth.tsx`.
- **Architectural & Security Specifications:** `docs/AUTHORIZATION.md`, `docs/PHASE_3_RBAC_MATRIX.md`, `docs/SECURITY.md`, `docs/ARCHITECTURE.md`, `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md`.

---

## 4. Governance / No-Change Confirmation

In strict compliance with the PEVN AI Software Factory v1.2 governance model:
- **Zero product code files were modified** across `backend/app/**` and `frontend/src/**`.
- **Zero database schemas, tables, columns, or constraints were altered.**
- **Zero Alembic migrations were generated or applied.**
- **Zero API contracts, request payloads, or response schemas were changed.**
- **Zero permissions or role mappings were altered in code.**
- **Zero route guards or authentication context logic were modified.**
- **Zero test files were modified.**
- **Zero Git commits or pushes were performed.**
- **Task Nature:** Documentary correction, numerical reconciliation, and forensic baseline establishment only.

---

## 5. Repository Baseline

- **Repository Branch:** `main`
- **Current HEAD Commit SHA-1:** `bbd2ed9c0559fbe64e157a45c4b9130b2685b2da` (`bbd2ed9`)
- **Current Commit Subject:** `RBAC FUNCTIONAL PRESERVATION & RECONCILIATION AUDIT`
- **Prior Reviewed Baseline Commit:** `7fb83fb14bc21d675d580511068f2c866de18654` (`7fb83fb`)
- **Prior Commit Subject:** `PHASE 0.2 — AUTHORIZATION MODEL CONSISTENCY & IMPLEMENTATION PLAN`
- **Working Tree State:** Clean (only documentation correction in progress).
- **Target Artifact Being Reconciled:** `docs/reports/PEVN_RBAC_FUNCTIONAL_PRESERVATION_RECONCILIATION_AUDIT.md`.

---

## 6. Sources Reviewed

| Category | File / Path | Scope & Authority |
| :--- | :--- | :--- |
| **Documentation** | `docs/AUTHORIZATION.md` | Multi-Tenant Isolation & Hierarchical Scope Rules |
| **Documentation** | `docs/PHASE_3_RBAC_MATRIX.md` | Phase 3A Granular Permission Matrix Specification |
| **Documentation** | `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` | Functional Capabilities by National/Territorial/School Role |
| **Documentation** | `docs/SECURITY.md` | Security by Design, Least Privilege, & Colombian Data Privacy |
| **Documentation** | `docs/ARCHITECTURE.md` | System Architecture, Hexagonal Boundaries & Tenancy Model |
| **Documentation** | `docs/reports/PEVN_RBAC_ROLE_VISIBILITY_RECONCILIATION.md` | Phase 0.2 RBAC Model & Route Consistency Audit |
| **Backend Core** | `backend/app/core/security/interfaces.py` | `SystemRole`, `Permission`, `OrganizationalScope` definitions |
| **Backend RBAC** | `backend/app/services/rbac_bootstrap_service.py` | `CANONICAL_ROLES`, `CANONICAL_PERMISSIONS`, `ROLE_PERMISSIONS_CONFIG` |
| **Backend Endpoints**| `backend/app/api/v1/endpoints/*.py` (27 routers) | Controllers, `require_permission` dependencies, tenancy resolution |
| **Backend Tests** | `backend/tests/test_*.py` (50 test suites) | Automated verification of auth, tenancy, SIEE, and domain workflows |
| **Frontend Core** | `frontend/src/context/AuthContext.tsx` | Reactive auth state, `hasRole`, `hasPermission`, `isInScope` |
| **Frontend Guards**| `frontend/src/components/auth/RequireAuth.tsx` | Route guard wrapper enforcing authentication and role match |
| **Frontend Shell** | `frontend/src/layouts/RootLayout.tsx`, `Dashboard.tsx` | Navigation shell, conditional links, directive access cards |
| **Frontend Routing**| `frontend/src/App.tsx` | Client-side routing table and route guard assignments |
| **Frontend Tests** | `frontend/src/test/*.test.ts*` (18 test suites) | Vitest suites verifying navigation, roles, and UI rendering |

---

## 7. Authorization Architecture

PEVN implements a comprehensive 5-layer authorization model designed to enforce Least Privilege and Multi-Tenant Isolation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. AUTHENTICATION                               │
│  Validates actor identity via JWT Bearer Token & HttpOnly Refresh      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                        2. SYSTEM ROLE & LEVEL                          │
│  Categorizes actor type: SystemRole with numeric hierarchy (10 - 100)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                   3. TENANT / ORGANIZATIONAL SCOPE                     │
│  Boundaries where actions execute (National, Territorial, Institution) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                     4. ATOMIC PERMISSION CHECK                         │
│  Granular resource:action evaluated against canonical role mappings    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                   5. RESOURCE-LEVEL AUTHORIZATION                      │
│  Anti-IDOR validation: Workload assignment, homeroom, or civil kinship │
└────────────────────────────────────────────────────────────────────────┘
```

### The Five Inviolable Principles
1. **ROLE is not AUTHORITY:** A technical role represents an identity classification, whereas authority represents the legitimate organizational mandate to act under Colombian law and educational governance.
2. **PERMISSION is not SCOPE:** Holding `grades:write` or `students:create` does not grant the right to execute that action globally across all institutions.
3. **SCOPE is not AUTOMATIC ACCESS:** Being a national official (`is_national=True`) does not bypass institutional tenancy; tenant-scoped endpoints require explicit institutional context resolution.
4. **FRONTEND VISIBILITY is not BACKEND AUTHORIZATION:** A visible button or route in the browser does not confer permission. The backend authorization layer enforces security sovereignty and fails closed.
5. **COHERENCE ACROSS ALL FIVE LAYERS:** Any operation must satisfy all five layers simultaneously: authentic actor, appropriate role, valid organizational scope, explicit permission, and legitimate resource ownership.

---

## 8. Role Inventory

The platform defines **11 canonical system roles** in `SystemRole` (`interfaces.py`) and `CANONICAL_ROLES` (`rbac_bootstrap_service.py`):

| # | Role Identifier | Security Level | DANE / Organizational Scope | Colombian Educational Mandate |
| :-: | :--- | :-: | :--- | :--- |
| **1** | `superadmin` | 100 | National (Technical Root) | Operador técnico de plataforma, infraestructura, mantenimiento y auditoría forense. |
| **2** | `national_admin` | 90 | National (MEN) | Ministerio de Educación Nacional: Catálogo DANE/DUE, rectorías y analítica macro. |
| **3** | `department_admin`| 80 | Departamental (SED) | Secretaría de Educación Departamental: Supervisión y cobertura territorial. |
| **4** | `municipality_admin`| 70 | Municipal (SEM) | Secretaría de Educación Municipal: Supervisión y seguimiento de colegios locales. |
| **5** | `rector` | 60 / 70 | Institución Educativa | Rector Oficial: Representante legal, gobierno escolar, planta docente, SIEE y actas. |
| **6** | `institution_admin`| 60 / 70 | Institución Educativa | Alias técnico de compatibilidad para funciones de Rectoría Institucional. |
| **7** | `academic_coordinator`| 50 / 60 | Institución / Sede | Coordinador Académico: Carga docente, horarios, planeación curricular y sábanas. |
| **8** | `coordinator` | 50 | Institución / Sede | Coordinador de Convivencia / Sede: Situaciones Ley 1620, salones, asistencia y disciplina. |
| **9** | `teacher` | 30 / 50 | Carga Asignada (Grupo/Asig) | Docente de Aula: Calificaciones SIEE, actividades pedagógicas, asistencia y notas. |
| **10**| `student` | 10 / 20 | Propio (SIMAT) | Estudiante Matriculado: Tareas, evaluaciones, boletines, asistencia y videoclases. |
| **11**| `guardian` | 10 | Hijos / Tutorados Vinculados| Acudiente Legal: Seguimiento académico, observador, circulares y boletines familiares. |

---

## 9. VERIFIED Permission Inventory

Programmatic verification of `CANONICAL_PERMISSIONS` in `backend/app/services/rbac_bootstrap_service.py` confirms exactly **102 canonical atomic permissions** across 26 modules:

| # | Domain Module | Permission Count | Atomic Permission Keys & Descriptions |
| :-: | :--- | :-: | :--- |
| **1** | `*` | 1 | `*:*` (Universal technical wildcard — Superadmin) |
| **2** | `institutions` | 4 | `institutions:read`, `institutions:create`, `institutions:update`, `institutions:delete` |
| **3** | `users` | 5 | `users:read`, `users:create`, `users:create_rector`, `users:update`, `users:delete` |
| **4** | `academic_years` | 5 | `academic_years:read`, `academic_years:create`, `academic_years:update`, `academic_years:close`, `academic_years:delete` |
| **5** | `academic_periods`| 4 | `academic_periods:read`, `academic_periods:create`, `academic_periods:update`, `academic_periods:close` |
| **6** | `grades` | 3 | `grades:read`, `grades:write`, `grades:manage` |
| **7** | `subjects` | 4 | `subjects:read`, `subjects:create`, `subjects:update`, `subjects:delete` |
| **8** | `groups` | 5 | `groups:read`, `groups:create`, `groups:update`, `groups:delete`, `groups:assign_director` |
| **9** | `teachers` | 4 | `teachers:read`, `teachers:create`, `teachers:update`, `teachers:delete` |
| **10**| `students` | 4 | `students:read`, `students:create`, `students:update`, `students:delete` |
| **11**| `guardians` | 4 | `guardians:read`, `guardians:create`, `guardians:update`, `guardians:link_student` |
| **12**| `enrollments` | 5 | `enrollments:read`, `enrollments:create`, `enrollments:transfer`, `enrollments:withdraw`, `enrollments:delete` |
| **13**| `academic_assignments`| 4 | `academic_assignments:read`, `academic_assignments:create`, `academic_assignments:update`, `academic_assignments:delete` |
| **14**| `virtual_classrooms`| 4 | `virtual_classrooms:read`, `virtual_classrooms:create`, `virtual_classrooms:join`, `virtual_classrooms:manage` |
| **15**| `recordings` | 3 | `recordings:read`, `recordings:manage`, `recordings:delete` |
| **16**| `activities` | 6 | `activities:read`, `activities:create`, `activities:update`, `activities:publish`, `activities:close`, `activities:delete` |
| **17**| `submissions` | 4 | `submissions:read`, `submissions:create`, `submissions:update`, `submissions:return` |
| **18**| `attendance` | 2 | `attendance:read`, `attendance:write` |
| **19**| `planning` | 4 | `planning:read`, `planning:create`, `planning:update`, `planning:delete` |
| **20**| `communications` | 5 | `communications:read`, `communications:create`, `communications:update`, `communications:publish`, `communications:delete` |
| **21**| `news` | 5 | `news:read`, `news:create`, `news:update`, `news:publish`, `news:delete` |
| **22**| `incidents` | 4 | `incidents:read`, `incidents:create`, `incidents:update`, `incidents:close` |
| **23**| `siee_policies` | 2 | `siee_policies:read`, `siee_policies:manage` |
| **24**| `evaluations` | 6 | `evaluations:read`, `evaluations:grade`, `evaluations:adjust`, `evaluations:close_period`, `evaluations:reopen_period`, `evaluations:recovery` |
| **25**| `report_cards` | 2 | `report_cards:read`, `report_cards:read_group` |
| **26**| `promotions` | 3 | `promotions:preview`, `promotions:execute`, `promotions:read` |
| **TOTAL** | **26 Modules** | **102** | **102 Total Canonical Atomic Permissions** |

---

## 10. VERIFIED Role-Permission Counts

### Baseline Verification Table

| Metric | Previous Report | Verified Current Source | Corrected Value | Source Reference |
| :--- | :---: | :---: | :---: | :--- |
| **Canonical permissions** | 73 | Programmatic count | **102** | `rbac_bootstrap_service.py:CANONICAL_PERMISSIONS` |
| **NATIONAL_ADMIN permissions** | 48 | Programmatic count | **72** | `rbac_bootstrap_service.py:ROLE_PERMISSIONS_CONFIG` |
| **System roles** | 11 | Programmatic count | **11** | `CANONICAL_ROLES` in `rbac_bootstrap_service.py` |
| **Backend routers reviewed** | 27 | Source file count | **27** | `backend/app/api/v1/endpoints/*.py` (excl. `__init__.py`) |
| **Endpoints with `_resolve_institution_id`** | 18 | Source file count | **18** | `backend/app/api/v1/endpoints/*.py` |
| **Backend test suites** | 52 (raw `.py` files)| Repository count | **50** | `backend/tests/test_*.py` (52 total incl. setup files) |
| **Frontend test suites** | 19 (raw files) | Repository count | **18** | `frontend/src/test/*.test.ts*` (19 total incl. setup) |

### Complete Role-Permission Seed Mapping (`ROLE_PERMISSIONS_CONFIG`)

| # | Role Identifier | Assigned Permissions | Wildcard Usage | Effective Capabilities |
| :-: | :--- | :-: | :---: | :--- |
| **1** | `superadmin` | 1 | `*:*` (Universal) | Global technical bypass across all endpoints; unrestricted permission check |
| **2** | `national_admin` | **72** | None | 72 explicit permission strings spanning 17 functional modules |
| **3** | `department_admin` | **17** | None | 17 read-only permissions across institutions and territorial resources |
| **4** | `municipality_admin`| **17** | None | 17 read-only permissions across institutions and local resources |
| **5** | `rector` | **90** | None | Full school governance: SIEE, calendar closure, staff, students, enrollments |
| **6** | `institution_admin` | **90** | None | Identical to Rector (technical alias) |
| **7** | `coordinator` | **82** | None | Operational management: academic load, groups, coexistence (excludes closure/deletion) |
| **8** | `academic_coordinator`| **82** | None | Identical to Coordinator |
| **9** | `teacher` | **45** | None | Pedagogical actions: activities, SIEE grading, attendance, observations |
| **10**| `student` | **19** | None | Self-service: homework submission, reading grades, attendance, joining classes |
| **11**| `guardian` | **12** | None | Family tracking: reading child records, attendance, bulletins, circulars |

### Conceptual Clarification
- **Catalog Count (102):** Total distinct permission tuples defined in the platform.
- **National Admin Assignment (72):** Specific permissions mapped to `national_admin`. Does not include 30 school-internal pedagogical/evaluation permissions (`activities` [6], `attendance` [2], `evaluations` [6], `planning` [4], `promotions` [3], `report_cards` [2], `siee_policies` [2], `submissions` [4], and wildcard [1]).
- **Wildcard vs. Explicit Permissions:** `superadmin` has 1 rule (`*:*`) evaluated dynamically by `has_permission()`. `national_admin` has 72 explicit strings and zero wildcard permissions.

---

## 11. Functional Preservation Matrix

The following matrix documents existing functional capabilities, tracing endpoints, services, roles, and verification status:

| Funcionalidad existente | Endpoint / UI | Operación | Rol actual | Rol correcto | Autoridad | Alcance actual | Alcance correcto | Permiso actual | Permiso necesario | Conservar | Riesgo | Evidencia | Estado Verificación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **Aprovisionar Institución** | `POST /institutions` | Alta DANE/DUE | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Operador | Nacional | Nacional | `institutions:create` | `institutions:create` | **SÍ** | Alto | `institutions.py:126`, `test_institution_provisioning.py` | VERIFIED BY TEST |
| **Invitar Rector** | `POST /institutions/{id}/rector-invitation` | Emitir token un solo uso | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Nombramiento | Nacional | Nacional | `users:create` | `users:create_rector` | **SÍ** | Crítico | `institutions.py:680`, `test_rbac_governance_and_rector_invitation.py` | VERIFIED BY TEST |
| **Sucesión de Rectoría** | `POST /institutions/{id}/rector/revoke` | Revocar y habilitar nuevo | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Nombramiento | Nacional | Nacional | `users:create` | `users:create_rector` | **SÍ** | Crítico | `institutions.py:729`, `test_rector_succession.py` | VERIFIED BY TEST |
| **Crear Año Lectivo** | `POST /academic-years` | Apertura calendario | `rector`, `coordinator`, `national_admin`* | `rector`, `institution_admin` | Consejo Directivo | Tenant / Nacional* | Institucional | `academic_years:create`| `academic_years:create`| **SÍ** | Medio | `academic_years.py:63`, `test_academic_api.py` | VERIFIED BY TEST |
| **Cerrar Año Lectivo** | `POST /academic-years/{id}/close` | Clausura y archivo anual | `rector`, `national_admin`* | `rector`, `institution_admin` | Rectoría Oficial | Tenant / Nacional* | Institucional | `academic_years:close` | `academic_years:close` | **SÍ** | Alto | `academic_years.py:239`, `test_academic_api.py` | VERIFIED BY TEST |
| **Crear Perfil Docente** | `POST /teachers` | Registrar docente en planta | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Directiva escolar | Tenant / Nacional* | Institucional | `teachers:create` | `teachers:create` | **SÍ** | Medio | `teachers.py:68`, `test_teacher_account_provisioning.py` | VERIFIED BY TEST |
| **Aprovisionar Cuenta Docente** | `POST /teachers/{id}/account/provision` | Crear credenciales y token | `rector`, `coordinator` | `rector`, `coordinator` | Directiva escolar | Institucional | Institucional | `teachers:create` | `teachers:create` | **SÍ** | Medio | `teachers.py:180`, `test_teacher_account_provisioning.py` | VERIFIED BY TEST |
| **Crear Estudiante (SIMAT)**| `POST /students` | Registro de ficha civil | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `students:create` | `students:create` | **SÍ** | Medio | `students.py:64`, `test_identity_family_lifecycle.py` | VERIFIED BY TEST |
| **Aprovisionar Cuenta Alumno** | `POST /students/{id}/account/provision`| Crear usuario y credencial | `rector`, `coordinator` | `rector`, `coordinator` | Secretaría académica | Institucional | Institucional | `students:create` | `students:create` | **SÍ** | Medio | `students.py:180`, `test_identity_family_lifecycle.py` | VERIFIED BY TEST |
| **Registrar Acudiente Civil**| `POST /guardians` | Ficha civil acudiente | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Registro escolar | Tenant / Nacional* | Institucional | `guardians:create` | `guardians:create` | **SÍ** | Medio | `guardians.py:64`, `test_guardian_onboarding.py` | VERIFIED BY TEST |
| **Vincular Acudiente ↔ Alumno**| `POST /students/{id}/guardians/{gid}`| Asociación civil formal | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `guardians:link_student`| `guardians:link_student`| **SÍ** | Alto | `students.py:324`, `test_identity_family_lifecycle.py` | VERIFIED BY TEST |
| **Auto-Activación Acudiente**| `POST /auth/guardians/accept-activation`| Verificación y password | Público (Anónimo) | Familiar verificado | Familiaridad civil | Nacional | Nacional | N/A (Token) | N/A (Token) | **SÍ** | Alto | `auth.py:270`, `test_guardian_onboarding.py` | VERIFIED BY TEST |
| **Crear Grupo / Salón** | `POST /groups` | Cursos y cupos | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Organización escolar | Tenant / Nacional* | Institucional | `groups:create` | `groups:create` | **SÍ** | Bajo | `groups.py:60`, `test_groups_and_actors_models.py` | VERIFIED BY TEST |
| **Asignar Carga Docente** | `POST /academic-assignments` | Docente + Asignatura + Grupo | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Coordinación académica | Tenant / Nacional* | Institucional | `academic_assignments:create`| `academic_assignments:create`| **SÍ** | Medio | `academic_assignments.py:60`, `test_enrollments_and_assignments.py`| VERIFIED BY TEST |
| **Matricular Alumno** | `POST /enrollments` | Matrícula en grupo activo | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `enrollments:create` | `enrollments:create` | **SÍ** | Medio | `enrollments.py:60`, `test_enrollments_and_assignments.py`| VERIFIED BY TEST |
| **Traslado de Salón** | `POST /transfers` | Cambio de grupo interno | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `enrollments:transfer`| `enrollments:transfer`| **SÍ** | Bajo | `transfers.py:60`, `test_academic_api.py` | VERIFIED BY TEST |
| **Crear Actividad Pedagógica**| `POST /teacher/activities` | Taller / Tarea / Examen | `teacher` | `teacher` | Autonomía docente | Carga asignada | Carga asignada | `activities:create` | `activities:create` | **SÍ** | Crítico | `teacher_portal.py:260`, `test_teacher_portal_api.py` | VERIFIED BY TEST |
| **Calificar Entregas** | `PUT /teacher/activities/{id}/grades` | Asentar nota de actividad | `teacher` | `teacher` | Evaluación docente | Carga asignada | Carga asignada | `grades:write` | `grades:write` | **SÍ** | Crítico | `teacher_portal.py:460`, `test_student_submissions_api.py` | VERIFIED BY TEST |
| **Registrar Asistencia Diaria**| `POST /teacher/groups/{id}/attendance`| Control de asistencia | `teacher` | `teacher` | Control de aula | Salón asignado | Salón asignado | `attendance:write` | `attendance:write` | **SÍ** | Alto | `teacher_portal.py:530`, `test_teacher_portal_api.py` | VERIFIED BY TEST |
| **Planeación Curricular** | `POST /teacher/planning` | Unidades y competencias | `teacher` | `teacher` | Pedagógica | Carga asignada | Carga asignada | `planning:create` | `planning:create` | **SÍ** | Bajo | `teacher_portal.py:600`, `test_teacher_portal_api.py` | VERIFIED BY TEST |
| **Parametrizar SIEE** | `POST /siee-policies` | Escala y reglas de notas | `rector`, `institution_admin` | `rector`, `institution_admin` | Consejo Directivo | Institucional | Institucional | `siee_policies:manage` | `siee_policies:manage` | **SÍ** | Crítico | `siee_policies.py:60`, `test_siee_and_evaluations_api.py` | VERIFIED BY TEST |
| **Asentar Notas de Período**| `POST /evaluations/grade` | Planilla oficial SIEE | `teacher`, `rector`, `coordinator` | `teacher` (Directivos: adjust) | Calificación oficial | Carga asignada | Carga asignada | `evaluations:grade` | `evaluations:grade` | **SÍ** | Crítico | `evaluation_grades.py:180`, `test_siee_and_evaluations_api.py` | VERIFIED BY TEST |
| **Cerrar Período Académico** | `POST /evaluations/periods/{id}/close` | Bloqueo inmutable de notas | `rector`, `coordinator` | `rector`, `institution_admin` | Rectoría / Dirección | Institucional | Institucional | `evaluations:close_period`| `evaluations:close_period`| **SÍ** | Crítico | `evaluation_grades.py:352`, `test_siee_and_evaluations_api.py` | VERIFIED BY TEST |
| **Emitir Boletín Oficial** | `GET /evaluations/report-card/{id}` | Calificaciones oficiales | `rector`, `coordinator`, `teacher`, `student`, `guardian` | Todos autorizados | Transparencia escolar | Según rol/parentesco | Según rol/parentesco | `report_cards:read` | `report_cards:read` | **SÍ** | Alto | `evaluation_grades.py:460`, `OfficialReportCard.test.tsx` | VERIFIED BY TEST |
| **Simular Promoción Escolar**| `POST /promotions/preview` | Algoritmo SIEE fin de año | `rector`, `coordinator`, `teacher` | `rector`, `coordinator` | Comisión de Evaluación | Institucional | Institucional | `promotions:preview` | `promotions:preview` | **SÍ** | Alto | `academic_promotions.py:60`, `test_promotion_governance.py` | VERIFIED BY TEST |
| **Asentar Acta de Promoción** | `POST /promotions/commit` | Cierre definitivo y actas | `rector`, `institution_admin` | `rector`, `institution_admin` | Rectoría Oficial | Institucional | Institucional | `promotions:execute` | `promotions:execute` | **SÍ** | Crítico | `academic_promotions.py:100`, `test_promotion_governance.py` | VERIFIED BY TEST |
| **Crear Clase Virtual** | `POST /virtual-classrooms` | Sala BigBlueButton | `rector`, `coordinator`, `teacher`, `national_admin`* | `rector`, `coordinator`, `teacher` | Convocatoria pedagógica | Tenant / Asignación | Tenant / Asignación | `virtual_classrooms:create`| `virtual_classrooms:create`| **SÍ** | Alto | `virtual_classrooms.py:71`, `test_virtual_classroom_api.py` | VERIFIED BY TEST |
| **Unirse a Clase Virtual** | `POST /virtual-classrooms/{id}/join`| Acceso MODERATOR / VIEWER | `rector`, `teacher`, `student`, `national_admin`* | Docente (Mod), Alumno (View) | Asistencia a clase | Salón / Matrícula | Salón / Matrícula | `virtual_classrooms:join` | `virtual_classrooms:join` | **SÍ** | Crítico | `virtual_classrooms.py:165`, `test_virtual_classroom_api.py` | VERIFIED BY TEST |
| **Emitir Circular** | `POST /communications` | Comunicado con acuse | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Dirección escolar | Institucional | Institucional | `communications:create`| `communications:create`| **SÍ** | Medio | `communications.py:60`, `test_institutional_communications_api.py`| VERIFIED BY TEST |
| **Firmar Acuse de Circular** | `POST /communications/{id}/acknowledge`| Sello digital de lectura | `student`, `guardian` | `student`, `guardian` | Notificación legal | Propio / Tutorado | Propio / Tutorado | `communications:read` | `communications:read` | **SÍ** | Medio | `communications.py:220`, `test_institutional_communications_api.py`| VERIFIED BY TEST |
| **Registrar Falta Observador**| `POST /incidents` | Situación Ley 1620 | `rector`, `coordinator`, `teacher`, `national_admin`* | `rector`, `coordinator`, `teacher` | Comité Convivencia | Institucional / Asign. | Institucional / Asign. | `incidents:create` | `incidents:create` | **SÍ** | Crítico | `incidents.py:60`, `test_coexistence_incidents_api.py` | VERIFIED BY TEST |

*\* Permiso presente en `ROLE_PERMISSIONS_CONFIG['national_admin']`, pero la invocación directa falla cerrado en tiempo de ejecución (`403 Forbidden`) cuando `institution_id = NULL`.*

---

## 12. Critical Existing Functionality

The following 18 capabilities represent verified business workflows in PEVN that must be preserved without disruption:
1. **National Catalog Management:** Provisioning and maintaining educational institutions and DANE sedes.
2. **Cryptographic Rector Invitations:** Generation of single-use, cryptographically signed onboarding tokens for verified Rectors.
3. **Rector Succession & Title Revocation:** Revoking outgoing Rector titularity and re-issuing credentials for incoming leadership.
4. **Academic Year & Calendar Lifecycles:** Configuration, activation, and formal closing of academic years.
5. **Teacher Onboarding & Account Provisioning:** Linking teachers to school faculties and generating user credentials.
6. **SIMAT Student Registration & Account Provisioning:** Registering student civil identity and provisioning student portal credentials.
7. **Guardian Civil Registration & Public Onboarding:** Registering legal guardians and handling public token verification and password initialization.
8. **Student ↔ Guardian Kinship Binding:** Formal association between guardians and students with legal relationship types.
9. **Curricular Workload Assignment:** Linking teachers, subjects, and groups with specific hourly intensity.
10. **SIMAT Student Enrollment & Section Transfers:** Placing students into active groups and managing internal classroom transfers.
11. **Teacher Pedagogical Activities:** Creating, updating, publishing, closing, and grading learning activities and assignments.
12. **Student Submission Lifecycle:** Multi-format file attachments with Magic Bytes validation and assignment delivery.
13. **Daily Attendance Tracking:** Recording daily student attendance with official status codes.
14. **SIEE Grading Scale Parameterization:** Institutional grading policies, thresholds, and performance rubrics.
15. **SIEE Period Grade Settlement:** Submitting formal period marks with mandatory pedagogical justifications for overrides.
16. **Period Grade Locking:** Sealing academic periods to guarantee grade immutability.
17. **Synchronous Virtual Classrooms:** Scheduling BigBlueButton sessions with differentiated MODERATOR and VIEWER roles.
18. **School Coexistence Observador (Ley 1620):** Logging Type I, II, and III disciplinary situations with commitments and resolution tracking.

---

## 13. NATIONAL_ADMIN Dependency Analysis

### Forensic Finding: The Rector Invitation Dependency Chain
Inspection of `backend/app/api/v1/endpoints/institutions.py` confirms that both:
- `POST /{institution_id}/rector-invitation` (Line 669)
- `POST /{institution_id}/rector/revoke` (Line 718)

enforce the FastAPI security dependency:
```python
auth: Annotated[AuthContextDep, Depends(require_permission("users", "create"))]
```
followed by the explicit role/scope check:
```python
if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
    raise AuthorizationError(
        "Solo administradores nacionales pueden emitir invitaciones para Rectores.",
        code="PERMISSION_DENIED",
    )
```

### Specialized Canonical Permission Availability
In `CANONICAL_PERMISSIONS` (`rbac_bootstrap_service.py`), the catalog already defines:
- `("users", "create", "Registrar nuevos usuarios en el sistema")`
- `("users", "create_rector", "Emitir invitación criptográfica para nuevo Rector")`

Both `users:create` and `users:create_rector` are currently assigned to `national_admin` in `ROLE_PERMISSIONS_CONFIG`.

### Functional Preservation Rule
- **CURRENT IMPLEMENTATION:** The endpoint controller checks `require_permission("users", "create")`.
- **CANONICAL SPECIALIZED PERMISSION AVAILABLE:** `users:create_rector` exists in the database catalog.
- **POTENTIAL FUTURE ALIGNMENT:** Evaluate whether the endpoint dependency should be refactored to `require_permission("users", "create_rector")`.
- **OWNER / IMPLEMENTATION DECISION REQUIRED:** An explicit decision is required before changing the endpoint signature.
- **CRITICAL RISK:** If `users:create` is stripped from `national_admin` prior to refactoring `institutions.py`, the Rector Invitation and Revocation endpoints will immediately fail with `403 Forbidden` (`PERMISSION_DENIED`). Functional preservation requires retaining `users:create` on `national_admin` until the endpoint dependency is updated.

---

## 14. SUPERADMIN Analysis

### Separation of Concerns: Authority vs. Visibility vs. Tenancy
- **Backend Authority:** Global technical root (`level: 100`, permissions: `["*:*"]`).
- **Data Scope:** National (`country_code="CO"`, `institution_id=None`).
- **Backend Tenancy Enforcement:** In `backend/app/api/v1/endpoints/*.py` (18 files), `_resolve_institution_id()` strictly requires an institutional context:
  ```python
  if current_user.institution_id is not None:
      return current_user.institution_id
  if institution_id_override is not None:
      # Validated against actor scope
      return institution_id_override
  raise AuthorizationError("Contexto institucional no disponible...", code="PERMISSION_DENIED")
  ```
  Consequently, when a `superadmin` invokes an institutional endpoint without passing `?institution_id=<UUID>`, the backend fails closed. This proves that `superadmin` is not automatically unauthorized, but rather constrained by tenant isolation rules.
- **Frontend Presentation Mismatch:**  
  `frontend/src/layouts/RootLayout.tsx` and `Dashboard.tsx` expose `/academic` and school management cards to `superadmin` without providing an institution selector. When clicked, API calls fail with 403.
- **Client-Side Bypass in `AuthContext.tsx`:**  
  `hasRole()` contains a short-circuit:
  ```typescript
  if (user.roles.includes('superadmin')) return true;
  ```
  This causes the client to display actor-specific portals (`/teacher`, `/student`, `/guardian`) to Superadmin, where no underlying teacher or student profile exists, leading to empty or error states.

### Architectural Options for Owner Decision (Neutral Representation)
- **Option A (Explicit Institution Context Selector):** Introduce a school selector in the UI (`?institution_id=<UUID>`). Superadmin retains global technical authority but operates within explicit institutional context.
- **Option B (Strict Platform Separation of Duties):** Restrict Superadmin strictly to platform infrastructure, catalog maintenance, and system logs. Forbid Superadmin from accessing school academic modules.
- **Option C (Retain Current Architecture):** Maintain current backend behavior; align frontend navigation so tenantless links are hidden.

---

## 15. Territorial Role Analysis

### Departmental and Municipal Administration (`department_admin`, `municipality_admin`)
- **Governmental Mandate:** Secretarías de Educación Departamentales (SED) and Municipales (SEM).
- **Security Level:** Level 80 (Departmental) and Level 70 (Municipal).
- **Assigned Permissions:** Exactly **17 read-only permissions** in `ROLE_PERMISSIONS_CONFIG`:
  `institutions:read`, `users:read`, `academic_years:read`, `academic_periods:read`, `grades:read`, `subjects:read`, `groups:read`, `teachers:read`, `students:read`, `guardians:read`, `enrollments:read`, `academic_assignments:read`, `virtual_classrooms:read`, `recordings:read`, `communications:read`, `news:read`, `incidents:read`.
- **Presentation / Navigation Mismatch:**  
  In `frontend/src/pages/Dashboard.tsx`, the directive check:
  ```typescript
  const isDirective = user?.roles.some((r) =>
    ['superadmin', 'national_admin', 'department_admin', 'municipality_admin', 'rector', 'coordinator'].includes(r)
  );
  ```
  includes territorial administrators. As a result, SED/SEM users see operational school management cards (e.g., "Registrar Estudiante", "Asignar Carga") that fail with `403 Forbidden` when clicked.
- **Clarification:** This is a **presentation and navigation mismatch**, not an exploitable backend security bypass. The backend authorization layer correctly enforces read-only boundaries and tenant isolation.

---

## 16. Institutional Role Analysis

### Rector and Institutional Administrator (`rector`, `institution_admin`)
- **Authority:** Chief Executive of the Educational Institution (Ley 115 de 1994, Ley 715 de 2001).
- **Security Level:** 60 / 70.
- **Assigned Permissions:** Exactly **90 permissions** in `ROLE_PERMISSIONS_CONFIG`.
- **Exclusive Capabilities:**
  - Closing academic years (`academic_years:close`).
  - SIEE grading scale approval and policy management (`siee_policies:manage`).
  - Deleting teachers or students (`teachers:delete`, `students:delete`).
  - Final execution of promotion records (`promotions:execute`).
  - Assigning group homeroom directors (`groups:assign_director`).

### Academic Coordinator and Coexistence Coordinator (`academic_coordinator`, `coordinator`)
- **Authority:** Operational school management, academic scheduling, and school coexistence (Ley 1620 de 2013).
- **Security Level:** 50 / 60.
- **Assigned Permissions:** Exactly **82 permissions** in `ROLE_PERMISSIONS_CONFIG`.
- **Relationship to Rector:** Exactly 8 permissions fewer than Rector. Coordinators manage operational workflows (workload assignments, enrollments, groups, daily attendance, incidents) but are barred from irreversible statutory closures (annual closure, student deletion, director assignment).

---

## 17. Teacher Analysis

- **Role Identifier:** `teacher` (Level 30 / 50).
- **Assigned Permissions:** Exactly **45 permissions** in `ROLE_PERMISSIONS_CONFIG`.
- **Academic Scope Boundary:**  
  Enforced by `TeacherPortalService` and validated in `test_teacher_academic_scope.py`. A teacher can only query or mutate groups and subjects linked to their active `AcademicAssignment`. Invocations targeting unassigned groups return `403 Forbidden` or empty sets.
- **Pedagogical Capabilities:**
  - Creating, updating, publishing, closing, and deleting assigned activities.
  - Submitting period grades via official SIEE planilla (`evaluations:grade`), requiring mandatory pedagogical justification (`adjustment_reason`) when overriding computed grades.
  - Recording daily attendance (`attendance:write`).
  - Authoring Type I, II, and III coexistence notes in the student Observador under Ley 1620.
  - Initiating BigBlueButton virtual sessions as `MODERATOR`.

---

## 18. Student Analysis

- **Role Identifier:** `student` (Level 10 / 20).
- **Assigned Permissions:** Exactly **19 permissions** in `ROLE_PERMISSIONS_CONFIG`.
- **Anti-IDOR Protection:**  
  Enforced by `StudentPortalService` and verified in `test_student_portal_api.py`. The backend resolves the student profile via `student.user_id = current_user.id`. Any attempt to access another student's academic records fails closed with `404 Not Found`.
- **Self-Service Capabilities:**
  - Uploading homework submissions (PDF, DOCX, ZIP) with Magic Bytes inspection and 10 MB limit (`test_activity_resources_and_storage.py`).
  - Reviewing published grades and official evaluation report cards (`report_cards:read`).
  - Signing digital acknowledgments for institutional circulars (`communications:read`).
  - Joining scheduled virtual classes as `VIEWER`.

---

## 19. Guardian Analysis

- **Role Identifier:** `guardian` (Level 10).
- **Assigned Permissions:** Exactly **12 permissions** in `ROLE_PERMISSIONS_CONFIG`.
- **Civil Kinship Boundary:**  
  Enforced by `GuardianPortalService` and verified in `test_guardian_tenant_isolation.py`. Access to student records is gated strictly through the `student_guardians` relationship table. Unlinked student records are inaccessible.
- **Parental Capabilities:**
  - Monitoring academic performance and period grades for linked children.
  - Reviewing attendance alerts and coexistence observations.
  - Signing institutional circulars on behalf of the family.
  - Multi-child switcher allowing seamless navigation across enrolled siblings.
- **Strict Prohibitions:** Guardians have zero homework submission or grading permissions.

---

## 20. Route / UI Authorization Analysis

| Route | Auth Guard | Role Guard in App.tsx | Context Required | Backend Protection | Frontend Visibility | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `/dashboard` | YES | None | None | User profile endpoint | Top bar / Direct | Coherent |
| `/admin/institutions` | YES | `superadmin`, `national_admin` | National | `institutions:read` + Scope | Nav bar (National) | Territorial admins excluded from directory |
| `/analytics/territorial`| YES | `institutions:read` | Territorial | `analytics` + Scope check | Nav bar (Erron. to Rector) | Presentation mismatch (Exposed via `institutions:read`) |
| `/academic` | YES | **NONE** | **YES (`institution_id`)** | 18 controllers fail closed | Nav bar (Erron. to Superadmin)| Route guard missing in App.tsx; fails closed in backend |
| `/virtual-classrooms` | YES | `virtual_classrooms:read` | **YES (`institution_id`)** | Controller fails closed | Nav bar (Erron. to National) | Presentation mismatch without institution context |
| `/teacher` | YES | `teacher` | **YES (Teacher Profile)** | TeacherPortalService fails closed | Nav bar (Teacher) | Superadmin bypass via `AuthContext.tsx` |
| `/student` | YES | `student` | **YES (SIMAT Profile)** | StudentPortalService fails closed | Nav bar (Student) | Superadmin bypass via `AuthContext.tsx` |
| `/guardian` | YES | `guardian` | **YES (Guardian Profile)**| GuardianPortalService fails closed | Nav bar (Guardian) | Superadmin bypass via `AuthContext.tsx` |

### Key Distinction: Route Guard Deficiency vs. Security Bypass
The lack of an explicit role guard on `/academic` in `App.tsx` allows unauthorized roles to load the frontend view shell. However, **this does not constitute a backend security bypass**. The 18 underlying API controllers enforce `_resolve_institution_id()`, causing all data fetching to fail closed with `403 Forbidden`. The defect is purely a presentation-layer and navigation mismatch.

---

## 21. Backend Authorization Analysis

The backend enforces defense-in-depth through four layered checkpoints:
1. **Dependency Injection:** `Depends(require_permission("resource", "action"))` verifies atomic permissions.
2. **Context Resolution:** `_resolve_institution_id(auth, current_user, institution_id_override)` resolves and validates institutional tenancy.
3. **Scope Containment:** `scope_contains(actor_scope, target_scope)` enforces DANE geographical boundaries.
4. **Domain Services:** Validate business relationships (e.g., teacher active workload, student enrollment, guardian kinship).

The backend authorization layer is technically robust and fails closed. All reported UX anomalies originate in frontend shell navigation or preliminary seed catalog misalignments.

---

## 22. Permission Functional Dependency Matrix

```
institutions:create ──────► POST /institutions ──────────────► InstitutionService ────────► DANE Provisioning
users:create ─────────────► POST /institutions/{id}/rector-invitation ► RectorOnboardingService ──► Rector Invitation
teachers:create ──────────► POST /teachers ──────────────────► TeacherService + UserService ──► Teacher Provisioning
students:create ──────────► POST /students ──────────────────► StudentService + UserService ──► SIMAT Student Creation
guardians:link_student ───► POST /students/{id}/guardians/{gid} ► GuardianService ──────────► Civil Kinship Binding
academic_years:create ────► POST /academic-years ────────────► AcademicYearService ───────► Academic Calendar Setup
groups:create ────────────► POST /groups ────────────────────► GroupService ──────────────► Course & Section Setup
academic_assignments:create ► POST /academic-assignments ────► AssignmentService ────────► Teacher Workload
enrollments:create ───────► POST /enrollments ───────────────► EnrollmentService ────────► Student Enrollment
activities:create ────────► POST /teacher/activities ────────► ActivityService ──────────► Pedagogical Tasks
evaluations:grade ────────► POST /evaluations/grade ─────────► EvaluationService ────────► SIEE Grade Planilla
evaluations:close_period ─► POST /evaluations/periods/{id}/close ► EvaluationService ─────► SIEE Period Lock
virtual_classrooms:join ──► POST /virtual-classrooms/{id}/join ► MeetingService ─────────► BBB Live Classroom
incidents:create ─────────► POST /incidents ─────────────────► CoexistenceIncidentService ► Ley 1620 Incident
```

---

## 23. Tenant / Scope Analysis

- **Institutional Tenancy:** Enforced by foreign keys (`institution_id`) across all school domain tables. Direct queries without tenant matching are prohibited.
- **Territorial Containment:** Governed by DANE geographic codes (`department_id`, `municipality_id`). A departmental admin cannot query data belonging to a sibling department.
- **National Scope Behavior:** National accounts (`country_code="CO"`, `institution_id=None`) must supply an explicit `institution_id_override` to operate tenant-scoped endpoints. Without this override, the backend fails closed.

---

## 24. Resource Authorization Analysis

- **Teacher Workload Scope:** Validated against `academic_assignments`. Access to groups outside the teacher's active assignments is rejected.
- **Student Anti-IDOR Scope:** Gated by `student.user_id = current_user.id`. Cross-student inspection is blocked.
- **Guardian Kinship Scope:** Gated by the `student_guardians` relationship table. Unlinked students are strictly inaccessible.
- **Controlled Runtime Validation:** Verified via automated regression suites (`test_teacher_academic_scope.py`, `test_student_portal_api.py`, `test_guardian_tenant_isolation.py`).

---

## 25. Security Findings

1. **Backend Tenancy Isolation Fails Closed:** All 18 institutional domain controllers enforce `_resolve_institution_id()` and fail closed with `403 Forbidden` when institutional context is missing.
2. **Presentation-Layer Decoupling:** The frontend shell renders navigation elements for institutional modules to national and territorial users whose `institution_id` is `NULL`, causing runtime 403 errors upon interaction.
3. **Client-Side SuperAdmin Role Bypass:** The `hasRole()` short-circuit in `frontend/src/context/AuthContext.tsx` bypasses functional role checks on the client, rendering irrelevant portal views to Superadmin.
4. **Seed Catalog Disconnect:** `national_admin` holds 72 permissions in `rbac_bootstrap_service.py`, whereas `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` specifies a macro/census mandate. This contradiction requires an explicit owner decision.
5. **Route Guard Omission in `App.tsx`:** The `/academic` route lacks an explicit role guard in `App.tsx`, representing a client-side navigation defect that is safely blocked by backend authorization.

---

## 26. Documentation Contradictions

| Contradiction ID | Source A | Source B | Actual Code Implementation | Category | Owner Decision Required? |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **CONT-01** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.2 (MEN cannot edit grades or local students) | `PHASE_3_RBAC_MATRIX.md` §3 (National Admin has broad CRUD) | `rbac_bootstrap_service.py` assigns 72 permissions to `national_admin` | A & C | **YES (Owner Decision 02)** |
| **CONT-02** | `docs/AUTHORIZATION.md` §1 (Multi-tenant containment mandatory) | `RootLayout.tsx` lines 89–101 | Navbar exposes `/academic` to `superadmin` without institution context | A & C | **YES (Owner Decision 01)** |
| **CONT-03** | `CANONICAL_PERMISSIONS` defines `users:create_rector` | `institutions.py` lines 680, 729 | Controllers enforce `require_permission("users", "create")` | E | **NO (Endpoint Refactor Alignment)** |
| **CONT-04** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.3 (Territorial admins are macro-only) | `Dashboard.tsx` line 337 | `isDirective` includes territorial admins | A & E | **NO (UI Presentation Alignment)** |
| **CONT-05** | Previous Audit Draft (73 canonical perms, 48 NA perms) | `rbac_bootstrap_service.py` | Exactly 102 canonical permissions and 72 NA permissions | B | **NO (Reconciled in this Report)** |

### Classification Taxonomy
- **Category A:** Current implementation mismatch.
- **Category B:** Documentation mismatch (reconciled).
- **Category C:** Owner decision required.
- **Category D:** Evidence insufficient.
- **Category E:** Future implementation alignment.

---

## 27. Functionality That MUST Be Preserved

The following 18 capabilities represent working, verified platform features that must remain inviolable during future RBAC refactoring:
1. National institution provisioning (`POST /institutions`).
2. Single-use cryptographic Rector invitations (`POST /institutions/{id}/rector-invitation`).
3. Rector titularity revocation and succession (`POST /institutions/{id}/rector/revoke`).
4. Academic year creation, activation, and formal closure (`/academic-years`).
5. Teacher faculty registration and account credential provisioning (`/teachers`).
6. Student SIMAT registration and credential provisioning (`/students`).
7. Guardian registration and public cryptographic self-activation (`/guardians`, `/auth/guardians/accept-activation`).
8. Student ↔ Guardian kinship binding (`POST /students/{id}/guardians/{gid}`).
9. Curricular workload assignment linking teachers, groups, and subjects (`/academic-assignments`).
10. Student enrollment and internal classroom transfers (`/enrollments`, `/transfers`).
11. Teacher pedagogical activity creation, publication, and grading (`/teacher/activities`).
12. Student homework file submissions with Magic Bytes validation (`/student/activities/{id}/submissions`).
13. Daily student attendance tracking (`/teacher/groups/{id}/attendance`).
14. SIEE institutional grading scale parameterization (`/siee-policies`).
15. SIEE period grade settlement with override justifications (`/evaluations/grade`).
16. Academic period grade locking and immutability (`/evaluations/periods/{id}/close`).
17. BigBlueButton virtual classroom sessions with MODERATOR/VIEWER roles (`/virtual-classrooms`).
18. School coexistence incident logging under Ley 1620 (`/incidents`).

---

## 28. Scope Corrections Proposed for Future Work

*(PROPOSED TARGETS — FOR FUTURE IMPLEMENTATION ONLY)*
- **National Admin Academic Operations:** Scope operational queries to read-only inspection, requiring an explicit `?institution_id=<UUID>` query parameter.
- **Territorial Directory Filtering:** Filter `/admin/institutions` to display only institutions situated within the administrator's department or municipality.
- **Territorial Macro Analytics:** Constrain `/analytics/territorial` so institutional rectors cannot view national-level macro aggregates.

---

## 29. Role Corrections Proposed for Future Work

*(PROPOSED TARGETS — FOR FUTURE IMPLEMENTATION ONLY)*
- **Rector Invitation Endpoint Alignment:** Update `POST /institutions/{id}/rector-invitation` and `POST /institutions/{id}/rector/revoke` to require `users:create_rector` instead of `users:create`.
- **National Admin Permission Re-alignment:** Following Owner Decision 02, align `ROLE_PERMISSIONS_CONFIG['national_admin']` to remove local mutation permissions that conflict with the approved governance model.

---

## 30. Route Guard Corrections Proposed for Future Work

*(PROPOSED TARGETS — FOR FUTURE IMPLEMENTATION ONLY)*
- **Protect `/academic` in `App.tsx`:** Assign explicit role guard: `roles={['rector', 'coordinator', 'institution_admin', 'academic_coordinator']}`.
- **Refactor `hasRole()` in `AuthContext.tsx`:** Remove the global `superadmin` short-circuit on actor-specific portals (`/teacher`, `/student`, `/guardian`).
- **Align Navbar Visibility in `RootLayout.tsx`:** Base `/analytics/territorial` visibility on geographic scope (`user.scope.is_national || user.scope.department_id || user.scope.municipality_id`).
- **Align Directive Cards in `Dashboard.tsx`:** Exclude territorial roles from school management cards.

---

## 31. Owner Decisions Required

### OWNER DECISION 01: SuperAdmin Operation of Tenant-Scoped Modules
- **Context:** How should `SUPER_ADMIN` interact with institutional modules (Academic, Classrooms)?
- **Current Behavior:** Global authority `*:*` exists, but tenantless API invocations fail with `403 Forbidden` (`Contexto institucional no disponible`).
- **Options for Owner Determination:**
  - *Option A:* Implement an Institution Context Selector in the UI. Superadmin selects an institution (`?institution_id=<UUID>`) to perform administrative tasks within an explicit tenant context.
  - *Option B:* Restrict Superadmin strictly to infrastructure, catalog provisioning, and audit logs. School-level academic modules remain inaccessible to Superadmin.
  - *Option C:* Retain current architecture and hide tenantless links in the frontend navigation shell.

### OWNER DECISION 02: National Admin (MEN) Operational Scope
- **Context:** Should `national_admin` retain local school mutation permissions?
- **Current Behavior:** 72 permissions assigned in `rbac_bootstrap_service.py` (including mutation of groups, students, enrollments, and incidents), conflicting with `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md`.
- **Options for Owner Determination:**
  - *Option A (Strict Least Privilege):* Prune local school mutation permissions from `national_admin`. Retain only national catalog governance, rector appointments, macro analytics, and read-only census audits.
  - *Option B (Broad Centralized Governance):* Retain operational permissions as emergency intervention powers, executable only when an explicit institution override is provided.
  - *Option C (Dedicated Technical Support Role):* Create a separate `technical_support` or `intervention_admin` role for school interventions, keeping `national_admin` strictly ministerial.

### OWNER DECISION 03: Virtual Classroom & Incident National Auditing
- **Context:** Should national officials be permitted to join live school video classes or inspect individual student disciplinary records under Ley 1620?
- **Current Behavior:** Permissions `virtual_classrooms:join` and `incidents:read` are assigned to `national_admin` in `ROLE_PERMISSIONS_CONFIG`.
- **Options for Owner Determination:**
  - *Option A (Privacy-Preserving / Aggregated):* Restrict live classrooms and disciplinary records to institutional actors. National officials access only aggregated statistical indicators.
  - *Option B (Formal Auditing Mode):* Permit national officials to access individual classrooms and incidents strictly with an official audit ticket ID under Ley 1581 de 2012.

---

## 32. Future Implementation Plan

*(STAGED ROADMAP FOR APPROVED FUTURE IMPLEMENTATION)*

```
PHASE A: Backend Endpoint Dependency Alignment
  ├── Update invite_rector_endpoint to depend on users:create_rector
  ├── Update revoke_rector_endpoint to depend on users:create_rector
  └── Verification: test_rbac_governance_and_rector_invitation.py passes

PHASE B: RBAC Bootstrap Catalog Reconciliation
  ├── Implement Owner Decision 02 in rbac_bootstrap_service.py
  └── Verification: Re-seed test database and verify role-permission matrices

PHASE C: Frontend Route Guard & Context Hardening
  ├── Update RequireAuth.tsx with requireInstitutionContext
  ├── Add explicit role guard to /academic in App.tsx
  └── Remove global superadmin bypass from AuthContext.tsx

PHASE D: Presentation Shell Clean-Up
  ├── Align RootLayout.tsx navigation links with verified scopes
  └── Update Dashboard.tsx isDirective role filtering

PHASE E: Institution Context Switcher (SuperAdmin UX)
  ├── Implement school selector in InstitutionsView.tsx
  └── Propagate ?institution_id=<UUID> to academic controllers

PHASE F: Comprehensive Regression Testing
  ├── Run all 50 backend test suites (test_*.py)
  └── Run all 18 frontend test suites (*.test.ts*)

PHASE G: Controlled Runtime Validation
  ├── Multi-role manual walkthrough on local development servers
  └── Document evidence in final implementation report
```

---

## 33. Regression Protection Plan

To safeguard existing functionality during future refactoring:
1. **Rector Onboarding & Succession:** Execute `test_rbac_governance_and_rector_invitation.py` and `test_rector_succession.py` upon any modification to user permissions.
2. **Teacher Academic Scope:** Execute `test_teacher_academic_scope.py` to ensure workload isolation remains intact.
3. **Student Anti-IDOR:** Execute `test_student_portal_api.py` ensuring cross-student isolation is preserved.
4. **Guardian Kinship Boundary:** Execute `test_guardian_tenant_isolation.py` and `test_identity_family_lifecycle.py`.
5. **SIEE Evaluation Integrity:** Execute `test_siee_and_evaluations_api.py` ensuring period lock cannot be bypassed.
6. **Virtual Classroom Access:** Execute `test_virtual_classroom_api.py` ensuring non-enrolled users cannot join.

---

## 34. Evidence Index

- **Backend Endpoints:** 27 router files in `backend/app/api/v1/endpoints/*.py` (18 implementing `_resolve_institution_id()`).
- **Backend Tests:** 50 test suites matching `backend/tests/test_*.py` (52 files total).
- **Frontend Code:** `frontend/src/` (`App.tsx`, `RootLayout.tsx`, `Dashboard.tsx`, `AuthContext.tsx`, `RequireAuth.tsx`).
- **Frontend Tests:** 18 test suites matching `frontend/src/test/*.test.ts*` (19 files total).
- **Programmatic Verification:** Executed via automated repository inspection scripts.

---

## 35. Final Gate

```
========================================================================================
FINAL AUDIT GATE:
AUDIT PASS — DOCUMENTATION BASELINE CORRECTED — OWNER DECISIONS REQUIRED
========================================================================================
```

- **Permission counts verified:** Exactly 102 canonical permissions verified from source.
- **National Admin count verified:** Exactly 72 permissions verified from source.
- **Role counts verified:** Exactly 11 system roles verified from source.
- **Repository baseline recorded:** HEAD `bbd2ed9c0559fbe64e157a45c4b9130b2685b2da` confirmed.
- **Contradictions documented:** CONT-01 through CONT-05 objectively documented with neutral owner options.
- **Product code modified:** STRICTLY ZERO lines of product code modified.
- **RBAC behavior modified:** STRICTLY ZERO runtime RBAC policies or assignments changed.
- **Database migrations created:** STRICTLY ZERO migrations created.
- **API contracts altered:** STRICTLY ZERO API contracts altered.
- **Preserved functionality certified:** All 18 critical capabilities documented and protected.
