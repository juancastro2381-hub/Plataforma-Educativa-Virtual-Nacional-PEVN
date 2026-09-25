# PEVN — MATRIZ DE ESTADO ACTUAL Y REGISTRO DE LIMITACIONES
## EVALUACIÓN TRANSPARENTE DE CAPACIDADES, DEPENDENCIAS Y BRECHAS (FASE 0.1)

**Destinatarios:** Comités Evaluadores Técnicos, Auditores de Sistemas y Directores de Tecnología Gubernamentales  
**Marco de Gobernanza:** AI Software Factory v1.2 — Transparent Engineering Standards  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Audit Assessment  

---

## 1. Declaración de Principios de Transparencia

> [!IMPORTANT]
> **POLÍTICA DE TRANSPARENCIA RADICAL:**
> Ninguna limitación técnica u operativa se maquilla ni se oculta en este documento. El valor fundamental de PEVN ante las autoridades del Estado colombiano radica en su **fidelidad técnica y honestidad arquitectónica**. Conocer con exactitud lo que está listo, lo que depende de infraestructura externa y lo que requiere decisiones institucionales es la única base legítima para planificar un despliegue gubernamental exitoso.

---

## 2. Matriz Maestra de Estado Actual y Dependencias

A continuación se auditan las **24 capacidades obligatorias del sistema**, mapeando su estado actual, su evidencia verificable en el repositorio y sus dependencias externas:

| # | Capacidad del Sistema | Estado Actual en el Repositorio | Evidencia en Código / Tests / Docs | Estado Canónico | Dependencia Externa de Infraestructura | Dependencia Institucional / Legal |
| :-: | :--- | :--- | :--- | :---: | :--- | :--- |
| **1** | **Autenticación (Authentication)** | Hashing Argon2id (64 MB), JWT efímero en memoria volátil de React, cookies HttpOnly rotativas y bloqueo por fuerza bruta. | `backend/app/core/security/password.py`, `backend/tests/test_password_hasher.py` (6 tests PASS) | `VERIFIED` | Ninguna | Ninguna |
| **2** | **Control de Acceso (RBAC)** | Permisos granulares `recurso:accion`, comodines (`*`, `users:*`), niveles 10 a 100 y prevención de escalamiento vertical. | `backend/app/services/authorization_service.py`, `backend/tests/test_authorization.py` | `VERIFIED` | Ninguna | Ninguna |
| **3** | **Multi-Tenancy y Anti-IDOR** | Aislamiento lógico por `institution_id`, contención territorial DANE y respuesta `404 Not Found` (Blind 404) ante accesos cross-tenant. | `backend/app/core/security/interfaces.py`, `backend/tests/test_teacher_academic_scope.py` | `VERIFIED` | Ninguna | Ninguna |
| **4** | **Catálogo DANE / DUE** | Ingesta estructurada, normalización y caché local de entidades territoriales, instituciones oficiales y sedes educativas. | `backend/app/models/official_catalog.py`, `backend/tests/test_official_dane_resolution.py` | `VERIFIED` | Ninguna | Actualización periódica con datos abiertos DANE |
| **5** | **Libro de Matrículas (Enrollment)** | Matrícula activa ligada al año lectivo, validación de código SIMAT y bloqueo estricto de cupos máximos por salón. | `backend/app/models/enrollment.py`, `backend/tests/test_enrollments_and_assignments.py` | `VERIFIED` | Ninguna | Ninguna |
| **6** | **Gestión Académica (Academic Mgmt)** | Años escolares, períodos académicos, grados, grupos, salones por jornada y sedes físicas. | `backend/app/models/academic_year.py`, `backend/tests/test_academic_api.py` | `VERIFIED` | Ninguna | Ninguna |
| **7** | **Gestión Docente (Teacher Mgmt)** | Padrón de docentes, asignaciones académicas (Docente + Materia + Grupo) y restricción estricta de visibilidad (*Teacher Scope*). | `backend/app/models/teacher.py`, `backend/tests/test_teacher_account_provisioning.py` | `VERIFIED` | Ninguna | Ninguna |
| **8** | **Portal del Estudiante (Student Portal)** | Portal `/student`: Tareas, entregas, notas de período, asistencias, observador y circulares con datos del alumno autenticado. | `frontend/src/pages/student/`, `backend/app/api/v1/endpoints/student_portal.py` | `VERIFIED` | Ninguna | Ninguna |
| **9** | **Portal del Acudiente (Guardian Portal)** | Portal `/guardian`: Panel familiar con selector dinámico de hijos, seguimiento de tareas, asistencias, observador y circulares. | `frontend/src/pages/guardian/`, `backend/tests/test_guardian_portal_api.py` | `VERIFIED` | Ninguna | Ninguna |
| **10** | **Sistema SIEE (Decreto 1290/2009)** | Políticas autónomas (`SieePolicy`), notas híbridas con justificación obligatoria, nivelaciones con tope, cierre de período y promoción anual. | `backend/app/services/evaluation_service.py`, `backend/tests/test_siee_and_evaluations_api.py` | `VERIFIED` | Ninguna | Parametrización de la política de cada colegio |
| **11** | **Control de Asistencia (Attendance)** | Planilla de asistencia diaria por grupo y fecha (`Presente`, `Ausente`, `Justificado`, `Retardo`) con persistencia multi-sesión. | `backend/app/models/academic_activity.py` (`DailyAttendance`), `test_teacher_portal_api.py` | `VERIFIED` | Ninguna | Ninguna |
| **12** | **Actividades Académicas (Activities)** | Creación, edición en borrador (`DRAFT`), publicación y cierre de tareas escolares por materia y grupo asignado. | `frontend/src/pages/teacher/TeacherActivitiesView.tsx`, `docs/reports/B3_IMPLEMENTATION_REPORT.md` | `VERIFIED` | Ninguna | Ninguna |
| **13** | **Entregas de Tareas (Submissions)** | Modalidades `TEXT`, `FILE`, `TEXT_AND_FILE`. Borradores, cálculo de tardanza UTC (`is_late`), devoluciones y reintentos versionados. | `backend/app/models/academic_activity.py`, `docs/reports/B3-H13_IMPLEMENTATION_REPORT.md` | `VERIFIED` | Ninguna | Ninguna |
| **14** | **Comunicaciones Institucionales** | Circulares oficiales segmentadas por sede/grado/rol y acuse de recibo digital con firma electrónica, fecha UTC e IP. | `backend/app/models/communication.py`, `backend/tests/test_institutional_communications_api.py` | `VERIFIED` | Ninguna | Ninguna |
| **15** | **Convivencia Escolar (Ley 1620/2013)** | Observador del estudiante Tipos I, II y III, descargos del alumno, acuerdos pedagógicos, seguimiento y reserva legal estricta. | `backend/app/models/coexistence_incident.py`, `backend/tests/test_coexistence_incidents_api.py` | `VERIFIED` | Ninguna | Ninguna |
| **16** | **Aulas Virtuales (Virtual Classrooms)** | Capa de software completa: `IMeetingProvider`, `BBBAdapter` (SHA-1/256), telemetría de conexión y grabaciones con Mock provider verificado. | `backend/app/core/meeting/bbb_adapter.py`, `backend/tests/test_meeting_provider.py` | `IMPLEMENTED / TESTED` | **Requiere comisionamiento de servidor físico BigBlueButton y Coturn TURN en TCP 443.** | Ninguna |
| **17** | **Almacenamiento de Archivos (Storage)** | Almacenamiento local particionado con detección de Magic Bytes (anti-ejecutables) y límite de 10 MB. | `backend/app/core/storage/service.py`, `backend/tests/test_activity_resources_and_storage.py` | `PARTIAL` | **Requiere bucket de objetos en la nube (S3 / MinIO) para despliegues multi-nodo.** | Ninguna |
| **18** | **Notificaciones en Tiempo Real** | Persistencia estructurada en base de datos. Sin WebSockets ni notificaciones Push móviles activas. | `backend/app/models/communication.py` | `NOT IMPLEMENTED` | Requiere servidor WebPush / Firebase FCM | Ninguna |
| **19** | **Pasarela de Correo (Email / SMTP)** | Flujos lógicos de reseteo probados; en desarrollo se imprimen tokens en consola de terminal. | `backend/app/services/auth_service.py`, `backend/tests/test_password_recovery.py` | `CONFIGURATION REQUIRED` | **Requiere servidor SMTP institucional o pasarela de correo gubernamental.** | Asignación de credenciales SMTP de la entidad |
| **20** | **Reportes en PDF (PDF Reports)** | Boletines y sábanas de notas se visualizan reactivamente en web y en JSON. Falta renderizado masivo en PDF imprimible. | `frontend/src/test/OfficialReportCard.test.tsx`, `pages/academic/...` | `PARTIAL` | Ninguna (requiere worker asíncrono en backend) | Definición del membrete oficial ministerial |
| **21** | **Interoperabilidad SIMAT (SIMAT API)** | Incorpora estructuras y reglas compatibles con el modelo de matrícula; arquitectónicamente preparada para interoperabilidad. No reemplaza al SIMAT. | `backend/app/models/enrollment.py`, `backend/app/models/student.py` | `ARCHITECTURALLY PREPARED` | Ninguna | **Convenio interinstitucional con MEN para enlace de Web Services / API.** |
| **22** | **Autenticación Única (SSO / Gov.co)** | Autenticación local Argon2id robusta. Sin integración activa con pasarela OIDC de Carpeta Ciudadana / Gov.co. | `backend/app/core/security/` | `NOT IMPLEMENTED` | Ninguna | **Definición de enlace con MinTIC para integración de Carpeta Ciudadana.** |
| **23** | **Escalabilidad Masiva (Scalability)** | Arquitectura diseñada para escalamiento horizontal; la capacidad efectiva a escala nacional deberá determinarse mediante pruebas de carga. | `docs/reports/PEVN_SCALABILITY_READINESS.md` | `ARCHITECTURALLY PREPARED` | **Requiere entorno de staging para ejecución de pruebas masivas con k6/Locust.** | Ninguna |
| **24** | **Infraestructura de Producción (Prod Infra)** | Entorno Docker local funcional. **No existen servidores físicos ni clústeres de producción desplegados actualmente.** | `docker-compose.yml`, `docs/reports/PEVN_INFRASTRUCTURE_READINESS.md` | `REQUIRES INFRASTRUCTURE` | **Aprovisionamiento de servidores en nube, Kubernetes, PgBouncer, WAF y DNS `.gov.co`.** | Asignación presupuestal y técnica por la entidad pública |

---

## 3. Clasificación de Brechas por Responsabilidad

### 3.1 Responsabilidad del Equipo de Desarrollo (Software)
- Implementar el adaptador de almacenamiento para la nube (`S3StorageService`).
- Desarrollar el motor de generación masiva de boletines PDF imprimibles con código QR (Fase 17).
- Actualizar los fixtures de mock heredados en 2 archivos de prueba de frontend (`vitest`).
- Integrar notificaciones en tiempo real (WebSockets / Push).

### 3.2 Responsabilidad de la Entidad Pública Receptora (Infraestructura)
- Aprovisionar los servidores físicos o instancias en nube para el backend, frontend, base de datos PostgreSQL y Redis.
- Desplegar el servidor físico dedicado para BigBlueButton (16 vCPU, 32 GB RAM) y el servidor Coturn TURN en TCP 443.
- Asignar y delegar los subdominios oficiales `.gov.co` con sus certificados SSL/TLS.
- Configurar el servidor de correo SMTP institucional para el envío de notificaciones y reseteo de claves.

### 3.3 Responsabilidad Jurídica e Institucional (Gobernanza)
- Formalizar los términos y autorizaciones de tratamiento de datos personales de menores de edad (Ley 1581/2012).
- Suscribir el convenio de donación / cesión técnica de derechos de uso del software al Estado colombiano.
- Gestionar ante el MEN la mesa técnica para la interoperabilidad en vivo con el sistema SIMAT.
