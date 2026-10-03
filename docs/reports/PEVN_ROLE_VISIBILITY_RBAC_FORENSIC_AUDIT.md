# PEVN — Role Visibility & RBAC Forensic Audit
## Comprehensive Forensic Analysis: SUPER_ADMIN vs. NATIONAL_ADMIN & Institutional Scoping

> **Standard:** PEVN AI Software Factory v1.2 — Implementation Evidence & Reporting Standard  
> **Document ID:** `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md`  
> **Classification:** Architectural & Security Forensic Audit (Read-Only)  
> **Audit Date:** 2026-10-03  
> **Auditor:** AI Technical Specialist & Systems Auditor  
> **Final Gate:** **AUDIT PASS**

---

## 1. Executive Summary

During manual validation of the Plataforma Educativa Virtual Nacional (PEVN), an administrator logged in as `admin_nacional` observed the following navigation and dashboard modules:
- **Top Navigation Bar:** `Gestión Académica`, `Instituciones`, `Analítica Territorial`, `Aulas Virtuales`, `Panel (admin_nacional)`
- **Dashboard Cards:** `Nivel Nacional • Fase 3C` (Aprovisionamiento Institucional y Rectores), `Módulo de Gestión Académica e Institucional` (8 subcards: *Años Lectivos*, *Grupos y Cupos*, *Estudiantes SIMAT*, *Planta Docente*, *Libro de Matrículas*, *Traslados de Salón*, *Carga Académica*, *Acudientes*), and `Aulas Virtuales y Clases en Vivo (Fase 4)`.

However, upon clicking **"Gestión Académica"** or any of its subcards, the application displays:
```
PERMISSION_DENIED: Contexto institucional no disponible.
```
Similarly, entering **"Aulas Virtuales"** displays:
```
Contexto institucional no disponible.
```

### Forensic Verdict & Core Finding
This forensic audit analyzed the complete end-to-end authorization chain across database models, backend dependency resolvers, RBAC services, React route guards, layout navigation, and component state.

The audit proves conclusively that:
1. **The Backend Is Working Exactly As Designed [CORRECT]:**  
   The backend enforces strict Multi-Tenant Isolation via `_resolve_institution_id()`. An Academic Year, Student, Group, Enrollment, or Virtual Classroom belongs strictly to a **tenant (Institución Educativa)**. Because national administrators (`superadmin` and `national_admin`) have `institution_id = NULL`, any direct call to institutional domain endpoints without an explicit `?institution_id=<UUID>` parameter fails closed with `403 Forbidden` (`AuthorizationError: Contexto institucional no disponible.`). This prevents cross-tenant data corruption and enforces sovereign tenant isolation.

2. **The Frontend Has A Severe Architectural Decoupling [INCORRECT & UX ISSUE]:**  
   The frontend layout (`RootLayout.tsx`) and dashboard (`Dashboard.tsx`) expose tenant-specific operational modules based purely on broad role checks or permissions without verifying whether the user possesses an **Institutional Context (`institution_id !== null`)**. 
   - `RootLayout.tsx` hardcoded `user.roles.includes('superadmin')` into the `Gestión Académica` link.
   - `RootLayout.tsx` checks only `hasPermission('virtual_classrooms:read')` for `Aulas Virtuales`, which evaluates to `true` for `superadmin` and `national_admin`.
   - `Dashboard.tsx` includes `'superadmin'` and `'national_admin'` in `isDirective`, showing all 8 school management cards to national users.
   - The frontend currently has **zero Institution Selector / Context Switcher** to supply `?institution_id=<UUID>` to those views.

3. **Identity & Role Misalignment in Documentation / CLI [INCONSISTENT]:**  
   The account named `admin_nacional` was provisioned using `python -m app.cli.create_superadmin`, which assigns the technical role `SystemRole.SUPERADMIN` (level 100), not `SystemRole.NATIONAL_ADMIN` (level 90). The system conflated the national superuser with the Ministry of Education functional role.

---

## 2. Audit Scope

This audit inspected the following layers without modifying product code:
- **Backend Authorization & RBAC:**
  - `backend/app/core/security/interfaces.py` (`SystemRole`, `Permission`, `OrganizationalScope`)
  - `backend/app/services/rbac_bootstrap_service.py` (Canonical role definitions & permission mappings)
  - `backend/app/services/auth_service.py` (Token generation, scope builder, `/auth/me` serialization)
  - `backend/app/api/deps.py` (`require_permission`, `AuthContextDep`)
  - `backend/app/cli/create_superadmin.py` (Superadmin provisioning CLI)
- **Backend Endpoints & Tenant Resolvers:**
  - `backend/app/api/v1/endpoints/institutions.py`
  - `backend/app/api/v1/endpoints/academic_years.py`
  - `backend/app/api/v1/endpoints/virtual_classrooms.py`
  - `backend/app/api/v1/endpoints/groups.py`
  - `backend/app/api/v1/endpoints/students.py`
  - `backend/app/api/v1/endpoints/teachers.py`
  - `backend/app/api/v1/endpoints/enrollments.py`
  - `backend/app/api/v1/endpoints/analytics.py`
  - `backend/app/api/v1/endpoints/users.py`
- **Frontend Presentation & Route Guards:**
  - `frontend/src/layouts/RootLayout.tsx` (Top navigation bar)
  - `frontend/src/App.tsx` (React Router v6 tree & guards)
  - `frontend/src/pages/Dashboard.tsx` (Role access cards & quick links)
  - `frontend/src/pages/academic/AcademicHub.tsx` & sub-views
  - `frontend/src/pages/virtual-classrooms/VirtualClassroomsView.tsx`
  - `frontend/src/pages/admin/InstitutionsView.tsx`
  - `frontend/src/pages/analytics/TerritorialAnalyticsView.tsx`
  - `frontend/src/components/auth/RequireAuth.tsx`
  - `frontend/src/context/AuthContext.tsx`
- **Authoritative Baselines:**
  - `docs/AUTHORIZATION.md`
  - `docs/PHASE_3_RBAC_MATRIX.md`
  - `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md`
  - PostgreSQL live schema and test database state (`pevn_db`)

---

## 3. Repository Evidence

### 3.1 Backend Tenant Resolver Implementation
Across all 18 institutional domain endpoints in `backend/app/api/v1/endpoints/`:
```python
def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")
```
**Evidence:** `backend/app/api/v1/endpoints/virtual_classrooms.py:45-59`, `academic_years.py:39-54`, `groups.py:44-55`, `students.py:45-56`, `teachers.py:49-60`.

### 3.2 Frontend Uncontextualized API Invocation
In `frontend/src/pages/academic/AcademicYearsView.tsx:60`:
```typescript
const data = await academicApi.listAcademicYears(statusFilter)
```
In `frontend/src/services/academic.ts:127-139`:
```typescript
async listAcademicYears(statusFilter?: AcademicYearStatus, institutionIdOverride?: string) {
  const params: Record<string, string> = {}
  if (statusFilter) params.status = statusFilter
  if (institutionIdOverride) params.institution_id = institutionIdOverride
  const response = await apiClient.get<AcademicYearListResponse>('/api/v1/academic-years', { params })
  return response.data
}
```
**Evidence:** The views never pass `institutionIdOverride`. The query is dispatched as `GET /api/v1/academic-years`. The backend receives `institution_id = None`. Because `current_user.institution_id` is also `None`, the backend raises `AuthorizationError("Contexto institucional no disponible.")` with HTTP 403.

### 3.3 Top Navigation Hardcoding in `RootLayout.tsx:89-179`
```tsx
{/* 1. Academic Hub: Hardcoded superadmin */}
{(user.roles.includes('rector') || user.roles.includes('institution_admin') || user.roles.includes('superadmin') || user.roles.includes('coordinator') || user.roles.includes('academic_coordinator')) && (
  <Link to="/academic">Gestión Académica</Link>
)}

{/* 2. Territorial Analytics: Gated only by institutions:read */}
{hasPermission('institutions:read') && (
  <Link to="/analytics/territorial">Analítica Territorial</Link>
)}

{/* 3. Virtual Classrooms: Gated only by virtual_classrooms:read */}
{hasPermission('virtual_classrooms:read') && (
  <Link to="/virtual-classrooms">Aulas Virtuales</Link>
)}
```

### 3.4 Dashboard Card Hardcoding in `Dashboard.tsx:336-340`
```tsx
const isDirective = user.roles.some((r) =>
  ['rector', 'superadmin', 'national_admin', 'coordinator', 'academic_coordinator', 'institution_admin', 'department_admin', 'municipality_admin'].includes(r)
)
```
`Dashboard.tsx` exposes all 8 institutional academic cards to `superadmin` and `national_admin`.

---

## 4. Current Role Model

The PEVN authoritative security architecture defines 11 canonical technical roles across 5 organizational levels:

| System Role (`name`) | Level | Scope Level | Business Role in Colombia | Primary Purpose |
| :--- | :---: | :---: | :--- | :--- |
| `superadmin` | 100 | Nacional | Operador Técnico del Estado / Root | Mantenimiento técnico, catálogo nacional, auditoría global, salud del sistema. |
| `national_admin` | 90 | Nacional | Funcionario Ministerio de Educación (MEN) | Supervisión nacional, DUE/DANE, nombramiento/revocación de rectores, analítica territorial macro. |
| `department_admin` | 80 | Departamental | Secretaría de Educación Departamental (SED) | Monitoreo territorial, indicadores de cobertura departamental. |
| `municipality_admin` | 70 | Municipal | Secretaría de Educación Municipal (SEM) | Monitoreo territorial de instituciones del municipio certificado. |
| `rector` | 60 | Institucional | Rector / Director de Colegio Oficial | Máxima autoridad del tenant escolar. Administra calendario, planta docente, matrículas y SIEE. |
| `institution_admin` | 60 | Institucional | Alias Institucional | Alias de compatibilidad para Rector. |
| `academic_coordinator` | 50 | Institucional | Coordinador Académico | Coordinación de carga horaria, salones, períodos y sábanas de notas. |
| `coordinator` | 50 | Institucional | Coordinador de Sede / Convivencia | Gestión de salones, asistencia y situaciones de convivencia escolar. |
| `teacher` | 30 / 50 | Grupos Asignados | Docente de Aula / Titular | Gestión pedagógica en aula: tareas, calificaciones, asistencia, planeación y videoclases. |
| `student` | 10 / 20 | Propio (Ownership) | Estudiante Matriculado (SIMAT) | Consultar asignaturas, entregar tareas, ver notas oficiales y conectarse a clases. |
| `guardian` | 10 | Hijos / Tutorados | Acudiente Legal / Padre de Familia | Acompañamiento familiar, supervisión de deberes, boletines y citaciones. |

---

## 5. SUPER_ADMIN Analysis

### 5.1 Responsibility Definition
- **Classification:** Root Technical Operator.
- **Scope:** Global National (`is_national = True`, `institution_id = None`).
- **Core Duties:** Infrastructure provisioning, DANE official catalog synchronization, system configuration, global audit logs inspection (`audit_logs`), emergency user lockouts, system health monitoring (`/ready`, `/health`).

### 5.2 Visibility Assessment
| Module | Current Visibility | Intended Status | Audit Classification | Justification |
| :--- | :---: | :---: | :--- | :--- |
| **Dashboard** (`/dashboard`) | Visible | **SHOULD SEE** | `[CORRECT]` | Shows identity, security controls, password reset, and national catalog. |
| **Instituciones** (`/admin/institutions`) | Visible | **SHOULD SEE** | `[CORRECT]` | Master national catalog, DANE synchronization, Rector invitation / succession. |
| **Analítica Territorial** (`/analytics/territorial`) | Visible | **SHOULD SEE** | `[CORRECT]` | High-level macro coverage and enrollment metrics across 32 departments. |
| **Gestión Académica** (`/academic`) | Visible | **SHOULD NOT SEE (Top-Level)** | `[INCORRECT]` | School management hub. Without an institution context, every tab crashes with `403 Forbidden`. |
| **Aulas Virtuales** (`/virtual-classrooms`) | Visible | **SHOULD NOT SEE (Top-Level)** | `[INCORRECT]` | Virtual classrooms are tenant-scoped. National operator has no standalone class meetings. |
| **Portales Pedagógicos** (`/teacher`, `/student`, `/guardian`) | Hidden | **SHOULD NOT SEE** | `[CORRECT]` | Excluded from navigation; route guards block access. |
| **Consola de Auditoría / Sistema** | Missing UI | **SHOULD SEE** | `[MISSING]` | Backend has `audit_logs` and catalog audit endpoints, but frontend lacks a dedicated audit UI for Superadmin. |

---

## 6. NATIONAL_ADMIN Analysis

### 6.1 Responsibility Definition
- **Classification:** National Educational Governance (Ministerio de Educación Nacional - MEN).
- **Scope:** Sovereign National (`is_national = True`, `institution_id = None`).
- **Core Duties:** National catalog verification, institutional status (active/suspended), Rector appointment and revocation, territorial coverage metrics, macro analytics.
- **Explicit Restriction (per `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` line 124):**  
  *"No puede modificar notas de estudiantes, no puede redactar actividades docentes ni intervenir en la convivencia interna del colegio."*

### 6.2 Visibility Assessment
| Module | Current Visibility | Intended Status | Audit Classification | Justification |
| :--- | :---: | :---: | :--- | :--- |
| **Dashboard** (`/dashboard`) | Visible | **SHOULD SEE** | `[CORRECT]` | Shows identity and national catalog access card. |
| **Instituciones** (`/admin/institutions`) | Visible | **SHOULD SEE** | `[CORRECT]` | Primary operational console for MEN: provision institutions and manage Rectors. |
| **Analítica Territorial** (`/analytics/territorial`) | Visible | **SHOULD SEE** | `[CORRECT]` | Primary macro analytics tool for national coverage and enrollment. |
| **Gestión Académica (Navbar)** | Hidden | **SHOULD NOT SEE** | `[CORRECT]` | Correctly omitted from `RootLayout.tsx` top navbar for `national_admin`. |
| **Gestión Académica (Dashboard)** | Visible (8 cards) | **SHOULD NOT SEE** | `[INCORRECT & UX ISSUE]` | `Dashboard.tsx` exposes school registrar cards (Años Lectivos, Grupos, Docentes, SIMAT) that fail with `403`. |
| **Aulas Virtuales** | Visible | **SHOULD NOT SEE** | `[INCORRECT & UX ISSUE]` | Visible in navbar and dashboard; clicking it returns `Contexto institucional no disponible.` |
| **Portales Pedagógicos** | Hidden | **SHOULD NOT SEE** | `[CORRECT]` | Hidden and blocked by route guards. |

---

## 7. TERRITORIAL_ADMIN Analysis (`department_admin`, `municipality_admin`)

### 7.1 Responsibility Definition
- **Classification:** Secretarías de Educación Departamentales (SED) y Municipales (SEM).
- **Scope:** Territorial Sub-National (`department_id` or `municipality_id`, `institution_id = None`).
- **Core Duties:** Monitor educational indicators, enrollment censo, and institutional capacity within their territorial DANE code.

### 7.2 Visibility Assessment
| Module | Current Visibility | Intended Status | Audit Classification | Justification |
| :--- | :---: | :---: | :--- | :--- |
| **Dashboard** (`/dashboard`) | Visible | **SHOULD SEE** | `[CORRECT]` | Base session view. |
| **Analítica Territorial** (`/analytics/territorial`) | Visible | **SHOULD SEE** | `[CORRECT]` | Aggregates KPIs strictly filtered by department/municipality via `auth.scope`. |
| **Instituciones** (`/admin/institutions`) | Hidden | **SHOULD NOT SEE / READ-ONLY** | `[OWNER DECISION REQUIRED]` | Currently hidden. Creating new DANE institutions is national; territorial read-only catalog may be desirable. |
| **Gestión Académica (Dashboard)** | Visible (Cards) | **SHOULD NOT SEE** | `[INCORRECT & UX ISSUE]` | Included in `Dashboard.tsx` `isDirective`. Links fail with `Contexto institucional no disponible`. |
| **Aulas Virtuales** | Visible | **SHOULD NOT SEE** | `[INCORRECT & UX ISSUE]` | Navbar and dashboard links exposed; fail with 403. |

---

## 8. Institutional Role Analysis

### 8.1 RECTOR / INSTITUTION_ADMIN
- **Context:** `institution_id !== null`.
- **Visible Modules:** `Gestión Académica` (all tabs), `Aulas Virtuales`, `Dashboard`.  
- **Findings:**
  - `Gestión Académica` and `Aulas Virtuales`: `[CORRECT]`. Requests succeed because `current_user.institution_id` is supplied to backend.
  - `Analítica Territorial`: Visible in navbar because Rector has `institutions:read`. `[INCONSISTENT / UX ISSUE]`. National/departmental macro analytics is outside the scope of a single school rector.
  - `Instituciones`: Correctly hidden.

### 8.2 ACADEMIC_COORDINATOR / COORDINATOR
- **Context:** `institution_id !== null`.
- **Visible Modules:** `Gestión Académica` (operational tabs), `Aulas Virtuales`, `Dashboard`.  
- **Findings:** `[CORRECT]`. Tab filtering in `AcademicHub.tsx` successfully restricts policy/closing operations.

### 8.3 TEACHER
- **Context:** `institution_id !== null`.
- **Visible Modules:** `Portal Docente` (`/teacher`), `Aulas Virtuales` (`/virtual-classrooms`), `Dashboard`.  
- **Findings:** `[CORRECT]`. Top navbar shows Portal Docente and Aulas Virtuales. Institutional management links are hidden.

### 8.4 STUDENT
- **Context:** `institution_id !== null`.
- **Visible Modules:** `Portal Estudiante` (`/student`), `Dashboard`.  
- **Findings:** `[CORRECT]`. Administrative and management links are completely hidden.

### 8.5 GUARDIAN
- **Context:** Civil relationship, linked to student.
- **Visible Modules:** `Portal Acudiente` (`/guardian`), `Dashboard`.  
- **Findings:** `[CORRECT]`. Institutional administrative links are completely hidden.

---

## 9. Comprehensive Navigation Matrix

The matrix below shows: **Current Frontend Visibility** vs. **Authoritative Intended Architecture**:

| Module / Link | SUPER_ADMIN | NATIONAL_ADMIN | TERRITORIAL_ADMIN | RECTOR | COORDINATOR | TEACHER | STUDENT | GUARDIAN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Panel (Dashboard)** | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) |
| **Catálogo Nacional** (`/admin/institutions`) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Analítica Territorial** (`/analytics/territorial`) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ⚠️ (Intended: ❌) | ⚠️ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Gestión Académica (Navbar)** (`/academic`) | ❌⚠️ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Gestión Académica (Dashboard Cards)** | ❌⚠️ (Intended: ❌) | ❌⚠️ (Intended: ❌) | ❌⚠️ (Intended: ❌) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Aulas Virtuales (Navbar & Dashboard)** | ❌⚠️ (Intended: ❌) | ❌⚠️ (Intended: ❌) | ❌⚠️ (Intended: ❌) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ✅ (Intended: ✅) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Portal Docente** (`/teacher`) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ✅ (Intended: ✅) | ❌ (Intended: ❌) | ❌ (Intended: ❌) |
| **Portal Estudiante** (`/student`) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ✅ (Intended: ✅) | ❌ (Intended: ❌) |
| **Portal Acudiente** (`/guardian`) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ❌ (Intended: ❌) | ✅ (Intended: ✅) |

*Key:*  
- ✅ = Visible and functionally working.  
- ❌ = Hidden and properly denied.  
- ❌⚠️ = Visible in UI, but crashes with `PERMISSION_DENIED: Contexto institucional no disponible` upon navigation.  
- ⚠️ = Visible in UI, but inappropriate for the role's scope.

---

## 10. Application Route Audit

| Route | Component | Role Guards in `App.tsx` | Permission Guards | Required Context | Exposed in Nav? | Behavior When Context Missing | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `/` | `ComingSoon` | None (Public) | None | None | Public | N/A | `[CORRECT]` |
| `/login` | `Login` | None (Public) | None | None | Public | N/A | `[CORRECT]` |
| `/dashboard` | `Dashboard` | `RequireAuth` | None | User session | All auth | Displays identity & cards | `[CORRECT]` (cards flawed) |
| `/admin/institutions` | `InstitutionsView` | `['superadmin', 'national_admin']` | None | National Scope | Nav (Super/Nat) | Works without institution | `[CORRECT]` |
| `/academic` | `AcademicHub` | `RequireAuth` (None!) | None | `institution_id` | Nav (Rector/Super) | **Crashes: HTTP 403** | `[INCORRECT & UX ISSUE]` |
| `/virtual-classrooms` | `VirtualClassroomsView` | `RequireAuth` | `virtual_classrooms:read` | `institution_id` | Nav (Many roles) | **Crashes: HTTP 403** | `[INCORRECT & UX ISSUE]` |
| `/analytics/territorial` | `TerritorialAnalyticsView` | `RequireAuth` | `institutions:read` | Territorial / Nat. | Nav (Many roles) | Works (aggregates) | `[INCONSISTENT]` (guard too wide) |
| `/teacher` | `TeacherPortal` | `['teacher']` | None | `institution_id` | Nav (Teacher) | Redirects to `/dashboard` | `[CORRECT]` |
| `/student` | `StudentPortal` | `['student']` | None | `institution_id` | Nav (Student) | Redirects to `/dashboard` | `[CORRECT]` |
| `/guardian` | `GuardianPortal` | `['guardian']` | None | Civil link | Nav (Guardian) | Redirects to `/dashboard` | `[CORRECT]` |

---

## 11. Permission vs. Scope Matrix

The audit reveals a fundamental misunderstanding in the frontend design between **Granular RBAC Permissions** and **Organizational Scope (Tenant Context)**:

```
+-----------------------------------------------------------------------------------+
| RBAC Permission (WHAT can be done)   |  Can the role read academic years?         |
|                                       |  -> Yes (SUPERADMIN, NATIONAL_ADMIN: TRUE) |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| Organizational Scope (WHERE it can be done) | In WHICH school?                    |
|                                              | -> NONE (institution_id = NULL)    |
|                                              | -> RESULT: FAIL CLOSED (HTTP 403)  |
+-----------------------------------------------------------------------------------+
```

1. In `rbac_bootstrap_service.py:230-303`, `NATIONAL_ADMIN` was granted permissions like `academic_years:read`, `groups:read`, `teachers:read`, `virtual_classrooms:read`.
2. These permissions exist on the backend so that **IF** a national official conducts an audit or provides support to a specific school (passing `?institution_id=<UUID>`), the RBAC check passes.
3. However, the frontend treated having `academic_years:read` as meaning: *"Render this link in the top menu and dashboard as a primary workspace."*
4. Because the frontend never prompt the user to select an institution, the user arrives at the page without an institutional context, and the backend promptly rejects the call.

---

## 12. Context / Scope Dependencies (18 Endpoints Requiring `institution_id`)

The following backend endpoints strictly enforce `_resolve_institution_id()`. For any user where `current_user.institution_id is None`, the call fails with `Contexto institucional no disponible` unless `?institution_id=<UUID>` is explicitly provided:

1. `GET /api/v1/academic-years`
2. `POST /api/v1/academic-years`
3. `GET /api/v1/academic-years/{id}`
4. `GET /api/v1/groups`
5. `POST /api/v1/groups`
6. `GET /api/v1/students`
7. `POST /api/v1/students`
8. `GET /api/v1/teachers`
9. `POST /api/v1/teachers`
10. `GET /api/v1/guardians`
11. `POST /api/v1/guardians`
12. `GET /api/v1/enrollments`
13. `POST /api/v1/enrollments`
14. `POST /api/v1/transfers`
15. `GET /api/v1/academic-assignments`
16. `GET /api/v1/siee-policies`
17. `GET /api/v1/evaluation-grades/period-sheet`
18. `GET /api/v1/virtual-classrooms`

---

## 13. Frontend Authorization Analysis

### Findings in `RequireAuth.tsx` & `AuthContext.tsx`:
1. **Superadmin Hardcoded Bypass in Client Helpers [SECURITY RISK & UX RISK]:**  
   In `frontend/src/context/AuthContext.tsx:114`:
   ```typescript
   if (user.roles.includes('superadmin')) return true
   ```
   And line 126:
   ```typescript
   if (user.roles.includes('superadmin') || user.permissions.includes('*')) return true
   ```
   While SuperAdmin has `*:*` on the backend, bypassing role and permission checks in client-side helpers causes all component-level checks like `hasPermission('virtual_classrooms:read')` to evaluate to `true`. This tricks the UI into displaying modules that require an `institution_id` that SuperAdmin does not have.
2. **Missing Institutional Context Guard [MISSING]:**  
   `RequireAuth.tsx` supports `roles` and `permissions`, but lacks an `institutionalOnly` or `requireTenantContext` flag.

---

## 14. Backend Authorization Analysis

### Findings in Backend Services:
1. **Multi-Tenant Isolation is Solid [CORRECT]:**  
   The backend never falls back to returning data across all institutions when `institution_id` is missing. It strictly raises `AuthorizationError("Contexto institucional no disponible.")`.
2. **Support for `institution_id_override` Exists [CORRECT]:**  
   The backend already accepts `?institution_id=<UUID>` for `SUPERADMIN` and `NATIONAL_ADMIN`. The missing link is purely in the frontend presentation and routing layer.

---

## 15. PERMISSION_DENIED Root Cause Analysis

### Sequence Diagram of the Defect:

```
[Administrator (admin_nacional)]
          │
          │ 1. Logs in (roles=['superadmin'] or ['national_admin'], institution_id=null)
          ▼
   [RootLayout / Dashboard]
          │
          │ 2. Evaluates navigation:
          │    - Is superadmin in roles? -> YES -> Render "Gestión Académica" link
          │    - Does user have virtual_classrooms:read? -> YES -> Render "Aulas Virtuales" link
          │    - Is user directive? -> YES -> Render 8 academic management cards
          ▼
    [User clicks "Años Lectivos" or "Aulas Virtuales"]
          │
          │ 3. Frontend navigates to /academic?tab=years or /virtual-classrooms
          ▼
  [AcademicYearsView / VirtualClassroomsView]
          │
          │ 4. Executes academicApi.listAcademicYears() or virtualClassroomApi.listVirtualClassrooms()
          │    (Sends GET /api/v1/academic-years with ZERO query parameters)
          ▼
   [Backend Endpoint]
          │
          │ 5. Executes _resolve_institution_id(auth, current_user, institution_id=None)
          │    - auth.scope.is_national() == True, BUT institution_id_override is None!
          │    - current_user.institution_id is None!
          │    - Result: raise AuthorizationError("Contexto institucional no disponible.")
          ▼
[HTTP 403 Forbidden Response: {"detail": "Contexto institucional no disponible."}]
          │
          │ 6. Frontend receives 403 ApiError
          ▼
[UI Error Display: "PERMISSION_DENIED: Contexto institucional no disponible."]
```

---

## 16. Security Findings

1. **`[CORRECT]` Tenant Containment Integrity:** The backend correctly prevents national accounts from accidentally dumping all institutional data or modifying records without specifying a target tenant.
2. **`[SECURITY RISK]` Client-Side Blind Bypasses:** Client-side helpers `hasRole()` and `hasPermission()` unconditionally return `true` for `superadmin`. While backend authorization remains intact, client-side guards degrade and expose broken UI flows.
3. **`[INCONSISTENT]` CLI Role Conflation:** The CLI `python -m app.cli.create_superadmin` assigned `SystemRole.SUPERADMIN` with username `admin_nacional`. This conflates the technical root operator (`superadmin`, level 100) with the civil ministry administrator (`national_admin`, level 90).

---

## 17. UX Findings

1. **`[UX ISSUE]` Dead-End Navigation:** National administrators are presented with prominent links to `Gestión Académica` and `Aulas Virtuales` that lead exclusively to HTTP 403 error screens.
2. **`[UX ISSUE]` Cluttered Dashboard:** The National Administrator dashboard is cluttered with 8 cards related to school-level classroom groups, student enrollment SIMAT, and teacher workload that cannot be operated at national scope.
3. **`[INCONSISTENT]` Rector Navigation Leak:** Institutional Rectors see `Analítica Territorial` in the top navbar because they hold `institutions:read`, leading to confusion between institutional governance and national macro analytics.

---

## 18. Regression Risk Assessment

- **Regression Risk for Future Remediation:** **LOW**.
- **Justification:**  
  The backend logic, database models, permissions catalog, and tenant resolvers are fully functional and secure. Remediation requires changes only in the frontend presentation layer (`RootLayout.tsx`, `Dashboard.tsx`, `App.tsx`) to filter navigation by tenant context, without touching backend business logic or database schemas.

---

## 19. Recommended Corrections (For Subsequent Implementation Phase)

When authorized to implement:

### 1. Correct Top Navigation in `RootLayout.tsx`
- **`Gestión Académica`:** Restrict strictly to institutional directiva:
  `user.institution_id && (user.roles.includes('rector') || user.roles.includes('institution_admin') || user.roles.includes('coordinator') || user.roles.includes('academic_coordinator'))`
  *(Remove `superadmin` from the top navbar link).*
- **`Aulas Virtuales`:** Require institutional context:
  `user.institution_id && hasPermission('virtual_classrooms:read')`
- **`Analítica Territorial`:** Restrict to territorial/national roles:
  `(user.scope.is_national || user.roles.includes('national_admin') || user.roles.includes('superadmin') || user.roles.includes('department_admin') || user.roles.includes('municipality_admin'))`
  *(Prevent institutional Rectors from seeing territorial macro analytics in the top bar).*

### 2. Correct `Dashboard.tsx` Cards
- **National Administration Card:** Keep visible for `superadmin` and `national_admin`.
- **Academic Management Card & 8 Subcards:** Require `user.institution_id !== null`:
  `const isInstitutionalDirective = Boolean(user.institution_id) && user.roles.some(...)`
- **Virtual Classrooms Card:** Require `user.institution_id !== null && hasPermission('virtual_classrooms:read')`.

### 3. Route Guards in `App.tsx`
- For `/academic` and `/virtual-classrooms`, wrap with an institutional context guard:
  `user.institution_id !== null` (or redirect national users to `/admin/institutions`).

### 4. Optional Context Switcher (Future Enhancement — OWNER DECISION REQUIRED)
If the project owner desires for `SUPER_ADMIN` or `NATIONAL_ADMIN` to inspect an individual school's academic data:
- Add an action button inside `InstitutionsView.tsx` ("Inspeccionar Gestión Académica") that navigates to `/academic?tab=years&institution_id=<UUID>`.
- Update `AcademicHub.tsx` to read `searchParams.get('institution_id')` and pass it down to `academicApi` calls as `institutionIdOverride`.
- *Recommendation:* Do NOT show `/academic` on the top navbar without context; only enter via `InstitutionsView.tsx` with an explicit school selected.

---

## 20. Final Gate

### **FINAL GATE: AUDIT PASS**

**Gate Justification:**
- [x] SUPER_ADMIN responsibilities and visibility fully audited and documented.
- [x] NATIONAL_ADMIN responsibilities and visibility fully audited and documented.
- [x] TERRITORIAL_ADMIN responsibilities and visibility fully audited and documented.
- [x] Institutional roles (`rector`, `coordinator`, `teacher`, `student`, `guardian`) visibility documented.
- [x] Complete Navigation Matrix and Route Matrix produced.
- [x] Complete Permission vs. Scope dependency traced across all 18 endpoints.
- [x] `PERMISSION_DENIED: Contexto institucional no disponible` root cause identified with exact code locations.
- [x] Frontend/Backend authorization alignment evaluated.
- [x] Zero product code modified. Zero migrations run. Zero Git commits/pushes.
- [x] Audit report generated at `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md`.
