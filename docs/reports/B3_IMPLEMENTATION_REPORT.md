# INFORME DE EJECUCIÓN TÉCNICA Y PERSISTENCIA TRANSACCIONAL — FASE B3
## PORTAL DOCENTE: COMPLETAR FUNCIONALIDADES EXISTENTES Y REMEDIACIÓN B3-H01
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** Septiembre 2026  
**Estado del Gate:**
* **`B3 TECHNICAL VERIFICATION = PASS`**
* **`B3 HUMAN VALIDATION = PENDING`**
* **`B3 CERTIFICATION = NOT CERTIFIED`**

---

## 1. RESUMEN EJECUTIVO Y ALCANCE AUTORIZADO

El presente documento consolida la finalización de la **Ejecución Técnica de la Fase B3** del Portal Docente y la resolución integral de la remediación transaccional **B3-H01**.

La Fase B3 tuvo como objetivo estricto y exclusivo **completar cuatro funcionalidades operativas existentes** que se encontraban incompletas en la interfaz web del docente, sin alterar modelos de datos, sin crear endpoints nuevos, sin modificar roles/permisos y sin alterar módulos certificados previamente (B1, B2, SIEE, Student Portal, Guardian Portal).

### Alcance Funcional Ejecutado:
1. **Edición de Actividad Académica en estado DRAFT (Borrador):**
   - Habilitada exclusivamente para actividades con estado `DRAFT`.
   - Conectada al endpoint contractual existente `PATCH /api/v1/teacher/activities/{activity_id}`.
   - Conservación inmutable del estado `DRAFT` (no publica automáticamente).
   - Persistencia confirmada en base de datos PostgreSQL en sesiones HTTP independientes.
   - Respeto estricto de asignación docente, tenant isolation y Anti-IDOR.
2. **Edición de Planeación Curricular:**
   - Interfaz de edición modal completa conectada al endpoint existente `PATCH /api/v1/teacher/planning/{plan_id}`.
   - Persistencia de unidades temáticas, metodologías, criterios de evaluación y estados curriculares.
   - Respeto estricto de asignación académica y tenant isolation.
3. **Navegación Contextual desde "Mis Grupos":**
   - Matriz de acciones contextuales por salón para: **Actividades**, **Calificaciones**, **Asistencia**, **Planeación** y **Convivencia / Observador**.
   - Transmisión de `groupId` exclusivamente como parámetro de contexto y filtro en la URL.
   - Preservación del principio de seguridad: *El frontend nunca asume control de acceso; el backend continúa siendo la única autoridad de autorización*.
4. **Navegación Contextual desde "Dashboard / Inicio":**
   - Vinculación del KPI "Actividades Publicadas" hacia la pestaña de Actividades con filtro `status=PUBLISHED`.
   - Vinculación del KPI "Pendientes por Calificar" hacia la pestaña de Calificaciones de forma general, documentando la limitación arquitectónica de no poseer un `activity_id` específico en el contrato de resumen existente.

---

## 2. INCIDENCIA B3-H01: DIAGNÓSTICO Y REMEDIACIÓN TRANSACCIONAL

### 2.1 Diagnóstico B3-H01
Durante la primera prueba de validación funcional humana (B3-H01):
1. El docente ingresó al Portal Docente → Actividades Académicas.
2. Creó una nueva actividad completando el formulario y pulsando **"Guardar Actividad (Borrador)"**.
3. El frontend recibió código `HTTP 201 Created` y mostró la notificación de éxito.
4. Al recargar la página o volver a filtrar por `Estado = Borrador`, la actividad no aparecía en el listado.
5. La inspección forense en la base de datos PostgreSQL (`pevn_db`) demostró que la tabla `academic_activities` **no contenía la fila**, a pesar de que el endpoint reportó creación exitosa.

### 2.2 Causa Raíz
* En la capa de servicios (`TeacherPortalService`), el método `create_activity` ejecutaba `await self._session.flush()` para generar el identificador UUID y las relaciones, pero **no ejecutaba commit**.
* En el controlador `backend/app/api/v1/endpoints/teacher_portal.py`, el endpoint `create_teacher_activity` finalizaba retornando el schema Pydantic sin invocar `await db.commit()`.
* La dependencia `get_async_session` cerraba la sesión HTTP al terminar la petición. Al no existir un commit explícito, el context manager de SQLAlchemy y el driver asyncpg ejecutaban un **rollback automático implícito** en PostgreSQL.
* Las pruebas unitarias/integración previas no detectaban este comportamiento porque utilizaban un fixture `client` donde la sesión de prueba compartida mantenía los objetos en memoria dentro de la misma transacción abierta.
* Se identificó idéntico patrón en los 9 endpoints mutantes del controlador del Portal Docente.

### 2.3 Corrección Transaccional Aplicada
Siguiendo la arquitectura canónica de PEVN (donde el endpoint controlador es el delimitador transaccional responsable del commit), se incorporó `await db.commit()` de forma explícita en los **9 endpoints mutantes** de [teacher_portal.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py):

| # | Endpoint Mutante | Método HTTP | Línea Intervenida | Acción Transaccional |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `/activities` | `POST` | 240 | `await db.commit()` posterior a `create_activity` |
| 2 | `/activities/{activity_id}` | `PATCH` | 331 | `await db.commit()` posterior a `update_activity` |
| 3 | `/activities/{activity_id}/publish` | `POST` | 380 | `await db.commit()` posterior a `publish_activity` |
| 4 | `/activities/{activity_id}/close` | `POST` | 429 | `await db.commit()` posterior a `close_activity` |
| 5 | `/activities/{activity_id}/grades` | `PUT` | 519 | `await db.commit()` posterior a `batch_update_grades` |
| 6 | `/groups/{group_id}/attendance` | `POST` | 580 | `await db.commit()` posterior a `record_daily_attendance` |
| 7 | `/planning` | `POST` | 654 | `await db.commit()` posterior a `create_plan` |
| 8 | `/planning/{plan_id}` | `PATCH` | 702 | `await db.commit()` posterior a `update_plan` |
| 9 | `/planning/{plan_id}` | `DELETE` | 747 | `await db.commit()` posterior a `delete_plan` |

**Restricciones cumplidas:**
- Cero cambios en modelos y esquemas de base de datos.
- Cero migraciones nuevas.
- Cero alteraciones en RBAC, Anti-IDOR o Tenant Isolation.
- Cero alteraciones en módulos certificados (Student Portal, Guardian Portal, B1, B2, SIEE).

### 2.4 Evidencia de Pruebas con Sesiones HTTP Independientes
Para certificar que la persistencia es física y resiste el ciclo de vida de peticiones HTTP desacopladas (tal como opera en producción), se diseñó en [backend/tests/test_teacher_portal_api.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_teacher_portal_api.py) el generador de clientes aislados:

```python
@asynccontextmanager
async def make_isolated_client(db_session: AsyncSession):
    async def fresh_session_override():
        async with sessionmanager._sessionmaker() as s:
            try:
                yield s
            except Exception:
                await s.rollback()
                raise
            finally:
                await s.close()

    app.dependency_overrides[get_async_session] = fresh_session_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as iso_c:
            yield iso_c
    finally:
        app.dependency_overrides.pop(get_async_session, None)
```

En este esquema:
1. La petición mutante (Petición A) abre una sesión `AsyncSession`, ejecuta la mutación, comete físicamente a PostgreSQL y cierra la conexión.
2. La petición de lectura posterior (Petición B) abre una sesión completamente nueva y verifica que la información persistió físicamente en la base de datos.
3. Se verifica el principio de atomicidad y rollback garantizando que errores de validación no dejen registros huérfanos o persistencia parcial.

### 2.5 Corrección Quirúrgica del Test de Asistencia
Durante la primera ejecución del suite independiente (6 PASS, 1 FAIL), se diagnosticó un fallo `HTTP 422` en:
`test_teacher_attendance_persistence_independent_sessions`

* **Diagnóstico:** El endpoint de producción `POST /api/v1/teacher/groups/{group_id}/attendance` requiere el contrato `DailyAttendanceBatchRequest`, el cual exige la clave `"records"` (lista de registros) y el campo `"subject_id"`. El test utilizaba erróneamente la clave `"items"` y omitía `"subject_id"`.
* **Tratamiento:** Se categorizó como **defecto del test**, prohibiéndose modificar el código de producción.
* **Corrección:** Se ajustó quirúrgicamente el payload en el archivo de prueba, pasando `records` y `subject_id`.
* **Resultado:** La aserción estricta de estado (`EXCUSED`) y observaciones (`"Cita médica comprobada en secretaría."`) pasó sin mocks ni debilitamiento.

### 2.6 Resultado Final de Pruebas de Persistencia Independiente (7/7 PASS)
**Comando:**
```powershell
pytest tests/test_teacher_portal_api.py -k "independent_sessions" -v
```

**Resultado Consolidado:**
```text
tests/test_teacher_portal_api.py::test_teacher_activity_draft_persistence_independent_sessions PASSED [ 14%]
tests/test_teacher_portal_api.py::test_teacher_activity_draft_update_persistence_independent_sessions PASSED [ 28%]
tests/test_teacher_portal_api.py::test_teacher_activity_publish_and_close_persistence_independent_sessions PASSED [ 42%]
tests/test_teacher_portal_api.py::test_teacher_batch_grading_persistence_independent_sessions PASSED [ 57%]
tests/test_teacher_portal_api.py::test_teacher_attendance_persistence_independent_sessions PASSED [ 71%]
tests/test_teacher_portal_api.py::test_teacher_planning_lifecycle_persistence_independent_sessions PASSED [ 85%]
tests/test_teacher_portal_api.py::test_teacher_atomicity_and_rollback_on_error_independent_sessions PASSED [100%]

====================== 7 passed, 12 deselected in 22.63s ======================
```

### 2.7 Incidencia Conocida de Teardown en Windows (Problema de Proceso, no Funcional)
Al igual que en ejecuciones previas, una vez que pytest emitió en consola el resultado final `7 passed in 22.63s`, el subproceso de Python/asyncio en Windows quedó retenido esperando el cierre de descriptores de sockets y threads durante el shutdown hacia PowerShell:
* **TEST RESULT = PASS** (7/7 pruebas superadas de forma limpia en 22.63s).
* **PROCESS STATE = HUNG/TIMEOUT** (Retención exclusiva de teardown de Windows).
* **Acción aplicada:** Terminación segura del proceso mediante el gestor de tareas sin alterar base de datos ni archivos.

---

## 3. POLÍTICA DE NO MODIFICACIÓN Y CUMPLIMIENTO DE REGLAS

Durante la ejecución de B3 y la remediación B3-H01 se mantuvieron inalteradas las siguientes restricciones mandatorias:

| Restricción | Estado | Evidencia / Verificación |
| :--- | :---: | :--- |
| **RBAC Existente** | INTACTO | No se agregaron nuevos permisos ni roles en backend ni frontend. |
| **Anti-IDOR y Tenant Isolation** | INTACTO | Validado con fixtures multi-tenant en pruebas automatizadas. |
| **Backend como Autoridad** | INTACTO | Toda petición pasa por validación de token JWT, roles y asignación académica. |
| **Endpoints Backend** | PRESERVADOS | 0 endpoints creados. Se reutilizó la superficie contractual existente. |
| **Modelos y Esquemas DB** | INTACTOS | 0 migraciones nuevas (`021_phase15_communications_news_incidents` en HEAD). |
| **B1 Convivencia** | PRESERVADO | Pruebas de regresión 3/3 PASS (`test_coexistence_incidents_api.py`). |
| **B2 Comunicaciones y Noticias**| PRESERVADO | Pruebas de regresión 4/4 PASS (`test_institutional_communications_api.py`, `test_institutional_news_api.py`). |
| **Student / Guardian Portals** | PRESERVADOS | Sin modificaciones en sus servicios ni vistas funcionales. |
| **SIEE y Evaluación Institucional**| PRESERVADO | Pruebas de regresión 6/6 PASS (`TeacherSieeEvaluation.test.tsx`). |
| **Auth / Ciclo de Vida Familiar** | PRESERVADO | Control de acceso y sesiones inalterados. |
| **Aulas Virtuales** | PRESERVADO | Sin modificaciones. |

---

## 4. ARCHIVOS MODIFICADOS Y DETALLE TÉCNICO

### 4.1 Backend
- **`backend/app/api/v1/endpoints/teacher_portal.py`**
  - Incorporación de `await db.commit()` en los 9 endpoints mutantes (creación, edición, publicación, cierre de actividades, calificaciones por lote, registro de asistencia y ciclo de vida de planeación).
- **`backend/tests/test_teacher_portal_api.py`**
  - Incorporación del arnés `make_isolated_client(db_session)`.
  - Incorporación de 7 pruebas exhaustivas de persistencia transaccional con sesiones HTTP desacopladas.
  - Corrección quirúrgica del test de asistencia adaptándolo al contrato estricto de `DailyAttendanceBatchRequest`.

### 4.2 Frontend
- **`frontend/src/pages/teacher/TeacherActivitiesView.tsx`**
  - Incorporación del modal de edición de actividades académicas (`editingActivity`).
  - Restricción del botón `✏️ Editar` exclusivamente a actividades con `act.status === 'DRAFT'`.
  - Conexión con `teacherApi.updateActivity(id, payload)`.
  - Recepción de props `initialGroupId` e `initialStatus` para filtros contextuales.
- **`frontend/src/pages/teacher/TeacherPlanningView.tsx`**
  - Modal de edición de planeación curricular (`editingPlan`).
  - Conexión con el endpoint `teacherApi.updatePlanning(id, payload)`.
  - Prop `initialGroupId` para preseleccionar y filtrar automáticamente el salón.
- **`frontend/src/pages/teacher/TeacherGroupsView.tsx`**
  - Matriz de navegación contextual por tarjeta de grupo hacia: Actividades, Calificaciones, Asistencia, Planeación y Observador/Convivencia.
- **`frontend/src/pages/teacher/TeacherAttendanceView.tsx`**
  - Soporte para la prop `initialGroupId`.
- **`frontend/src/pages/teacher/TeacherGradesView.tsx`**
  - Soporte para las props `initialGroupId` e `initialSelectedActivityId`.
- **`frontend/src/pages/teacher/TeacherDashboardView.tsx`**
  - Manejador `onTabChange` con parámetros contextuales.
  - KPI "Actividades Publicadas" navega con `{ status: 'PUBLISHED' }`.
  - KPI "Pendientes por Calificar" navega a `grades` de forma general.
- **`frontend/src/pages/teacher/TeacherPortal.tsx`**
  - Sincronización de parámetros en URL (`tab`, `groupId`, `activityId`, `status`).
- **`frontend/src/test/TeacherPortal.test.tsx`**
  - Pruebas unitarias completas de la interfaz (11/11 PASS).

---

## 5. RESUMEN DE VERIFICACIÓN AUTOMATIZADA

| Suite / Verificación | Entorno | Cantidad | Resultado | Duración / Observación |
| :--- | :--- | :---: | :---: | :--- |
| **Persistencia Sesiones Independientes** | Backend (Pytest) | 7 / 7 | **PASS** | 22.63s (Aislamiento HTTP real verificado) |
| **Regresión Portal Docente Base** | Backend (Pytest) | 12 / 12 | **PASS** | Cobertura total de endpoints docentes |
| **Regresión Convivencia (B1)** | Backend (Pytest) | 3 / 3 | **PASS** | Tipificación y ciclo de vida de incidentes |
| **Regresión Comunicaciones y Noticias (B2)** | Backend (Pytest) | 4 / 4 | **PASS** | Circulares, feeds y Anti-IDOR |
| **Unitarios Portal Docente (B3)** | Frontend (Vitest) | 11 / 11 | **PASS** | Modales, navegación contextual y estados |
| **Regresión Comunicaciones Docente (B2)** | Frontend (Vitest) | 7 / 7 | **PASS** | Lectura y acuse de recibo |
| **Regresión Planilla SIEE** | Frontend (Vitest) | 6 / 6 | **PASS** | Escala nacional de evaluación |
| **Chequeo de Tipos TypeScript (`typecheck`)** | Frontend (`tsc`) | N/A | **PASS** | 0 errores (`tsc --noEmit`) |
| **Compilación Producción (`build`)** | Frontend (`vite`) | N/A | **PASS** | Bundle y PWA generados exitosamente |
| **Migraciones de Base de Datos** | Alembic | N/A | **PASS** | En `HEAD` (021), 0 pendientes |

---

## 6. B3-H02 — VALIDACIÓN FUNCIONAL HUMANA (GUÍA PASO A PASO PARA EL SUPERVISOR)

> [!IMPORTANT]
> **Esta validación es estrictamente manual y debe ser efectuada por el supervisor desde el navegador web.**  
> No se ejecutarán scripts de browser automation.

### Credenciales y Acceso
* **URL:** `http://localhost:5173/portal-docente` (o login general en `http://localhost:5173/login`)
* **Usuario:** `carlos.docente` (o credencial docente asignada en el entorno QA)
* **Rol:** Docente Institucional

---

### Prueba A: Actividad DRAFT (Creación y Persistencia)
1. Iniciar sesión como docente y dirigirse a la pestaña **Actividades**.
2. Hacer clic en el botón **"+ Nueva Actividad Académica"**.
3. Diligenciar los campos requeridos:
   - **Título:** *"Taller de Refuerzo Mecánica Clásica"*
   - **Grupo:** Seleccionar un grupo asignado (ej. *10-A*).
   - **Asignatura:** Seleccionar la materia correspondiente (ej. *Física Clásica*).
   - **Tipo de Actividad:** *Taller* (o *Tarea*).
   - **Calificación Máxima:** `5.0`.
   - **Fecha Límite:** Seleccionar una fecha futura.
4. Hacer clic en el botón explícito: **"Guardar Actividad (Borrador)"**.
5. **Verificación Inmediata:** Confirmar que la actividad aparece en la tabla con la insignia naranja **Borrador (`DRAFT`)**.
6. **Verificación de Persistencia Física:**
   - Presionar `F5` (recargar completamente el navegador).
   - Volver a filtrar por estado **"Borrador"** si aplica.
   - Confirmar que la actividad continúa presente en la tabla con todos sus datos y en estado **Borrador**.

---

### Prueba B: Edición de Actividad DRAFT
1. En la tabla de Actividades, localizar la actividad en borrador creada en la Prueba A.
2. Confirmar que el botón **`✏️ Editar`** se encuentra visible y habilitado junto a `🚀 Publicar`.
3. Hacer clic en **`✏️ Editar`**.
4. En el modal "Editar Actividad Académica (Borrador)":
   - Modificar el título a: *"Taller de Refuerzo Mecánica Clásica — Versión Actualizada"*.
   - Agregar instrucciones pedagógicas: *"Resolver los ejercicios impares de la guía 3."*.
5. Hacer clic en **"Guardar Cambios (Borrador)"**.
6. **Verificación de Persistencia:**
   - Confirmar visualmente la actualización del título en la tabla.
   - Recargar la página (`F5`).
   - Reabrir el modal `✏️ Editar` o verificar el registro en la tabla: el nuevo título e instrucciones deben mantenerse exactamente iguales.
   - Confirmar que el estado de la actividad **permanece inmutablemente en DRAFT** (no se publicó automáticamente al editarse).

---

### Prueba C: Regla de Publicación y Bloqueo de Edición
1. En la actividad en borrador, hacer clic en el botón **`🚀 Publicar`**.
2. Confirmar la acción en el diálogo.
3. Observar que el estado cambia a verde **Publicada (`PUBLISHED`)**.
4. **Verificación:**
   - Confirmar que el botón **`✏️ Editar` desaparece** para esta actividad.
   - Confirmar que en su lugar se presenta únicamente el botón de calificación (`📊 Calificar`).
   - Esto valida que una actividad publicada no permite edición indebida de borrador.

---

### Prueba D: Edición y Persistencia de Planeación Curricular
1. Dirigirse a la pestaña **Planeación**.
2. Hacer clic en **"+ Nueva Unidad / Plan"** (o seleccionar una existente).
3. Registrar una unidad temática: *"Dinámica de Fluidos y Presión Hidrostática"*.
4. Guardar la planeación.
5. En la tarjeta o fila de la unidad, hacer clic en el botón **`✏️ Editar`**.
6. En el modal "Editar Unidad de Planeación Curricular":
   - Modificar las competencias o metodología: *"Laboratorio práctico de vasos comunicantes."*.
   - Cambiar el estado si se requiere (ej. *Aprobada*).
7. Hacer clic en **"Guardar Cambios"**.
8. **Verificación:**
   - Recargar la página (`F5`).
   - Confirmar que los cambios pedagógicos persisten físicamente en la vista y en la base de datos.

---

### Prueba E: Navegación Contextual y No-Regresión
1. **Desde "Mis Grupos":**
   - Dirigirse a la pestaña **Mis Grupos**.
   - En la tarjeta del *Grupo 10-A*, probar los botones de la barra contextual:
     - Clic en `📝 Actividades` → Debe abrir la pestaña de Actividades con el selector de grupo prefiltrado en *10-A*.
     - Clic en `📋 Asistencia` → Debe abrir la pestaña de Asistencia con el selector posicionado en *10-A*.
     - Clic en `🎯 Planeación` → Debe abrir la pestaña de Planeación filtrando las unidades de *10-A*.
     - Clic en `🛡️ Observador / Convivencia` → Debe navegar al Observador de Convivencia con el salón *10-A* preestablecido.
2. **Desde "Dashboard / Inicio":**
   - Dirigirse a la pestaña **Inicio**.
   - Clic en la tarjeta KPI **"Actividades Publicadas"** → Debe navegar a Actividades con filtro `Estado = Publicada`.
   - Clic en la tarjeta KPI **"Pendientes por Calificar"** → Debe navegar a la pestaña de Calificaciones de forma general.
3. **No-Regresión:**
   - Verificar que los módulos de **Convivencia (B1)** y **Comunicaciones / Noticias (B2)** cargan sin errores y presentan sus registros previos.

---

## 7. ESTADO DE CERTIFICACIÓN Y GATE FINAL

```text
============================================================
ESTADO FINAL DEL GATE B3 TRAS REMEDIACIÓN B3-H01:
============================================================
B3 TECHNICAL VERIFICATION = PASS
B3 HUMAN VALIDATION       = PENDING
B3 CERTIFICATION          = NOT CERTIFIED
============================================================
```

* **Cero cambios de código pendientes.**
* **Cero alteraciones a producción no autorizadas.**
* **Se detiene la ejecución a la espera de la autorización y ejecución humana del protocolo B3-H02 por parte del supervisor.**
