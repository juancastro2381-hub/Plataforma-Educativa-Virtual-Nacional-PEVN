# PEVN — MATRIZ FORENSE DE CAPACIDADES FUNCIONALES Y ROLES
## INVENTARIO DE CAPACIDADES DEL PRODUCTO Y MATRIZ DETALLADA POR ROL (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Tipo de Documento:** Matriz de Capacidades Funcionales & Control de Acceso por Perfil  
**Marco de Auditoría:** AI Software Factory v1.2 (Fase 0 — Forensic Readiness)  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Audit Evidence  

---

## 1. Visión General del Producto y Modelo Institucional

### 1.1 Propósito del Producto
La **Plataforma Educativa Virtual Nacional (PEVN)** es un sistema de información misional y de gestión educativa diseñado para el sector oficial colombiano. Integra en una única plataforma soberana y multi-inquilino (*multi-tenant*) los procesos de:
- Organización territorial y catálogo oficial de colegios (DANE / DUE).
- Estructura académica, matrícula oficial (SIMAT), asignaciones docentes y planeación curricular.
- Calificaciones y Sistema Institucional de Evaluación de los Estudiantes (SIEE, Decreto 1290 de 2009).
- Aulas virtuales sincrónicas (BigBlueButton) con telemetría de asistencia y grabaciones.
- Gestión de convivencia escolar y observador del estudiante (Ley 1620 de 2013).
- Comunicaciones institucionales con acuse de recibo y periódico escolar digital.
- Portales soberanos e independientes para Directivos, Docentes, Estudiantes y Acudientes.

### 1.2 Jerarquía Territorial y Estructura Organizacional
El modelo de datos refleja de manera exacta la división político-administrativa de Colombia:
```
Nivel 0: Colombia (Nación / MEN)
  └── Nivel 1: Departamentos (32) / Distritos Capitales
       └── Nivel 2: Municipios (Entidades Territoriales Certificadas / No Certificadas)
            └── Nivel 3: Institución Educativa (Código DANE 12 dígitos, Rectoría)
                 └── Nivel 4: Sede Educativa (Código DANE Sede, Campus)
                      └── Nivel 5: Estructura Académica (Año Lectivo -> Períodos -> Grados -> Grupos)
```

### 1.3 Perfiles Técnicos vs. Roles de Negocio
| Rol Técnico (`SystemRole`) | Nivel Seguridad | Rol de Negocio en Sistema Educativo Colombiano |
| :--- | :---: | :--- |
| `superadmin` | 100 | Administrador Técnico de Infraestructura Nacional y Soporte de Plataforma. |
| `national_admin` | 90 | Funcionario del Ministerio de Educación Nacional (MEN) con alcance nacional. |
| `territorial_leader` | 80 | Líder / Secretario de Educación Departamental o Municipal (ETC). |
| `institution_admin` | 70 | Rector(a) / Director(a) de Establecimiento Educativo Oficial. |
| `coordinator` | 60 | Coordinador(a) Académico(a) o Coordinador(a) de Convivencia Escolar. |
| `teacher` | 50 | Docente de Aula nombrado en la planta institucional. |
| `student` | 20 | Estudiante matriculado legalmente en el padrón SIMAT. |
| `guardian` | 10 | Padre, madre o acudiente legal vinculado civilmente al estudiante. |

---

## 2. Inventario Exhaustivo de Capacidades del Producto

A continuación se audita cada capacidad técnica y funcional del sistema, clasificando su estado bajo la taxonomía canónica:
`VERIFIED` | `IMPLEMENTED BUT NOT FULLY VERIFIED` | `PARTIAL` | `CONFIGURATION REQUIRED` | `INFRASTRUCTURE REQUIRED` | `NOT IMPLEMENTED` | `UNKNOWN`.

| # | Capacidad | Implementación Actual | API Backend | Vista Frontend | Evidencia de Pruebas | Evidencia Runtime | Estado | Limitación Conocida |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **1** | **Autenticación Central** | Hashing Argon2id, JWT en memoria volátil, cookie de refresco HttpOnly. | `POST /api/v1/auth/login`, `POST /refresh`, `POST /logout` | `pages/Login.tsx`, `context/AuthContext.tsx` | `test_auth_service.py`, `test_auth_endpoints.py` (11 tests) | Verificado en 8000/3000 | `VERIFIED` | No soporta aún Single Sign-On (SSO) con Gov.co o Google/Microsoft Workspace. |
| **2** | **Protección de Sesión y Detección de Replay** | Rotación en cada refresh. Reutilización de token previo revoca la familia completa (`family_id`). | `POST /api/v1/auth/refresh` | Axios interceptor con cola single-flight (`SingleFlightRefresh.test.ts`) | `test_auth_service.py` | Validado con pruebas concurrentes | `VERIFIED` | Requiere sincronización en clúster Redis para despliegues multi-nodo. |
| **3** | **Recuperación de Contraseñas** | Tokens criptográficos de un solo uso (1 hora). Flujo seguro con anti-enumeración de correos. | `POST /api/v1/auth/password/reset/request`, `POST .../confirm` | `pages/auth/PasswordResetRequest.tsx`, `PasswordResetConfirm.tsx` | `test_password_recovery.py` (5 tests) | Verificado en local | `VERIFIED` | El envío de correos opera mediante log/consola en dev; requiere servidor SMTP/SendGrid en prod. |
| **4** | **Aislamiento Multi-Inquilino (Multi-Tenancy)** | Filtro `institution_id` obligatorio en ORM. `OrganizationalScope` evalúa jerarquía DANE. | Middleware y dependencias en `api/deps.py` | `context/AuthContext.tsx` (inyección de tenant) | `test_authorization.py`, `test_guardian_tenant_isolation.py` | Validado con múltiples instituciones | `VERIFIED` | No utiliza Row Level Security (RLS) en Postgres; el aislamiento reside en capa ORM/código. |
| **5** | **Anti-IDOR & Blind 404** | Accesos no autorizados o fuera de tenant devuelven 404 Not Found en lugar de 403 Forbidden. | Decoradores y servicios en `backend/app/services/` | Manejo reactivo de 404 en componentes | `test_teacher_academic_scope.py`, `test_identity_family_lifecycle.py` | Blind 404 verificado en pruebas | `VERIFIED` | Implementado sistemáticamente en endpoints de estudiantes, grupos, notas y tareas. |
| **6** | **Catálogo DANE / DUE** | Ingesta, caché local y sincronización de entidades territoriales, instituciones y sedes. | `/api/v1/institutions/dane/...`, `/api/v1/institutions/search` | `pages/admin/InstitutionsView.tsx` | `test_official_dane_resolution.py`, `test_national_catalog_*.py` (62 tests) | Verificado con dataset oficial | `VERIFIED` | Ingesta masiva requiere subida de archivos CSV oficiales del MEN/DANE. |
| **7** | **Aprovisionamiento de Rectores** | Invitaciones criptográficas seguras, asignación formal a institución y auto-activación. | `POST /api/v1/institutions/{id}/invite-rector` | Modal en `InstitutionsView.tsx` | `test_rbac_governance_and_rector_invitation.py` | Validado en runtime | `VERIFIED` | Un solo rector activo simultáneamente por establecimiento; requiere flujo de revocación/sucesión. |
| **8** | **Sucesión de Rectoría** | Revocación controlada de credenciales del rector saliente y apertura de nueva invitación. | `POST /api/v1/institutions/{id}/rector/revoke` | Botón en `InstitutionsView.tsx` | `test_rector_succession.py` (10 tests) | Verificado | `VERIFIED` | Restringido a `superadmin` y `national_admin`. |
| **9** | **Años Lectivos y Períodos** | Apertura de calendario escolar, configuración de fechas y división en 3 o 4 períodos. | `/api/v1/academic-years`, `/periods` | `pages/academic/AcademicYearsView.tsx` | `test_academic_api.py` | Verificado | `VERIFIED` | No permite solapamiento de fechas dentro del mismo colegio. |
| **10** | **Padrón de Estudiantes (SIMAT)** | Registro de fichas civiles, asignación de código SIMAT, estado (`ACTIVE`, `TRANSFERRED`). | `/api/v1/students` | `pages/academic/StudentsView.tsx` | `test_academic_api.py`, `test_identity_family_lifecycle.py` | Verificado en pantalla | `VERIFIED` | Código SIMAT es validado por unicidad dentro del colegio. |
| **11** | **Cuentas de Estudiantes** | Creación bajo demanda de credenciales de acceso para estudiantes ya registrados en SIMAT. | `POST /api/v1/students/{id}/account/provision`, `.../status` | Modales en `StudentsView.tsx` | `test_identity_family_lifecycle.py` | Validado | `VERIFIED` | El toggle a inactivo revoca de inmediato la sesión (JTI blacklist). |
| **12** | **Padrón de Acudientes Civiles** | Registro de familiares civiles desacoplados de credenciales (`OPEN-DECISION-3A-01`). | `/api/v1/guardians` | `pages/academic/GuardiansView.tsx` | `test_identity_family_lifecycle.py` | Verificado | `VERIFIED` | Un acudiente puede existir sin cuenta de usuario hasta que se active. |
| **13** | **Vinculación Familiar (N:M)** | Asociación bidireccional entre estudiantes y acudientes con tipo de parentesco y responsable legal. | `POST /api/v1/students/{id}/guardians`, `POST /guardians/{id}/students` | Tablas de vinculación en vistas de Estudiantes y Acudientes | `test_identity_family_lifecycle.py` | Verificado | `VERIFIED` | Permite múltiples acudientes por estudiante y múltiples hijos por acudiente. |
| **14** | **Auto-Onboarding de Acudientes** | Activación pública mediante documento de identidad y correo validado contra ficha civil. | `POST /api/v1/auth/guardians/request-activation`, `accept-activation` | Formulario público de registro de familias | `test_guardian_onboarding.py` (8 tests) | Verificado en local | `VERIFIED` | Requiere que el colegio haya registrado previamente la ficha civil con el correo exacto. |
| **15** | **Gestión de Docentes** | Registro en planta, número de documento, título profesional y cuenta institucional. | `/api/v1/teachers` | `pages/academic/TeachersView.tsx` | `test_teacher_account_provisioning.py` (9 tests) | Verificado | `VERIFIED` | Incluye entrega de credenciales segura y modal de copia de token. |
| **16** | **Asignación Académica** | Vinculación ternaria de Docente + Asignatura + Grupo en Año Lectivo con intensidad horaria. | `/api/v1/academic-assignments` | `pages/academic/AcademicAssignmentsView.tsx` | `test_enrollments_and_assignments.py` | Verificado | `VERIFIED` | Delimita de manera estricta el ámbito de acceso (*Teacher Academic Scope*). |
| **17** | **Grupos y Salones** | Definición de cursos (ej. 10-A, 6-1), jornada (Mañana, Tarde, Única), sede y capacidad. | `/api/v1/groups` | `pages/academic/GroupsView.tsx` | `test_groups_and_actors_models.py` | Verificado | `VERIFIED` | Control estricto de sobrecupo al matricular. |
| **18** | **Libro de Matrículas** | Vinculación del estudiante al grupo en el año lectivo activo (`status=ACTIVE`). | `/api/v1/enrollments` | `pages/academic/EnrollmentsView.tsx` | `test_enrollments_and_assignments.py` | Verificado | `VERIFIED` | Impide doble matrícula activa en el mismo año lectivo. |
| **19** | **Traslados Escolares** | Flujo de retiro o cambio de grupo/sede con registro de fecha y motivo justificado. | `/api/v1/transfers` | `pages/academic/TransfersView.tsx` | `test_academic_api.py` | Verificado | `VERIFIED` | Preserva el historial académico previo al traslado. |
| **20** | **Actividades Académicas (Docente)** | Creación, borrador (`DRAFT`), publicación (`PUBLISHED`), edición y cierre de tareas/talleres. | `POST/PATCH/DELETE /api/v1/teacher/activities` | `pages/teacher/TeacherActivitiesView.tsx` | `test_teacher_portal_api.py`, `test_activity_resources_and_storage.py` | Verificado en pantalla | `VERIFIED` | Solo permite edición en estado `DRAFT`. Persistencia física multi-sesión aprobada. |
| **21** | **Entregas de Estudiantes (Submissions)** | Tipos `TEXT`, `FILE`, `TEXT_AND_FILE`. Borradores, entregas tardías UTC y devoluciones. | `/api/v1/student/activities/{id}/submission/...`, `/api/v1/teacher/...` | `StudentTaskDetailModal.tsx`, `TeacherActivitiesView.tsx` | `test_student_submissions_api.py` (10 tests) | Verificado en 8000/3000 | `VERIFIED` | Archivos adjuntos almacenados localmente; máximo 3 archivos de hasta 10 MB por entrega. |
| **22** | **Almacenamiento de Archivos** | Validación de Magic Bytes, anti-path traversal, estructura particionada por institución. | Servicio de almacenamiento interno | Modales de carga y descarga | `test_activity_resources_and_storage.py` | Verificado en disco | `VERIFIED` | Almacenamiento local en disco; requiere migración a S3/MinIO para producción. |
| **23** | **Planilla de Asistencia Diaria** | Registro por fecha y estudiante (`PRESENT`, `ABSENT`, `JUSTIFIED`, `LATE`). | `/api/v1/teacher/groups/{id}/attendance` | `pages/teacher/TeacherAttendanceView.tsx` | `test_teacher_portal_api.py` | Verificado | `VERIFIED` | Permite actualización en bloque y cálculo de porcentaje acumulado de ausencias. |
| **24** | **Planeación Curricular** | Programación pedagógica de unidades, estándares, competencias y metodologías. | `/api/v1/teacher/planning` | `pages/teacher/TeacherPlanningView.tsx` | `test_teacher_portal_api.py` | Verificado | `VERIFIED` | Permite edición y borrado por parte del docente titular de la asignación. |
| **25** | **Sistema SIEE (Decreto 1290)** | Configuración institucional de escalas (1.00-5.00), notas aprobatorias y topes de nivelación. | `/api/v1/siee-policies` | `pages/academic/DirectiveEvaluationManagementView.tsx` | `test_siee_and_evaluations_domain_services.py`, `test_siee_and_evaluations_api.py` | Verificado en runtime | `VERIFIED` | Mapeo a escalas nacionales *Bajo, Básico, Alto, Superior*. Versiones inmutables. |
| **26** | **Planilla de Notas y Calificaciones** | Cálculo automático del promedio de actividades (`calculated_score`) y ajuste docente. | `/api/v1/evaluation-grades/period-sheet` | `pages/teacher/TeacherSieeEvaluationView.tsx` | `test_siee_and_evaluations_api.py` | Verificado | `VERIFIED` | Exige justificación obligatoria (`adjustment_reason`) si la nota final difiere del cálculo. |
| **27** | **Nivelaciones y Recuperaciones** | Examen de recuperación con tope SIEE (`recovery_grade_cap`, def. 3.00) y nota original inmutable. | `/api/v1/evaluation-grades/recovery` | Modal en `TeacherSieeEvaluationView.tsx` | `test_siee_and_evaluations_domain_services.py` | Verificado | `VERIFIED` | Cumple Decreto 1290: la nota anterior queda registrada históricamente. |
| **28** | **Cierre y Apertura de Período** | Bloqueo inmutable de planillas al cerrar período (`is_locked=True`). Reapertura auditada. | `POST /api/v1/evaluation-grades/periods/{id}/close`, `.../unlock` | Controles en `DirectiveEvaluationManagementView.tsx` | `test_siee_and_evaluations_api.py` | Verificado | `VERIFIED` | Cierre bloquea mutaciones; reapertura requiere permiso directivo y justificación. |
| **29** | **Boletines de Calificaciones** | Boletines periódicos, acumulativos anuales y sábanas de notas con puesto en el grupo. | `/api/v1/evaluation-grades/report-card/...`, `.../consolidation-matrix` | `DirectiveEvaluationManagementView.tsx` (visores) | `test_siee_and_evaluations_api.py`, `OfficialReportCard.test.tsx` | Verificado en frontend | `VERIFIED` | Visualización en pantalla estructurada y JSON; exportación a PDF en papel pendiente. |
| **30** | **Promoción Escolar y Actas** | Algoritmo SIEE de fin de año: materias reprobadas, inasistencias, aprobación y graduación. | `/api/v1/academic-promotions/preview`, `.../commit` | Pestaña de Promoción en `DirectiveEvaluationManagementView.tsx` | `test_academic_promotion_service_preview_and_commit` | Verificado | `VERIFIED` | Simulación previa y confirmación transaccional con número de acta oficial. |
| **31** | **Comunicaciones Institucionales** | Circulares, directrices con segmentación por sede/grado/grupo y vigencia temporal. | `/api/v1/communications` | Vistas en `/student` y `/guardian` | `test_institutional_communications_api.py` | Verificado en portales | `VERIFIED` | Portales de estudiante y acudiente consumen circulares; consola de redacción directiva en desarrollo. |
| **32** | **Acuse de Recibo Digital** | Firma electrónica de confirmación de lectura para estudiantes y acudientes. | `POST /api/v1/communications/{id}/acknowledge` | Botón interactivo con sello en portales | `test_institutional_communications_api.py` | Verificado | `VERIFIED` | Registra estampa de tiempo UTC, usuario firmante y dirección IP. |
| **33** | **Noticias / Periódico Escolar** | Publicaciones pedagógicas y comunitarias por categorías (Académico, Cultural, Deportivo). | `/api/v1/news` | Vistas en `/student`, `/guardian`, `/teacher` | `test_institutional_news_api.py` | Verificado | `VERIFIED` | Filtrado automático de noticias expiradas o en borrador para perfiles públicos. |
| **34** | **Observador del Estudiante (L.1620)** | Anotaciones de convivencia Tipos I, II y III, descargos del alumno y acuerdos formativos. | `/api/v1/incidents` | Vistas de convivencia en portales | `test_coexistence_incidents_api.py` | Verificado | `VERIFIED` | Cumple estrictamente la Ley 1620 de 2013 y Decreto 1965 de 2013; visibilidad protegida por parentesco. |
| **35** | **Clases Virtuales (BigBlueButton)** | Creación de salas, cálculo criptográfico de URLs firmadas SHA-1/256 y control de acceso. | `/api/v1/virtual-classrooms` | `pages/virtual-classrooms/VirtualClassroomsView.tsx` | `test_meeting_provider.py`, `test_virtual_classroom_*.py` (25 tests) | Verificado con Mock | `READY WITH CONDITIONS` | Software completo y validado; **requiere comisionamiento de servidor físico BigBlueButton**. |
| **36** | **Telemetría de Videoclases** | Registro de ingresos, salidas, duración en segundos y lista de participantes. | `/api/v1/virtual-classrooms/{id}/attendances`, `/leave` | Modal de Asistencias en `VirtualClassroomsView.tsx` | `test_virtual_classroom_services.py` | Verificado | `READY WITH CONDITIONS` | Operativo con Mock; requiere integración con webhooks de BigBlueButton en vivo. |
| **37** | **Grabaciones de Clases** | Sincronización desde el proveedor, publicación controlada y reproducción en portales. | `/api/v1/recordings` | Pestaña de Grabaciones en `VirtualClassroomsView.tsx` y modal de estudiante | `test_virtual_classroom_services.py` | Verificado | `READY WITH CONDITIONS` | Docente controla si la grabación es pública para los alumnos; requiere almacenamiento BBB. |
| **38** | **Auditoría de Seguridad** | Registro inmutable de eventos con censura recursiva de contraseñas y tokens (`[REDACTED]`). | Servicio interno en PostgreSQL | No expuesta en frontend general (auditoría forense interna) | `test_authorization.py`, `test_auth_service.py` | Verificado en tabla `audit_logs` | `VERIFIED` | Tabla optimizada con índices en `event_type`, `actor_id`, `institution_id` y `occurred_at`. |
| **39** | **Analítica Territorial** | Tableros agregados por departamento, municipio e institución con conteo de matriculados. | `/api/v1/analytics/territorial` | `pages/analytics/TerritorialAnalyticsView.tsx` | `test_territorial_analytics.py` (4 tests) | Verificado en pantalla | `VERIFIED` | Diseñado para MEN y Secretarías de Educación; sin exposición de datos personales de alumnos. |
| **40** | **Portales Especializados (8)** | Espacios adaptados para SuperAdmin, MEN, Territorio, Rector, Coordinador, Docente, Estudiante, Acudiente. | Endpoints dedicados (`/teacher-portal`, `/student-portal`, `/guardian-portal`) | Vistas dedicadas y enrutador condicional | Suites de integración de portales | Verificado en runtime | `VERIFIED` | Redirección contextual al iniciar sesión según rol principal del usuario. |

---

## 3. Matriz Funcional Rol por Rol

### 3.1 SUPER_ADMIN (Nivel 100 — Administrador Técnico Global)
- **Autenticación:** Credenciales de máxima seguridad, Argon2id, soporte de CLI para primer arranque (`python -m app.cli.create_superadmin`).
- **Permisos Granulares:** Comodín universal `*` / `*:*`.
- **Módulos Disponibles:** `/admin/institutions`, `/dashboard`, `/analytics`, `/academic`, `/virtual-classrooms`.
- **Operaciones Permitidas:**
  - Crear, editar e incorporar instituciones educativas en el catálogo nacional.
  - Generar y revocar invitaciones de Rectoría.
  - Ejecutar revocación de rectores y sucesión directiva.
  - Consultar auditoría inmutable global (`audit_logs`).
  - Gestionar configuración técnica del sistema y endpoints de salud (`/health`, `/ready`).
- **Operaciones Restringidas:** No tiene restricciones técnicas. Su uso está regulado por políticas de ética y custodia técnica.
- **Fronteras Multi-Tenant:** Alcance global (`is_national = True`); puede operar e inspeccionar cualquier inquilino del país.
- **Comportamiento de Auditoría:** Todas sus acciones generan eventos de nivel `SECURITY` o `INFO` con registro de IP y User-Agent.

### 3.2 NATIONAL_ADMIN (Nivel 90 — Funcionario MEN)
- **Autenticación:** Usuario corporativo institucional del Ministerio de Educación Nacional.
- **Permisos Granulares:** Lectura nacional, analítica territorial, gestión de rectores, catálogo oficial DANE/DUE.
- **Módulos Disponibles:** `/analytics`, `/admin/institutions`, `/dashboard`.
- **Operaciones Permitidas:**
  - Inspeccionar métricas y cobertura escolar de los 32 departamentos y 1.100+ municipios.
  - Consultar directorio de colegios y sedes del país.
  - Emitir y revocar nombramientos de rectores oficiales.
  - Auditar consolidaciones académicas y de permanencia escolar.
- **Operaciones Restringidas:** No puede modificar notas de estudiantes, no puede redactar actividades docentes ni intervenir en la convivencia interna del colegio.
- **Fronteras Multi-Tenant:** Alcance nacional unificado; visibilidad transversal de sólo lectura sobre instituciones.
- **Comportamiento de Auditoría:** Consultas y emisiones quedan registradas bajo `actor_id` y `correlation_id`.

### 3.3 TERRITORIAL_ADMIN (Nivel 80 — Secretaría de Educación Departamental / Municipal)
- **Autenticación:** Usuario de la Entidad Territorial Certificada (ETC).
- **Permisos Granulares:** Lectura y analítica acotada a su jurisdicción DANE (`department_id` o `municipality_id`).
- **Módulos Disponibles:** `/analytics/territorial`, `/dashboard`.
- **Operaciones Permitidas:**
  - Monitorear indicadores de cobertura, matrícula y capacidad de las instituciones de su departamento/municipio.
  - Consultar distribución de estudiantes por sedes y zonas (urbana/rural).
- **Operaciones Restringidas:** No puede acceder a instituciones de otros departamentos ni alterar datos académicos internos.
- **Fronteras Multi-Tenant:** Confinado estrictamente a su código DANE departamental o municipal (`scope_contains`).
- **Comportamiento de Auditoría:** Intentos de consulta fuera de su territorio son denegados y auditados como `user.access_denied`.

### 3.4 RECTOR / INSTITUTION_ADMIN (Nivel 70 — Rector de Colegio Oficial)
- **Autenticación:** Cuenta institucional unificada ligada al código DANE de la institución.
- **Permisos Granulares:** Administración integral del colegio: `academic:*`, `enrollments:*`, `teachers:*`, `students:*`, `guardians:*`, `evaluations:*`, `communications:*`.
- **Módulos Disponibles:** `/academic` (completo), `/virtual-classrooms`, `/dashboard`.
- **Operaciones Permitidas:**
  - Apertura y cierre de años lectivos y períodos académicos.
  - Aprovisionamiento y administración de la planta docente del colegio.
  - Registro de matrículas SIMAT, aprobación de traslados y asignación de grupos.
  - Parametrización del Sistema Institucional de Evaluación (SIEE) de la institución.
  - Cierre oficial de períodos y reapertura justificada de planillas de calificaciones.
  - Simulación y consolidación formal del acta de promoción escolar y graduación.
  - Programación y supervisión de aulas virtuales institucionales.
- **Operaciones Restringidas:** Confinado estrictamente a su institución (`institution_id`). No puede ver ni modificar datos de otros colegios.
- **Fronteras Multi-Tenant:** Frontera rígida; cualquier acceso fuera de su colegio devuelve Blind 404.
- **Comportamiento de Auditoría:** Cierres de período, aperturas y promociones emiten logs críticos con número de acta y justificación.

### 3.5 ACADEMIC_COORDINATOR (Nivel 60 — Coordinador Académico o de Convivencia)
- **Autenticación:** Cuenta de coordinador asociada a la institución.
- **Permisos Granulares:** `academic:read`, `academic:update`, `evaluations:read`, `evaluations:update`, `incidents:*`, `communications:create`.
- **Módulos Disponibles:** `/academic/students`, `/academic/teachers`, `/academic/groups`, `/academic/assignments`, `/academic/evaluations`, `/virtual-classrooms`.
- **Operaciones Permitidas:**
  - Construcción de asignaciones académicas y horarios docentes.
  - Supervisión de planillas de calificaciones y generación de boletines.
  - Gestión integral de situaciones de convivencia escolar (Ley 1620) y seguimiento de compromisos.
  - Monitoreo de inasistencias por grupo y grado.
- **Operaciones Restringidas:** No puede revocar rectores ni alterar políticas SIEE fundamentales sin aval de Rectoría.
- **Fronteras Multi-Tenant:** Restringido a su institución educativa.
- **Comportamiento de Auditoría:** Registro de incidencias y seguimientos queda firmado por el coordinador actuante.

### 3.6 TEACHER (Nivel 50 — Docente de Aula)
- **Autenticación:** Cuenta institucional individual con rol `teacher`.
- **Permisos Granulares:** `teacher_portal:*`, `activities:*`, `attendance:create`, `grades:create`, `submissions:read`, `submissions:return`, `virtual_classrooms:join`.
- **Módulos Disponibles:** `/teacher` (Dashboard, Asignaturas, Mis Grupos, Actividades, Calificaciones SIEE, Asistencia, Planeación, Convivencia, Periódico).
- **Operaciones Permitidas:**
  - Crear, editar (borrador), publicar y cerrar actividades académicas de sus asignaturas.
  - Revisar entregas de estudiantes, descargar evidencias, registrar observaciones y devolver tareas para corrección (`RETURNED`).
  - Calificar actividades individuales y asentar notas de período en la planilla SIEE.
  - Asignar calificaciones de nivelación/recuperación sujetas al tope institucional.
  - Tomar asistencia diaria de sus salones asignados.
  - Registrar observaciones y descargos formativos en el Observador del Estudiante.
  - Iniciar o unirse a videoclases de sus grupos como Moderador (`MODERATOR`).
- **Operaciones Restringidas:**
  - **Restricción de Alcance Docente (*Academic Scope*):** Solo puede ver y calificar estudiantes pertenecientes a los grupos y materias formalmente asignados en su carga académica.
  - No puede alterar notas de períodos formalmente cerrados por Rectoría.
- **Fronteras Multi-Tenant:** Doble contención: Confinado a su institución y confinado a su asignación académica (*Group + Subject*).
- **Comportamiento de Auditoría:** Asentamiento de notas, devoluciones y modificaciones de notas calculadas registran autoría y justificación.

### 3.7 STUDENT (Nivel 20 — Estudiante Matriculado)
- **Autenticación:** Cuenta personal ligada a su ficha de matrícula SIMAT (`student.user_id = user.id`).
- **Permisos Granulares:** `student_portal:*`, `submissions:create`, `communications:acknowledge`, `virtual_classrooms:join`.
- **Módulos Disponibles:** `/student` (Dashboard, Mis Materias, Tareas y Entregas, Calificaciones y Boletines, Asistencias, Clases en Vivo, Circulares, Noticias, Mi Observador).
- **Operaciones Permitidas:**
  - Consultar horario y materias en las que se encuentra matriculado.
  - Cargar borradores y presentar entregas formales de tareas (`TEXT`, `FILE` o mixtas).
  - Reintentar entregas de tareas devueltas por el profesor con contador de intentos.
  - Consultar calificaciones parciales, notas de período y boletines oficiales emitidos.
  - Firmar acuses de recibo digital de circulares institucionales obligatorias.
  - Ingresar a clases virtuales sincrónicas en calidad de Asistente (`VIEWER`).
  - Consultar sus anotaciones formativas registradas en el Observador del Estudiante.
- **Operaciones Restringidas:**
  - No puede ver notas, tareas ni observador de otros compañeros.
  - No puede ingresar a videoclases de grupos ajenos a su matrícula (bloqueo SIMAT).
  - No puede subir archivos ejecutables o que excedan 10 MB.
- **Fronteras Multi-Tenant:** Aislamiento absoluto por su identificador de estudiante y grupo matriculado.
- **Comportamiento de Auditoría:** Entregas, firmas de circulares y conexiones a clase quedan grabadas con IP y estampa de tiempo UTC.

### 3.8 GUARDIAN (Nivel 10 — Acudiente / Padre de Familia)
- **Autenticación:** Cuenta personal asociada civilmente a uno o más estudiantes del colegio.
- **Permisos Granulares:** `guardian_portal:*`, `communications:acknowledge`.
- **Módulos Disponibles:** `/guardian` (Dashboard familiar, Selector dinámico de hijos, Tareas del hijo, Boletines y Notas, Asistencias, Circulares familiares, Noticias, Observador del hijo).
- **Operaciones Permitidas:**
  - Conmutar entre los perfiles de sus distintos hijos matriculados mediante selector dinámico.
  - Monitorear el estado de cumplimiento de tareas escolares y calificaciones de cada hijo.
  - Revisar porcentaje de asistencia y alertas por inasistencias injustificadas.
  - Leer y firmar acuses de recibo de circulares dirigidas a las familias.
  - Consultar el Observador de Convivencia de sus hijos (anotaciones Tipos I, II y III, compromisos pedagógicos).
  - Consultar grabaciones de clases virtuales publicadas de sus acudidos.
- **Operaciones Restringidas:**
  - **Filtro Anti-IDOR Estricto:** Cualquier intento de consultar la información de un alumno que no esté civilmente vinculado en la tabla `student_guardians` produce un **Blind 404 (Not Found)** inmediato.
  - No puede calificar, no puede enviar tareas en nombre del estudiante y no puede acceder a clases sincrónicas en vivo con rol de moderador.
- **Fronteras Multi-Tenant:** Triple barrera: Inquilino del colegio + Vínculo familiar activo + Estado de cuenta vigente.
- **Comportamiento de Auditoría:** Consultas y firmas parentales se registran como evidencia ante eventuales requerimientos del Comité de Convivencia o Bienestar Familiar (ICBF).
