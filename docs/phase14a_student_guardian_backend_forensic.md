# PEVN — INFORME DE ARQUITECTURA Y FORENSE DE IMPLEMENTACIÓN: FASE 14A
## Servicios de Aplicación y Endpoints Backend para los Portales de Estudiante y Acudiente
**Fecha de Certificación:** 2026-09-01  
**Estado:** IMPLEMENTACIÓN COMPLETADA Y 100% CERTIFICADA  
**Ambiente:** Multi-Tenant Anti-IDOR / FastAPI / SQLAlchemy Async / Pytest  

---

### 1. Resumen Ejecutivo de la Fase 14A

La Fase 14A implementa la infraestructura backend completa para los dos portales clave de actores educativos de la Plataforma Educativa Virtual Nacional (PEVN):
1. **Portal del Estudiante (`/api/v1/student`):** Acceso auto-contenido a la vida académica del alumno autenticado (perfil, asignaturas, actividades, calificaciones, asistencia, aulas virtuales y grabaciones).
2. **Portal del Acudiente (`/api/v1/guardian`):** Supervisión y acompañamiento parental multi-hijo con selector dinámico de tutorados y autorización centralizada de relación acudiente-estudiante.

| Parámetro | Métrica / Resultado |
| :--- | :--- |
| **Cambios de Esquema / Tablas Nuevas** | **0 (Cero)** — Cero alteraciones de base de datos |
| **Migraciones de Base de Datos** | **0 (Cero)** — Reutilización 100% de entidades canónicas existentes |
| **Servicios de Aplicación Creados** | `StudentPortalService`, `GuardianPortalService` |
| **Modelos Pydantic Creados** | `StudentProfileResponse`, `StudentDashboardSummaryResponse`, `StudentSubjectItemResponse`, `StudentActivityItemResponse`, `StudentGradeReportResponse`, `StudentAttendanceSummaryResponse`, `StudentVirtualClassroomItemResponse`, `StudentRecordingsListResponse`, `GuardianProfileResponse`, `GuardianStudentItemResponse`, `GuardianChildOverviewResponse`, `GuardianChildActivityItemResponse`, `GuardianChildGradesResponse`, `GuardianChildAttendanceResponse`, etc. |
| **Endpoints REST Implementados** | **18 endpoints** (10 Student, 8 Guardian) |
| **Nuevas Pruebas de Integración** | **17 tests** (8 Student, 9 Guardian) |
| **Total de Pruebas Backend Ejecutadas** | **366 / 366 PASSED (100% Éxito)** |

---

### 2. Archivos Inspeccionados y Reutilizados

- `backend/app/models/student.py`: Entidad `Student` con vínculo 1:1 estricto con `User` (`user_id NOT NULL UNIQUE`) y pertenencia institucional `institution_id`.
- `backend/app/models/guardian.py`: Entidad `Guardian` con vínculo opcional `0..1` con `User` (`user_id NULLABLE UNIQUE`) e `institution_id NOT NULL` con restricción multi-tenant blindada en Fase 13E.4.
- `backend/app/models/guardian.py`: Entidad de enlace `StudentGuardian` ($M:N$) con atributos `relationship_type`, `is_primary_contact`, `is_authorized_pickup`.
- `backend/app/models/enrollment.py`: Matrículas activas `Enrollment` con asociación a `AcademicYear` y `Group`.
- `backend/app/models/academic_activity.py`: Actividades académicas `AcademicActivity`, calificaciones `ActivityGrade` y control de asistencia `DailyAttendance`.
- `backend/app/models/virtual_classroom.py`: Aulas virtuales `VirtualClassroom` y grabaciones `MeetingRecording`.
- `backend/app/models/grade.py` y `backend/app/models/subject.py`: Catálogo curricular nacional estándar.
- `backend/app/core/security/rbac_service.py` y `tokens.py`: Control de acceso basado en roles (RBAC) y tokens JWT.

---

### 3. Servicios de Aplicación Implementados

#### A. `StudentPortalService` (`backend/app/services/student_portal_service.py`)
- **Derivación de Identidad del Alumno:**  
  `get_student_by_user_id(user_id, institution_id)` consulta al alumno a partir de `current_user.id`. El cliente **nunca** envía `student_id`.
- **Resolución de Matrícula Activa:**  
  Resuelve el grupo, grado, sede y año lectivo vigente del estudiante con estado `ACTIVE`.
- **Cálculo Dinámico de Estado de Actividades:**  
  Deriva en tiempo real el estado de entrega y cumplimiento de tareas: `PENDING`, `OVERDUE` (si fecha límite vencida), `SUBMITTED` o `GRADED`.
- **Protección Anti-IDOR en Actividades y Clases Virtuales:**  
  Verifica que la actividad o el aula virtual pertenezca inequívocamente al grupo y año escolar donde el alumno está formalmente matriculado.

#### B. `GuardianPortalService` (`backend/app/services/guardian_portal_service.py`)
- **Derivación de Identidad del Acudiente:**  
  `get_guardian_by_user_id(user_id, institution_id)` recupera el registro institucional del acudiente.
- **Frontera de Autorización Centralizada (`authorize_student_access`):**  
  Verifica que el acudiente y el estudiante pertenezcan a la misma institución (`Student.institution_id == guardian.institution_id`) y que exista un vínculo activo en la tabla de enlace `student_guardians`.
- **Política Anti-IDOR y Anti-Enumeración:**  
  Si el estudiante solicitado no existe, pertenece a otra institución (cross-tenant), o no está legalmente vinculado al acudiente, el servicio levanta un error unificado `NotFoundError` que genera **`HTTP 404 Not Found`**, impidiendo que atacantes deduzcan la existencia de registros ajenos.
- **Modo de Acompañamiento Parental:**  
  El portal del acudiente es de monitoreo y seguimiento formativo; no permite el envío de entregas de actividades ni funciones de moderador en sesiones de clase.

---

### 4. Endpoints REST Implementados

#### Portal del Estudiante (`/api/v1/student`)
| Método | Ruta | Permiso RBAC | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/student/profile` | `students:read` | Perfil del alumno, datos de matrícula, sede, grado y grupo. |
| `GET` | `/api/v1/student/dashboard` | `students:read` | Resumen de métricas: asignaturas, tareas pendientes/vencidas, promedio acumulado, tasa de asistencia y próximas clases. |
| `GET` | `/api/v1/student/subjects` | `subjects:read` | Lista de asignaturas matriculadas con datos de docentes y ponderaciones. |
| `GET` | `/api/v1/student/activities` | `activities:read` | Bandeja de tareas y evaluaciones con filtros de estado (`PENDING`, `OVERDUE`, `SUBMITTED`, `GRADED`). |
| `GET` | `/api/v1/student/activities/{activity_id}` | `activities:read` | Detalle, instrucciones, enlaces y calificación de una actividad específica (Anti-IDOR). |
| `GET` | `/api/v1/student/grades` | `grades:read` | Libreta de calificaciones desglosada por asignatura y periodo académico. |
| `GET` | `/api/v1/student/attendance` | `attendance:read` | Resumen porcentual e historial detallado de asistencias y ausencias. |
| `GET` | `/api/v1/student/virtual-classrooms` | `virtual_classrooms:read` | Aulas virtuales programadas y activas del grupo del alumno. |
| `GET` | `/api/v1/student/virtual-classrooms/{classroom_id}` | `virtual_classrooms:read` | Información autorizada de ingreso a la sesión de videoconferencia (Anti-IDOR). |
| `GET` | `/api/v1/student/virtual-classrooms/{classroom_id}/recordings` | `recordings:read` | Grabaciones publicadas de las clases autorizadas. |

#### Portal del Acudiente (`/api/v1/guardian`)
| Método | Ruta | Permiso RBAC | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/guardian/profile` | `guardians:read` | Perfil del acudiente autenticado. |
| `GET` | `/api/v1/guardian/students` | `guardians:read` | Lista de estudiantes tutorados para el selector familiar de hijos. |
| `GET` | `/api/v1/guardian/students/{student_id}/overview` | `guardians:read` | Ficha resumen del hijo seleccionado (promedio, tareas pendientes, asistencia). |
| `GET` | `/api/v1/guardian/students/{student_id}/activities` | `activities:read` | Seguimiento de deberes y actividades del hijo seleccionado. |
| `GET` | `/api/v1/guardian/students/{student_id}/grades` | `grades:read` | Informe de notas y retroalimentaciones pedagógicas del hijo. |
| `GET` | `/api/v1/guardian/students/{student_id}/attendance` | `attendance:read` | Registro de asistencia y ausencias del tutorado. |
| `GET` | `/api/v1/guardian/students/{student_id}/virtual-classrooms` | `virtual_classrooms:read` | Cronograma de clases virtuales del tutorado. |
| `GET` | `/api/v1/guardian/students/{student_id}/virtual-classrooms/{classroom_id}` | `virtual_classrooms:read` | Detalle de la clase virtual del hijo. |

---

### 5. Matrices de Acceso y Seguridad

#### Matriz de Acceso del Estudiante
```
[Token Alumno] -> current_user.id -> Student (institution_id)
                      |
                      v
             Active Enrollment (Group, AcademicYear)
                      |
        +-------------+-------------+-------------+
        |             |             |             |
        v             v             v             v
    Subjects      Activities     Grades       Attendance & Aulas
  (mismo grupo)  (mismo grupo) (mismo alumno)   (mismo grupo)
```

#### Matriz de Acceso del Acudiente
```
[Token Acudiente] -> current_user.id -> Guardian (institution_id)
                                             |
                                  +----------v----------+
                                  | StudentGuardian M:N |
                                  +----------+----------+
                                             |
                   [student_id pertenece a su institución Y está vinculado?]
                                  /                     \
                             SÍ /                         \ NO
                               v                           v
                 Acceso de Lectura Autorizado          HTTP 404 Not Found
                 (Overview, Notas, Asistencia)         (Anti-Enumeration)
```

---

### 6. Pruebas Automatizadas y Resultados

Se implementaron dos suites de pruebas integrales con cobertura exhaustiva de casos de uso y vectores de ataque:

1. **`backend/tests/test_student_portal_api.py` (8 pruebas):**
   - `test_student_get_profile`: Verificación de datos de perfil, grupo, grado y sede.
   - `test_student_get_dashboard`: Verificación de cálculo de tareas pendientes, vencidas, promedio y asistencias.
   - `test_student_list_subjects`: Asignaturas del grupo del alumno.
   - `test_student_list_activities_and_status`: Derivación de estados `PENDING`, `SUBMITTED`, `GRADED`.
   - `test_student_activity_detail_and_anti_idor`: Validación de consulta autorizada y rechazo `404` para actividades de otro grupo.
   - `test_student_grades_isolation`: Comprobación de que el estudiante sólo ve sus propias notas.
   - `test_student_attendance_history`: Registro de asistencia personal.
   - `test_student_virtual_classrooms_and_recordings`: Listado de aulas y grabaciones autorizadas.

2. **`backend/tests/test_guardian_portal_api.py` (9 pruebas):**
   - `test_guardian_get_profile`: Perfil del acudiente.
   - `test_guardian_list_students_child_switcher`: Listado correcto de hijos para el selector de estudiantes.
   - `test_guardian_get_child_overview`: Métricas consolidadas del hijo seleccionado.
   - `test_guardian_list_child_activities_follow_up`: Monitoreo de tareas del hijo.
   - `test_guardian_list_child_grades`: Calificaciones del hijo.
   - `test_guardian_list_child_attendance`: Registro de asistencias y fallas del hijo.
   - `test_guardian_list_child_virtual_classrooms`: Clases virtuales del hijo.
   - `test_guardian_cannot_access_unlinked_child_anti_idor`: **Anti-IDOR intra-tenant**: Un acudiente que intenta acceder a un estudiante de su misma institución pero sin relación de parentesco recibe `HTTP 404`.
   - `test_guardian_cannot_access_cross_tenant_student_anti_idor`: **Anti-IDOR cross-tenant**: Un acudiente que intenta acceder a un estudiante de otra institución recibe `HTTP 404`.

#### Resultado de la Suite de Regresión Completa:
```
================= 366 passed, 8 warnings in 339.37s (0:05:39) =================
```

---

### 7. Evaluación de Preparación para Fase 14B

- **Backend Readiness:** 100% de los endpoints requeridos por el Portal del Estudiante (`/api/v1/student`) y el Portal del Acudiente (`/api/v1/guardian`) están activos, documentados con OpenAPI / Swagger y protegidos con pruebas automatizadas.
- **Fase Siguiente:** **Fase 14B — Student Portal Frontend Implementation** (`/student`).
- **Separación de Responsabilidades:** No se construyó interfaz de usuario en esta fase; el frontend consumirá de manera limpia las APIs aquí implementadas.
