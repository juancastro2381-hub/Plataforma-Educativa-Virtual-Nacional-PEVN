# PLAN DE REMEDIACIÓN CONTROLADA — INCIDENCIA B3-H01
## PERSISTENCIA TRANSACCIONAL EN ENDPOINTS MUTANTES DEL PORTAL DOCENTE
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** Septiembre 2026  
**Documento:** `docs/reports/B3_H01_REMEDIATION_PLAN.md`  
**Estado:** `B3-H01 REMEDIATION PLAN = READY` *(Esperando Autorización Humana)*

---

## 1. RESUMEN DE LA CAUSA RAÍZ

El diagnóstico read-only `B3_H01_DRAFT_CREATION_DIAGNOSTIC.md` demostró de manera concluyente:
1. Al crear una actividad académica (`POST /api/v1/teacher/activities`), `TeacherPortalService.create_activity()` agrega la entidad a la sesión y ejecuta `await self._session.flush()`, registrando el evento de auditoría en la misma sesión.
2. El endpoint retorna `AcademicActivityResponse` con código `HTTP 201 Created`.
3. Sin embargo, ni el endpoint ni el servicio ejecutan `await db.commit()`.
4. Conforme a la especificación de `backend/app/db/session.py` (*"Transactions must be explicitly committed by the caller"*), al finalizar la petición HTTP, FastAPI sale del generador `get_async_session` y ejecuta `finally: await session.close()`.
5. El cierre de la sesión de SQLAlchemy sin commit previo provoca un **ROLLBACK automático** en PostgreSQL/asyncpg.
6. La actividad y su log de auditoría se descartan de la base de datos.
7. La siguiente petición HTTP (`GET /api/v1/teacher/activities`) se atiende en una nueva sesión de base de datos donde la actividad no existe (`Total academic_activities in DB: 0`).
8. Los tests automatizados previos no detectaron la falla porque la fixture `client` de pytest reutilizaba una única sesión (`db_session`) para múltiples peticiones consecutivas, permitiendo leer datos en estado *flushed* en memoria.

---

## 2. INVENTARIO DE ENDPOINTS MUTANTES AFECTADOS

El análisis exhaustivo de `backend/app/api/v1/endpoints/teacher_portal.py` reveló que la omisión de `await db.commit()` es sistemática en las 9 operaciones mutantes del módulo docente previas a la Fase 15 (sección 8):

| # | Endpoint | Método HTTP | Operación | Riesgo de Transacción / Atomicidad |
| :-: | :--- | :---: | :--- | :--- |
| **1** | `/activities` | `POST` | `create_teacher_activity` | Crea actividad + log de auditoría. Rollback actual descarta ambos. |
| **2** | `/activities/{activity_id}` | `PATCH` | `update_teacher_activity` | Actualiza campos + log de auditoría. Rollback actual revierte cambios. |
| **3** | `/activities/{activity_id}/publish` | `POST` | `publish_teacher_activity` | **Crítica:** Cambia estado a `PUBLISHED` y genera casillas iniciales (`ActivityGrade`) para todos los estudiantes activos del grupo. |
| **4** | `/activities/{activity_id}/close` | `POST` | `close_teacher_activity` | Cambia estado a `CLOSED` + log de auditoría. |
| **5** | `/activities/{activity_id}/grades` | `PUT` | `batch_update_activity_grades` | **Crítica:** Calificación por lote de múltiples estudiantes. Debe ser atómica (o se guardan todas las notas o ninguna). |
| **6** | `/groups/{group_id}/attendance` | `POST` | `record_daily_attendance` | **Crítica:** Registro de asistencia diaria de todo un grupo. Debe ser atómica. |
| **7** | `/planning` | `POST` | `create_teacher_plan` | Crea unidad didáctica curricular + log de auditoría. |
| **8** | `/planning/{plan_id}` | `PATCH` | `update_teacher_plan` | Actualiza planeación curricular + log de auditoría. |
| **9** | `/planning/{plan_id}` | `DELETE` | `delete_teacher_plan` | Elimina planeación curricular + log de auditoría. |

*(Nota: Los endpoints de Comunicaciones Institucionales de la sección 8, añadidos en Fase 15/B2, líneas 804 y 838, ya cuentan con `await db.commit()`, confirmando la regla del proyecto).*

---

## 3. EVALUACIÓN DE PATRONES ARQUITECTÓNICOS EN PEVN

Se evaluaron tres alternativas para la ubicación del `commit`:

### Alternativa A: Commit dentro de cada método de `TeacherPortalService`
- **Ventajas:** Centraliza la persistencia en la clase del servicio.
- **Desventajas:**
  - Viola el principio de diseño de los servicios en PEVN: los servicios reciben `session: AsyncSession` para permitir orquestación compuesta y reutilización en transacciones más amplias.
  - Impide que una capa superior orqueste múltiples servicios dentro de una misma transacción sin incurrir en commits prematuros.
  - Desalineado con los demás servicios del proyecto (`CoexistenceIncidentService`, `VirtualClassroomService`, `StudentService`, etc.), los cuales solo ejecutan `flush()` y delegan el `commit()` al endpoint controlador.

### Alternativa B: Unit of Work Middleware / Commit Automático en `get_async_session`
- **Ventajas:** Hace commit automático al salir del generador si no hubo excepciones.
- **Desventajas:**
  - Modificación de alto riesgo en `backend/app/db/session.py`.
  - Impacto colateral masivo en todo el backend (Auth, SIEE, Admin, Student, Guardian).
  - Podría causar commits accidentales en endpoints de solo lectura que accidentalmente modifiquen atributos en sesión.
  - Viola la política de no modificar componentes transversales estables.

### Alternativa C (Recomendada): Commit Explícito en el Endpoint Controlador
- **Patrón canónico verificado en PEVN:**
  Utilizado en más de 45 endpoints mutantes a lo largo de:
  - `backend/app/api/v1/endpoints/virtual_classrooms.py` (líneas 101, 194, 231, 281, 352)
  - `backend/app/api/v1/endpoints/incidents.py` (líneas 91, 154, 191, 227)
  - `backend/app/api/v1/endpoints/teachers.py` (líneas 133, 278, 321, 361)
  - `backend/app/api/v1/endpoints/students.py` (líneas 97, 198, 240, 279, 354, 390)
  - `backend/app/api/v1/endpoints/news.py` (líneas 83, 141, 174)
  - `backend/app/api/v1/endpoints/institutions.py` (líneas 132, 205, 260, 299, 338...)
  - `backend/app/api/v1/endpoints/teacher_portal.py` (sección B2, líneas 804 y 838)
- **Mecanismo:**
  ```python
  # 1. El endpoint recibe db: SessionDep
  # 2. Invoca al servicio que realiza validaciones, cálculos, flushes y agrega eventos de auditoría:
  result = await service.operacion(...)
  # 3. El endpoint confirma la transacción completa de forma atómica:
  await db.commit()
  # 4. Retorna el esquema de respuesta validado:
  return ResponseSchema.model_validate(result)
  ```
- **Justificación:** Es el estándar ya adoptado por el 100% de los módulos funcionales certificados de PEVN. Mantiene el principio de que el controlador HTTP delimita la frontera de la transacción HTTP.

---

## 4. ANÁLISIS DE ATOMICIDAD Y EFECTOS SECUNDARIOS

Se revisaron minuciosamente los tres casos de operaciones múltiples:

1. **`publish_teacher_activity`:**
   - La operación involucra:
     a) Cambiar el estado de la actividad a `PUBLISHED`.
     b) Asignar `publication_date`.
     c) Consultar la lista de estudiantes inscritos activos.
     d) Insertar masivamente las casillas iniciales de calificación (`ActivityGrade`).
     e) Registrar el evento de auditoría en la sesión.
   - **Comportamiento con Alternativa C:** Todo se ejecuta en el mismo `AsyncSession` bajo una única transacción de base de datos. Si la consulta de estudiantes o la creación de notas fallase, la excepción cancela la petición y `get_async_session` ejecuta `rollback()`. Ningún cambio parcial se persiste. Al ejecutar `await db.commit()` al final del endpoint, la publicación y las calificaciones se comprometen de forma atómica e indivisible.

2. **`batch_update_activity_grades`:**
   - Itera sobre un lote de estudiantes y calificaciones.
   - Si una sola nota viola los límites (`0.0 <= score <= max_score`), el servicio levanta una excepción `ValidationError`.
   - Como el commit solo se llama tras concluir con éxito la totalidad del lote, no hay riesgo de calificaciones parciales.

3. **`record_daily_attendance`:**
   - Itera sobre la lista de asistencia del grupo.
   - Al igual que en notas, o se guardan todos los registros del día o la transacción se revierte completa.

**Conclusión:** No existen riesgos de commits parciales ni desincronización de auditoría. La atomicidad se preserva al 100%.

---

## 5. ESTRATEGIA DE PRUEBAS DE PERSISTENCIA REAL ENTRE SESIONES

Para erradicar el falso positivo provocado por la sesión única compartida en los tests de Pytest, se diseñó la siguiente estrategia de verificación:

### 5.1 Mecanismo de Prueba de Persistencia Real
Para comprobar que una mutación realmente se persistió en la base de datos y no solo en el buffer de una sesión en memoria:

```python
# Paso 1: Petición HTTP mutante
res = await client.post("/api/v1/teacher/activities", headers=headers, json=payload)
assert res.status_code == 201
created_id = res.json()["id"]

# Paso 2: Romper el caché de sesión en memoria
# Al invocar db_session.rollback() en el runner de pruebas:
# Si el endpoint ejecutó commit(), los datos ya están en la base de datos y el rollback no los afecta.
# Si el endpoint omitió el commit(), el rollback descarta el flush y los datos se pierden.
await db_session.rollback()

# Paso 3: Petición HTTP de consulta en sesión fresca
list_res = await client.get("/api/v1/teacher/activities", headers=headers)
assert list_res.status_code == 200
items = list_res.json()["items"]
assert any(act["id"] == created_id for act in items), "FALLA: La actividad no persistió tras el cierre transaccional"
```

Esta técnica emula exactamente el comportamiento de producción, garantizando que ninguna prueba valide como positiva una mutación no consolidada en almacenamiento persistente.

---

## 6. ALCANCE DE ARCHIVOS A MODIFICAR (PLAN DE ACCIÓN)

La remediación requiere intervenir exclusivamente dos archivos:

### 6.1 Backend Controller
- **`backend/app/api/v1/endpoints/teacher_portal.py`**
  - Añadir `await db.commit()` en los 9 endpoints mutantes:
    1. `create_teacher_activity` (tras `service.create_activity`)
    2. `update_teacher_activity` (tras `service.update_activity`)
    3. `publish_teacher_activity` (tras `service.publish_activity`)
    4. `close_teacher_activity` (tras `service.close_activity`)
    5. `batch_update_activity_grades` (tras `service.batch_grade_activity`)
    6. `record_daily_attendance` (tras `service.record_daily_attendance`)
    7. `create_teacher_plan` (tras `service.create_academic_plan`)
    8. `update_teacher_plan` (tras `service.update_academic_plan`)
    9. `delete_teacher_plan` (tras `service.delete_academic_plan`)

### 6.2 Pruebas Backend
- **`backend/tests/test_teacher_portal_api.py`**
  - Actualizar `test_teacher_activity_draft_update_and_persistence` para incluir la verificación transaccional con `await db_session.rollback()`.
  - Actualizar `test_teacher_planning_update_and_persistence` para incluir la misma validación.
  - Agregar un test de regresión específico de persistencia entre sesiones para `publish_teacher_activity` y `batch_update_activity_grades`.

---

## 7. MATRIZ DE RIESGOS Y NO REGRESIÓN

| Factor de Riesgo | Nivel | Mitigación |
| :--- | :---: | :--- |
| **Regresión en Módulos Certificados** | CERO | No se toca ningún archivo fuera de `teacher_portal.py` y sus tests. SIEE, Convivencia (B1), Comunicaciones (B2), Estudiantes y Acudientes permanecen intactos. |
| **Cambios en Esquemas / Modelos** | CERO | Cero cambios en modelos SQLAlchemy, cero migraciones Alembic. |
| **Modificación de RBAC** | CERO | Los permisos exigidos por los endpoints se mantienen exactamente iguales. |
| **Rendimiento de Base de Datos** | MÍNIMO | El commit al final de la petición HTTP es el comportamiento normal y esperado de cualquier API REST en PostgreSQL. |

---

## 8. ORDEN DE IMPLEMENTACIÓN PROPUESTO (POST-AUTORIZACIÓN)

1. **Paso 1:** Aplicar la adición quirúrgica de `await db.commit()` en los 9 endpoints de `backend/app/api/v1/endpoints/teacher_portal.py`.
2. **Paso 2:** Actualizar los tests de integración en `backend/tests/test_teacher_portal_api.py` con las aserciones de persistencia post-rollback.
3. **Paso 3:** Ejecutar la suite completa de pruebas backend (Teacher Portal + Regresión B1 + Regresión B2) para verificar 100% PASS.
4. **Paso 4:** Ejecutar la prueba directa de simulación de sesiones independientes (`verify_real_session_isolation.py`) para confirmar que el DRAFT persiste y es visible en la segunda sesión.
5. **Paso 5:** Informar al supervisor para la reanudación de la validación funcional humana (Prueba B3-H01).

---

## 9. CONCLUSIÓN Y GATE

El plan de remediación resuelve de manera directa, robusta y mínima la causa raíz sin tocar componentes certificados, alineando el Portal Docente con la arquitectura transaccional estándar de PEVN.

```text
============================================================
RESULTADO DEL PLAN DE REMEDIACIÓN:
B3-H01 REMEDIATION PLAN = READY
============================================================
```

*Se detiene la ejecución. No se han modificado archivos de código ni de base de datos. Se espera la autorización humana para proceder a la ejecución de este plan.*
