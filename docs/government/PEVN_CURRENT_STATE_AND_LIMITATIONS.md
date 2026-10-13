# PEVN — MATRIZ DE ESTADO ACTUAL Y REGISTRO DE LIMITACIONES
## EVALUACIÓN TRANSPARENTE DE CAPACIDADES, DEPENDENCIAS Y BRECHAS (DOC-01)

**Destinatarios:** Comités Evaluadores Técnicos, Auditores de Sistemas y Directores de Tecnología Gubernamentales  
**Marco de Gobernanza:** AI Software Factory v1.2 — Transparent Engineering Standards  
**Fecha:** 13 de Octubre de 2026 (Actualización Consolidada)  
**Carácter:** Read-Only Audit Assessment  

---

## 1. Declaración de Principios de Transparencia

> [!IMPORTANT]
> **POLÍTICA DE TRANSPARENCIA RADICAL:**
> Ninguna limitación técnica u operativa se maquilla ni se oculta en este documento. El valor fundamental de PEVN ante las autoridades del Estado colombiano radica en su **fidelidad técnica y honestidad arquitectónica**. Conocer con exactitud lo que está listo, lo que depende de infraestructura externa y lo que requiere decisiones institucionales es la única base legítima para planificar un despliegue gubernamental exitoso.

---

## 2. Matriz Maestra de Estado Actual y Dependencias

A continuación se auditan las capacidades del sistema, clasificadas bajo los **5 estados canónicos estandarizados**:
1. `IMPLEMENTED — VERIFIED`
2. `IMPLEMENTED — MANUAL ACCEPTANCE PENDING`
3. `PARTIALLY IMPLEMENTED`
4. `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT`
5. `PROPOSED / NOT YET IMPLEMENTED`

| # | Capacidad del Sistema | Estado Actual en el Repositorio | Evidencia en Código / Tests / Docs | Estado Canónico Oficial | Dependencia Externa de Infraestructura | Dependencia Institucional / Legal |
| :-: | :--- | :--- | :--- | :---: | :--- | :--- |
| **1** | **Autenticación (Authentication)** | Hashing Argon2id (64 MB), JWT efímero en memoria volátil de React, cookies HttpOnly rotativas y bloqueo por fuerza bruta. | `backend/app/core/security/password.py`, `backend/tests/test_tokens.py` (704 tests PASS) | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **2** | **Control de Acceso (RBAC 11 Roles)** | Permisos granulares `recurso:accion`, comodines, niveles 10 a 100 y contención de 11 roles (incluye `municipality_admin`). | `backend/app/services/authorization_service.py`, `backend/tests/test_authorization.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **3** | **Multi-Tenancy y Anti-IDOR** | Aislamiento lógico por `institution_id`, contención territorial DANE y respuesta `404 Not Found` (Blind 404) ante accesos cross-tenant. | `backend/app/api/deps.py`, `backend/tests/test_teacher_academic_scope.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **4** | **Catálogo DANE / DUE** | 18,031 Establecimientos Educativos y 51,521 Sedes físicas integradas con índices B-Tree e inspección forense. | `official_institution_catalog`, `official_campus_catalog`, `test_official_dane_resolution.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Actualización periódica con datos abiertos DANE |
| **5** | **Administrador Municipal** | Aprovisionamiento con token criptográfico, activación de cuenta y gobierno de rectores en su municipio. | `backend/app/api/v1/endpoints/municipality_admin.py`, `frontend/src/test/MunicipalityAdminInvitationUrl.test.tsx` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **6** | **Libro de Matrículas (Enrollment)** | Matrícula activa ligada al año lectivo, validación de código SIMAT y bloqueo estricto de cupos máximos por salón. | `backend/app/models/enrollment.py`, `backend/tests/test_enrollments_and_assignments.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **7** | **Gestión Académica (Academic Mgmt)** | Años escolares, períodos académicos, grados, grupos, salones por jornada y sedes físicas. | `backend/app/models/academic_year.py`, `backend/tests/test_academic_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **8** | **Gestión Docente (Teacher Mgmt)** | Padrón de docentes, asignaciones académicas (Docente + Materia + Grupo) y restricción estricta de visibilidad (*Teacher Scope*). | `backend/app/models/teacher.py`, `backend/tests/test_teacher_account_provisioning.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **9** | **Portal del Estudiante (Student Portal)** | Portal `/student`: Tareas, entregas, notas de período, asistencias, observador y circulares con datos del alumno autenticado. | `frontend/src/pages/student/`, `frontend/src/test/StudentPortal.test.tsx` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **10** | **Portal del Acudiente (Guardian Portal)** | Portal `/guardian`: Panel familiar con selector dinámico de hijos, seguimiento de tareas, asistencias, observador y circulares. | `frontend/src/pages/guardian/`, `frontend/src/test/GuardianPortal.test.tsx` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **11** | **Sistema SIEE (Decreto 1290/2009)** | Políticas autónomas (`SieePolicy`), notas híbridas con justificación obligatoria, nivelaciones con tope, cierre de período y promoción. | `backend/app/services/evaluation_service.py`, `backend/tests/test_siee_and_evaluations_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Parametrización de la política de cada colegio |
| **12** | **Control de Asistencia (Attendance)** | Planilla de asistencia diaria por grupo y fecha (`Presente`, `Ausente`, `Justificado`, `Retardo`) con persistencia multi-sesión. | `backend/app/models/academic_activity.py` (`DailyAttendance`), `test_teacher_portal_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **13** | **Actividades Académicas (Activities)** | Creación, edición en borrador (`DRAFT`), publicación y cierre de tareas escolares por materia y grupo asignado. | `frontend/src/pages/teacher/TeacherActivitiesView.tsx`, `backend/tests/test_teacher_activities_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **14** | **Entregas de Tareas (Submissions)** | Modalidades `TEXT`, `FILE`, `TEXT_AND_FILE`. Borradores, cálculo de tardanza UTC (`is_late`), devoluciones y reintentos versionados. | `backend/app/models/academic_activity.py`, `docs/reports/B3-H13_IMPLEMENTATION_REPORT.md` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **15** | **Planeación Curricular y Didáctica** | Módulo de unidades didácticas docentes, DBA y estándares articulados con actividades escolares. | `TeacherCurricularPlanningView.tsx`, `backend/tests/test_teacher_planning_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **16** | **Comunicaciones y Acuses de Recibo** | Circulares oficiales segmentadas y acuse de recibo electrónico con registro de fecha/hora UTC y dirección IP. | `backend/app/models/communication.py`, `backend/tests/test_institutional_communications_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **17** | **Convivencia Escolar (Ley 1620/2013)** | Observador del estudiante Tipos I, II y III, descargos del alumno, acuerdos pedagógicos, seguimiento y reserva legal estricta. | `backend/app/models/coexistence_incident.py`, `backend/tests/test_coexistence_incidents_api.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **18** | **Diagnóstico de Inquilinos (`/operations`)** | Consola para SuperAdmin y Administrador Nacional: inspección de salud, búsqueda DANE y conteos en vivo. | `frontend/src/pages/admin/TenantDiagnosticsView.tsx`, `test_tenant_diagnostics_search.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **19** | **Auditoría Inmutable (`audit_logs`)** | Registro estructurado en base de datos con censura automática y recursiva de datos sensibles (`[REDACTED]`). | `backend/app/audit/database_service.py`, `backend/app/models/audit_log.py` | `IMPLEMENTED — VERIFIED` | Ninguna | Ninguna |
| **20** | **Boletines en Pantalla Web** | Visualización reactiva e impresión estándar de boletines y sábanas de calificaciones. | `frontend/src/test/OfficialReportCard.test.tsx` | `IMPLEMENTED — MANUAL ACCEPTANCE PENDING` | Ninguna | Aprobación visual de formatos de boletín por la entidad |
| **21** | **Periódico Escolar** | Publicación de artículos pedagógicos y noticias segmentadas por categoría temática. | `frontend/src/test/TeacherCommunicationsAndNews.test.tsx` | `IMPLEMENTED — MANUAL ACCEPTANCE PENDING` | Ninguna | Validación de políticas editoriales institucionales |
| **22** | **Almacenamiento Local de Archivos** | Almacenamiento local particionado con detección de Magic Bytes (anti-ejecutables) y límite de 10 MB. | `backend/app/core/storage/service.py`, `test_activity_resources_and_storage.py` | `PARTIALLY IMPLEMENTED` | **Requiere bucket de objetos en la nube (S3 / MinIO) para despliegues multi-nodo.** | Ninguna |
| **23** | **Reportes Masivos en PDF en Lote** | Motor de generación individual probado; falta worker asíncrono para renderizado masivo de miles de boletines. | `docs/government/pdf/`, `scripts/generate_government_pdfs.py` | `PARTIALLY IMPLEMENTED` | Requiere worker Celery / Redis | Definición del membrete oficial ministerial |
| **24** | **Aulas Virtuales (BigBlueButton)** | Capa de software completa: `IMeetingProvider`, `BBBAdapter` (SHA-1/256), telemetría de conexión y grabaciones con Mock verificado. | `backend/app/core/meeting/bbb_adapter.py`, `backend/tests/test_meeting_provider.py` | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | **Requiere comisionamiento de servidor físico BigBlueButton y Coturn TURN en TCP 443.** | Ninguna |
| **25** | **Sincronización en Vivo con SIMAT** | Estructuras de datos y reglas de negocio compatibles con SIMAT; preparada para interoperabilidad. No sustituye al SIMAT. | `backend/app/models/enrollment.py`, `backend/app/models/student.py` | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Ninguna | **Convenio interadministrativo con MEN para enlace de Web Services / API.** |
| **26** | **Autenticación Ciudadana (Gov.co)** | Autenticación local Argon2id robusta. Sin integración activa con pasarela OIDC de Carpeta Ciudadana / Gov.co. | `backend/app/core/security/` | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Ninguna | **Definición de enlace con MinTIC para integración de Carpeta Ciudadana.** |
| **27** | **Mensajería SMS / WhatsApp Gateway** | Registro de comunicaciones en base de datos. Sin proveedor SMS o WhatsApp en vivo. | `backend/app/models/communication.py` | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Gateway SMS / WhatsApp Business API | Contratación de servicios de mensajería estatal |
| **28** | **Notificaciones Push en Tiempo Real** | Persistencia estructurada en base de datos. Sin WebSockets ni notificaciones Push móviles activas. | `backend/app/models/communication.py` | `PROPOSED / NOT YET IMPLEMENTED` | Requiere servidor WebPush / Firebase FCM | Ninguna |
| **29** | **Aplicación Móvil Nativa (App Store)** | Interfaz web responsiva con soporte PWA (`vite-plugin-pwa`). Sin aplicaciones nativas en tiendas. | `frontend/vite.config.ts` | `PROPOSED / NOT YET IMPLEMENTED` | Cuentas de desarrollador en Apple Store / Google Play | Definición institucional |

---

## 3. Clasificación de Brechas por Responsabilidad

### 3.1 Responsabilidad del Equipo de Desarrollo (Software)
- Implementar el adaptador de almacenamiento para la nube (`S3StorageService`).
- Desarrollar la cola asíncrona de generación masiva de boletines PDF para impresión oficial por lotes.
- Implementar el canal de WebSockets para notificaciones reactivas instantáneas.

### 3.2 Responsabilidad de la Entidad Pública Receptora (Infraestructura)
- Aprovisionamiento de 1 servidor dedicado Ubuntu 22.04 LTS (16 vCPU, 32 GB RAM, NVMe) para BigBlueButton en Fase 1.
- Aprovisionamiento de servidor Coturn (STUN/TURN en puerto TCP 443 con certificado TLS) para garantizar conectividad WebRTC en escuelas rurales con CGNAT.
- Asignación de credenciales de servidor de correo SMTP ministerial para notificaciones transaccionales.
- Aprovisionamiento de clúster Kubernetes y balanceador de carga en la nube gubernamental para fases 2 y 3.

### 3.3 Responsabilidad de Autoridades Gubernamentales (Gobernanza y Acuerdos)
- Suscripción de acuerdos interadministrativos para definir la interoperabilidad de datos con el SIMAT (MEN).
- Integración técnica con la pasarela única del Estado Gov.co / Carpeta Ciudadana (MinTIC).
- Aprobación formal de las directrices de Habeas Data institucional y retención documental escolar.
