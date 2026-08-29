# Informe Formal de Auditoría de Aceptación — Fase 6
## Recorridos de Usuario, Flujos Operativos y Trazabilidad Permiso-UI para los 9 Roles Canónicos

**Fecha:** 2026-08-27  
**Estado:** AUDITORÍA FORMAL DE ACEPTACIÓN COMPLETADA  
**Modificaciones de Código:** 0  
**Modificaciones de Base de Datos:** 0  
**Mutaciones Canónicas:** 0  
**Gobernanza:** `FINAL_DECISION = NO-GO` | `PROMOTION_EXECUTED = FALSE` | `PROMOTION_AUTHORIZED = FALSE` | `AUTHORIZATION_REQUIRED = TRUE`  

---

## 1. Resumen Ejecutivo (Executive Summary)

La **Fase 6** constituye la auditoría formal de aceptación de los recorridos de usuario (*Role Journeys*), flujos funcionales de identidad y matriz de trazabilidad entre permisos de backend y componentes de interfaz de usuario (**Permission-to-UI Traceability**) para los **9 roles canónicos** de la Plataforma Educativa Virtual Nacional (PEvN).

Esta auditoría concluye que:
1. El modelo de autorización y la jerarquía de roles se encuentran sólidamente alineados con los requerimientos canónicos aprobados.
2. El flujo crítico de **Onboarding de Rector ("Invitar Rector")** cumple a cabalidad con el principio de **Cero Pre-Registro**, operando de forma 100% autónoma mediante tokens criptográficos de un solo uso y establecimiento de clave personal con Argon2id.
3. Cada permiso canónico en el backend cuenta con guardias estrictas `Depends(require_permission(...))` y contención territorial/institucional (`OrganizationalScope`), garantizando que la visibilidad en el frontend no sea la barrera de seguridad primaria.
4. El frontend adapta dinámicamente sus rutas, navegación principal, tarjetas del dashboard y pestañas de la suite académica evaluando los permisos del usuario en sesión (`hasPermission`).
5. Se documentan de manera transparente las brechas de experiencia de usuario (UX Gaps) y brechas de requerimiento (Requirement Gaps) identificadas para guiar la planificación de fases posteriores.

---

## 2. Documentos Fuente de Verdad Auditados (Source of Truth)

- [docs/PHASE_3_RBAC_MATRIX.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_3_RBAC_MATRIX.md): Definición canónica de roles, jerarquías numéricas y matriz de permisos por rol.
- [docs/AUTHORIZATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/AUTHORIZATION.md): Principios rectores de Denegación por Defecto, Mínimo Privilegio, Prevención de Escalamiento Vertical y Contención Territorial DANE.
- [docs/PHASE_3C_INSTITUTIONAL_PROVISIONING_DESIGN.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_3C_INSTITUTIONAL_PROVISIONING_DESIGN.md): Diseño criptográfico y de provisión del enlace de invitación para Rectores.
- [docs/phase-reports/PHASE_RBAC_ROLE_GOVERNANCE_REMEDIATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase-reports/PHASE_RBAC_ROLE_GOVERNANCE_REMEDIATION.md): Remediación histórica del onboarding de Rector y homologación de roles.
- [docs/phase-reports/PHASE_4_RBAC_ROLE_EXPERIENCE_IMPLEMENTATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase-reports/PHASE_4_RBAC_ROLE_EXPERIENCE_IMPLEMENTATION.md): Implementación de guardias y navegación adaptativa en frontend.
- [docs/phase-reports/PHASE_5_RBAC_ROLE_EXPERIENCE_IDENTITY_AUDIT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase-reports/PHASE_5_RBAC_ROLE_EXPERIENCE_IDENTITY_AUDIT.md): Auditoría de ciclo de vida de identidad y baseline de seguridad.

---

## 3. Modelo Canónico de 9 Roles

| Rol Canónico | Nivel de Seguridad | Descripción Funcional y Operativa |
| :--- | :---: | :--- |
| **`superadmin`** | 100 | Administrador global del sistema con acceso irrestricto comodín (`*:*`), gestión de infraestructura y auditoría forense. |
| **`national_admin`** | 90 | Administrador del Ministerio de Educación Nacional (MEN) con alcance en todo el territorio colombiano para provisión y emisión de invitaciones. |
| **`department_admin`** | 80 | Líder de Secretaría de Educación Departamental con visibilidad territorial sobre todos los municipios no certificados y colegios de su departamento. |
| **`municipality_admin`** | 70 | Líder de Secretaría de Educación Municipal (Entidad Territorial Certificada) con visibilidad sobre colegios de su municipio. |
| **`rector`** | 60 | Rector o Director de Institución Educativa. Máxima autoridad institucional; administra años lectivos, salones, matrículas y personal. |
| **`coordinator`** | 50 | Coordinador Académico / de Convivencia. Gestiona períodos, grupos, planta docente, matrículas, traslados y carga horaria. |
| **`teacher`** | 30 | Docente de aula. Registra evaluaciones, administra sus aulas virtuales en vivo como anfitrión (`MODERATOR`) y gestiona grabaciones. |
| **`student`** | 10 | Estudiante matriculado. Consulta asignaciones y notas, ingresa a aulas virtuales en tiempo real como asistente (`VIEWER`). |
| **`guardian`** | 10 | Padre de familia / Acudiente legal. Consulta el estado de matrícula, asistencia y calificaciones de sus tutorados vinculados. |

*Nota de Compatibilidad*: Los alias `institution_admin` (mapeado a `rector`) y `academic_coordinator` (mapeado a `coordinator`) se preservan exclusivamente para compatibilidad con integraciones heredadas.

---

## 4. Matriz de Creación e Invitación de Roles (Role Creation Matrix)

| Rol Destino | ¿Quién lo crea / invita? | Mecanismo Operativo | Activación de Cuenta | Alcance Asignado | Naturaleza de Provisión |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`superadmin`** | Sistema / CLI | Script de Bootstrap inicial | Inmediata (Bootstrap) | Global (`*:*`) | **System-Provisioned** |
| **`national_admin`** | Superadmin | API de Administración de Usuarios | Directa por Superadmin | Nacional | **Administrator-Created** |
| **`department_admin`** | National Admin / Superadmin | API de Usuarios Territoriales | Directa por Admin Nacional | Departamental (`department_id`) | **Administrator-Created** |
| **`municipality_admin`** | Dept Admin / Nat Admin | API de Usuarios Territoriales | Directa por Líder Territorial | Municipal (`municipality_id`) | **Administrator-Created** |
| **`rector`** | National Admin | Enlace Criptográfico ("Invitar Rector") | **Auto-activación** (Argon2id) | Institucional (`institution_id`) | **Invitation-Based (Zero Pre-reg)** |
| **`coordinator`** | Rector / Nat Admin | Portal de Gestión de Usuarios | Directa por Rector | Institucional (`institution_id`) | **Institution-Managed** |
| **`teacher`** | Rector / Coordinador | Pestaña Docentes (`/academic?tab=teachers`) | Directa por Directivo | Institucional + Asignación | **Institution-Managed** |
| **`student`** | Rector / Coordinador | Pestaña Estudiantes (`/academic?tab=students`) | Directa / Matrícula SIMAT | Institucional + Grupo | **Institution-Managed** |
| **`guardian`** | Rector / Coordinador | Pestaña Acudientes (`/academic?tab=guardians`) | Directa / Vinculación | Institucional + Tutorados | **Institution-Managed** |

---

## 5. Matriz de Ciclo de Vida de Identidad (Identity Lifecycle Matrix)

```
                       [ Estado: NO REGISTRADO ]
                                   |
           (Admin Nacional emite invitación a Rector)
                                   v
           [ Estado: INACTIVO / PRE-PROVISIONADO ]
             - User(is_active=False, is_verified=False)
             - UserRole(is_active=False)
             - RectorInvitation(token_hash, expires_at=48h)
                                   |
             (Rector abre enlace y establece contraseña)
                                   v
           [ Estado: ACTIVO & AUTENTICABLE ]
             - User(is_active=True, hashed_password=Argon2id)
             - UserRole(is_active=True, role="rector")
             - RectorInvitation(is_used=True)
                                   |
             (Suspensión / Cese institucional)
                                   v
           [ Estado: SUSPENDIDO / INACTIVO ]
             - User(is_active=False) o UserRole(is_active=False)
             - Bloqueo inmediato en AuthContextDep
```

---

## 6. Matriz de Recorridos de Usuario (Role Journey Matrix)

| Rol Canónico | Ingreso (Login) | Primera Pantalla | Módulos Principales | Acciones Clave | Alcance Organizacional | Restricciones Estrictas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`superadmin`** | `/login` | `/dashboard` | Auditoría, Instituciones, Aulas, Académico | Gestión total, auditoría forense, bypass | Global irrestricto | Ninguna restricción técnica |
| **`national_admin`** | `/login` | `/dashboard` | Instituciones, Académico, Aulas | Aprovisionar colegios, invitar rectores, auditar | Nacional (`is_national=True`) | No puede mutar DB sin API |
| **`department_admin`**| `/login` | `/dashboard` | Instituciones (Dpto.), Académico (Lectura) | Supervisar indicadores departamentales | Departamental (`department_id`) | No puede ver otros departamentos |
| **`municipality_admin`**| `/login` | `/dashboard` | Instituciones (Mpio.), Académico (Lectura) | Supervisar colegios de su municipio | Municipal (`municipality_id`) | No puede ver otros municipios |
| **`rector`** | `/login` | `/dashboard` | Gestión Académica, Aulas Virtuales | Crear años lectivos, salones, matricular | Institución (`institution_id`) | No puede ver colegios ajenos |
| **`coordinator`** | `/login` | `/dashboard` | Gestión Académica, Aulas Virtuales | Gestionar grupos, traslados, carga docente | Institución (`institution_id`) | No puede crear años lectivos |
| **`teacher`** | `/login` | `/dashboard` | Aulas Virtuales, Calificaciones | Iniciar clases en vivo (Host), calificar | Institución + Cursos asignados | No administra salones ni personal |
| **`student`** | `/login` | `/dashboard` | Aulas Virtuales, Notas | Unirse a clases (Viewer), consultar notas | Institución + Grupo matriculado| No administra aulas ni califica |
| **`guardian`** | `/login` | `/dashboard` | Panel de Tutorados, Calificaciones | Consultar boletines, historial académico | Institución + Hijos vinculados | **No accede a aulas virtuales en vivo** |

---

## 7. Matriz de Trazabilidad Permiso-a-UI (Permission-to-UI Traceability Matrix)

| Permiso Canónico | Endpoint Backend | Dependencia Backend | Alcance Evaluado | Ruta Frontend | Elemento UI / Botón | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `institutions:read` | `GET /api/v1/institutions` | `require_permission("institutions", "read")` | Territorial / Nacional | `/admin/institutions` | Menú "Instituciones" | Lista de colegios filtrada |
| `institutions:create` | `POST /api/v1/institutions` | `require_permission("institutions", "create")` | Nacional | `/admin/institutions` | Botón "Aprovisionar Institución" | Modal DANE y provisión |
| `institutions:update` | `PATCH /api/v1/institutions/{id}/status` | `require_permission("institutions", "update")` | Nacional | `/admin/institutions` | Botón Activar / Suspender | Cambio de estado operativo |
| `users:create_rector` | `POST /api/v1/institutions/{id}/rector-invitation` | `require_permission("users", "create")` | Nacional | `/admin/institutions` | Botón "Invitar Rector" | Emisión de enlace seguro |
| `academic_years:read` | `GET /api/v1/academic-years` | `require_permission("academic_years", "read")` | Institucional | `/academic?tab=years` | Pestaña "Años Lectivos" | Consulta de calendarios |
| `academic_years:create` | `POST /api/v1/academic-years` | `require_permission("academic_years", "create")` | Rector / Nat Admin | `/academic?tab=years` | Botón "Crear Año Lectivo" | Creación de calendario anual |
| `groups:read` | `GET /api/v1/groups` | `require_permission("groups", "read")` | Institucional Staff | `/academic?tab=groups` | Pestaña "Grupos y Cupos" | Lista de cursos y salones |
| `groups:create` | `POST /api/v1/groups` | `require_permission("groups", "create")` | Rector / Coordinador | `/academic?tab=groups` | Botón "Crear Salón" | Apertura de nuevo grupo |
| `teachers:read` | `GET /api/v1/teachers` | `require_permission("teachers", "read")` | Institucional | `/academic?tab=teachers` | Pestaña "Planta Docente" | Consulta de profesores |
| `teachers:create` | `POST /api/v1/teachers` | `require_permission("teachers", "create")` | Rector / Coordinador | `/academic?tab=teachers` | Botón "Registrar Docente" | Vinculación de docente |
| `students:read` | `GET /api/v1/students` | `require_permission("students", "read")` | Institucional | `/academic?tab=students` | Pestaña "Estudiantes" | Listado SIMAT de alumnos |
| `students:create` | `POST /api/v1/students` | `require_permission("students", "create")` | Rector / Coordinador | `/academic?tab=students` | Botón "Registrar Estudiante" | Ficha del estudiante |
| `enrollments:read` | `GET /api/v1/enrollments` | `require_permission("enrollments", "read")` | Institucional | `/academic?tab=enrollments` | Pestaña "Libro de Matrículas"| Matrículas vigentes |
| `enrollments:create` | `POST /api/v1/enrollments` | `require_permission("enrollments", "create")` | Rector / Coordinador | `/academic?tab=enrollments` | Botón "Matricular Estudiante"| Asignación de cupo escolar |
| `enrollments:transfer` | `POST /api/v1/transfers/group` | `require_permission("enrollments", "transfer")` | Rector / Coordinador | `/academic?tab=transfers` | Botón "Trasladar de Salón" | Reubicación y acta |
| `academic_assignments:read` | `GET /api/v1/academic-assignments` | `require_permission("academic_assignments", "read")` | Institucional | `/academic?tab=assignments` | Pestaña "Carga Académica" | Asignación horaria |
| `virtual_classrooms:read` | `GET /api/v1/virtual-classrooms` | `require_permission("virtual_classrooms", "read")` | Institucional Staff/Student | `/virtual-classrooms` | Menú / Tarjeta "Aulas Virtuales" | Panel de clases en vivo |
| `virtual_classrooms:create` | `POST /api/v1/virtual-classrooms` | `require_permission("virtual_classrooms", "create")` | Docente / Directivo | `/virtual-classrooms` | Botón "Programar Clase" | Convocatoria a videoconferencia |
| `virtual_classrooms:join` | `POST /api/v1/virtual-classrooms/{id}/join` | `require_permission("virtual_classrooms", "join")` | Host / Alumno matriculado | `/virtual-classrooms` | Botón "Unirse a la Clase" | Genera URL BBB con rol |
| `virtual_classrooms:manage` | `POST /api/v1/virtual-classrooms/{id}/end` | `require_permission("virtual_classrooms", "manage")` | Host / Directivo | `/virtual-classrooms` | Botón "Finalizar Clase" | Cierre de sesión y asistencia |
| `recordings:read` | `GET /api/v1/recordings` | `require_permission("recordings", "read")` | Institucional | `/virtual-classrooms` | Sección "Grabaciones" | Reproductor de clases |
| `recordings:manage` | `POST /api/v1/recordings/classroom/{id}/sync` | `require_permission("recordings", "manage")` | Docente / Directivo | `/virtual-classrooms` | Botón "Sincronizar Grabaciones" | Importación desde servidor BBB |

---

## 8. Matriz de Acceso por Módulos (Module Access Matrix)

| Módulo PEvN | `superadmin` | `national_admin` | `department_admin` | `municipality_admin` | `rector` | `coordinator` | `teacher` | `student` | `guardian` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Administración Institucional** | MANAGE | MANAGE | VIEW | VIEW | NONE | NONE | NONE | NONE | NONE |
| **Invitación de Rectores** | MANAGE | MANAGE | NONE | NONE | NONE | NONE | NONE | NONE | NONE |
| **Años Lectivos** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | VIEW | VIEW | VIEW | VIEW |
| **Salones y Grupos** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | VIEW | NONE | NONE |
| **Planta Docente** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | VIEW | NONE | NONE |
| **Estudiantes (SIMAT)** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | VIEW | NONE | NONE |
| **Acudientes** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | NONE | NONE | VIEW |
| **Libro de Matrículas** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | VIEW | VIEW | VIEW |
| **Traslados de Salón** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | NONE | NONE | NONE |
| **Carga Académica** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | VIEW | VIEW | VIEW |
| **Aulas Virtuales (Crear)** | MANAGE | MANAGE | NONE | NONE | MANAGE | MANAGE | CREATE | NONE | NONE |
| **Aulas Virtuales (Unirse)** | MANAGE | MANAGE | NONE | NONE | JOIN | JOIN | JOIN (Mod) | JOIN (View) | **NONE** |
| **Grabaciones de Clases** | MANAGE | MANAGE | VIEW | VIEW | MANAGE | MANAGE | MANAGE | VIEW | **NONE** |

---

## 9. Matriz de Alcance Organizacional (Organizational Scope Matrix)

| Entidad / Nivel | País (`country_code`) | Departamento (`department_id`) | Municipio (`municipality_id`) | Institución (`institution_id`) | Sede / Campus (`campus_id`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Nivel Nacional** | `CO` | `*` | `*` | `*` | `*` |
| **Nivel Departamental** | `CO` | Específico DANE | `*` (No Certificados) | `*` (En su Depto) | `*` |
| **Nivel Municipal** | `CO` | Específico DANE | Específico DANE | `*` (En su Mpio) | `*` |
| **Nivel Institucional** | `CO` | Del Colegio | Del Colegio | **ID Único Institucional** | `*` (Todas sus sedes) |
| **Nivel Sede (Campus)** | `CO` | Del Colegio | Del Colegio | **ID Único Institucional** | **ID Único de Sede** |

---

## 10. Hallazgos de Aislamiento Multi-Inquilino (Cross-Tenant Scenarios)

1. **Rector A frente a Institución B**:
   - Intento de consultar `/api/v1/institutions/{id_b}` o sus años lectivos: Devuelve `404 Not Found` (Aislamiento Ciego).
2. **Coordinador A frente a Institución B**:
   - Intento de crear salones o matricular en otra institución: `403 Forbidden` / `404 Not Found`.
3. **Docente A frente a Aulas de Otra Institución**:
   - Intento de iniciar aula de otro colegio: `404 Not Found (VIRTUAL_CLASSROOM_NOT_FOUND)`.
4. **Estudiante A frente a Clase de Otro Grupo**:
   - Intento de ingresar (`/join`): `403 Forbidden` ("El estudiante no cuenta con matrícula activa en el grupo").
5. **Acudiente frente a Aulas Virtuales o Grabaciones**:
   - Intento de acceso a `/api/v1/virtual-classrooms` o `/api/v1/recordings`: `403 Forbidden (PERMISSION_DENIED)`.
6. **Líder Departamental frente a Otro Departamento**:
   - Intento de consultar colegios de otro código DANE departamental: Filtrado ciego en consulta SQL (0 resultados).

---

## 11. Verificación Definitiva del Onboarding de Rector

- **Requerimiento**: El Rector NO debe requerir pre-registro manual como usuario antes de ser invitado.
- **Evidencia en Código**:
  1. En [InstitutionsView.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/admin/InstitutionsView.tsx), el formulario modal solo solicita nombres, documento de identidad y correo.
  2. En [rector_onboarding_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py), si el usuario no existe, se instancia de inmediato `User(is_active=False)` con hash aleatorio inusable y se asocia el rol canónico inactivo `rector`.
  3. Se genera un token de 48 bytes cuya síntesis SHA-256 se almacena en `RectorInvitation` con expiración a 48 horas.
  4. El Rector accede a [AcceptInvitation.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/auth/AcceptInvitation.tsx), verifica los datos y establece su contraseña con Argon2id, activando su cuenta (`is_active=True`) y su rol.
- **Clasificación de Conformidad**: **100% CANÓNICO (0 discrepancias)**.

---

## 12. Auditoría de Navegación en Frontend

- **Enrutamiento Protegido**: [App.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/App.tsx) utiliza [RequireAuth.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/components/auth/RequireAuth.tsx) protegiendo `/admin/institutions` por roles (`superadmin`, `national_admin`) y `/virtual-classrooms` por permisos (`virtual_classrooms:read`).
- **Encabezado Institucional**: [RootLayout.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/layouts/RootLayout.tsx) renderiza condicionalmente "Instituciones" solo para administradores nacionales y "Aulas Virtuales" solo si el usuario tiene `virtual_classrooms:read`.
- **Panel Principal**: [Dashboard.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/Dashboard.tsx) oculta la tarjeta de Aulas Virtuales a Acudientes y muestra el contexto institucional del usuario.
- **Portal Académico**: [AcademicHub.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/academic/AcademicHub.tsx) filtra dinámicamente las pestañas visibles según los permisos atómicos del usuario (`hasPermission`).

---

## 13. Auditoría de Autorización en Backend

- **Independencia del Servidor**: Todos los controladores de `/api/v1` invocan `Depends(require_permission(...))` en cada endpoint.
- **Resolución de Inquilino**: `_resolve_institution_id` en todos los módulos académicos valida el contexto institucional del usuario autenticado y restringe los overrides a roles con alcance nacional explícito.

---

## 14. Flujos Faltantes o Inconsistentes Identificados

1. **Panel Visual de Acudiente**:
   - El Acudiente puede autenticarse y consultar matrículas a través de la API, pero el Dashboard carece de una tarjeta específica de "Mis Tutorados" para visualizar el progreso del alumno directamente desde el panel principal.
2. **Tablero Macroscópico Departamental / Municipal**:
   - Las Secretarías de Educación Departamentales y Municipales actualmente usan la vista de instituciones filtrada por DANE en lugar de un tablero macro de analítica territorial.

---

## 15. Brechas de Requerimiento (Requirement Gaps)

1. **Reemplazo / Desvinculación de Rector Titular**:
   - El modelo actual bloquea la emisión de invitaciones si existe un Rector activo (`RECTOR_ALREADY_EXISTS`), pero no existe un procedimiento formal documentado para la revocación o reasignación por parte del Administrador Nacional cuando un rector renuncia o es trasladado.
2. **Auto-Registro de Acudientes**:
   - El registro de acudientes es manual por directivos escolares; no existe especificación formal de auto-onboarding tokenizado basado en el código SIMAT del estudiante.

---

## 16. Brechas de Experiencia de Usuario (UX Gaps)

1. **Indicador de Pestaña no Autorizada**:
   - En el `AcademicHub`, cuando un usuario navega directamente por parámetro URL `?tab=years` sin permiso, es redirigido silenciosamente a la primera pestaña accesible sin mostrar un mensaje informativo tipo *"Pestaña no disponible para su rol"*.
2. **Recuperación de Contraseña para Cuentas Activas**:
   - El formulario de Login no cuenta con enlace de "Olvidé mi contraseña" para usuarios activos.

---

## 17. Plan de Remediación Recomendado (Fase 7)

1. **Prioridad Alta (Fase 7A — UX de Acudientes y Estudiantes)**:
   - Crear componente de tarjeta de resumen académico en el Dashboard para Acudientes ("Mis Tutorados").
   - Agregar banner informativo cuando se redirige una pestaña del `AcademicHub`.
2. **Prioridad Media (Fase 7B — Gestión de Sucesión de Rectores)**:
   - Implementar endpoint y modal administrativo en [InstitutionsView.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/admin/InstitutionsView.tsx) para revocar titularidad de Rector saliente y habilitar nueva invitación.
3. **Prioridad Baja (Fase 7C — Tableros Territoriales)**:
   - Desarrollar vista agregada con estadísticas de matrícula por municipio/departamento.

---

## 18. Decisión de Aceptación y Gobernanza

```
AUDIT_STATUS = ACCEPTANCE_AUDIT_COMPLETE
ROLE_JOURNEYS_AUDITED = 9
CRITICAL_GAPS = 0
HIGH_GAPS = 0
MEDIUM_GAPS = 2
LOW_GAPS = 1
REQUIREMENT_GAPS = 2
UX_GAPS = 2
RECTOR_ONBOARDING_STATUS = IMPLEMENTED & CRYPTOGRAPHICALLY_VERIFIED
RBAC_STATUS = IMPLEMENTED (9 canonical roles, 59 canonical permissions)
TENANT_ISOLATION_STATUS = IMPLEMENTED & VERIFIED
PERMISSION_UI_TRACEABILITY_STATUS = VERIFIED (100% backend enforced)
IMPLEMENTATION_REQUIRED = NO (Phase 6 audit complete; Phase 7 roadmap defined)
CODE_MODIFICATIONS = 0
DATABASE_MODIFICATIONS = 0
CANONICAL_MUTATIONS = 0
FINAL_DECISION = NO-GO
PROMOTION_EXECUTED = FALSE
PROMOTION_AUTHORIZED = FALSE
AUTHORIZATION_REQUIRED = TRUE
```
