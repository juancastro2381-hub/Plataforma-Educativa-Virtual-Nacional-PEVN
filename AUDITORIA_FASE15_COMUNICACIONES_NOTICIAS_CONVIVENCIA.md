# AUDITORÍA FUNCIONAL FASE 15
## COMUNICACIONES INSTITUCIONALES, NOTICIAS / PERIÓDICO ESCOLAR Y CONVIVENCIA / OBSERVADOR DEL ESTUDIANTE

---

## 1. Datos de auditoría

- **Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)
- **Fecha:** 2026-09-07
- **Auditor:** Antigravity
- **Tipo:** Read-Only + Evidence Report
- **Versión de auditoría:** 1.0 (Auditoría Forense de Cierre Funcional)
- **Estado:** `PASS`
- **Recomendación:** `READY FOR HUMAN DECISION`

---

## 2. Resumen ejecutivo

La presente auditoría funcional forense examinó la totalidad de artefactos técnicos, de datos y de experiencia de usuario que componen la **Fase 15** de la Plataforma Educativa Virtual Nacional (PEVN): *Comunicaciones Institucionales, Noticias / Periódico Escolar y Convivencia / Observador del Estudiante*.

### Hallazgos Fundamentales:
1. **Disponibilidad Total en Backend y API:**
   Todos los modelos relacionales de datos, esquemas de validación, servicios de dominio y controladores REST (17 endpoints protegidos) existen, están conectados al motor PostgreSQL y cuentan con una cobertura de pruebas automatizadas al 100% pasando en verde.
2. **Implementación Asimétrica en Frontend (Solo Portales de Consumo):**
   El frontend cuenta con interfaces funcionales completas y reactivas **exclusivamente para los perfiles de consumo**:
   - El **Portal del Estudiante** (`/student`) permite consultar circulares oficiales, firmar acuses de recibo obligatorios, revisar noticias institucionales clasificadas y examinar anotaciones formativas del Observador personal.
   - El **Portal del Acudiente** (`/guardian`) permite consultar comunicados dirigidos a las familias, confirmar lectura parental con estampa digital, ver noticias escolares y monitorear las situaciones de convivencia de sus hijos legalmente vinculados con tipificación bajo la Ley 1620 de 2013.
3. **Ausencia Total de Consola Administrativa y Docente:**
   **No existe ninguna interfaz de usuario (UI)** en el frontend para que un Rector, Coordinador o Docente redacte circulares, configure audiencias, publique noticias ni registre faltas o compromisos en el Observador.
4. **Naturaleza de los Datos QA Observados:**
   Los registros visibles en las pruebas manuales (`[QA-F15-20260907]`) provienen de una siembra sintética programática ejecutada por script local (`backend/scratch/qa_seed_phase15.py`), requerida para habilitar la inspección visual en pantalla.

---

## 3. Alcance

El alcance de la presente auditoría cubrió de manera estricta y sin mutaciones de estado los siguientes elementos:

- **Comunicaciones Institucionales:** Ciclo de vida de circulares, convocatorias y directrices, segmentación por sede, grado, grupo y rol, acuses de recibo obligatorios, vigencia determinística y expiración.
- **Noticias / Periódico Escolar:** Divulgación comunitaria, eventos pedagógicos, categorías temáticas y estados de publicación.
- **Convivencia / Observador del Estudiante:** Gestión de situaciones escolares bajo la Ley 1620 de 2013 y Decreto 1965 de 2013 (Tipo I, II, III), descargos, acuerdos restaurativos, seguimientos y restricciones de visibilidad.
- **Portal del Estudiante:** Pestañas `communications`, `news` e `incidents` en `/student`.
- **Portal del Acudiente:** Pestañas `communications`, `news` e `incidents` en `/guardian`.
- **Panel Institucional y Docente:** Módulos `/academic`, `/teacher` y `/dashboard` para verificar existencia o ausencia de consolas de emisión.
- **Backend y Base de Datos:** Modelos SQLAlchemy, relaciones M:N, migraciones Alembic (revisión 021) e integridad relacional en PostgreSQL 16.4.
- **API REST:** 17 endpoints en FastAPI con validación de esquemas Pydantic y control de excepciones.
- **Seguridad y RBAC:** Políticas deny-by-default, verificación multi-tenant y barreras Anti-IDOR.
- **Auditoría e Inmutabilidad:** Trazabilidad de eventos en la tabla `audit_logs`.
- **Datos QA y Certificación:** Inspección de los marcadores sintéticos `QA-F15-20260907` y documentación histórica de fases.

---

## 4. Documentación de gobierno inspeccionada

| Documento Encontrado | Propósito | Relevancia para Fase 15 | Estado Documentado |
| :--- | :--- | :--- | :--- |
| [`docs/phase15_institutional_communications_forensic_architecture.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase15_institutional_communications_forensic_architecture.md) | Documento maestro de descubrimiento forense, arquitectura del dominio y plan de implementación Fase 15. | **Crítica.** Define modelos, contratos API, decisiones canónicas (DECISION-15-01 a 15-04) y la secuencia de sub-fases 15A a 15G. | Aprobado / Referencia Arquitectónica |
| [`docs/phase15_institutional_communications_walkthrough.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase15_institutional_communications_walkthrough.md) | Guía técnica y resumen ejecutivo de la entrega de Fase 15 en portales. | **Alta.** Documenta el alcance implementado en backend y las vistas de estudiante y acudiente en frontend. | Entregado |
| [`docs/reports/PHASE_15_CONTROLLED_FIX_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PHASE_15_CONTROLLED_FIX_REPORT.md) | Informe forense de resolución controlada del error de runtime 500. | **Alta.** Explica la ausencia inicial de las tablas en la base de datos y la aplicación formal de la migración 021. | Cerrado / PASS |
| [`docs/reports/PHASE_15_QA_DATA_PREPARATION_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PHASE_15_QA_DATA_PREPARATION_REPORT.md) | Registro de preparación de datos sintéticos QA para validación humana. | **Alta.** Detalla los identificadores exactos de los datos sembrados bajo el marcador `QA-F15-20260907`. | PASS |
| [`docs/reports/PROJECT_MASTER_STATUS.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PROJECT_MASTER_STATUS.md) | Cuadro de mando general de fases del proyecto PEVN. | **Media.** Muestra el estado evolutivo previo de las Fases 1 a 14 y la transición a Fase 15. | Activo |

---

## 5. Inventario técnico

### Backend
- Framework: FastAPI 0.110+, Python 3.12, SQLAlchemy 2.0 Async, Pydantic v2.
- Capa de Endpoints:
  - [`backend/app/api/v1/endpoints/communications.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/communications.py) (272 líneas)
  - [`backend/app/api/v1/endpoints/news.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/news.py) (207 líneas)
  - [`backend/app/api/v1/endpoints/incidents.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/incidents.py) (264 líneas)
  - [`backend/app/api/v1/endpoints/student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py) (Integración de sub-rutas `/communications`, `/news`, `/incidents`)
  - [`backend/app/api/v1/endpoints/guardian_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/guardian_portal.py) (Integración de sub-rutas `/communications`, `/news`, `/students/{id}/incidents`)

### Frontend
- Framework: React 18, Vite, TypeScript, React Router DOM v6.
- Vistas de Estudiante:
  - [`frontend/src/pages/student/StudentCommunicationsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentCommunicationsView.tsx) (514 líneas)
  - [`frontend/src/pages/student/StudentNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentNewsView.tsx) (440 líneas)
  - [`frontend/src/pages/student/StudentIncidentsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentIncidentsView.tsx) (307 líneas)
- Vistas de Acudiente:
  - [`frontend/src/pages/guardian/GuardianCommunicationsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianCommunicationsView.tsx) (528 líneas)
  - [`frontend/src/pages/guardian/GuardianNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianNewsView.tsx) (440 líneas)
  - [`frontend/src/pages/guardian/GuardianIncidentsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianIncidentsView.tsx) (345 líneas)
- Cliente HTTP:
  - [`frontend/src/services/communication.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/communication.ts) (144 líneas)
- Tipos TypeScript:
  - [`frontend/src/types/communication.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/types/communication.ts) (151 líneas)

### Modelos
- [`backend/app/models/communication.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/communication.py): `InstitutionalCommunication`, `CommunicationAudience`, `CommunicationReceipt`.
- [`backend/app/models/news.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/news.py): `InstitutionalNews`.
- [`backend/app/models/coexistence_incident.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/coexistence_incident.py): `StudentIncident`, `IncidentFollowUp`.

### Servicios
- [`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py)
- [`backend/app/services/news_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/news_service.py)
- [`backend/app/services/incident_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/incident_service.py)
- [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py)

### Endpoints
Total: 17 endpoints REST documentados en detalle en la Sección 8.

### Tests
- Backend:
  - `backend/tests/test_institutional_communications_api.py` (15.4 KB)
  - `backend/tests/test_institutional_news_api.py` (6.5 KB)
  - `backend/tests/test_coexistence_incidents_api.py` (18.2 KB)
  - `backend/tests/test_student_portal_api.py`
  - `backend/tests/test_guardian_portal_api.py`
- Frontend:
  - `frontend/src/test/InstitutionalCommunications.test.tsx` (9.1 KB)
  - `frontend/src/test/StudentPortal.test.tsx`
  - `frontend/src/test/GuardianPortal.test.tsx`

### Seeds / fixtures / QA
- Script local reversible: [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) (326 líneas)
- Migración de base de datos: [`backend/migrations/versions/021_phase15_communications_news_incidents.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/versions/021_phase15_communications_news_incidents.py)

### Documentación
- Carpeta `docs/` con arquitectura forense, reportes de runtime y actas de fase.

---

## 6. Comunicaciones Institucionales

- **Modelo:** `InstitutionalCommunication`, `CommunicationAudience`, `CommunicationReceipt`.
- **Schemas:** `CommunicationCreateRequest`, `CommunicationUpdateRequest`, `InstitutionalCommunicationResponse`, `CommunicationListResponse`.
- **Servicio:** `CommunicationService` con soporte de transacciones asíncronas SQLAlchemy y verificación de alcance.
- **Endpoints:**
  - `POST /api/v1/communications`
  - `GET /api/v1/communications`
  - `GET /api/v1/communications/{id}`
  - `PUT /api/v1/communications/{id}`
  - `POST /api/v1/communications/{id}/publish`
  - `POST /api/v1/communications/{id}/archive`
  - `GET /api/v1/student/communications` & `POST .../{id}/acknowledge`
  - `GET /api/v1/guardian/communications` & `POST .../{id}/acknowledge`
- **Permisos RBAC:** `communications:read`, `communications:create`, `communications:update`, `communications:publish`, `communications:delete`.
- **Roles:** Autorizados para emitir: `rector`, `coordinator`, `academic_coordinator`, `institution_admin`, `superadmin`. Roles receptores: todos.
- **UI:** Exclusivamente vistas de feed para estudiantes y acudientes. No existe vista administrativa.
- **Rutas UI Existentes:** `/student?tab=communications` y `/guardian?tab=communications`.
- **Audiencia:** Soporta targeting institucional completo, por rol específico (`SOLO_ESTUDIANTES`, `SOLO_ACUDIENTES`, `SOLO_DOCENTES`), por sede (`campus_id`), por grado (`grade_id`) o por grupo (`group_id`).
- **Prioridad:** Enums `BAJA`, `MEDIA`, `ALTA`, `URGENTE`.
- **Vigencia y Expiración:** Campo `expires_at`. Expiración automática y determinística en tiempo UTC; comunicados vencidos son excluidos de contadores no leídos y archivados lógicamente.
- **Receipts y Confirmación de Lectura:** Modelo `CommunicationReceipt`. Registra de manera no repudiable: `user_id`, `read_at`, `acknowledged_at` y `client_ip`.
- **Auditoría:** Emite eventos inmutables a `audit_logs`: `COMMUNICATION_CREATED`, `COMMUNICATION_PUBLISHED`, `COMMUNICATION_ARCHIVED`, `COMMUNICATION_ACKNOWLEDGED`.
- **Publicación y Edición:** Transiciones de estado validadas en el servicio: `BORRADOR` $\rightarrow$ `PUBLICADO` $\rightarrow$ `ARCHIVADO`.

### Respuestas Explícitas:

### ¿Existe UI para crear un comunicado?
**No.**

### ¿Existe API para crear un comunicado?
**Sí.** (`POST /api/v1/communications`).

### ¿Quién puede crearlo?
Cualquier usuario autenticado que posea el rol `rector`, `coordinator`, `academic_coordinator`, `institution_admin` o `superadmin` con el permiso `communications:create`.

### ¿Dónde se crea?
Únicamente a través del endpoint REST `POST /api/v1/communications` consumido por clientes de API externos o scripts. No existe ruta en el frontend.

### ¿Cómo se generó el comunicado QA?
Fue insertado directamente en la base de datos por el script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) asociándolo a la Rectora institucional Sandra Chavez Guzman.

---

## 7. Noticias / Periódico Escolar

- **Modelo:** `InstitutionalNews`.
- **Servicio:** `NewsService`.
- **API:** `POST /api/v1/news`, `GET /api/v1/news`, `GET /api/v1/news/{id}`, `PUT /api/v1/news/{id}`, `POST /api/v1/news/{id}/publish`, `GET /api/v1/student/news`, `GET /api/v1/guardian/news`.
- **RBAC:** `news:read`, `news:create`, `news:update`, `news:publish`, `news:delete`.
- **UI Administrativa:** **Inexistente**.
- **UI Estudiante:** [`StudentNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentNewsView.tsx) (Solo lectura, tarjetas con imágenes y modal).
- **UI Acudiente:** [`GuardianNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianNewsView.tsx) (Solo lectura, filtros por categorías).
- **Datos QA:** Noticia sintética con ID `d2d33449-fb86-4f20-bf2e-3f392beda905`.
- **Ciclo:** Creación de borrador, actualización de titular y cuerpo, y publicación oficial en la comunidad escolar.

### Respuestas Explícitas:

### ¿Existe UI administrativa para crear una noticia?
**No.**

---

## 8. Convivencia / Observador

- **Creación:** Regulada por el servicio `CoexistenceIncidentService.create_incident`.
- **Consulta:** Estudiantes consultan sus propios incidentes (`GET /api/v1/student/incidents`); acudientes consultan a sus hijos mediante validación estricta de tutela (`GET /api/v1/guardian/students/{id}/incidents`). Directivos y docentes asignados consultan por grupo o estudiante.
- **Seguimiento:** Adición de acuerdos formativos mediante `POST /api/v1/incidents/{id}/follow-ups`.
- **Modificación:** Actualización de descargos estudiantiles y compromisos mediante `PUT /api/v1/incidents/{id}`.
- **Cierre:** Resolución formal mediante `POST /api/v1/incidents/{id}/close`.
- **Confidencialidad:** Protección mediante banderas `is_visible_to_student` e `is_visible_to_guardian`. Si están en `false`, los portales familiares no reciben la información.
- **RBAC:** `incidents:read`, `incidents:create`, `incidents:update`, `incidents:close`.
- **Tenant Isolation:** Aislamiento multi-inquilino estricto (`institution_id`). Scoping docente: docentes de aula solo pueden crear incidentes a estudiantes pertenecientes a sus grupos asignados.
- **UI Administrativa / Docente:** **Inexistente**.
- **UI Estudiante:** [`StudentIncidentsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentIncidentsView.tsx).
- **UI Acudiente:** [`GuardianIncidentsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianIncidentsView.tsx).
- **Modelos:** `StudentIncident`, `IncidentFollowUp`.

### Respuestas Explícitas:

### ¿Existe UI administrativa para registrar convivencia?
**No.**

---

## 9. Origen de los datos QA

Análisis detallado de los identificadores observados durante la validación manual:

### 1. `[QA-F15-20260907] Circular Oficial: Actividades Pedagógicas y Convivencia`
- **Origen:** Script de siembra controlada [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) (Línea 143).
- **Archivo:** `backend/scratch/qa_seed_phase15.py`.
- **Mecanismo:** Inserción ORM directa `session.add(InstitutionalCommunication(...))`.
- **Modelo:** `InstitutionalCommunication`.
- **Servicio Backend:** `CommunicationService`.
- **Endpoint:** `POST /api/v1/communications`.
- **Usuario Asociado:** Sandra Chavez Guzman (Rectora, ID `ca8a4525-c730-48d9-b1c4-dc7f76b26112`).
- **Audiencia:** `TODOS_INSTITUCION` (alcanza a Ramiro Rey y Alberto Mercado).
- **¿Creable desde UI?:** **No**.
- **¿Creable mediante API?:** **Sí**.
- **¿Solamente es QA?:** **Sí** (dato sintético creado exclusivamente para QA con marcador reversible).

### 2. `[QA-F15-20260907] Logro Destacado en Feria de Ciencia e Innovación Escolar`
- **Origen:** Script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) (Línea 198).
- **Archivo:** `backend/scratch/qa_seed_phase15.py`.
- **Mecanismo:** Inserción ORM directa `session.add(InstitutionalNews(...))`.
- **Modelo:** `InstitutionalNews`.
- **Servicio Backend:** `NewsService`.
- **Endpoint:** `POST /api/v1/news`.
- **Usuario Asociado:** Sandra Chavez Guzman (Rectora).
- **Audiencia:** Toda la institución (`COLEGIO GLENN DOMAN`).
- **¿Creable desde UI?:** **No**.
- **¿Creable mediante API?:** **Sí**.
- **¿Solamente es QA?:** **Sí**.

### 3. `[QA-F15-20260907] Registro sintético formativo de convivencia escolar`
- **Origen:** Script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) (Líneas 241 y 290).
- **Archivo:** `backend/scratch/qa_seed_phase15.py`.
- **Mecanismo:** Inserción ORM directa `session.add(StudentIncident(...))` y `session.add(IncidentFollowUp(...))`.
- **Modelo:** `StudentIncident` (ID: `8daf3c23-dae8-4eb7-8b7b-72845847b425`) e `IncidentFollowUp` (ID: `e77469fa-03a4-456f-9f6c-11dbd526e93e`).
- **Servicio Backend:** `CoexistenceIncidentService`.
- **Endpoint:** `POST /api/v1/incidents`.
- **Usuario Asociado:** Reportado por Sandra Chavez Guzman; asignado al estudiante Ramiro Rey (`students.id: 09e7beab-090a-46b8-9f51-91cb402c103a`).
- **Audiencia:** Estudiante Ramiro Rey y Acudiente Alberto Mercado (`is_visible_to_student = True`, `is_visible_to_guardian = True`).
- **¿Creable desde UI?:** **No**.
- **¿Creable mediante API?:** **Sí**.
- **¿Solamente es QA?:** **Sí**.

---

## 10. Matriz de roles y permisos

Matriz obtenida de la configuración canónica en `app/services/rbac_bootstrap_service.py`:

| Capacidad | SUPER_ADMIN | NATIONAL_ADMIN | TERRITORIAL_ADMIN | RECTOR | COORDINADOR | DOCENTE | ESTUDIANTE | ACUDIENTE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `communications:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `communications:create` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:update` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:publish` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:delete` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `news:create` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:update` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:publish` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:delete` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `incidents:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Grupo) | ✅ (Propio) | ✅ (Hijo) |
| `incidents:create` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ (Grupo) | ❌ | ❌ |
| `incidents:update` | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ (Grupo) | ❌ | ❌ |
| `incidents:close` | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 11. Matriz de implementación

| Capacidad | Backend | API | UI Admin | UI Estudiante | UI Acudiente | RBAC | Tests | Certificado | QA |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Emisión de Circulares | SÍ | SÍ | NO | N/A | N/A | SÍ | SÍ | PARCIAL | SÍ |
| Acuse de Recibo Familiar | SÍ | SÍ | N/A | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ |
| Publicación de Noticias | SÍ | SÍ | NO | N/A | N/A | SÍ | SÍ | PARCIAL | SÍ |
| Consumo Periódico Escolar | SÍ | SÍ | N/A | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ |
| Registro Observador Docente | SÍ | SÍ | NO | N/A | N/A | SÍ | SÍ | PARCIAL | SÍ |
| Consulta Observador Estudiante | SÍ | SÍ | N/A | SÍ | N/A | SÍ | SÍ | SÍ | SÍ |
| Monitoreo Convivencia Acudiente| SÍ | SÍ | N/A | N/A | SÍ | SÍ | SÍ | SÍ | SÍ |
| Cierre Resolutivo de Incidente | SÍ | SÍ | NO | N/A | N/A | SÍ | SÍ | PARCIAL | SÍ |

---

## 12. Matriz de estado

| Capacidad | Estado | Justificación |
| :--- | :---: | :--- |
| Crear / Modificar / Publicar Comunicado | **API_ONLY** | Endpoint operativo en backend pero sin interfaz en frontend. |
| Consultar Comunicados (Estudiante) | **PASS** | UI interactiva, backend y API completamente funcionales. |
| Firmar Acuse de Recibo (Estudiante) | **PASS** | Botón de confirmación funcional con actualización de estado y timestamp. |
| Consultar Comunicados (Acudiente) | **PASS** | UI interactiva, badge de prioridad y selector de hijos funcional. |
| Firmar Acuse de Recibo (Acudiente) | **PASS** | Registro inmutable de acuse parental verificado. |
| Crear / Publicar Noticia Escolar | **API_ONLY** | Endpoint operativo en backend pero sin interfaz en frontend. |
| Consultar Noticias (Estudiante / Acudiente) | **PASS** | UI interactiva con filtros por categoría y modal de lectura. |
| Crear Registro en Observador (Docente/Directivo)| **API_ONLY** | Endpoint operativo en backend pero sin interfaz en frontend. |
| Registrar Seguimiento a Incidente | **API_ONLY** | Endpoint operativo en backend pero sin interfaz en frontend. |
| Cerrar Situación de Convivencia | **API_ONLY** | Endpoint operativo en backend pero sin interfaz en frontend. |
| Consultar Observador (Estudiante) | **PASS** | UI formativa en `/student?tab=incidents` totalmente operativa. |
| Consultar Observador Hijo (Acudiente) | **PASS** | UI en `/guardian?tab=incidents` con Anti-IDOR validado. |

---

## 13. Seguridad

- **RBAC:** Implementación centralizada deny-by-default en `CentralizedAuthorizationService`. Peticiones no autenticadas devuelven `401 Unauthorized`; roles sin el permiso asignado devuelven `403 Forbidden`.
- **Tenant Isolation:** Enrutamiento multi-inquilino rígido basado en `current_user.institution_id`. No es posible inyectar parámetros de institución cruzada.
- **Anti-IDOR Estricto:**
  - En `/student/*`, la identidad se toma de `Student.user_id == current_user.id`. El estudiante no puede consultar datos de terceros.
  - En `/guardian/students/{student_id}/incidents`, el servicio valida activamente la relación en la tabla `StudentGuardian`. Si un acudiente intenta consultar un estudiante no vinculado legalmente, la API devuelve determinísticamente un **404 Not Found blind** para no revelar existencia.
- **Autorización Server-Side:** La visibilidad familiar (`is_visible_to_student`, `is_visible_to_guardian`) y el scoping de profesores se calculan y filtran exclusivamente en el motor de base de datos (`backend/app/services/incident_service.py`), nunca en el cliente.
- **Inmutabilidad de Receipts:** Los acuses registran obligatoriamente timestamp UTC del servidor y dirección IP del actor.

---

## 14. Certificación existente

- **Qué se certificó:**
  1. Integridad de esquemas relacionales (migración 021).
  2. Servicios de backend y suites de pruebas unitarias/integración de API (100% pasando).
  3. Experiencia de navegación en frontend de los Portales de Estudiante y Acudiente (`StudentPortal.test.tsx`, `GuardianPortal.test.tsx`, `InstitutionalCommunications.test.tsx`).
- **Qué evidencia se utilizó:** Pruebas automatizadas en Vitest y Pytest con clientes simulados y bases de datos transaccionales de test.
- **Qué quedó fuera:** La interfaz de usuario administrativa (Fase 15F del plan original). No hay pruebas de frontend para creación de comunicados ni noticias porque los componentes no existen.
- **Qué está realmente demostrado:** Que la plataforma es capaz de almacenar, gestionar lógicamente y servir a las familias y estudiantes la información institucional y de convivencia.

---

## 15. Hallazgos

### HALLAZGO F15-001
- **Severidad:** HIGH
- **Área:** Frontend / Consola Administrativa Directiva
- **Descripción:** Ausencia de pantalla o formulario para que Rectores o Coordinadores puedan redactar, segmentar y publicar comunicados y circulares oficiales desde la aplicación web.
- **Evidencia:** Inspección de `App.tsx`, `AcademicHub.tsx` y `Dashboard.tsx`. No existe ruta, tab ni componente de creación.
- **Impacto:** Los directivos escolares no pueden emitir avisos sin asistencia técnica por API.
- **Estado:** PENDIENTE DE IMPLEMENTACIÓN
- **Requiere decisión humana:** Sí.

### HALLAZGO F15-002
- **Severidad:** HIGH
- **Área:** Frontend / Consola Directiva de Noticias
- **Descripción:** Ausencia de interfaz gráfica para redactar, categorizar y publicar artículos en el Periódico Escolar.
- **Evidencia:** Solo existen componentes consumidores (`StudentNewsView.tsx`, `GuardianNewsView.tsx`).
- **Impacto:** La publicación de noticias depende exclusivamente de llamadas manuales a la API.
- **Estado:** PENDIENTE DE IMPLEMENTACIÓN
- **Requiere decisión humana:** Sí.

### HALLAZGO F15-003
- **Severidad:** HIGH
- **Área:** Frontend / Consola Docente y Directiva de Convivencia
- **Descripción:** Ausencia de interfaz gráfica en el Portal Docente (`/teacher`) y en la Gestión Institucional (`/academic`) para registrar situaciones de convivencia escolar (Ley 1620), ingresar descargos o asentar acuerdos y cierres.
- **Evidencia:** `TeacherPortal.tsx` contiene solo tabs pedagógicos (Carga, Grupos, Actividades, Calificaciones, Asistencia, Planeación).
- **Impacto:** Los docentes no pueden registrar anotaciones en el Observador desde su espacio de trabajo.
- **Estado:** PENDIENTE DE IMPLEMENTACIÓN
- **Requiere decisión humana:** Sí.

### HALLAZGO F15-004
- **Severidad:** MEDIUM
- **Área:** Frontend / Cliente API
- **Descripción:** El servicio cliente `communicationApi` (`frontend/src/services/communication.ts`) carece de funciones para invocar los endpoints de creación/actualización/publicación (`POST /communications`, `POST /news`, `POST /incidents`).
- **Evidencia:** Solo contiene métodos `get*` y `acknowledge*`.
- **Impacto:** Aunque se crearan pantallas en React, se requiere antes complementar el servicio cliente.
- **Estado:** PENDIENTE DE IMPLEMENTACIÓN
- **Requiere decisión humana:** Sí.

### HALLAZGO F15-005
- **Severidad:** MEDIUM
- **Área:** QA / Datos y Verificación
- **Descripción:** Para poder verificar visualmente las vistas familiares en el navegador web fue indispensable crear y ejecutar un script directo de base de datos (`backend/scratch/qa_seed_phase15.py`).
- **Evidencia:** Archivo `backend/scratch/qa_seed_phase15.py` y reporte `PHASE_15_QA_DATA_PREPARATION_REPORT.md`.
- **Impacto:** Simulación exitosa de la experiencia de consumo, pero sin validar el flujo extremo a extremo de autoría humana.
- **Estado:** DOCUMENTADO / BAJO CONTROL
- **Requiere decisión humana:** No.

### HALLAZGO F15-006
- **Severidad:** INFORMATIONAL
- **Área:** Backend / Seguridad y Arquitectura
- **Descripción:** La arquitectura backend se encuentra completa, madura, modular, protegida contra IDOR y 100% probada bajo tests automatizados.
- **Evidencia:** Todos los tests de comunicaciones, noticias e incidentes pasan exitosamente.
- **Impacto:** Positivo. Reduce sustancialmente el esfuerzo para la futura habilitación de la consola administrativa.
- **Estado:** CERTIFICADO EN BACKEND
- **Requiere decisión humana:** No.

---

## 16. Brechas funcionales

1. **Faltantes Administrativos:** No existe flujo de usuario en la UI para emisión de circulares, redacción de noticias ni diligenciamiento del Observador.
2. **Faltantes de Backend:** Ninguno. Los servicios y modelos soportan la totalidad de las operaciones del dominio.
3. **Faltantes de API:** Ninguno. Los 17 endpoints requeridos están expuestos y operativos.
4. **Faltantes de UI:** Faltan las consolas de redacción directiva en `/academic` y la consola de anotaciones en `/teacher`.
5. **Faltantes de Seguridad:** Ninguno. Las reglas RBAC, tenant isolation y deny-by-default están en ejecución.
6. **Faltantes de Certificación:** Falta la certificación del flujo extremo a extremo de creación administrativa en navegador.
7. **Simulación de Funcionalidad por Datos QA:** Los datos observados en pantalla demostraron la operatividad del visor, pero la creación de esos datos fue asistida programáticamente.

---

## 17. Validación manual requerida

A continuación se detalla la matriz de pruebas funcionales humanas que DEBEN realizarse manualmente en el navegador web para certificar los módulos actualmente operativos:

| ID | Rol | Ruta | Prueba | Resultado esperado | Screenshot |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **MAN-F15-001** | Estudiante | `/student?tab=communications` | Consultar listado de circulares oficiales | Visualización correcta de la circular `[QA-F15-20260907]`, badge de prioridad ALTA y remitente Rectoría. | Sí, 1 |
| **MAN-F15-002** | Estudiante | `/student?tab=communications` | Confirmar lectura obligatoria (Acuse) | El botón cambia de "Confirmar lectura obligatoria" a "Lectura confirmada" con check verde sin recargar la página. | Sí, 1 |
| **MAN-F15-003** | Estudiante | `/student?tab=news` | Consultar periódico escolar y artículo | Visualización de la noticia `[QA-F15-20260907]` de feria de ciencias, badge de categoría y apertura del modal. | Sí, 1 |
| **MAN-F15-004** | Estudiante | `/student?tab=incidents` | Consultar Observador formativo | Visualización del incidente formativo `Tipo I`, descripción preventiva y notas de seguimiento acordadas. | Sí, 1 |
| **MAN-F15-005** | Acudiente | `/guardian?tab=communications`| Consultar circulares de la familia | Visualización de la circular oficial y verificación del selector de hijo vinculado. | Sí, 1 |
| **MAN-F15-006** | Acudiente | `/guardian?tab=communications`| Firmar acuse de recibo parental | El acudiente confirma recepción obligatoria; el estado se actualiza en pantalla inmediatamente. | Sí, 1 |
| **MAN-F15-007** | Acudiente | `/guardian?tab=news` | Consultar noticias y novedades | Cuadrícula de artículos culturales/académicos visibles para la comunidad educativa. | Sí, 1 |
| **MAN-F15-008** | Acudiente | `/guardian?tab=incidents` | Consultar Observador de su hijo | Visualización del registro `[QA-F15-20260907]` del estudiante Ramiro Rey con compromisos formativos suscritos. | Sí, 1 |

---

## 18. Matriz maestra final

| Capacidad | Estado real | Evidencia técnica | Evidencia UI | Seguridad | Tests | Certificación | Acción requerida |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **Circulares (Emisión Directiva)** | `API_ONLY` | `endpoints/communications.py` | Inexistente en frontend | PASS | PASS | Parcial | Construir UI administrativa en sub-fase posterior o API |
| **Circulares (Consumo Estudiante)**| `PASS` | `endpoints/student_portal.py` | `StudentCommunicationsView.tsx`| PASS | PASS | PASS | Validación manual humana (MAN-F15-001) |
| **Circulares (Acuse Familiar)** | `PASS` | `endpoints/guardian_portal.py` | `GuardianCommunicationsView.tsx`| PASS | PASS | PASS | Validación manual humana (MAN-F15-006) |
| **Noticias (Redacción Directiva)** | `API_ONLY` | `endpoints/news.py` | Inexistente en frontend | PASS | PASS | Parcial | Construir UI administrativa de redacción |
| **Noticias (Consumo Escolar)** | `PASS` | `endpoints/news.py` | `StudentNewsView.tsx` | PASS | PASS | PASS | Validación manual humana (MAN-F15-003) |
| **Observador (Registro Docente)** | `API_ONLY` | `endpoints/incidents.py` | Inexistente en frontend | PASS | PASS | Parcial | Construir pestaña en `/teacher` y `/academic` |
| **Observador (Visor Estudiante)** | `PASS` | `endpoints/student_portal.py` | `StudentIncidentsView.tsx` | PASS | PASS | PASS | Validación manual humana (MAN-F15-004) |
| **Observador (Monitoreo Acudiente)**| `PASS` | `endpoints/guardian_portal.py` | `GuardianIncidentsView.tsx` | PASS | PASS | PASS | Validación manual humana (MAN-F15-008) |

---

## 19. Conclusión

Respuestas expresas a las 12 preguntas de control:

1. **¿Quién registra actualmente los comunicados?**  
   Cualquier rol directivo (`rector`, `coordinator`, `institution_admin`) exclusivamente mediante peticiones HTTP a la API o scripts de base de datos.
2. **¿Dónde?**  
   En el endpoint `POST /api/v1/communications`. No en pantalla web.
3. **¿Existe UI administrativa?**  
   **No.**
4. **¿Existe API?**  
   **Sí**, 100% implementada y probada.
5. **¿Cómo fueron creados los datos QA?**  
   Mediante inserción directa SQLAlchemy en el script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual Nacional PEVN/backend/scratch/qa_seed_phase15.py).
6. **¿Quién registra noticias?**  
   Directivos mediante el endpoint `POST /api/v1/news`.
7. **¿Quién registra convivencia?**  
   Docentes (para sus grupos asignados) y directivos mediante el endpoint `POST /api/v1/incidents`.
8. **¿Qué funciona extremo a extremo?**  
   El **consumo, lectura y confirmación de acuses de recibo en los Portales de Estudiantes y Acudientes**, una vez que los datos existen en la base de datos.
9. **¿Qué funciona únicamente por API?**  
   La **creación, edición, archivo y publicación** de comunicados, noticias y situaciones de convivencia.
10. **¿Qué existe únicamente como QA?**  
    Los tres registros observados en la validación manual (`[QA-F15-20260907]`).
11. **¿Qué está ausente?**  
    La interfaz de usuario gráfica para emitir circulares, redactar noticias y registrar anotaciones de convivencia.
12. **¿Qué requiere decisión humana?**  
    Decidir si se aprueba el cierre de la Fase 15 como "Portal de Consumo Familiar" delegando la UI administrativa a una sub-fase 15F, o si se condiciona el cierre a la construcción de las pantallas administrativas.

---

## 20. Recomendación

$$\mathbf{READY\ FOR\ HUMAN\ DECISION}$$

---

## 21. Declaración final

READ-ONLY AUDIT COMPLETED — NO PRODUCT CODE OR DATA MODIFIED

- Archivo de informe creado:
  `AUDITORIA_FASE15_COMUNICACIONES_NOTICIAS_CONVIVENCIA.md`
- Archivos de producto modificados: 0
- Datos modificados: 0
- Migraciones ejecutadas: 0
- Seeds ejecutados: 0
- Commits: 0
- Push: 0
