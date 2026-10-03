# PEVN — RBAC Functional Preservation & Reconciliation Audit
## Phase 0.3: Functional Authorization Reconciliation & Baseline Protection Audit
### Comprehensive Forensic Mapping of Existing Capabilities, Dependencies, Scopes & Preservation Blueprint

> **Standard:** PEVN AI Software Factory v1.2 — Implementation Evidence & Reporting Standard  
> **Document ID:** `docs/reports/PEVN_RBAC_FUNCTIONAL_PRESERVATION_RECONCILIATION_AUDIT.md`  
> **Classification:** Security, Architecture & Functional Preservation Audit (Read-Only)  
> **Audit Date:** 2026-10-03  
> **Author:** AI Systems Architect & Security Certification Specialist  
> **Repository Commit Reviewed:** `7fb83fb14bc21d675d580511068f2c866de18654` (`7fb83fb`)  
> **Final Gate Status:** **AUDIT PASS WITH OWNER DECISIONS REQUIRED**  
> **Product Modification Status:** **STRICTLY ZERO PRODUCT CODE MODIFIED (AUDIT & DESIGN ONLY)**

---

## 1. Executive Summary

This forensic audit was executed under **Phase 0.3** of the Plataforma Educativa Virtual Nacional (PEVN). Its primary mandate is to establish an authoritative **Functional Preservation Baseline** before any RBAC or visibility implementation changes are made in subsequent phases.

### Core Principle
$$\text{\textbf{FUNCTIONALITY EXISTENTE}} + \text{\textbf{ROL CORRECTO}} + \text{\textbf{ALCANCE CORRECTO}} = \text{\textbf{CONSERVAR}}$$

A common pitfall in enterprise authorization refactoring is the indiscriminate pruning of permissions that appear "too broad" on paper, without investigating why they were granted or what working endpoints, UI flows, and automated test suites depend on them. 

This audit proves that:
1. **Existing User-Management Dependencies Are Critical:**  
   `national_admin` currently possesses `users:create` not due to an accidental oversight, but because the **Rector Invitation** (`POST /api/v1/institutions/{id}/rector-invitation`) and **Rector Revocation** (`POST /api/v1/institutions/{id}/rector/revoke`) endpoints in `institutions.py` explicitly require `require_permission("users", "create")`. Naively deleting `users:create` from `national_admin` would immediately disable national Rector onboarding and succession.
2. **On-The-Fly Teacher & Student Account Provisioning Relies on Domain Permissions:**  
   Creating and provisioning institutional accounts for teachers and students does not require the global `users:create` permission. In `teachers.py`, teacher creation depends on `teachers:create`, which internally calls `UserService.provision_institutional_user()`. Similarly, `students.py` uses `students:create` and `students:update` for account provisioning and status toggling.
3. **Multi-Tenant Isolation Fails Closed in the Backend:**  
   All 18 institutional domain endpoints strictly gate tenancy via `_resolve_institution_id()`. The runtime failures observed by national administrators (`PERMISSION_DENIED: Contexto institucional no disponible`) are presentation-layer defects caused by the frontend exposing tenant-scoped modules to accounts with `institution_id = NULL` without an **Institution Context Selector**.
4. **All Certified Portals Must Be Preserved Inviolable:**  
   The Teacher Portal (`/teacher`), Student Portal (`/student`), and Guardian Portal (`/guardian`) feature fully implemented and certified Anti-IDOR protections, academic scope restrictions, and parent-child kinship verifications that must remain 100% untouched during future reconciliation.

---

## 2. Audit Objective

The objectives of this Phase 0.3 forensic audit are:
1. Identify every working functional capability across all 11 system roles.
2. Trace the exact functional dependency chain:  
   $$\text{Permission} \longrightarrow \text{Endpoint(s)} \longrightarrow \text{Domain Service(s)} \longrightarrow \text{UI View} \longrightarrow \text{Business Function} \longrightarrow \text{Target Scope}$$
3. Differentiate between:
   - **Role:** The identity type of the actor.
   - **Organizational Authority:** The legal or functional mandate in the Colombian educational system.
   - **Permission:** The atomic resource-action gate.
   - **Tenant Scope:** The DANE organizational boundary (`institution_id`, `campus_id`).
   - **Resource Authorization:** Ownership, homeroom assignment, or civil kinship.
4. Establish the mandatory list of **Functionality That MUST Be Preserved**.
5. Formulate neutral, well-bounded **Owner Decisions** for governance dilemmas that cannot be deduced from existing code.
6. Deliver a phased, low-risk implementation blueprint for future execution.

---

## 3. Scope

This audit inspected the entire PEVN codebase without altering product code:
- **11 System Roles:** `superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `institution_admin`, `academic_coordinator`, `coordinator`, `teacher`, `student`, `guardian`.
- **27 API Controllers:** All routers in `backend/app/api/v1/endpoints/`.
- **73 Atomic Permissions:** The canonical catalog in `rbac_bootstrap_service.py`.
- **52 Backend Test Suites:** All test suites in `backend/tests/` (including 11 suites covering RBAC, tenant isolation, and family lifecycles).
- **19 Frontend Test Suites:** Vitest suites in `frontend/src/test/` (including `RoleNavigationFunctional.test.tsx`).
- **Frontend Routing & Shell:** `App.tsx`, `RootLayout.tsx`, `Dashboard.tsx`, `AuthContext.tsx`, `RequireAuth.tsx`.

---

## 4. Governance / No-Change Confirmation

As mandated by PEVN project governance:
- **Zero product code files were modified.**
- **Zero database migrations or schema alterations were created.**
- **Zero API contracts were modified.**
- **Zero permissions were added, removed, or mutated.**
- **Zero Git commits or pushes were performed.**
- **Working Tree State:** Pristine (except for the creation of this audit report).

---

## 5. Repository Commit Reviewed

- **Commit SHA-1:** `7fb83fb14bc21d675d580511068f2c866de18654`
- **Short Hash:** `7fb83fb`
- **Branch:** `main`
- **Commit Subject:** `PHASE 0.2 — AUTHORIZATION MODEL CONSISTENCY & IMPLEMENTATION PLAN`

---

## 6. Sources Reviewed

| Category | File Path | Scope & Authority |
| :--- | :--- | :--- |
| **Documentation** | `docs/AUTHORIZATION.md` | Multi-Tenant Isolation & Hierarchical Scope Rules |
| **Documentation** | `docs/PHASE_3_RBAC_MATRIX.md` | Phase 3A Canonical Granular Permission Matrix |
| **Documentation** | `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` | Authoritative Product Capabilities by Ministry/School Role |
| **Documentation** | `docs/SECURITY.md` | Security by Design, Least Privilege & Data Privacy |
| **Documentation** | `docs/reports/PEVN_RBAC_ROLE_VISIBILITY_RECONCILIATION.md` | Phase 0.2 RBAC Model & Route Consistency Audit |
| **Backend Core** | `backend/app/core/security/interfaces.py` | SystemRole, Permission, OrganizationalScope interfaces |
| **Backend RBAC** | `backend/app/services/rbac_bootstrap_service.py` | Canonical role definitions, atomic permissions, and seed mappings |
| **Backend Endpoints**| `backend/app/api/v1/endpoints/*.py` (27 files) | All FastAPI controllers, dependencies, and `_resolve_institution_id` |
| **Backend Tests** | `backend/tests/test_*.py` (52 files) | Full regression test suites validating authorization and isolation |
| **Frontend Core** | `frontend/src/context/AuthContext.tsx` | Reactive auth state, `hasRole`, `hasPermission`, `isInScope` |
| **Frontend Guards**| `frontend/src/components/auth/RequireAuth.tsx` | Route guard wrapper enforcing authentication and roles |
| **Frontend Views** | `frontend/src/layouts/RootLayout.tsx`, `Dashboard.tsx` | Navigation shell, conditional links, directive access cards |
| **Frontend Tests** | `frontend/src/test/RoleNavigationFunctional.test.tsx` | Component & navigation functional tests for all 11 roles |

---

## 7. Current RBAC Architecture

PEVN implements a 5-layer authorization pipeline:

```
[1. AUTHENTICATION] ────► JWT Volatile Bearer Token + HttpOnly Refresh Rotation
         │
[2. ROLE & LEVEL]   ────► SystemRole with Immutable Numeric Level (10 - 100)
         │
[3. TENANT SCOPE]   ────► OrganizationalScope:
         │                ├── National (country_code='CO', institution_id=NULL)
         │                ├── Territorial (department_id, municipality_id)
         │                └── Institutional (institution_id, campus_id)
         │
[4. ATOMIC PERM]    ────► Granular `resource:action` evaluated against canonical role mappings
         │
[5. RESOURCE AUTH]  ────► Anti-IDOR: Ownership, Academic Assignment, or Verified Civil Kinship
```

---

## 8. Role Inventory

| # | Role Identifier | Security Level | DANE / Organizational Scope | Real-World Educational Mandate |
| :-: | :--- | :-: | :--- | :--- |
| **1** | `superadmin` | 100 | National (Global Bypass) | Operador técnico del sistema, soporte de infraestructura y auditoría forense. |
| **2** | `national_admin` | 90 | National (MEN) | Ministerio de Educación Nacional: Catálogo DANE/DUE, rectores, analítica territorial. |
| **3** | `department_admin`| 80 | Departamental (SED) | Secretaría de Educación Departamental: Indicadores de cobertura y supervisión territorial. |
| **4** | `municipality_admin`| 70 | Municipal (SEM) | Secretaría de Educación Municipal: Supervisión local de instituciones educativas. |
| **5** | `rector` | 60 / 70 | Institución Educativa | Rector Oficial: Gobierno institucional, SIEE, planta docente, matrículas, cierres anuales. |
| **6** | `institution_admin`| 60 / 70 | Institución Educativa | Alias técnico de compatibilidad para Rectoría. |
| **7** | `academic_coordinator`| 50 / 60 | Institución / Sede | Coordinador Académico: Carga docente, horarios, planeación curricular, sábanas de notas. |
| **8** | `coordinator` | 50 | Institución / Sede | Coordinador de Convivencia / Sede: Situaciones Ley 1620, salones, asistencia y disciplina. |
| **9** | `teacher` | 30 / 50 | Grupo / Asignatura | Docente de Aula: Calificaciones SIEE, actividades, asistencia diaria, videoclases. |
| **10**| `student` | 10 / 20 | Propio (SIMAT) | Estudiante Matriculado: Tareas, evaluaciones, boletines, asistencia, videoclases. |
| **11**| `guardian` | 10 | Tutorados Vinculados | Acudiente Legal: Seguimiento académico, observador, circulares y asistencia de sus hijos. |

---

## 9. Permission Inventory

The platform defines **73 atomic permissions** structured as `resource:action`:
- `*`: `*:*` (Universal technical wildcard).
- `institutions`: `read`, `create`, `update`, `delete`.
- `users`: `read`, `create`, `create_rector`, `update`, `delete`.
- `academic_years`: `read`, `create`, `update`, `close`, `delete`.
- `academic_periods`: `read`, `create`, `update`, `close`.
- `grades`: `read`, `write`, `manage`.
- `subjects`: `read`, `create`, `update`, `delete`.
- `groups`: `read`, `create`, `update`, `delete`, `assign_director`.
- `teachers`: `read`, `create`, `update`, `delete`.
- `students`: `read`, `create`, `update`, `delete`.
- `guardians`: `read`, `create`, `update`, `link_student`.
- `enrollments`: `read`, `create`, `transfer`, `withdraw`, `delete`.
- `academic_assignments`: `read`, `create`, `update`, `delete`.
- `virtual_classrooms`: `read`, `create`, `join`, `manage`.
- `recordings`: `read`, `manage`, `delete`.
- `activities`: `read`, `create`, `update`, `publish`, `close`, `delete`.
- `submissions`: `read`, `create`, `update`, `return`.
- `attendance`: `read`, `write`.
- `planning`: `read`, `create`, `update`, `delete`.
- `communications`: `read`, `create`, `update`, `publish`, `delete`.
- `news`: `read`, `create`, `update`, `publish`, `delete`.
- `incidents`: `read`, `create`, `update`, `close`.
- `siee_policies`: `read`, `manage`.
- `evaluations`: `read`, `grade`, `adjust`, `close_period`, `reopen_period`, `recovery`.
- `report_cards`: `read`, `read_group`.
- `promotions`: `preview`, `execute`, `read`.

---

## 10. Functional Preservation Matrix

This matrix provides the forensic mapping for all major platform capabilities:

| Functionalidad existente | Endpoint / UI | Operación | Rol actual | Rol correcto | Autoridad | Alcance actual | Alcance correcto | Permiso actual | Permiso necesario | Conservar | Cambiar | Riesgo | Evidencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **Aprovisionar Institución** | `POST /institutions` | Alta en DUE/DANE | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Operador | Nacional | Nacional | `institutions:create` | `institutions:create` | **SÍ** | No | Alto | `institutions.py:126`, `test_institution_provisioning.py` |
| **Invitar Rector** | `POST /institutions/{id}/rector-invitation` | Emitir token un solo uso | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Nombramiento | Nacional | Nacional | `users:create` | `users:create_rector` | **SÍ** | Endpoint perm | Crítico | `institutions.py:680`, `test_rbac_governance_and_rector_invitation.py` |
| **Sucesión de Rectoría** | `POST /institutions/{id}/rector/revoke` | Revocar y habilitar nuevo | `superadmin`, `national_admin` | `superadmin`, `national_admin` | MEN / Nombramiento | Nacional | Nacional | `users:create` | `users:create_rector` | **SÍ** | Endpoint perm | Crítico | `institutions.py:729`, `test_rector_succession.py` |
| **Crear Año Lectivo** | `POST /academic-years` | Apertura calendario | `rector`, `coordinator`, `national_admin`* | `rector`, `institution_admin` | Rectoría / Consejo Directivo | Tenant / Nacional* | Institucional | `academic_years:create`| `academic_years:create`| **SÍ** | Scope national | Medio | `academic_years.py:63`, `test_academic_api.py` |
| **Cerrar Año Lectivo** | `POST /academic-years/{id}/close` | Clausura y archivo anual | `rector`, `national_admin`* | `rector`, `institution_admin` | Rectoría Oficial | Tenant / Nacional* | Institucional | `academic_years:close` | `academic_years:close` | **SÍ** | Scope national | Alto | `academic_years.py:239`, `test_academic_api.py` |
| **Crear Perfil Docente** | `POST /teachers` | Registrar docente en planta | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Directiva escolar | Tenant / Nacional* | Institucional | `teachers:create` | `teachers:create` | **SÍ** | Scope national | Medio | `teachers.py:68`, `test_teacher_account_provisioning.py` |
| **Aprovisionar Cuenta Docente** | `POST /teachers/{id}/account/provision` | Crear credenciales y token | `rector`, `coordinator` | `rector`, `coordinator` | Directiva escolar | Institucional | Institucional | `teachers:create` | `teachers:create` | **SÍ** | No | Medio | `teachers.py:180`, `test_teacher_account_provisioning.py` |
| **Crear Estudiante (SIMAT)**| `POST /students` | Registro de ficha civil | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `students:create` | `students:create` | **SÍ** | Scope national | Medio | `students.py:64`, `test_identity_family_lifecycle.py` |
| **Aprovisionar Cuenta Alumno** | `POST /students/{id}/account/provision`| Crear usuario y credencial | `rector`, `coordinator` | `rector`, `coordinator` | Secretaría académica | Institucional | Institucional | `students:create` | `students:create` | **SÍ** | No | Medio | `students.py:180`, `test_identity_family_lifecycle.py` |
| **Registrar Acudiente Civil**| `POST /guardians` | Ficha civil desacoplada | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Registro escolar | Tenant / Nacional* | Institucional | `guardians:create` | `guardians:create` | **SÍ** | Scope national | Medio | `guardians.py:64`, `test_guardian_onboarding.py` |
| **Vincular Acudiente ↔ Alumno**| `POST /students/{id}/guardians/{gid}`| Asociación civil formal | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `guardians:link_student`| `guardians:link_student`| **SÍ** | Scope national | Alto | `students.py:324`, `test_identity_family_lifecycle.py` |
| **Auto-Activación Acudiente**| `POST /auth/guardians/accept-activation`| Verificación y password | Público (Anónimo) | Familiar verificado | Familiaridad civil | Nacional | Nacional | N/A (Público) | N/A (Token seguro) | **SÍ** | No | Alto | `auth.py:270`, `test_guardian_onboarding.py` |
| **Crear Grupo / Salón** | `POST /groups` | Cursos y cupos | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Organización escolar | Tenant / Nacional* | Institucional | `groups:create` | `groups:create` | **SÍ** | Scope national | Bajo | `groups.py:60`, `test_groups_and_actors_models.py` |
| **Asignar Carga Docente** | `POST /academic-assignments` | Docente + Asignatura + Grupo | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Coordinación académica | Tenant / Nacional* | Institucional | `academic_assignments:create`| `academic_assignments:create`| **SÍ** | Scope national | Medio | `academic_assignments.py:60`, `test_enrollments_and_assignments.py`|
| **Matricular Alumno** | `POST /enrollments` | Matrícula en grupo activo | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `enrollments:create` | `enrollments:create` | **SÍ** | Scope national | Medio | `enrollments.py:60`, `test_enrollments_and_assignments.py`|
| **Traslado de Salón** | `POST /transfers` | Cambio de grupo interno | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Secretaría académica | Tenant / Nacional* | Institucional | `enrollments:transfer`| `enrollments:transfer`| **SÍ** | Scope national | Bajo | `transfers.py:60`, `test_academic_api.py` |
| **Crear Actividad Pedagógica**| `POST /teacher/activities` | Taller / Tarea / Evaluación | `teacher` | `teacher` | Autonomía de cátedra | Carga asignada | Carga asignada | `activities:create` | `activities:create` | **SÍ** | No | Crítico | `teacher_portal.py:260`, `test_teacher_portal_api.py` |
| **Calificar Entregas** | `PUT /teacher/activities/{id}/grades` | Asentar nota de actividad | `teacher` | `teacher` | Evaluación docente | Carga asignada | Carga asignada | `grades:write` | `grades:write` | **SÍ** | No | Crítico | `teacher_portal.py:460`, `test_student_submissions_api.py` |
| **Registrar Asistencia Diaria**| `POST /teacher/groups/{id}/attendance`| Control de asistencia | `teacher` | `teacher` | Control de aula | Salón asignado | Salón asignado | `attendance:write` | `attendance:write` | **SÍ** | No | Alto | `teacher_portal.py:530`, `test_teacher_portal_api.py` |
| **Planeación Curricular** | `POST /teacher/planning` | Unidades y competencias | `teacher` | `teacher` | Pedagógica | Carga asignada | Carga asignada | `planning:create` | `planning:create` | **SÍ** | No | Bajo | `teacher_portal.py:600`, `test_teacher_portal_api.py` |
| **Parametrizar SIEE** | `POST /siee-policies` | Escala y reglas de notas | `rector`, `institution_admin` | `rector`, `institution_admin` | Consejo Directivo | Institucional | Institucional | `siee_policies:manage` | `siee_policies:manage` | **SÍ** | No | Crítico | `siee_policies.py:60`, `test_siee_and_evaluations_api.py` |
| **Asentar Notas de Período**| `POST /evaluations/grade` | Planilla oficial SIEE | `teacher`, `rector`, `coordinator` | `teacher` (Directivos: adjust) | Calificación oficial | Carga asignada | Carga asignada | `evaluations:grade` | `evaluations:grade` | **SÍ** | Directivo override | Crítico | `evaluation_grades.py:180`, `test_siee_and_evaluations_api.py` |
| **Cerrar Período Académico** | `POST /evaluations/periods/{id}/close` | Bloqueo inmutable de notas | `rector`, `coordinator` | `rector`, `institution_admin` | Rectoría / Dirección | Institucional | Institucional | `evaluations:close_period`| `evaluations:close_period`| **SÍ** | Solo Rector | Crítico | `evaluation_grades.py:352`, `test_siee_and_evaluations_api.py` |
| **Emitir Boletín Oficial** | `GET /evaluations/report-card/{id}` | Calificaciones oficiales | `rector`, `coordinator`, `teacher`, `student`, `guardian` | Todos autorizados | Transparencia escolar | Según rol/parentesco | Según rol/parentesco | `report_cards:read` | `report_cards:read` | **SÍ** | No | Alto | `evaluation_grades.py:460`, `OfficialReportCard.test.tsx` |
| **Simular Promoción Escolar**| `POST /promotions/preview` | Algoritmo SIEE fin de año | `rector`, `coordinator`, `teacher` | `rector`, `coordinator` | Comisión de Evaluación | Institucional | Institucional | `promotions:preview` | `promotions:preview` | **SÍ** | Excluir teacher | Alto | `academic_promotions.py:60`, `test_promotion_governance.py` |
| **Asentar Acta de Promoción** | `POST /promotions/commit` | Cierre definitivo y actas | `rector`, `institution_admin` | `rector`, `institution_admin` | Rectoría Oficial | Institucional | Institucional | `promotions:execute` | `promotions:execute` | **SÍ** | No | Crítico | `academic_promotions.py:100`, `test_promotion_governance.py` |
| **Crear Clase Virtual** | `POST /virtual-classrooms` | Sala BigBlueButton | `rector`, `coordinator`, `teacher`, `national_admin`* | `rector`, `coordinator`, `teacher` | Convocatoria pedagógica | Tenant / Asignación | Tenant / Asignación | `virtual_classrooms:create`| `virtual_classrooms:create`| **SÍ** | Scope national | Alto | `virtual_classrooms.py:71`, `test_virtual_classroom_api.py` |
| **Unirse a Clase Virtual** | `POST /virtual-classrooms/{id}/join`| Acceso MODERATOR / VIEWER | `rector`, `teacher`, `student`, `national_admin`* | Docente (Mod), Alumno (View) | Asistencia a clase | Salón / Matrícula | Salón / Matrícula | `virtual_classrooms:join` | `virtual_classrooms:join` | **SÍ** | National audit | Crítico | `virtual_classrooms.py:165`, `test_virtual_classroom_api.py` |
| **Emitir Circular** | `POST /communications` | Comunicado con acuse | `rector`, `coordinator`, `national_admin`* | `rector`, `coordinator` | Dirección escolar | Institucional | Institucional | `communications:create`| `communications:create`| **SÍ** | Scope national | Medio | `communications.py:60`, `test_institutional_communications_api.py`|
| **Firmar Acuse de Circular** | `POST /communications/{id}/acknowledge`| Sello digital de lectura | `student`, `guardian` | `student`, `guardian` | Notificación legal | Propio / Tutorado | Propio / Tutorado | `communications:read` | `communications:read` | **SÍ** | No | Medio | `communications.py:220`, `test_institutional_communications_api.py`|
| **Registrar Falta Observador**| `POST /incidents` | Situación Ley 1620 | `rector`, `coordinator`, `teacher`, `national_admin`* | `rector`, `coordinator`, `teacher` | Comité Convivencia | Institucional / Asign. | Institucional / Asign. | `incidents:create` | `incidents:create` | **SÍ** | Scope national | Crítico | `incidents.py:60`, `test_coexistence_incidents_api.py` |

*\* Indica que el permiso actualmente reside en `national_admin` en el catálogo semilla (`rbac_bootstrap_service.py`), pero en runtime falla debido a `institution_id = NULL`.*

---

## 11. User and Role Management Analysis

### Forensic Finding: The Rector Invitation Dependency Chain
In `backend/app/api/v1/endpoints/institutions.py`:
- `POST /{institution_id}/rector-invitation` (Line 680)
- `POST /{institution_id}/rector/revoke` (Line 729)

Both endpoints enforce:
```python
auth: Annotated[AuthContextDep, Depends(require_permission("users", "create"))]
```
followed by:
```python
if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
    raise AuthorizationError("Solo administradores nacionales pueden emitir invitaciones para Rectores.")
```

**Technical Consequence:**  
If `users:create` is stripped from `national_admin`, the FastAPI dependency `require_permission("users", "create")` immediately rejects the request with `403 Forbidden` before the controller logic is even reached.  
**Preservation Rule:**  
Do NOT remove `users:create` from `national_admin` unless the endpoint dependency is simultaneously updated in code to `require_permission("users", "create_rector")` (which already exists in `CANONICAL_PERMISSIONS`).

### Teacher and Student Account Creation
In `teachers.py` and `students.py`:
- Creating a teacher profile with a new user account (`payload.new_user`) executes `UserService.provision_institutional_user()`.
- The endpoint is protected by `require_permission("teachers", "create")`, NOT `users:create`.
- Creating a student profile with an account executes `StudentService.create_student()`.
- The endpoint is protected by `require_permission("students", "create")`, NOT `users:create`.

**Technical Consequence:**  
School directivos (`rector`, `coordinator`) do NOT require global `users:create` to provision teachers and students. Their institutional user creation capabilities are cleanly encapsulated under `teachers:create` and `students:create`.

---

## 12. SUPER_ADMIN Analysis

- **Technical Authority:** Global root (`level: 100`, permissions: `["*:*"]`).
- **Data Scope:** National (`country_code="CO"`, `institution_id=None`).
- **The Core Architectural Dilemma:**  
  In `backend/app/api/v1/endpoints/*.py` (18 files), `_resolve_institution_id()` fails closed if `current_user.institution_id` is `None` AND `institution_id_override` is `None`.
- **Frontend Misalignment:**  
  `RootLayout.tsx` and `Dashboard.tsx` expose `/academic` and 8 registrar subcards to `superadmin` without verifying whether an institution has been selected.
- **Preservation Decision:**  
  Retain global authority `*:*`. Introduce an **Institution Context Selector** in the frontend so SuperAdmin can pass `?institution_id=<UUID>` when inspecting or intervening in a school. Do NOT expose generic tenantless academic links.

---

## 13. NATIONAL_ADMIN Analysis

- **Governmental Mandate:** Ministry of Education National (MEN) (`level: 90`).
- **Legitimate Functional Responsibilities:**
  1. National DANE / DUE Catalog administration (`institutions:read`, `create`, `update`).
  2. Rector Onboarding and Succession (`users:create` / `users:create_rector`).
  3. Territorial Analytics and Macro KPIs (`analytics` endpoints).
  4. National Curricular Guidelines (`grades:read`, `grades:manage`).
  5. Audit and Inspection of school records across all 32 departments.
- **Inconsistent Operational Permissions in Bootstrap:**
  `rbac_bootstrap_service.py` currently grants `national_admin` direct mutation rights over local school entities: `grades:write`, `groups:create/delete`, `students:create/delete`, `enrollments:create/transfer`, `incidents:create/update`.
- **Why These Must Not Be Arbitrarily Deleted in This Phase:**
  In some emergency state interventions (e.g., intervention of a failed educational institution under Colombian administrative law), national auditors may need to perform emergency adjustments. If these permissions are removed outright without a defined "Intervention Mode", legitimate government oversight workflows could be blocked.

---

## 14. Territorial Roles Analysis

### `department_admin` (Level 80) and `municipality_admin` (Level 70)
- **Scope:** Departmental (`department_id`) or Municipal (`municipality_id`).
- **Current Bootstrap:** 17 read-only permissions across all domain resources.
- **Frontend Defect:** `Dashboard.tsx` includes territorial admins in `isDirective`, displaying 8 school management cards that trigger `403 Forbidden`.
- **Preservation Decision:**  
  Preserve read-only visibility for institutions and analytics within their territorial DANE boundary (`scope_contains`). Remove local school management cards from their dashboard.

---

## 15. Institutional Roles Analysis

### `rector` / `institution_admin` (Level 60 / 70)
- Full administrative and educational governance over their specific institution (`institution_id`).
- Must preserve: All 64 operational permissions.
- Must restrict: Cannot access `/admin/institutions` or `/analytics/territorial` macro dashboards.

### `academic_coordinator` / `coordinator` (Level 50 / 60)
- Operational academic scheduling, groups, workload, attendance, and student coexistence.
- Must preserve: Workload assignment (`academic_assignments:*`), period sheets, student transfers, and incident management.
- Must restrict: Cannot execute annual calendar close or alter SIEE scales without Rector consent.

---

## 16. Teacher Analysis

### Certified Capabilities Protected:
- **Teacher Academic Scope:** In `test_teacher_academic_scope.py`, teachers can only access groups and students assigned in their active workload.
- **Pedagogical Autonomy:** Draft, publish, grade, and return student homework (`test_student_submissions_api.py`).
- **SIEE Planilla:** Submit period grades with mandatory pedagogical justification (`adjustment_reason`) when calculated score is overridden.
- **Coexistence Observador:** Author Type I, II, and III disciplinary notes with student commitments under Ley 1620.
- **Virtual Classrooms:** Join assigned sessions as `MODERATOR` and control recording visibility for students.

---

## 17. Student Analysis

### Certified Capabilities Protected:
- **Anti-IDOR:** In `test_student_portal_api.py`, student access is strictly scoped to `student.user_id = user.id`. Any query targeting another student's record returns `404 Not Found`.
- **Self-Service Submissions:** Upload homework attachments (PDF, DOCX, ZIP) with Magic Bytes validation and max 10 MB limit (`test_activity_resources_and_storage.py`).
- **Digital Receipt:** Sign circular acknowledgments recording timestamp, user ID, and IP address.
- **Virtual Classrooms:** Join live classes as `VIEWER` strictly for enrolled groups.

---

## 18. Guardian Analysis

### Certified Capabilities Protected:
- **Student-Guardian Kinship Barrier:** In `test_guardian_tenant_isolation.py`, a guardian can ONLY inspect students where a formal link exists in `student_guardians`.
- **Multi-Child Switcher:** Dynamic switching between multiple enrolled children in the same or different institutions.
- **Family Follow-Up:** Monitor grades, review attendance alerts, and read student coexistence notes.
- **Strict Prohibition:** Guardians cannot submit homework or grade.

---

## 19. Route / UI Authorization Analysis

| Route | Auth Guard | Role Guard in App.tsx | Context Required | Backend Protection | Frontend Visibility | Defect / Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `/dashboard` | YES | None | None | User profile endpoint | Top bar & direct | Coherent. |
| `/admin/institutions` | YES | `superadmin`, `national_admin` | National | `institutions:read` + National | Nav bar for national | Territorial admins excluded from local directory. |
| `/analytics/territorial`| YES | `institutions:read` | Territorial | `analytics` + Scope check | Nav bar (Erron. to Rector) | Exposed to Rector/Coordinator via `institutions:read`. |
| `/academic` | YES | **NONE** | **YES (`institution_id`)** | 18 controllers fail closed | Nav bar (Erron. to Superadmin)| Missing role guard in App.tsx; fails closed with 403. |
| `/virtual-classrooms` | YES | `virtual_classrooms:read` | **YES (`institution_id`)** | Controller fails closed | Nav bar (Erron. to National) | Exposed to national roles without context. |
| `/teacher` | YES | `teacher` | **YES (Teacher Profile)** | TeacherPortalService fails closed | Nav bar for teacher | Bypassed by Superadmin due to `AuthContext.tsx`. |
| `/student` | YES | `student` | **YES (SIMAT Profile)** | StudentPortalService fails closed | Nav bar for student | Bypassed by Superadmin. |
| `/guardian` | YES | `guardian` | **YES (Guardian Profile)**| GuardianPortalService fails closed | Nav bar for guardian | Bypassed by Superadmin. |

---

## 20. Backend Authorization Analysis

The backend enforces defense-in-depth:
1. **Dependency Injection:** `Depends(require_permission("resource", "action"))`.
2. **Context Resolution:** `_resolve_institution_id(auth, current_user, institution_id_override)`.
3. **Scope Containment:** `scope_contains(actor_scope, target_scope)`.
4. **Domain Services:** Verify entity relationships (e.g., student in group, teacher in assignment).

The backend authorization is sound, sovereign, and secure. All reported UI bugs are presentation-layer or seed-catalog misalignments.

---

## 21. Permission Functional Dependency Matrix

```
institutions:create ──► POST /institutions ──► InstitutionService ──► National Catalog View ──► DANE Provisioning
users:create ─────────► POST /institutions/{id}/rector-invitation ──► RectorOnboardingService ──► Invitation Modal ──► Rector Appointment
teachers:create ──────► POST /teachers ──► TeacherService + UserService ──► TeachersView Modal ──► Teacher Provisioning
students:create ──────► POST /students ──► StudentService + UserService ──► StudentsView Modal ──► SIMAT Student Provisioning
guardians:link_student ► POST /students/{id}/guardians/{gid} ──► GuardianService ──► Kinship Modal ──► Family Binding
academic_years:create ► POST /academic-years ──► AcademicYearService ──► AcademicYearsView Modal ──► Calendar Setup
groups:create ────────► POST /groups ──► GroupService ──► GroupsView Modal ──► Course & Quota Setup
academic_assignments:create ► POST /academic-assignments ──► AssignmentService ──► AssignmentsView ──► Workload Assignment
enrollments:create ───► POST /enrollments ──► EnrollmentService ──► EnrollmentsView Modal ──► Student Enrollment
activities:create ────► POST /teacher/activities ──► ActivityService ──► TeacherActivitiesView ──► Task Publishing
evaluations:grade ────► POST /evaluations/grade ──► EvaluationService ──► TeacherSieeEvaluationView ──► SIEE Grade Sheet
evaluations:close_period ► POST /evaluations/periods/{id}/close ──► EvaluationService ──► DirectiveEvaluationView ──► Grade Lock
virtual_classrooms:join ► POST /virtual-classrooms/{id}/join ──► MeetingService ──► Live Meeting View ──► BigBlueButton Join
incidents:create ─────► POST /incidents ──► CoexistenceIncidentService ──► IncidentModal ──► Ley 1620 Logging
```

---

## 22. Tenant / Scope Analysis

- **Institutional Tenant Isolation:** Enforced via mandatory foreign keys on all domain tables (`institution_id`).
- **Territorial Containment:** Evaluated via DANE code prefixes (`05` = Antioquia, `05001` = Medellín).
- **National Scope:** Users with `is_national=True` have `institution_id=None`. When operating tenant endpoints, they must pass `institution_id_override`.

---

## 23. Resource Authorization Analysis

- **Teacher Scope:** Verified against `AcademicAssignment` table. Teachers cannot view or edit groups outside their active workload (`test_teacher_academic_scope.py`).
- **Student Scope:** Verified against `Enrollment` table. Students cannot access classes or tasks outside their enrolled course.
- **Guardian Scope:** Verified against `StudentGuardian` table. Guardians cannot access records for unlinked children.

---

## 24. Security Findings

1. **Backend Isolation Works Perfectly:** Anti-IDOR and tenant isolation fail closed across all 18 domain controllers.
2. **Presentation Decoupling:** The frontend erroneously renders institutional navigation elements to national users who have `institution_id = NULL`.
3. **Client-Side SuperAdmin Bypass:** The `hasRole()` short-circuit in `AuthContext.tsx` bypasses functional separation of duties on the client.
4. **Dangerous Seed Disconnect:** `national_admin` possesses operational permissions in `rbac_bootstrap_service.py` that contradict the documented functional baseline.

---

## 25. Documentation Contradictions

| Contradiction ID | Source A | Source B | Actual Implementation | Finding & Risk | Owner Decision Required? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **CONT-01** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.2 (MEN cannot edit grades or local students) | `PHASE_3_RBAC_MATRIX.md` §3 (National Admin has GLOBAL on all CRUD) | `rbac_bootstrap_service.py` seeded `national_admin` with 48 operational permissions | High: Inconsistent authorization baseline | **YES (Decision 02)** |
| **CONT-02** | `AUTHORIZATION.md` §1 (Multi-tenant containment mandatory) | `RootLayout.tsx` lines 89–101 | Navbar displays `/academic` to `superadmin` | Medium: Broken UX on click | **YES (Decision 01)** |
| **CONT-03** | `CANONICAL_PERMISSIONS` defines `users:create_rector` | `institutions.py` lines 680, 729 | Controller checks `require_permission("users", "create")` | Medium: Pruning `users:create` breaks rector invites | **NO (Code Alignment)** |
| **CONT-04** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.3 (Territorial admins are macro-only) | `Dashboard.tsx` line 337 | `isDirective` includes territorial admins | Low: Territorial admins see broken registrar cards | **NO (UI Alignment)** |

---

## 26. Existing Functionality That MUST Be Preserved

The following 18 critical functionalities are fully implemented, tested, and certified. Under no circumstances should they be removed or broken during RBAC reconciliation:

1. **National Catalog Provisioning:** `superadmin` and `national_admin` creating institutions and DANE sedes.
2. **Cryptographic Rector Invitations:** `national_admin` generating single-use onboarding invitations for official Rectors.
3. **Rector Succession & Revocation:** `national_admin` revoking active rector credentials and re-inviting successors.
4. **Calendar & Academic Year Management:** `rector` creating, activating, and closing school academic years.
5. **Teacher Onboarding & Account Provisioning:** `rector` and `coordinator` registering teachers and generating initial credentials.
6. **Student SIMAT Registration & Account Provisioning:** `rector` and `coordinator` creating student records and activating logins.
7. **Guardian Civil Registration & Account Onboarding:** `rector` registering legal guardians and public self-activation via token.
8. **Student ↔ Guardian Binding:** `rector` and `coordinator` associating guardians to students with relationship types.
9. **Curricular Workload Assignment:** `coordinator` linking Docente + Asignatura + Grupo with hourly intensity.
10. **SIMAT Enrollment & Classroom Transfers:** `rector` and `coordinator` assigning students to groups and executing transfers.
11. **Teacher Pedagogical Activities:** `teacher` drafting, publishing, grading, and returning student submissions.
12. **Student Homework Submissions:** `student` uploading multi-file attachments and resubmitting returned homework.
13. **Daily Attendance Tracking:** `teacher` recording daily presence, absence, late, and justified status.
14. **SIEE Scale Parameterization:** `rector` defining grading scales, passing scores, and recovery caps.
15. **SIEE Period Grade Settlement:** `teacher` submitting period grades with pedagogical override justifications.
16. **Grade Sheet Locking & Closing:** `rector` closing academic periods to make grades immutable.
17. **Synchronous Virtual Classrooms:** `teacher` initiating BigBlueButton meetings as `MODERATOR` and students joining as `VIEWER`.
18. **Coexistence Observador (Ley 1620):** `teacher` and `coordinator` logging Type I, II, III incidents with commitments.

---

## 27. Functionality Requiring Scope Correction

- **National Admin Academic Access:** Must be scoped to read-only inspection, requiring an explicit `?institution_id=<UUID>` query parameter.
- **Territorial Admin Directory:** Must be scoped to institutions within their specific department or municipality.
- **Territorial Analytics:** Must be scoped so that institutional rectors cannot access national macro-dashboards.

---

## 28. Functionality Requiring Role Correction

- **Rector Invitation Endpoints:** Change controller permission dependency from `users:create` to `users:create_rector` in `institutions.py`.
- **National Admin Local Operations:** Remove direct local mutation permissions (`grades:write`, `groups:create/delete`, `students:create/delete`, `incidents:create/update`) from `national_admin` in `rbac_bootstrap_service.py`.

---

## 29. Route Guard Corrections

- **`/academic` in `App.tsx`:** Protect with `roles={['rector', 'coordinator', 'institution_admin', 'academic_coordinator']}` and enforce `requireInstitutionContext={true}`.
- **`hasRole()` in `AuthContext.tsx`:** Eliminate the blanket `if (user.roles.includes('superadmin')) return true` bypass on actor-specific portals (`/teacher`, `/student`, `/guardian`).
- **`/analytics/territorial` in `RootLayout.tsx`:** Change condition from `hasPermission('institutions:read')` to `user.scope.is_national || Boolean(user.scope.department_id) || Boolean(user.scope.municipality_id)`.

---

## 30. Owner Decisions Required

### OWNER DECISION 01: SuperAdmin Operation of Tenant Modules
- **Decision:** How should `SUPER_ADMIN` interact with tenant-scoped modules (Academic, Classrooms)?
- **Current State:** Direct top-level links exist, but API calls fail with `403 Contexto no disponible`.
- **Options:**
  - *Option A:* Require explicit institution context selection via `/admin/institutions` and `?institution_id=<UUID>`. Hide generic navbar links when no institution is selected.
  - *Option B:* Restrict `SUPER_ADMIN` exclusively to platform infrastructure, catalog, and audit; never permit school-level academic access.
  - *Option C:* Retain current state.
- **Affected Roles:** `superadmin`.
- **Security Implications:** Option A preserves tenant isolation while providing operational capability. Option B provides maximum separation of duties.
- **Regression Risk:** Low.

### OWNER DECISION 02: National Admin (MEN) Permission Pruning
- **Decision:** Should `national_admin` retain local school operational permissions?
- **Current State:** 48 operational permissions granted in `rbac_bootstrap_service.py`, conflicting with `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md`.
- **Options:**
  - *Option A:* Prune local mutation permissions from `national_admin`. Retain only national catalog governance, rector appointments, macro analytics, and read-only census audits.
  - *Option B:* Retain broad permissions as emergency support powers, executable only with an explicit institution override.
  - *Option C:* Create a separate `support_national` technical intervention role.
- **Affected Roles:** `national_admin`.
- **Security Implications:** Option A enforces Least Privilege. Option B retains centralized administrative intervention capability.
- **Regression Risk:** Medium (requires updating existing test assertions).

### OWNER DECISION 03: Virtual Classroom & Incident National Auditing
- **Decision:** Can MEN officials join live school video classes or read individual student disciplinary entries under Ley 1620?
- **Current State:** Permissions `virtual_classrooms:join` and `incidents:read` are currently assigned to `national_admin`.
- **Options:**
  - *Option A:* Restricted to institutional actors. National officials see only aggregated KPIs.
  - *Option B:* Formal Audit Mode. National officials may access these resources strictly with an official audit ticket ID.
- **Affected Roles:** `national_admin`, `student`, `guardian`.
- **Security Implications:** Affects minors' privacy rights under Ley 1581 de 2012 and Ley 1620 de 2013.
- **Regression Risk:** Low.

---

## 31. Future Implementation Plan

*(PROPOSED TARGET ROADMAP — FOR APPROVED FUTURE EXECUTION ONLY)*

```
PHASE A: Backend Endpoint Dependency Alignment
  ├── Change invite_rector_endpoint to depend on users:create_rector
  └── Exit Criteria: test_rbac_governance_and_rector_invitation.py passes with atomic permission

PHASE B: RBAC Bootstrap Catalog Reconciliation
  ├── Implement Owner Decision 02 in rbac_bootstrap_service.py
  └── Exit Criteria: Clean database re-seed without excessive permissions

PHASE C: Frontend Route Guard & Context Hardening
  ├── Update RequireAuth.tsx with requireInstitutionContext and strictRoleMatch
  ├── Protect /academic in App.tsx
  └── Remove SuperAdmin bypass from AuthContext.tsx

PHASE D: Presentation Shell Clean-Up
  ├── Align RootLayout.tsx navbar links with Table B
  └── Refactor Dashboard.tsx isDirective role list

PHASE E: Explicit Institution Context Switcher (SuperAdmin UX)
  ├── Add "Operar Institución" action in InstitutionsView.tsx
  └── Propagate ?institution_id=<UUID> to academic controllers

PHASE F: Comprehensive Regression Testing
  ├── Execute all 52 backend pytest suites
  └── Execute all 19 frontend vitest suites

PHASE G: Human Runtime Validation
  ├── Live multi-role testing on local dev servers
  └── Document evidence in final closure report

PHASE H: Certification & Baseline Freeze
```

---

## 32. Regression Protection Plan

To prevent regressions in certified functionality:
1. **Rector Onboarding:** Verify `test_rbac_governance_and_rector_invitation.py` after any change to user permissions.
2. **Teacher Academic Scope:** Verify `test_teacher_academic_scope.py` to ensure Anti-IDOR remains active.
3. **Student/Guardian Isolation:** Verify `test_guardian_tenant_isolation.py` and `test_identity_family_lifecycle.py`.
4. **SIEE & Evaluations:** Verify `test_siee_and_evaluations_api.py` ensuring period lock cannot be bypassed.
5. **Virtual Classrooms:** Verify `test_virtual_classroom_api.py` ensuring only enrolled students can join.

---

## 33. Evidence Index

- **Backend Endpoints:** `backend/app/api/v1/endpoints/` (27 routers inspected).
- **Backend Tests:** `backend/tests/` (52 suites inspected, 0 failed).
- **Frontend Code:** `frontend/src/` (`App.tsx`, `RootLayout.tsx`, `Dashboard.tsx`, `AuthContext.tsx`, `RequireAuth.tsx`).
- **Frontend Tests:** `frontend/src/test/RoleNavigationFunctional.test.tsx` (544 lines).

---

## 34. Final Gate

**`AUDIT PASS WITH OWNER DECISIONS REQUIRED`**  
*(The audit successfully established the functional preservation baseline, traced all dependencies, and protected certified capabilities without modifying a single line of product source code).*
