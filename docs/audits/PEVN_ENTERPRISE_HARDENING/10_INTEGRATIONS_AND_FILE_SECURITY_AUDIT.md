# AUDITORÍA ENTERPRISE DE ALMACENAMIENTO DE ARCHIVOS, DOCUMENTOS E INTEGRACIONES EXTERNAS (AGENTE 09)

**Programa:** Auditoría Maestra de Endurecimiento Enterprise — Plataforma Educativa Virtual Nacional (PEVN)  
**Agente Responsable:** AGENTE 09 — File Storage, Documents and External Integrations  
**Fecha de Corte:** 2026-11-01  
**Alcance Técnico:**
- **Almacenamiento y Gestión Documental:** `backend/app/core/storage/` ([`interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/interfaces.py), [`local.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py), [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py)), [`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py), [`student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py), [`teacher_portal_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/teacher_portal_service.py), [`student_portal_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/student_portal_service.py) y generadores de documentos [`scripts/generate_*.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/scripts/generate_government_pdfs.py).
- **Integración de Videoconferencia (BigBlueButton):** `backend/app/core/meeting/` ([`bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py), [`mock_provider.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/mock_provider.py), [`factory.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/factory.py), [`interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/interfaces.py), [`exceptions.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/exceptions.py)), [`virtual_classroom_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/virtual_classroom_service.py), [`recording_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/recording_service.py), [`virtual_classrooms.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/virtual_classrooms.py) y [`recordings.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py).
- **Integración de Correo Electrónico (SMTP):** [`email_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/email_service.py), [`config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py) y [`auth.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py).
- **Integración de Datos Abiertos Gubernamentales (MEN / DANE SODA):** [`men_open_data_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/adapters/men_open_data_adapter.py), [`official_catalog_sync_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py), [`official_dane_catalog.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/official_dane_catalog.py), [`harvest_due_dataset.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/harvest_due_dataset.py), [`ingest_dataset2_sedes.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/ingest_dataset2_sedes.py) e [`institutions.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py).

---

## 1. RESUMEN EJECUTIVO

La arquitectura de almacenamiento y de integraciones externas de la Plataforma Educativa Virtual Nacional (PEVN) exhibe bases de diseño sólidas en cuanto a desacoplamiento por interfaces (`StorageProviderInterface`, `IMeetingProvider`), aislamiento multi-inquilino en la autorización de descarga de archivos (ausencia de exposición pública estática de adjuntos académicos) y controles criptográficos anti-manipulación en la firma de peticiones hacia BigBlueButton.

Sin embargo, el análisis estático exhaustivo de código, configuración y artefactos de almacenamiento reveló **13 hallazgos técnicos (`INT-001` a `INT-013`)**, de los cuales **3 son de severidad `HIGH`**, **8 de severidad `MEDIUM`** y **2 de severidad `LOW`**:

| Severidad | Cantidad | Identificadores |
| :--- | :---: | :--- |
| **CRITICAL** | 0 | — |
| **HIGH** | 3 | `INT-001`, `INT-004`, `INT-006` |
| **MEDIUM** | 8 | `INT-002`, `INT-003`, `INT-005`, `INT-007`, `INT-008`, `INT-009`, `INT-010`, `INT-011` |
| **LOW** | 2 | `INT-012`, `INT-013` |
| **TOTAL** | **13** | `INT-001` a `INT-013` |

### Puntos Críticos Destacados (`HIGH`)
1. **Riesgo de Denegación de Servicio (OOM) en Cargas de Archivos (`INT-001`):** Los endpoints de carga docente y estudiantil invocan `await file.read()` sin límite de lectura antes de ejecutar `StorageService.validate_file()`, cargando la totalidad del payload en memoria RAM antes de comprobar el umbral de 20 MB.
2. **Orfandad de Archivos en Disco y Pérdida de Transacción al Eliminar Actividades (`INT-004`):** El endpoint `DELETE /teacher/activities/{activity_id}` omite `await db.commit()` (por lo que la eliminación con `flush()` se revierte al cerrar la sesión) y `TeacherPortalService.delete_activity()` no elimina los archivos físicos asociados en `data/storage/`.
3. **Almacenamiento en Texto Plano de Secretos de Reunión BBB y Firma SHA-1 por Defecto (`INT-006`):** Las columnas `moderator_password_hash` y `attendee_password_hash` en `virtual_classrooms` almacenan las contraseñas en texto plano (sin cifrado reversible Fernet/AES-GCM), el algoritmo de firma por defecto es `sha1` y `Settings` no bloquea el arranque en producción si `MEETING_PROVIDER_TYPE="mock"`.

---

## 2. INVENTARIO COMPLETO DE INTEGRACIONES EXTERNAS Y SUBSISTEMAS DE ARCHIVOS

Siguiendo la taxonomía estricta de gobernanza (`Implementado`, `Probado`, `Verificado`, `No probado`, `Parcialmente implementado`, `Pendiente de dependencia externa`, `No aplica`), se presenta el estado real de cada componente auditado:

| Subsistema / Integración | Módulos Principales | Estado Clasificado | Justificación y Evidencia Técnica |
| :--- | :--- | :--- | :--- |
| **Almacenamiento Local de Archivos (`LocalStorageProvider`)** | [`local.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py), [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py) | **Implementado / Probado** | Escritura atómica mediante archivo temporal `.tmp` (`os.replace`), mitigación de Path Traversal con `Path.relative_to()` y nombres UUID. Existen pruebas de flujos de carga/descarga, pero presenta lectura completa en RAM (`INT-001`) y rutas que exceden `MAX_PATH` en Windows (`INT-005`). |
| **Almacenamiento Cloud Objeto (AWS S3 / MinIO / GCS / Azure Blob)** | [`interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/interfaces.py) | **Pendiente de dependencia externa** | La interfaz `StorageProviderInterface` está definida para desacoplar el backend, pero solo existe la implementación `LocalStorageProvider`. No hay adaptador `S3StorageProvider` (`boto3`/`aiobotocore`) implementado. |
| **Validación de Tipos de Archivo y Magic Bytes** | [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L22-L120) | **Parcialmente implementado** | Valida lista blanca de 12 extensiones y firmas binarias (*magic bytes*) para PDF, PNG, JPG, GIF, WEBP y ZIP/OOXML. Sin embargo, para `.txt`/`.csv` solo verifica rechazo de bytes nulos (`\x00`), no inspecciona la estructura interna de contenedores ZIP/OOXML y confía en el `Content-Type` declarado por el cliente (`INT-002`). |
| **Autorización de Descarga de Adjuntos Académicos (Anti-IDOR)** | [`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L510-L680), [`student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L211-L382) | **Implementado / Verificado** | `app/main.py` **no** monta `StaticFiles` sobre `data/storage`. Toda descarga pasa por endpoints autenticados que verifican `institution_id`, titularidad docente o matrícula activa del estudiante (`EnrollmentStatus.ACTIVE`) y devuelven `Content-Disposition: attachment`. |
| **Escaneo Antimalware / Antivirus (ClamAV / ICAP)** | [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py) | **Pendiente de dependencia externa** | No existe cliente `clamd`, conector ICAP ni pipeline de desinfección (CDR) antes de persistir archivos subidos por docentes o estudiantes (`INT-003`). |
| **Adaptador de Videoconferencia BigBlueButton (`BBBAdapter`)** | [`bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py), [`factory.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/factory.py) | **Implementado / Probado (Con Mocks)** | Implementa `create`, `join`, `isMeetingRunning`, `getMeetingInfo`, `end` y `getRecordings` con firma criptográfica (`sha1`/`sha256`/`sha512`) y parseo XML seguro (`defusedxml`). Probado contra `httpx.MockTransport` y `MockMeetingProvider`. |
| **Infraestructura Externa de Servidor BigBlueButton en Vivo** | [`config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L130-L136) | **Pendiente de dependencia externa** | En el entorno actual `MEETING_PROVIDER_TYPE="mock"` y `BBB_SERVER_BASE_URL=""`. No hay un clúster BBB aprovisionado ni verificado en vivo. Faltan llamadas remotas `publishRecordings`/`deleteRecordings` (`INT-007`) y receptor de Webhooks (`INT-008`). |
| **Servicio de Correo Electrónico SMTP (`EmailService`)** | [`email_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/email_service.py) | **Parcialmente implementado / Pendiente de dependencia externa** | Implementa envío vía `smtplib.SMTP` con `asyncio.to_thread` y fallback controlado a modo `mock` cuando no hay credenciales. Carece de escape HTML (`INT-009`), validación explícita de contexto SSL/TLS y cola de reintentos. No conectado a un relay SMTP productivo verificado. |
| **Adaptador de Normalización de Datos Abiertos MEN (`MenOpenDataAdapter`)** | [`men_open_data_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/adapters/men_open_data_adapter.py) | **Implementado / Probado** | Normaliza códigos DANE (12 dígitos), códigos DANE de sede, municipios (5 dígitos), departamentos (2 dígitos), zonas y niveles educativos, aplicando compuertas de calidad (*Quality Gates*). |
| **Sincronización en Vivo con API SODA (`datos.gov.co`)** | [`official_catalog_sync_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py), [`harvest_due_dataset.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/harvest_due_dataset.py) | **Parcialmente implementado** | El endpoint administrativo `/institutions/official-catalog/sync` ingiere una semilla estática local (`official_dane_catalog.py`) en lugar de consultar `datos.gov.co` en tiempo real (`INT-011`). La descarga real reside en scripts CLI offline (`harvest_due_dataset.py`). |
| **Generadores de Documentos Oficiales y Manuales (`scripts/generate_*.py`)** | [`generate_government_pdfs.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/scripts/generate_government_pdfs.py), [`generate_men_presentation.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/scripts/generate_men_presentation.py) | **Implementado / Verificado (CLI Offline)** | Scripts independientes de construcción documental basados en `reportlab` y `python-pptx` que leen archivos Markdown estáticos del repositorio (`docs/government/`) y generan PDFs/PPTX locales. No están expuestos a entradas HTTP de usuarios. |

---

## 3. AUDITORÍA DE SEGURIDAD DE ALMACENAMIENTO DE ARCHIVOS Y DOCUMENTOS

### 3.1 Validación de Cargas (MIME Type, Extensiones, Magic Bytes, Tamaño y Memoria)
El servicio [`StorageService`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L20-L120) aplica las siguientes reglas en `validate_file()`:
- **Lista blanca de extensiones (`ALLOWED_EXTENSIONS`):** `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`, `.csv`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.zip`.
- **Verificación de Magic Bytes (`MAGIC_SIGNATURES`):**
  - `.pdf` $\rightarrow$ `%PDF-`
  - `.png` $\rightarrow$ `\x89PNG\r\n\x1a\n`
  - `.jpg` / `.jpeg` $\rightarrow$ `\xff\xd8\xff`
  - `.gif` $\rightarrow$ `GIF87a` / `GIF89a`
  - `.webp` $\rightarrow$ `RIFF` + `WEBP` en bytes `8:12`
  - `.zip`, `.docx`, `.xlsx`, `.pptx` $\rightarrow$ `PK\x03\x04`, `PK\x05\x06`, `PK\x07\x08`
  - `.doc`, `.xls`, `.ppt` $\rightarrow$ `\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1` (OLE2 Compound Document)
  - `.txt`, `.csv` $\rightarrow$ Rechazo si contiene `\x00` en los primeros 8192 bytes.

**Debilidades identificadas:**
1. **Lectura en memoria RAM sin streaming (`INT-001`):** Tanto en [`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L462) (`file_bytes = await file.read()`) como en [`student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L295) (`content = await file.read()`), se lee todo el cuerpo del archivo en memoria antes de invocar `storage.save_activity_resource()` o `storage.save_submission_attachment()`. Si no existe un proxy inverso (Nginx/Cloudflare) delante con `client_max_body_size` estricto, un atacante autenticado puede enviar múltiples peticiones concurrentes con archivos de varios gigabytes y provocar un fallo `MemoryError` / OOM Kill en el worker Uvicorn.
2. **Inconsistencia de límite documentado vs implementado:** El endpoint [`upload_student_submission_attachment`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L284) documenta un límite `<= 10MB`, mientras que `StorageService` aplica `MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024` (20 MB).
3. **Confianza en `declared_mime_type` y contenedores ZIP/OOXML (`INT-002`):** En [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L114), el tipo MIME retornado prioriza `declared_mime_type` (enviado por el navegador/cliente en el header multipart `Content-Type`) sin comprobar que coincida con la extensión validada. Ese valor se persiste en base de datos y se utiliza posteriormente como encabezado `media_type` al servir el archivo. Además, cualquier archivo `.zip` (incluyendo un archivo con ejecutables internos o una *zip bomb*) renombrado a `.docx` supera la validación de magic bytes `PK\x03\x04`.

### 3.2 Rutas de Almacenamiento, Nombres UUID y Protección contra Path Traversal
- **Prevención de Path Traversal:** [`LocalStorageProvider._resolve_safe_path()`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py#L25-L49) rechaza rutas vacías, rutas absolutas y segmentos `..`, resuelve la ruta canónica con `.resolve()` y verifica `candidate.relative_to(self.base_dir)`. Adicionalmente, los archivos nunca se guardan en disco con el nombre proporcionado por el usuario (`original_filename`); siempre se almacenan como `<resource_uuid>.<ext>` o `<attachment_uuid>.<ext>`.
- **Sanitización del nombre original:** `sanitize_filename()` elimina caracteres de control (`0x00-0x1f`, `0x7f`), reemplaza separadores `/` y `\`, elimina puntos iniciales y trunca a 200 caracteres.
- **Problema de longitud de ruta en Windows (`INT-005`):** La jerarquía de adjuntos de entregas estudiantiles definida en [`build_submission_attachment_path()`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L159-L173) concatena **cinco UUIDs** en niveles sucesivos:
  `<institution_id>/submissions/<activity_id>/<student_id>/<submission_id>/<attachment_id>.<ext>`
  Solo la ruta relativa mide ~195 caracteres. Combinada con la ruta base del proyecto en Windows (`c:\Users\...\backend\data\storage\...`), supera los **310 caracteres**, excediendo el límite `MAX_PATH` (260 caracteres) de las APIs Win32 estándar y provocando fallos `DirectoryNotFoundException` al recorrer `backend/data/storage` con herramientas administrativas de Windows/PowerShell o agentes de backup.

### 3.3 Autorización de Descarga y Aislamiento Multi-Inquilino
Se verificó que la aplicación FastAPI ([`main.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/main.py)) **no expone** ningún directorio de archivos mediante `StaticFiles`. Todas las descargas se realizan a través de cuatro endpoints autenticados que aplican controles estrictos de pertenencia institucional y académica:
1. `GET /api/v1/teacher/activities/{activity_id}/resources/{resource_id}/download` ([`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L510-L579)): Verifica que el docente pertenezca a la institución y sea titular de la asignación docente (`TeacherAssignment`) de la actividad.
2. `GET /api/v1/teacher/activities/{activity_id}/submissions/{submission_id}/attachments/{attachment_id}/download` ([`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L615-L683)): Verifica que la entrega pertenezca a una actividad de la asignación del docente en la misma institución.
3. `GET /api/v1/student/activities/{activity_id}/resources/{resource_id}/download` ([`student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L202-L237)): Verifica que el estudiante tenga matrícula `ACTIVE` en el grupo de la actividad, que la actividad esté en estado `PUBLISHED` y pertenezca a su `institution_id`.
4. `GET /api/v1/student/activities/{activity_id}/submission/attachments/{attachment_id}/download` ([`student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L346-L384)): Verifica que el adjunto pertenezca exclusivamente al `StudentSubmission` del estudiante autenticado (`student_id`).

Todos los endpoints fuerzan `headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}`, mitigando la ejecución inline de contenido activo en el navegador.

---

## 4. AUDITORÍA DE INTEGRACIONES EXTERNAS

### 4.1 Videoconferencia BigBlueButton (`backend/app/core/meeting/`)
- **Separación entre Adaptador e Infraestructura:** El adaptador [`BBBAdapter`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py) está completamente codificado y utiliza `defusedxml.ElementTree` para prevenir ataques XXE (*XML External Entity*) al parsear las respuestas XML de BBB. Sin embargo, el entorno opera por defecto con [`MockMeetingProvider`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/mock_provider.py) (`MEETING_PROVIDER_TYPE="mock"`).
- **Seguridad de Checksums y Secretos (`INT-006`):**
  - El método `_compute_checksum()` calcula `hash(call_name + query_string + shared_secret)` y `_verify_checksum()` utiliza `hmac.compare_digest()` en tiempo constante.
  - Por defecto, `BBB_SIGNING_ALGORITHM` está configurado en `"sha1"` en lugar de `"sha256"`.
  - En la tabla `virtual_classrooms`, los campos `moderator_password_hash` y `attendee_password_hash` almacenan las contraseñas generadas con `secrets.token_urlsafe(12)` **en texto plano**, ya que el protocolo de BBB exige enviar las contraseñas en claro en los parámetros `moderatorPW`, `attendeePW` y `password`.
- **Sincronización de Grabaciones y Webhooks (`INT-007`, `INT-008`):**
  - `RecordingService.publish_recording()` y `delete_recording()` solo actualizan o eliminan filas en PostgreSQL; `BBBAdapter` no implementa las llamadas remotas `publishRecordings` ni `deleteRecordings` hacia el servidor BBB.
  - No existe endpoint de Webhook para eventos de BBB (`meeting-ended`, `rap-publish-ended`), obligando a sincronizar grabaciones manualmente mediante `POST /recordings/classroom/{id}/sync`.

### 4.2 Correo Electrónico y SMTP (`backend/app/services/email_service.py`)
- **Comportamiento Dev/Prod y Protección de Credenciales:**
  - En [`config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L140-L148), las credenciales `SMTP_HOST`, `SMTP_USER` y `SMTP_PASSWORD` están vacías por defecto. Si no se configuran, `EmailService.is_configured()` devuelve `False` y el sistema registra un warning estructurado sin exponer tokens ni contraseñas en los logs, retornando estado `"mock"`.
  - Cuando está configurado, ejecuta `_send_smtp_sync()` en un hilo separado mediante `asyncio.to_thread()` con `timeout=10`.
- **Debilidades de Seguridad y Resiliencia (`INT-009`, `INT-010`):**
  - Las plantillas HTML interpolan `recipient_name`, `role_label` y `jurisdiction_label` sin `html.escape()`.
  - `server.starttls()` se invoca sin un contexto `ssl.create_default_context()` explícito y no se soporta conexión implícita TLS (`SMTP_SSL` en puerto 465).
  - En [`auth.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py#L287-L288), el enlace de recuperación de contraseña se construye concatenando `settings.FRONTEND_URL` en lugar de usar un método validado equivalente a `settings.build_invitation_url()`.

### 4.3 Fuentes de Datos Gubernamentales (`men_open_data_adapter.py`, `official_catalog_sync_service.py`)
- **Desconexión entre el Servicio de Sincronización y la API SODA (`INT-011`):**
  - El método [`OfficialCatalogSyncService.sync_national_catalog()`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py#L442-L502) invocado desde `POST /api/v1/institutions/official-catalog/sync` **no realiza peticiones HTTP** a `datos.gov.co`; importa la lista estática `OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET` desde `official_dane_catalog.py`.
  - El script de cosecha real [`harvest_due_dataset.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/harvest_due_dataset.py) usa `urllib.request.urlopen(..., timeout=30)` sin cabeceras `X-App-Token` de Socrata ni política de reintentos con *exponential backoff*.

---

## 5. EVALUACIÓN DE RIESGOS DE DEPENDENCIAS EXTERNAS

| Dependencia Externa | Propósito en PEVN | Mecanismo de Fallback Actual | Timeout / Retries Configurados | Nivel de Riesgo Operativo |
| :--- | :--- | :--- | :--- | :---: |
| **Servidor BigBlueButton (BBB API)** | Aulas virtuales sincrónicas y grabaciones de clase | Si falla `create`/`join`/`end`, lanza `MeetingProviderError` (HTTP 502). En `sync_recordings_from_provider`, si BBB falla, retorna las grabaciones locales en caché BD. | Timeout: `10.0s` (`BBB_REQUEST_TIMEOUT_SECONDS`).<br>Retries: **Ninguno (0)**. Sin connection pooling (`INT-008`). | **ALTO** |
| **Servidor / Relay SMTP** | Envío de invitaciones de onboarding y recuperación de contraseña | Si no está configurado, opera en modo `mock`. Si falla la entrega SMTP, captura la excepción, registra el error y persiste la invitación en BD (permitiendo reenvío posterior). | Timeout: `10s` en `smtplib.SMTP`.<br>Retries: **Ninguno (0)**. Sin cola asíncrona (`INT-009`). | **MEDIO** |
| **Portal Datos Abiertos Colombia (API SODA `datos.gov.co`)** | Cosecha del Directorio Único de Establecimientos Educativos (DUE / DANE) | La API web usa el catálogo semilla local (`official_dane_catalog.py`), por lo que una caída de `datos.gov.co` no interrumpe la operación del backend. | En CLI (`harvest_due_dataset.py`): Timeout `30s`, sin `X-App-Token`, sin retries (`INT-011`). | **BAJO** |
| **Sistema de Archivos Local (`backend/data/storage`)** | Persistencia de recursos docentes y entregas de estudiantes | Sin replicación ni almacenamiento objeto S3 externo. Si el disco local se llena o corrompe, las cargas y descargas fallan con HTTP 500/404. | Escritura síncrona bloqueante en el bucle de eventos (`Path.write_bytes`). | **ALTO** |

---

## 6. REGISTRO ESTRUCTURADO DE HALLAZGOS (`INT-001` A `INT-013`)

---

### `INT-001` — Lectura completa de archivos en memoria RAM (`await file.read()`) antes de validar el límite de tamaño (Riesgo de DoS por agotamiento de memoria / OOM)

- **Finding ID:** `INT-001`
- **Módulo afectado:**
  - [`backend/app/api/v1/endpoints/teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L460-L473) (línea 462)
  - [`backend/app/api/v1/endpoints/student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L280-L303) (líneas 284 y 295)
  - [`backend/app/core/storage/service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L67-L85) (líneas 67-85, 132-157, 175-204)
  - [`backend/app/core/storage/local.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py#L51-L67) (líneas 51-67)
- **Descripción:** Los controladores de carga de recursos docentes (`create_teacher_activity_resource`) y de entregas de estudiantes (`upload_student_submission_attachment`) ejecutan `await file.read()` sin especificar un tamaño máximo de lectura, cargando la totalidad del archivo subido en un objeto `bytes` en la memoria RAM del proceso Python antes de llamar a `StorageService.validate_file()`. Adicionalmente, existe una discrepancia entre el límite documentado en el portal estudiantil (`<= 10MB` en la descripción OpenAPI de `student_portal.py:284`) y el límite real codificado en `StorageService` (`MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024` = 20 MB). Finalmente, `LocalStorageProvider.save_file()` escribe los bytes de forma síncrona (`temp_path.write_bytes(content)`) dentro de una corrutina `async def`, bloqueando el event loop.
- **Causa raíz:** Diseño de la interfaz `StorageProviderInterface.save_file(relative_path: str, content: bytes)` basado en buffers completos en memoria en lugar de flujos por bloques (*chunked streaming*) con verificación incremental de bytes leídos.
- **Impacto:** Un usuario autenticado malintencionado puede enviar múltiples peticiones multipart concurrentes con archivos de gran tamaño (por ejemplo, 500 MB o 1 GB cada uno) y agotar la memoria RAM del contenedor/servidor antes de que se ejecute `if size > self.max_size_bytes`, provocando la caída del worker Uvicorn por *Out-Of-Memory (OOM)* y denegación de servicio para toda la plataforma.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  En [`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L460-L471):
  ```python
  if file is None:
      raise HTTPException(status_code=400, detail="Debe adjuntar un archivo cuando resource_type es FILE.")
  file_bytes = await file.read()  # <-- Carga ilimitada en RAM antes de validar tamaño
  resource_id = uuid.uuid4()
  storage = get_storage_service()
  try:
      stored = await storage.save_activity_resource(
          ...,
          content=file_bytes,
          declared_mime_type=file.content_type,
      )
  ```
- **Corrección recomendada:**
  1. Implementar un lector por fragmentos (`chunk_size = 64 * 1024`) sobre `UploadFile` que aborte inmediatamente con HTTP `413 Payload Too Large` o `400 Bad Request` en cuanto el acumulador supere `max_size_bytes + 1`, leyendo únicamente el primer bloque (8 KB) para validar los *magic bytes*.
  2. Unificar o parametrizar explícitamente el tamaño máximo permitido entre el portal docente (20 MB) y el portal estudiantil (10 MB o 20 MB según regla de negocio).
  3. Ejecutar las operaciones de escritura/lectura de disco mediante `asyncio.to_thread()` o `aiofiles` para no bloquear el bucle de eventos asíncrono.
- **Riesgo residual:** Bajo, una vez implementado el corte temprano por streaming y configurado `client_max_body_size 25m;` en el proxy inverso de borde.

---

### `INT-002` — Confianza en `declared_mime_type` suministrado por el cliente y validación superficial de contenedores ZIP/OOXML

- **Finding ID:** `INT-002`
- **Módulo afectado:**
  - [`backend/app/core/storage/service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L40-L52) (líneas 40-52 y 103-116)
  - [`backend/app/api/v1/endpoints/teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L570-L579) (líneas 572 y 676)
  - [`backend/app/api/v1/endpoints/student_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/student_portal.py#L228-L237) (líneas 229 y 378)
- **Descripción:** En `StorageService.validate_file()`, el tipo MIME devuelto se asigna mediante `mime_type = declared_mime_type or guessed_mime or "application/octet-stream"`, priorizando ciegamente el encabezado `Content-Type` enviado por el cliente en la petición HTTP multipart (`file.content_type`). Ese `mime_type` se guarda en base de datos y se envía como encabezado `Content-Type` (`media_type=resource.mime_type`) al descargar el archivo. Además, los formatos `.docx`, `.xlsx`, `.pptx` y `.zip` se validan únicamente comprobando que los primeros 4 bytes sean `PK\x03\x04`, sin verificar la existencia de `[Content_Types].xml` en documentos Office ni evaluar ratios de compresión anómalos (*zip bombs*). Tampoco se incluye el encabezado `X-Content-Type-Options: nosniff` en las respuestas de descarga.
- **Causa raíz:** Priorización de `declared_mime_type` sobre el mapa canónico de tipos MIME derivado de la extensión/firma binaria validada.
- **Impacto:** Un usuario puede subir un archivo `.txt` o `.pdf` válido pero declarar `Content-Type: text/html` o un tipo arbitrario que quedará almacenado en la base de datos y será emitido por el servidor en las descargas. Asimismo, cualquier archivo comprimido `.zip` que contenga binarios maliciosos o bombas de descompresión puede subirse camuflado con extensión `.docx`.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`backend/app/core/storage/service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L112-L115):
  ```python
  guessed_mime, _ = mimetypes.guess_type(safe_name)
  mime_type = declared_mime_type or guessed_mime or "application/octet-stream"
  return safe_name, ext, mime_type
  ```
- **Corrección recomendada:**
  1. Definir un diccionario inmutable `EXTENSION_TO_CANONICAL_MIME` en `StorageService` e ignorar `declared_mime_type` para determinar el `mime_type` almacenado (o rechazar la carga si `declared_mime_type` difiere del esperado).
  2. Para extensiones `.docx`, `.xlsx` y `.pptx`, inspeccionar el directorio central del archivo ZIP con `zipfile.ZipFile` verificando que contenga `[Content_Types].xml` y que la suma de tamaños descomprimidos (`file_size`) de sus entradas no supere un umbral seguro (ej. 100 MB) ni exceda un número máximo de entradas (ej. 1000 archivos).
  3. Añadir `"X-Content-Type-Options": "nosniff"` en las cabeceras de respuesta de todos los endpoints de descarga.
- **Riesgo residual:** Bajo.

---

### `INT-003` — Ausencia de escaneo antimalware (ClamAV / ICAP) en cargas de archivos de docentes y estudiantes

- **Finding ID:** `INT-003`
- **Módulo afectado:** [`backend/app/core/storage/service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L67-L116)
- **Descripción:** El flujo de carga de archivos valida tamaño, extensión y firma mágica inicial, pero carece de integración con un motor de análisis antimalware (como ClamAV a través de socket TCP/Unix `clamd` o un servidor ICAP corporativo) antes de almacenar los archivos en el repositorio institucional y ponerlos a disposición de docentes y estudiantes.
- **Causa raíz:** Funcionalidad de escaneo antivirus no implementada (pendiente de dependencia externa e integración de adaptador).
- **Impacto:** Un estudiante o cuenta comprometida podría adjuntar un documento PDF con JavaScript embebido malicioso, un documento Office `.doc`/`.xls` con macros VBA maliciosas (permitidos actualmente en `ALLOWED_EXTENSIONS`) o un archivo `.zip` con malware, utilizando la plataforma oficial como vector de distribución hacia los equipos de docentes y compañeros.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:** En [`service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L22-L38), se permiten formatos legados `.doc`, `.xls` y `.ppt` (contenedores binarios OLE2 propensos a macros) y archivos `.zip` sin ninguna etapa de escaneo antivirus en `save_activity_resource()` ni en `save_submission_attachment()`.
- **Corrección recomendada:**
  1. Integrar un adaptador `MalwareScannerInterface` en `backend/app/core/storage/` con soporte para ClamAV (`INSTREAM` vía socket TCP hacia contenedor `clamav/clamav`) configurable mediante variables `MALWARE_SCAN_ENABLED`, `CLAMAV_HOST`, `CLAMAV_PORT` y política *fail-closed* en producción.
  2. Retirar las extensiones binarias legadas de Office (`.doc`, `.xls`, `.ppt`) de `ALLOWED_EXTENSIONS`, permitiendo únicamente los formatos modernos libres de macros (`.docx`, `.xlsx`, `.pptx`).
- **Riesgo residual:** Bajo con ClamAV activo y bloqueo de formatos legados con macros.

---

### `INT-004` — Orfandad de archivos físicos en disco y omisión de `await db.commit()` al eliminar actividades académicas

- **Finding ID:** `INT-004`
- **Módulo afectado:**
  - [`backend/app/api/v1/endpoints/teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L387-L407) (líneas 387-407: `delete_teacher_activity`)
  - [`backend/app/services/teacher_portal_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/teacher_portal_service.py#L703-L729) (líneas 703-729: `delete_activity`)
- **Descripción:** Se identificaron dos defectos combinados en el ciclo de vida de eliminación de actividades académicas:
  1. El endpoint `DELETE /api/v1/teacher/activities/{activity_id}` llama a `await TeacherPortalService.delete_activity(...)` y retorna inmediatamente `Response(status_code=status.HTTP_204_NO_CONTENT)` **sin ejecutar `await db.commit()`**. Dado que `delete_activity` solo ejecuta `await db.delete(activity)` y `await db.flush()`, al finalizar la petición la sesión SQLAlchemy hace rollback implícito y la actividad nunca se elimina realmente en la base de datos.
  2. `TeacherPortalService.delete_activity()` elimina la entidad `AcademicActivity` (cuyas relaciones ORM tienen `cascade="all, delete-orphan"` sobre `ActivityResource` y `StudentSubmission` $\rightarrow$ `SubmissionAttachment`), pero **nunca recopila las rutas `storage_path` ni invoca `storage.delete_file()`**, dejando todos los archivos físicos de recursos docentes y entregas estudiantiles huérfanos en `data/storage/` de forma indefinida.
- **Causa raíz:** Omisión de `await db.commit()` en el controlador `delete_teacher_activity` y ausencia de limpieza de archivos físicos en `TeacherPortalService.delete_activity()`.
- **Impacto:** Fallo funcional del borrado de actividades en estado `DRAFT` (retorna `204 No Content` falso mientras el registro persiste en BD) y acumulación progresiva de archivos huérfanos en el almacenamiento sin referencia en base de datos, incumpliendo políticas de retención y agotando el espacio en disco.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  En [`teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L398-L407):
  ```python
  await TeacherPortalService.delete_activity(
      db=db,
      institution_id=inst_id,
      teacher_id=current_user.id,
      activity_id=activity_id,
  )
  # FALTA: await db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)
  ```
- **Corrección recomendada:**
  1. Antes de eliminar `activity` en `TeacherPortalService.delete_activity()`, consultar las rutas `storage_path` de todos sus `ActivityResource` y `SubmissionAttachment` asociados.
  2. Ejecutar `await db.commit()` en `delete_teacher_activity` y, una vez confirmada la transacción en BD, invocar `await storage.delete_file(path)` para cada ruta recopilada.
- **Riesgo residual:** Nulo tras aplicar el commit y la recolección de archivos post-commit.

---

### `INT-005` — Estructura de rutas de almacenamiento con 5 UUIDs anidados supera el límite `MAX_PATH` (260 caracteres) en sistemas Windows y herramientas de backup

- **Finding ID:** `INT-005`
- **Módulo afectado:**
  - [`backend/app/core/storage/service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py#L159-L173) (líneas 159-173: `build_submission_attachment_path`)
  - [`backend/app/core/storage/local.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py#L51-L55)
- **Descripción:** `StorageService.build_submission_attachment_path()` construye rutas relativas con 5 identificadores UUID anidados: `<institution_id>/submissions/<activity_id>/<student_id>/<submission_id>/<attachment_id>.<ext>`. Esta estructura consume ~195 caracteres únicamente en la ruta relativa. Cuando se combina con un directorio raíz estándar en entornos Windows, la ruta absoluta supera ampliamente los 260 caracteres (`MAX_PATH`). Aunque `LocalStorageProvider._to_io_path()` aplica el prefijo `\\?\` en Windows para evitar que Python falle al escribir, las herramientas del sistema operativo, scripts de respaldo y utilidades de inspección de directorios fallan con `DirectoryNotFoundException`.
- **Causa raíz:** Anidamiento excesivo y redundante de identificadores UUID en la jerarquía de directorios (dado que `submission_id` y `attachment_id` ya son globalmente únicos y la relación con `activity_id` y `student_id` ya existe en la base de datos).
- **Impacto:** Errores operativos en copias de seguridad, sincronización de volúmenes, escáneres de seguridad en host y herramientas de administración sobre entornos Windows.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:** Durante la auditoría, la ejecución de `Get-ChildItem -Path "backend" -Recurse` en PowerShell arrojó errores `DirectoryNotFoundException` exactamente sobre los directorios generados en `backend\data\storage\f0e1f26a-fd4c-43be-b52e-8545df2bf682\submissions\06640c10-c9c8-4c4e-958a-832d53184569\15a8bf6c-823a-4161-99e4-3fcfaad07d5a` debido al desbordamiento de `MAX_PATH`.
- **Corrección recomendada:** Simplificar la ruta relativa de adjuntos a `<institution_id>/submissions/<submission_id>/<attachment_id>.<ext>` (reduciendo la longitud en 74 caracteres sin perder aislamiento por institución ni por entrega).
- **Riesgo residual:** Nulo.

---

### `INT-006` — Almacenamiento en texto plano de contraseñas de reunión (`moderator_password_hash`, `attendee_password_hash`), uso de SHA-1 por defecto y falta de bloqueo del proveedor Mock en producción

- **Finding ID:** `INT-006`
- **Módulo afectado:**
  - [`backend/app/services/virtual_classroom_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/virtual_classroom_service.py#L115-L143) (líneas 116-117, 141-142, 207-208, 285, 313, 388)
  - [`backend/app/models/virtual_classroom.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/virtual_classroom.py#L139-L148) (líneas 139-148)
  - [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L130-L136) (líneas 130-136 y 199-243)
  - [`backend/app/core/meeting/bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py#L50) (líneas 50 y 102-104)
- **Descripción:**
  1. En `VirtualClassroomService.create_classroom()`, se generan contraseñas aleatorias `mod_pw = secrets.token_urlsafe(12)` y `att_pw = secrets.token_urlsafe(12)` y se guardan **en texto plano** en las columnas `moderator_password_hash` y `attendee_password_hash` de la tabla `virtual_classrooms`. Aunque los nombres de columna sugieren que son hashes, el código las lee directamente como contraseñas en claro para pasarlas a BigBlueButton en `join_classroom()` y `end_classroom()`.
  2. La configuración por defecto en `config.py` y `BBBAdapter` define `BBB_SIGNING_ALGORITHM: str = "sha1"`. Las versiones modernas de BigBlueButton (2.6 / 2.7 / 3.0) soportan `sha256` y `sha512`, siendo SHA-1 criptográficamente débil.
  3. El validador `validate_production_security` en `config.py` no verifica que en entornos `production`/`staging` no se utilice `MEETING_PROVIDER_TYPE="mock"` ni valida una longitud/entropía mínima para `BBB_SHARED_SECRET`.
- **Causa raíz:** Nomenclatura engañosa en el esquema de base de datos sin capa de cifrado simétrico en reposo (Fernet / AES-GCM) para secretos recuperables, y valores por defecto heredados de especificaciones antiguas de BBB.
- **Impacto:** Cualquier exposición de solo lectura de la tabla `virtual_classrooms` (backups, logs SQL o inyección en lectura) compromete las contraseñas de moderador de todas las aulas virtuales activas y programadas, permitiendo a un atacante forjar o controlar sesiones en el servidor BBB. Asimismo, un despliegue en producción con variables por defecto dejaría las aulas operando sobre `MockMeetingProvider` (generando URLs falsas `https://mock-bbb.pevn.edu.co/...`).
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  En [`virtual_classroom_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/virtual_classroom_service.py#L116-L143):
  ```python
  mod_pw = secrets.token_urlsafe(12)
  att_pw = secrets.token_urlsafe(12)
  ...
  classroom = VirtualClassroom(
      ...,
      moderator_password_hash=mod_pw,
      attendee_password_hash=att_pw,
  )
  ```
- **Corrección recomendada:**
  1. Cifrar simétricamente `mod_pw` y `att_pw` con `cryptography.fernet.Fernet` (derivando la clave desde una clave maestra de configuración `FIELD_ENCRYPTION_KEY`) antes de persistirlos en BD, y descifrarlos en memoria únicamente al invocar a `IMeetingProvider`.
  2. Cambiar el valor por defecto de `BBB_SIGNING_ALGORITHM` a `"sha256"` en `config.py` y `BBBAdapter`.
  3. Agregar en `Settings.validate_production_security()` una validación que exija `BBB_SHARED_SECRET` de al menos 32 caracteres cuando `MEETING_PROVIDER_TYPE == "bbb"` y bloquee `MEETING_PROVIDER_TYPE == "mock"` en `production`.
- **Riesgo residual:** Bajo.

---

### `INT-007` — Desincronización del ciclo de vida de grabaciones entre la base de datos local y el servidor BigBlueButton (`publish_recording`, `delete_recording`) y paginación en memoria

- **Finding ID:** `INT-007`
- **Módulo afectado:**
  - [`backend/app/services/recording_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/recording_service.py#L117-L197) (líneas 117-197)
  - [`backend/app/core/meeting/interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/interfaces.py#L80-L114)
  - [`backend/app/core/meeting/bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py#L283-L335)
  - [`backend/app/api/v1/endpoints/recordings.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py#L83-L103) (líneas 83-103)
- **Descripción:**
  1. `IMeetingProvider` y `BBBAdapter` solo implementan `get_recordings()` (`getRecordings`), pero carecen de los métodos `publish_recording(record_id, publish)` (`publishRecordings`) y `delete_recording(record_id)` (`deleteRecordings`). Cuando un docente o rector despublica o elimina una grabación desde PEVN, `RecordingService` solo actualiza o borra el registro en PostgreSQL (`meeting_recordings`). En consecuencia: (a) la grabación permanece publicada y accesible públicamente en el servidor BigBlueButton externo para cualquiera que posea el `playback_url` previo, y (b) si se ejecuta nuevamente `POST /recordings/classroom/{id}/sync`, la grabación "eliminada" vuelve a importarse y reaparece en la plataforma.
  2. En [`recordings.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py#L100-L102), cuando se consulta `GET /api/v1/recordings/` sin `classroom_id`, el controlador descarga **todas** las grabaciones de la institución en memoria (`all_recs = list((await db.execute(query)).scalars().all())`) y aplica la paginación en Python (`all_recs[skip : skip + limit]`).
- **Causa raíz:** Implementación incompleta de la interfaz de gestión de grabaciones de BigBlueButton y ausencia de consulta SQL paginada (`OFFSET`/`LIMIT` + `COUNT(*)`) en el listado general de grabaciones.
- **Impacto:** Fuga de privacidad/incumplimiento de borrado de grabaciones de menores de edad en el servidor de videoconferencia externo, reaparición de grabaciones borradas tras sincronización, y degradación de rendimiento al crecer el histórico institucional de grabaciones.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`recording_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/recording_service.py#L172-L197), `delete_recording()` solo ejecuta `await db.delete(rec)` sin invocar a `get_meeting_provider()`.
  En [`recordings.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py#L100-L102):
  ```python
  all_recs = list((await db.execute(query)).scalars().all())
  total = len(all_recs)
  recordings = all_recs[skip : skip + limit]
  ```
- **Corrección recomendada:**
  1. Añadir `publish_recording(record_id: str, publish: bool) -> bool` y `delete_recording(record_id: str) -> bool` a `IMeetingProvider`, implementando las llamadas `publishRecordings` y `deleteRecordings` en `BBBAdapter` e invocándolas desde `RecordingService` antes de confirmar el cambio en BD.
  2. Reemplazar la carga completa en memoria en `list_institution_recordings` por una consulta `select(func.count())` seguida de `query.offset(skip).limit(limit)`.
- **Riesgo residual:** Bajo.

---

### `INT-008` — Ausencia de Webhooks autenticados de BigBlueButton y creación repetitiva de `httpx.AsyncClient` sin connection pooling ni reintentos

- **Finding ID:** `INT-008`
- **Módulo afectado:**
  - [`backend/app/core/meeting/bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py#L123-L143) (líneas 123-143)
  - [`backend/app/api/v1/endpoints/virtual_classrooms.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/virtual_classrooms.py)
  - [`backend/app/api/v1/endpoints/recordings.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py)
- **Descripción:**
  1. El backend no dispone de un endpoint receptor de Webhooks de BigBlueButton (con validación de firma HMAC/checksum) para procesar eventos asíncronos del servidor de medios (`meeting-ended`, `user-joined`, `user-left`, `rap-publish-ended`). Si un estudiante cierra la pestaña de BBB directamente sin regresar al portal a pulsar "Salir" (`POST /leave`), su registro `ClassroomAttendance` queda con `left_at = None` hasta que el docente cierre manualmente el aula (`POST /end`), y las grabaciones procesadas por BBB no se sincronizan automáticamente.
  2. En `BBBAdapter._send_request()`, cuando `self._http_client` es `None` (comportamiento en producción), se instancia y destruye un nuevo `httpx.AsyncClient(timeout=self.timeout)` en cada llamada individual (`async with httpx.AsyncClient(...) as client:`), realizando un handshake TCP y TLS completo en cada petición y sin ninguna política de reintento ante errores de red transitorios.
- **Causa raíz:** Arquitectura de integración con BBB basada exclusivamente en *polling*/acciones manuales del usuario y cliente HTTP efímero por petición.
- **Impacto:** Mayor latencia y consumo de sockets bajo alta concurrencia de ingreso a clases virtuales (ej. inicio de jornada escolar a las 7:00 AM), fallos inmediatos (HTTP 502) ante micro-cortes de red con el servidor BBB, e imprecisión en los tiempos de permanencia (`duration_minutes`) de estudiantes que cierran la ventana de videoconferencia.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`bbb_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/meeting/bbb_adapter.py#L126-L131):
  ```python
  if self._http_client is not None:
      response = await self._http_client.get(url, timeout=self.timeout)
  else:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
          response = await client.get(url)
  ```
- **Corrección recomendada:**
  1. Mantener un cliente compartido `httpx.AsyncClient` con `httpx.Limits(max_keepalive_connections=20, max_connections=100)` gestionado en el ciclo de vida (`lifespan`) de FastAPI y añadir 2 reintentos con backoff corto para operaciones idempotentes (`isMeetingRunning`, `getMeetingInfo`, `getRecordings`).
  2. Implementar un endpoint `POST /api/v1/webhooks/bbb` que verifique la firma `checksum` del callback con `BBB_SHARED_SECRET` y actualice automáticamente el estado del aula, la salida de participantes y las grabaciones publicadas.
- **Riesgo residual:** Bajo.

---

### `INT-009` — Posible inyección HTML en plantillas de correo y falta de contexto SSL/TLS explícito y cola de reintentos en `EmailService`

- **Finding ID:** `INT-009`
- **Módulo afectado:** [`backend/app/services/email_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/email_service.py#L75-L290) (líneas 75-165 y 199-282)
- **Descripción:**
  1. `EmailService.send_invitation_email()` y `send_password_reset_email()` construyen el cuerpo HTML interpolando directamente `recipient_name`, `role_label` y `jurisdiction_label` mediante f-strings sin aplicar `html.escape()`. Si un nombre de destinatario o jurisdicción contiene etiquetas HTML (`<a href="https://malicioso.co">...</a>` o `<img src=...>`), estas se inyectan directamente en el correo oficial enviado desde el dominio institucional.
  2. En `_send_smtp_sync()` (líneas 161 y 278), se invoca `server.starttls()` sin pasar `context=ssl.create_default_context()`, por lo que en la biblioteca estándar de Python `smtplib` no se fuerza la verificación de cadena de certificados ni de hostname del servidor SMTP a menos que se suministre un `SSLContext`. Tampoco se soporta `smtplib.SMTP_SSL` para proveedores que operan en el puerto 465.
  3. El atributo `_mock_delivery_status = "sent"` (línea 24) está declarado como variable de clase compartida en lugar de parámetro de instancia, y no existe mecanismo de reintento ante errores SMTP transitorios (`421`/`450`).
- **Causa raíz:** Interpolación directa de cadenas en plantillas HTML y configuración básica de `smtplib.SMTP`.
- **Impacto:** Riesgo de inyección de contenido HTML (phishing dentro de correos legítimos de la plataforma), susceptibilidad a interceptación MitM en el tramo hacia el servidor SMTP si no se valida el certificado TLS, y pérdida de correos de recuperación de contraseña ante fallos transitorios del relay SMTP.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`email_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/email_service.py#L94-L162):
  ```python
  <p>Estimado/a <strong>{recipient_name}</strong>,</p>
  <p>Ha sido designado/a como <strong>{role_label}</strong> para la jurisdicción <strong>{jurisdiction_label}</strong>...</p>
  ...
  with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
      if settings.SMTP_TLS:
          server.starttls()  # <-- Sin context=ssl.create_default_context()
  ```
- **Corrección recomendada:**
  1. Sanitizar todas las variables interpoladas en las plantillas HTML con `html.escape(str(val), quote=True)` y limpiar saltos de línea (`\r`, `\n`) en `Subject` y `To` para prevenir inyección de cabeceras SMTP.
  2. Pasar explícitamente `context=ssl.create_default_context()` a `server.starttls(context=...)` y soportar `smtplib.SMTP_SSL` cuando `settings.SMTP_PORT == 465`.
  3. Despachar el envío de correos a través de `BackgroundTasks` o una cola con política de hasta 3 reintentos con *exponential backoff*.
- **Riesgo residual:** Bajo.

---

### `INT-010` — Inconsistencia en la construcción del enlace de recuperación de contraseña en `auth.py` frente a `Settings.build_invitation_url()`

- **Finding ID:** `INT-010`
- **Módulo afectado:**
  - [`backend/app/api/v1/endpoints/auth.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py#L285-L295) (líneas 287-288)
  - [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L293-L356) (líneas 293-356)
- **Descripción:** En `config.py`, el método `Settings.build_invitation_url()` implementa controles de seguridad rigurosos para construir enlaces enviados por correo: prioriza `FRONTEND_PUBLIC_URL` sobre `FRONTEND_URL`, exige esquema `https://` en entornos `production`/`staging`, bloquea hosts locales (`localhost`, `127.0.0.1`) en producción y codifica los parámetros con `urlencode()`. Sin embargo, el endpoint `POST /api/v1/auth/password-recovery` en `auth.py` omite esta lógica y construye el enlace manualmente con `base_url = settings.FRONTEND_URL.rstrip("/")` y `reset_link = f"{base_url}/reset-password?token={raw_token}"`.
- **Causa raíz:** Falta de un método centralizado `Settings.build_password_reset_url(token)` en `config.py` análogo a `build_invitation_url()`.
- **Impacto:** En despliegues donde se configure `FRONTEND_PUBLIC_URL` pero `FRONTEND_URL` conserve su valor por defecto (`http://localhost:5173`), los correos de recuperación de contraseña enviarán enlaces rotos apuntando a `localhost` o por canal no cifrado `http://`.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`auth.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py#L287-L288):
  ```python
  base_url = settings.FRONTEND_URL.rstrip("/")
  reset_link = f"{base_url}/reset-password?token={raw_token}"
  ```
- **Corrección recomendada:** Implementar `Settings.build_password_reset_url(token: str) -> str` reutilizando `resolve_frontend_base_url()` y `urlencode({"token": token})`, e invocarlo desde `auth.py`.
- **Riesgo residual:** Nulo.

---

### `INT-011` — Sincronización del catálogo nacional (`OfficialCatalogSyncService.sync_national_catalog`) ingiere semilla estática local con consultas N+1 en lugar de consultar la API SODA de Datos Abiertos

- **Finding ID:** `INT-011`
- **Módulo afectado:**
  - [`backend/app/services/official_catalog_sync_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py#L153-L250) (líneas 153-250 y 442-502)
  - [`backend/app/db/seeds/official_dane_catalog.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/official_dane_catalog.py#L1-L35)
  - [`backend/app/db/seeds/harvest_due_dataset.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/harvest_due_dataset.py#L33-L98)
  - [`backend/app/db/seeds/ingest_dataset2_sedes.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/ingest_dataset2_sedes.py#L32-L40)
- **Descripción:**
  1. `OfficialCatalogSyncService.sync_national_catalog()` (invocado por `POST /api/v1/institutions/official-catalog/sync`) no se conecta a la API SODA de Datos Abiertos (`datos.gov.co`); únicamente importa el arreglo estático `OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET` desde `official_dane_catalog.py`.
  2. La descarga real desde `datos.gov.co` está aislada en el script CLI [`harvest_due_dataset.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/harvest_due_dataset.py), el cual utiliza `urllib.request.urlopen` síncrono sin soporte de cabecera `X-App-Token` de Socrata (exponiéndose a *throttling* HTTP 429) y sin reintentos con backoff exponencial. A su vez, [`ingest_dataset2_sedes.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/seeds/ingest_dataset2_sedes.py#L34) apunta a una ruta temporal `scratch/official_sedes_dataset_x5ay.json` no versionada en el repositorio.
  3. Durante la ingesta en [`ingest_official_records()`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py#L168-L185), por cada establecimiento del lote se ejecutan múltiples consultas `SELECT` individuales (`Institution` por `dane_code`, `Institution` por `nit`, y `Campus` por cada sede), generando un patrón $N+1$ que degrada el tiempo de respuesta ante catálogos de miles de instituciones.
- **Causa raíz:** Separación entre el script de cosecha SODA y el servicio de sincronización del backend, sumado a consultas individuales fila por fila en el bucle de ingesta.
- **Impacto:** El botón/endpoint de sincronización del catálogo nacional solo recarga el snapshot estático empaquetado en el código y puede exceder el timeout HTTP de la petición al procesar miles de sedes fila por fila.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  En [`official_catalog_sync_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/official_catalog_sync_service.py#L463-L469):
  ```python
  from app.db.seeds.official_dane_catalog import OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET
  ...
  metrics = await cls.ingest_official_records(
      db,
      records=OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET,
      source_label="MEN_DANE_NATIONAL_CATALOG",
      ...
  )
  ```
- **Corrección recomendada:**
  1. Incorporar en `MenOpenDataAdapter` un método asíncrono `fetch_soda_dataset(resource_id, app_token, timeout, max_retries)` usando `httpx.AsyncClient` con backoff exponencial (1s, 2s, 4s) ante códigos `429`/`502`/`503`/`504`, manteniendo `OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET` como fallback explícito si `datos.gov.co` no está disponible.
  2. Pre-cargar en bloque (`WHERE dane_code IN (...)`) las instituciones y sedes existentes por lotes de 500 registros para eliminar las consultas $N+1$.
- **Riesgo residual:** Bajo.

---

### `INT-012` — Agrupación ambigua de filas malformadas bajo la clave `"UNKNOWN"` en `MenOpenDataAdapter`

- **Finding ID:** `INT-012`
- **Módulo afectado:** [`backend/app/adapters/men_open_data_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/adapters/men_open_data_adapter.py#L351-L364) (líneas 351-364)
- **Descripción:** En `MenOpenDataAdapter.group_flat_rows_into_establishments()`, cuando `cls.normalize_record(row)` lanza cualquier excepción, el bloque `except Exception:` captura silenciosamente el error y agrupa todas las filas sin `codigo_dane` bajo una única entrada `grouped["UNKNOWN"]`. Si un lote plano contiene 50 filas corruptas sin código DANE, estas se fusionan en un único registro `"UNKNOWN"` antes de pasar por las compuertas de calidad (*Quality Gates*), subreportando el conteo real de registros rechazados (`records_rejected`) y omitiendo el motivo exacto de la excepción en los logs.
- **Causa raíz:** Uso de una clave estática `"UNKNOWN"` en el diccionario `grouped` cuando falla la normalización de una fila plana sin código DANE.
- **Impacto:** Subregistro en las métricas de rechazo (`records_rejected`) y pérdida de trazabilidad de errores de parseo en lotes de datos sucios.
- **Severidad:** `LOW`
- **Evidencia / Reproducción:**
  En [`men_open_data_adapter.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/adapters/men_open_data_adapter.py#L353-L364):
  ```python
  except Exception:
      raw_dane = str(row.get("codigo_dane", "")).strip() or "UNKNOWN"
      if raw_dane not in grouped:
          grouped[raw_dane] = { ... }
  ```
- **Corrección recomendada:** Asignar una clave única por índice de fila fallida (`f"INVALID_ROW_{idx}"`) y registrar la excepción con `logger.debug` o `logger.warning` para que cada fila corrupta sea contabilizada individualmente por `evaluate_record_quality()`.
- **Riesgo residual:** Nulo.

---

### `INT-013` — Validación incompleta de esquema HTTP/HTTPS en recursos docentes tipo `URL` por formulario multipart y fragilidad de regex XML en scripts generadores de PDF

- **Finding ID:** `INT-013`
- **Módulo afectado:**
  - [`backend/app/api/v1/endpoints/teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py#L444-L488) (líneas 444-488)
  - [`backend/app/services/teacher_portal_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/teacher_portal_service.py#L747-L765) (líneas 747-765)
  - [`scripts/generate_government_pdfs.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/scripts/generate_government_pdfs.py#L238-L263) (líneas 238-263)
- **Descripción:**
  1. Mientras el endpoint JSON `POST /api/v1/teacher/activities/{activity_id}/resources/url` valida la URL mediante el esquema Pydantic `ActivityUrlResourceCreate` (`url: AnyHttpUrl`), el endpoint multipart `POST /api/v1/teacher/activities/{activity_id}/resources` recibe `url: Annotated[str | None, Form()] = None` y `TeacherPortalService.add_activity_resource()` solo comprueba `if not url or not url.strip():`, permitiendo almacenar esquemas peligrosos como `javascript:...` o `data:...` cuando `resource_type="URL"`.
  2. En los scripts CLI de generación documental (`scripts/generate_government_pdfs.py`, `generate_institutional_user_guide_pdf.py`, `generate_men_technical_report_pdf.py`), la función `md_inline_to_xml()` escapa `&`, `<`, `>` y luego transforma marcadores Markdown (`**`, `*`, `` ` ``) en etiquetas XML de ReportLab (`<b>`, `<i>`, `<font>`). Aunque actualmente solo procesan documentación estática del repositorio, si se reutilizaran en el backend con texto ingresado por usuarios con asteriscos/backticks anidados desbalanceados, el parser XML de `reportlab.platypus.Paragraph` lanzaría `ValueError` / `ExpatError`.
- **Causa raíz:** Falta de validación `AnyHttpUrl` o `urllib.parse.urlparse` (exigiendo `scheme in {"http", "https"}`) en `TeacherPortalService.add_activity_resource()`.
- **Impacto:** Riesgo de XSS basado en DOM si el frontend renderiza el `external_url` de un recurso tipo `URL` en un atributo `<a href="...">` sin validar que el esquema sea `http://` o `https://`.
- **Severidad:** `LOW`
- **Evidencia / Reproducción:**
  En [`teacher_portal_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/teacher_portal_service.py#L747-L751):
  ```python
  if r_type == ActivityResourceType.URL:
      if not url or not url.strip():
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="La URL es obligatoria para recursos tipo URL.",
          )
  ```
- **Corrección recomendada:** Validar en `TeacherPortalService.add_activity_resource()` que `urlparse(url.strip()).scheme.lower() in {"http", "https"}` y que posea `netloc` válido antes de persistir el recurso.
- **Riesgo residual:** Nulo.

---

## 7. PLAN DE REMEDIACIÓN PRIORIZADO

1. **Fase 1 — Inmediata (Bloqueantes de Seguridad y Estabilidad - `HIGH`):**
   - **`INT-001`:** Reemplazar `await file.read()` por lectura en streaming con corte temprano al superar `max_size_bytes` en `teacher_portal.py` y `student_portal.py`.
   - **`INT-004`:** Añadir `await db.commit()` en `delete_teacher_activity` y eliminar del almacenamiento los archivos físicos asociados a la actividad eliminada.
   - **`INT-006`:** Cifrar con Fernet las contraseñas de reunión BBB en `virtual_classrooms`, cambiar `BBB_SIGNING_ALGORITHM` a `"sha256"` por defecto y prohibir `MEETING_PROVIDER_TYPE="mock"` en `production`.
2. **Fase 2 — Corto Plazo (Endurecimiento de Integraciones y Archivos - `MEDIUM`):**
   - **`INT-002` y `INT-003`:** Asignar el `mime_type` desde un mapa canónico por extensión, validar estructura interna de archivos ZIP/OOXML, agregar `X-Content-Type-Options: nosniff` e integrar escaneo ClamAV.
   - **`INT-005`:** Acortar la jerarquía de directorios de `build_submission_attachment_path` para evitar desbordamientos `MAX_PATH` en Windows.
   - **`INT-007` y `INT-008`:** Implementar `publishRecordings` y `deleteRecordings` en `BBBAdapter`, paginar en SQL `list_institution_recordings`, reutilizar `httpx.AsyncClient` con pool de conexiones y habilitar Webhooks firmados de BBB.
   - **`INT-009` y `INT-010`:** Aplicar `html.escape()` en `EmailService`, pasar `ssl.create_default_context()` a `starttls()` y centralizar la generación de `reset_link` en `Settings.build_password_reset_url()`.
   - **`INT-011`:** Optimizar `ingest_official_records` mediante consultas por lotes (eliminando el patrón $N+1$) y añadir cliente SODA asíncrono con reintentos y `X-App-Token`.
3. **Fase 3 — Mejora Continua (`LOW`):**
   - **`INT-012` y `INT-013`:** Desagregar claves de filas fallidas en `MenOpenDataAdapter` y forzar esquema `http`/`https` en `TeacherPortalService.add_activity_resource()`.
