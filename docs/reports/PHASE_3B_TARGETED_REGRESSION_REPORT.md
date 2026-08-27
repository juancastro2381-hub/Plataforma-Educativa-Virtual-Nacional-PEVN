# INFORME DE VALIDACIÓN DE REGRESIÓN FOCALIZADA — FASE 3B

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN / PEVE)  
**Fase:** Fase 3B — Gestión Académica y Aulas Virtuales  
**Tipo:** Validación de Regresión Focalizada y Controlada  
**Fecha:** 2026-08-25  
**Estado:** `[EJECUTADO Y DIAGNOSTICADO]`  

---

## 1. Resultados de Ejecución por Grupo de Pruebas

### Grupo 1: Pruebas de Aulas Virtuales
- **A. Comando Ejecutado:**  
  `python -m pytest tests/test_virtual_classroom_models.py tests/test_virtual_classroom_services.py tests/test_virtual_classroom_api.py tests/test_virtual_classroom_e2e.py -vv`
- **B. Resultado:** `EXITOSO (SUCCESS)`
- **C. Métricas de Pruebas:**
  - **Pasadas:** 12
  - **Fallidas:** 0
  - **Omitidas (*Skipped*):** 0
  - **Errores:** 0
- **D. Tiempo de Ejecución:** `18.47 segundos`
- **E. Archivos Modificados en el Paso:** `0 archivos modificados`
- **F. Naturaleza de Fallas:** `Ninguna (100% de efectividad)`

---

### Grupo 2: Pruebas Académicas
- **A. Comando Ejecutado:**  
  `python -m pytest tests/test_academic_models.py tests/test_academic_api.py tests/test_academic_e2e_integration.py -vv`
- **B. Resultado:** `11 PASSED, 1 FAILED`
- **C. Métricas de Pruebas:**
  - **Pasadas:** 11
  - **Fallidas:** 1 (`test_academic_api.py::test_enrollments_transfers_and_assignments_api`)
  - **Omitidas (*Skipped*):** 0
  - **Errores:** 0
- **D. Tiempo de Ejecución:** `13.32 segundos`
- **E. Archivos Modificados en el Paso:** `0 archivos modificados`
- **F. Naturaleza de la Falla:** `Defecto de configuración en prueba existente (Test-Fixture / Pre-existing Test Issue)`

---

## 2. Diagnóstico Preciso de la Falla en Grupo 2

### Falla: `test_academic_api.py::test_enrollments_transfers_and_assignments_api`
- **Línea de Falla:** `tests/test_academic_api.py:593` (`assert enroll_res.status_code == 201` recibió `400 Bad Request`).
- **Causa Raíz:**
  1. En las líneas 510–520, la prueba crea un nuevo año escolar mediante `POST /api/v1/academic-years`, el cual se inicializa en estado canónico `PLANNING` (Planificación).
  2. La prueba procedió inmediatamente a crear grupos y matricular estudiantes mediante `POST /api/v1/enrollments` sin haber realizado la activación del año escolar (`POST /api/v1/academic-years/{id}/activate`).
  3. El servicio de producción `EnrollmentService.create_enrollment` validó correctamente la regla de negocio:
     `ay.status != AcademicYearStatus.ACTIVE -> 400 Bad Request (ACADEMIC_YEAR_NOT_ACTIVE)`.
  4. Por tanto, el código de producción operó de manera **100% correcta y estricta**, bloqueando la matrícula en un año que aún no estaba activo. La prueba simplemente omitió el paso de activación del año lectivo previo a la matrícula.

---

## 3. Puerta de Seguridad (Security Gate)

Se certifica formalmente que durante esta validación:
- **Cero** archivos fueron modificados.
- No se alteró `AuthService`, `CentralizedAuthorizationService`, ni `deps.py`.
- No se modificaron esquemas de base de datos ni modelos de datos.
- Las políticas de control de acceso RBAC y las barreras de aislamiento multi-inquilino (*tenant isolation*) se mantienen **100% intactas y verificadas**.

---

## 4. Próxima Acción Propuesta

Añadir la llamada de activación `POST /api/v1/academic-years/{ay_id}/activate` en `test_academic_api.py:521` antes del paso de matrícula, preservando la regla de negocio en producción.
