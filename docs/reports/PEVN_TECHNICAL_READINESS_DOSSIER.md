# PEVN — DOSSIER DE PREPARACIÓN TÉCNICA Y ARQUITECTURA DEL SISTEMA
## INVENTARIO DE ARQUITECTURA ACTUAL, COMPONENTES Y BRECHAS INFRAESTRUCTURALES (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Documento:** Dossier de Arquitectura Técnica y Preparación Tecnológica  
**Metodología:** AI Software Factory v1.2 — Technical Readiness Assessment  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Audit Evidence  

---

## 1. Topología Arquitectónica General

La **Plataforma Educativa Virtual Nacional (PEVN)** adopta un patrón arquitectónico de **Micro-Monolito Modular Asíncrono** en backend desacoplado de una **Single Page Application (SPA)** reactiva en frontend, complementado con bases de datos relacionales ACID y cachés en memoria:

```
[ NAVEGADOR WEB / PWA ] 
        │
        ▼ (HTTPS / TLS 1.3 en Producción)
[ REVERSE PROXY / INGRESS / NGINX / WAF ]
        │
        ├──► /assets/* ──► [ Frontend SPA: React 18 / TypeScript / Vite ]
        │
        └──► /api/v1/* ──► [ Backend REST: FastAPI 0.110+ / Python 3.12 ]
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            [ PostgreSQL 16 ]  [ Redis 7 ]  [ IMeetingProvider ]
            (Datos ACID/JSONB) (Sesiones/    (BigBlueButton /
                                Caché/Queue)   Mock Adapter)
                    │
                    ▼
            [ Local / S3 File Storage ]
            (Evidencias / Tareas / Adjuntos)
```

---

## 2. Inventario Técnico Componente por Componente

A continuación se detalla cada componente arquitectónico, identificando con precisión forense su estado actual:
`CURRENT` | `PLANNED` | `MISSING` | `EXTERNAL DEPENDENCY`.

---

### 2.1 Arquitectura Frontend
- **Tecnologías Centrales:** React 18.3.1, TypeScript 5.7.3, Vite 6.0.5, Tailwind CSS 3.4.17, React Router DOM 6.28.0, Axios 1.7.9.
- **Patrón de Estado:** Estado en memoria puro mediante React Context (`AuthContext`). Los tokens JWT de acceso residen únicamente en memoria volátil de la aplicación.
- **Soporte PWA:** Integración de Service Worker mediante `vite-plugin-pwa` para caché de recursos estáticos e instalación en dispositivos móviles o de escritorio.
- **Cliente HTTP:** Cliente Axios tipado con interceptores para:
  - Inyección automática del Bearer Access Token desde memoria.
  - Intercepción de errores 401 para reintento transparente mediante cola *single-flight refresh* llamando a `/api/v1/auth/refresh`.
  - Captura centralizada de correlación (`X-Correlation-ID`).
- **Estado Técnico:** `CURRENT`.
- **Brecha Detectada:** Los mocks de algunas pruebas heredadas de frontend (`RoleNavigationFunctional.test.tsx`, `StudentPortal.test.tsx`) presentan desalineación cosmética con las nuevas firmas introducidas en B3-H13 (`getSubmissionDetail`), requiriendo actualización de fixtures en la siguiente fase de mantenimiento.

---

### 2.2 Arquitectura Backend
- **Tecnologías Centrales:** Python 3.12, FastAPI 0.110+, Uvicorn ASGI server, SQLAlchemy 2.0 (AsyncIO con `asyncpg`), Pydantic v2 Settings.
- **Estructura de Capas:**
  - Capa de Enrutamiento y Controladores REST (`backend/app/api/v1/endpoints/`).
  - Capa de Inyección de Dependencias y Seguridad (`backend/app/api/deps.py`).
  - Capa de Servicios de Dominio Misional (`backend/app/services/`).
  - Capa de Modelado de Datos ORM (`backend/app/models/`).
  - Capa de Persistencia y Conexión (`backend/app/db/session.py`).
  - Capa de Auditoría y Eventos Inmutables (`backend/app/audit/`).
- **Patrón Transaccional:** Delimitación transaccional explícita a nivel de endpoint controlador mediante `await db.commit()`, previniendo rollbacks implícitos tras peticiones exitosas (remediado y verificado formalmente en B3-H01).
- **Estado Técnico:** `CURRENT`.

---

### 2.3 Arquitectura de API RESTful
- **Especificación:** RESTful JSON bajo estándar OpenAPI v3.
- **Prefijo y Versionamiento:** Todos los servicios de negocio se exponen bajo `/api/v1/`.
- **Documentación Viva:** Swagger UI (`/docs`) y Redoc (`/redoc`) generados automáticamente; condicionados por configuración para apagarse en entornos de producción (`OPENAPI_URL=None`).
- **Manejo de Errores:** Controladores de excepciones globales (`backend/app/exceptions/handlers.py`) que capturan excepciones de dominio (`AppException`), errores de validación Pydantic (`RequestValidationError`) y fallos no controlados (`Exception`), transformándolos en respuestas JSON canónicas sanitizadas sin revelar jamás trazas de pila (*stack traces*) al cliente:
  ```json
  {
    "error_code": "RESOURCE_NOT_FOUND",
    "message": "El recurso solicitado no existe o no tiene acceso en este ámbito.",
    "correlation_id": "c6b2552e-a133-4d2b-8af9-432c977691d9"
  }
  ```
- **Estado Técnico:** `CURRENT`.

---

### 2.4 Arquitectura de Base de Datos
- **Motor de Persistencia:** PostgreSQL 16.4.
- **Driver de Conexión:** `asyncpg` (driver asíncrono nativo en C/Cython de ultra alto rendimiento).
- **Gestión de Esquemas y Migraciones:** Alembic con 23 migraciones versionadas y lineales en `backend/migrations/versions/`.
- **Pool de Conexiones:**
  - `pool_size = 10`
  - `max_overflow = 20`
  - `pool_recycle = 1800` (30 minutos)
  - `pool_pre_ping = True` (detección y purga activa de conexiones caídas o muertas).
- **Modelo de Seguridad de Usuarios de Base de Datos:**
  - `pevn_admin`: Propietario del esquema, utilizado exclusivamente por Alembic y tareas de setup.
  - `pevn_app`: Usuario de mínimos privilegios (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) con permiso `CREATE SCHEMA/TABLE` revocado expresamente.
- **Estado Técnico:** `CURRENT`.
- **Requerimiento para Producción:** `EXTERNAL DEPENDENCY` — Incorporación de PgBouncer para agrupar conexiones ante cargas masivas concurrentes a nivel nacional.

---

### 2.5 Arquitectura de Autenticación
- **Algoritmo de Contraseñas:** Argon2id (RFC 9106), memoria 64 MB, 3 iteraciones, 4 hilos, salting aleatorio de 16 bytes.
- **Token de Acceso (Access Token):** JWT efímero firmado con HMAC-SHA256 (`HS256`), duración 15 minutos, almacenado en memoria volátil de JavaScript (cero uso de `localStorage`/`sessionStorage`).
- **Token de Refresco (Refresh Token):** Almacenado como hash SHA-256 en la tabla `refresh_tokens`, entregado al cliente exclusivamente mediante cookie HttpOnly con directivas estrictas:
  - `HttpOnly = True`
  - `SameSite = Strict`
  - `Path = /api/v1/auth`
  - `Secure = True` (forzado en producción)
  - Duración: 7 días.
- **Mecanismo de Detección de Brechas / Replay:** Cada refresco invalida el token anterior mediante puntero `replaced_by_token_id`. Si se detecta un intento de reutilización de un token anterior, toda la familia de tokens (`family_id`) queda revocada inmediatamente y la sesión se bloquea.
- **Protección de Fuerza Bruta:** Bloqueo automático de cuenta por 15 minutos tras 5 fallos consecutivos (`user.account.locked`).
- **Estado Técnico:** `CURRENT`.

---

### 2.6 Arquitectura de Autorización y Aislamiento Multi-Inquilino
- **Modelo RBAC Granular:** Control de acceso basado en `recurso:accion` con evaluación de comodines (`*`, `users:*`, `*:read`).
- **Jerarquía Numérica:** Niveles de rol del 10 al 100 que previenen escalamiento vertical de privilegios.
- **Aislamiento Multi-Inquilino (Multi-Tenancy):**
  - Todas las entidades del dominio escolar se encuentran asociadas al `institution_id` de la institución educativa.
  - Las consultas del ORM inyectan el filtro de institución del usuario autenticado de forma mandatoria.
  - La jerarquía territorial DANE (Nación $\rightarrow$ Departamento $\rightarrow$ Municipio $\rightarrow$ Institución $\rightarrow$ Sede) se valida mediante la regla de contención `scope_contains()`.
- **Mitigación Anti-IDOR (Blind 404):** Intentos de manipulación de identificadores UUID en URLs devuelven `404 Not Found` en lugar de revelar la existencia del registro con un 403.
- **Estado Técnico:** `CURRENT`.

---

### 2.7 Arquitectura de Almacenamiento de Archivos (Storage)
- **Implementación Actual:** `LocalStorageService` en sistema de archivos local (`backend/data/storage/`).
- **Estructura Particionada:**
  `{institution_id}/submissions/{activity_id}/{student_id}/{submission_id}/{attachment_id}.ext`
- **Controles de Seguridad en Carga de Archivos:**
  - Validación de extensiones permitidas (`.pdf`, `.docx`, `.xlsx`, `.zip`, `.jpg`, `.png`).
  - Límite de tamaño estricto de 10 MB por archivo (máximo 3 archivos por entrega).
  - Detección binaria de cabeceras ejecutables (Magic Bytes) para impedir la carga de `.exe`, `.elf`, `.bat` o `.sh` camuflados.
  - Mitigación de Path Traversal mediante resolución canónica y validación de frontera de directorio base.
- **Estado Técnico:** `CURRENT` (en modo local).
- **Brecha / Requisito de Producción:** `PLANNED` / `EXTERNAL DEPENDENCY` — Implementación del adaptador `S3StorageService` (AWS S3 / MinIO) para almacenamiento de objetos distribuido con URLs presignadas temporales.

---

### 2.8 Arquitectura de Auditoría Persistente
- **Tabla Inmutable:** `audit_logs` en PostgreSQL con particionamiento y optimización de índices por tipo de evento, actor, institución, correlación y fecha.
- **Sanitización de Datos Sensibles (Zero Secrets/PII):** Función recursiva `sanitize_audit_metadata()` que censura automáticamente valores bajo llaves como `password`, `token`, `secret`, `jwt_secret`, `key` y enmascara parcialmente números de documentos de identidad.
- **Estado Técnico:** `CURRENT`.

---

### 2.9 Arquitectura de Notificaciones y Comunicaciones
- **Circulares y Avisos:** Persistencia estructurada en PostgreSQL (`institutional_communications`, `communication_audiences`, `communication_receipts`).
- **Acuse de Recibo:** Firma electrónica con estampa UTC y dirección IP registrada.
- **Estado Técnico:** `CURRENT` (vía base de datos).
- **Brecha / Requisito de Producción:** `MISSING` — Falta servicio de notificaciones en tiempo real vía WebSockets o Push Notifications (WebPush / FCM) y pasarela SMTP institucional para correos transaccionales.

---

### 2.10 Arquitectura de Aulas Virtuales y Clases Sincrónicas
- **Abstracción:** Protocolo `IMeetingProvider` que desacopla la lógica de negocio de cualquier motor de videoconferencia.
- **Adaptadores Implementados:**
  - `BBBAdapter`: Implementación oficial del protocolo BigBlueButton API (cálculo de checksums SHA-1 y SHA-256, builder determinístico de parámetros URL y parser XML de respuestas).
  - `MockMeetingProvider`: Simulador en memoria para desarrollo y pruebas determinísticas.
  - `MeetingProviderFactory`: Resuelve dinámicamente el proveedor activo según la variable de entorno `MEETING_PROVIDER_TYPE`.
- **Telemetría y Control de Asistencia:** Endpoints `/launch`, `/join`, `/leave` y `/end` con cálculo automático de duración en segundos.
- **Control de Grabaciones:** Sincronización asíncrona, visibilidad controlada por el docente y reproductor integrado.
- **Estado Técnico del Software:** `CURRENT` (Software 100% terminado y testeado).
- **Estado de Infraestructura:** `INFRASTRUCTURE REQUIRED` / `EXTERNAL DEPENDENCY` — **El servidor físico BigBlueButton y el servidor de relay Coturn (STUN/TURN en TCP 443) NO están comisionados ni conectados.** El sistema opera actualmente en modo `"mock"`.

---

### 2.11 Integraciones Externas y Catálogos
- **Catálogo DANE / DUE:** Caché relacional local con soporte de búsqueda fonética y geográfica.
- **Armonización SIMAT:** Estructura de matrícula modelada bajo las especificaciones de datos del Sistema de Matrículas del MEN.
- **Estado Técnico:** `CURRENT` (mediante caché e ingesta local).
- **Requerimiento de Producción:** `PLANNED` / `EXTERNAL DEPENDENCY` — Enlace mediante Web Services oficiales o APIs del Ministerio de Educación Nacional (sujeto a convenios interinstitucionales).

---

### 2.12 Configuración y Gestión de Entornos
- **Mecanismo:** Pydantic Settings v2 (`backend/app/core/config.py`) cargado desde variables de entorno y archivos `.env`.
- **Validación al Inicio:** La aplicación valida en el arranque la robustez de las configuraciones; rechaza el inicio en modo producción si se detectan contraseñas por defecto, secretos vacíos o comodines `*` en CORS.
- **Estado Técnico:** `CURRENT`.

---

### 2.13 Despliegue e Infraestructura de Contenedores
- **Desarrollo:** `docker-compose.yml` local con servicios para backend FastAPI, frontend Vite, PostgreSQL 16 y Redis 7.
- **Seguridad en Contenedores:** Dockerfile multi-etapa con ejecución bajo usuario no root (`UID 1001:pevn`).
- **Estado Técnico:** `CURRENT` (para entorno de desarrollo).
- **Requerimiento de Producción:** `INFRASTRUCTURE REQUIRED` — Manifiestos de orquestación (Kubernetes / Helm charts o Docker Swarm), balanceadores de carga Nginx/Traefik con terminación TLS y clústeres de base de datos administrados.

---

### 2.14 Arquitectura de Respaldos (Backups) y Continuidad
- **Desarrollo:** Script de inicialización y dumps manuales mediante `pg_dump`.
- **Estado Técnico:** `PARTIAL`.
- **Requerimiento de Producción:** `INFRASTRUCTURE REQUIRED` — Implementación de política de respaldos automatizados WAL-G o pgBackRest con replicación a almacenamiento secundario inmutable (RPO < 15 min, RTO < 2 horas).

---

### 2.15 Observabilidad, Registro y Trazabilidad (Logging & Metrics)
- **Logging Estructurado:** `structlog` en formato JSON estructurado para facilitar la ingesta por agentes de monitoreo (Logstash, Loki o CloudWatch).
- **Correlación de Peticiones:** Middleware `CorrelationIdMiddleware` que inyecta un identificador único UUID (`X-Correlation-ID`) en cada petición HTTP, propagándolo a través de logs, errores y respuestas al cliente.
- **Sondas de Salud:**
  - `GET /api/v1/health`: Sonda de liveness rápida.
  - `GET /api/v1/ready`: Sonda de readiness que valida conectividad física contra PostgreSQL y Redis.
- **Estado Técnico:** `CURRENT`.
- **Requerimiento de Producción:** `EXTERNAL DEPENDENCY` — Despliegue del stack de monitoreo Prometheus + Grafana y agente de recolección de logs.

---

## 3. Matriz de Síntesis Arquitectónica

| Componente | Estado de Software | Dependencia de Infraestructura | Brecha Crítica |
| :--- | :---: | :---: | :--- |
| **Frontend SPA (React 18 / Vite)** | `CURRENT` | Servidor Web / CDN | 4 tests con mock drift en vitest |
| **Backend API (FastAPI / Python 3.12)** | `CURRENT` | Servidor de Aplicaciones | Ninguna |
| **Base de Datos (PostgreSQL 16)** | `CURRENT` | Clúster BD Administrado | Requiere PgBouncer en alta carga |
| **Caché / Sesión (Redis 7)** | `CURRENT` | Clúster Redis | Ninguna |
| **Autenticación (Argon2id + JWT)** | `CURRENT` | Ninguna | Ninguna |
| **Autorización (RBAC + Scope DANE)** | `CURRENT` | Ninguna | Ninguna |
| **Almacenamiento de Archivos** | `CURRENT` (Local) | Storage S3 / MinIO | Falta adaptador S3 para producción |
| **Auditoría Inmutable** | `CURRENT` | PostgreSQL | Ninguna |
| **Aulas Virtuales (Software)** | `CURRENT` | Servidor BigBlueButton | **Servidor BBB físico NO comisionado** |
| **Relay WebRTC (Coturn)** | `CURRENT` (Config) | Servidor Coturn en TCP 443 | **Servidor Coturn NO desplegado** |
| **Generación Masiva de PDFs** | `MISSING` | Worker / WeasyPrint | Renderizado de boletines en PDF |
| **Notificaciones en Tiempo Real** | `MISSING` | WebSockets / Push / SMTP | Notificaciones push y correos |
| **Monitoreo & Métricas** | `PARTIAL` | Prometheus / Grafana | Dashboard centralizado de métricas |
