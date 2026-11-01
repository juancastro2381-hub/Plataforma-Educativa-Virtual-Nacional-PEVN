# PEVN — REGISTRO MAESTRO DE REMEDIACIONES Y HALLAZGOS (REMEDIATION REGISTER)

**Documento:** `11_REMEDIATION_REGISTER.md`  
**Programa:** Master Enterprise Audit, Remediation, Security Hardening and Production Readiness  
**Plataforma:** Plataforma Educativa Virtual Nacional (PEVN) — República de Colombia  
**Fecha de Emisión:** 1 de Noviembre de 2026  
**Clasificación:** Confidencial / Gestión de Defectos & Trazabilidad  
**Estado:** *Consolidado, Probado y Verificado*

---

## 1. INTRODUCCIÓN Y METODOLOGÍA DE CLASIFICACIÓN

El presente documento consolida el inventario formal de todos los hallazgos técnicos, vulnerabilidades de seguridad, defectos de persistencia, inconsistencias pedagógicas y mejoras de experiencia de usuario identificados y atendidos durante el programa de endurecimiento empresarial de la Plataforma Educativa Virtual Nacional (PEVN).

Cada hallazgo se categoriza según su severidad y estado de resolución:
- **CRÍTICA**: Afecta directamente la integridad de calificaciones, la confidencialidad de datos personales o la disponibilidad del servicio.
- **ALTA**: Vulnerabilidad de seguridad explotable, falla de persistencia o degradación funcional severa.
- **MEDIA**: Inconsistencia visual, defecto de usabilidad o ausencia de optimización.
- **BAJA / INFO**: Oportunidad de refactorización o mejora preventiva de código.

---

## 2. MATRIZ CONSOLIDADA DE HALLAZGOS Y REMEDIACIONES

| ID | Categoría | Título del Hallazgo | Severidad | Estado | Componente Afectado |
|---|---|---|:---:|:---:|---|
| **SEC-001** | Ciberseguridad | Detección y Bloqueo de Replay en Familias de Refresh Tokens | **CRÍTICA** | **Verificado** | `backend/app/services/auth_service.py` |
| **SEC-002** | Ciberseguridad | Restricción Estricta de CORS y Cabecera Host en Producción | **ALTA** | **Verificado** | `backend/app/core/config.py` & `main.py` |
| **SEC-003** | Ciberseguridad | Prohibición del Enlace Dev de Reseteo de Password en Prod | **CRÍTICA** | **Verificado** | `backend/app/api/v1/endpoints/auth.py` |
| **SEC-004** | Ciberseguridad | Validación de Magic Bytes y Bloqueo Anti-Path-Traversal | **ALTA** | **Verificado** | `backend/app/core/storage/local.py` |
| **RBAC-001**| Control de Acceso| Principio PO Least-Privilege sobre Recursos Académicos | **CRÍTICA** | **Verificado** | `backend/app/core/security/authorization.py` |
| **RBAC-002**| Control de Acceso| Falla de Serialización de Roles Canónicos en Directorio | **ALTA** | **Verificado** | `backend/app/schemas/user.py` & `user_service.py` |
| **RBAC-003**| Control de Acceso| Enforzamiento Anti-IDOR en Portales Estudiante y Acudiente| **CRÍTICA** | **Verificado** | `backend/app/api/deps.py` & `guardian_portal_service.py` |
| **DB-001**  | Base de Datos   | Omisión de Modelos ORM en Registro `backend/app/db/base.py`| **ALTA** | **Verificado** | `backend/app/db/base.py` |
| **DB-002**  | Base de Datos   | Discrepancia en Columnas de Auditoría (Migración 033) | **ALTA** | **Verificado** | `backend/migrations/versions/033_*.py` |
| **EDU-001** | Dominio SIEE    | Replicación Indebida de Calificaciones P1 a Períodos Futuros| **CRÍTICA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **EDU-002** | Dominio SIEE    | Omisión de Asignaturas Estatutarias en Boletines de Período| **CRÍTICA** | **Verificado** | `backend/app/services/curriculum_resolution_service.py`|
| **EDU-003** | Dominio SIEE    | Penalización Errónea de Asignaturas Pendientes en Promedio| **CRÍTICA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **EDU-004** | Dominio SIEE    | Omisión de Calificaciones con Status por Defecto PENDING | **ALTA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **EDU-005** | Dominio SIEE    | Pérdida de Ajustes Pedagógicos sin Actividades LMS Previas | **ALTA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **EDU-006** | Dominio SIEE    | Reset Involuntario de Inasistencias en Período Abierto | **ALTA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **API-001** | Servicios API   | Error Recurrente HTTP 500 en GET `/evaluations/period-sheet`| **CRÍTICA** | **Verificado** | `backend/app/services/academic_calculation_service.py`|
| **UI-001**  | Frontend / UX   | Uso de Diálogos Nativos Bloqueantes (`window.alert/confirm`)| **MEDIA** | **Verificado** | `frontend/src/context/ModalContext.tsx` |
| **UI-002**  | Frontend / UX   | Visualización de "Sin roles" en Directorio de Usuarios | **MEDIA** | **Verificado** | `frontend/src/views/UserDirectoryView.tsx` |

---

## 3. FICHAS DETALLADAS DE REMEDIACIÓN

### Ficha Técnica: SEC-001 (Rotación y Detección de Replay en Refresh Tokens)
- **Causa Raíz**: Si un token de refresco era interceptado y reutilizado después de haber sido rotado, no se invalidaba la familia de tokens, permitiendo sesiones concurrentes fraudulentas.
- **Remediación**: Se implementó el campo `family_id` en la tabla `refresh_tokens`. Si se presenta un token ya revocado perteneciente a una familia activa, el sistema asume compromiso de credenciales y revoca inmediatamente **todos** los tokens de la familia, obligando a un nuevo login.
- **Archivos Modificados**: `backend/app/models/token.py`, `backend/app/services/auth_service.py`.
- **Verificación**: `backend/tests/test_auth_security_hardening.py` (100% PASSED).

---

### Ficha Técnica: RBAC-001 (Principio PO Least-Privilege en Gestión Académica)
- **Causa Raíz**: Roles administrativos de nivel ministerial y territorial tenían asignados accidentalmente permisos de visualización y edición sobre recursos académicos de aula.
- **Remediación**: Se definió la lista `ACADEMIC_MANAGEMENT_RESOURCES` en `backend/app/core/security/authorization.py` y se bloqueó categóricamente su asignación a `SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN` y `MUNICIPALITY_ADMIN`.
- **Archivos Modificados**: `backend/app/core/security/authorization.py`, `backend/app/services/rbac_bootstrap_service.py`.
- **Verificación**: `backend/tests/test_academic_admin_roles_authorization.py` (7 tests PASSED).

---

### Ficha Técnica: DB-001 (Registro Incompleto de Modelos en `app/db/base.py`)
- **Causa Raíz**: Los modelos `TechnicalIncident`, `StudentSubmission`, `SieePolicy`, `PeriodSubjectGrade`, `AcademicAchievement`, `StudentPromotion` y `RecoveryGrade` estaban declarados en `app/models/`, pero ausentes en `backend/app/db/base.py`. Esto impedía que `Alembic` los detectara en `target_metadata = Base.metadata`.
- **Remediación**: Se actualizó `backend/app/db/base.py` incorporando el 100% de los modelos declarados en `app/models/__init__.py`.
- **Archivos Modificados**: `backend/app/db/base.py`.
- **Verificación**: `alembic check` y pruebas de descubrimiento relacional PASSED.

---

### Ficha Técnica: EDU-001 (Aislamiento de Períodos Futuros en Boletines)
- **Causa Raíz**: El servicio de reporte anual asumía calificaciones históricas para períodos futuros cuando no encontraba notas, o duplicaba las notas del Período 1 en los Períodos 2 y 3.
- **Remediación**: Se implementó una verificación estricta de estado de período en `AcademicCalculationService` y `ReportCardService`. Un período con estado `CONFIGURADO` o `PROGRAMADO` se reporta invariablemente como `Pendiente` (renderizado como `—`).
- **Archivos Modificados**: `backend/app/services/academic_calculation_service.py`, `backend/app/services/report_card_service.py`.
- **Verificación**: `backend/tests/test_academic_curriculum_and_report_cards.py` (tests 01 a 09 PASSED).

---

### Ficha Técnica: API-001 / EDU-004 / EDU-005 (Recurrencia de HTTP 500 en `/period-sheet`)
- **Causa Raíz**: 
  1. La consulta `sub_stmt` en `AcademicCalculationService` filtraba estrictamente por `ActivityGrade.status == ActivitySubmissionStatus.GRADED`. Aquellas notas creadas con `score` válido pero con `status` por defecto `PENDING` eran omitidas.
  2. Cuando no existían actividades evaluadas en el LMS (`total_weight == 0`), el algoritmo sobreescribía `calculated_score = computed_score` fijándolo en `0.00` en lugar de preservar el ajuste pedagógico previo guardado por el docente.
  3. Las inasistencias consolidadas se reseteaban a 0 si no había registros en `daily_attendance`.
- **Remediación**:
  - Filtro inclusivo: `or_(ActivityGrade.status == ActivitySubmissionStatus.GRADED, ActivityGrade.score.is_not(None))`.
  - Preservación de ajuste: `calculated_score = computed_score if total_weight > Decimal("0.00") else existing_rec.calculated_score`.
  - Fallback de asistencia consolidada: `if not st_atts and existing_rec: total_absences = existing_rec.total_absences`.
- **Archivos Modificados**: `backend/app/services/academic_calculation_service.py`.
- **Verificación**: `backend/tests/test_evaluation_period_sheet_regression.py` (7 tests PASSED).

---

### Ficha Técnica: UI-001 (Sistema Centralizado de Modales y Notificaciones)
- **Causa Raíz**: Vistas del frontend invocaban diálogos sincrónicos bloqueantes del navegador (`window.confirm()`, `window.alert()`).
- **Remediación**: Se creó `ModalContext` y su componente anfitrión `ModalContainer`, ofreciendo confirmaciones asíncronas con soporte para teclado (`Escape`, `Tab`), variantes de color institucionales y promesa limpia.
- **Archivos Modificados**: `frontend/src/context/ModalContext.tsx`, `frontend/src/components/common/ModalContainer.tsx`, `frontend/src/views/TeacherSieeEvaluationView.tsx`.
- **Verificación**: Typecheck y build exitosos, validación en navegador.

---

## 4. CONCLUSIÓN DEL REGISTRO

El 100% de los hallazgos críticos y de alta severidad identificados durante la auditoría fueron remediados, documentados y validados mediante pruebas automatizadas de regresión. No persisten defectos bloqueantes abiertos en la plataforma.

**Dictamen:** **REGISTRO DE REMEDIACIONES CERRADO Y VALIDADO**

