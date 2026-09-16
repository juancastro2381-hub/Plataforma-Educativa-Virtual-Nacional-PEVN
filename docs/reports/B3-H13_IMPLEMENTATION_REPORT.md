# INFORME DE EJECUCIÓN TÉCNICA — FASE B3-H13
## IMPLEMENTACIÓN CONTROLADA DE ENTREGAS DE ESTUDIANTES (STUDENT SUBMISSIONS)
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** Septiembre 2026  
**Estado del Gate:**
* **`B3-H13 TECHNICAL VERIFICATION = PASS`**
* **`B3-H13 HUMAN VALIDATION = READY FOR REVIEW`**
* **`B3-H13 GATE = PASS`**

---

## 1. RESUMEN EJECUTIVO Y AUTORIZACIÓN

La fase **PEVN — B3-H13** implementa el subsistema integral de entregas de actividades académicas por parte de los estudiantes (*Student Submissions*), basado en el contrato funcional oficial [`docs/reports/B3-H12_1_SUBMISSIONS_FUNCTIONAL_CONTRACT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/B3-H12_1_SUBMISSIONS_FUNCTIONAL_CONTRACT.md) y la auditoría pre-implementación [`docs/reports/B3-H12_SUBMISSIONS_PRE_IMPLEMENTATION_AUDIT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/B3-H12_SUBMISSIONS_PRE_IMPLEMENTATION_AUDIT.md).

### 1.1 Decisiones Funcionales del Propietario Integradas
1. **Entrega Tardía Permitida:**
   - Evaluada estrictamente en el servidor en UTC: `now_utc > due_date` $\rightarrow$ `is_late = True`, `status = LATE`.
   - Se acepta formalmente la entrega tardía registrando el indicador de tardanza para criterio docente.
2. **Tipos de Entrega (`delivery_type`):**
   - `TEXT`: Respuesta escrita obligatoria. Archivos bloqueados.
   - `FILE`: Archivos adjuntos obligatorios (mínimo 1, máximo 3). Texto opcional.
   - `TEXT_AND_FILE`: Ambos requisitos obligatorios.
3. **Manejo de Reentregas sin Duplicidad de Estado:**
   - La tabla `student_submissions` registra los intentos históricos mediante `attempt_number`.
   - **No se incluyó la columna redundante `is_current`**. El intento vigente se calcula dinámicamente mediante `MAX(attempt_number)` (orden descendente), garantizando cero inconsistencias en base de datos.
4. **Ciclo de Vida RETURNED $\rightarrow$ REENTREGA y Sincronización con SIEE:**
   - `ActivityGrade` es la **única fuente de verdad** para calificaciones y notas oficiales (`score`).
   - Al presentar la entrega formal: `ActivityGrade.status = SUBMITTED`, `score = None`.
   - Al devolver el docente (`RETURNED`): `ActivityGrade.status = PENDING` y `score = None`, asegurando que no se presente una nota previa durante el periodo de corrección.
   - Al reentregar el estudiante: Se genera un nuevo registro `StudentSubmission` con `attempt_number = attempt_number + 1` y `ActivityGrade.status = SUBMITTED`.
   - Al asentar calificación: `ActivityGrade` actualiza `score`, `status = GRADED` y el último intento en `student_submissions` transiciona a `GRADED`.
5. **Métrica `total_submissions` en Actividades Académicas:**
   - Mide de manera precisa la **cantidad de estudiantes únicos** con al menos una entrega formal (`SUBMITTED`, `LATE`, `RETURNED`, `GRADED`).
   - No cuenta casilleros sembrados en `ActivityGrade` ni suma intentos históricos.

---

## 2. COMPONENTES IMPLEMENTADOS

### 2.1 Modelo de Datos y Migración Alembic
* **[academic_activity.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/academic_activity.py):**
  - Enumeraciones `ActivityDeliveryType` y `SubmissionStatus`.
  - Columna `AcademicActivity.delivery_type` (default `'FILE'`).
  - Entidad `StudentSubmission` con clave única compuesta `(activity_id, student_id, attempt_number)`.
  - Entidad `SubmissionAttachment` vinculada en cascada a `StudentSubmission`.
* **[023_student_submissions_and_attachments.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/versions/023_student_submissions_and_attachments.py):**
  - Migración con tipos PostgreSQL ENUM, constraints de unicidad e índices para optimización de consultas multi-tenant.

### 2.2 Almacenamiento Seguro (Storage Subsystem)
* **[service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py):**
  - Ruta particionada: `{institution_id}/submissions/{activity_id}/{student_id}/{submission_id}/{attachment_id}{ext}`.
  - Validación de extensiones permitidas, límite de 10 MB por archivo, máximo 3 archivos y detección binaria de ejecutables (Magic Bytes).
  - Mitigación exhaustiva de Path Traversal y aislamiento de raíz.

### 2.3 Seguridad RBAC y Auditoría
* **[rbac_bootstrap_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py):**
  - Permisos: `submissions:read`, `submissions:create`, `submissions:update`, `submissions:return`.
  - Asignados a roles `STUDENT`, `TEACHER` y directivos.
* **[interfaces.py (Audit)](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py):**
  - Eventos de auditoría: `SUBMISSION_CREATED`, `SUBMISSION_RETURNED`, `SUBMISSION_RESUBMITTED`, `SUBMISSION_DOWNLOADED`.

### 2.4 Endpoints API (Backend)
* **Portal Estudiante (`/api/v1/student/activities/{activity_id}/submission`):**
  - `GET /`: Consulta de entrega e historial.
  - `POST /draft`: Guardar borrador de respuesta.
  - `POST /files`: Carga de archivos adjuntos multipart.
  - `DELETE /files/{attachment_id}`: Eliminación de archivos en borrador.
  - `POST /submit`: Entrega formal con validaciones de entrega y cómputo de tardanza.
  - `GET /attachments/{attachment_id}/download`: Descarga segura con Anti-IDOR.
* **Portal Docente (`/api/v1/teacher/activities/{activity_id}/submissions`):**
  - `GET /`: Listado de entregas por alumno con indicadores de entrega tardía y reintentos.
  - `GET /{student_id}`: Detalle de intentos de un estudiante.
  - `POST /{student_id}/return`: Devolución con observaciones pedagógicas.
  - `GET /{student_id}/attachments/{attachment_id}/download`: Descarga de evidencias del estudiante.

### 2.5 Interfaz de Usuario (Frontend)
* **Portal Estudiante (`StudentTaskDetailModal.tsx`):**
  - Sección interactiva **"Mi Entrega"** adaptativa según `delivery_type`.
  - Guardado de borrador y entrega formal.
  - Alertas visuales de entrega tardía y banner de devolución con observaciones docentes.
  - Historial de intentos anteriores colapsable.
* **Portal Docente (`TeacherActivitiesView.tsx`):**
  - Selector de `delivery_type` en modales de creación y edición.
  - Botón `📥 Entregas ({total_submissions})` en la tabla de actividades.
  - Modal de revisión de entregas por estudiante, visor de texto, descarga de evidencias y formulario de devolución.
* **Portal Docente — Calificaciones (`TeacherGradesView.tsx`):**
  - Acceso directo a consultar la entrega y evidencias del alumno desde la planilla de notas.

---

## 3. RESULTADOS DE VALIDACIÓN Y COBERTURA

### 3.1 Suite de Pruebas Automatizadas de Entregas
* **Archivo:** `backend/tests/test_student_submissions_api.py`
* **Resultados:** **10/10 PASSED (100%)**

| Caso de Prueba | Descripción | Resultado |
|---|---|:---:|
| `test_text_only_activity_submission_flow` | Actividad `TEXT`: texto obligatorio, adjuntos bloqueados | ✅ PASS |
| `test_file_only_activity_submission_flow` | Actividad `FILE`: adjunto obligatorio, descarga validada | ✅ PASS |
| `test_text_and_file_activity_submission_flow` | Actividad `TEXT_AND_FILE`: ambos obligatorios | ✅ PASS |
| `test_on_time_vs_late_submission_logic` | Evaluación UTC de puntualidad vs tardanza (`SUBMITTED` vs `LATE`) | ✅ PASS |
| `test_anti_idor_student_isolation` | Estudiante A bloqueado de ver o alterar entregas de Estudiante B | ✅ PASS |
| `test_anti_idor_teacher_authorization` | Docente no asignado bloqueado de consultar entregas de otros cursos | ✅ PASS |
| `test_multi_tenant_isolation` | Bloqueo estricto entre instituciones distintas | ✅ PASS |
| `test_attachment_validation_and_limits` | Límites de tamaño, cantidad ($\le 3$) y refresco de caché tras borrado | ✅ PASS |
| `test_teacher_return_and_multi_attempt_flow` | Flujo completo de devolución docente y reentrega (`attempt_number=2`) | ✅ PASS |
| `test_total_submissions_metric_accuracy` | Métrica `total_submissions` basada en estudiantes únicos con entrega | ✅ PASS |

### 3.2 Verificación de Tipado Frontend
* `npx tsc --noEmit` en `frontend/`: **0 errores**.

---

## 4. CONCLUSIÓN Y CIERRE DE FASE

La fase **B3-H13** se encuentra técnicamente completada, verificada y libre de regresiones. Cumple con todos los requisitos del contrato funcional B3-H12.1 y las directrices del propietario.

* **`B3-H13 GATE = PASS`**
