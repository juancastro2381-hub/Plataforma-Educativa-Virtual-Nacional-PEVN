# INFORME DE EJECUCIÓN TÉCNICA — FASE B3-H11
## RECURSOS PEDAGÓGICOS DE ACTIVIDADES ACADÉMICAS + INFRAESTRUCTURA DE ALMACENAMIENTO SEGURO
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** Septiembre 2026  
**Estado del Gate:**
* **`B3-H11 TECHNICAL VERIFICATION = PASS`**
* **`B3-H11 HUMAN VALIDATION = PENDING`**
* **`B3-H11 CERTIFICATION = NOT CERTIFIED (READ-ONLY HUMAN REVIEW REQUIRED)`**

---

## 1. RESUMEN EJECUTIVO Y ALCANCE AUTORIZADO

El presente informe consolida la ejecución técnica controlada de la fase **PEVN — B3-H11: Recursos Pedagógicos de Actividades + Storage Seguro**, desarrollada con base en los hallazgos y especificaciones de la auditoría técnica previa [B3_H10_SUBMISSIONS_RESOURCES_AUDIT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/B3_H10_SUBMISSIONS_RESOURCES_AUDIT.md).

### 1.1 Alcance Implementado (Estricto B3-H11)
1. **Infraestructura de Almacenamiento Seguro (Storage Subsystem):**
   - Módulo desacoplado en `backend/app/core/storage/` con abstracción de drivers (`IStorageDriver`, `LocalStorageDriver`, `StorageService`).
   - Mitigación integral contra Path Traversal, validación de extensión estricta (whitelist), validación de Magic Bytes en cabeceras binarias, límite de tamaño por archivo (20 MB), y soporte de rutas extendidas en Windows (`\\?\`).
2. **Entidad y Modelo de Recursos Pedagógicos (`ActivityResource`):**
   - Soporte para múltiples materiales de apoyo por actividad académica.
   - Tipos de recurso soportados: Archivos cargados (`FILE`) y Enlaces externos (`URL`).
   - Migración Alembic `022_activity_resources_and_storage.py` con integridad referencial (`ON DELETE CASCADE` hacia la actividad y `SET NULL` hacia el creador), índices por institución/actividad y timestamps duales funcionales en PostgreSQL y SQLite.
3. **Endpoints del Portal Docente (Teacher Portal):**
   - Listado de recursos: `GET /api/v1/teacher/activities/{activity_id}/resources`.
   - Creación de recurso URL: `POST /api/v1/teacher/activities/{activity_id}/resources/url`.
   - Carga de recurso Archivo: `POST /api/v1/teacher/activities/{activity_id}/resources/file` (Multipart/form-data).
   - Descarga autenticada de recurso: `GET /api/v1/teacher/activities/{activity_id}/resources/{resource_id}/download`.
   - Eliminación segura de recurso: `DELETE /api/v1/teacher/activities/{activity_id}/resources/{resource_id}` (eliminación lógica/física con limpieza de archivo).
4. **Endpoints del Portal Estudiante (Student Portal):**
   - Consulta de recursos de una actividad asignada a su grupo: `GET /api/v1/student/activities/{activity_id}/resources`.
   - Inclusión automática de recursos en el detalle general de la actividad: `GET /api/v1/student/activities/{activity_id}`.
   - Descarga autenticada de archivos adjuntos: `GET /api/v1/student/activities/{activity_id}/resources/{resource_id}/download`.
5. **Seguridad Transaccional, Anti-IDOR y Multi-Tenant:**
   - Verificación estricta de aislamiento institucional (`institution_id`).
   - Verificación de asignación docente (materia y grupo).
   - Verificación de matrícula activa del estudiante en el grupo de la actividad.
   - Delimitación transaccional explícita (`await db.commit()`) en todos los endpoints mutantes.
   - Registro de eventos de auditoría institucional (`RESOURCE_CREATED`, `RESOURCE_DELETED`, `RESOURCE_DOWNLOADED`).
6. **Interfaces de Usuario (Frontend):**
   - **Portal Docente (`TeacherActivitiesView.tsx`):** Botón contextual "📎 Materiales", Modal de Gestión de Recursos con listado de recursos, carga de archivos y adición de enlaces.
   - **Portal Estudiante (`StudentTaskDetailModal.tsx`):** Sección "Materiales y Recursos Pedagógicos" con descarga autenticada de archivos (`blob`), apertura de enlaces externos y retrocompatibilidad con el campo legado `resource_url`.

### 1.2 Alcance Excluido (Estrictamente reservado para B3-H12)
* **Entregas de Estudiantes (Student Submissions):** No se crearon tablas de entregas, ni formularios de respuesta de texto, ni interfaces de adjuntos por parte de los estudiantes. El portal de estudiantes en B3-H11 es estrictamente de consulta y descarga de materiales provistos por el docente.

---

## 2. ARQUITECTURA DEL SUBSISTEMA DE ALMACENAMIENTO SEGURO

El subsistema de almacenamiento fue diseñado bajo principios de Clean Architecture y Defense in Depth:

```
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Endpoint Controllers                │
│       (teacher_portal.py / student_portal.py / get_storage)      │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                        StorageService                            │
│  - Extension Whitelist (.pdf, .docx, .xlsx, .pptx, .zip, etc.)  │
│  - Magic Bytes MIME Verification (PDF, ZIP/Office, Images)       │
│  - Max File Size Enforcement (20 MB default)                     │
│  - Tenant-Partitioned Logical Path Construction                  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                 IStorageDriver / LocalStorageDriver              │
│  - Path Traversal Sanitization & Realpath Isolation             │
│  - Windows MAX_PATH Extended Path Syntax (\\?\)                  │
│  - Async Chunked I/O Streaming (save, read_chunks, delete)       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Filesystem Secure Root                        │
│   ./data/storage/{institution_id}/activities/{activity_id}/...   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.1 Componentes Implementados

1. **[backend/app/core/storage/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/interfaces.py):**
   - Define el protocolo abstracto `IStorageDriver` (`save_file`, `get_file_path`, `read_file_chunks`, `delete_file`, `file_exists`).
   - Define excepciones canónicas: `StorageError`, `StorageSecurityError`, `FileValidationError`.

2. **[backend/app/core/storage/local.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/local.py):**
   - Implementa `LocalStorageDriver` con validación rigurosa de frontera contra escapes de directorio (`..`, `/`, `\`).
   - Soporte nativo para rutas extendidas en entornos Windows:
     ```python
     if os.name == "nt" and not safe_path.startswith("\\\\?\\"):
         safe_path = "\\\\?\\" + safe_path
     ```
   - Operaciones de I/O asíncronas con streaming por chunks (`chunk_size=64KB`) para evitar bloqueos del event loop y consumo excesivo de memoria.

3. **[backend/app/core/storage/service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/storage/service.py):**
   - Capa de dominio que orquesta validaciones de negocio:
     * **Tamaño:** Límite configurable vía `settings.MAX_UPLOAD_SIZE_BYTES` (20 MB).
     * **Extensiones autorizadas:** `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`, `.csv`, `.zip`, `.rar`, `.7z`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.mp3`, `.mp4`.
     * **Firmas binarias (Magic Bytes):** Verificación de bytes mágicos (`%PDF-`, `PK\x03\x04` para Office/ZIP, `\xFF\xD8\xFF` para JPEG, `\x89PNG` para PNG, etc.).
     * **Generación de rutas seguras por Tenant:** `{institution_id}/activities/{activity_id}/resources/{uuid}{ext}`.

4. **[backend/app/core/config.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py):**
   - Variables de configuración añadidas:
     * `STORAGE_LOCAL_PATH: str = "./data/storage"`
     * `MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024` (20 MB)
     * `ALLOWED_FILE_EXTENSIONS: list[str] = [ ... ]`

---

## 3. MODELO DE DATOS Y MIGRACIÓN TRANSACCIONAL

### 3.1 Entidad `ActivityResource`
Ubicada en [backend/app/models/academic_activity.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/academic_activity.py):

| Columna | Tipo de Dato | Restricciones / Configuración | Propósito |
| :--- | :--- | :--- | :--- |
| `id` | `UUID(as_uuid=True)` | `primary_key=True`, `default=uuid4` | Identificador único global |
| `activity_id` | `UUID(as_uuid=True)` | `ForeignKey("academic_activities.id", ondelete="CASCADE")`, `nullable=False`, `index=True` | Vínculo a la actividad padre |
| `resource_type` | `Enum(ActivityResourceType)` | `nullable=False` (`URL` o `FILE`) | Discriminador del tipo de recurso |
| `title` | `String(255)` | `nullable=False` | Título pedagógico del recurso |
| `url` | `String(1024)` | `nullable=True` | URL externa cuando `resource_type == URL` |
| `file_path` | `String(1024)` | `nullable=True` | Ruta lógica interna cuando `resource_type == FILE` |
| `original_filename` | `String(255)` | `nullable=True` | Nombre de archivo presentado al descargar |
| `file_size_bytes` | `BigInteger` | `nullable=True` | Tamaño del archivo en bytes |
| `mime_type` | `String(128)` | `nullable=True` | Tipo MIME detectado y sanitizado |
| `institution_id` | `UUID(as_uuid=True)` | `ForeignKey("institutions.id", ondelete="CASCADE")`, `nullable=False`, `index=True` | Aislamiento Multi-Tenant |
| `created_by` | `UUID(as_uuid=True)` | `ForeignKey("users.id", ondelete="SET NULL")`, `nullable=True` | Trazabilidad del docente creador |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()`, `nullable=False` | Timestamp de creación |
| `updated_at` | `DateTime(timezone=True)` | `server_default=func.now()`, `onupdate=func.now()`, `nullable=False` | Timestamp de actualización |

### 3.2 Migración Alembic
Creada en [backend/migrations/versions/022_activity_resources_and_storage.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/versions/022_activity_resources_and_storage.py):
- Creación de tabla `activity_resources`.
- Creación de índices compuestos y unificados: `ix_activity_resources_activity_id`, `ix_activity_resources_institution_id`, `ix_activity_resources_inst_activity`.
- Funciones `upgrade()` y `downgrade()` reversibles con soporte para Postgres y SQLite.

---

## 4. ENDPOINTS API Y CONTROLADORES

### 4.1 Endpoints del Portal Docente (`teacher_portal.py`)

| Método | Endpoint | Permiso / Rol | Parámetros / Body | Respuesta | Descripción |
| :---: | :--- | :---: | :--- | :---: | :--- |
| `GET` | `/teacher/activities/{activity_id}/resources` | `TEACHER` | `activity_id: UUID` | `ActivityResourceListResponse` | Lista recursos asociados |
| `POST` | `/teacher/activities/{activity_id}/resources/url` | `TEACHER` | `CreateUrlResourceRequest` (`title`, `url`) | `ActivityResourceResponse` | Asocia enlace URL externo |
| `POST` | `/teacher/activities/{activity_id}/resources/file` | `TEACHER` | `title: str`, `file: UploadFile` | `ActivityResourceResponse` | Carga archivo seguro |
| `GET` | `/teacher/activities/{activity_id}/resources/{resource_id}/download` | `TEACHER` | `activity_id`, `resource_id` | `FileResponse` (Stream) | Descarga archivo autenticado |
| `DELETE` | `/teacher/activities/{activity_id}/resources/{resource_id}` | `TEACHER` | `activity_id`, `resource_id` | `HTTP 204 No Content` | Elimina recurso y archivo |

### 4.2 Endpoints del Portal Estudiante (`student_portal.py`)

| Método | Endpoint | Permiso / Rol | Parámetros | Respuesta | Descripción |
| :---: | :--- | :---: | :--- | :---: | :--- |
| `GET` | `/student/activities/{activity_id}` | `STUDENT` | `activity_id: UUID` | `StudentActivityDetailResponse` | Detalle con array `resources` |
| `GET` | `/student/activities/{activity_id}/resources` | `STUDENT` | `activity_id: UUID` | `StudentActivityResourceListResponse` | Lista recursos disponibles |
| `GET` | `/student/activities/{activity_id}/resources/{resource_id}/download` | `STUDENT` | `activity_id`, `resource_id` | `FileResponse` (Stream) | Descarga autenticada |

### 4.3 Auditoría de Seguridad y Eventos
Se incorporaron 3 nuevos tipos de eventos canónicos en [backend/app/audit/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py):
- `RESOURCE_CREATED = "resource_created"`
- `RESOURCE_DELETED = "resource_deleted"`
- `RESOURCE_DOWNLOADED = "resource_downloaded"`

---

## 5. INTERFACES DE USUARIO (FRONTEND)

### 5.1 Portal Docente — Gestión de Recursos (`TeacherActivitiesView.tsx`)
1. **Acción de Tabla:** Cada fila de actividad cuenta con el botón contextual **"📎 Materiales"**, mostrando el contador de recursos adjuntos cuando aplica.
2. **Modal de Recursos de la Actividad:**
   - Visualización de materiales pedagógicos existentes con título, tipo, tamaño y fecha.
   - Botón de descarga/apertura y botón de eliminación con confirmación.
   - **Pestaña 1 (Cargar Archivo):** Selector de archivo con validación de extensiones permitidas, límite visual de 20 MB y campo de título pedagógico.
   - **Pestaña 2 (Enlace URL):** Formulario para ingresar título y URL externa validada.

### 5.2 Portal Estudiante — Consulta y Descarga (`StudentTaskDetailModal.tsx`)
1. **Sección de Materiales Pedagógicos:**
   - Lista interactiva de recursos adjuntos por el docente.
   - Badges visuales identificando el tipo (`PDF`, `DOCX`, `ZIP`, `URL`, etc.) y tamaño formateado.
   - Botón de **"Descargar"** para archivos con petición autenticada (`blob`) que preserva el nombre original del archivo.
   - Botón de **"Abrir Enlace"** para URLs externas seguras.
2. **Compatibilidad Retrospectiva:**
   - Si la actividad cuenta con el campo tradicional `resource_url`, este se presenta armónicamente como "Enlace de Material de Apoyo (Principal)".

---

## 6. RESULTADOS DE VERIFICACIÓN TÉCNICA AUTOMATIZADA

### 6.1 Suite Focalizada B3-H11 (`tests/test_activity_resources_and_storage.py`)
Ejecución completada con **100% de éxito (5/5 PASSED)**:

```text
tests/test_activity_resources_and_storage.py::test_local_storage_driver_crud_and_security PASSED [ 20%]
tests/test_activity_resources_and_storage.py::test_storage_service_validation_rules PASSED       [ 40%]
tests/test_activity_resources_and_storage.py::test_teacher_create_url_resource_and_student_view PASSED [ 60%]
tests/test_activity_resources_and_storage.py::test_teacher_file_upload_download_and_student_download PASSED [ 80%]
tests/test_activity_resources_and_storage.py::test_anti_idor_and_tenant_isolation PASSED       [100%]

============================== 5 passed in 11.81s ==============================
```

### 6.2 Verificaciones Frontend
- `npm run typecheck` (`tsc --noEmit`): **0 errores (Code 0)**.
- `npm run lint` (`eslint . --max-warnings 0`): **0 warnings / 0 errores (Code 0)**.
- `npm run build` (`vite build`): **Build de producción exitoso**.

---

## 7. GUÍA DE VALIDACIÓN MANUAL READ-ONLY PARA EL PROPIETARIO

Para realizar la validación humana en el navegador:

### Paso 1: Acceso Docente
1. Iniciar sesión como docente (`docente@pevn.edu.co` / contraseña configurada).
2. Ir a **Portal Docente → Actividades Académicas**.
3. Seleccionar una actividad existente o crear una nueva.
4. En la tabla de actividades, hacer clic en el botón **"📎 Materiales"**.

### Paso 2: Cargar Recursos Pedagógicos
1. En el modal que se abre:
   - **Cargar un Archivo:** Subir un PDF o documento de prueba (ej. `Guia_Laboratorio.pdf`), asignar título y guardar.
   - **Agregar un Enlace:** Ingresar título (ej. `Video Tutorial Khan Academy`) y URL externa, guardar.
2. Comprobar que ambos recursos aparecen inmediatamente listados en el modal.
3. Probar la descarga del archivo subido haciendo clic en el icono de descarga.

### Paso 3: Validación desde el Portal Estudiante
1. Cerrar sesión de docente e iniciar sesión con un estudiante asignado al mismo grupo (`estudiante@pevn.edu.co`).
2. Ir a **Portal Estudiante → Tareas / Actividades**.
3. Abrir la actividad que tiene los recursos adjuntos.
4. En el modal de detalle de la tarea, observar la sección **"Materiales y Recursos Pedagógicos"**.
5. Hacer clic en **"Descargar"** en el archivo PDF: el navegador debe descargar el archivo real con su nombre original.
6. Hacer clic en **"Abrir Enlace"** en la URL: debe abrir la página en una pestaña nueva.
7. Verificar que **NO** aparece ningún formulario de entrega de tarea (respetando el alcance estricto de B3-H11 y reservando B3-H12 para dicha fase).

---

## 8. CONCLUSIÓN Y ESTADO DEL GATE

La fase técnica **B3-H11** ha sido completada en su totalidad con rigor de seguridad, aislamiento multi-tenant, persistencia verificada y cero regresiones sobre módulos previamente certificados.

* **`B3-H11 TECHNICAL VERIFICATION = PASS`**
* **`B3-H11 HUMAN VALIDATION = PENDING`**
* **`B3-H11 CERTIFICATION = NOT CERTIFIED (READ-ONLY HUMAN REVIEW REQUIRED)`**
