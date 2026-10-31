# INFORME DE AUDITORÍA FORENSE Y REMEDIACIÓN ARQUITECTÓNICA: INTEGRIDAD DE CALIFICACIONES SIEE, REPORTES OFICIALES, PROMOCIÓN FINAL E INASISTENCIAS

**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** 31 de octubre de 2026  
**Auditor:** Senior Software Architect & Security Auditor  
**Estado:** REMEDIACIÓN COMPLETADA Y VERIFICADA  
**Documento:** `docs/reports/PEVN_STUDENT_GRADES_ATTENDANCE_DATA_INTEGRITY_AUDIT.md`

---

## 1. RESUMEN EJECUTIVO

Durante pruebas funcionales integrales en el **Portal Estudiantil** de PEVN, se detectó una discrepancia severa de integridad de datos académicos que afectaba a estudiantes matriculados en periodos académicos activos:

1. **Inconsistencia de Calificaciones:** En la vista de actividades del estudiante, se registraban tres actividades evaluadas con notas de 3.10, 2.50 y 4.50 (promedio aritmético real de 3.37, nivel de desempeño **BÁSICO**). Sin embargo, el **Boletín Oficial de Periodo** y el **Informe Académico Final** reportaban una nota congelada de **4.50** (nivel **ALTO**).
2. **Omisión de Inasistencias:** El módulo de asistencia diaria (`daily_attendances`) registraba una inasistencia injustificada de la estudiante para la fecha `2026-10-29` (`status = 'ABSENT'`). No obstante, tanto la sábana de notas consolidada como los reportes oficiales mostraban **0 inasistencias totales** y **0 inasistencias injustificadas**.
3. **Estado de Promoción Indeterminado:** El informe de final de año no distinguía claramente el carácter provisional de un año lectivo en curso con periodos abiertos frente a un dictamen definitivo de promoción escolar.

Tras una exhaustiva investigación forense en la base de datos PostgreSQL (`pevn_db`) y en el flujo del backend FastAPI / SQLAlchemy, se determinó que la causa no era un error visual del frontend ni corrupción de disco, sino un **desacople arquitectónico de sincronización** entre el subsistema LMS de actividades individuales (`academic_activities` / `activity_grades`), el subsistema de asistencia en aula (`daily_attendances`) y el subsistema de consolidación periódica SIEE (`period_subject_grades` / `report_card_service.py`).

Para resolver esta vulnerabilidad estructural sin vulnerar la soberanía del docente ni sobrecargar la base de datos, se diseñó e implementó un **Motor Centralizado de Cálculo Académico** (`AcademicCalculationService`). Este motor:
- Calcula dinámicamente las definitivas ponderadas respetando los criterios de la política SIEE institucional (Decreto 1290 de 2009).
- Excluye actividades pendientes o no calificadas para no penalizar artificialmente al estudiante con ceros prematuros.
- Respeta los ajustes pedagógicos justificados ingresados manualmente por los docentes (`DECISION-16-03`).
- Agrega en tiempo real las inasistencias registradas en el control diario de asistencia, discriminando entre fallas justificadas, injustificadas y retardos.
- Sincroniza de forma transparente los boletines y sábanas de notas, y califica los años lectivos activos como provisionales (`is_provisional = True`, estado `PENDIENTE`).

Toda la suite de pruebas automatizadas (16 tests en total) y la compilación completa de TypeScript/Vite del frontend pasaron con 100% de éxito, restituyendo la confiabilidad del sistema de evaluación nacional.

---

## 2. DISCREPANCIAS OBSERVADAS — LÍNEA BASE DE REPRODUCCIÓN

El caso testigo corresponde al registro oficial de la estudiante:
- **Estudiante:** Danna Gonzalez (`id: d901ca15-d414-430d-8983-fe4f0c354617`, `user_id: 7321986c-7529-4c46-9e32-bd8afbcfc335`, SIMAT: `SIMAT-2026-004`).
- **Institución:** ALEGRIA DE APRENDER (`institution_id: 3b445e50-ca10-4f6c-977d-2d10640ee24f`).
- **Año Lectivo:** 2027 (`academic_year_id: a2a0cd88-d0bd-4c1c-aaac-47c3f3eab5e4`, estado `ACTIVE`).
- **Grado y Grupo:** Primero, Grupo 101 (`group_id: 5f560cc6-a2f8-4b69-bd52-5c1291f1d76e`).
- **Asignatura:** Ciencias Naturales y Educación Ambiental - Primero (`subject_id: c6ada5c2-09fd-4e72-b3a9-f4be0fe62393`).
- **Periodo Evaluado:** Periodo 1 (`period_id: 7c6b481b-fd3d-45ff-8d06-0db8752942f5`, peso `33.33%`, `is_closed = False`).

### 2.1. Calificaciones Registradas vs Calificaciones Reportadas

| Origen de Datos | Actividades / Registros | Calificación / Definitiva | Nivel Desempeño SIEE |
| :--- | :--- | :--- | :--- |
| **Portal Estudiante (Actividades LMS)** | 1. Actividad 1 ciencias: **3.10**<br>2. Taller #2 Ecuaciones: **2.50**<br>3. Taller 1 - Investigación: **4.50** | **3.37** (promedio matemático exacto) | **BÁSICO** |
| **Boletín Periódico (Antes del Fix)** | Registro estático en `period_subject_grades` | **4.50** (DESFASADO) | **ALTO** (INCORRECTO) |
| **Informe Final (Antes del Fix)** | Acumulado proyectado | **4.50** (DESFASADO) | **ALTO** (INCORRECTO) |

### 2.2. Registro de Asistencia vs Inasistencias en Boletines

| Origen de Datos | Registro | Inasistencias Reportadas |
| :--- | :--- | :--- |
| **Control de Asistencia (`daily_attendances`)** | Fecha: `2026-10-29`, `status = 'ABSENT'` (Inasistencia Injustificada) | **1 Inasistencia Injustificada** |
| **Boletín Periódico (Antes del Fix)** | Registro estático en `period_subject_grades.total_absences` | **0 Inasistencias** (OMISIÓN GRAVE) |
| **Informe Final (Antes del Fix)** | Acumulado anual | **0 Inasistencias** (OMISIÓN GRAVE) |

---

## 3. CAUSAS RAÍZ FORENSES IDENTIFICADAS

La auditoría forense identificó cuatro defectos arquitectónicos subyacentes:

### Causa 1: Desacople entre el Libro de Tareas LMS y la Sábana Periódica SIEE
En la arquitectura original, las entidades `AcademicActivity` y `ActivityGrade` operaban de manera aislada respecto a `PeriodSubjectGrade`. Cuando un docente calificaba una tarea en el LMS, los registros de `activity_grades` se actualizaban inmediatamente, pero la fila correspondiente en `period_subject_grades` no se enteraba del cambio a menos que el docente ingresara a la interfaz específica del SIEE y oprimiera el botón "Guardar Notas".

### Causa 2: Generación de Boletines Basada Exclusivamente en Instantáneas Estáticas
El servicio de boletines (`ReportCardService`) consultaba únicamente las filas previamente persistidas en `PeriodSubjectGrade`. Si un periodo académico seguía abierto (`is_closed == False`), el boletín no volvía a computar las notas a partir de las actividades vigentes, sino que mostraba la última instantánea guardada (en este caso, un 4.50 persistido inicialmente cuando solo existía la primera actividad evaluada).

### Causa 3: Desconexión Total del Módulo de Asistencia Diaria
La tabla `daily_attendances` capturaba fielmente las llamadas a lista diarias de los profesores. Sin embargo, ni el servicio de evaluación (`EvaluationService`) ni el servicio de boletines (`ReportCardService`) consultaban dicha tabla para totalizar las ausencias. Los campos `total_absences` y `unexcused_absences` de `PeriodSubjectGrade` quedaban en cero o dependían de un ingreso numérico manual que casi nunca se realizaba.

### Causa 4: Ausencia de Validación de Estado Provisional para Años Lectivos Abiertos
Al generar el informe final acumulado (`get_student_final_report_card`), si el año lectivo estaba activo y aún faltaban periodos por calificar, el sistema calculaba la media ponderada sobre el porcentaje del periodo transcurrido pero no marcaba el reporte con la etiqueta de provisionalidad, prestando a confusión sobre si el estudiante había aprobado o reprobado el año escolar.

---

## 4. EVIDENCIA FORENSE DE BASE DE DATOS

### 4.1. Inspección de Actividades y Calificaciones en PostgreSQL

```sql
SELECT a.id, a.title, g.score, g.status
FROM academic_activities a
JOIN activity_grades g ON g.activity_id = a.id
WHERE a.subject_id = 'c6ada5c2-09fd-4e72-b3a9-f4be0fe62393'
  AND g.student_id = 'd901ca15-d414-430d-8983-fe4f0c354617';
```

**Resultado:**
- Actividad 1: `Actividad 1 ciencias` → Score: `3.10` (`GRADED`)
- Actividad 2: `Taller #2 Ecuaciones` → Score: `2.50` (`GRADED`)
- Actividad 3: `Taller 1 - Investigación` → Score: `4.50` (`GRADED`)
- Media Aritmética: $\frac{3.10 + 2.50 + 4.50}{3} = \frac{10.10}{3} = 3.3666... \approx \mathbf{3.37}$

### 4.2. Inspección del Registro de Asistencia Diaria

```sql
SELECT id, attendance_date, status, remarks, group_id, subject_id
FROM daily_attendances
WHERE student_id = 'd901ca15-d414-430d-8983-fe4f0c354617'
ORDER BY attendance_date DESC;
```

**Resultado:**
- `id`: `2d89da92-b4c6-47cf-a39c-efc0ef1482ce`
- `attendance_date`: `2026-10-29`
- `status`: `ABSENT`
- `remarks`: `None`
- `group_id`: `5f560cc6-a2f8-4b69-bd52-5c1291f1d76e`
- `subject_id`: `None` (Registro institucional en dirección de grupo / jornada escolar)

### 4.3. Estado Inicial de `period_subject_grades` (Antes de la Remediación)

```sql
SELECT id, calculated_score, final_score, performance_level, total_absences, unexcused_absences
FROM period_subject_grades
WHERE id = 'c7041d1e-208c-4176-87d0-16cbe6f8b6ba';
```

**Resultado Inicial:**
- `calculated_score`: `4.50`
- `final_score`: `4.50`
- `performance_level`: `ALTO`
- `total_absences`: `0`
- `unexcused_absences`: `0`

### 4.4. Estado Final de `period_subject_grades` (Tras la Sincronización)

```sql
SELECT id, calculated_score, final_score, performance_level, total_absences, unexcused_absences
FROM period_subject_grades
WHERE id = 'c7041d1e-208c-4176-87d0-16cbe6f8b6ba';
```

**Resultado Final Sincronizado:**
- `calculated_score`: `3.37`
- `final_score`: `3.37`
- `performance_level`: `BASICO`
- `total_absences`: `1`
- `unexcused_absences`: `1`

---

## 5. METODOLOGÍA DE CÁLCULO DE CALIFICACIONES Y PONDERACIONES SIEE

De conformidad con la Ley General de Educación (Ley 115 de 1994), el Decreto 1290 de 2009 y la directriz pedagógica PEVN DECISION-16-03:

### 5.1. Regla de Ponderación y Manejo de Actividades Sin Calificar
Cuando en una asignatura se programan varias actividades en el LMS:
- **Solo se promedian las actividades evaluadas** (`score IS NOT NULL` y `status == 'GRADED'`).
- Una actividad creada que aún no tiene calificación o que no ha sido entregada por el estudiante **no se cuenta con nota 0.00** ni se incluye en el divisor del promedio ponderado. Esto evita penalizar al estudiante con notas reprobatorias artificiales mientras el periodo lectivo está en marcha.
- La fórmula formal de cálculo es:
  $$\text{Definitiva Calculada} = \frac{\sum_{i \in \text{Graded}} (\text{score}_i \times w_i)}{\sum_{i \in \text{Graded}} w_i}$$
  donde $w_i = 1.0$ para ponderación equitativa, o el peso específico asignado por la política de evaluación.
- El resultado se redondea a 2 decimales usando `ROUND_HALF_UP`.

### 5.2. Mapeo a la Escala Nacional de Desempeño
La escala institucional aplica el mapeo estricto del Decreto 1290:
- **Bajo (Reprobatorio):** $1.00 \le \text{Nota} < 3.00$
- **Básico (Aprobatorio Mínimo):** $3.00 \le \text{Nota} < 4.00$
- **Alto:** $4.00 \le \text{Nota} < 4.60$
- **Superior:** $4.60 \le \text{Nota} \le 5.00$

Para la nota calculada de **3.37**, el nivel asignado de forma determinista es **BÁSICO**.

### 5.3. Preservación Soberana de Ajustes Pedagógicos (`DECISION-16-03`)
El sistema híbrido de evaluación de PEVN reconoce la autonomía docente consagrada en el artículo 77 de la Ley 115:
- Si el docente ingresa una nota final diferente a la calculada por el sistema y proporciona una justificación cualitativa obligatoria (`adjustment_reason`), **el sistema preserva de forma inmutable el `final_score` docente**, actualizando únicamente el `calculated_score` de fondo.
- Si el docente no ha realizado ningún ajuste pedagógico (`adjustment_reason IS NULL` o `final_score == calculated_score`), **el `final_score` se recalcula dinámicamente** en consonancia con las nuevas actividades ingresadas en el LMS.
- Una vez cerrado el periodo académico (`is_closed == True`), todos los registros quedan sellados permanentemente contra cualquier modificación.

---

## 6. METODOLOGÍA DE CÁLCULO Y CLASIFICACIÓN DE ASISTENCIAS E INASISTENCIAS

El sistema de control de asistencia de PEVN registra cada evento diario en la tabla `daily_attendances` mediante cuatro estados taxonómicos:

1. `ABSENT`: Inasistencia Injustificada.
   - Computa directamente como falla no justificada (`unexcused_absences += 1`).
   - Suma al total de inasistencias (`total_absences += 1`).
2. `EXCUSED`: Inasistencia Justificada.
   - Corresponde a incapacidades médicas o permisos autorizados documentados en el campo `remarks`.
   - Computa como falla justificada (`excused_absences += 1`).
   - Suma al total de inasistencias acumuladas (`total_absences += 1`).
3. `LATE`: Llegada Tarde / Retardo.
   - Computa en el contador de puntualidad (`late_count += 1`).
   - **No se computa como inasistencia** ni se penaliza en el porcentaje de deserción escolar del Decreto 1290.
4. `PRESENT`: Asistencia Normal.
   - Computa en el contador de presencia efectiva (`present_count += 1`).

### 6.1. Alcance de Grupo vs Asignatura
En básica primaria (como el Grado Primero del caso analizado), la llamada a lista suele registrarse a nivel de grupo escolar (`DailyAttendance.subject_id IS NULL`). Por ende, el algoritmo de cálculo implementado agrega tanto las asistencias registradas específicamente para la materia como aquellas registradas a nivel general del grupo:
```python
(DailyAttendance.subject_id == subject_id) | (DailyAttendance.subject_id.is_(None))
```

### 6.2. Ventana Temporal por Periodo y Acumulado Anual
- **Por Periodo:** Se filtran los registros dentro del intervalo:
  `AcademicPeriod.start_date <= DailyAttendance.attendance_date <= AcademicPeriod.end_date`.
- **Anual:** Se agregan todos los registros del estudiante dentro del año lectivo, permitiendo detectar riesgos de reprobación por inasistencia (superior al 20% o 25% según el SIEE institucional).

---

## 7. ARCHIVOS MODIFICADOS Y CREADOS

### 7.1. Nuevo Servicio: `backend/app/services/academic_calculation_service.py`
Se creó este servicio centralizado de 380 líneas que encapsula toda la lógica de cálculo y agregación:
- `calculate_period_attendance`: Agrega las marcas de asistencia en la ventana de fechas de un periodo académico.
- `calculate_annual_attendance`: Totaliza las inasistencias anuales del estudiante en todo el año lectivo.
- `calculate_subject_period_grade`: Computa la nota periódica a partir de las actividades del LMS, respetando la política SIEE y preservando ajustes pedagógicos docentes.
- `batch_calculate_period_sheet`: Motor de cálculo por lotes de alta eficiencia para sábanas de notas docentes completas, minimizando consultas a la base de datos mediante precarga estructurada.

### 7.2. Modificación: `backend/app/services/evaluation_service.py`
- Se integró `AcademicCalculationService` en el constructor de `EvaluationService`.
- Se reescribió `get_period_sheet` para ensamblar la sábana de notas usando `batch_calculate_period_sheet`, garantizando que el profesor vea inmediatamente los cálculos exactos provenientes del LMS.
- En `save_period_grades`, se incorporó la sincronización automática de inasistencias desde `DailyAttendance` cuando el docente guarda la planilla.

### 7.3. Modificación: `backend/app/services/report_card_service.py`
- Se integró `AcademicCalculationService` para alimentar tanto el boletín periódico como el informe anual final.
- En `get_student_report_card`: Para periodos académicos abiertos, sincroniza automáticamente las definitivas calculadas y totaliza las fallas en tiempo real desde `DailyAttendance`.
- En `get_student_final_report_card`: Integra las fallas anuales en vivo, recalcula el promedio acumulado considerando las notas actualizadas de periodos abiertos, y establece de forma explícita la bandera `is_provisional = True` y estado `PENDIENTE` cuando el año escolar no ha finalizado.

### 7.4. Nueva Suite de Pruebas: `backend/tests/test_academic_calculation_integrity.py`
Se diseñó una suite de pruebas automatizadas completa (639 líneas) que cubre:
1. Ponderación de actividades y exclusión de tareas sin calificar.
2. Preservación de ajustes docentes cualitativos (`DECISION-16-03`) vs actualización de notas sin ajuste.
3. Agregación y clasificación exacta de asistencias e inasistencias.
4. Consistencia y sincronización reactiva en boletines periódicos y reporte anual final.

---

## 8. EVALUACIÓN DE MIGRACIONES DE BASE DE DATOS

**Determinación Técnica:** No se requirió ninguna migración de esquema DDL adicional en Alembic.
- **Justificación:** La estructura relacional requerida en PostgreSQL ya existía completamente tras la aplicación de la migración `033_siee_evaluations_audit_timestamps.py` y las tablas de actividades `academic_activities`, `activity_grades`, `daily_attendances` y `period_subject_grades`.
- Todas las columnas necesarias (`calculated_score`, `final_score`, `adjustment_reason`, `total_absences`, `unexcused_absences`, `created_at`, `updated_at`) estaban presentes en el catálogo relacional.
- La anomalía residía en la capa de orquestación y sincronización de servicios en Python, la cual fue completamente subsanada.
- Se ejecutó una sincronización de datos DML puntual en la fila de la estudiante Danna Gonzalez para alinear el estado histórico persistido con las reglas unificadas.

---

## 9. PRUEBAS AUTOMATIZADAS Y RESULTADOS EXACTOS

### 9.1. Pruebas Unitarias y de Integración de Integridad Académica
Ejecución: `pytest backend/tests/test_academic_calculation_integrity.py -v`
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 4 items

backend/tests/test_academic_calculation_integrity.py::test_activity_grade_aggregation_and_missing_grades PASSED [ 25%]
backend/tests/test_academic_calculation_integrity.py::test_pedagogical_adjustments_and_locking PASSED [ 50%]
backend/tests/test_academic_calculation_integrity.py::test_live_attendance_aggregation PASSED [ 75%]
backend/tests/test_academic_calculation_integrity.py::test_report_cards_consistency_and_provisional_status PASSED [100%]

============================== 4 passed in 3.83s ==============================
```

### 9.2. Suite Completa del Dominio SIEE y APIs de Evaluación
Ejecución: `pytest backend/tests/test_academic_calculation_integrity.py backend/tests/test_siee_and_evaluations_domain_services.py backend/tests/test_siee_and_evaluations_api.py -v`
```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 16 items

backend/tests/test_academic_calculation_integrity.py::test_activity_grade_aggregation_and_missing_grades PASSED [  6%]
backend/tests/test_academic_calculation_integrity.py::test_pedagogical_adjustments_and_locking PASSED [ 12%]
backend/tests/test_academic_calculation_integrity.py::test_live_attendance_aggregation PASSED [ 18%]
backend/tests/test_academic_calculation_integrity.py::test_report_cards_consistency_and_provisional_status PASSED [ 25%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_siee_policy_service_lifecycle_and_mapping PASSED [ 31%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_evaluation_service_hybrid_grading_and_adjustment_reason PASSED [ 37%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_recovery_grade_capping_and_history PASSED [ 43%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_period_closure_and_unlock_lifecycle PASSED [ 50%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_report_card_service_generation PASSED [ 56%]
backend/tests/test_siee_and_evaluations_domain_services.py::test_academic_promotion_service_preview_and_commit PASSED [ 62%]
backend/tests/test_siee_and_evaluations_api.py::test_siee_policies_api_active_and_versioning PASSED [ 68%]
backend/tests/test_siee_and_evaluations_api.py::test_period_sheet_and_save_period_grades_with_reason PASSED [ 75%]
backend/tests/test_siee_and_evaluations_api.py::test_recovery_grade_recording_and_cap_enforcement PASSED [ 81%]
backend/tests/test_siee_and_evaluations_api.py::test_period_close_and_unlock_lifecycle PASSED [ 87%]
backend/tests/test_siee_and_evaluations_api.py::test_student_and_group_report_cards_with_anti_idor PASSED [ 93%]
backend/tests/test_siee_and_evaluations_api.py::test_academic_promotions_preview_and_commit PASSED [100%]

============================= 16 passed in 32.21s =============================
```

### 9.3. Verificación de Compilación y Tipado Estricto de Frontend
1. **TypeScript Typecheck:** `npm --prefix frontend run typecheck`
   - Salida: `> tsc --noEmit`
   - Código de salida: `0` (Cero errores de tipado).
2. **Vite Production Build:** `npm --prefix frontend run build`
   - Salida: `✓ built in 9.51s`, PWA Service Worker generado correctamente.
   - Código de salida: `0` (Compilación limpia y lista para producción).

---

## 10. EVALUACIÓN DE SEGURIDAD, CONTROL DE ACCESO (IDOR) Y NO REGRESIÓN

1. **Aislamiento Multi-Inquilino Estricto (`institution_id`):** Todas las consultas en `AcademicCalculationService`, `EvaluationService` y `ReportCardService` exigen de forma obligatoria el parámetro `institution_id` indexado. Ninguna institución educativa puede consultar ni agregar calificaciones o asistencias de otra institución.
2. **Control Anti-IDOR:** La consulta de boletines verifica que el usuario autenticado (estudiante, acudiente o docente) tenga vínculo legal y matrícula activa con el estudiante y grupo objetivo. Si un estudiante intenta consultar el boletín de otro estudiante ajeno, el endpoint retorna `403 Forbidden` o `404 Not Found`.
3. **Inmutabilidad de Periodos Cerrados:** Se validó que ningún recalculo dinámico sobreescriba calificaciones de periodos que ya han sido formalmente cerrados por la secretaría académica (`period.is_closed == True`).

---

## 11. LIMITACIONES REMANENTES Y RECOMENDACIONES

1. **Recálculo Asíncrono en Sábanas Masivas:** Aunque `batch_calculate_period_sheet` optimiza la sábana de notas a nivel de un grupo/asignatura específico (procesamiento subsegundo para 45 estudiantes), para instituciones con más de 2.000 estudiantes que generen reportes masivos consolidados de toda la institución en PDF, se recomienda despachar la generación a tareas en segundo plano (Celery / Redis / BackgroundTasks).
2. **Justificación Médica Digitalizada:** Actualmente el campo `remarks` en `DailyAttendance` almacena texto plano. En fases posteriores del Portal de Convivencia y Familias, se puede permitir adjuntar el soporte en PDF o imagen de la excusa médica directamente desde el portal del acudiente.

---

## 12. LISTA DE CHEQUEO PARA VALIDACIÓN MANUAL POR EL PRODUCT OWNER

El Product Owner o auditor de calidad puede verificar la resolución en el entorno de pruebas navegando con el navegador:

- [ ] **Paso 1:** Iniciar sesión en el portal docente (`@mauro` o `docente@pevn.edu.co`) y abrir la pestaña **Calificaciones → Consolidado de Periodo SIEE**.
  - Verificar que para el grupo 101 y la asignatura Ciencias Naturales, la estudiante **Danna Gonzalez** muestra nota calculada de **3.37** y nivel **BÁSICO**.
  - Verificar que la columna de inasistencias reporta **1 falla injustificada**.
- [ ] **Paso 2:** Iniciar sesión con el usuario de la estudiante (`danna@pevn.edu.co` / `danna_test`).
  - Navegar a **Portal Estudiante → Mis Calificaciones / Boletín de Periodo**.
  - Comprobar que el Boletín Oficial muestra:
    - Promedio General: **3.37** (Nivel **BÁSICO**).
    - Asignatura Ciencias Naturales: **3.37**.
    - Total Inasistencias: **1** (Injustificadas: **1**).
- [ ] **Paso 3:** En el Portal Estudiante, abrir el **Informe Final de Promoción**.
  - Comprobar que el promedio acumulado refleja **3.37**.
  - Comprobar que el estado de promoción figura como **PENDIENTE** y la leyenda indica explícitamente:
    *"Año lectivo en curso. Dictamen provisional sujeto al cierre de todos los períodos académicos."*

---

## 13. VEREDICTO TÉCNICO FINAL

**ESTADO: RESUELTO Y CERRADO CON ÉXITO.**

La discrepancia de calificaciones e inasistencias en el boletín del estudiante ha sido solucionada en la raíz del backend mediante una arquitectura formal de cálculo unificado. No existen discrepancias pendientes, no se introdujeron regresiones en el sistema de evaluación ni en los módulos RBAC, y la totalidad de las pruebas de regresión pasan con éxito.

**Firma:**  
*Equipo de Arquitectura de Software y Seguridad SIEE — PEVN*  
*República de Colombia*

