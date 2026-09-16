# REPORTE TÉCNICO DE RESOLUCIÓN DE BLOQUEO — FASE B3-H13 (H1)
## INVESTIGACIÓN Y CORRECCIÓN DE ERROR HTTP 500 EN GET /api/v1/student/activities/{activity_id}/submission
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** Septiembre 2026  
**Estado:** `B3-H13 H1 BLOCKER RESOLVED — READY FOR HUMAN RETEST`

---

## 1. DESCRIPCIÓN DEL INCIDENTE (BLOQUEO H1)

Durante la validación funcional manual de la prueba contractual **H1** (actividad con `delivery_type=TEXT`, título: *"QA B3-H13 H1 — Entrega TEXT"*), el estudiante Samuel Rua (`samuel.rua@colegio.edu.co`) visualizaba correctamente la actividad publicada en su portal, pero al abrir la sección **"Mi Entrega"** el frontend presentaba el mensaje:
> *"An unexpected error occurred. Please try again later."*

La consola y DevTools de red confirmaron:
```http
GET /api/v1/student/activities/c2d84f0c-35e0-4d44-b6a0-3fc203c5ac14/submission
HTTP/1.1 500 Internal Server Error
```

---

## 2. INVESTIGACIÓN PRE-FLIGHT Y CAUSA RAÍZ

### 2.1 Reproducción y Captura del Traceback Real
Se reprodujo la consulta exacta contra la base de datos PostgreSQL de desarrollo bajo el tenant de Samuel Rua (`institution_id: 404c2ebe-478c-45a0-a9a2-453fc7fcecb3`), capturando el siguiente traceback emitido por SQLAlchemy y `asyncpg`:

```text
sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) 
<class 'asyncpg.exceptions.UndefinedColumnError'>: column submission_attachments.updated_at does not exist
HINT: Perhaps you meant to reference the column "submission_attachments.created_at".
[SQL: SELECT 
    submission_attachments.submission_id AS submission_attachments_submission_id, 
    submission_attachments.id AS submission_attachments_id, 
    submission_attachments.institution_id AS submission_attachments_institution_id, 
    submission_attachments.file_path AS submission_attachments_file_path, 
    submission_attachments.original_filename AS submission_attachments_original_filename, 
    submission_attachments.file_size_bytes AS submission_attachments_file_size_bytes, 
    submission_attachments.mime_type AS submission_attachments_mime_type, 
    submission_attachments.created_at AS submission_attachments_created_at, 
    submission_attachments.updated_at AS submission_attachments_updated_at 
FROM submission_attachments 
WHERE submission_attachments.submission_id IN ($1::UUID) 
ORDER BY submission_attachments.created_at]
```

### 2.2 Diagnóstico de la Causa Raíz
* **Archivo afectado:** [`backend/app/models/academic_activity.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/academic_activity.py), línea 605.
* **Componente:** Modelo ORM [`SubmissionAttachment`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/academic_activity.py#L605-L675).
* **Mecanismo del error:**
  1. En PEVN, la clase base declarativa [`Base`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/base_class.py) inyecta automáticamente las columnas de auditoría `created_at` y `updated_at` a todas las entidades hijas.
  2. En la migración oficial [`023_student_submissions_and_attachments.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/versions/023_student_submissions_and_attachments.py), la tabla `submission_attachments` fue diseñada intencionalmente sin la columna `updated_at`, dado que los archivos adjuntos de entrega son evidencias inmutables (se crean o eliminan, nunca se modifican in situ).
  3. Al inicializar o consultar una entrega en [`get_submission_detail`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/student_portal_service.py#L560-L615), SQLAlchemy carga la relación de adjuntos (`selectinload(StudentSubmission.attachments)`).
  4. Dado que el modelo `SubmissionAttachment(Base)` heredaba `updated_at` de `Base` pero la tabla física en PostgreSQL no contenía dicha columna, PostgreSQL rechazaba la consulta con `UndefinedColumnError`, disparando el error HTTP 500.

---

## 3. CORRECCIÓN APLICADA

Se reconcilió el modelo SQLAlchemy con el esquema físico existente de PostgreSQL (creado por la migración 023) **sin requerir una nueva migración de base de datos** (en cumplimiento estricto de la Regla 13):

* En [`backend/app/models/academic_activity.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/academic_activity.py):
  Se declaró explícitamente `updated_at = None` dentro del cuerpo de la clase `SubmissionAttachment`, suprimiendo la columna heredada de `Base`:

```python
class SubmissionAttachment(Base):
    """
    Submission Attachment Entity (Archivo Adjunto a una Entrega de Estudiante).
    """
    ...
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # Submission attachments are immutable upload evidence; migration 023 intentionally does not include updated_at.
    updated_at = None
```

---

## 4. VERIFICACIÓN Y RESULTADOS DE PRUEBAS

### 4.1 Prueba en Vivo contra PostgreSQL y Servidor HTTP
Se ejecutó una petición HTTP directa con el token JWT de Samuel Rua hacia el servidor en desarrollo (`http://localhost:8000`):

```http
GET /api/v1/student/activities/c2d84f0c-35e0-4d44-b6a0-3fc203c5ac14/submission
HTTP/1.1 200 OK
```

**Respuesta recibida:**
```json
{
  "activity_id": "c2d84f0c-35e0-4d44-b6a0-3fc203c5ac14",
  "activity_title": "QA B3-H13 H1 — Entrega TEXT",
  "activity_status": "PUBLISHED",
  "delivery_type": "TEXT",
  "due_date": "2026-09-15T18:53:00Z",
  "can_submit": true,
  "can_edit_draft": true,
  "current_attempt": {
    "id": "d469a934-0911-4cb5-9772-e01142f87544",
    "activity_id": "c2d84f0c-35e0-4d44-b6a0-3fc203c5ac14",
    "student_id": "2b049452-de46-48be-80b1-45291c9387d9",
    "attempt_number": 1,
    "status": "DRAFT",
    "student_response": null,
    "submitted_at": null,
    "is_late": false,
    "return_feedback": null,
    "returned_at": null,
    "attachments": []
  },
  "history": [],
  "grade_score": null,
  "grade_feedback": null,
  "graded_at": null
}
```

### 4.2 Suites de Pruebas Automatizadas
1. **Entregas de Estudiantes (`test_student_submissions_api.py`):**
   - **10/10 PASSED (100%)** en 43.88s.
   - Incluyendo `test_student_fetch_or_create_draft` (cobertura del escenario exacto de primera apertura sin submission previa).
2. **Almacenamiento y Recursos (`test_activity_resources_and_storage.py`):**
   - **5/5 PASSED (100%)** en 11.07s.
3. **Portal Estudiante General (`test_student_portal_api.py`):**
   - **8/8 PASSED (100%)** en 22.77s.
4. **Verificación Estática Frontend (`npx tsc --noEmit`):**
   - **0 errores** (código de salida 0).

---

## 5. CUMPLIMIENTO DE REGLAS INNEGOCIABLES

| Regla | Estado | Observación |
|---|:---:|---|
| No avanzar a H2/H3 | ✅ CUMPLIDO | Foco exclusivo en resolución del HTTP 500 en H1. |
| No modificar contrato funcional B3-H13 | ✅ CUMPLIDO | Contrato y flujo de entrega preservados íntegramente. |
| No cambiar `delivery_type` | ✅ CUMPLIDO | La actividad permanece en `delivery_type=TEXT`. |
| No introducir `StudentSubmission.is_current` | ✅ CUMPLIDO | Intento actual continúa derivado vía `attempt_number`. |
| `ActivityGrade` única fuente de verdad | ✅ CUMPLIDO | No se alteró `ActivityGrade` ni SIEE. |
| No modificar B3-H11 | ✅ CUMPLIDO | Almacenamiento seguro y recursos docentes 100% intactos. |
| Mantener Anti-IDOR y tenant isolation | ✅ CUMPLIDO | Probado y verificado. |
| No eliminar datos QA | ✅ CUMPLIDO | Todos los datos de prueba y seed permanecen intactos. |
| No crear nueva migración sin autorización | ✅ CUMPLIDO | Se reconcilió el modelo ORM con el esquema ya creado por la 023. |

---

## 6. ESTADO FINAL

* **Veredicto:** `B3-H13 H1 BLOCKER RESOLVED — READY FOR HUMAN RETEST`
* La aplicación se encuentra lista en el entorno de desarrollo para que el propietario repita la prueba funcional manual de **H1**.
