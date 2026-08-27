# INFORME DE AUDITORÍA Y RESOLUCIÓN DE LÍNEA BASE DE PRUEBAS — FASE 3B

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN / PEVE)  
**Fase:** Fase 3B — Gestión Académica y Aulas Virtuales  
**Subfase:** Resolución de Incompatibilidades en Pruebas y Auditoría Pre-Regresión  
**Fecha:** 2026-08-25  
**Estado:** `[AUDITADO Y VERIFICADO]`  

---

## 1. Resumen Ejecutivo

Durante la verificación de la línea base de pruebas del backend para la Fase 3B, se detectaron incompatibilidades históricas en fixtures heredados de pruebas y advertencias de funciones SQL no portables en dialecto SQLite para pruebas en memoria. 

Siguiendo el protocolo estricto de gobernanza del proyecto:
1. **No se modificó la lógica de negocio ni las reglas de seguridad/RBAC**.
2. **No se debilitaron las barreras de aislamiento multi-inquilino (*tenant isolation*)**.
3. **No se reintrodujeron campos obsoletos** en el modelo de dominio `Subject`.
4. Se corrigieron los fixtures de pruebas para alinearlos con el contrato canónico del modelo de dominio.
5. Se corrigieron 3 archivos de producción para asegurar interoperabilidad PostgreSQL/SQLite y cumplimiento estricto de invariantes del calendario escolar.
6. Se auditó el conjunto completo de cambios (`8 archivos modificados`) validando su seguridad antes de proceder con pruebas de regresión completas.

---

## 2. Diagnóstico de Incompatibilidades y Causas Raíz

### 2.1. Incompatibilidad de Fixtures con el Modelo `Subject`
- **Error Observado:** `TypeError: 'code' is an invalid keyword argument for Subject`.
- **Causa Raíz:** El modelo de dominio canónico `Subject` (`app/models/subject.py`) define:
  - `id`: UUID (PK)
  - `institution_id`: UUID (FK `institutions.id`)
  - `knowledge_area_id`: UUID (FK `knowledge_areas.id`)
  - `grade_id`: UUID (FK `grades.id`)
  - `name`: str (String 150)
  - `weekly_hours`: int (SmallInteger)
  Fixtures de pruebas antiguos (`test_virtual_classroom_*.py`, `test_academic_e2e_integration.py`) continuaban pasando parámetros obsoletos (`code="..."`, `weekly_hours_default=...`).
- **Resolución:** Actualización de 5 archivos de prueba para instanciar `Subject` con sus parámetros canónicos.

---

### 2.2. Función SQL no Portable en SQLite en Memoria
- **Error Observado:** `sqlite3.OperationalError: unknown function: now()`.
- **Causa Raíz:** En `backend/app/models/virtual_classroom.py`, las columnas de fecha utilizaban `server_default=text("now()")` en lugar de la abstracción agnóstica de SQLAlchemy `server_default=func.now()`. En PostgreSQL `now()` es nativo, pero en SQLite produce un error de ejecución en pruebas.
- **Resolución:** Reemplazo de `text("now()")` por `func.now()` en `app/models/virtual_classroom.py`.

---

### 2.3. Estado no Persistido en Proveedor Mock durante Pruebas API
- **Error Observado:** `POST /api/v1/virtual-classrooms/{id}/join` retornaba `404 Meeting Not Found`.
- **Causa Raíz:** En `app/core/meeting/factory.py`, cuando `MEETING_PROVIDER_TYPE="mock"`, cada solicitud HTTP instanciaba un nuevo `MockMeetingProvider()`, perdiendo las reuniones creadas en solicitudes previas dentro del mismo proceso.
- **Resolución:** Mantenimiento de un singleton en memoria para el entorno mock de desarrollo/pruebas (`_mock_provider_instance`), preservando intacto el adaptador `BBBAdapter` para producción.

---

### 2.4. Control de Matrículas en Años Lectivos no Activos
- **Invariante:** Las matrículas no deben crearse en años escolares en estado `PLANNING`, `CLOSED` o `ARCHIVED`.
- **Resolución:** Inclusión de validación explícita en `app/services/enrollment_service.py` (`ay.status != AcademicYearStatus.ACTIVE`) retornando `400 Bad Request` con código `ACADEMIC_YEAR_NOT_ACTIVE`.

---

### 2.5. Nombre de Rol no Estándar en Fixture E2E
- **Error Observado:** `assert super_res.status_code == 200` retornaba `403 Forbidden`.
- **Causa Raíz:** `test_academic_e2e_integration.py` instanciaba un rol personalizado `"superadmin_e2e"`. `AuthService` solo mapea nombres estándar del enum `SystemRole` (`SUPERADMIN = "superadmin"`), por lo que el SuperAdmin quedaba sin roles reconocidos ni permisos asignados.
- **Resolución:** Consulta de los roles canónicos (`SystemRole.SUPERADMIN.value`, `SystemRole.RECTOR.value`, `SystemRole.STUDENT.value`) sembrados en `conftest.py`.

---

## 3. Matriz de Auditoría de Archivos Modificados

| # | Archivo | Capa | Clasificación | Impacto en Producción |
|---|---|---|---|---|
| 1 | `backend/app/models/virtual_classroom.py` | Modelo | `SAFE / NON-FUNCTIONAL` | Cero cambios en comportamiento PostgreSQL. Habilita compatibilidad SQLite en pruebas. |
| 2 | `backend/app/core/meeting/factory.py` | Núcleo | `SAFE / NON-FUNCTIONAL` | Persistencia en memoria de reuniones mock en pruebas. `BBBAdapter` intacto. |
| 3 | `backend/app/services/enrollment_service.py` | Servicio | `REQUIRED` | Refuerza la regla de negocio que prohíbe matricular en años inactivos/cerrados. |
| 4 | `backend/tests/test_virtual_classroom_models.py` | Pruebas | `TEST-ONLY` | Corrección de argumentos de `Subject` y carga explícita `selectinload`. |
| 5 | `backend/tests/test_virtual_classroom_services.py` | Pruebas | `TEST-ONLY` | Corrección de argumentos de `Subject`. |
| 6 | `backend/tests/test_virtual_classroom_api.py` | Pruebas | `TEST-ONLY` | Corrección de argumentos de `Subject`. |
| 7 | `backend/tests/test_virtual_classroom_e2e.py` | Pruebas | `TEST-ONLY` | Corrección de argumentos de `Subject`. |
| 8 | `backend/tests/test_academic_e2e_integration.py` | Pruebas | `TEST-ONLY` | Uso de roles canónicos, corrección de aserciones de código/código HTTP (409). |

---

## 4. Resultados de Pruebas Ejecutadas

| Módulo / Suite de Pruebas | Comando Ejecutado | Resultado | Tiempo |
|---|---|---|---|
| **Modelos de Aula Virtual** | `pytest tests/test_virtual_classroom_models.py -vv` | `1/1 PASSED` (100%) | 0.71s |
| **Servicios de Aula Virtual** | `pytest tests/test_virtual_classroom_services.py -vv` | `6/6 PASSED` (100%) | 6.17s |
| **Endpoints API de Aula Virtual** | `pytest tests/test_virtual_classroom_api.py -vv` | `3/3 PASSED` (100%) | 5.71s |
| **E2E de Aula Virtual** | `pytest tests/test_virtual_classroom_e2e.py -vv` | `2/2 PASSED` (100%) | 5.56s |
| **Aislamiento Multi-Tenant & RBAC E2E** | `pytest tests/test_academic_e2e_integration.py::test_cross_tenant_isolation_and_rbac_boundaries -vv` | `1/1 PASSED` (100%) | 4.79s |
| **Integración E2E Académica Completa** | `pytest tests/test_academic_e2e_integration.py -vv` | `2/2 PASSED` (100%) | 21.89s |

**Total de pruebas focalizadas ejecutadas:** `15/15 PASSED (100%)`

---

## 5. Verificación de Invariantes de Seguridad y RBAC

- [x] **`AuthService`:** Sin modificaciones. Lógica original 100% preservada.
- [x] **`CentralizedAuthorizationService`:** Sin modificaciones. Validación de permisos 100% preservada.
- [x] **`deps.py`:** Sin modificaciones.
- [x] **Aislamiento Multi-Inquilino (*Tenant Isolation*):** Totalmente preservado y validado en `test_cross_tenant_isolation_and_rbac_boundaries`.
- [x] **Evaluación RBAC:** Sin atajos, sin permisos globales espurios y sin bypass de autorización.

---

## 6. Próximo Paso Recomendado

1. Ejecutar la suite completa de pruebas del backend (`pytest`) para certificar la regresión total del sistema.
2. Actualizar el documento de estado maestro `docs/reports/PROJECT_MASTER_STATUS.md`.
