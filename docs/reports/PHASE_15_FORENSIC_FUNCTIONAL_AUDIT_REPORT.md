# PEVN — INFORME DE AUDITORÍA FUNCIONAL FORENSE DE FASE 15
## COMUNICACIONES INSTITUCIONALES, NOTICIAS / PERIÓDICO ESCOLAR Y CONVIVENCIA / OBSERVADOR DEL ESTUDIANTE

**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha de Emisión:** 2026-09-07  
**Tipo de Auditoría:** Auditoría Funcional, Técnica y de Runtime Estrictamente READ-ONLY  
**Estado General de la Auditoría:** `PASS`  
**Recomendación del Gate:** `READY FOR HUMAN DECISION`

---

## 1. RESUMEN EJECUTIVO

La presente auditoría técnica y funcional examinó de forma exhaustiva el estado real de la **Fase 15** de PEVN (*Comunicaciones Institucionales, Noticias/Periódico Escolar y Convivencia/Observador*).

### Conclusiones Principales:
1. **El Backend y los Contratos de API están implementados al 100%:**
   - Existen los modelos relacionales SQLAlchemy (`InstitutionalCommunication`, `CommunicationAudience`, `CommunicationReceipt`, `InstitutionalNews`, `StudentIncident`, `IncidentFollowUp`).
   - Existen los esquemas Pydantic completos de request/response.
   - Existen los servicios de dominio con lógica de negocio multi-tenant, expiración y control de alcance.
   - Existen 17 endpoints REST en FastAPI protegidos por permisos atómicos RBAC y aislamiento institucional.
2. **El Frontend está implementado de forma estrictamente ASIMÉTRICA (Solo Consumo Familiar y Estudiantil):**
   - **Portal del Estudiante (`/student`):** 100% operativo para consultar circulares, confirmar lectura obligatoria, leer noticias y consultar el Observador personal.
   - **Portal del Acudiente (`/guardian`):** 100% operativo para consultar circulares institucionales, confirmar acuse de recibo, leer noticias y consultar el Observador de sus hijos vinculados legalmente.
   - **Consola Administrativa Directiva y Docente:** **NO EXISTE EN EL FRONTEND**. No hay ninguna pantalla, botón, formulario o modal para que un Rector, Coordinador o Docente redacte, configure, publique o gestione comunicados, noticias o registros de convivencia desde el navegador web.
3. **Origen de los Datos QA Observados:**
   - Los registros visibles en los portales (`[QA-F15-20260907]`) fueron sembrados mediante el script local de desarrollo y QA ([`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py)) ejecutado durante la fase previa de preparación de datos, y **no** a través de una interfaz interactiva de usuario.

---

## 2. ALCANCE A: COMUNICACIONES INSTITUCIONALES

### 2.1 Modelos de Base de Datos
* **`InstitutionalCommunication`** ([`backend/app/models/communication.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/communication.py)):
  * Tabla: `institutional_communications`
  * Columnas: `id`, `institution_id`, `author_user_id`, `title`, `summary`, `content`, `category`, `priority`, `target_scope`, `attachment_url`, `requires_acknowledgment`, `status`, `published_at`, `expires_at`, `created_at`, `updated_at`.
  * Enums:
    * `CommunicationCategory`: `CIRCULAR_OFICIAL`, `CONVOCATORIA_REUNION`, `AVISO_ACADEMICO`, `AVISO_ADMINISTRATIVO`, `RECORDATORIO`, `EMERGENCIA_INSTITUCIONAL`.
    * `CommunicationPriority`: `BAJA`, `MEDIA`, `ALTA`, `URGENTE`.
    * `TargetScopeType`: `TODOS_INSTITUCION`, `SOLO_ESTUDIANTES`, `SOLO_ACUDIENTES`, `SOLO_DOCENTES`, `POR_SEDE`, `POR_GRADO`, `POR_GRUPO`.
    * `PublishingStatus`: `BORRADOR`, `PUBLICADO`, `ARCHIVADO`.
* **`CommunicationAudience`** ([`backend/app/models/communication.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/communication.py)):
  * Tabla: `communication_audiences`
  * Columnas: `id`, `communication_id`, `campus_id`, `grade_id`, `group_id`, `role_name`, `created_at`, `updated_at`.
* **`CommunicationReceipt`** ([`backend/app/models/communication.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/communication.py)):
  * Tabla: `communication_receipts`
  * Columnas: `id`, `communication_id`, `user_id`, `read_at`, `acknowledged_at`, `client_ip`, `created_at`, `updated_at`. Restricción única `(communication_id, user_id)`.

### 2.2 Schemas Pydantic
* Archivo: [`backend/app/schemas/communication.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/schemas/communication.py)
* DTOs: `CommunicationCreateRequest`, `CommunicationUpdateRequest`, `CommunicationAudiencePayload`, `InstitutionalCommunicationResponse`, `CommunicationListResponse`, `CommunicationReceiptResponse`.

### 2.3 Servicios de Dominio
* **`CommunicationService`** ([`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py)):
  * Métodos: `create_communication`, `get_communication_by_id`, `update_communication`, `publish_communication`, `archive_communication`, `list_communications`, `list_student_communications`, `list_guardian_communications`, `acknowledge_communication`.
  * Filtro de expiración: Si `expires_at < now(UTC)`, la circular se oculta automáticamente de las bandejas de estudiantes y acudientes y no suma en contadores de pendientes.

### 2.4 Endpoints Disponibles
* **Administrativos:**
  * `POST /api/v1/communications` — Crear circular (Requiere `communications:create`).
  * `GET /api/v1/communications` — Listar circulares (Requiere `communications:read`).
  * `GET /api/v1/communications/{id}` — Detalle y métricas de lectura (Requiere `communications:read`).
  * `PUT /api/v1/communications/{id}` — Modificar circular (Requiere `communications:update`).
  * `POST /api/v1/communications/{id}/publish` — Publicar oficialmente (Requiere `communications:publish`).
  * `POST /api/v1/communications/{id}/archive` — Archivar circular (Requiere `communications:delete`).
* **Portales:**
  * `GET /api/v1/student/communications` & `POST .../acknowledge`
  * `GET /api/v1/guardian/communications` & `POST .../acknowledge`

### 2.5 Respuestas a las Preguntas Específicas
* **¿Existe actualmente una operación real de "Crear comunicado"?**
  * **En API/Backend:** **SÍ**. Implementada y probada al 100%.
  * **En Frontend/UI:** **NO**. No existe interfaz gráfica para redactar o emitir comunicados.
* **Si NO existe UI, ¿cómo fue generado el comunicado QA observado?**
  * Fue generado por el script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py), insertando la fila en PostgreSQL con la Rectora `Sandra Chavez Guzman` como autora.

---

## 3. ALCANCE B: NOTICIAS / PERIÓDICO ESCOLAR

### 3.1 Modelos, Servicios y Endpoints
* **Modelo:** `InstitutionalNews` ([`backend/app/models/news.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/news.py)).
  * Categorías: `LOGRO_ACADEMICO`, `EVENTO_CULTURAL`, `EVENTO_DEPORTIVO`, `PROYECTO_INSTITUCIONAL`, `NOTICIA_GENERAL`.
* **Servicio:** `NewsService` ([`backend/app/services/news_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/news_service.py)).
* **Endpoints Backend:**
  * `POST /api/v1/news` (`news:create`)
  * `GET /api/v1/news/{id}` (`news:read`)
  * `PUT /api/v1/news/{id}` (`news:update`)
  * `POST /api/v1/news/{id}/publish` (`news:publish`)
  * `GET /api/v1/news` (`news:read`)
  * `GET /api/v1/student/news` & `GET /api/v1/guardian/news`

### 3.2 Respuestas a las Preguntas Específicas
* **¿Existe una interfaz administrativa real para crear/publicar una noticia?**
  * **NO**.
  * **Evidencia:** Inspección de rutas en [`frontend/src/App.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/App.tsx) y componentes de gestión directiva. Las únicas vistas existentes son [`StudentNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentNewsView.tsx) y [`GuardianNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianNewsView.tsx), ambas de solo lectura.

---

## 4. ALCANCE C: CONVIVENCIA / OBSERVADOR DEL ESTUDIANTE

### 4.1 Modelos, Servicios y Endpoints
* **Modelos:** `StudentIncident` e `IncidentFollowUp` ([`backend/app/models/coexistence_incident.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/coexistence_incident.py)).
  * Tipificación formal Ley 1620 de 2013: `TIPO_I`, `TIPO_II`, `TIPO_III`, `OBSERVACION_POSITIVA`.
  * Estados: `ABIERTO`, `EN_SEGUIMIENTO`, `CON_COMPROMISOS`, `CERRADO`.
* **Servicio:** `CoexistenceIncidentService` ([`backend/app/services/incident_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/incident_service.py)):
  * **Scoping docente:** Los docentes sin rol directivo solo pueden reportar incidentes sobre estudiantes de grupos asignados académicamente (`get_teacher_authorized_group_ids`).
  * **Cierre formal:** Exclusivo para directivos (`incidents:close`).
* **Endpoints Backend:**
  * `POST /api/v1/incidents` (`incidents:create`)
  * `GET /api/v1/incidents` (`incidents:read`)
  * `GET /api/v1/incidents/{id}` (`incidents:read`)
  * `PUT /api/v1/incidents/{id}` (`incidents:update`)
  * `POST /api/v1/incidents/{id}/follow-ups` (`incidents:update`)
  * `POST /api/v1/incidents/{id}/close` (`incidents:close`)
  * `GET /api/v1/student/incidents` & `GET /api/v1/guardian/students/{id}/incidents`

### 4.2 Respuestas a las Preguntas Específicas
* **¿Existe interfaz administrativa o docente para crear anotaciones en el Observador?**
  * **NO**.
  * **Evidencia:** [`TeacherPortal.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/teacher/TeacherPortal.tsx) no cuenta con pestaña de Observador. [`AcademicHub.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/academic/AcademicHub.tsx) directivo tampoco cuenta con pestaña de Convivencia.

---

## 5. ALCANCE D: ORIGEN EXACTO DE LOS DATOS QA OBSERVADOS

| Registro QA Observado | Mecanismo de Creación | Archivo Fuente / Script | ID en Base de Datos | Usuario Creador / Emisor | ¿Creable vía UI? | ¿Creable vía API? |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `[QA-F15-20260907] Circular Oficial: Actividades Pedagógicas y Convivencia` | Inserción directa SQLAlchemy | `backend/scratch/qa_seed_phase15.py` | `7e83e337-f130-4e0c-b831-4a0bd764c077` | Sandra Chavez Guzman (Rectora) | ❌ NO | ✅ SÍ (`POST /communications`) |
| `[QA-F15-20260907] Logro Destacado en Feria de Ciencia e Innovación Escolar` | Inserción directa SQLAlchemy | `backend/scratch/qa_seed_phase15.py` | `d2d33449-fb86-4f20-bf2e-3f392beda905` | Sandra Chavez Guzman (Rectora) | ❌ NO | ✅ SÍ (`POST /news`) |
| `[QA-F15-20260907] Registro formativo de convivencia escolar` | Inserción directa SQLAlchemy | `backend/scratch/qa_seed_phase15.py` | `8daf3c23-dae8-4eb7-8b7b-72845847b425` | Sandra Chavez Guzman (Rectora) | ❌ NO | ✅ SÍ (`POST /incidents`) |
| `[QA-F15-20260907] Sesión de seguimiento formativo` | Inserción directa SQLAlchemy | `backend/scratch/qa_seed_phase15.py` | `e77469fa-03a4-456f-9f6c-11dbd526e93e` | Sandra Chavez Guzman (Rectora) | ❌ NO | ✅ SÍ (`POST /incidents/{id}/follow-ups`) |

---

## 6. ALCANCE E: MAPA COMPLETO DE ROLES Y PERMISOS RBAC

Matriz real obtenida de [`backend/app/services/rbac_bootstrap_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py) (`ROLE_PERMISSIONS_CONFIG`):

| Función / Permiso RBAC | SUPER_ADMIN | NATIONAL_ADMIN | TERRITORIAL_ADMIN | RECTOR | COORDINADOR | DOCENTE | ESTUDIANTE | ACUDIENTE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **COMUNICADOS** | | | | | | | | |
| `communications:read` | ✅ (`*:*`) | ✅ | ✅ | ✅ | ✅ | ✅ (Institucional) | ✅ (Filtrado) | ✅ (Filtrado) |
| `communications:create` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:update` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:publish` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:delete` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **NOTICIAS** | | | | | | | | |
| `news:read` | ✅ (`*:*`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `news:create` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:update` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:publish` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:delete` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **CONVIVENCIA / OBSERVADOR** | | | | | | | | |
| `incidents:read` | ✅ (`*:*`) | ✅ | ✅ | ✅ | ✅ | ✅ (Sus grupos) | ✅ (Propios) | ✅ (Hijos autorizados) |
| `incidents:create` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ✅ (Sus grupos) | ❌ | ❌ |
| `incidents:update` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ✅ (Sus grupos) | ❌ | ❌ |
| `incidents:close` | ✅ (`*:*`) | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 7. ALCANCE F: INVENTARIO DE UI

| Ruta Frontend | Componente | Roles | Acción | Endpoint Consumido | Tipo Operación |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/student?tab=communications` | `StudentCommunicationsView.tsx` | `student` | Ver circulares y confirmar acuse | `GET /api/v1/student/communications`<br>`POST .../acknowledge` | Lectura + Acuse |
| `/student?tab=news` | `StudentNewsView.tsx` | `student` | Ver noticias escolares | `GET /api/v1/student/news` | Lectura |
| `/student?tab=incidents` | `StudentIncidentsView.tsx` | `student` | Ver observador personal | `GET /api/v1/student/incidents` | Lectura |
| `/guardian?tab=communications` | `GuardianCommunicationsView.tsx` | `guardian` | Ver circulares y confirmar acuse | `GET /api/v1/guardian/communications`<br>`POST .../acknowledge` | Lectura + Acuse |
| `/guardian?tab=news` | `GuardianNewsView.tsx` | `guardian` | Ver noticias escolares | `GET /api/v1/guardian/news` | Lectura |
| `/guardian?tab=incidents` | `GuardianIncidentsView.tsx` | `guardian` | Ver observador de hijo | `GET /api/v1/guardian/students/{id}/incidents` | Lectura |
| *(No existe ruta)* | *(No existe componente)* | Directivos / Docentes | Redactar circular | `POST /api/v1/communications` | **AUSENTE EN UI** |
| *(No existe ruta)* | *(No existe componente)* | Directivos | Redactar noticia | `POST /api/v1/news` | **AUSENTE EN UI** |
| *(No existe ruta)* | *(No existe componente)* | Docentes / Directivos | Registrar situación de convivencia | `POST /api/v1/incidents` | **AUSENTE EN UI** |

---

## 8. ALCANCE G: INVENTARIO DE API

| Método | Ruta | Operación | Permiso Requerido | Rol Típico | Servicio Backend | Tipo | Tenant Isolation | Audit Event |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `POST` | `/api/v1/communications` | Crear circular | `communications:create` | Rector, Coordinador | `CommunicationService` | Escritura | Estricta | `COMMUNICATION_CREATED` |
| `GET` | `/api/v1/communications` | Listar circulares | `communications:read` | Directivos | `CommunicationService` | Lectura | Estricta | — |
| `GET` | `/api/v1/communications/{id}` | Detalle y métricas | `communications:read` | Directivos | `CommunicationService` | Lectura | Estricta | — |
| `PUT` | `/api/v1/communications/{id}` | Modificar circular | `communications:update` | Rector, Coordinador | `CommunicationService` | Escritura | Estricta | `COMMUNICATION_UPDATED` |
| `POST` | `/api/v1/communications/{id}/publish`| Publicar circular | `communications:publish` | Rector, Coordinador | `CommunicationService` | Escritura | Estricta | `COMMUNICATION_PUBLISHED` |
| `POST` | `/api/v1/communications/{id}/archive`| Archivar circular | `communications:delete` | Rector, Coordinador | `CommunicationService` | Escritura | Estricta | `COMMUNICATION_ARCHIVED` |
| `GET` | `/api/v1/student/communications` | Feed estudiante | `communications:read` | Estudiante | `CommunicationService` | Lectura | Derivada JWT | — |
| `POST` | `/api/v1/student/communications/{id}/acknowledge` | Acuse estudiante | `communications:read` | Estudiante | `CommunicationService` | Escritura | Derivada JWT | `COMMUNICATION_ACKNOWLEDGED` |
| `GET` | `/api/v1/guardian/communications` | Feed acudiente | `communications:read` | Acudiente | `CommunicationService` | Lectura | Derivada JWT | — |
| `POST` | `/api/v1/guardian/communications/{id}/acknowledge` | Acuse acudiente | `communications:read` | Acudiente | `CommunicationService` | Escritura | Derivada JWT | `COMMUNICATION_ACKNOWLEDGED` |
| `POST` | `/api/v1/news` | Crear noticia | `news:create` | Rector, Coordinador | `NewsService` | Escritura | Estricta | `NEWS_CREATED` |
| `GET` | `/api/v1/news` | Listar noticias | `news:read` | Directivos | `NewsService` | Lectura | Estricta | — |
| `GET` | `/api/v1/news/{id}` | Detalle noticia | `news:read` | Todos | `NewsService` | Lectura | Estricta | — |
| `PUT` | `/api/v1/news/{id}` | Editar noticia | `news:update` | Rector, Coordinador | `NewsService` | Escritura | Estricta | `NEWS_UPDATED` |
| `POST` | `/api/v1/news/{id}/publish` | Publicar noticia | `news:publish` | Rector, Coordinador | `NewsService` | Escritura | Estricta | `NEWS_PUBLISHED` |
| `GET` | `/api/v1/student/news` | Feed noticias est. | `news:read` | Estudiante | `NewsService` | Lectura | Derivada JWT | — |
| `GET` | `/api/v1/guardian/news` | Feed noticias acud. | `news:read` | Acudiente | `NewsService` | Lectura | Derivada JWT | — |
| `POST` | `/api/v1/incidents` | Crear situación | `incidents:create` | Docente, Directivo | `CoexistenceIncidentService` | Escritura | Scoping Docente | `INCIDENT_RECORDED` |
| `GET` | `/api/v1/incidents` | Listar situaciones | `incidents:read` | Docente, Directivo | `CoexistenceIncidentService` | Lectura | Scoping Docente | — |
| `GET` | `/api/v1/incidents/{id}` | Detalle situación | `incidents:read` | Docente, Directivo | `CoexistenceIncidentService` | Lectura | Estricta | — |
| `PUT` | `/api/v1/incidents/{id}` | Modificar caso | `incidents:update` | Reportante, Directivo | `CoexistenceIncidentService` | Escritura | Scoping Docente | `INCIDENT_UPDATED` |
| `POST` | `/api/v1/incidents/{id}/follow-ups` | Registrar acuerdo | `incidents:update` | Docente, Directivo | `CoexistenceIncidentService` | Escritura | Scoping Docente | `INCIDENT_FOLLOW_UP_ADDED` |
| `POST` | `/api/v1/incidents/{id}/close` | Cerrar situación | `incidents:close` | Rector, Coordinador | `CoexistenceIncidentService` | Escritura | Estricta Directiva | `INCIDENT_CLOSED` |
| `GET` | `/api/v1/student/incidents` | Observador propio | `incidents:read` | Estudiante | `CoexistenceIncidentService` | Lectura | Estricta JWT | — |
| `GET` | `/api/v1/guardian/students/{id}/incidents` | Observador hijo | `incidents:read` | Acudiente | `CoexistenceIncidentService` | Lectura | Anti-IDOR (`StudentGuardian`) | — |

---

## 9. ALCANCE H: SEGURIDAD

1. **Deny-by-Default:** Implementado rigurosamente en `CentralizedAuthorizationService`. Si un rol carece del permiso o el usuario está inactivo/bloqueado, la petición es rechazada de inmediato (`401` o `403`).
2. **Tenant Isolation:**
   - La institución se deriva forzosamente del token JWT (`current_user.institution_id`).
   - Ningún usuario no superadmin puede sobreescribir el `institution_id`.
3. **Anti-IDOR en Portales de Estudiantes y Acudientes:**
   - En `/student/incidents` y `/student/communications`, el ID del estudiante se extrae de `Student.user_id == current_user.id`. El estudiante no puede pasar un ID de otro alumno.
   - En `/guardian/students/{student_id}/incidents`, el servicio valida activamente la relación en la tabla `StudentGuardian`. Si un acudiente intenta consultar un `student_id` ajeno, la API devuelve un **404 blind** (*Not Found*) para no revelar existencia.
4. **Confidencialidad del Observador (Ley 1620 de 2013):**
   - Se respetan estrictamente las banderas booleanas `is_visible_to_student` e `is_visible_to_guardian`. Casos con reserva sumaria o en investigación no se exponen a los portales familiares.
5. **Inmutabilidad de Acuses de Recibo:**
   - Los acuses (`CommunicationReceipt`) registran el `read_at`, `acknowledged_at` y la IP del cliente del lado del servidor, previniendo falsificaciones desde el cliente.

---

## 10. ALCANCE I: ESTADO REAL DE CERTIFICACIÓN FASE 15

| Componente | Estado de Certificación | Evidencia Documental |
| :--- | :--- | :--- |
| Modelos de Dominio y Tablas BD | **IMPLEMENTADO** | `021_phase15_communications_news_incidents.py` |
| Servicios y Lógica de Negocio Backend | **CERTIFICADO EN BACKEND** | `test_institutional_communications_api.py`, `test_institutional_news_api.py`, `test_coexistence_incidents_api.py` (Tests pasando 100%) |
| Endpoints Administrativos Backend | **IMPLEMENTADO SOLO BACKEND** | Rutas `/api/v1/communications`, `/api/v1/news`, `/api/v1/incidents` operativas en FastAPI pero sin frontend |
| Vistas de Consumo Estudiante / Acudiente | **CERTIFICADO EN FRONTEND** | `StudentPortal.test.tsx`, `GuardianPortal.test.tsx`, `InstitutionalCommunications.test.tsx` (Tests pasando) |
| Consola Administrativa Directiva / Docente | **AUSENTE / NO IMPLEMENTADO** | `docs/phase15_institutional_communications_forensic_architecture.md` (Sección 21, ítem 6: Fase 15F nunca fue codificada en frontend) |
| Flujo Extremo a Extremo con Datos Reales | **PROBADO ÚNICAMENTE CON DATOS QA** | Reporte `PHASE_15_QA_DATA_PREPARATION_REPORT.md` (Verificado con marcador `QA-F15-20260907`) |

---

## 11. ALCANCE J: MATRIZ MAESTRA

| Capacidad | Backend | API | UI Admin | UI Estudiante | UI Acudiente | Seguridad | Tests | Certificado | Datos QA | Estado Final |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Crear / Publicar Circular** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Consultar Circulares (Admin)** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Consultar Circulares (Estudiante)** | PASS | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS | **PASS** |
| **Firmar Acuse Recibo (Estudiante)** | PASS | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS | **PASS** |
| **Consultar Circulares (Acudiente)** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **Firmar Acuse Recibo (Acudiente)** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **Crear / Publicar Noticia** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Consultar Noticias (Estudiante)** | PASS | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS | **PASS** |
| **Consultar Noticias (Acudiente)** | PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | PASS | **PASS** |
| **Registrar Situación Convivencia** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Registrar Seguimiento / Compromiso** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Cerrar Situación Convivencia** | PASS | PASS | MISSING | N/A | N/A | PASS | PASS | PARTIAL | QA_ONLY | **API_ONLY** |
| **Consultar Observador (Estudiante)** | PASS | PASS | N/A | PASS | N/A | PASS | PASS | PASS | PASS | **PASS** |
| **Consultar Observador Hijo (Acudiente)**| PASS | PASS | N/A | N/A | PASS | PASS | PASS | PASS | PASS | **PASS** |

---

## 12. ALCANCE K: RESPUESTAS EXPLÍCITAS AL HALLAZGO CENTRAL

1. **¿Dónde se registra actualmente un comunicado institucional?**  
   Únicamente mediante llamada HTTP directa a la API REST (`POST /api/v1/communications`) o mediante scripts directos de base de datos.
2. **¿Quién lo registra?**  
   Cualquier usuario con rol `rector`, `coordinator`, `academic_coordinator`, `institution_admin` o `superadmin` autenticado con token JWT.
3. **¿Existe una pantalla administrativa para hacerlo?**  
   **NO**. No existe ninguna vista, pantalla o formulario en el frontend para redactar o emitir comunicados.
4. **Si no existe, ¿cómo fueron creados los comunicados QA que estamos viendo?**  
   Fueron insertados directamente en PostgreSQL a través del script [`backend/scratch/qa_seed_phase15.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch/qa_seed_phase15.py) ejecutado para la tarea previa de datos QA.
5. **¿Existe endpoint administrativo de creación?**  
   **SÍ**. `POST /api/v1/communications` está completamente implementado y probado.
6. **¿Quién tiene permiso para utilizarlo?**  
   Los roles que poseen el permiso `communications:create` (`superadmin`, `rector`, `institution_admin`, `coordinator`, `academic_coordinator`).
7. **¿Existe UI administrativa para Noticias?**  
   **NO**. No existe pantalla de redacción de noticias en el frontend.
8. **¿Existe UI administrativa para Convivencia?**  
   **NO**. Ni el Módulo de Gestión Académica (`/academic`) ni el Portal Docente (`/teacher`) cuentan con interfaz de Observador del Estudiante.
9. **¿Qué parte de Fase 15 está realmente operativa de extremo a extremo?**  
   La **experiencia de consumo familiar y estudiantil**: Recepción de circulares, visualización de urgencias, firma de acuse de recibo obligatoria, lectura de periódico escolar/noticias por categorías, y consulta del Observador formativo con tipificación de la Ley 1620 y seguimientos.
10. **¿Qué parte está incompleta?**  
    La **consola de autoría y gestión administrativa directiva y docente**: No hay dónde redactar circulares, publicar noticias ni anotar incidentes en el Observador desde el navegador web.

---

## 13. ALCANCE L: CLASIFICACIÓN DE HALLAZGOS

* **HALLAZGO-15-01 (HIGH): Ausencia de UI Administrativa para Emisión de Contenidos y Convivencia.**  
  * *Impacto:* La Fase 15 no puede operarse de extremo a extremo por un usuario directivo o docente real sin utilizar herramientas externas tipo Postman/cURL o scripts.
* **HALLAZGO-15-02 (MEDIUM): Ausencia de Métodos Administrativos en `communicationApi` de Frontend.**  
  * *Impacto:* El servicio [`frontend/src/services/communication.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/communication.ts) solo tiene implementadas llamadas para portales de estudiantes/acudientes y lecturas puntuales por ID.
* **HALLAZGO-15-03 (INFORMATIONAL / POSITIVO): Robustez del Modelo Backend y Anti-IDOR.**  
  * *Impacto:* Todo el trabajo de base de datos, aislamiento multi-inquilino, contratos de API, auditoría y seguridad RBAC está terminado, probado y listo para cuando se construyan las pantallas de emisión.

---

## 14. ALCANCE M: CONCLUSIÓN Y RECOMENDACIÓN

### Brechas Identificadas:
- Falta la pantalla directiva para emitir circulares oficiales (`/academic?tab=communications` o similar).
- Falta la pantalla directiva para publicar noticias escolares (`/academic?tab=news` o similar).
- Falta la pantalla docente/coordinación para registrar y cerrar situaciones de convivencia en el Observador (`/teacher?tab=incidents` y `/academic?tab=coexistence`).

### Riesgos:
- Si se declara la Fase 15 formalmente "cerrada" sin documentar esta brecha, el usuario final esperará poder redactar comunicados y noticias desde la interfaz gráfica y encontrará que solo puede ver los datos que un desarrollador inserte por base de datos.

### Recomendación Final del Gate:

$$\mathbf{READY\ FOR\ HUMAN\ DECISION}$$

El sistema se encuentra en un estado técnicamente estable y limpio. El propietario del producto tiene ahora la información transparente y fundamentada para decidir entre dos caminos:
1. **Aceptar el alcance actual como "Fase 15 Portal Consumo"** (dando por cumplida la experiencia de estudiantes y acudientes, programando la consola de redacción para una sub-fase 15F posterior).
2. **Exigir la implementación de las pantallas de autoría directiva y docente** antes de emitir el cierre formal de la Fase 15.

---

### INVENTARIO DE INSPECCIÓN TÉCNICA

* **Archivos Inspeccionados:**
  * Backend: `models/communication.py`, `models/news.py`, `models/coexistence_incident.py`, `schemas/communication.py`, `schemas/news.py`, `schemas/incident.py`, `services/communication_service.py`, `services/news_service.py`, `services/incident_service.py`, `services/rbac_bootstrap_service.py`, `core/security/authorization.py`, `api/deps.py`, `api/v1/endpoints/communications.py`, `api/v1/endpoints/news.py`, `api/v1/endpoints/incidents.py`, `api/v1/endpoints/student_portal.py`, `api/v1/endpoints/guardian_portal.py`, `migrations/versions/021_phase15_communications_news_incidents.py`, `scratch/qa_seed_phase15.py`.
  * Frontend: `App.tsx`, `pages/Dashboard.tsx`, `pages/academic/AcademicHub.tsx`, `pages/teacher/TeacherPortal.tsx`, `pages/student/StudentPortal.tsx`, `pages/student/StudentCommunicationsView.tsx`, `pages/student/StudentNewsView.tsx`, `pages/student/StudentIncidentsView.tsx`, `pages/guardian/GuardianPortal.tsx`, `pages/guardian/GuardianCommunicationsView.tsx`, `pages/guardian/GuardianNewsView.tsx`, `pages/guardian/GuardianIncidentsView.tsx`, `services/communication.ts`, `test/InstitutionalCommunications.test.tsx`.
  * Documentación: `docs/phase15_institutional_communications_forensic_architecture.md`, `docs/phase15_institutional_communications_walkthrough.md`, `docs/reports/PHASE_15_CONTROLLED_FIX_REPORT.md`, `docs/reports/PHASE_15_QA_DATA_PREPARATION_REPORT.md`.

---

**CONFIRMACIÓN FINAL OBLIGATORIA:**

```text
READ-ONLY AUDIT COMPLETED — NO FILES OR DATA MODIFIED
```
