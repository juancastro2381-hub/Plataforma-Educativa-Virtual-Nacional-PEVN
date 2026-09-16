# INFORME DE DIAGNÓSTICO READ-ONLY — INCIDENCIA B3-H01
## NO PERSISTENCIA DE ACTIVIDAD DRAFT EN EL PORTAL DOCENTE
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha/Hora:** 2026-09-09 20:10:00 UTC-5  
**Tipo de Análisis:** Investigación Read-Only Forense y Técnica  
**Estado:** `B3-H01 DIAGNÓSTICO = CAUSA IDENTIFICADA`

---

## 1. CONTEXTO Y SÍNTOMA REPORTADO

Durante la validación funcional humana de la Fase B3 (Prueba B3-H01):
1. El usuario docente ingresó al Portal Docente → Actividades Académicas.
2. Seleccionó el filtro `Estado = Borrador`.
3. El listado mostró: *"No se encontraron actividades con los filtros seleccionados"*.
4. El usuario abrió el formulario *"Nueva Actividad Académica"*, diligenció los campos y pulsó *"Guardar Actividad (Borrador)"*.
5. El formulario cerró y el usuario volvió al listado con `Estado = Borrador`.
6. Nuevamente apareció: *"No se encontraron actividades con los filtros seleccionados"*.

---

## 2. INVESTIGACIÓN DEL FLUJO FRONTEND

### 2.1 Componente e Interfaz
- **Archivo:** `frontend/src/pages/teacher/TeacherActivitiesView.tsx`
- **Manejador:** `handleCreateSubmit` (líneas 163–206)
- **Botón:**
  ```tsx
  <Button variant="primary" type="submit" disabled={isSubmitting}>
    {isSubmitting ? 'Guardando...' : '💾 Guardar Actividad (Borrador)'}
  </Button>
  ```

### 2.2 Payload Enviado
El frontend empaqueta los datos validados del formulario en la estructura `AcademicActivityCreateRequest`:
```typescript
const payload: AcademicActivityCreateRequest = {
  subject_id: assignment.subject_id,
  group_id: assignment.group_id,
  academic_year_id: assignment.academic_year_id,
  title: title.trim(),
  description: description.trim() || null,
  activity_type: activityType,
  due_date: dueDate ? new Date(dueDate).toISOString() : null,
  max_score: maxScore,
  instructions: instructions.trim() || null,
  resource_url: resourceUrl.trim() || null,
}
```

### 2.3 Llamada a la API y Manejo de Respuesta
1. Ejecuta: `await teacherApi.createActivity(payload)`.
2. Método y Endpoint: `POST /api/v1/teacher/activities`.
3. Código HTTP retornado por el servidor: `HTTP 201 Created`.
4. El frontend ejecuta:
   ```typescript
   setFormSuccess('¡Actividad académica creada exitosamente en modo BORRADOR!')
   await onRefresh()
   setTimeout(() => { setShowCreateModal(false) }, 1200)
   ```
5. En `TeacherPortal.tsx`, `onRefresh` ejecuta `loadAllTeacherData()`, el cual lanza:
   `teacherApi.listActivities()` (`GET /api/v1/teacher/activities`).
6. El listado en frontend recibe la respuesta y aplica el filtro en memoria:
   ```typescript
   const filteredActivities = activities.filter((act) => {
     if (filterGroup && act.group_id !== filterGroup) return false
     if (filterStatus && act.status !== filterStatus) return false
     return true
   })
   ```
7. Al estar `filterStatus === 'DRAFT'`, evalúa `act.status !== 'DRAFT'`.

---

## 3. INVESTIGACIÓN DEL BACKEND Y CONTRATOS

### 3.1 Endpoint de Creación
- **Archivo:** `backend/app/api/v1/endpoints/teacher_portal.py` (Líneas 217–264)
- **Definición:**
  ```python
  @router.post(
      "/activities",
      response_model=AcademicActivityResponse,
      status_code=status.HTTP_201_CREATED,
      summary="Crear nueva actividad académica",
      description="Crea una actividad asociada a una asignación académica activa del docente.",
      dependencies=[Depends(require_permission("activities", "create"))],
  )
  async def create_teacher_activity(
      data: AcademicActivityCreateRequest,
      current_user: CurrentUserDep,
      db: SessionDep,
      request: Request,
  ) -> AcademicActivityResponse:
      service = TeacherPortalService(session=db)
      teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
      activity = await service.create_activity(
          teacher,
          data,
          actor_id=str(current_user.id),
          actor_ip=request.client.host if request.client else "0.0.0.0",
      )
      return AcademicActivityResponse(...)
  ```

### 3.2 Lógica en el Servicio
- **Archivo:** `backend/app/services/teacher_portal_service.py` (Líneas 500–554)
- **Código:**
  ```python
  activity = AcademicActivity(
      institution_id=teacher.institution_id,
      teacher_id=teacher.id,
      academic_assignment_id=assignment.id,
      subject_id=data.subject_id,
      group_id=data.group_id,
      academic_year_id=data.academic_year_id,
      title=data.title.strip(),
      description=data.description.strip() if data.description else None,
      activity_type=data.activity_type,
      status=ActivityStatus.DRAFT,
      due_date=data.due_date,
      max_score=data.max_score,
      instructions=data.instructions.strip() if data.instructions else None,
      resource_url=data.resource_url.strip() if data.resource_url else None,
  )
  self._session.add(activity)
  await self._session.flush()

  await self._audit.record(...)
  return await self.get_activity(teacher, activity.id)
  ```

---

## 4. EVIDENCIA FORENSE Y CAUSA RAÍZ

### 4.1 La Dependencia de Sesión de Base de Datos
En `backend/app/db/session.py` (líneas 129–151), la dependencia `get_async_session` define formalmente:
```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    The session is automatically closed after the request completes.
    Transactions must be explicitly committed by the caller.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```
El contrato arquitectónico del backend estipula expresamente:
> **"Transactions must be explicitly committed by the caller."**

### 4.2 La Omisión del Commit
Al revisar todos los endpoints mutantes en `backend/app/api/v1/endpoints/teacher_portal.py` y `TeacherPortalService`:
- `create_teacher_activity`: **NO** ejecuta `await db.commit()`.
- `TeacherPortalService.create_activity`: Ejecuta `await self._session.flush()`, pero **NO** ejecuta `commit()`.
- Al finalizar la función del endpoint, FastAPI envía la respuesta HTTP al cliente (`201 Created`).
- Inmediatamente después, FastAPI sale del generador `get_async_session`, ejecutando el bloque `finally: await session.close()`.
- En SQLAlchemy con `asyncpg` sobre PostgreSQL, cerrar una sesión con transacciones en curso sin un `commit` explícito provoca un **ROLLBACK AUTOMÁTICO** por parte del motor de base de datos.

### 4.3 Verificación en Base de Datos Real (PostgreSQL)
Se consultó la base de datos de desarrollo mediante script read-only:
```text
Total academic_activities in DB: 0
```
La tabla `academic_activities` se encuentra completamente vacía.
Asimismo, en la tabla `audit_logs` no existe ningún registro `ACTIVITY_CREATED`, confirmando que tanto la entidad como su evento de auditoría fueron descartados por el rollback de la transacción.

### 4.4 Demostración de Aislamiento de Sesiones
Se ejecutó una prueba de simulación de sesiones independientes (`verify_real_session_isolation.py`):
1. Sesión 1 ejecuta `create_activity` (hace `flush`) y cierra sin `commit`.
2. Sesión 2 (nueva petición HTTP) consulta la actividad por su ID.
**Resultado:**
```text
RESULT: Activity WAS NOT FOUND in session 2! (ROLLED BACK due to missing commit)
```

### 4.5 ¿Por qué pasaron los tests automatizados de Pytest?
En `backend/tests/conftest.py` (líneas 122–126):
```python
async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    yield db_session

test_app.dependency_overrides[get_async_session] = _override_get_async_session
```
En el entorno de pruebas de pytest:
- La fixture `db_session` es una **única instancia de sesión compartida** durante toda la ejecución de la función de test.
- No se cierra ni se abre una nueva sesión entre peticiones de `client`.
- Al ejecutar `client.post` y luego `client.get`, ambas peticiones operan sobre la misma sesión en memoria. Los objetos en estado `flushed` son visibles dentro de la misma transacción para consultas subsiguientes.
- Por esta razón, `test_teacher_portal_api.py` reportaba `PASS`, a pesar de que en runtime real (donde cada petición HTTP es una sesión independiente) la transacción se revertía.

---

## 5. EVALUACIÓN DE HIPÓTESIS

| Hipótesis | Estado | Evidencia |
| :--- | :---: | :--- |
| **A. El DRAFT nunca fue creado** | **CONFIRMADA (en persistencia)** | Se instanció en memoria y devolvió 201, pero fue revertido (rollback) al cerrar la sesión HTTP; nunca se insertó en PostgreSQL. |
| **B. El DRAFT fue creado pero el listado no lo recupera** | **DESCARTADA** | El listado consulta correctamente; el registro no existe en la base de datos. |
| **C. El DRAFT fue creado con un estado incorrecto** | **DESCARTADA** | El modelo asigna explícitamente `ActivityStatus.DRAFT`. |
| **D. El filtro DRAFT está incorrectamente implementado** | **DESCARTADA** | Frontend y backend utilizan unívocamente la cadena `"DRAFT"`. |
| **E. El frontend no procesa correctamente la respuesta** | **DESCARTADA** | El frontend procesó correctamente el 201, mostró éxito y consultó el listado. |
| **F. Omisión de `await db.commit()` en backend** | **CONFIRMADA Y DEMOSTRADA** | El endpoint `create_teacher_activity` no ejecuta commit, provocando rollback al salir de `get_async_session`. |

---

## 6. IMPACTO ARQUITECTÓNICO ADICIONAL IDENTIFICADO

La omisión de `await db.commit()` no se limita a `create_teacher_activity`. Afecta de forma idéntica a los siguientes endpoints mutantes del módulo `teacher_portal.py`:
1. `create_teacher_activity` (`POST /activities`)
2. `update_teacher_activity` (`PATCH /activities/{activity_id}`)
3. `publish_teacher_activity` (`POST /activities/{activity_id}/publish`)
4. `close_teacher_activity` (`POST /activities/{activity_id}/close`)
5. `batch_update_activity_grades` (`PUT /activities/{activity_id}/grades`)
6. `record_daily_attendance` (`POST /groups/{group_id}/attendance`)
7. `create_teacher_plan` (`POST /planning`)
8. `update_teacher_plan` (`PATCH /planning/{plan_id}`)
9. `delete_teacher_plan` (`DELETE /planning/{plan_id}`)

*(En contraste, los endpoints de Comunicaciones Institucionales agregados en B2 —líneas 804 y 838— sí incluyen explícitamente `await db.commit()`, motivo por el cual la validación humana de B2 sí persistió lecturas y acuses).*

---

## 7. ARCHIVOS Y TESTS REVISADOS

- `frontend/src/pages/teacher/TeacherActivitiesView.tsx`
- `frontend/src/pages/teacher/TeacherPortal.tsx`
- `backend/app/api/v1/endpoints/teacher_portal.py`
- `backend/app/services/teacher_portal_service.py`
- `backend/app/db/session.py`
- `backend/app/audit/service.py`
- `backend/tests/conftest.py`
- `backend/tests/test_teacher_portal_api.py`
- Script de diagnóstico: `scratch/check_activities_db.py`
- Script de diagnóstico: `scratch/check_audit_logs.py`
- Script de diagnóstico: `scratch/verify_real_session_isolation.py`

---

## 8. CONCLUSIÓN Y GATE

La causa raíz ha sido identificada y probada de forma técnica, forense e incontrovertible mediante análisis read-only sin alterar código ni base de datos.

```text
============================================================
RESULTADO DEL DIAGNÓSTICO:
B3-H01 DIAGNÓSTICO = CAUSA IDENTIFICADA
============================================================
```

*Se detiene la ejecución inmediatamente en estricto cumplimiento de las reglas. NO se ha modificado código. Se espera la autorización humana para los siguientes pasos.*
