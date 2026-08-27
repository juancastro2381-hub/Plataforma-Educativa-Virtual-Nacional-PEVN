# INFORME DE REGRESIÓN COMPLETA DEL BACKEND — FASE 3B

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN / PEVE)  
**Fase:** Fase 3B — Gestión Académica y Aulas Virtuales  
**Tipo:** Validación Secuencial de Regresión del Backend (109 Pruebas)  
**Fecha:** 2026-08-25  
**Estado:** `[108/109 PASSED (99.1%) — 1 FIXTURE PREEXISTENTE IDENTIFICADO]`  

---

## 1. Resultados de Ejecución por Etapa

### Etapa 1: Suite Focalizada de Aulas Virtuales
- **Comando:**  
  `python -m pytest tests/test_virtual_classroom_models.py tests/test_virtual_classroom_services.py tests/test_virtual_classroom_api.py tests/test_virtual_classroom_e2e.py -vv`
- **Pruebas Colectadas:** 12
- **Resultado:** `12 PASSED / 0 FAILED / 0 SKIPPED / 0 ERRORS`
- **Efectividad:** **100% PASS**
- **Tiempo de Ejecución:** `13.55 segundos`
- **Fallas:** Ninguna.

---

### Etapa 2: Suite Focalizada Académica
- **Comando:**  
  `python -m pytest tests/test_academic_models.py tests/test_academic_api.py tests/test_academic_e2e_integration.py -vv`
- **Pruebas Colectadas:** 12
- **Resultado:** `12 PASSED / 0 FAILED / 0 SKIPPED / 0 ERRORS`
- **Efectividad:** **100% PASS**
- **Tiempo de Ejecución:** `16.00 segundos`
- **Fallas:** Ninguna.

---

### Etapa 3: Suite Completa del Backend (109 Pruebas)
- **Comando:**  
  `python -m pytest -vv`
- **Pruebas Colectadas:** 109
- **Resultado:** `108 PASSED / 1 FAILED / 0 SKIPPED / 0 ERRORS`
- **Efectividad:** **99.08% PASS**
- **Tiempo de Ejecución:** `73.81 segundos`
- **Prueba Fallida:** `tests/test_domain_services.py::test_enrollment_service_and_transfer_service_atomicity`
- **Naturaleza de la Falla:** **`Defecto de Fixture / Secuencia en Prueba Unitaria Preexistente (Pre-existing Test Fixture Issue)`**

---

## 2. Diagnóstico Preciso de la Única Prueba Fallida

### Prueba: `tests/test_domain_services.py::test_enrollment_service_and_transfer_service_atomicity`
- **Línea de Falla:** `tests/test_domain_services.py:482`
- **Excepción:** `AcademicDomainError: No se pueden crear matrículas en un año lectivo que no esté activo.`
- **Causa Raíz:**
  1. En las líneas 446–452 de `test_domain_services.py`, la prueba crea un nuevo año lectivo directamente mediante el servicio de dominio:
     `ay = await ay_service.create_academic_year(...)`, el cual se inicializa en estado canónico `PLANNING` (Planificación).
  2. La prueba unitaria procede inmediatamente a invocar `enrollment_service.create_enrollment(...)` sin antes haber activado el año mediante `await ay_service.activate_academic_year(institution_id=inst1.id, academic_year_id=ay.id)`.
  3. El servicio de producción `EnrollmentService` hace cumplir estrictamente la regla de negocio que prohíbe matricular estudiantes en años escolares inactivos.
  4. El comportamiento de producción es **100% correcto y legítimo**.

---

## 3. Verificación de Invariantes de Seguridad (Security Invariants)

Se certifica formalmente que los siguientes componentes se mantienen **100% intactos, no debilitados y sin modificaciones**:
- [x] **`AuthService`**: Intacto.
- [x] **`CentralizedAuthorizationService`**: Intacto.
- [x] **`deps.py`**: Intacto.
- [x] **Control de Acceso Basado en Roles (RBAC)**: Intacto y validado.
- [x] **Aislamiento Multi-Inquilino (*Tenant Isolation*)**: Intacto y validado.
- [x] **Límites de Permisos (*Permission Boundaries*)**: Intactos y validados.
- [x] **Esquemas de Base de Datos**: Intactos.
