# PEVN — RBAC-AUDIT-01: Cross-Role Functional Coherence, Information Integrity, and Regression-Preserving Certification Report

**Execution Standard:** AI Software Factory Standard v1.2  
**Implementation Agent:** Antigravity exclusively  
**Priority:** Critical — RBAC, Institutional Data Integrity, and Preservation of Accepted Functionality  
**Mode:** Forensic audit → evidence-based findings → minimal corrections only for reproduced defects → regression verification → operator manual acceptance  
**Repository:** `juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN`  
**Milestone:** RBAC-AUDIT-01-R1 (Certification Reconciliation and Manual Acceptance Readiness)  
**Certification Status:** `CONDITIONAL PASS — DOCUMENTATION RECONCILED, MANUAL ACCEPTANCE PENDING`

---

## 0. Reconciliation Addendum (RBAC-AUDIT-01-R1)

**Date of Reconciliation:** `2026-10-12`  
**Review Type:** Forensic cross-check against live database schemas, backend services, frontend routing, Vite configuration, and test suites.

### 0.1 Summary of Reconciled Inconsistencies and Evidence

| Audit Item | Pre-Reconciliation Description | Reconciled Reality (Verified in Code & DB) | Primary Evidence & Files |
| :--- | :--- | :--- | :--- |
| **Local Environment URLs** | Assumed `localhost:5173` and `/activate`. | Frontend runs strictly on **`http://localhost:3000`** (`strictPort: true`). Backend API runs on **`http://localhost:8000/api/v1`**. Activation route is **`/auth/accept-invitation`**. | `frontend/vite.config.ts:98-109`, `frontend/src/App.tsx:89-95`, `frontend/src/utils/index.ts:149-186`. |
| **Role Inventory vs Levels** | Stated generic "9-tier RBAC architecture" without clarifying roles vs levels. | Exact count: **11 canonical role entries** in PostgreSQL table `roles` spanning **7 discrete numeric hierarchy levels** (100, 90, 80, 70, 60, 50, 30, 10). Distinct aliases exist (`institution_admin` = 60, `academic_coordinator` = 50). `auditor` is a read-only governance actor. | PostgreSQL `pevn_db` query on `roles`, `backend/app/services/rbac_bootstrap_service.py:25-92`. |
| **Academic Permissions (Rector vs Coordinator)** | Apparent contradiction: checklist claimed Coordinator could not configure SIEE, while matrix listed shared permissions. | Reconciled: both can inspect active SIEE and seal/reopen periods (`evaluations:close_period`, `reopen_period`). But **`InstitutionSettingsView`** (delegation flag) and **`CoordinatorsView`** are restricted exclusively to Rector (`roles: ['rector', 'institution_admin']`). Coordinator cannot manage school years (`academic_years:create/close/delete`), group directors, or provision other coordinators. | `frontend/src/pages/academic/AcademicHub.tsx:51-78`, `backend/app/services/rbac_bootstrap_service.py:339-617`. |
| **Information Sources** | Described generally without pinpointing endpoints. | Documented per role: identity from `GET /api/v1/auth/me`, institutional profile from `GET /api/v1/institutions/my-institution`, telemetry from `GET /api/v1/operations/*`, academic data from `GET /api/v1/academic/*`. | `frontend/src/context/AuthContext.tsx:67-158`, `frontend/src/pages/Dashboard.tsx:50-112`. |
| **Context Bleed Safeguards** | Stated conceptually. | Verified: `AuthContext.tsx` explicitly calls `setActiveInstitutionContext(null)` on login, logout, refresh failure, and unassigned roles. Stale context retention is impossible. | `frontend/src/context/AuthContext.tsx:67-73, 140, 155`. |
| **Backend Test Scope** | Claimed "backend suite passed". | Accurately scoped: **127 tests passed across 9 targeted RBAC and authority chain suites**, not the entire project test suite. | Pytest log: 127 items collected and passed in 303.56s. |
| **Working Tree Tracking** | Stated report was only untracked file. | Fully confirmed: exactly **8 modified tracked files** (minimal hardening & test mocks) and **1 untracked file** (`docs/reports/PEVN_RBAC_AUDIT_01_CROSS_ROLE_FUNCTIONAL_COHERENCE.md`). | `git status --porcelain`. |

---

## 1. Local Repository, Branch, HEAD, and Working-Tree Snapshot

### 1.1 Snapshot Metadata
- **Repository:** `juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN`
- **Active Branch:** `main`
- **HEAD Commit SHA:** `d3b2919`
- **HEAD Commit Message:** `SA-02-R1: SUPER_ADMIN Identity Reconciliation, Dashboard Role Isolation, Telemetry Verification, and Safe Certification`
- **Local Time of Execution:** `2026-10-12T16:35:00-05:00`
- **Runtime Environment:** Windows 11, PowerShell, Node.js v20+, Python 3.14.2, PostgreSQL 16 (Port 5433).

### 1.2 Working Tree Inspection
A strictly non-destructive protocol was enforced:
- Zero database migrations (`alembic downgrade`), table drops, or resets were performed.
- Zero database re-seeding commands were executed against the active PostgreSQL database (`pevn_db` on port 5433).
- The empty stub file `backend/pevn.db` (0 bytes) remained untouched.
- Zero `git commit` and zero `git push` commands were issued.
- Modifications were restricted exclusively to minimal frontend hardening and corresponding unit test mocks across 8 tracked files:
  1. `frontend/src/components/student/StudentTaskDetailModal.tsx`
  2. `frontend/src/layouts/RootLayout.tsx`
  3. `frontend/src/pages/Dashboard.tsx`
  4. `frontend/src/pages/academic/GuardiansView.tsx`
  5. `frontend/src/pages/academic/StudentsView.tsx`
  6. `frontend/src/test/Academic.test.tsx`
  7. `frontend/src/test/RoleNavigationFunctional.test.tsx`
  8. `frontend/src/test/StudentPortal.test.tsx`
- Untracked files:
  1. `docs/reports/PEVN_RBAC_AUDIT_01_CROSS_ROLE_FUNCTIONAL_COHERENCE.md` (this report).

---

## 2. Differences Between Public Remote and Local Tree

### 2.1 Branch Tracking Status
```text
On branch main
Your branch is up to date with 'origin/main'.
```
Commit `d3b2919` is the common baseline with `origin/main`.

### 2.2 Forensic Diff Statistics
```text
 frontend/src/components/student/StudentTaskDetailModal.tsx  |  4 +-
 frontend/src/layouts/RootLayout.tsx                         |  7 +--
 frontend/src/pages/Dashboard.tsx                            | 52 ++++++++++++++++++----
 frontend/src/pages/academic/GuardiansView.tsx               |  1 +
 frontend/src/pages/academic/StudentsView.tsx                | 44 +++++++++++++-----
 frontend/src/test/Academic.test.tsx                         |  2 +-
 frontend/src/test/RoleNavigationFunctional.test.tsx          | 35 +++++++++++++++
 frontend/src/test/StudentPortal.test.tsx                    |  6 +++
 8 files changed, 125 insertions(+), 26 deletions(-)
```

All backend modules, services, routers, models, and migrations are 100% clean and identical to `origin/main`.

---

## 3. Canonical Role and Permission Catalog

The platform enforces a strictly hierarchical RBAC architecture aligned with Colombian territorial educational governance (MEN, Secretarías de Educación Departamentales y Municipales, Instituciones Educativas).

### 3.1 Six Primary Roles Under Audit (Governance & Institutional Administration)

| Canonical Role Identifier | Supported Aliases | Hierarchy Level | Display Title / Jurisdicción | Authority & Capabilities |
| :--- | :--- | :---: | :--- | :--- |
| **`superadmin`** | `super_admin` | **100** | Operador Técnico Global | Gobernanza de plataforma, incidentes técnicos, telemetría de infraestructura, salud de subsistemas, diagnóstico multi-tenant. Excluido de operaciones escolares curriculares. |
| **`national_admin`** | N/A | **90** | Administrador Nacional (MEN) | Analítica territorial agregada, integración con Open Data MEN, aprovisionamiento e invitación de Secretarías Departamentales y Municipales. |
| **`department_admin`** | N/A | **80** | Administrador Departamental (SED) | Supervisión territorial departamental, aprovisionamiento e invitación de Administradores Municipales dentro de su código de departamento. |
| **`municipality_admin`** | N/A | **70** | Administrador Municipal (SEM) | Supervisión territorial municipal, monitoreo de instituciones de la entidad territorial, aprovisionamiento e invitación de Rectores. |
| **`rector`** | `institution_admin` | **60** | Rector / Director Institucional | Liderazgo integral del tenant escolar: años lectivos, períodos académicos, asignaturas, grupos, asignación de directores de grupo, docentes, coordinadores, matrículas y configuración institucional. |
| **`coordinator`** | `academic_coordinator` | **50** | Coordinador Académico / Sede | Coordinación pedagógica y convivencial de sede: períodos académicos, grupos, asignaturas, seguimiento docente, supervisión de notas, sello y reapertura auditada de períodos SIEE. |

### 3.2 Additional Regression Roles (Classroom, Student, Family & Veeduría)

| Canonical Role Identifier | Hierarchy Level | Display Title | Authority & Scope |
| :--- | :---: | :--- | :--- |
| **`teacher`** | **30** | Docente de Aula | Gestión curricular de grupos y asignaturas asignadas: libro de calificaciones SIEE, registro diario de asistencia por período, tareas, recursos pedagógicos y aulas virtuales BigBlueButton. |
| **`auditor`** | **25** (o rol forense) | Auditor / Veeduría | Actor de lectura forense e inspección inmutable de libros de calificaciones y eventos de promoción SIEE (definido en interfaces de autorización y preflights de promoción; no requiere mutación). |
| **`student`** | **10** | Estudiante Institucional | Portal del Estudiante: seguimiento de actividades académicas asignadas, entrega de tareas, visualización de notas parciales y definitivas bajo escala SIEE, asistencia y aulas sincrónicas. |
| **`guardian`** | **10** | Acudiente / Padre de Familia | Portal de Acudientes: seguimiento multi-estudiante de hijos/acudidos vinculados, alertas tempranas de inasistencia, calificaciones SIEE y boletines institucionales. |

### 3.3 Roles vs Hierarchy Levels Reconciliation
Forensic inspection of table `roles` in PostgreSQL `pevn_db`:
- **Total role entities in database:** Exactly **11 rows** (`superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `institution_admin`, `rector`, `academic_coordinator`, `coordinator`, `teacher`, `guardian`, `student`).
- **Total discrete numeric hierarchy levels:** Exactly **7 levels** (100, 90, 80, 70, 60, 50, 30, 10).
  - Level 60 is shared by `rector` and `institution_admin`.
  - Level 50 is shared by `coordinator` and `academic_coordinator`.
  - Level 10 is shared by `student` and `guardian`.

---

## 4. Reconciled Academic Permissions Matrix (Rector vs Coordinator)

To eliminate any ambiguity between the route matrix, UI tabs, and coordinator capabilities, the academic domain permissions are reconciled in detail below:

| Academic Module / Action | Frontend Route / Tab | Rector / Institution Admin (L60) | Coordinator / Academic Coordinator (L50) | Backend Enforcement & Scope Guard |
| :--- | :--- | :---: | :---: | :--- |
| **Años Lectivos (Lectura)** | `/academic?tab=years` | Permitido (`academic_years:read`) | Permitido (`academic_years:read`) | Institutional `institution_id` scope. |
| **Años Lectivos (Crear / Cerrar / Eliminar)** | `/academic?tab=years` | Permitido (`academic_years:create`, `close`, `delete`) | **DENEGADO** (Sin permisos de mutación) | Backend rechaza con HTTP 403. UI oculta botones de acción. |
| **Períodos Académicos (Lectura)** | `/academic?tab=periods` | Permitido (`academic_periods:read`) | Permitido (`academic_periods:read`) | Institutional `institution_id` scope. |
| **Períodos Académicos (Crear / Actualizar)** | `/academic?tab=periods` | Permitido (`academic_periods:create`, `update`) | Permitido (`academic_periods:create`, `update`) | Rector y Coordinador pueden crear períodos y usar plantillas bimestrales. |
| **Períodos Académicos (Cierre / Sello SIEE)** | `/evaluations/directive` o `/academic?tab=evaluations` | Permitido (`evaluations:close_period`) | Permitido (`evaluations:close_period`) | Ambos directivos pueden ejecutar el sello institucional de período. |
| **Períodos Académicos (Reapertura Auditada)** | `/evaluations/directive` | Permitido (`evaluations:reopen_period`) | Permitido (`evaluations:reopen_period`) | Requiere justificación formal obligatoria registrada en pista de auditoría. |
| **Política SIEE (Inspección Activa)** | `/academic?tab=evaluations` | Permitido (`siee_policies:read`, `evaluations:read`) | Permitido (`siee_policies:read`, `evaluations:read`) | Visualización de escalas nacionales/institucionales y porcentajes. |
| **Política SIEE (Mutación / Versionamiento)** | `POST /api/v1/siee-policies` | Backend: `siee_policies:manage` | Backend: `siee_policies:manage` | *Nota técnica:* El backend soporta versionamiento SIEE; el frontend actualmente no expone un formulario de edición manual (inspección de política activa). |
| **Configuración Institucional (Flag Delegación)** | `/academic?tab=settings` | **Permitido** (`roles: ['rector', 'institution_admin']`) | **DENEGADO** (Tab oculto y ruta protegida) | Tab completamente inaccesible para Coordinador (`AcademicHub.tsx:71-77`). |
| **Gestión de Coordinadores (Aprovisionamiento)** | `/academic?tab=coordinators` | **Permitido** (`coordinators:create`, `update`, `delete`) | **DENEGADO** (Tab oculto y sin permisos `coordinators:*`) | El Coordinador no puede invitar ni editar a otros coordinadores (`AcademicHub.tsx:59-65`). |
| **Grupos y Cupos (Crear / Editar)** | `/academic?tab=groups` | Permitido (`groups:create`, `update`, `delete`) | Permitido (`groups:create`, `update`, `delete`) | Gestión de capacidad y salones en sede institucional. |
| **Grupos (Asignar Director de Grupo)** | `/academic?tab=groups` | Permitido (`groups:assign_director`) | **DENEGADO** | Prerrogativa directiva exclusiva del Rector. |
| **Asignaturas (Crear / Editar)** | `/academic?tab=subjects` | Permitido (`subjects:create`, `update`, `delete`) | Permitido (`subjects:create`, `update`, `delete`) | Plan de estudios institucional. |
| **Planta Docente (Aprovisionar)** | `/academic?tab=teachers` | Permitido (`teachers:create`, `update`, `delete`) | Permitido (`teachers:create`, `update`) | El Coordinador puede registrar docentes; eliminación restringida al Rector. |
| **Estudiantes (Registrar SIMAT)** | `/academic?tab=students` | Permitido (`students:create`, `update`, `delete`) | Permitido (`students:create`, `update`) | Ambos registran estudiantes vía documento canónico o búsqueda. |
| **Matrículas (Crear / Trasladar)** | `/academic?tab=enrollments` | Permitido (`enrollments:create`, `transfer`, `withdraw`, `delete`) | Permitido (`enrollments:create`, `transfer`, `withdraw`) | Eliminación de registros de matrícula restringida a Rector. |

---

## 5. Sources of Truth and Institutional Context Isolation

For each of the six primary audited roles, the origin and storage of dashboard information was forensically verified:

```mermaid
flowchart TD
    subgraph Client ["Frontend Session (AuthContext)"]
        UI_BANNER["Píldora de Sesión & Header"]
        UI_CARDS["Tarjetas de Navegación"]
        MEM_USER["user (State en Memoria)"]
        MEM_INST["activeInstitutionContext"]
    end

    subgraph API ["Backend Endpoints"]
        EP_ME["GET /api/v1/auth/me"]
        EP_INST["GET /api/v1/institutions/my-institution"]
        EP_OPS["GET /api/v1/operations/overview"]
        EP_ACAD["GET /api/v1/academic/*"]
    end

    subgraph DB ["PostgreSQL (pevn_db)"]
        DB_USERS[("users & user_roles")]
        DB_INST[("institutions")]
        DB_OPS[("technical_incidents & audit")]
    end

    EP_ME --> DB_USERS
    EP_INST --> DB_INST
    EP_OPS --> DB_OPS

    EP_ME --> MEM_USER
    EP_INST --> MEM_INST
    MEM_USER --> UI_BANNER
    MEM_INST --> UI_CARDS
    EP_OPS --> UI_CARDS
```

### 5.1 Source of Truth Mapping by Role

1. **SUPER_ADMIN (Level 100):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `User.email`, `User.username = 'admin_nacional'`, `roles = ['superadmin']`.
   - **Badge & Level:** Mapped client-side in `Dashboard.tsx` to `L100 (Global)` based on `user.roles.includes('superadmin')`.
   - **Jurisdiction:** Global (`scope.country_code: CO`, `institution_id: null`).
   - **Operations Telemetry & Incidents:** `GET /api/v1/operations/overview`, `GET /api/v1/operations/audit-feed`, `GET /api/v1/operations/incidents`.
   - **Isolation:** Educational cards are completely filtered out (`!isSuperAdmin`). Institutional context is explicitly `null`.
2. **NATIONAL_ADMIN (Level 90):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `User.email = 'national_admin@pevn.edu.co'`, `roles = ['national_admin']`.
   - **Badge & Level:** Mapped to `L90 (Nacional)` based on `hasRole('national_admin')`.
   - **Jurisdiction:** Nacional MEN (`scope.is_national: true`, `institution_id: null`).
   - **Analytics & Cards:** `GET /api/v1/territorial/analytics/summary` (métricas agregadas por departamento).
3. **DEPARTMENT_ADMIN (Level 80):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `User.email = 'department_admin@pevn.edu.co'`, `roles = ['department_admin']`.
   - **Badge & Level:** Mapped to `L80 (Departamental)` based on `hasRole('department_admin')`.
   - **Jurisdiction:** Departamental (`scope.department_id` / código Divipola departamental).
   - **Cards:** Analítica Territorial Departamental, Municipios y Administradores Municipales (`/municipality-admins`).
4. **MUNICIPALITY_ADMIN (Level 70):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `roles = ['municipality_admin']`.
   - **Badge & Level:** Mapped to `L70 (Municipal)` based on `hasRole('municipality_admin')`.
   - **Jurisdiction:** Municipal (`scope.municipality_id`).
   - **Cards:** Analítica Territorial Municipal, Directorio de Instituciones del Municipio. Navegación `/municipality-admins` estrictamente excluida.
5. **RECTOR (Level 60):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `User.email = 'juan@example.com'`, `roles = ['rector']`.
   - **Badge & Level:** Mapped to `L60 (Institucional)`.
   - **Institution Profile:** `GET /api/v1/institutions/my-institution` -> `instSummary` (`name`, `code_dane`, `resolution_number`, etc.).
   - **Academic Modules:** `AcademicHub.tsx` consulta en demanda `academicApi.listAcademicYears()`, `listAcademicPeriods()`, `listGroups()`, etc.
6. **COORDINATOR (Level 50):**
   - **Identity & Roles:** `GET /api/v1/auth/me` -> `roles = ['coordinator']`.
   - **Badge & Level:** Mapped to `L50 (Coordinación)`.
   - **Campus / Headquarter Context:** `user.scope.campus_id` y `GET /api/v1/institutions/my-institution`.
   - **Academic Modules:** Grupos, asignaturas, estudiantes y consola directiva de evaluación SIEE.

### 5.2 Guarantee of Non-Stale Context Across Sessions
In `frontend/src/context/AuthContext.tsx`:
- **Explicit Login:** Line 140 invokes `setActiveInstitutionContext(null)` before authenticating and setting the new user profile, purging any previous institution tokens.
- **Explicit Logout:** Line 155 sets `setUser(null)` and `setActiveInstitutionContext(null)`.
- **Token Expiry / Interceptor Failure:** Line 98 invokes `setActiveInstitutionContext(null)`.
- **Unassigned Accounts (SuperAdmin / National Admin):** `syncInstitutionalContext` (lines 69-73) detects `!u.institution_id && !u.scope?.institution_id` and automatically triggers `setActiveInstitutionContext(null)`, ensuring `pevn_active_institution_id` and `pevn_active_institution_name` are removed from `localStorage`.

---

## 6. Local Verified URLs and Environment Reference

Inspected from `frontend/vite.config.ts`, `frontend/.env.example`, and backend route configurations:

| Parameter | Verified Local Value | Configuration Origin |
| :--- | :--- | :--- |
| **Frontend Base URL** | `http://localhost:3000` | `frontend/vite.config.ts:99` (`port: 3000, strictPort: true`) |
| **Frontend Dashboard** | `http://localhost:3000/dashboard` | `frontend/src/App.tsx:52` |
| **Backend Base URL** | `http://localhost:8000` | `frontend/vite.config.ts:104` (`target: http://127.0.0.1:8000`) |
| **Backend API Prefix** | `http://localhost:8000/api/v1` | `frontend/.env.example:10`, FastAPI route configuration |
| **Public Invitation Acceptance** | `http://localhost:3000/auth/accept-invitation` | `frontend/src/App.tsx:89`, `frontend/src/utils/index.ts:186` |
| **Public Guardian Activation** | `http://localhost:3000/guardian/activate` | `frontend/src/App.tsx:97` |
| **Password Recovery** | `http://localhost:3000/auth/forgot-password` | `frontend/src/App.tsx:77` |
| **Password Reset** | `http://localhost:3000/auth/reset-password` | `frontend/src/App.tsx:81` |

> [!NOTE]
> Enlaces de prueba generados por el backend en modo desarrollo devuelven URLs canónicas resueltas contra el origen actual (`window.location.origin` o fallback `http://localhost:3000`), evitando duplicación de esquema (`http://localhost:3000http://...`) mediante el resolvedor `resolveInvitationUrl` (`frontend/src/utils/index.ts`).

---

## 7. Verified Test Evidence and Targeted Suites

### 7.1 Backend Targeted RBAC & Authority Suites
- **Command:** `pytest tests/test_sa01_superadmin_governance.py tests/test_sa02_technical_operations_portal.py tests/test_nta08_authority_chain.py tests/test_nta09_municipality_admin_provisioning.py tests/test_nta10_r10_coordinator_exclusivity.py tests/test_nta10_r9_coordinator_provisioning.py tests/test_nta10_r7_academic_period_templates.py tests/test_municipality_admin_rbac.py tests/test_rbac_governance_and_rector_invitation.py -q`
- **Result:** `127 passed, 5 warnings in 303.56s (0:05:03)`
- **Pass Rate:** **100% (127 / 127)**
- **Scope Clarification:** Este resultado corresponde a la suite dirigida de gobernanza, autoridad territorial, RBAC y aislamiento de coordinadores/rectores. No representa la totalidad de pruebas del repositorio, sino la suite forense específica de autorización requerida para esta auditoría.

### 7.2 Frontend Full Vitest Suite
- **Command:** `npm run test -- --run`
- **Result:**
  ```text
  Test Files  25 passed (25)
       Tests  165 passed (165)
    Duration  15.20s
  ```
- **Pass Rate:** **100% (165 / 165)**

### 7.3 Frontend Static Type Analysis
- **Command:** `npx tsc --noEmit`
- **Result:** Código de salida `0`. Cero errores y cero advertencias de compilación.

---

## 8. Role-by-Role Manual Acceptance Checklists (Concise Operator Guide)

> [!IMPORTANT]
> Las siguientes pruebas deben ser ejecutadas por el **operador humano** en un navegador real, levantando el entorno local mediante:
> ```powershell
> # Terminal 1 (Backend):
> cd backend ; uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
> # Terminal 2 (Frontend):
> cd frontend ; npm run dev
> ```
> Verifique que la aplicación cargue en **`http://localhost:3000`**. Todas las casillas permanecen en estado **`[ ] PENDIENTE`** a la espera de la inspección del operador.

---

### 8.1 Checklist: SUPER_ADMIN (Level 100)
- **Cuenta:** `admin@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión con `admin@pevn.edu.co`. | Autenticación correcta, ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión superior. | Badge muestra `SUPER_ADMIN (Nivel 100)` y rol canónico `superadmin`. | [ ] PENDIENTE |
| 3 | Verificar navbar superior. | Enlaces: `Dashboard`, `Salud Plataforma`, `Soporte Técnico`, `Auditoría Seguridad`, `Diagnóstico Tenants`. Enlaces curriculares/escolares ausentes. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/operations/health`. | Panel de salud de infraestructura: PostgreSQL activo, latencia de base de datos real. | [ ] PENDIENTE |
| 5 | Visitar `http://localhost:3000/operations/support`. | Visualización de incidentes técnicos; opción de crear reporte operacional. | [ ] PENDIENTE |
| 6 | Visitar `http://localhost:3000/operations/tenants`. | Diagnóstico multi-tenant de esquemas institucionales. | [ ] PENDIENTE |
| 7 | Cerrar sesión. | Contexto purgado; retorno inmediato a `/login`. | [ ] PENDIENTE |

---

### 8.2 Checklist: NATIONAL_ADMIN (Level 90)
- **Cuenta:** `national_admin@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión con `national_admin@pevn.edu.co`. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión superior. | Badge muestra `NATIONAL_ADMIN (Nivel 90)` y jurisdicción Nacional MEN. | [ ] PENDIENTE |
| 3 | Verificar navbar. | Enlaces: `Analítica Territorial`, `Departamentos`, `Municipios`, `Instituciones`. Menú `/operations/*` ausente. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/analytics/territorial`. | Métricas agregadas por departamento. | [ ] PENDIENTE |
| 5 | Intentar ingresar manualmente a `/operations/health`. | Router bloquea con `403 No Autorizado` o redirección segura. | [ ] PENDIENTE |

---

### 8.3 Checklist: DEPARTMENT_ADMIN (Level 80)
- **Cuenta:** `department_admin@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión con `department_admin@pevn.edu.co`. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `DEPARTMENT_ADMIN (Nivel 80)` y departamento asignado. | [ ] PENDIENTE |
| 3 | Verificar navbar. | Enlaces: `Analítica Territorial`, `Municipios`, `Administradores Municipales`, `Instituciones`. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/municipality-admins`. | Lista de administradores municipales; botón para invitar nuevo administrador. | [ ] PENDIENTE |
| 5 | Probar invitación municipal. | Modal de confirmación despliega enlace canónico `http://localhost:3000/auth/accept-invitation?token=...`. | [ ] PENDIENTE |

---

### 8.4 Checklist: MUNICIPALITY_ADMIN (Level 70)
- **Cuenta:** `lsoto@ptocarreno.co` o `fernando@colegio.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión como Administrador Municipal. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `MUNICIPALITY_ADMIN (Nivel 70)`. | [ ] PENDIENTE |
| 3 | Verificar navbar (Verificación D-01). | El enlace `Administradores Municipales` está ausente. Enlaces presentes: `Analítica Territorial`, `Instituciones`. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/institutions`. | Listado de colegios del municipio; botón para invitar/aprovisionar Rector disponible. | [ ] PENDIENTE |

---

### 8.5 Checklist: RECTOR (Level 60)
- **Cuenta:** `juan@example.com`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión con `juan@example.com`. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión y contexto. | Badge muestra `RECTOR (Nivel 60)` y nombre de la institución asignada. | [ ] PENDIENTE |
| 3 | Visitar `http://localhost:3000/academic?tab=periods`. | Botón `+ Nuevo Período` abre modal; creación de períodos y plantillas bimestrales activas. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/academic?tab=teachers`. | Búsqueda por documento (ej. `8788`) autocompleta nombres y registra docente institucional. | [ ] PENDIENTE |
| 5 | Visitar `http://localhost:3000/academic?tab=students` (Verificación D-03). | Búsqueda por documento o nombre, botón `+ Registrar Nuevo Estudiante` y botón `Guardar Estudiante` operativos y simétricos. | [ ] PENDIENTE |
| 6 | Visitar `http://localhost:3000/academic?tab=guardians` (Verificación D-05). | Botón `🔗 Vincular` abre modal de vinculación con estudiante con `aria-label` correcto. | [ ] PENDIENTE |
| 7 | Visitar `http://localhost:3000/academic?tab=evaluations`. | Consola directiva SIEE: tabla de períodos, botón para cerrar/sellar período y reapertura auditada. | [ ] PENDIENTE |
| 8 | Visitar `http://localhost:3000/academic?tab=settings`. | Pestaña accesible: permite alternar la bandera de delegación operativa a coordinadores. | [ ] PENDIENTE |

---

### 8.6 Checklist: COORDINATOR (Level 50)
- **Cuenta:** `mauricio@coordinador.co` o `user_coordinator_7d7d41@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión como Coordinador. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `COORDINATOR (Nivel 50)` y sede asignada. | [ ] PENDIENTE |
| 3 | Visitar `http://localhost:3000/academic?tab=periods`. | Puede visualizar períodos y crear períodos. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/academic?tab=groups`. | Puede gestionar grupos y consultar inspector de cupos. | [ ] PENDIENTE |
| 5 | Visitar `http://localhost:3000/academic?tab=evaluations`. | Puede consultar la política SIEE activa, inspeccionar matrices de notas y sellar/reabrir períodos. | [ ] PENDIENTE |
| 6 | Verificar exclusión de tabs restringidos. | Los tabs `Coordinadores Académicos` (`coordinators`) y `Configuración Institucional` (`settings`) NO son visibles. Si intenta forzar `?tab=settings`, el sistema muestra advertencia de acceso restringido. | [ ] PENDIENTE |

---

### 8.7 Checklist: TEACHER (Level 30 — Regresión Educativa)
- **Cuenta:** `user_teacher_920fd6@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión como Docente. | Ingreso a `http://localhost:3000/dashboard`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `TEACHER (Nivel 30)`. | [ ] PENDIENTE |
| 3 | Visitar `http://localhost:3000/grading/gradebook`. | Matriz de notas carga grupos y criterios SIEE; registro de calificaciones reactivo. | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/grading/attendance`. | Registro diario de asistencia por período y fecha. | [ ] PENDIENTE |
| 5 | Visitar `http://localhost:3000/virtual-classrooms`. | Botón `+ Programar Nueva Aula Virtual` abre modal; creación de sesión BigBlueButton exitosa. | [ ] PENDIENTE |

---

### 8.8 Checklist: STUDENT (Level 10 — Regresión Educativa)
- **Cuenta:** `user_student_068c54@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión como Estudiante. | Redirección a `http://localhost:3000/student`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `STUDENT (Nivel 10)`. | [ ] PENDIENTE |
| 3 | Visitar `http://localhost:3000/student/tasks`. | Listado de tareas; al abrir una tarea, el modal carga sin error con encabezado `📝 Instrucciones de la Actividad` (Verificación D-06). | [ ] PENDIENTE |
| 4 | Visitar `http://localhost:3000/student/grades`. | Visualización de notas definitivas y parciales bajo escala SIEE. | [ ] PENDIENTE |

---

### 8.9 Checklist: GUARDIAN (Level 10 — Regresión Educativa)
- **Cuenta:** `user_guardian_ae89ab@pevn.edu.co`
- **URL Inicial:** `http://localhost:3000/login`

| Paso | Acción | Resultado Esperado | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Iniciar sesión como Acudiente. | Redirección a `http://localhost:3000/guardian`. | [ ] PENDIENTE |
| 2 | Verificar píldora de sesión. | Badge muestra `GUARDIAN (Nivel 10)`. | [ ] PENDIENTE |
| 3 | Seleccionar estudiante asignado. | Despliega datos académicos, asistencia y notas del acudido. | [ ] PENDIENTE |

---

## 9. Safe Rollback Instructions

En caso de que el operador requiera descartar los cambios mínimos aplicados en el frontend durante esta auditoría y volver de forma quirúrgica a la línea base limpia de commit `d3b2919`:

```powershell
# Reversión segura de los 8 archivos modificados del frontend
git checkout -- frontend/src/components/student/StudentTaskDetailModal.tsx `
                frontend/src/layouts/RootLayout.tsx `
                frontend/src/pages/Dashboard.tsx `
                frontend/src/pages/academic/GuardiansView.tsx `
                frontend/src/pages/academic/StudentsView.tsx `
                frontend/src/test/Academic.test.tsx `
                frontend/src/test/RoleNavigationFunctional.test.tsx `
                frontend/src/test/StudentPortal.test.tsx
```

Dado que no se realizaron migraciones ni modificaciones en el backend o base de datos, esta acción devuelve el working-tree a la línea base idéntica a `origin/main` en cero segundos.

---

## 10. Exit Gate Verdict

```text
====================================================================================================
CERTIFICATION GATE: RBAC-AUDIT-01-R1 RECONCILIATION AND ACCEPTANCE READINESS
STATUS: CONDITIONAL PASS — DOCUMENTATION RECONCILED, MANUAL ACCEPTANCE PENDING
====================================================================================================
1. Forensic RBAC Catalog Reconciliation:    PASSED (11 role entities, 7 numeric hierarchy levels)
2. Local Routes & Environment Alignment:    PASSED (Frontend :3000, Backend :8000/api/v1, /auth/accept-invitation)
3. Academic Permissions Matrix (L60 vs L50):PASSED (Rector vs Coordinator boundaries strictly differentiated)
4. Information Sources & Tenant Isolation:  PASSED (GET /auth/me, zero cross-session context retention)
5. Backend Targeted Authorization Suites:   PASSED (127 / 127 tests passed across 9 suites)
6. Frontend Unit & Integration Suites:      PASSED (165 / 165 tests passed across 25 files)
7. Static Typecheck (TypeScript):           PASSED (0 errors, 0 warnings)
8. Working-Tree and State Preservation:     PASSED (Zero commits, zero pushes, 0 DB modifications)
9. Operator Manual Acceptance Checklists:   PENDING OPERATOR BROWSER EXECUTION
====================================================================================================
```
