# INFORME DIAGNÓSTICO FORENSE — FASE 13E.2
## TEACHER ACADEMIC SCOPE UX & DATA FLOW DIAGNOSTIC
**Jerarquía Canónica:** `Teacher → Subject → Grade / Group → Students`

**Fecha:** 31 de Agosto de 2026  
**Sistema:** Plataforma Educativa Virtual Nacional (PEVN)  
**Tipo de Análisis:** Diagnóstico Forense de Solo Lectura (*Read-Only Forensic Audit*)  
**Estado:** ✅ **AUDITORÍA COMPLETADA — SIN CAMBIOS DE ESQUEMA REQUERIDOS**

---

## A. Executive Summary

Se realizó una auditoría forense exhaustiva de arquitectura de datos, backend APIs, servicios de dominio, contexto de autenticación/RBAC y capas de presentación/estado en el frontend para diagnosticar por qué a un Rector o Docente recién aprovisionado le aparecían visualmente los estudiantes institucionales previos, y validar el funcionamiento de la cadena canónica:

$$\text{Teacher} \xrightarrow{\text{user\_id}} \text{AcademicAssignment} \xrightarrow{} \text{Subject} \xrightarrow{} \text{Grade / Group} \xrightarrow{} \text{Enrollment} \xrightarrow{} \text{Students}$$

### Hallazgos Principales:
1. **La creación de un docente NO crea asignaciones ni grupos:** El flujo Rector $\rightarrow$ `POST /api/v1/teachers` crea exclusivamente el perfil `Teacher` y la relación `UserRole(role="teacher")`. Deja al docente con $0$ `AcademicAssignment`, $0$ grupos asignados, $0$ direcciones de grupo y $0$ estudiantes.
2. **El backend (Fase 13E.1) funciona al 100% y es hermético:** Las pruebas automatizadas (337/337 pasadas) y el análisis de código confirman que `StudentService`, `GroupService`, `EnrollmentService` y `teacher_portal_service.py` filtran estrictamente a nivel de base de datos (`JOIN Enrollment` + `WHERE group_id IN (authorized_group_ids)`). Un docente sin carga académica recibe `[]` (0 estudiantes, 0 grupos, 0 matrículas).
3. **Causa Raíz de la Observación UX:**
   - **Exposición del módulo administrativo en Dashboard:** En `frontend/src/pages/Dashboard.tsx`, la tarjeta *"Módulo de Gestión Académica (Fase 3B)"* (`/academic?tab=...`) se renderizaba si el usuario poseía el permiso `students:read` (el cual forma parte del catálogo canónico de permisos del rol `teacher`).
   - Al hacer clic en `/academic?tab=students` o `/academic?tab=groups`, el docente era dirigido a las vistas administrativas de Rectoría (`AcademicHub.tsx` / `StudentsView.tsx`).
   - Antes de la Fase 13E.1, `GET /api/v1/students` devolvía todos los estudiantes de la institución por falta de scoping a nivel de docente. Con la Fase 13E.1 ya implementada, `GET /api/v1/students` devuelve `[]` al docente sin carga; sin embargo, la interfaz de `/academic` sigue siendo la consola de administración del Rector (con formularios de registro SIMAT, creación de cupos, etc.) en lugar de la experiencia pedagógica del docente.
   - El portal oficial y diseñado para el docente es `/teacher` (`TeacherPortal.tsx`), el cual opera exclusivamente contra `/api/v1/teacher/*` respetando la jerarquía `Docente → Materia → Grado/Grupo → Estudiantes`.

---

## B. Actual Teacher Creation Flow

El flujo de aprovisionamiento de un docente fue auditado paso a paso:

```
[Rector en /academic?tab=teachers]
       │
       ▼
[Modal: Registrar Perfil Docente]
       │
       ├── Datos: user_id (o nuevo User), contract_type, specialty_area, escalafon_grade
       ├── Flag: provision_account = True
       │
       ▼
[POST /api/v1/teachers]
       │
       ├── 1. Crea registro en tabla `users` (si es nuevo) con institution_id
       ├── 2. Crea registro en tabla `teachers` (user_id, institution_id, contract_type, specialty_area)
       ├── 3. En `provision_teacher_account()`:
       │      - Asigna `UserRole(role='teacher', institution_id=inst_id, is_active=True)`
       │      - Marca `user.is_active = True`, `user.must_change_password = True`
       │      - Genera token criptográfico de un solo uso (`PasswordResetToken`)
       └── 4. Retorna `TeacherResponse` con `account_status = ACTIVA` y `reset_token`
```

### Registros creados en la base de datos:
- `teachers`: **1 registro** (perfil profesional).
- `users`: **1 registro** (cuenta de identidad).
- `user_roles`: **1 registro** (rol canónico `teacher`).
- `password_reset_tokens`: **1 registro** (token SHA-256 temporal).
- `academic_assignments`: **0 registros** (NO se crean asignaciones implícitas).
- `groups`: **0 registros** (NO se crean grupos).
- `group_director_teacher_id`: **NULL** (NO se asigna dirección de grupo).
- `enrollments`: **0 registros** (NO se crean matrículas).

---

## C. Actual AcademicAssignment State

Para cualquier docente recién creado:
- `teacher_id`: UUID único.
- `user_id`: UUID único.
- `institution_id`: UUID de la institución del Rector.
- `status`: `ACTIVA` (cuenta aprovisionada).
- `AcademicAssignment records`: **Ninguno** (`COUNT(*) = 0`).
- `assigned subject(s)`: **Ninguno**.
- `assigned group(s)`: **Ninguno**.
- `academic year`: Sin asignaciones vinculadas.
- `Group Director relationships`: **Ninguna**.

---

## D. Actual Group / Student Scope

Bajo las reglas de negocio canónicas:

| Estado del Docente | Grupos Autorizados | Estudiantes Autorizados | Matrículas Autorizadas |
| :--- | :---: | :---: | :---: |
| **Docente Nuevo (Sin Asignación)** | `[]` (0) | `[]` (0) | `[]` (0) |
| **Docente Asignado a 3-A (Matemáticas)** | `[3-A]` (1) | Estudiantes de 3-A con `Enrollment(ACTIVE)` | Matrículas de 3-A |
| **Docente Asignado a 3-A y 5-B** | `[3-A, 5-B]` (2) | Unión de estudiantes de 3-A y 5-B | Matrículas de 3-A y 5-B |
| **Docente Director de Grupo de 4-A** | `[4-A]` (1) | Estudiantes de 4-A con `Enrollment(ACTIVE)` | Matrículas de 4-A |
| **Rector / Administrador Institucional** | Todos los grupos de la institución | Todos los estudiantes de la institución | Todas las matrículas |

---

## E. API Endpoints Used by Teacher Portal

El portal docente `/teacher` (`TeacherPortal.tsx`) interactúa exclusivamente con los siguientes endpoints:

1. **Dashboard:** `GET /api/v1/teacher/dashboard`
   - Devuelve KPIs: total asignaciones, materias, grupos, estudiantes a cargo, actividades pendientes.
2. **Mi Carga:** `GET /api/v1/teacher/assignments?is_active=true`
   - Devuelve las asignaciones académicas (`AcademicAssignment`) del docente autenticado con metadatos de asignatura, grado, grupo, sede y horas semanales.
3. **Mis Grupos:** `GET /api/v1/teacher/groups`
   - Devuelve los grupos únicos derivados de sus asignaciones activas o dirección de grupo.
4. **Planilla de Estudiantes:** `GET /api/v1/teacher/groups/{group_id}/roster`
   - Devuelve la lista de estudiantes con matrícula activa en el grupo especificado. Valida anti-IDOR (el docente debe estar asignado a dicho grupo o ser su director).
5. **Actividades Académicas:** `GET /api/v1/teacher/activities`, `POST /api/v1/teacher/activities`, `GET/PATCH/DELETE /api/v1/teacher/activities/{id}`
   - Gestión de tareas y evaluaciones dentro de sus materias/grupos autorizados.
6. **Calificaciones:** `GET /api/v1/teacher/activities/{id}/grades`, `PUT /api/v1/teacher/activities/{id}/grades`
   - Planilla de notas para los estudiantes del grupo de la actividad.
7. **Asistencia:** `GET /api/v1/teacher/groups/{group_id}/attendance`, `POST /api/v1/teacher/groups/{group_id}/attendance`
   - Registro de asistencia diaria para los estudiantes del grupo asignado.
8. **Planeación Curricular:** `GET /api/v1/teacher/planning`, `POST /api/v1/teacher/planning`
   - Unidades y planes de clase asociados a sus asignaturas y grupos.

### Endpoints Administrativos Genéricos:
- `GET /api/v1/students`
- `GET /api/v1/students/{student_id}`
- `GET /api/v1/groups`
- `GET /api/v1/groups/{group_id}`
- `GET /api/v1/enrollments`
- `GET /api/v1/enrollments/{enrollment_id}`

*Comportamiento verificado:* Tras la implementación de la Fase 13E.1, estos endpoints genéricos aplican scoping estricto basado en `get_teacher_authorized_group_ids()`. Si un docente los invoca directamente, recibe únicamente los datos de sus grupos o `[]` / `404 Not Found`.

---

## F. Frontend Data Flow & UX Architecture

Actualmente coexisten dos rutas en el frontend:

```mermaid
graph TD
    Login[Login como Docente] --> Dash[/dashboard]
    
    Dash -->|Opción A: Confusa| AcadCard["Tarjeta: Módulo de Gestión Académica (Fase 3B)"]
    AcadCard --> AcadHub[/academic?tab=students]
    AcadHub --> StudentsView["StudentsView (Vista del Rector/Secretaría)"]
    StudentsView --> ApiStudents["GET /api/v1/students"]
    ApiStudents --> ResA["Retorna [] (Fase 13E.1)<br/>(Antes de 13E.1 retornaba todos los estudiantes)"]
    
    Dash -->|Opción B: Correcta| TeachCard["Tarjeta: Portal Docente Institucional (Fase 13D.5)"]
    TeachCard --> TeachHub[/teacher]
    TeachHub --> TeachPortal["TeacherPortal (Tabs: Inicio, Mi Carga, Mis Grupos, etc.)"]
    TeachPortal --> ApiTeach["GET /api/v1/teacher/assignments & /groups"]
    ApiTeach --> ResB["Retorna carga y salones específicos del docente"]
```

### Problema de Experiencia de Usuario (UX):
- En `Dashboard.tsx`, tanto Rectores como Docentes ven la tarjeta de acceso a `/academic` porque ambos tienen el permiso `students:read`.
- En el header/menú principal de navegación, un docente ve enlaces a la consola administrativa `/academic`.
- Esto provoca confusión: un docente entra a `/academic` esperando ver sus clases y ve la consola de secretaría/rectoría.

---

## G. Cache / State Analysis

Se auditó el ciclo de vida del estado en el cliente React:
1. **Tokens JWT:** Almacenados exclusivamente en memoria (`inMemoryAccessToken` en `frontend/src/services/api/client.ts`). Cero persistencia en `localStorage` o `sessionStorage`.
2. **Contexto de Autenticación (`AuthContext.tsx`):**
   - Al cerrar sesión (`logout()`), el estado `user` se establece en `null` y el token en memoria se destruye.
   - Al iniciar sesión con otra cuenta (Docente), se realiza una petición limpia a `/auth/profile` y `/auth/refresh`.
   - **No existe caché cruzada de sesión:** El docente no hereda el estado de usuario del Rector.
3. **Estado de Componentes:** Cada vista (`StudentsView`, `TeacherPortal`, `TeacherGroupsView`) mantiene su propio `useState` local y ejecuta llamadas de red al montarse.
4. **Conclusión de Caché:** La visualización de estudiantes institucionales no se debió a un almacenamiento en caché persistente en el navegador, sino a la llamada a la ruta `/academic` antes de la Fase 13E.1 o a la navegación accidental a las vistas administrativas de Rectoría.

---

## H. Root Cause

1. **Backend (Resuelto en Fase 13E.1):** Anteriormente, los endpoints genéricos `/api/v1/students`, `/api/v1/groups` y `/api/v1/enrollments` solo validaban `institution_id` y permisos atómicos sin cruzar contra `AcademicAssignment`. Esto permitía que cualquier docente con `students:read` recibiera el listado general del colegio si navegaba a `/api/v1/students`.
2. **Frontend Navigation & Role Routing (Diagnóstico Fase 13E.2):**
   - El menú de navegación principal (`RootLayout.tsx`) y las tarjetas de inicio (`Dashboard.tsx`) dirigen al docente hacia el `/academic` (panel del Rector) en lugar de canalizarlo de forma predeterminada y exclusiva hacia el `/teacher` (Portal Docente).
   - En `/academic`, no se restringen las pestañas para roles puramente docentes, lo que permite que el docente acceda a pantallas administrativas que no forman parte de su rol operativo diario.

---

## I. Status of Phase 13E.1 Backend Enforcement

### ✅ ESTADO: 100% OPERATIVO Y VERIFICADO

- **337 / 337 pruebas unitarias y de integración pasando al 100%**.
- Suite `test_teacher_academic_scope.py` (10/10 pruebas pasadas):
  - Docente con grupo 3-A solo ve estudiantes de 3-A.
  - Docente con grupo 5-B solo ve estudiantes de 5-B.
  - Docente sin asignación ve `0` grupos y `0` estudiantes (`[]`).
  - Intentos de acceso directo IDOR denegados con `404 Not Found`.
  - Director de grupo accede legítimamente a los estudiantes de su grupo.
  - Docente con múltiples grupos recibe la unión exacta de sus estudiantes.
  - Rector conserva la visibilidad institucional integral.

---

## J. Exact Files / Components Requiring UX Alignment (Phase 13E.2 Scope)

Para alinear perfectamente la experiencia de usuario con el modelo de datos y la jerarquía `Docente → Asignatura → Grupo → Estudiantes`:

1. [`frontend/src/pages/Dashboard.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/Dashboard.tsx):
   - Ajustar el condicional de la tarjeta *"Módulo de Gestión Académica"* para que sea visible únicamente para roles directivos (`rector`, `superadmin`, `national_admin`, `coordinator`, `academic_coordinator`, `institution_admin`).
   - Promover la tarjeta *"Portal Docente Institucional"* como la tarjeta de acción principal para usuarios con rol `teacher`.
2. [`frontend/src/layouts/RootLayout.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/layouts/RootLayout.tsx):
   - Asegurar que la barra de navegación dirija al docente a `/teacher` y oculte el enlace a `/academic`.
3. [`frontend/src/pages/academic/AcademicHub.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/academic/AcademicHub.tsx):
   - Proteger la ruta `/academic` para que docentes sin roles directivos sean redirigidos automáticamente a `/teacher` con un banner informativo amigable.
4. [`frontend/src/pages/teacher/TeacherGroupsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa/Plataforma Educativa Virtual Nacional PEVN/frontend/src/pages/teacher/TeacherGroupsView.tsx) & [`TeacherAssignmentsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo proyectos/Plataforma Educativa/Plataforma Educativa Virtual Nacional PEVN/frontend/src/pages/teacher/TeacherAssignmentsView.tsx):
   - Presentar claramente la jerarquía visual:
     $$\text{Asignatura (Materia)} \longrightarrow \text{Grado y Salón (Grupo)} \longrightarrow \text{Planilla de Estudiantes Matriculados}$$
   - Ofrecer un estado vacío (*Empty State*) claro y educativo cuando el docente no tenga asignaciones aún: *"Su perfil docente está activo. Comuníquese con la Rectoría para que le sea asignada su carga académica (materias y salones)."*

---

## K. Data Contract Verification

El contrato de datos actual en el backend es **100% completo y autosuficiente** para soportar el flujo pedagógico completo sin necesidad de alterar ningún esquema:

### 1. Carga Académica (`TeacherAssignmentItemResponse`):
```json
{
  "id": "uuid",
  "subject_id": "uuid",
  "subject_name": "Matemáticas",
  "knowledge_area_name": "Ciencias Exactas",
  "group_id": "uuid",
  "group_name": "3-A",
  "grade_id": "uuid",
  "grade_name": "Tercero",
  "campus_name": "Sede Principal",
  "shift": "MANANA",
  "academic_year_name": "2026",
  "weekly_hours": 4,
  "is_active": true
}
```

### 2. Grupo y Salón (`TeacherGroupItemResponse`):
```json
{
  "group_id": "uuid",
  "group_name": "3-A",
  "grade_name": "Tercero",
  "campus_name": "Sede Principal",
  "shift": "MANANA",
  "academic_year_name": "2026",
  "capacity_limit": 35,
  "active_enrolled_count": 28,
  "subjects_taught": ["Matemáticas"],
  "is_director": false
}
```

### 3. Planilla de Estudiantes (`TeacherGroupRosterResponse`):
```json
{
  "group_id": "uuid",
  "group_name": "3-A",
  "grade_name": "Tercero",
  "academic_year_name": "2026",
  "total_students": 28,
  "students": [
    {
      "student_id": "uuid",
      "full_name": "Juan Pérez",
      "document_type": "TI",
      "document_number": "1002345678",
      "code_simat": "SIMAT-3A-01",
      "enrollment_status": "ACTIVE",
      "is_active": true
    }
  ]
}
```

---

## L. Multi-Teacher and Scoping Scenario Validations

### 1. Escenario Mismo Grupo / Múltiples Docentes (Compartido Legítimo)
- **Docente A:** Asignado a *Matemáticas* en Grado 3-A.
- **Docente B:** Asignado a *Ciencias Naturales* en Grado 3-A.
- **Resultado:** Ambos docentes ven legítimamente a los 28 estudiantes matriculados en 3-A.
- **Veredicto:** ✅ **CORRECTO Y APROBADO** (Comportamiento pedagógico estándar).

### 2. Escenario Grupos Diferentes (Aislamiento Total)
- **Docente A:** Asignado a 3-A.
- **Docente B:** Asignado a 5-B.
- **Resultado:**
  - Docente A **únicamente** ve los estudiantes de 3-A. No tiene acceso ni visibilidad sobre 5-B.
  - Docente B **únicamente** ve los estudiantes de 5-B. No tiene acceso ni visibilidad sobre 3-A.
- **Veredicto:** ✅ **CORRECTO Y COMPROBADO POR TESTS** (`TEST-SCOPE-01`, `TEST-SCOPE-02`, `TEST-SCOPE-04`).

### 3. Escenario Docente Sin Carga Asignada
- **Docente C:** Perfil creado por el Rector, sin registros en `academic_assignments` y sin dirección de grupo.
- **Resultado:**
  - `/teacher/assignments` $\rightarrow$ `[]`
  - `/teacher/groups` $\rightarrow$ `[]`
  - `/api/v1/students` $\rightarrow$ `[]`
  - Total estudiantes visibles: **0**.
- **Veredicto:** ✅ **CORRECTO Y COMPROBADO POR TESTS** (`TEST-SCOPE-03`).

---

## M. Risks & Regression Considerations

1. **Riesgo de Regresión en Rectoría:** Cualquier cambio futuro de UX no debe alterar la visibilidad institucional del Rector en `/academic`. El Rector debe continuar viendo el 100% de los estudiantes, docentes, grupos y matrículas de su colegio.
2. **Riesgo de Aislamiento de Directores de Grupo:** Se debe mantener siempre la regla que permite al Director de Grupo consultar la planilla de su grupo aunque no tenga asignada una asignatura específica en dicho salón.
3. **Cero migraciones:** No se requiere ningún cambio estructural en PostgreSQL.

---

## N. Veredicto Final

| Ítem | Evaluación | Detalle |
| :--- | :---: | :--- |
| **1. Backend Scope** | ✅ **WORKING** | Hermético. 337/337 tests aprobados. Scoping en `StudentService`, `GroupService`, `EnrollmentService` y `teacher_portal_service.py`. |
| **2. Frontend Scope** | ⚠️ **NEEDS UX ROUTING ALIGNMENT** | El frontend actual expone tarjetas y rutas administrativas (`/academic`) a docentes en lugar de canalizarlos exclusivamente a `/teacher`. |
| **3. Causa Raíz** | **UX / Role Navigation Confusion** | Docentes navegando a la consola administrativa de Rectoría (`/academic`) en lugar del Portal Docente (`/teacher`), sumado al comportamiento previo a la Fase 13E.1. |
| **4. Solución Requerida** | **Alineación de Navegación Frontend** | Condicionar enlaces de `/academic` a roles directivos, canalizar docentes automáticamente a `/teacher`, y pulir estados vacíos de asignación académica. |
| **5. Cambios en Base de Datos** | ❌ **NO REQUIRED** | Cero cambios de esquema, cero migraciones, cero tablas nuevas. El modelo canónico existente es suficiente. |
| **6. Fase Recomendada** | 🚀 **PROCEED TO PHASE 13E.3** | Implementación controlada de ajustes de navegación y UX en el frontend (`Dashboard.tsx`, `RootLayout.tsx`, `AcademicHub.tsx`, `TeacherPortal.tsx`). |
