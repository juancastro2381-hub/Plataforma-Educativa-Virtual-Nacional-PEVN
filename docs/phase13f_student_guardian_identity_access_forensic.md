# PEVN — Informe Forense de Auditoría: Fase 13F
## Arquitectura de Identidad, Acceso y Aprovisionamiento para Estudiantes y Acudientes

---

### 1. Resumen Ejecutivo

| Métrica | Estado |
| :--- | :--- |
| **Fase** | **13F — Student & Guardian Identity / Access Forensic Audit** |
| **Fecha de Auditoría** | 2026-09-01 |
| **Objetivo** | Auditoría forense exhaustiva de la identidad, autenticación, autorización, aprovisionamiento y aislamiento multi-tenant para **Estudiantes** y **Acudientes / Guardians**. |
| **Modificaciones de Código / Esquema** | **0 Cambios / 0 Migraciones / 0 Mutaciones de Base de Datos** (Fase de descubrimiento puro). |
| **Veredicto Final** | **B. REQUIRES ARCHITECTURAL DECISIONS + C. EXISTING IMPLEMENTATION CAN BE EXTENDED** |

#### Síntesis del Hallazgo Principal:
1. **Estudiantes:** El modelo de datos ya asocia obligatoriamente cada `Student` de forma 1:1 con una cuenta `User` central (`user_id NOT NULL UNIQUE`), con rol institucional `student` y `institution_id`. Sin embargo, al crearse un estudiante, la contraseña inicial se genera de forma aleatoria en memoria sin mecanismo de entrega/activación para el alumno, y no existen endpoints ni vistas dedicadas de **Portal del Estudiante** (`/student`).
2. **Acudientes:** El modelo de datos mantiene desacoplada la ficha civil del acudiente (`Guardian`) de la cuenta de usuario (`user_id` es `NULLABLE`), respetando la compatibilidad rural/offline (`[OPEN-DECISION-3A-01]`). Existe un servicio robusto de auto-activación tokenizada (`GuardianOnboardingService` en `/api/v1/auth/guardians/...`), pero tras iniciar sesión no existen rutas, endpoints ni vistas de **Portal del Acudiente** para consultar las calificaciones, asistencia o actividades de sus tutorados.

---

### 2. Arquitectura Actual de Identidad

La plataforma PEVN opera bajo un modelo de **Identidad Central (`User`)** complementado por **Perfiles de Dominio Especializados** y **Control de Acceso Basado en Roles con Alcance Organizacional (RBAC + Scope)**.

```
                  ┌────────────────────────────────────────┐
                  │                 User                   │
                  │  (Email, Username, Password Argon2id, │
                  │   Documento, institution_id, Security) │
                  └───────┬──────────────────────┬─────────┘
                          │ 1:1                  │ 0..1 (Opcional)
                          ▼                      ▼
               ┌─────────────────────┐ ┌─────────────────────┐
               │       Student       │ │      Guardian       │
               │ (code_simat, birth, │ │(Documento, Teléfono,│
               │  institution_id)    │ │ institution_id)     │
               └──────────┬──────────┘ └──────────┬──────────┘
                          │                       │
                          └───────────┬───────────┘
                                      │ M:N
                                      ▼
                          ┌───────────────────────┐
                          │    StudentGuardian    │
                          │(relationship, primary,│
                          │   authorized_pickup)  │
                          └───────────────────────┘
```

---

### 3. Hallazgos Forenses: Dominio de Estudiantes (`Student`)

1. **Pertenencia Institucional (`institution_id`):**  
   - `Student.institution_id` es `Mapped[uuid.UUID]` obligatorio (`NOT NULL`), indexado y con clave foránea `institutions.id (ON DELETE RESTRICT)`.
   - Representa de manera inequívoca la frontera del tenant institucional.
2. **Identidad / Cuenta de Usuario (`user_id`):**  
   - `Student.user_id` es `Mapped[uuid.UUID]` obligatorio (`NOT NULL`), indexado y con restricción de unicidad (`uq_students_user_id`).
   - La relación `Student.user` es de tipo `1:1` con carga `selectin`.
3. **Identificador Nacional SIMAT (`code_simat`):**  
   - `Student.code_simat` es `String(50)` obligatorio (`NOT NULL`) y único a nivel nacional (`uq_students_code_simat`).
4. **Relación con Matrículas (`Enrollment`):**  
   - El estudiante participa activamente en el ciclo de matrículas institucionales a través de `Enrollment.student_id -> students.id`.
   - Cada matrícula vincula al estudiante con un `AcademicYear` y un `Group` específico.
5. **Estado Actual:**  
   - El estudiante está formalmente modelado como un actor con identidad en la base de datos, pero operativamente hoy funciona como un **registro institucional pasivo**, debido a la ausencia de interfaz y endpoints de consulta para el alumno.

---

### 4. Hallazgos Forenses: Dominio de Acudientes (`Guardian`)

1. **Esquema Posterior a Fase 13E.4 (`institution_id`):**  
   - `Guardian.institution_id` es `Mapped[uuid.UUID]` obligatorio (`NOT NULL`), indexado y con clave foránea `institutions.id (ON DELETE RESTRICT)`.
   - Restricción de unicidad multi-tenant compuesta: `uq_guardians_institution_document` sobre `(institution_id, document_type, document_number)`.
2. **Vínculo Opcional con `User` (`user_id`):**  
   - `Guardian.user_id` es `Mapped[uuid.UUID | None]` opcional (`NULLABLE`), con clave foránea `users.id (ON DELETE SET NULL)` y restricción de unicidad.
   - Si el acudiente no tiene cuenta en la plataforma, `user_id = NULL`.
3. **Preservación Rural/Offline (`[OPEN-DECISION-3A-01]`):**  
   - Los acudientes del sector rural o sin correo electrónico registrado pueden existir válidamente en el sistema como contactos de emergencia y retiro autorizado sin requerir cuenta de usuario interactiva.
4. **Estado Actual:**  
   - El acudiente está modelado como una entidad civil independiente que **puede ser elevada a usuario interactivo** mediante el flujo de activación de Fase 7 (`GuardianOnboardingService`).

---

### 5. Hallazgos Forenses: Relación Estudiante-Acudiente (`StudentGuardian`)

1. **Tabla / Entidad Relacional:**  
   - Entidad `StudentGuardian` (`__tablename__ = "student_guardians"`).
   - Clave primaria compuesta o UUID propio con restricción de unicidad `uq_student_guardians_student_guardian` sobre `(student_id, guardian_id)`.
2. **Cardinalidad y Soporte de Relaciones:**  
   - Soporta que **un estudiante tenga múltiples acudientes** (e.g. Madre y Padre).
   - Soporta que **un acudiente esté vinculado a múltiples estudiantes** (e.g. Hermanos en la misma institución).
3. **Atributos de Parentesco y Autorización:**  
   - `relationship_type`: Enum canónico `PADRE`, `MADRE`, `ABUELO_A`, `TIO_A`, `TUTOR_LEGAL`, `OTRO`.
   - `is_primary_contact`: Booleano para orden de llamada en emergencias.
   - `is_authorized_pickup`: Booleano que autoriza el retiro físico del alumno en la jornada escolar.
4. **Suficiencia para Autorización de Portal:**  
   - La tabla `student_guardians` contiene toda la información necesaria para derivar con exactitud qué estudiantes puede consultar un acudiente autenticado.

---

### 6. Hallazgos Forenses: Usuario (`User`) y Roles (`UserRole`)

1. **Mecanismo de Creación y Credenciales:**  
   - Almacenamiento criptográfico con **Argon2id** (`hashed_password`).
   - Identificadores únicos: `email` (único global), `username` (único global), `(document_type, document_number)` (único global en `users`).
2. **Controles de Seguridad:**  
   - `is_active` (estado operativo).
   - `is_verified` (verificación de correo).
   - `must_change_password` (fuerza cambio en primer login).
   - `failed_login_attempts` y `locked_until` (bloqueo ante ataques de fuerza bruta).
3. **Taxonomía de Roles del Sistema:**  
   - Roles canónicos definidos en `SystemRole`: `superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `coordinator`, `academic_coordinator`, `teacher`, `student`, `guardian`, `support`, `observer`.
4. **Asignación de Roles (`UserRole`):**  
   - Soporta asignación múltiple de roles por usuario.
   - Cada asignación tiene `institution_id` y `campus_id` opcionales, permitiendo alcances institucionales específicos.
   - La jerarquía de roles (`level: 10 a 100`) previene escalamiento de privilegios vertical.

---

### 7. Hallazgos Forenses: Autenticación y Autorización

#### Respuestas a las Preguntas Clave:

1. **¿Puede un Estudiante existente autenticarse hoy?**  
   - **Técnicamente SÍ**, si se le asigna o restablece su contraseña mediante `/auth/password/reset/confirm`. Al iniciar sesión en `POST /api/v1/auth/login`, el backend valida credenciales, emite JWT con rol `student`, y devuelve `200 OK`.
   - **Operativamente NO**, porque en el aprovisionamiento actual la contraseña se genera aleatoriamente en el servidor y no se le entrega al estudiante ni se le envía enlace de activación.
2. **¿Puede un Acudiente existente autenticarse hoy?**  
   - **SÍ**, si completó el flujo de activación tokenizada (`/auth/guardians/request-activation` y `/auth/guardians/accept-activation`). Inicia sesión en `POST /api/v1/auth/login` con rol `guardian`.
3. **¿Qué falta exactamente?**  
   - **Para Estudiantes:** Flujo formal de entrega de credenciales / primer login o activación, y endpoints de consulta acotados a su propia matrícula (`/student/me/...`).
   - **Para Acudientes:** Endpoints acotados para consultar la información de sus tutorados (`/guardian/my-students/...`) y la interfaz visual del Portal de Acudientes.
4. **¿Puede existir un `User` sin `Student`/`Guardian`?**  
   - **SÍ.** Rectores, administradores nacionales y docentes son usuarios sin perfil de estudiante ni acudiente.
5. **¿Puede `Student`/`Guardian` existir sin `User`?**  
   - **`Guardian` SÍ:** Diseñado explícitamente para permitir `user_id = NULL` (`[OPEN-DECISION-3A-01]`).
   - **`Student` NO:** El modelo actual exige `user_id NOT NULL UNIQUE`.
6. **¿Cómo resuelve el backend la institución para un Estudiante?**  
   - A través de `current_user.institution_id` o `student.institution_id`.
7. **¿Cómo resuelve el backend la institución para un Acudiente?**  
   - A través de `guardian.institution_id` (añadido en Fase 13E.4) y `user.institution_id`.
8. **¿Existe un mecanismo para que el Acudiente acceda solo a sus estudiantes vinculados?**  
   - La relación de datos existe en `student_guardians`, pero **no existe un endpoint de servicio** que filtre los datos académicos bajo la condición `StudentGuardian.guardian_id == current_guardian.id`.

---

### 8. Hallazgos Forenses: Frontend

| Componente / Ruta | Estudiante (`Student`) | Acudiente (`Guardian`) | Estado |
| :--- | :--- | :--- | :--- |
| **Página de Login** | Compartida (`/login`) | Compartida (`/login`) | IMPLEMENTADO |
| **Activación / Onboarding** | No existe | `/auth/accept-invitation` (Rector), faltan vistas GUI para Acudiente | PARTIAL (Endpoints API listos, vista pendiente) |
| **Ruta del Portal** | `/student` (Inexistente) | `/guardian` (Inexistente) | NOT IMPLEMENTED |
| **Dashboard** | Genérico sin widgets | Tarjeta informativa pasiva | PARTIAL |
| **Calificaciones** | Inexistente | Inexistente | NOT IMPLEMENTED |
| **Asistencia** | Inexistente | Inexistente | NOT IMPLEMENTED |
| **Horario / Carga** | Inexistente | Inexistente | NOT IMPLEMENTED |
| **Estudiantes Vinculados** | N/A | Inexistente en UI | NOT IMPLEMENTED |
| **Aulas Virtuales** | Acceso a `/virtual-classrooms` | Sin acceso a aulas | PARTIAL (Permiso RBAC existe) |

---

### 9. Hallazgos Forenses: Aprovisionamiento de Cuentas

1. **Flujo para Rectores:**  
   - Administrador Nacional emite `RectorInvitation` (`POST /api/v1/institutions/{id}/rector/invite`).
   - Rector recibe enlace criptográfico, canjea token en `/auth/accept-invitation`, define contraseña y activa cuenta.
2. **Flujo para Docentes:**  
   - Rector o Coordinador provisiona docente con `POST /api/v1/academic/teachers` (o `POST /api/v1/teachers/provision`).
   - Se crea `User` con rol `teacher` y `must_change_password = True`.
3. **Flujo para Estudiantes:**  
   - Rector o Secretaría registra estudiante con `POST /api/v1/students` (payload `new_user`).
   - Se crea `User` con rol `student`, contraseña aleatoria no expuesta, y `must_change_password = True`.
4. **Flujo para Acudientes:**  
   - Rector o Secretaría registra la ficha del acudiente con `POST /api/v1/guardians` (`user_id = NULL`).
   - El acudiente solicita auto-activación con `POST /api/v1/auth/guardians/request-activation` validando el código SIMAT de su hijo.
   - El acudiente define su contraseña en `POST /api/v1/auth/guardians/accept-activation`.

---

### 10. Auditoría de Seguridad Multi-Tenant

1. **Aislamiento de Registros de Estudiantes:**  
   - `StudentService.list_students` y `get_student_by_id` filtran estrictamente por `Student.institution_id == target_institution_id`.
   - Denegación de acceso IDOR con `HTTP 404/403` al intentar consultar estudiantes de otra institución.
2. **Aislamiento de Registros de Acudientes (Fase 13E.4):**  
   - `GuardianService` y `endpoints/guardians.py` aíslan estrictamente por `Guardian.institution_id == target_institution_id`.
   - Restricción única compuesta `(institution_id, document_type, document_number)`.
3. **Aislamiento en Activación de Acudientes:**  
   - `GuardianOnboardingService` valida que el estudiante y el acudiente pertenezcan a la misma institución antes de emitir o redimir el token de activación.

---

### 11. Mapa de Propiedad y Dependencia de Datos

```
[Institución Educativa (Tenant Boundary)]
   │
   ├── [Año Lectivo] ── [Períodos Académicos]
   │       │
   │       └── [Grupos / Salones] ── [Asignaciones Académicas Docentes]
   │                 ▲
   │                 │ (Matrícula Activa)
   ├── [Estudiantes] ┴── [Matrícula / Enrollment]
   │       ▲                      │
   │       │ 1:1                  └── [Calificaciones, Asistencia, Actividades]
   │   [Usuario Alumno (User)]
   │
   ├── [Acudientes (Guardian)]
   │       │ (Opcional 1:1)
   │       ├── [Usuario Acudiente (User)]
   │       │
   │       └── [StudentGuardian (Vínculo de Tutoría)]
   │                 │
   │                 └───► [Estudiante Tutorado]
```

---

### 12. Matriz de Capacidades y Gaps

| Capacidad | Estudiante (`Student`) | Acudiente (`Guardian`) | Estado Actual | Evidencia |
| :--- | :--- | :--- | :---: | :--- |
| **Registro de Dominio** | Implementado | Implementado | **IMPLEMENTED** | `Student` y `Guardian` models |
| **Pertenencia Institucional** | Implementado | Implementado | **IMPLEMENTED** | `institution_id` FK NOT NULL en ambos |
| **Cuenta de Usuario (`User`)** | Obligatorio (1:1) | Opcional (0..1) | **IMPLEMENTED** | `Student.user_id` vs `Guardian.user_id` |
| **Rol en RBAC** | `student` (Nivel 10) | `guardian` (Nivel 10) | **IMPLEMENTED** | `SystemRole.STUDENT` y `GUARDIAN` |
| **Autenticación (Login)** | Implementado | Implementado | **IMPLEMENTED** | `POST /api/v1/auth/login` |
| **Recuperación de Clave** | Implementado | Implementado | **IMPLEMENTED** | `/auth/password/reset/...` |
| **Activación de Cuenta** | No implementado | Implementado | **PARTIAL** | `GuardianOnboardingService` listo |
| **Ruta en Frontend** | No existe | No existe | **NOT IMPLEMENTED** | `App.tsx` no tiene `/student` ni `/guardian` |
| **Dashboard Específico** | No existe | Tarjeta informativa | **PARTIAL** | `Dashboard.tsx` |
| **Consulta de Hijos/Tutorados** | N/A | No implementado | **NOT IMPLEMENTED** | Falta endpoint `/guardian/students` |
| **Acceso a Calificaciones** | No implementado | No implementado | **NOT IMPLEMENTED** | Solo Docente/Rector consultan notas |
| **Acceso a Asistencia** | No implementado | No implementado | **NOT IMPLEMENTED** | Solo Docente/Rector consultan asistencia |
| **Acceso a Actividades** | No implementado | No implementado | **NOT IMPLEMENTED** | Solo Docente/Rector gestionan tareas |
| **Aislamiento Multi-Tenant** | Implementado | Implementado | **IMPLEMENTED** | Fases 13E.1, 13E.4 y 13E.5 |

---

### 13. Respuestas Explícitas a las 16 Decisiones Arquitectónicas

1. **¿Deben las cuentas de Estudiante y Acudiente reutilizar la entidad `User` existente?**  
   **SÍ.** La entidad `User` centraliza la autenticación con Argon2id, tokens JWT, rotación de sesiones, bloqueo por fuerza bruta y auditoría.
2. **¿Deben tener valores dedicados en `UserRole`?**  
   **SÍ.** Ya existen `SystemRole.STUDENT = "student"` y `SystemRole.GUARDIAN = "guardian"`.
3. **¿Debe ser 1:1 la relación entre `User` y `Student`/`Guardian`?**  
   **SÍ por institución.** Un `User` representa a una persona física con un único perfil de estudiante o acudiente en ese establecimiento.
4. **¿Puede una cuenta de Acudiente estar vinculada a múltiples estudiantes?**  
   **SÍ.** La tabla `student_guardians` permite vincular un único `guardian_id` a múltiples `student_id`.
5. **¿Pueden múltiples Acudientes estar vinculados a un solo Estudiante?**  
   **SÍ.** `student_guardians` permite múltiples registros para el mismo `student_id` (e.g. Madre, Padre, Abuelo).
6. **¿Puede un Acudiente pertenecer a múltiples instituciones?**  
   **DECISIÓN REQUERIDA:** Actualmente `Guardian.institution_id` ancla al acudiente a una sola institución. Si una persona tiene hijos en dos colegios distintos, el modelo actual crea dos registros de acudiente independientes (uno por institución) compartiendo el mismo documento. Para una cuenta de login unificada, se requerirá soporte multisede/multi-institución en `UserRole`.
7. **¿Puede un Estudiante pertenecer a múltiples instituciones simultáneamente?**  
   **NO.** Bajo la normativa del MEN y SIMAT, un alumno solo puede tener una matrícula activa en una única institución oficial a la vez. El traslado anula la matrícula previa.
8. **¿Cuál es la ruta canónica de resolución de tenant para cada cuenta?**  
   - Para `Student`: `current_user.institution_id` $\rightarrow$ `Student.institution_id`.
   - Para `Guardian`: `current_user.institution_id` $\rightarrow$ `Guardian.institution_id` $\rightarrow$ `StudentGuardian.student.institution_id`.
9. **¿Quién debe estar autorizado para aprovisionar cuentas de Estudiantes?**  
   - Rector, Coordinador Académico y Administrador Institucional (mediante matrícula SIMAT / creación de estudiante).
10. **¿Quién debe estar autorizado para aprovisionar cuentas de Acudientes?**  
    - La institución registra la ficha civil; la activación de la cuenta de login es realizada por el propio acudiente mediante auto-activación tokenizada con el código SIMAT de su hijo.
11. **¿Es apropiado el auto-registro o debe ser aprovisionado por la institución?**  
    - **Aprovisionado con activación verificada:** No debe existir auto-registro libre ("crear cuenta abierta"). La cuenta solo se activa si existe una vinculación civil previa registrada por el colegio.
12. **¿Qué sucede cuando un estudiante cambia de institución?**  
    - Su matrícula pasa a estado `TRANSFERRED`/`WITHDRAWN` en la Institución A. En la Institución B se registra su nueva matrícula. El usuario conserva su historial.
13. **¿Qué sucede cuando un acudiente tiene hijos en diferentes instituciones?**  
    - **DECISIÓN REQUERIDA:** Definir si el portal del acudiente ofrecerá un selector de institución o si se mantendrán cuentas separadas por colegio.
14. **¿Qué sucede cuando un estudiante se gradúa o queda inactivo?**  
    - `Student.is_active` o `Enrollment.status = GRADUATED`. Su cuenta `User` pasa a solo lectura para consulta de certificados históricos.
15. **¿Qué sucede cuando se elimina una relación de acudiente (`StudentGuardian`)?**  
    - Se revoca el acceso del acudiente a los datos de ese estudiante específico. Si no le quedan otros estudiantes vinculados, la cuenta queda sin tutorados activos.
16. **¿Qué sucede con la cuenta de login cuando la persona queda inactiva?**  
    - `User.is_active = False` impide nuevos inicios de sesión y revoca los tokens de refresco activos.

---

### 14. Fases de Implementación Recomendadas

```
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14A: Aprovisionamiento y Activación del Estudiante                │
│ (Entrega de credenciales, primer login, cambio forzoso de clave)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14B: Portal del Estudiante (Backend & Frontend)                   │
│ (Rutas /student, consulta de materias, notas, asistencia, tareas)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Fase 14C: Portal del Acudiente / Familia (Backend & Frontend)          │
│ (Rutas /guardian, selector de hijos, seguimiento pedagógico, alertas)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 15. Archivos, Endpoints y Pruebas Inspeccionadas

- **Modelos:** `backend/app/models/student.py`, `guardian.py`, `user.py`, `role.py`, `invitation.py`, `enrollment.py`.
- **Servicios:** `backend/app/services/student_service.py`, `guardian_service.py`, `user_service.py`, `guardian_onboarding_service.py`, `rbac_bootstrap_service.py`.
- **Endpoints:** `backend/app/api/v1/endpoints/students.py`, `guardians.py`, `auth.py`, `teacher_portal.py`, `users.py`.
- **Frontend:** `frontend/src/App.tsx`, `Dashboard.tsx`, `RequireAuth.tsx`, `GuardiansView.tsx`, `StudentsView.tsx`.
- **Pruebas:** `backend/tests/test_guardian_onboarding.py`, `test_guardian_tenant_isolation.py`, `test_academic_api.py`, `test_groups_and_actors_models.py`.

---

### 16. Veredicto Final

**B. REQUIRES ARCHITECTURAL DECISIONS + C. EXISTING IMPLEMENTATION CAN BE EXTENDED**

La arquitectura de datos existente es **sólida, limpia y multi-tenant**, constituyendo una base excelente para habilitar el acceso a Estudiantes y Acudientes sin necesidad de rediseñar las tablas fundamentales.
