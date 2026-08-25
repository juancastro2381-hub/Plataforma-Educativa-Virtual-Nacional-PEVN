# ARQUITECTURA DE LA CAPA DE SERVICIOS DE DOMINIO ACADÉMICO (FASE 3B — PASO 4)
## Plataforma Educativa Virtual Nacional (PEVN)

---

## 1. Visión General y Responsabilidades

La capa de servicios de dominio (`backend/app/services/`) concentra de manera exclusiva, autoritativa y reutilizable toda la lógica de negocio, validación de invariantes, aislamiento multi-tenant y emisión de eventos de auditoría para la gestión académica nacional de Colombia.

```
                      [ CONTROLADORES REST (PASO 5) ]
                                    │
                                    ▼
                 [ CAPA DE SERVICIOS DE DOMINIO (PASO 4) ]
   ┌──────────────────────────────────────────────────────────────────┐
   │ • AcademicYearService         • GroupService                     │
   │ • StudentService              • TeacherService                   │
   │ • GuardianService             • EnrollmentService                │
   │ • TransferService             • AcademicAssignmentService        │
   └───────────────┬──────────────────────────────────┬───────────────┘
                   │                                  │
                   ▼                                  ▼
        [ PostgreSQL & Modelos ORM ]       [ DatabaseAuditService ]
```

---

## 2. Catálogo de Servicios de Dominio Implementados

### 2.1 `AcademicYearService`
- **Responsabilidad:** Ciclo de vida de años lectivos institucionales (`PLANNING` $\rightarrow$ `ACTIVE` $\rightarrow$ `CLOSED`).
- **Invariantes:**
  - `start_date < end_date`.
  - Unicidad de año por institución (`institution_id`, `year`).
  - No sobrescritura silenciosa: se rechaza activar un año si ya existe otro activo sin cerrar.
- **Excepciones:** `AcademicYearNotFoundError`, `AcademicYearLifecycleError`, `AcademicDomainError`.

### 2.2 `GroupService`
- **Responsabilidad:** Creación, configuración de cupos y dirección de salones de clase.
- **Invariantes:**
  - `capacity_limit > 0`.
  - Unicidad de grupo en la sede (`campus_id`, `academic_year_id`, `grade_id`, `name`).
  - Aislamiento tenant: la sede, el año lectivo y el docente director deben pertenecer estrictamente a la misma institución.
- **Excepciones:** `GroupNotFoundError`, `CrossTenantMismatchError`, `AcademicDomainError`.

### 2.3 `StudentService`
- **Responsabilidad:** Perfil del estudiante, código nacional SIMAT y datos de inclusión social.
- **Invariantes:**
  - Relación 1:1 estricta con `User` sin duplicar credenciales de autenticación.
  - Unicidad de `code_simat` en todo el sistema.
  - Validación de estrato socioeconómico ($1 \le \text{estrato} \le 6$).
- **Excepciones:** `StudentNotFoundError`, `CrossTenantMismatchError`, `AcademicDomainError`.

### 2.4 `TeacherService`
- **Responsabilidad:** Perfil profesional docente, escalafón y validación de aptitud académica.
- **Invariantes:**
  - Relación 1:1 estricta con `User` institucional.
  - Validación de estado activo en la cuenta de usuario.
- **Excepciones:** `TeacherNotFoundError`, `CrossTenantMismatchError`, `AcademicDomainError`.

### 2.5 `GuardianService`
- **Responsabilidad:** Gestión de acudientes y parentescos conforme a la decisión `[OPEN-DECISION-3A-01]`.
- **Invariantes:**
  - Desacoplamiento de identidad: correo y cuenta `User` son opcionales para acudientes rurales o sin conectividad.
  - Unicidad por documento nacional (`document_type`, `document_number`).
  - Unicidad de asociación estudiante-acudiente (`student_id`, `guardian_id`).
- **Excepciones:** `GuardianNotFoundError`, `StudentNotFoundError`, `AcademicDomainError`.

### 2.6 `EnrollmentService`
- **Responsabilidad:** Matrícula regular, prematrícula, retiro y graduación de estudiantes.
- **Invariantes:**
  - Invariante obligatoria de matrícula única activa por estudiante en el año escolar (`StudentAlreadyEnrolledActiveError`).
  - Protección de cupos con bloqueo de fila (`SELECT ... FOR UPDATE` sobre `groups`).
  - Inmutabilidad histórica: los retiros o traslados preservan el registro de matrícula original.
- **Excepciones:** `StudentAlreadyEnrolledActiveError`, `GroupCapacityExceededError`, `EnrollmentNotFoundError`, `CrossTenantMismatchError`.

### 2.7 `TransferService`
- **Responsabilidad:** Transacción atómica de traslados de grupo y generación de historial inmutable.
- **Invariantes:**
  - Solo matrículas en estado `ACTIVE` pueden trasladarse.
  - El grupo destino debe pertenecer al mismo año lectivo y a la misma institución.
  - Bloqueo transaccional de fila (`SELECT ... FOR UPDATE`) en el grupo destino para garantizar disponibilidad de cupos.
  - Creación de registro inmutable en `group_transfer_history`.
- **Excepciones:** `InvalidTransferError`, `GroupCapacityExceededError`, `CrossTenantMismatchError`.

### 2.8 `AcademicAssignmentService`
- **Responsabilidad:** Carga académica docente por materia y grupo en el año lectivo.
- **Invariantes:**
  - Invariante de docente titular activo único por `(subject_id, group_id, academic_year_id)` (`DuplicateActiveAssignmentError`).
  - Sustitución docente atómica: desactiva la asignación previa (`is_active = False`) y genera la nueva asignación activa conservando el histórico.
- **Excepciones:** `DuplicateActiveAssignmentError`, `TeacherNotFoundError`, `CrossTenantMismatchError`.

---

## 3. Estrategia de Concurrencia y Bloqueo de Fila

Para prevenir condiciones de carrera (*race conditions*) en inscripciones o traslados simultáneos hacia salones con cupos limitados, los servicios `EnrollmentService` y `TransferService` aplican bloqueo pesimista en PostgreSQL:

```python
group_stmt = (
    select(Group)
    .join(Campus, Group.campus_id == Campus.id)
    .where(
        Group.id == group_id,
        Campus.institution_id == institution_id,
    )
    .with_for_update()
)
```

Cualquier transacción concurrente espera a la liberación del bloqueo de la fila del grupo antes de evaluar la capacidad disponible.

---

## 4. Integración Centralizada de Auditoría

Todos los servicios emiten eventos de auditoría inmutables usando el servicio institucional existente `DatabaseAuditService`:

- `ACADEMIC_YEAR_CREATED`, `ACADEMIC_YEAR_ACTIVATED`, `ACADEMIC_YEAR_CLOSED`
- `GROUP_CREATED`, `GROUP_UPDATED`, `GROUP_DIRECTOR_ASSIGNED`
- `STUDENT_CREATED`, `STUDENT_UPDATED`
- `TEACHER_CREATED`, `TEACHER_UPDATED`
- `GUARDIAN_CREATED`, `GUARDIAN_ASSOCIATED`
- `ENROLLMENT_CREATED`, `ENROLLMENT_ACTIVATED`, `ENROLLMENT_WITHDRAWN`, `ENROLLMENT_TRANSFERRED`, `ENROLLMENT_GRADUATED`
- `ACADEMIC_ASSIGNMENT_CREATED`, `ACADEMIC_ASSIGNMENT_REPLACED`, `ACADEMIC_ASSIGNMENT_DEACTIVATED`
