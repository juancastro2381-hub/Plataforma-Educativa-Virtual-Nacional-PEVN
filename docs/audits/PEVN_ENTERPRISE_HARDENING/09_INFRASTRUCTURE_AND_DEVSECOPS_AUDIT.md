# 09 — AUDITORÍA INTEGRAL DE INFRAESTRUCTURA, CONTENEDORES Y DEVSECOPS
## Plataforma Educativa Virtual Nacional (PEVN) — Programa Maestro de Endurecimiento Empresarial

- **Agente Auditor:** AGENT 10 — DEVSECOPS, INFRASTRUCTURE AND DISASTER RECOVERY
- **Fecha de Auditoría:** 2026-11-01
- **Alcance:** Configuración de entornos (`development`, `staging`, `production`), gestión de secretos, seguridad de contenedores (`Dockerfile`, `docker-compose.yml`), pipeline CI/CD (`.github/workflows/ci.yml`), bloqueo de dependencias, observabilidad, correlación de logs, sondas `/health` y `/ready`, y telemetría operativa (`operations.py`, `system_operations_service.py`).
- **Metodología:** Inspección estática exhaustiva de código e infraestructura como código (IaC), verificación de higiene de repositorio Git en modo de solo lectura y contraste contra estándares OWASP Docker Security, CIS Docker Benchmark, NIST SP 800-190 y lineamientos de seguridad del Estado colombiano (Ley 1581 de 2012 / MSPI).

---

## 1. Resumen Ejecutivo

La arquitectura base de infraestructura y DevSecOps de **PEVN** muestra una intención de diseño sólida (principios de *Security by Design*, contenedores que crean un usuario sin privilegios `pevn` con UID `1001`, separación nominal entre el usuario administrativo de base de datos `pevn_admin` y el usuario de aplicación `pevn_app`, sanitización estructurada con `structlog` y defensas de aislamiento en `db_safety.py`).

Sin embargo, la auditoría forense de los artefactos reales de despliegue, contenedores, CI/CD y monitoreo operativo reveló **brechas críticas y altas entre el diseño documentado y la implementación ejecutable**, las cuales impiden certificar la plataforma para un despliegue productivo sin aplicar las remediaciones descritas en este informe.

### Resumen Cuantitativo de Hallazgos (`OPS-001` a `OPS-018`)

| Severidad | Cantidad | Identificadores de Hallazgos |
| :--- | :---: | :--- |
| **CRITICAL** | **3** | `OPS-001`, `OPS-006`, `OPS-016` |
| **HIGH** | **7** | `OPS-002`, `OPS-004`, `OPS-007`, `OPS-009`, `OPS-011`, `OPS-012`, `OPS-015`, `OPS-017` *(8 en total considerando `OPS-017` en DR)* |
| **MEDIUM** | **7** | `OPS-003`, `OPS-005`, `OPS-008`, `OPS-010`, `OPS-013`, `OPS-014`, `OPS-018` |
| **LOW** | **0** | — |
| **INFORMATIONAL** | **0** | — |
| **TOTAL** | **18** | `OPS-001` a `OPS-018` (`OPS-001` a `OPS-015` detallados en este informe; `OPS-015` a `OPS-018` detallados en `13_BACKUP_AND_DISASTER_RECOVERY_PLAN.md`) |

---

## 2. Matriz de Clasificación de Estado de Controles DevSecOps e Infraestructura

Siguiendo las reglas estrictas de gobernanza de auditoría, ningún control se clasifica como *Verificado* únicamente por la existencia de su código o documentación:

| Dominio / Control Técnico | Artefacto Principal | Clasificación de Estado | Justificación Técnica y Evidencia |
| :--- | :--- | :---: | :--- |
| **Separación de Entornos (`ENVIRONMENT`, `DEBUG`)** | `backend/app/core/config.py` | **Parcialmente implementado** | En `production` rechaza `DEBUG=True`, comodines CORS y desactiva `/docs`. Pero genera `SECRET_KEY` aleatoria efímera si se omite (`OPS-001`) y no aplica restricciones equivalentes en `staging` ni valida `ALLOWED_HOSTS` o `DATABASE_URL` (`OPS-002`). |
| **Validador Pre-Vuelo de Entorno (`check_env.sh`)** | `infrastructure/scripts/check_env.sh` | **Implementado / No probado en CI** | Valida presencia de variables y `DEBUG`/`CORS_ORIGINS`, pero exige solo 64 caracteres para `SECRET_KEY` (contra 128 en `.env.example`) y no carga `.env` automáticamente (`OPS-003`). |
| **Aislamiento Fail-Closed de BD de Pruebas** | `backend/app/core/db_safety.py` | **Implementado / Parcialmente probado** | Excelente diseño fail-closed que exige `pevn_test_db` y bloquea `pevn_db`. Sin embargo, el pipeline CI/CD en `.github/workflows/ci.yml` configura `pevn_test` en lugar de `pevn_test_db` y no define `TEST_DATABASE_URL` (`OPS-009`). |
| **Higiene de Secretos en Plantillas y Bundles Frontend** | `.env.example`, `frontend/.env.example`, `frontend/src/config/index.ts` | **Verificado** | No existen secretos de producción en `.env.example` ni en las variables `VITE_*` empaquetadas en el cliente React. `sourcemap: false` está activo en `vite.config.ts`. |
| **Escaneo Automatizado de Secretos (Gitleaks)** | `.gitleaks.toml`, `.github/workflows/ci.yml` | **Parcialmente implementado** | `.gitleaks.toml` existe pero restringe sus reglas personalizadas a `backend/app/.*`, excluye `docs/.*` y **no se ejecuta en `.github/workflows/ci.yml`** (`OPS-004`). |
| **Higiene de Control de Versiones (`.gitignore` / `.dockerignore`)** | `.gitignore`, `backend/pevn.db`, `frontend/tsconfig.tsbuildinfo` | **Parcialmente implementado** | `backend/pevn.db` y `frontend/tsconfig.tsbuildinfo` están versionados en Git; `.gitignore` no excluye `*.db`, `*.sqlite*`, `*.sql`, `*.dump`; no existen archivos `.dockerignore` (`OPS-005`). |
| **Contenedor Backend Multi-Stage y Usuario No-Root** | `backend/Dockerfile` | **Implementado** | Construcción en 2 etapas (`builder` y `final`) sobre `python:3.12.8-slim` con usuario `pevn` (UID `1001`, `/usr/sbin/nologin`). Sin embargo, el `CMD` usa `uvicorn` de un solo proceso en vez de `gunicorn` (`OPS-007`). |
| **Contenedor Frontend para Producción** | `frontend/Dockerfile` | **Parcialmente implementado (Solo Desarrollo)** | Solo implementa la etapa `development` con `npm run dev` sobre `node:20.18-alpine`. Carece de etapa `builder` (`npm run build`) y servidor estático de producción como Nginx sin privilegios (`OPS-006`). |
| **Orquestación Local y Red de Contenedores** | `docker-compose.yml` | **Implementado (Solo Desarrollo)** | Incluye healthchecks y red bridge `pevn-network`. No persiste el volumen `/app/data/storage`, expone Redis sin contraseña y carece de perfil de producción (`OPS-007`, `OPS-008`). |
| **Pipeline CI/CD (Calidad, Tests, Auditoría)** | `.github/workflows/ci.yml` | **Implementado / Con brechas** | Ejecuta `black`, `isort`, `ruff`, `mypy`, `pytest`, `pip-audit`, `tsc`, `eslint`, `prettier`, `vitest`, `npm audit` y `docker buildx`. Carece de `gitleaks`, `alembic upgrade head`, escaneo Trivy y lockfile con hashes en Python (`OPS-009`, `OPS-010`). |
| **Logs Estructurados y `Correlation-ID`** | `backend/app/core/logging.py`, `middleware/correlation.py`, `logging_middleware.py` | **Parcialmente implementado** | Genera y propaga `X-Correlation-ID` con validación regex. Presenta brecha de orden de ejecución con `RateLimitMiddleware`, spoofing de `X-Forwarded-For` en `RequestLoggingMiddleware` y sanitización no recursiva (`OPS-013`). |
| **Sondas de Liveness (`/health`) y Readiness (`/ready`)** | `backend/app/api/v1/endpoints/health.py`, `ready.py`, `db/health.py` | **Implementado** | `/api/v1/health` y `/api/v1/ready` operan sin filtrar credenciales. Sin embargo, `/ready` abre y cierra una conexión TCP nueva a Redis en cada invocación sin connection pool (`OPS-014`). |
| **Portal y Telemetría de Operaciones Técnicas (`SUPER_ADMIN`)** | `backend/app/api/v1/endpoints/operations.py`, `services/system_operations_service.py` | **Parcialmente implementado** | Protegido para Nivel 100 (`SUPER_ADMIN`), pero ejecuta DDL en caliente (`TechnicalIncident.__table__.create`), carece de migración Alembic (`OPS-011`), hardcodea `actor_ip="127.0.0.1"`, omite el filtro de 24h y simula integraciones (`OPS-012`). |
| **Separación de Privilegios PostgreSQL (`pevn_app` vs `pevn_admin`)** | `infrastructure/docker/postgres/01-init-app-user.sh`, `migrations/env.py` | **Parcialmente implementado** | Revoca `CREATE ON SCHEMA public` a `pevn_app`, pero `migrations/env.py` usa `DATABASE_URL` (`pevn_app`), rompiendo `alembic upgrade head` dentro del contenedor, y otorga `UPDATE, DELETE` a `pevn_app` sobre `audit_logs` (`OPS-015`). |
| **Automatización de Backups y Recuperación ante Desastres (DR)** | `docs/OPERATIONS.md`, `infrastructure/scripts/` | **No implementado (Solo comando manual dev)** | No existen scripts automatizados de respaldo, retención, cifrado ni sincronización de `./data/storage` (`OPS-016`, `OPS-017`, `OPS-018`). Ver informe `13_BACKUP_AND_DISASTER_RECOVERY_PLAN.md`. |
| **Despliegue en Nube / WAF / Balanceador TLS / Vault / BBB Live** | `docs/DEPLOYMENT.md`, `docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md` | **Pendiente de dependencia externa** | La infraestructura perimetral (WAF, TLS, HashiCorp Vault, clúster BigBlueButton + Coturn y réplicas PostgreSQL) está documentada como arquitectura objetivo pero depende de aprovisionamiento en entorno gubernamental. |

---

## 3. Análisis Detallado por Dominio

### 3.1 Separación de Entornos (`development`, `staging`, `production`)

En [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L31-L376), la clase `Settings` define el enumerador `Environment` (`development`, `staging`, `production`) y aplica reglas en `validate_production_settings` (líneas 240–273) y `model_post_init` (líneas 371–377):

1. **Controles Implementados Correctamente:**
   - Cuando `ENVIRONMENT == Environment.PRODUCTION`:
     - Rechaza el arranque si `DEBUG == True` (`ValueError`).
     - Rechaza comodines (`"*"`) o cadenas vacías en `CORS_ORIGINS`.
     - Desactiva automáticamente `OPENAPI_URL`, `DOCS_URL` y `REDOC_URL` (`None`).
     - Bloquea `AUTH_PASSWORD_RESET_DEV_LINK = True` y fuerza `DB_ECHO = False`.
   - En `build_invitation_url` (líneas 323–333), exige esquema `https` tanto en `production` como en `staging` y prohíbe `localhost` en `production`.

2. **Deficiencias Detectadas (`OPS-001`, `OPS-002`, `OPS-003`):**
   - **Autogeneración silenciosa de `SECRET_KEY` en producción (`OPS-001`):** El validador `ensure_secret_key` (líneas 232–238) intercepta `SECRET_KEY: str = ""` antes de `validate_production_settings` y ejecuta `secrets.token_hex(64)` si está vacía, sin verificar si `ENVIRONMENT` es `production` o `staging`. Tampoco valida longitud mínima (128 caracteres hex) ni rechaza el valor de plantilla `REPLACE_ME_WITH_A_MINIMUM_128_CHARACTER_RANDOM_HEX_STRING`.
   - **Debilidad en `staging` y defaults inseguros en `production` (`OPS-002`):** En `ENVIRONMENT=staging`, no se prohíbe `DEBUG=True` ni `CORS_ORIGINS=["*"]`. En `ENVIRONMENT=production`, no se valida que `DATABASE_URL` haya sido cambiada respecto al default local (`postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db`), ni que `ALLOWED_HOSTS` no contenga `"*"` o exclusivamente `localhost`.
   - **Divergencia en `check_env.sh` (`OPS-003`):** [`infrastructure/scripts/check_env.sh`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/infrastructure/scripts/check_env.sh#L67) verifica `[ ${#SECRET_KEY} -lt 64 ]` en vez de `128`, y no carga el archivo `.env` antes de evaluar `${!var_name}`.

---

### 3.2 Gestión de Secretos e Higiene del Repositorio

1. **Inspección de Plantillas y Bundles de Frontend (Verificado):**
   - [`.env.example`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.env.example#L1-L89) y [`frontend/.env.example`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/.env.example#L1-L23) contienen únicamente valores placeholder (`REPLACE_ME_*`).
   - [`frontend/src/config/index.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/config/index.ts#L12-L42) solo expone variables públicas de entorno (`VITE_API_BASE_URL`, `VITE_APP_VERSION`, `VITE_APP_NAME`, `VITE_APP_ENV`, `VITE_API_TIMEOUT_MS`).
   - [`frontend/vite.config.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/vite.config.ts#L119) deshabilita los mapas de código fuente en producción (`sourcemap: false`).

2. **Brechas en Escaneo de Secretos y Control de Versiones (`OPS-004`, `OPS-005`):**
   - [`.gitleaks.toml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitleaks.toml#L25-L37) limita el alcance (`path = '''backend/app/.*'''`) de sus reglas personalizadas y excluye por completo `docs/.*`. Más grave aún, **no se ejecuta Gitleaks en `.github/workflows/ci.yml`**.
   - La inspección de archivos rastreados por Git (`git ls-files`) confirmó que **`backend/pevn.db`** y **`frontend/tsconfig.tsbuildinfo`** están comprometidos en el repositorio. Además, [`.gitignore`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitignore#L1-L187) no bloquea `*.db`, `*.sqlite*`, `*.sql`, `*.dump` ni `backup_*`.

---

### 3.3 Auditoría de Seguridad de Contenedores y Orquestación Docker

| Aspecto Evaluado | `backend/Dockerfile` | `frontend/Dockerfile` | `docker-compose.yml` |
| :--- | :--- | :--- | :--- |
| **Imagen Base** | `python:3.12.8-slim` (Fijada a versión parche) | `node:20.18-alpine` (Fijada a versión menor) | `postgres:16.4-alpine`, `redis:7.4-alpine` |
| **Multi-Stage Build** | **Sí** (`builder` → `final`) | **No** (`AS development` únicamente) (`OPS-006`) | `target: final` en `backend`; sin target en `frontend` |
| **Usuario No-Root** | **Sí** (`pevn`, UID/GID `1001`, `nologin`) | **Sí** (`pevn`, UID/GID `1001`) | Imágenes `db` y `redis` usan sus usuarios estándar |
| **Archivo `.dockerignore`** | **No existe** (`OPS-005`) | **No existe** (`COPY . .` copia todo) (`OPS-005`, `OPS-006`) | N/A |
| **Proceso de Arranque (`CMD`)** | `uvicorn` (1 proceso, sin `gunicorn`) (`OPS-007`) | `npm run dev` (Vite dev server) (`OPS-006`) | Sobrescribe `backend` con `--reload` |
| **Persistencia de Volúmenes** | N/A | N/A | `postgres_data`, `redis_data`. **Falta volumen para `/app/data/storage`** (`OPS-007`) |
| **Exposición de Puertos** | `EXPOSE 8000` | `EXPOSE 3000` | `0.0.0.0:5433->5432`, `0.0.0.0:6379->6379`, `8000`, `3000` (`OPS-008`) |
| **Endurecimiento de Runtime** | `HEALTHCHECK` configurado | `HEALTHCHECK` configurado | Sin `cap_drop`, sin `no-new-privileges`, sin límites CPU/RAM (`OPS-008`) |

---

### 3.4 Auditoría del Pipeline CI/CD y Gestión de Dependencias

El flujo [`.github/workflows/ci.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.github/workflows/ci.yml#L1-L260) se estructura en 3 jobs (`backend`, `frontend`, `docker`):

```mermaid
flowchart LR
    subgraph CI["GitHub Actions CI (.github/workflows/ci.yml)"]
        B["Job 1: backend (ubuntu-latest)<br/>- black / isort / ruff / mypy<br/>- pytest --cov=app<br/>- pip-audit -r base.txt"]
        F["Job 2: frontend (ubuntu-latest)<br/>- npm ci<br/>- tsc --noEmit / eslint / prettier<br/>- vitest --coverage<br/>- npm run build / npm audit"]
        D["Job 3: docker (needs: backend, frontend)<br/>- build pevn-backend:ci<br/>- build pevn-frontend:ci"]
        B --> D
        F --> D
    end
```

**Puntos Débiles Críticos en CI/CD (`OPS-009`, `OPS-010`):**
1. **Incompatibilidad de Base de Datos de Prueba en CI (`OPS-009`):** El job `backend` levanta un contenedor PostgreSQL con `POSTGRES_DB: pevn_test` y define `DATABASE_URL: ".../pevn_test"` sin definir `TEST_DATABASE_URL`. Esto contradice directamente [`backend/app/core/db_safety.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/db_safety.py#L28-L325), que exige `TEST_DATABASE_URL` apuntando estrictamente a `pevn_test_db`. Tampoco se ejecuta `alembic upgrade head` en CI para validar la cadena de 33 migraciones.
2. **Ausencia de Lockfile con Hashes en Backend y Excepción en `pip-audit` (`OPS-010`):** `backend/requirements/base.txt`, `production.txt` y `development.txt` usan rangos `>=X.Y.0,<X.(Y+1).0` sin archivo de bloqueo determinista (`requirements.lock`) ni verificación de hashes. Además, `pip-audit` se ejecuta solo sobre `base.txt` (omitiendo `production.txt` y `development.txt`) e incluye `--ignore-vuln PYSEC-2022-42969`.
3. **Ausencia de Escaneo de Contenedores y Secretos en CI (`OPS-004`, `OPS-010`):** El job `docker` compila las imágenes pero no ejecuta Trivy/Grype sobre ellas, y no existe un job de `gitleaks`.

---

### 3.5 Logging, Correlation IDs, Sondas `/health` y `/ready`, y Monitoreo Operativo (`operations.py`)

1. **Sondas `/api/v1/health` y `/api/v1/ready` (`OPS-014`):**
   - [`backend/app/api/v1/endpoints/health.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/health.py#L41-L43) responde `{"status": "ok", "service": "pevn-backend"}` sin tocar dependencias (sonda de *liveness* pura).
   - [`backend/app/api/v1/endpoints/ready.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/ready.py#L75-L136) verifica PostgreSQL (`SELECT 1` mediante `check_database_connectivity()`) y Redis (`PING`), devolviendo HTTP 200 o HTTP 503 sin exponer detalles internos. Sin embargo, `_check_redis_connectivity()` crea y destruye un cliente `aioredis.from_url(...)` en cada petición en vez de usar un pool compartido, y los runbooks de Fase 8 y 9 documentan erróneamente la ruta como `/api/v1/health/ready`.

2. **Cadena de Middlewares y Correlación (`OPS-013`):**
   - En [`backend/app/main.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/main.py#L155-L165), el orden de registro (LIFO en Starlette) es:
     - `RequestLoggingMiddleware` (más interno)
     - `CorrelationIDMiddleware`
     - `RateLimitMiddleware`
     - `SecurityHeadersMiddleware`
     - `TrustedHostMiddleware`
     - `CORSMiddleware` (más externo)
   - Debido a que `RateLimitMiddleware` envuelve por fuera a `CorrelationIDMiddleware`, cuando una petición a `/api/v1/auth/login` es bloqueada con HTTP 429 o 503 en `RateLimitMiddleware`, `CorrelationIDMiddleware` aún no se ha ejecutado. Además, `RateLimitMiddleware` lee `getattr(request.state, "correlation_id", str(uuid.uuid4()))` (línea 98), atributo que `CorrelationIDMiddleware` nunca escribe en `request.state`.
   - Por su parte, `RequestLoggingMiddleware._get_client_ip` (líneas 46–51) toma el primer valor de `X-Forwarded-For` sin validar `TRUSTED_PROXIES`, a diferencia de `RateLimitMiddleware` que sí usa `resolve_client_ip`.

3. **Defectos en el Portal de Operaciones Técnicas Nivel 100 (`OPS-011`, `OPS-012`):**
   - En [`backend/app/services/system_operations_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/system_operations_service.py#L44-L58), `ensure_incident_table_exists` intenta crear la tabla `technical_support_cases` en caliente con `TechnicalIncident.__table__.create(sync_conn, checkfirst=True)`. El modelo `TechnicalIncident` no está importado en `app/db/base.py` y carece de migración Alembic (`OPS-011`).
   - En el mismo servicio (`OPS-012`):
     - `actor_ip="127.0.0.1"` está hardcodeado en todas las escrituras a `audit_logs` (líneas 370, 423, 474).
     - En `get_platform_overview` (línea 114), la variable `yesterday` se calcula pero nunca se aplica al `WHERE` de `sec_query`, por lo que `security_events_24h` reporta el total histórico.
     - En `get_tenant_diagnostics` (línea 473), el acceso legítimo de diagnóstico del `SUPER_ADMIN` se registra como `AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED`.
     - En `get_platform_integrations` (líneas 507–539), el estado y host de Redis y SMTP están hardcodeados.

---

## 4. Lista de Chequeo de Endurecimiento de Infraestructura (Infrastructure Hardening Checklist)

| # | Control de Endurecimiento | Estado Actual | Referencia | Acción Requerida para Producción |
| :-: | :--- | :---: | :--- | :--- |
| 1 | `SECRET_KEY` obligatoria, >= 128 chars hex y sin generación efímera en `production`/`staging` | ❌ Fallo | `OPS-001` | Validar en `Settings.validate_production_settings` que `SECRET_KEY` sea explícita, >= 128 chars y sin texto `REPLACE_ME`. |
| 2 | `DEBUG=False`, `DOCS_URL=None` y `CORS_ORIGINS` sin `*` en `production` y `staging` | ⚠️ Parcial | `OPS-002` | Extender validaciones de `config.py` a `Environment.STAGING` y validar `ALLOWED_HOSTS` y `DATABASE_URL`. |
| 3 | Validación automática de `.env` con `check_env.sh` exigiendo 128 caracteres | ⚠️ Parcial | `OPS-003` | Cargar `.env` en `check_env.sh` y elevar el umbral de `SECRET_KEY` de 64 a 128 caracteres. |
| 4 | Escaneo de secretos `gitleaks` activo en CI/CD y cubriendo todo el repositorio | ❌ Fallo | `OPS-004` | Ampliar `.gitleaks.toml` a todo el repo y agregar step de `gitleaks` en `.github/workflows/ci.yml`. |
| 5 | Exclusión de archivos `*.db`, `*.sqlite*`, `*.sql`, `*.dump` en `.gitignore` y creación de `.dockerignore` | ❌ Fallo | `OPS-005` | Eliminar `backend/pevn.db` y `frontend/tsconfig.tsbuildinfo` del índice Git, actualizar `.gitignore` y crear `.dockerignore`. |
| 6 | `frontend/Dockerfile` multi-stage con Nginx sin privilegios para producción | ❌ Fallo | `OPS-006` | Implementar etapa `builder` (`npm run build`) y etapa `production` con `nginxinc/nginx-unprivileged:alpine`. |
| 7 | `backend/Dockerfile` ejecutando workers `gunicorn` + `UvicornWorker` en producción | ❌ Fallo | `OPS-007` | Cambiar `CMD` de `backend/Dockerfile` a `gunicorn app.main:app -k uvicorn.workers.UvicornWorker`. |
| 8 | Volumen persistente para almacenamiento de archivos (`/app/data/storage`) | ❌ Fallo | `OPS-007` | Montar volumen nombrado `storage_data:/app/data/storage` en `docker-compose.yml` y migrar a S3/MinIO en producción (`OPS-017`). |
| 9 | Puertos de BD/Redis ligados a `127.0.0.1` en dev, autenticación Redis y límites de recursos | ⚠️ Parcial | `OPS-008` | Ligar puertos a `127.0.0.1`, activar `--requirepass` en Redis y añadir `cap_drop: [ALL]` + `no-new-privileges`. |
| 10 | Pipeline CI alineado con `db_safety.py` (`pevn_test_db`) y validación de `alembic upgrade head` | ❌ Fallo | `OPS-009` | Configurar `POSTGRES_DB: pevn_test_db`, `TEST_DATABASE_URL` y ejecutar `alembic upgrade head` en `.github/workflows/ci.yml`. |
| 11 | Dependencias Python bloqueadas con hashes y escaneo Trivy de imágenes Docker | ⚠️ Parcial | `OPS-010` | Generar `requirements.lock` con `pip-compile --generate-hashes`, auditar `production.txt` y escanear imágenes con Trivy. |
| 12 | Migración Alembic para `technical_support_cases` y eliminación de `create_all` en runtime | ❌ Fallo | `OPS-011` | Registrar `TechnicalIncident` en `app/db/base.py`, crear migración `034` y eliminar `ensure_incident_table_exists`. |
| 13 | Telemetría y auditoría fidedigna en `SystemOperationsService` (IP real, filtro 24h, estado SMTP/Redis real) | ❌ Fallo | `OPS-012` | Propagar `client_ip` y `correlation_id`, aplicar `AuditLog.occurred_at >= yesterday` y consultar `settings` reales. |
| 14 | `CorrelationIDMiddleware` externo a `RateLimitMiddleware` y resolución de IP confiable en logs | ⚠️ Parcial | `OPS-013` | Invertir el orden de `CorrelationIDMiddleware` y `RateLimitMiddleware` en `main.py` y usar `resolve_client_ip` en `logging_middleware.py`. |
| 15 | Pool de conexiones compartido para Redis en `/api/v1/ready` y corrección de ruta en runbooks | ⚠️ Parcial | `OPS-014` | Reutilizar pool `aioredis` en `ready.py` y corregir `/api/v1/health/ready` a `/api/v1/ready` en documentación. |
| 16 | Soporte de `MIGRATION_DATABASE_URL` (`pevn_admin`) en Alembic e inmutabilidad estricta de `audit_logs` | ❌ Fallo | `OPS-015` | Soportar `MIGRATION_DATABASE_URL` en `migrations/env.py` y revocar `UPDATE, DELETE` sobre `audit_logs` a `pevn_app`. |
| 17 | Automatización de Backups cifrados (PostgreSQL + Redis + Storage) y pruebas de restauración | ❌ Fallo | `OPS-016` | Implementar scripts y cronjobs documentados en `13_BACKUP_AND_DISASTER_RECOVERY_PLAN.md`. |

---

## 5. Catálogo Estructurado de Hallazgos (`OPS-001` a `OPS-015`)

---

### `OPS-001` — Generación silenciosa de `SECRET_KEY` efímera y ausencia de validación de entropía en `ENVIRONMENT=production` y `staging`

- **Finding ID:** `OPS-001`
- **Módulo afectado:** [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L69) (línea 69 y líneas 232–273).
- **Descripción:** En la clase `Settings`, el atributo `SECRET_KEY` tiene como valor por defecto `""` (línea 69), y el validador `@field_validator("SECRET_KEY", mode="before")` (`ensure_secret_key`, líneas 232–238) genera automáticamente una clave aleatoria mediante `secrets.token_hex(64)` cuando el valor es vacío, sin importar si `ENVIRONMENT` es `production` o `staging`. Además, `validate_production_settings` (líneas 240–273) no verifica que `SECRET_KEY` tenga al menos 128 caracteres ni bloquea el placeholder `REPLACE_ME_WITH_A_MINIMUM_128_CHARACTER_RANDOM_HEX_STRING` de `.env.example`.
- **Causa raíz:** `ensure_secret_key` se ejecuta en modo `before` sin acceso al campo `ENVIRONMENT`, sobrescribiendo la cadena vacía antes de que `validate_production_settings` (`mode="after"`) pueda detectar que `SECRET_KEY` nunca fue provista en el entorno.
- **Impacto:**
  1. Si se despliega en producción con múltiples procesos (`gunicorn -w 4`) o múltiples contenedores sin inyectar `SECRET_KEY`, cada proceso generará una clave distinta en memoria, invalidando el ~75% de las peticiones autenticadas y rompiendo la rotación de tokens.
  2. Si un operador copia `.env.example` a `.env` sin cambiar `SECRET_KEY=REPLACE_ME_WITH_A_MINIMUM_128_CHARACTER_RANDOM_HEX_STRING` (57 caracteres), el backend arranca en producción con una clave públicamente conocida en el repositorio, permitiendo falsificar tokens JWT de `SUPER_ADMIN` (Nivel 100).
- **Severidad:** `CRITICAL`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/core/config.py:232-238
  @field_validator("SECRET_KEY", mode="before")
  @classmethod
  def ensure_secret_key(cls, v: str) -> str:
      """Generate a random secret key if none is provided (development only)."""
      if not v:
          return secrets.token_hex(64)
      return v
  ```
- **Corrección recomendada:**
  Eliminar la generación automática en `mode="before"` para entornos no locales y validar estrictamente en `validate_production_settings` (`mode="after"`):
  ```python
  if self.ENVIRONMENT in (Environment.PRODUCTION, Environment.STAGING):
      if (
          not self.SECRET_KEY
          or len(self.SECRET_KEY) < 128
          or "REPLACE_ME" in self.SECRET_KEY.upper()
          or "CI-TEST" in self.SECRET_KEY.upper()
      ):
          raise ValueError(
              "SECURITY: SECRET_KEY must be explicitly set to a random hex string "
              "of at least 128 characters in staging and production."
          )
  elif not self.SECRET_KEY:
      object.__setattr__(self, "SECRET_KEY", secrets.token_hex(64))
  ```
- **Riesgo residual:** `LOW` (mitigado al garantizar fallo inmediato en el arranque — *fail-fast* — ante claves ausentes, cortas o de plantilla).

---

### `OPS-002` — Ausencia de validación en `production`/`staging` para `DATABASE_URL`, `ALLOWED_HOSTS` y controles de endurecimiento en `staging`

- **Finding ID:** `OPS-002`
- **Módulo afectado:** [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L84-L105) (líneas 84–105 y 240–273).
- **Descripción:** `Settings` define valores por defecto de desarrollo para `DATABASE_URL` (`postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db`) y `ALLOWED_HOSTS` (`["localhost", "127.0.0.1"]`). En `validate_production_settings`, no se verifica que `DATABASE_URL` no contenga contraseñas de desarrollo (`pevn_app_dev_pass`, `REPLACE_ME`) o el superusuario `pevn_admin`, ni que `ALLOWED_HOSTS` no incluya el comodín `"*"` en producción. Adicionalmente, `ENVIRONMENT=staging` no impone `DEBUG=False` ni prohíbe `CORS_ORIGINS=["*"]`.
- **Causa raíz:** Las validaciones de `validate_production_settings` se limitaron a `DEBUG`, `CORS_ORIGINS`, `OPENAPI_URL` y `AUTH_PASSWORD_RESET_DEV_LINK` únicamente cuando `self.ENVIRONMENT == Environment.PRODUCTION`.
- **Impacto:** Posibilidad de iniciar una instancia productiva o de preproducción (`staging`) con `ALLOWED_HOSTS=["*"]` (anulando `TrustedHostMiddleware` contra ataques de *Host Header Injection*), con `DEBUG=True` en `staging`, o conectada como superusuario `pevn_admin`.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/core/config.py:84-86, 104
  DATABASE_URL: str = (
      "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
  )
  ALLOWED_HOSTS: list[str] | str = ["localhost", "127.0.0.1"]
  ```
- **Corrección recomendada:**
  En `validate_production_settings`, validar para `Environment.PRODUCTION` y `Environment.STAGING`:
  1. Prohibir `"*"` en `ALLOWED_HOSTS` y exigir al menos un dominio real en `PRODUCTION`.
  2. Rechazar `DATABASE_URL` si contiene `pevn_app_dev_pass`, `REPLACE_ME` o el usuario `pevn_admin`.
  3. Prohibir `DEBUG=True` y `CORS_ORIGINS=["*"]` también en `Environment.STAGING`.
- **Riesgo residual:** `LOW`.

---

### `OPS-003` — Discrepancia de longitud de `SECRET_KEY` (64 vs 128) y falta de carga de `.env` en `infrastructure/scripts/check_env.sh`

- **Finding ID:** `OPS-003`
- **Módulo afectado:** [`infrastructure/scripts/check_env.sh`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/infrastructure/scripts/check_env.sh#L32-L72) (líneas 32–72) y [`docs/DEPLOYMENT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/DEPLOYMENT.md#L35-L44) (líneas 35–44).
- **Descripción:**
  1. `.env.example` (línea 31) y `check_env.sh` (línea 52) indican que `SECRET_KEY` debe tener mínimo 128 caracteres, pero la validación en la línea 67 de `check_env.sh` evalúa `[ ${#SECRET_KEY} -lt 64 ]`.
  2. `check_env.sh` lee `${!var_name}` del entorno del proceso actual sin hacer `source .env`. Al seguir el flujo de `docs/DEPLOYMENT.md` (`cp .env.example .env`, editar `.env` y ejecutar `./infrastructure/scripts/check_env.sh`), el script falla reportando todas las variables como `✗ MISSING`.
- **Causa raíz:** Omisión de carga automática de `.env` (`set -a; source .env; set +a`) al inicio del script y umbral desactualizado (`64` en lugar de `128`).
- **Impacto:** Falsos negativos al validar claves de entre 64 y 127 caracteres y fricción operativa que lleva a los operadores a omitir el uso de `check_env.sh`.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  ```bash
  # infrastructure/scripts/check_env.sh:66-70
  if [ -n "$SECRET_KEY" ] && [ ${#SECRET_KEY} -lt 64 ]; then
      echo -e "${YELLOW}⚠ WARNING${NC}  SECRET_KEY is shorter than 64 characters"
      ERRORS=$((ERRORS + 1))
  ```
- **Corrección recomendada:**
  Cargar `.env` si existe al inicio de `check_env.sh` (`if [ -f .env ]; then set -a; source .env; set +a; fi`) y actualizar la condición a `[ ${#SECRET_KEY} -lt 128 ]`.
- **Riesgo residual:** `LOW`.

---

### `OPS-004` — Cobertura restringida en `.gitleaks.toml` y ausencia de ejecución de Gitleaks en el pipeline CI/CD

- **Finding ID:** `OPS-004`
- **Módulo afectado:** [`.gitleaks.toml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitleaks.toml#L10-L37) (líneas 10–37) y [`.github/workflows/ci.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.github/workflows/ci.yml#L1-L260).
- **Descripción:**
  1. El archivo `.gitleaks.toml` define dos reglas específicas para PEVN (`pevn-plaintext-password-assignment` y `pevn-jwt-secret-leak`), pero ambas restringen su alcance a `path = '''backend/app/.*'''` (líneas 29 y 36), dejando fuera a `frontend/`, `infrastructure/`, `scripts/` y `docker-compose.yml`.
  2. El `[allowlist]` global excluye por completo `'''docs/.*'''` (línea 13), lo que impide detectar credenciales filtradas accidentalmente en documentación o reportes técnicos.
  3. **Gitleaks no está integrado en `.github/workflows/ci.yml`**, por lo que ningún push o pull request es escaneado automáticamente en CI.
- **Causa raíz:** Configuración parcial durante la fase NTA-05 enfocada únicamente en `backend/app/` y falta de un job de escaneo de secretos en GitHub Actions.
- **Impacto:** Riesgo alto de filtración inadvertida de secretos, tokens o salts de BigBlueButton en scripts de infraestructura, configuraciones de frontend o documentación sin bloqueo en CI.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```toml
  # .gitleaks.toml:25-36
  [[rules]]
  id = "pevn-plaintext-password-assignment"
  ...
  path = '''backend/app/.*'''
  ```
- **Corrección recomendada:**
  1. Eliminar la restricción `path = '''backend/app/.*'''` en `.gitleaks.toml` para que las reglas apliquen a todo el repositorio (excluyendo únicamente tests sintéticos específicos).
  2. Agregar un job `secrets-scan` en `.github/workflows/ci.yml` utilizando `gitleaks/gitleaks-action@v2`.
- **Riesgo residual:** `LOW`.

---

### `OPS-005` — Base de datos SQLite (`backend/pevn.db`) y artefactos de compilación versionados en Git, brechas en `.gitignore` y ausencia de `.dockerignore`

- **Finding ID:** `OPS-005`
- **Módulo afectado:** [`.gitignore`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitignore#L1-L187), `backend/pevn.db`, `frontend/tsconfig.tsbuildinfo`, `backend/` y `frontend/`.
- **Descripción:**
  1. La inspección del índice de Git (`git ls-files`) reveló que el archivo de base de datos SQLite `backend/pevn.db` y el artefacto incremental `frontend/tsconfig.tsbuildinfo` están versionados en el repositorio.
  2. `.gitignore` no incluye patrones para bases de datos locales ni volcados de respaldo (`*.db`, `*.sqlite`, `*.sqlite3`, `*.sql`, `*.dump`, `backup_*`), ni `*.tsbuildinfo`.
  3. No existen archivos `.dockerignore` en `backend/` ni en `frontend/`. Al ejecutar `docker build`, el contexto de compilación transfiere `.venv`, `.env`, `pevn.db`, `data/` y `node_modules` al demonio de Docker.
- **Causa raíz:** Omisión de extensiones de bases de datos/backups en `.gitignore` y falta de creación de `.dockerignore` en ambos contextos de construcción.
- **Impacto:**
  1. Si un operador ejecuta el comando de backup de `docs/OPERATIONS.md` (`pg_dump ... > backup_YYYYMMDD.sql`) en la raíz del proyecto y ejecuta `git add .`, subirá al repositorio un volcado completo de PostgreSQL con datos personales de menores (Ley 1581 de 2012) y hashes de contraseñas.
  2. En `frontend/Dockerfile`, `COPY . .` sin `.dockerignore` empaqueta cualquier archivo `.env.local` o artefacto local dentro de la imagen del contenedor.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  Ejecución de `git ls-files "*.env*" "*.db" "*tsbuildinfo*"`:
  ```text
  .env.example
  backend/pevn.db
  frontend/.env.example
  frontend/tsconfig.tsbuildinfo
  ```
- **Corrección recomendada:**
  1. Ejecutar `git rm --cached backend/pevn.db frontend/tsconfig.tsbuildinfo`.
  2. Añadir a `.gitignore`: `*.db`, `*.sqlite`, `*.sqlite3`, `*.sql`, `*.dump`, `*.backup`, `backup_*`, `*.tsbuildinfo`.
  3. Crear `backend/.dockerignore` y `frontend/.dockerignore` excluyendo `.env*`, `.venv/`, `node_modules/`, `tests/`, `coverage/`, `data/`, `*.db`, `*.md`.
- **Riesgo residual:** `LOW`.

---

### `OPS-006` — `frontend/Dockerfile` carece de construcción multi-etapa para producción y ejecuta el servidor de desarrollo Vite (`npm run dev`)

- **Finding ID:** `OPS-006`
- **Módulo afectado:** [`frontend/Dockerfile`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/Dockerfile#L1-L49) (líneas 1–49) y [`.github/workflows/ci.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.github/workflows/ci.yml#L251-L260) (líneas 251–260).
- **Descripción:** `frontend/Dockerfile` contiene únicamente una etapa `FROM node:20.18-alpine AS development` que instala todas las dependencias de desarrollo (`npm ci`), copia el código fuente completo (`COPY . .`) y arranca el servidor de desarrollo de Vite (`CMD ["npm", "run", "dev"]`). No existe una etapa `builder` (`npm run build`) ni una etapa final de producción basada en un servidor web ligero y endurecido (como `nginxinc/nginx-unprivileged:alpine`) con soporte para enrutamiento SPA (`try_files $uri $uri/ /index.html`) y cabeceras de seguridad.
- **Causa raíz:** El `Dockerfile` de frontend fue escrito en la Fase 1 exclusivamente para hot-reload en desarrollo local (como indica su propio comentario en las líneas 4–6) y nunca fue actualizado a multi-stage para producción.
- **Impacto:** No existe una imagen de contenedor de producción para el frontend. Desplegar la imagen actual en staging o producción expondría el servidor de desarrollo Vite al tráfico público, con un tamaño de imagen inflado (~400+ MB con compiladores y `devDependencies`), bajo rendimiento bajo concurrencia y superficie de ataque innecesaria (Node.js + npm + código fuente TypeScript completo dentro del contenedor).
- **Severidad:** `CRITICAL`
- **Evidencia / Reproducción:**
  ```dockerfile
  # frontend/Dockerfile:9, 26, 30, 48
  FROM node:20.18-alpine AS development
  ...
  RUN npm ci --prefer-offline
  COPY . .
  ...
  CMD ["npm", "run", "dev"]
  ```
- **Corrección recomendada:**
  Reestructurar `frontend/Dockerfile` en tres etapas:
  1. `development`: para `docker-compose.yml` local.
  2. `builder`: ejecuta `npm ci` y `npm run build` generando `/app/dist`.
  3. `final` (target por defecto para producción): basado en `nginxinc/nginx-unprivileged:1.27-alpine`, copiando únicamente `/app/dist` a `/usr/share/nginx/html` y un archivo `nginx.conf` con `try_files $uri $uri/ /index.html;` escuchando en el puerto no privilegiado `8080`.
- **Riesgo residual:** `LOW`.

---

### `OPS-007` — `backend/Dockerfile` utiliza `uvicorn` monoproceso en lugar de `gunicorn` en su `CMD` de producción y `docker-compose.yml` no persiste el volumen de almacenamiento `/app/data/storage`

- **Finding ID:** `OPS-007`
- **Módulo afectado:** [`backend/Dockerfile`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/Dockerfile#L85-L88) (líneas 85–88), [`backend/requirements/production.txt`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/requirements/production.txt#L10-L15) y [`docker-compose.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docker-compose.yml#L91-L142).
- **Descripción:**
  1. Aunque `backend/requirements/production.txt` instala `gunicorn>=23.0.0,<24.0.0` con la instrucción explícita de usar `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`, la etapa `final` de `backend/Dockerfile` (línea 87) ejecuta un único proceso `uvicorn`: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]`.
  2. El servicio de almacenamiento físico (`LocalStorageDriver` en `backend/app/core/storage/local.py`) guarda los recursos docentes y entregas estudiantiles en `STORAGE_LOCAL_PATH = "./data/storage"` (`/app/data/storage` dentro del contenedor). En `backend/Dockerfile` no se declara ni pre-crea `/app/data/storage` con permisos para `pevn:pevn`, y en `docker-compose.yml` no existe un volumen persistente dedicado para `/app/data/storage`.
- **Causa raíz:** Desalineación entre `requirements/production.txt` y el `CMD` de `backend/Dockerfile`, y adición posterior del módulo de almacenamiento local (Fase B3-H11) sin actualizar `Dockerfile` ni los volúmenes nombrados de `docker-compose.yml`.
- **Impacto:**
  1. En producción, el backend corre en un solo núcleo de CPU sin gestor de procesos maestro que reinicie workers bloqueados o con fugas de memoria (`--max-requests`).
  2. En despliegues de contenedores sin el bind-mount de desarrollo `./backend:/app`, todos los documentos PDF/Office subidos por docentes y estudiantes se escriben en la capa efímera del contenedor y **se pierden irreversiblemente** al recrear o actualizar el contenedor.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```dockerfile
  # backend/Dockerfile:87
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
  ```
- **Corrección recomendada:**
  1. Actualizar `backend/Dockerfile` para crear `/app/data/storage` con propietario `pevn:pevn` y cambiar el `CMD` de producción a:
     ```dockerfile
     CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "60", "--graceful-timeout", "30", "--max-requests", "2000", "--max-requests-jitter", "200"]
     ```
  2. Agregar el volumen nombrado `storage_data:/app/data/storage` en `docker-compose.yml`.
- **Riesgo residual:** `LOW`.

---

### `OPS-008` — Exposición de puertos internos en todas las interfaces (`0.0.0.0`), Redis sin autenticación, inconsistencia de variables en `docker-compose.yml` y falta de directivas de endurecimiento de contenedores

- **Finding ID:** `OPS-008`
- **Módulo afectado:** [`docker-compose.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docker-compose.yml#L30-L168) (líneas 30–168) y [`docs/OPERATIONS.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/OPERATIONS.md#L105).
- **Descripción:**
  1. En `docker-compose.yml`, los puertos de PostgreSQL (`"${POSTGRES_PORT:-5433}:5432"`) y Redis (`"6379:6379"`) se publican en `0.0.0.0` en lugar de `127.0.0.1`, y Redis se ejecuta sin contraseña (`--requirepass`).
  2. En el servicio `db` (líneas 38–39), se definen valores por defecto `${POSTGRES_APP_USER:-pevn_app}` y `${POSTGRES_APP_PASSWORD:-pevn_app_dev_pass}`, pero en el servicio `backend` (línea 106) `DATABASE_URL` usa `${POSTGRES_APP_USER}:${POSTGRES_APP_PASSWORD}` **sin los valores por defecto**, causando un fallo de conexión si las variables no están definidas en `.env`.
  3. `docs/OPERATIONS.md` (línea 105) y `docs/DEPLOYMENT.md` (línea 82) documentan el puerto local de PostgreSQL como `5432`, mientras que `docker-compose.yml` (línea 50) y `config.py` (línea 85) usan `5433`.
  4. Ningún contenedor en `docker-compose.yml` configura `security_opt: ["no-new-privileges:true"]`, `cap_drop: ["ALL"]` ni límites de memoria/CPU.
- **Causa raíz:** Configuración orientada a facilidad de desarrollo local sin restricciones de interfaz de loopback ni controles CIS Docker Benchmark.
- **Impacto:** Exposición de Redis (sin autenticación) y PostgreSQL en redes locales compartidas; fallos de conexión por interpolación incompleta de variables en `docker-compose.yml`; riesgo de agotamiento de recursos del host (DoS) ante fugas de memoria.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  ```yaml
  # docker-compose.yml:78, 106
  ports:
    - "6379:6379"
  ...
  DATABASE_URL: postgresql+asyncpg://${POSTGRES_APP_USER}:${POSTGRES_APP_PASSWORD}@db:5432/${POSTGRES_DB}
  ```
- **Corrección recomendada:**
  1. Ligar los puertos de desarrollo a loopback: `"127.0.0.1:${POSTGRES_PORT:-5433}:5432"` y `"127.0.0.1:6379:6379"`.
  2. Unificar los defaults en la línea 106 de `docker-compose.yml`: `${POSTGRES_APP_USER:-pevn_app}:${POSTGRES_APP_PASSWORD:-pevn_app_dev_pass}@db:5432/${POSTGRES_DB:-pevn_db}`.
  3. Añadir `security_opt: ["no-new-privileges:true"]` y límites de recursos a todos los servicios.
- **Riesgo residual:** `LOW`.

---

### `OPS-009` — Desconexión crítica en CI/CD (`.github/workflows/ci.yml`) respecto a `db_safety.py` (`pevn_test` vs `pevn_test_db`), uso de superusuario en pruebas y ausencia de verificación de migraciones Alembic

- **Finding ID:** `OPS-009`
- **Módulo afectado:** [`.github/workflows/ci.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.github/workflows/ci.yml#L39-L77) (líneas 39–77 y 113–121) y [`backend/app/core/db_safety.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/db_safety.py#L28-L327).
- **Descripción:**
  1. En `.github/workflows/ci.yml` (líneas 44 y 71), el servicio PostgreSQL de CI crea la base de datos `pevn_test` y asigna `DATABASE_URL: "postgresql+asyncpg://pevn_test_admin:...@localhost:5432/pevn_test"`, omitiendo por completo la variable `TEST_DATABASE_URL`.
  2. Sin embargo, el módulo de seguridad de base de datos `backend/app/core/db_safety.py` (implementado en DOC-03-R3) exige de manera *fail-closed* que exista `TEST_DATABASE_URL` y que el nombre de la base de datos sea exactamente `pevn_test_db` (`ALLOWED_TEST_DATABASES = frozenset({"pevn_test_db"})`). Cualquier test de integración que invoque `get_safe_test_db_url()` o `validate_and_sanitize_db_url(..., mode="test")` en GitHub Actions fallará con `DatabaseSecurityError`.
  3. Además, CI ejecuta las pruebas como superusuario (`pevn_test_admin`) en lugar de inicializar el usuario de privilegios mínimos `pevn_app`, y **no ejecuta `alembic upgrade head`** antes de `pytest`, dejando las 33 migraciones de Alembic sin prueba de ejecución limpia en CI.
- **Causa raíz:** `.github/workflows/ci.yml` conserva la configuración inicial de la Fase 1 y no fue actualizado cuando se introdujeron `db_safety.py` (`pevn_test_db`) y las migraciones de las Fases 2 a 16.
- **Impacto:** Fallo de pruebas de integración que dependen de `TEST_DATABASE_URL`/`pevn_test_db` en CI, y ausencia de detección en CI de migraciones Alembic rotas o de operaciones de código que requieran privilegios de superusuario que `pevn_app` no posee en producción (como `OPS-011`).
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```yaml
  # .github/workflows/ci.yml:44, 71
  POSTGRES_DB: pevn_test
  ...
  DATABASE_URL: "postgresql+asyncpg://pevn_test_admin:ci_test_password_not_a_secret@localhost:5432/pevn_test"
  ```
  Contra `backend/app/core/db_safety.py:28`:
  ```python
  ALLOWED_TEST_DATABASES: frozenset[str] = frozenset({"pevn_test_db"})
  ```
- **Corrección recomendada:**
  En `.github/workflows/ci.yml`:
  1. Cambiar `POSTGRES_DB: pevn_test_db`.
  2. Definir tanto `DATABASE_URL` como `TEST_DATABASE_URL` apuntando a `pevn_test_db`.
  3. Agregar un paso previo a `pytest`: `alembic upgrade head` (con `pevn_test_admin`) y ejecutar `01-init-app-user.sh` para correr `pytest` con `pevn_app`.
- **Riesgo residual:** `LOW`.

---

### `OPS-010` — Ausencia de lockfile con hashes criptográficos en Python, alcance parcial e ignorado de CVE en `pip-audit`, y falta de escaneo de vulnerabilidades en imágenes Docker

- **Finding ID:** `OPS-010`
- **Módulo afectado:** [`backend/requirements/base.txt`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/requirements/base.txt#L1-L65), [`backend/requirements/production.txt`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/requirements/production.txt#L1-L16) y [`.github/workflows/ci.yml`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.github/workflows/ci.yml#L131-L135) (líneas 131–135 y 212–260).
- **Descripción:**
  1. Las dependencias de Python en `backend/requirements/*.txt` utilizan rangos semánticos (`>=X.Y.0,<X.(Y+1).0`) sin un archivo de bloqueo de versiones exactas ni hashes SHA-256 (`--require-hashes`), por lo que las dependencias transitivas no están fijadas y dos compilaciones de `backend/Dockerfile` en fechas distintas pueden producir binarios diferentes.
  2. En `.github/workflows/ci.yml` (línea 132), `pip-audit` solo escanea `requirements/base.txt` (omitiendo `requirements/production.txt`) y suprime explícitamente `PYSEC-2022-42969` (`--ignore-vuln PYSEC-2022-42969`, vulnerabilidad en `py` que no debería estar presente en un entorno Python 3.12 moderno con `pytest>=8.3.4`).
  3. El job `docker` no ejecuta ningún escáner de vulnerabilidades de sistema operativo/paquetes Debian/Alpine (como `aquasecurity/trivy-action`) sobre `pevn-backend:ci` y `pevn-frontend:ci`.
- **Causa raíz:** Uso de archivos `requirements/*.txt` manuales sin `pip-tools` (`pip-compile`) o `uv lock`.
- **Impacto:** Susceptibilidad a ataques de cadena de suministro (Supply Chain Attacks) en dependencias transitivas de Python y vulnerabilidades a nivel de paquetes del sistema operativo (`apt`/`apk`) en las imágenes de contenedor.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  ```yaml
  # .github/workflows/ci.yml:131-134
  - name: Security audit (pip-audit)
    run: pip-audit -r requirements/base.txt --ignore-vuln PYSEC-2022-42969
  ```
- **Corrección recomendada:**
  1. Generar archivos `requirements/production.lock` con versiones exactas y hashes mediante `pip-compile --generate-hashes` e instalar con `pip install --no-cache-dir --require-hashes` en `backend/Dockerfile`.
  2. Ejecutar `pip-audit -r requirements/production.txt` sin `--ignore-vuln` e integrar `aquasecurity/trivy-action` en el job `docker` de CI.
- **Riesgo residual:** `LOW`.

---

### `OPS-011` — Ejecución de DDL en tiempo de ejecución (`TechnicalIncident.__table__.create`) en `SystemOperationsService`, omisión en `app/db/base.py` y ausencia de migración Alembic para `technical_support_cases`

- **Finding ID:** `OPS-011`
- **Módulo afectado:** [`backend/app/services/system_operations_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/system_operations_service.py#L44-L58) (líneas 44–58), [`backend/app/db/base.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/base.py#L10-L91) y `backend/migrations/versions/`.
- **Descripción:**
  1. El modelo `TechnicalIncident` (`__tablename__ = "technical_support_cases"`, definido en `backend/app/models/technical_incident.py`) **no tiene ninguna migración en `backend/migrations/versions/`** y **no está importado en `backend/app/db/base.py`** (por lo que Alembic desconoce su existencia).
  2. En su lugar, `SystemOperationsService.ensure_incident_table_exists` ejecuta `TechnicalIncident.__table__.create(sync_conn, checkfirst=True)` durante las peticiones HTTP de la aplicación, y captura cualquier error con un bloque vacío `except Exception: self._table_initialized = True`.
  3. En un entorno PostgreSQL inicializado con `01-init-app-user.sh`, el usuario de la aplicación (`pevn_app`) tiene revocado el permiso `CREATE ON SCHEMA public` (línea 78). Por consiguiente, `TechnicalIncident.__table__.create(...)` falla con `InsufficientPrivilegeError`, el error es silenciado, y las llamadas a `/api/v1/system/operations/support-cases` terminan lanzando `UndefinedTableError: relation "technical_support_cases" does not exist` (HTTP 500).
- **Causa raíz:** Creación ad-hoc de la tabla desde el servicio en lugar de seguir el flujo canónico de migraciones Alembic y registro en `app/db/base.py`.
- **Impacto:** Violación directa de la política de seguridad de base de datos (la aplicación nunca debe ejecutar DDL en runtime) y caída funcional (`HTTP 500`) del módulo de soporte técnico de `SUPER_ADMIN` cuando se ejecuta bajo el usuario de privilegios mínimos `pevn_app`.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/services/system_operations_service.py:49-57
  try:
      engine = get_engine()
      async with engine.begin() as conn:
          await conn.run_sync(
              lambda sync_conn: TechnicalIncident.__table__.create(sync_conn, checkfirst=True)
          )
      self._table_initialized = True
  except Exception:
      self._table_initialized = True
  ```
- **Corrección recomendada:**
  1. Importar y exportar `TechnicalIncident` (así como los demás modelos faltantes en `base.py`) dentro de `backend/app/db/base.py`.
  2. Crear la migración `backend/migrations/versions/034_technical_support_cases.py` que cree la tabla `technical_support_cases` y su índice `ix_technical_cases_status_severity`.
  3. Eliminar el método `ensure_incident_table_exists` de `SystemOperationsService`.
- **Riesgo residual:** `LOW`.

---

### `OPS-012` — Hardcoding de `actor_ip="127.0.0.1"`, omisión del filtro temporal de 24h en `security_events_24h`, clasificación errónea de auditoría y telemetría simulada en `SystemOperationsService`

- **Finding ID:** `OPS-012`
- **Módulo afectado:** [`backend/app/services/system_operations_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/system_operations_service.py#L113-L540) (líneas 113–137, 367–383, 420–436, 470–488, 507–539) y [`backend/app/api/v1/endpoints/operations.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/operations.py#L64-L214).
- **Descripción:** Se identificaron cuatro defectos en la telemetría y auditoría del Portal de Operaciones Técnicas (Nivel 100):
  1. **IP de auditoría falsificada:** En `create_support_case` (línea 370), `update_support_case` (línea 423) y `get_tenant_diagnostics` (línea 474), se invoca `audit_service.record(AuditEvent(..., actor_ip="127.0.0.1"))` sin propagar la IP real del cliente ni el `correlation_id` de la petición.
  2. **Filtro de 24 horas omitido en `security_events_24h`:** En `get_platform_overview` (línea 114), se define `yesterday = datetime.now(UTC) - timedelta(days=1)`, pero la consulta `sec_query` (líneas 117–132) **nunca filtra por `AuditLog.occurred_at >= yesterday`**, devolviendo el conteo histórico acumulado de todos los tiempos bajo la etiqueta `security_events_24h`.
  3. **Contaminación de eventos de seguridad:** En `get_tenant_diagnostics` (línea 473), la inspección diagnóstica legítima realizada por el `SUPER_ADMIN` se registra con `event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED`, inflando artificialmente las alertas de actividad sospechosa cada vez que el operador diagnostica un colegio.
  4. **Estado de integraciones hardcodeado:** En `get_platform_integrations` (líneas 527–537), Redis reporta `"safe_host": "redis://localhost:6379/0"` y `"status": "active"` sin consultar `settings.REDIS_URL` ni `_check_redis()`, y el servicio de correo reporta `"safe_host": "smtp.pevn.edu.co:587"` y `"status": "configured"` aunque `settings.SMTP_HOST` sea `None` y `settings.EMAIL_DELIVERY_ENABLED` sea `False`.
- **Causa raíz:** Implementación incompleta de las consultas de telemetría y falta de inyección del objeto `Request` (o `client_ip` / `correlation_id`) desde los endpoints de `operations.py` hacia `SystemOperationsService`.
- **Impacto:** Pérdida de trazabilidad forense de la dirección IP desde la cual actúa un `SUPER_ADMIN`, métricas de seguridad de 24 horas engañosas en el tablero de control y falsos positivos de integraciones supuestamente activas cuando están deshabilitadas o caídas.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/services/system_operations_service.py:114-133
  yesterday = datetime.now(UTC) - timedelta(days=1)
  security_count = 0
  try:
      sec_query = (
          select(func.count())
          .select_from(AuditLog)
          .where(
              or_(
                  AuditLog.event_type.like("security.%"),
                  ...
              )
          ) # <-- Falta: AuditLog.occurred_at >= yesterday
      )
  ```
- **Corrección recomendada:**
  1. Añadir `.where(AuditLog.occurred_at >= yesterday)` en `sec_query`.
  2. Pasar `actor_ip=getattr(request.state, "client_ip", ...)` y `correlation_id=correlation_id_ctx.get()` desde `operations.py` a `SystemOperationsService`.
  3. Usar un tipo de evento apropiado (ej. `AuditEventType.SUPERADMIN_TENANT_DIAGNOSTIC_READ` o `CONFIG_CHANGED`) en lugar de `SUSPICIOUS_ACTIVITY_DETECTED`.
  4. En `get_platform_integrations`, enmascarar `settings.REDIS_URL` y evaluar `await self._check_redis()`, así como inspeccionar `settings.EMAIL_DELIVERY_ENABLED` y `settings.SMTP_HOST`.
- **Riesgo residual:** `LOW`.

---

### `OPS-013` — Spoofing de `X-Forwarded-For` en `RequestLoggingMiddleware`, desalineación de orden entre `RateLimitMiddleware` y `CorrelationIDMiddleware`, y sanitización superficial en `logging.py`

- **Finding ID:** `OPS-013`
- **Módulo afectado:** [`backend/app/middleware/logging_middleware.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/middleware/logging_middleware.py#L46-L62) (líneas 46–62), [`backend/app/middleware/rate_limit_middleware.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/middleware/rate_limit_middleware.py#L98) (línea 98), [`backend/app/main.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/main.py#L155-L162) (líneas 155–162) y [`backend/app/core/logging.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/logging.py#L74-L86).
- **Descripción:**
  1. En `logging_middleware.py` (líneas 46–51), `_get_client_ip(request)` extrae `request.headers.get("X-Forwarded-For").split(",")[0].strip()` sin verificar si el peer directo pertenece a `settings.TRUSTED_PROXIES`. Un cliente malicioso puede enviar `X-Forwarded-For: 1.2.3.4` y falsificar su IP en todos los registros de log HTTP.
  2. En `main.py` (líneas 158–161), `RateLimitMiddleware` se registra después de `CorrelationIDMiddleware`. Por el orden LIFO de Starlette, `RateLimitMiddleware` se ejecuta *antes* de que `CorrelationIDMiddleware` inicialice `correlation_id_ctx`. Cuando `RateLimitMiddleware` bloquea una petición (HTTP 429/503), genera un UUID aislado (`getattr(request.state, "correlation_id", str(uuid.uuid4()))`) y la respuesta sale sin la cabecera `X-Correlation-ID`.
  3. En `app/core/logging.py` (líneas 74–85), `_sanitize_sensitive_fields` solo redacta coincidencias exactas en el nivel superior de `event_dict`, sin recorrer diccionarios anidados ni detectar sufijos como `new_password` o `reset_token` (como sí lo hace `sanitize_audit_metadata` en `app/audit/service.py`).
- **Causa raíz:** Implementación separada de la resolución de IP y sanitización en los middlewares iniciales de Fase 1 respecto al endurecimiento introducido en la Fase NTA-05 (`rate_limit_middleware.py` y `audit/service.py`).
- **Impacto:** Falsificación de direcciones IP en los logs de acceso y pérdida de correlación de trazas (`X-Correlation-ID`) durante ataques de fuerza bruta bloqueados por el rate limiter.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/middleware/logging_middleware.py:46-51
  def _get_client_ip(request: Request) -> str:
      """Extract client IP, respecting X-Forwarded-For if set by reverse proxy."""
      forwarded = request.headers.get("X-Forwarded-For")
      if forwarded:
          return forwarded.split(",")[0].strip()
      return request.client.host if request.client else "unknown"
  ```
- **Corrección recomendada:**
  1. En `main.py`, registrar `CorrelationIDMiddleware` **después** de `RateLimitMiddleware` (para que se ejecute antes en el flujo de entrada) y asignar también `request.state.correlation_id = correlation_id` en `CorrelationIDMiddleware`.
  2. En `logging_middleware.py`, reutilizar `resolve_client_ip` de `app.core.security.rate_limiter` (o leer `getattr(request.state, "client_ip", ...)`).
  3. Hacer recursiva la función `_sanitize_sensitive_fields` en `app/core/logging.py`.
- **Riesgo residual:** `LOW`.

---

### `OPS-014` — Creación efímera de conexiones Redis sin pool en cada llamada a `/api/v1/ready` y ruta errónea `/api/v1/health/ready` en runbooks operativos

- **Finding ID:** `OPS-014`
- **Módulo afectado:** [`backend/app/api/v1/endpoints/ready.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/ready.py#L112-L136) (líneas 112–136), [`docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md#L85) (línea 85) y [`docs/PHASE_9_ROLLBACK_RUNBOOK.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_9_ROLLBACK_RUNBOOK.md#L36) (línea 36).
- **Descripción:**
  1. En `ready.py`, la función `_check_redis_connectivity()` instancia un nuevo cliente `aioredis.from_url(settings.REDIS_URL, ...)`, ejecuta `await client.ping()` y cierra la conexión (`await client.aclose()`) en cada petición HTTP a `GET /api/v1/ready`. Dado que `/api/v1/ready` es público (no requiere autenticación) y no está sujeto a rate limiting, un volumen alto de peticiones a `/api/v1/ready` fuerza la apertura y cierre continuo de sockets TCP hacia Redis y consultas `SELECT 1` hacia PostgreSQL.
  2. En `docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md` (línea 85) y `docs/PHASE_9_ROLLBACK_RUNBOOK.md` (línea 36), el comando de verificación documentado es `curl -X GET https://api.pevn.gov.co/api/v1/health/ready`, ruta inexistente que devuelve HTTP 404 (la ruta real es `/api/v1/ready`).
- **Causa raíz:** Ausencia de un singleton de pool de conexiones Redis compartido en el ciclo de vida (`lifespan`) de FastAPI y error tipográfico en los runbooks de las Fases 8 y 9.
- **Impacto:** Riesgo de agotamiento de sockets efímeros o conexiones a Redis ante sondeos agresivos sobre `/api/v1/ready`, y confusión operativa durante procedimientos de contingencia al recibir HTTP 404 en `/api/v1/health/ready`.
- **Severidad:** `MEDIUM`
- **Evidencia / Reproducción:**
  ```python
  # backend/app/api/v1/endpoints/ready.py:122-128
  client = aioredis.from_url(
      settings.REDIS_URL,
      socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
      socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
  )
  await client.ping()
  await client.aclose()
  ```
- **Corrección recomendada:**
  1. Inicializar un pool de conexiones `aioredis` compartido durante el `lifespan` de la aplicación (en `app/main.py`) y reutilizarlo en `ready.py` y `system_operations_service.py`, además de cachear el resultado de `/api/v1/ready` por 2–5 segundos (TTL corto en memoria) para proteger a PostgreSQL y Redis contra ráfagas de sondeo.
  2. Corregir `/api/v1/health/ready` por `/api/v1/ready` en `docs/PHASE_8_PRODUCTION_OPERATIONS_RUNBOOK.md` y `docs/PHASE_9_ROLLBACK_RUNBOOK.md`.
- **Riesgo residual:** `LOW`.

---

### `OPS-015` — Incompatibilidad de privilegios en `migrations/env.py` (`pevn_app` sin permiso `CREATE` al ejecutar `alembic upgrade head`) y permisos `UPDATE`/`DELETE` excesivos sobre `audit_logs` en `01-init-app-user.sh`

- **Finding ID:** `OPS-015`
- **Módulo afectado:** [`infrastructure/docker/postgres/01-init-app-user.sh`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/infrastructure/docker/postgres/01-init-app-user.sh#L56-L79) (líneas 56–79), [`backend/migrations/env.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/env.py#L44-L48) (líneas 44–48 y 97–102) y [`docs/DEPLOYMENT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/DEPLOYMENT.md#L53) (línea 53).
- **Descripción:**
  1. `01-init-app-user.sh` revoca explícitamente el privilegio `CREATE` en el esquema `public` al usuario `pevn_app` (`REVOKE CREATE ON SCHEMA public FROM "${POSTGRES_APP_USER}"`). Sin embargo, en `docker-compose.yml` el contenedor `backend` recibe `DATABASE_URL` con las credenciales de `pevn_app`, y `backend/migrations/env.py` utiliza exclusivamente `settings.DATABASE_URL`. Por tanto, al ejecutar `docker compose exec backend alembic upgrade head` (como indican `docs/DEPLOYMENT.md` y `docs/OPERATIONS.md`), Alembic se conecta como `pevn_app` y falla por falta de privilegios DDL.
  2. Aunque `docs/DATABASE.md` (línea 164) y `backend/app/audit/service.py` (línea 9) establecen que `audit_logs` es una tabla inmutable (*append-only*, sin permisos `UPDATE` ni `DELETE` para el usuario de aplicación), `01-init-app-user.sh` (líneas 57–65) concede `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pevn_app` y `ALTER DEFAULT PRIVILEGES ... GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO pevn_app`, permitiendo que `pevn_app` modifique o elimine registros de auditoría si ocurre una vulnerabilidad en la capa de aplicación.
- **Causa raíz:** Falta de una variable `MIGRATION_DATABASE_URL` (que utilice `pevn_admin` únicamente durante el job de migración) en `migrations/env.py`, y ausencia de una cláusula `REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM pevn_app` en la migración `001_phase2_auth_schema.py` o en un trigger de base de datos.
- **Impacto:** Imposibilidad de aplicar migraciones Alembic desde el contenedor `backend` cuando se respeta la separación de usuarios, y riesgo de alteración/borrado del rastro forense en `audit_logs` por parte del usuario de aplicación `pevn_app`.
- **Severidad:** `HIGH`
- **Evidencia / Reproducción:**
  ```sql
  -- infrastructure/docker/postgres/01-init-app-user.sh:61-65, 78
  ALTER DEFAULT PRIVILEGES
      IN SCHEMA public
      GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
      TO "${POSTGRES_APP_USER}";
  ...
  REVOKE CREATE ON SCHEMA public FROM "${POSTGRES_APP_USER}";
  ```
- **Corrección recomendada:**
  1. Modificar `backend/migrations/env.py` para preferir `os.environ.get("MIGRATION_DATABASE_URL") or settings.DATABASE_URL`, permitiendo inyectar las credenciales de `pevn_admin` exclusivamente al comando o job de migración.
  2. Añadir una migración Alembic que cree un trigger en PostgreSQL que prohíba `UPDATE` y `DELETE` sobre `audit_logs` (excepto para operaciones de archivado particionado por superusuario) y ejecute `REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_logs FROM pevn_app`.
- **Riesgo residual:** `LOW`.

---

## 6. Referencia Cruzada con el Plan de Respaldo y Recuperación ante Desastres

Los hallazgos **`OPS-016` (`CRITICAL`)**, **`OPS-017` (`HIGH`)** y **`OPS-018` (`MEDIUM`)**, correspondientes a la automatización de copias de seguridad, procedimientos de restauración, retención de base de datos, almacenamiento de objetos y matriz RPO/RTO, se desarrollan de forma exhaustiva en el informe complementario:
- [`13_BACKUP_AND_DISASTER_RECOVERY_PLAN.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/audits/PEVN_ENTERPRISE_HARDENING/13_BACKUP_AND_DISASTER_RECOVERY_PLAN.md)
