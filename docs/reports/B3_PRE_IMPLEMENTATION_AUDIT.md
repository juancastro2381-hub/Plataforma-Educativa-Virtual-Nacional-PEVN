# PEVN — B3 — INFORME DE AUDITORÍA PRE-FLIGHT READ-ONLY
## Portal Docente — Completar Funcionalidades Existentes

**Fecha:** 2026-09-09  
**Fase:** B3 — Portal Docente (Completar Funcionalidades Existentes)  
**Tipo de Análisis:** Auditoría Forense y Arquitectural Read-Only  
**Resultado Pre-Flight:** **B3 PRE-FLIGHT = READY**  

---

## 1. Alcance Exacto de Fase B3

El objetivo de la Fase B3 es completar de manera rigurosa y quirúrgica cuatro capacidades existentes en el Portal Docente que permanecen incompletas a nivel funcional o de experiencia de usuario:

1. **Edición de Actividad Académica en estado BORRADOR (DRAFT).**
2. **Edición de Planeación Curricular (Unidades Didácticas).**
3. **Navegación Contextual desde Mis Grupos hacia submódulos operativos.**
4. **Navegación Contextual desde el Dashboard / Inicio hacia contextos funcionales.**

B3 **NO** es una nueva fase funcional, **NO** rediseña el portal, **NO** crea rutas paralelas ni modelos nuevos, y **NO** modifica componentes certificados de B1 (Convivencia), B2 (Comunicaciones/Noticias), SIEE, Auth ni RBAC.

---

## 2. Estado Actual de la Base de Código

### 2.1 Edición de Actividad DRAFT
- **Backend (`backend/app/api/v1/endpoints/teacher_portal.py` y `TeacherPortalService`):**
  - Ya existe el endpoint `PATCH /api/v1/teacher/activities/{activity_id}` con permisos `("activities", "update")`.
  - El esquema `AcademicActivityUpdateRequest` ya define los campos editables (`title`, `description`, `activity_type`, `due_date`, `max_score`, `instructions`, `resource_url`).
  - La lógica de servicio `TeacherPortalService.update_activity()` valida rigurosamente que la actividad pertenezca al docente autenticado y a su institución (`AcademicActivity.teacher_id == teacher.id` y `AcademicActivity.institution_id == teacher.institution_id`).
  - La actualización preserva el estado `DRAFT` intacto sin publicarla.
  - Registra evento de auditoría `AuditEventType.ACTIVITY_UPDATED`.
- **Frontend Client (`frontend/src/services/teacher.ts`):**
  - Ya define `teacherApi.updateActivity(activityId, data)` apuntando a `PATCH /api/v1/teacher/activities/${activityId}`.
- **Frontend UI (`frontend/src/pages/teacher/TeacherActivitiesView.tsx`):**
  - **Incompletitud detectada:** La tabla de actividades muestra botones `👁️ Ver`, `🚀 Publicar` y `🗑️ Eliminar` para registros en `DRAFT`, pero **no dispone de botón ni modal de Edición**. El modal de detalle tampoco ofrece opción de editar.

### 2.2 Edición de Planeación Curricular
- **Backend (`backend/app/api/v1/endpoints/teacher_portal.py` y `TeacherPortalService`):**
  - Ya existe el endpoint `PATCH /api/v1/teacher/planning/{plan_id}` con permisos `("planning", "update")`.
  - El esquema `AcademicPlanUpdateRequest` ya define los campos actualizables (`unit_name`, `competencies`, `learning_objectives`, `methodology`, `evaluation_criteria`, `resources`, `status`, `start_date`, `end_date`).
  - `TeacherPortalService.update_academic_plan()` valida la pertenencia y el aislamiento multi-tenant del docente, actualiza los campos permitidos y genera `AuditEventType.PLAN_UPDATED`.
- **Frontend Client (`frontend/src/services/teacher.ts`):**
  - Ya define `teacherApi.updatePlanning(planId, data)` apuntando a `PATCH /api/v1/teacher/planning/${planId}`.
- **Frontend UI (`frontend/src/pages/teacher/TeacherPlanningView.tsx`):**
  - **Incompletitud detectada:** La tabla de planeaciones solo tiene acciones `👁️ Ver Detalle` y `🗑️ Eliminar`. El modal de detalle solo tiene botón `Cerrar`. No existe formulario ni modal para editar una planeación existente.

### 2.3 Navegación Contextual desde Mis Grupos
- **Frontend UI (`frontend/src/pages/teacher/TeacherGroupsView.tsx`):**
  - Cada tarjeta de grupo renderiza metadatos (año, cupos, materias impartidas) y un único botón: `👥 Ver Planilla de Estudiantes` (que abre el modal de nómina).
  - **Incompletitud detectada:** No hay opciones directas para que el docente, situado en la tarjeta del "Grupo 10-A", pueda saltar con un clic a ver las **Actividades del 10-A**, la **Asistencia del 10-A**, las **Calificaciones del 10-A**, la **Planeación del 10-A** o el **Observador de Convivencia del 10-A**.
- **Routing y Parámetros (`TeacherPortal.tsx`):**
  - Utiliza `useSearchParams()` con `?tab=<tab_name>`.
  - No sincroniza el `groupId` hacia las vistas hijas, por lo que al cambiar de pestaña el usuario pierde el filtro del grupo previamente seleccionado.

### 2.4 Navegación Contextual desde Dashboard / Inicio
- **Frontend UI (`frontend/src/pages/teacher/TeacherDashboardView.tsx`):**
  - Posee 4 tarjetas KPI (`Asignaciones de Carga`, `Grupos / Salones`, `Actividades Publicadas`, `Pendientes por Calificar`) y 7 accesos rápidos en cuadrícula.
  - Al hacer clic, únicamente invocan `onTabChange('<tab_id>')` sin transmitir parámetros de contexto.
  - **Incompletitud detectada:** 
    - Clic en `Actividades Publicadas` navega a `tab=activities`, pero no pre-filtra por estado `PUBLISHED`.
    - Clic en `Pendientes por Calificar` navega a `tab=grades`, pero no transporta la actividad con entregas pendientes de evaluación.
    - Clic en `Tomar Asistencia Diaria` no transporta el grupo activo.

---

## 3. Arquitectura y Endpoints Reutilizables

No se creará ningún endpoint nuevo. Toda la funcionalidad se apoyará en la infraestructura backend existente y validada:

| Funcionalidad | Endpoint Backend Existente | Método | Permiso Requerido | Cliente Frontend |
| :--- | :--- | :---: | :--- | :--- |
| **Editar Actividad DRAFT** | `/api/v1/teacher/activities/{activity_id}` | `PATCH` | `activities:update` | `teacherApi.updateActivity` |
| **Consultar Actividad** | `/api/v1/teacher/activities/{activity_id}` | `GET` | `activities:read` | `teacherApi.getActivity` |
| **Editar Planeación** | `/api/v1/teacher/planning/{plan_id}` | `PATCH` | `planning:update` | `teacherApi.updatePlanning` |
| **Listar Planeaciones** | `/api/v1/teacher/planning` | `GET` | `planning:read` | `teacherApi.listPlanning` |
| **Asistencia por Grupo** | `/api/v1/teacher/groups/{group_id}/attendance` | `GET` / `POST` | `attendance:read` / `attendance:write` | `teacherApi.getDailyAttendance` |
| **Calificaciones Actividad** | `/api/v1/teacher/activities/{activity_id}/grades` | `GET` / `PUT` | `grades:read` / `grades:write` | `teacherApi.getActivityGrades` |
| **Convivencia por Grupo** | `/api/v1/incidents` | `GET` | `incidents:read` | `teacherApi.getIncidents` |

---

## 4. Análisis de Seguridad, RBAC y Anti-IDOR

1. **Autorización Backend:**
   - La seguridad **no recae en el frontend ni en la URL**.
   - Si un usuario malicioso o curioso manipula los parámetros de la URL (ej. `?tab=attendance&groupId=fake-uuid`), los endpoints correspondientes en el backend rechazan la consulta con HTTP 400/403/404 al verificar que el grupo no forma parte de la asignación académica activa del docente en la institución (`TeacherPortalService._assert_active_assignment`).
2. **Aislamiento Multi-Tenant y Ownership:**
   - Tanto `update_activity` como `update_academic_plan` realizan filtros compuestos obligatorios:
     ```python
     AcademicActivity.id == activity_id
     AcademicActivity.teacher_id == teacher.id
     AcademicActivity.institution_id == teacher.institution_id
     ```
   - Ningún docente puede consultar ni modificar actividades o planeaciones de otra institución ni de otro colega docente.
3. **RBAC:**
   - No se crearán roles ni permisos nuevos. El rol `teacher` ya cuenta de forma canónica con `activities:update`, `planning:update`, `attendance:write`, `grades:write`.

---

## 5. Archivos Candidatos para Modificación

| Componente / Archivo | Tipo | Justificación de la Intervención |
| :--- | :---: | :--- |
| `frontend/src/pages/teacher/TeacherActivitiesView.tsx` | Modificar | Incorporar botón de edición en filas DRAFT y en el modal de detalle; implementar modal de edición de actividad DRAFT conectando con `teacherApi.updateActivity`; aceptar `initialGroupId` e `initialStatus`. |
| `frontend/src/pages/teacher/TeacherPlanningView.tsx` | Modificar | Incorporar botón de edición en filas y en el modal de detalle; implementar modal de edición de planeación curricular conectando con `teacherApi.updatePlanning`; aceptar `initialGroupId`. |
| `frontend/src/pages/teacher/TeacherGroupsView.tsx` | Modificar | Incorporar barra/menú de accesos contextuales en cada tarjeta de grupo (Actividades, Calificaciones, Asistencia, Planeación, Convivencia) que active la navegación con `groupId`. |
| `frontend/src/pages/teacher/TeacherDashboardView.tsx` | Modificar | Conectar KPIs y accesos rápidos para transmitir parámetros de contexto (`status=PUBLISHED`, `activityId`, `groupId`) al llamar a `onTabChange`. |
| `frontend/src/pages/teacher/TeacherPortal.tsx` | Modificar | Leer y sincronizar parámetros contextuales (`groupId`, `activityId`, `status`) desde `useSearchParams` y transmitirlos a las vistas hijas correspondientes. |
| `frontend/src/pages/teacher/TeacherAttendanceView.tsx` | Modificar | Aceptar prop opcional `initialGroupId` para preseleccionar el grupo si proviene de navegación contextual. |
| `frontend/src/pages/teacher/TeacherGradesView.tsx` | Modificar | Aceptar prop opcional `initialGroupId` para sincronizar selección. |
| `backend/tests/test_teacher_portal_api.py` | Modificar (Tests) | Incorporar pruebas de integración explícitas para actualización de actividades DRAFT y actualización de planeación curricular con verificación anti-IDOR. |
| `frontend/src/test/TeacherPortal.test.tsx` | Modificar (Tests) | Incorporar pruebas de renderizado y flujo de edición de actividad DRAFT, edición de planeación y navegación contextual con parámetros de URL. |

---

## 6. Riesgos Identificados y Estrategia de Mitigación

| Riesgo | Probabilidad | Severidad | Mitigación |
| :--- | :---: | :---: | :--- |
| **Publicación accidental al guardar edición en DRAFT** | Baja | Alta | El formulario de edición no alterará el campo `status`; invocará exclusivamente `teacherApi.updateActivity`, el cual en backend no toca `status` y mantiene `ActivityStatus.DRAFT`. |
| **Inyección de ID ajeno por manipulación de URL** | Media | Nula | El backend rechaza cualquier acceso IDOR mediante verificaciones estrictas en base de datos. En frontend, si el `groupId` no coincide con ninguno de los grupos autorizados del docente, el selector retrocede elegantemente al primer grupo válido. |
| **Regresión en módulos B1 o B2** | Muy Baja | Alta | No se modificará ningún archivo de B1 (`TeacherIncidentsView.tsx` ya recibe `initialGroupId`), ni de B2 (`TeacherCommunicationsView.tsx`, `TeacherNewsView.tsx`). Se ejecutarán las baterías de regresión automatizada completas antes de cerrar B3. |
| **Aparición de errores no controlados en UI** | Baja | Media | Uso de bloques try/catch en todas las llamadas asíncronas, retroalimentación visual al usuario con estados de carga y mensajes de éxito/error. |

---

## 7. Elementos Estrictamente Fuera de Alcance

- Modificaciones en Convivencia (B1), Comunicaciones (B2), Noticias (B2).
- Modificaciones en SIEE / Cierre de Periodo / Consolidación Directiva (Fase 16D).
- Modificaciones en Student Portal y Guardian Portal.
- Modificaciones en Aulas Virtuales (BigBlueButton).
- Cambios en el motor de autenticación, esquema de tokens o tablas de RBAC.
- Nuevas migraciones de base de datos Alembic (no se requieren).

---

## 8. Conclusión Pre-Flight

```text
================================================================================
B3 PRE-FLIGHT = READY
================================================================================
Se han auditado exhaustivamente los modelos, servicios, endpoints, esquemas,
permisos y vistas involucradas. No existen bloqueos técnicos, ni dependencias
faltantes en el backend, ni requerimientos de migración de base de datos.
Se autoriza la formulación del plan de implementación formal.
================================================================================
```
