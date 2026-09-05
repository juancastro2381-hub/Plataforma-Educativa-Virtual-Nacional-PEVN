# PEVN — Arquitectura Funcional y Auditoría Forense: Fase 13G
## Portales de Autoservicio para Estudiantes y Acudientes (Student Portal & Guardian Portal)

---

### 1. Resumen Ejecutivo

| Parámetro | Detalle |
| :--- | :--- |
| **Fase** | **13G — Student & Guardian Portal Forensic + Functional Architecture** |
| **Fecha de Elaboración** | 2026-09-01 |
| **Naturaleza de la Fase** | **ANÁLISIS + DISEÑO ARQUITECTÓNICO CANÓNICO (0 Mutaciones de Código/BD)** |
| **Objetivo Principal** | Diseñar la arquitectura funcional, de seguridad multi-tenant, flujos de datos y contratos de servicio para el **Portal del Estudiante** y el **Portal del Acudiente**, maximizando la reutilización de los modelos existentes (`AcademicActivity`, `ActivityGrade`, `DailyAttendance`, `VirtualClassroom`, `StudentGuardian`). |
| **Estado de Base de Datos** | Modelos académicos, calificaciones, asistencia y aulas virtuales ya implementados; modelos de Comunicaciones, Noticias y Convivencia Escolar / Incidencias catalogados como requerimientos pendientes. |

---

### 2. Arquitectura Existente y Fuentes Canónicas de Verdad

```
                           ┌───────────────────────────────┐
                           │      Institución (Tenant)     │
                           └───────────────┬───────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│   Docente / Aula │             │ Estudiante / SIMAT│             │    Acudiente     │
│(AcademicActivity,│             │ (Student, User,  │             │ (Guardian, User, │
│ DailyAttendance, │             │   Enrollment)    │             │ StudentGuardian) │
│ VirtualClassroom)│             └─────────┬────────┘             └─────────┬────────┘
└────────┬─────────┘                       │                                │
         │                                 │                                │
         └────────────────────────► ◄──────┴────────────────────────────────┘
                                  Relación Pedagógica
                                (ActivityGrade, Attendance)
```

---

### 3. Matriz de Capacidades: Existentes vs. Faltantes

| Capacidad | Ya Existe | Parcialmente | Faltante | Componente / API Reutilizable | Notas de Auditoría |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Autenticación Alumno** | | **X** | | `POST /api/v1/auth/login` | Requiere mecanismo de primer login / cambio forzoso de clave. |
| **Autenticación Acudiente** | **X** | | | `GuardianOnboardingService` | Token de activación con código SIMAT validado. |
| **Portal Estudiante (GUI)** | | | **X** | Rutas `/student` | Pendiente de construcción frontend. |
| **Portal Acudiente (GUI)** | | | **X** | Rutas `/guardian` | Pendiente de construcción frontend. |
| **Dashboard Estudiante** | | | **X** | Nuevo `/student/dashboard` | Resumen de materias, tareas y clases virtuales. |
| **Dashboard Acudiente** | | **X** | | `Dashboard.tsx` (Tarjeta) | Requiere selector dinámico de hijos/tutorados. |
| **Tareas / Actividades** | **X** | | | `academic_activities` | Modelo completo (`TASK`, `WORKSHOP`, `EXAM`, etc.). |
| **Calificaciones / Notas** | **X** | | | `activity_grades` | Escala 0.0 - 5.0 con feedback pedagógico. |
| **Asistencia Escolar** | **X** | | | `daily_attendances` | Estados: `PRESENT`, `ABSENT`, `EXCUSED`, `LATE`. |
| **Aulas Virtuales en Vivo** | **X** | | | `virtual_classrooms` | Sesiones WebRTC/Jitsi con control de rol. |
| **Grabaciones de Clases** | **X** | | | `meeting_recordings` | Acceso a clases grabadas de sus grupos. |
| **Comunicaciones / Circulares** | | | **X** | Nuevo módulo | Requiere modelo de comunicados institucionales. |
| **Noticias Institucionales** | | | **X** | Nuevo módulo | Noticias generales diferenciadas de circulares. |
| **Observador / Incidencias** | | | **X** | Nuevo módulo | Registro de convivencia escolar acotado a la familia. |
| **Vínculo Estudiante-Acudiente** | **X** | | | `student_guardians` | Soporta múltiples acudientes y múltiples alumnos. |

---

### 4. Arquitectura Funcional: Portal del Estudiante (`/student`)

El lema operativo del estudiante es: **"Aprender, Asistir y Cumplir"**.

```
Portal del Estudiante (/student)
├── 🏠 Inicio (Dashboard)
│    ├── Resumen del Año Lectivo y Grupo Matriculado
│    ├── Próximas Clases Virtuales Hoy
│    ├── Tareas Pendientes con Alerta de Vencimiento
│    └── Últimas Calificaciones y Observaciones Docentes
├── 📚 Mis Asignaturas
│    ├── Lista de Materias (Docente, Horas Semanales, Plan de Estudios)
│    └── Planilla de Calificaciones por Período Académico
├── 📝 Mis Tareas y Entregas
│    ├── Pendientes / Por Entregar (Instrucciones, Recursos, Fecha Límite)
│    ├── Entregadas / En Revisión
│    └── Calificadas (Nota Obtenida y Retroalimentación del Docente)
├── 📹 Clases Virtuales
│    ├── Clases en Vivo Programadas (Botón "Ingresar a Clase")
│    └── Repositorio de Clases Grabadas
├── 📋 Mi Asistencia
│    └── Historial de Asistencias, Inasistencias y Justificaciones
└── 📢 Circulares y Avisos
     └── Comunicaciones Oficiales de la Institución
```

---

### 5. Arquitectura Funcional: Portal del Acudiente / Familia (`/guardian`)

El lema operativo del acudiente es: **"Acompañar, Monitorear y Comunicar"**.

```
Portal del Acudiente (/guardian)
├── 👨‍👩‍👧‍👦 Selector de Tutorados (Context Switcher: Hijo A, Hijo B)
│    └── Encabezado con foto, grado, grupo y sede del estudiante activo
├── 📊 Seguimiento Académico
│    ├── Desempeño en Tiempo Real por Asignatura
│    ├── Promedio Ponderado y Semáforo de Riesgo Académico
│    └── Observaciones y Recomendaciones de los Docentes
├── 📝 Tareas y Deberes Escolares (MODO SEGUIMIENTO)
│    ├── Tareas Pendientes del Alumno (Ver qué debe hacer en casa)
│    ├── Tareas Vencidas o No Entregadas (Alerta preventiva)
│    └── Tareas Calificadas (Ver notas y comentarios del docente)
│    *(Nota: El acudiente no suplanta al alumno en la entrega de tareas)*
├── 📋 Control de Asistencia y Puntualidad
│    ├── Reporte Diario de Asistencia (Fallas injustificadas)
│    └── Radicación / Notificación de Excusas Médicas
├── 📹 Horario y Clases Virtuales
│    └── Cronograma de Aulas Virtuales programadas para sus hijos
└── 📬 Circulares, Citaciones y Convivencia
     ├── Circulares Oficiales y Confirmación de Lectura
     ├── Citaciones a Reuniones de Padres / Entrega de Informes
     └── Observador del Alumno (Anotaciones de convivencia escolar)
```

---

### 6. Modelo de Tareas, Deberes y Calificaciones

La entidad `AcademicActivity` y su relación con `ActivityGrade` son la base técnica:

1. **Creación por el Docente:**  
   El docente publica una actividad para su grupo y materia con fecha límite (`due_date`), puntaje máximo (`max_score=5.0`), tipo (`TASK`, `WORKSHOP`, `EXAM`) e instrucciones.
2. **Visualización del Estudiante:**  
   El endpoint `/api/v1/student/activities` consulta las actividades publicadas para los grupos donde el alumno tiene matrícula activa (`EnrollmentStatus.ACTIVE`).
3. **Monitoreo del Acudiente:**  
   El endpoint `/api/v1/guardian/students/{student_id}/activities` valida la relación en `student_guardians` y presenta el estado de cumplimiento:
   - `PENDING`: Tarea no entregada dentro del plazo.
   - `OVERDUE`: Tarea vencida sin entrega.
   - `SUBMITTED`: Tarea entregada, esperando revisión.
   - `GRADED`: Tarea calificada con nota y retroalimentación docente.

---

### 7. Modelo de Clases Virtuales y Grabaciones

1. **Frontera de Acceso:**  
   Las clases virtuales (`VirtualClassroom`) vinculadas a una `AcademicAssignment` se filtran para los alumnos matriculados en dicho grupo.
2. **Rol en la Sala:**  
   - Docente: `MODERATOR` (control de micrófono, pantalla y grabación).
   - Estudiante: `VIEWER` (participante con cámara/micrófono controlado).
   - Acudiente: Acceso a la agenda y cronograma de sesiones (modo espectador/acompañamiento si la institución lo habilita).

---

### 8. Seguridad Multi-Tenant y Anti-IDOR

#### Reglas Inviolables de Frontera:

```
[Usuario Autenticado]
       │
       ├── Es STUDENT ──► student.user_id == current_user.id
       │                  AND student.institution_id == current_user.institution_id
       │                  (Acceso EXCLUSIVO a sus propios datos)
       │
       └── Es GUARDIAN ──► guardian.user_id == current_user.id
                          AND EXISTS (
                              SELECT 1 FROM student_guardians sg
                              JOIN students s ON s.id = sg.student_id
                              WHERE sg.guardian_id = guardian.id
                              AND sg.student_id = :target_student_id
                              AND s.institution_id == current_user.institution_id
                          )
                          (Acceso EXCLUSIVO a sus hijos/tutorados autorizados)
```

1. **Protección Anti-IDOR en Estudiantes:**  
   Ningún endpoint del portal de estudiantes aceptará `student_id` como parámetro de ruta o query. El backend derivará siempre el `student_id` directamente a partir de `current_user.id` mediante la relación `1:1`.
2. **Protección Anti-IDOR en Acudientes:**  
   Cuando un acudiente consulte `/api/v1/guardian/students/{student_id}/...`, el servicio verificará obligatoriamente la existencia de un registro activo en `student_guardians` que vincule al acudiente autenticado con el `student_id` solicitado dentro del mismo `institution_id`. Cualquier discrepancia retornará `HTTP 404 Not Found`.

---

### 9. Matriz Formal de Roles y Permisos (RBAC)

| Módulo / Capacidad | SUPERADMIN | RECTOR | COORDINADOR | DOCENTE | ESTUDIANTE | ACUDIENTE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Carga / Asignaciones** | MANAGE | MANAGE | MANAGE | VIEW (Propia) | VIEW (Grupo) | VIEW (Hijo) |
| **Crear Tareas** | MANAGE | VIEW | VIEW | CREATE/UPDATE | - | - |
| **Ver Tareas / Deberes** | VIEW | VIEW | VIEW | VIEW | VIEW (Grupo) | VIEW (Hijo) |
| **Entregar Tareas** | - | - | - | - | SUBMIT | - |
| **Calificar Tareas** | - | - | - | GRADE | - | - |
| **Ver Calificaciones** | VIEW | VIEW | VIEW | VIEW/GRADE | VIEW (Propias)| VIEW (Hijo) |
| **Tomar Asistencia** | - | VIEW | VIEW | CREATE/UPDATE | - | - |
| **Ver Asistencia** | VIEW | VIEW | VIEW | VIEW | VIEW (Propia) | VIEW (Hijo) |
| **Aulas Virtuales** | MANAGE | MANAGE | MANAGE | MODERATOR | VIEWER/JOIN | VIEW Agenda |
| **Circulares Institucionales**| MANAGE | PUBLISH | PUBLISH | VIEW | VIEW | VIEW/CONFIRM |
| **Noticias del Colegio** | MANAGE | PUBLISH | PUBLISH | VIEW | VIEW | VIEW |
| **Observador / Convivencia** | MANAGE | MANAGE | MANAGE | CREATE/VIEW | VIEW (Propio) | VIEW (Hijo) |

---

### 10. Flujos de Datos Canónicos

#### Flujo 1: Ciclo de Vida de Tarea Escolar
```
1. Docente publica tarea (AcademicActivity) para Grupo 6-A
      │
      ├──► 2. Estudiante 6-A recibe notificación en su Dashboard
      │         │
      │         └──► 3. Estudiante consulta instrucciones y recursos
      │                   │
      │                   └──► 4. Estudiante marca/envía entrega
      │
      ├──► 5. Acudiente ve en su Portal: "Tarea pendiente de Ciencias (Entrega: Viernes)"
      │
      └──► 6. Docente califica en Planilla (ActivityGrade)
                │
                ├──► 7. Estudiante ve su nota y comentarios
                └──► 8. Acudiente ve la calificación y desempeño en su reporte
```

#### Flujo 2: Consulta del Acudiente con Múltiples Hijos
```
1. Acudiente inicia sesión con su cuenta única
      │
      ├──► 2. Backend consulta StudentGuardian vinculados al Guardian
      │
      ├──► 3. Frontend despliega selector: [Hijo A - Grado 3°] [Hijo B - Grado 8°]
      │
      └──► 4. Al seleccionar Hijo B:
                Backend autoriza y entrega notas, asistencia y tareas de Hijo B
```

---

### 11. Decisiones Arquitectónicas Canónicas

1. **Rutas Dedicadas en Frontend:**  
   - Portal Estudiante: `/student` (con sub-rutas `/student/activities`, `/student/grades`, `/student/attendance`, `/student/virtual-classrooms`).
   - Portal Acudiente: `/guardian` (con sub-rutas `/guardian/students/:id/overview`, `/guardian/students/:id/tasks`, `/guardian/students/:id/grades`, `/guardian/students/:id/attendance`).
2. **Desacoplamiento de Servicios:**  
   - Crear `StudentPortalService` y `GuardianPortalService` como servicios de aplicación especializados, consumiendo las entidades existentes `AcademicActivity`, `ActivityGrade`, `DailyAttendance`, `VirtualClassroom` sin duplicar lógica ni crear modelos paralelos.
3. **Módulos Faltantes (Comunicaciones, Noticias, Observador):**  
   - Diseñar esquemas dedicados para `InstitutionalAnnouncement`, `SchoolNews` y `StudentDisciplinaryRecord` en fases posteriores, garantizando aislamiento estricto por `institution_id`.
4. **Experiencia de Usuario PWA y Baja Conectividad:**  
   - Diseño Mobile-First con tipografía clara (Outfit/Inter), badges de estado de alto contraste (Verde = Al día, Amarillo = Pendiente, Rojo = Vencido/Falla), y soporte offline mediante Service Workers para consulta de boletines y horarios cacheados.

---

### 12. Secuencia Recomendada de Implementación

```
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14A: Backend Student & Guardian Portal Services & Endpoints       │
│ (Endpoints /api/v1/student/... y /api/v1/guardian/...)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14B: Frontend Student Portal (/student)                           │
│ (Dashboard, Mis Clases, Mis Tareas, Calificaciones, Aulas Virtuales)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14C: Frontend Guardian Portal (/guardian)                         │
│ (Selector de Tutorados, Seguimiento de Deberes, Asistencia, Boletines) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 15: Comunicaciones, Noticias y Observador de Convivencia          │
│ (Circulares, Citaciones, Anotaciones del Observador)                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 13. Veredicto Final de Preparación

**LISTO PARA ARQUITECTURA DE IMPLEMENTACIÓN (FASE 14).**

El sistema cuenta con todos los cimientos estructurales necesarios en el modelo de base de datos para habilitar el Portal del Estudiante y el Portal del Acudiente de forma segura, limpia y sin deuda técnica.
