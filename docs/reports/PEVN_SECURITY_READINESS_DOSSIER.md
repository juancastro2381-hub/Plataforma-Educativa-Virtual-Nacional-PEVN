# PEVN — DOSSIER FORENSE DE PREPARACIÓN EN CIBERSEGURIDAD
## EVALUACIÓN DE CONTROLES, POSTURA DEFENSIVA, MITIGACIÓN OWASP Y BLINDAJE MULTI-TENANT (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Documento:** Dossier de Auditoría Forense de Seguridad de la Información  
**Marco de Referencia:** OWASP ASVS v4.0, NIST SP 800-63B, ISO/IEC 27001, Ley 1581 de 2012  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Security Evidence  

---

## 1. Declaración de Filosofía Defensiva y Principios de Diseño

La Plataforma Educativa Virtual Nacional (PEVN) procesa datos sensibles de carácter personal, académico y disciplinario pertenecientes a **niñas, niños, adolescentes, docentes y directivos del sector educativo público colombiano**. 

En concordancia con lo anterior, la arquitectura de seguridad se rige bajo los siguientes principios innegociables:
1. **Seguridad por Diseño y por Defecto (*Security by Design & Default*):** Toda funcionalidad nace restringida y requiere privilegios explícitos para operar.
2. **Defensa en Profundidad (*Defense in Depth*):** Se disponen capas defensivas concéntricas e independientes (Cabeceras HTTP $\rightarrow$ Validación de Entrada Pydantic $\rightarrow$ Autenticación JWT $\rightarrow$ RBAC Granular $\rightarrow$ Aislamiento Multi-Tenant $\rightarrow$ Anti-IDOR Blind 404 $\rightarrow$ Consultas Parametrizadas ORM $\rightarrow$ Auditoría Inmutable).
3. **Privacidad por Diseño (*Privacy by Design*):** Cero exposición de información identificable innecesaria, censura automática en logs y separación estricta de expedientes familiares.
4. **Principio de Mínimo Privilegio (*Least Privilege*):** Tanto usuarios de la aplicación como procesos del sistema operativo y usuarios de base de datos operan con el conjunto más restrictivo de permisos técnicos requeridos para su función.

---

## 2. Inventario Forense de Controles de Seguridad

A continuación se evalúa cada control de seguridad, clasificándolo en una de las tres categorías autorizadas:
- `IMPLEMENTED & EVIDENCED` (Implementado y con evidencia en pruebas/código).
- `REQUIRES VALIDATION` (Implementado pero sujeto a pruebas de penetración o auditoría externa).
- `REQUIRES INFRASTRUCTURE / INSTITUTIONAL POLICY` (Depende de hardware, certificados o directrices institucionales).

---

### 2.1 Autenticación y Criptografía de Credenciales
- **Algoritmo de Hashing:** Argon2id conforme a RFC 9106.
  - Coste de memoria: 64 MB (65,536 KiB).
  - Iteraciones en el tiempo: 3.
  - Hilos en paralelo: 4.
  - Salting: 16 bytes criptográficamente seguros generados por `os.urandom()` por cada contraseña.
  - Detección de rehash: Algoritmo verifica si los parámetros del hash han cambiado para actualizarlo automáticamente en el siguiente inicio de sesión exitoso.
- **Evidencia Técnica:** `backend/app/core/security/password.py`, suite de pruebas en `backend/tests/test_password_hasher.py` (6 pruebas PASSED).
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.2 Gestión de Tokens de Acceso (JWT) y Ciclo de Vida en Memoria
- **Algoritmo de Firma:** HMAC con SHA-256 (`HS256`) utilizando una clave secreta simétrica robusta (`JWT_SECRET_KEY`).
- **Tiempo de Expiración:** 15 minutos (900 segundos).
- **Claims Requeridos:** `sub` (UUID usuario), `roles` (lista de roles canónicos), `institution_id` (UUID de contexto institucional), `jti` (identificador único de token), `iat` (emisión), `exp` (expiración).
- **Manejo Seguro en Cliente Frontend:** Los tokens JWT de acceso residen única y exclusivamente en la **memoria volátil de JavaScript** (React State en `AuthContext.tsx`).
  - **CERO PERSISTENCIA:** No se almacena ningún token en `localStorage`, `sessionStorage`, `IndexedDB`, cookies accesibles por script ni variables globales de `window`.
  - Esta práctica mitiga al 100% el robo persistente de credenciales mediante ataques de Cross-Site Scripting (XSS).
- **Evidencia Técnica:** `backend/app/core/security/tokens.py`, `frontend/src/context/AuthContext.tsx`, `backend/tests/test_tokens.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.3 Tokens de Refresco (Refresh Tokens), Cookies y Detección de Replay
- **Almacenamiento en Servidor:** Los refresh tokens no se guardan en texto plano en la base de datos; se almacena estrictamente su hash SHA-256 (`token_hash`) en la tabla `refresh_tokens`.
- **Transporte Seguro:** Entregados al navegador mediante una cookie HTTP con directivas de máxima restricción:
  - `HttpOnly = True`: Inaccesible para código JavaScript del navegador.
  - `SameSite = Strict`: Previene el envío de la cookie en peticiones cross-site, neutralizando ataques CSRF en navegación ordinaria.
  - `Path = /api/v1/auth`: La cookie solo se transmite hacia los endpoints de autenticación, protegiendo el resto de rutas.
  - `Secure = True`: Obligatorio en entornos no locales para exigir cifrado TLS en tránsito.
  - Vigencia: 7 días.
- **Mecanismo de Detección de Brecha / Replay (*Token Family Rotation*):**
  - Cada vez que se invoca `/api/v1/auth/refresh`, el token actual se marca con `replaced_by_token_id` y se emite un nuevo token hijo dentro de la misma `family_id`.
  - Si un atacante intercepta un token de refresco antiguo e intenta usarlo, el backend detecta que dicho token ya tiene sucesor (`replaced_by_token_id is not None`).
  - **Acción Inmediata:** Se revoca de manera transaccional **toda la familia de tokens asociada** (`family_id`), desconectando inmediatamente tanto al atacante como a la víctima, se bloquea la sesión y se emite un evento de auditoría de severidad crítica (`token.reuse.detected`).
- **Evidencia Técnica:** `backend/app/services/auth_service.py`, `backend/tests/test_auth_service.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.4 Control de Acceso Basado en Roles (RBAC) y Jerarquía Anti-Escalamiento
- **Sintaxis de Permisos:** Formato granular `recurso:accion` (ej. `students:read`, `grades:create`, `evaluations:unlock_period`).
- **Comodines Soportados:** `*` (acceso irrestricto de SuperAdmin), `users:*` (todas las acciones sobre usuarios), `*:read` (lectura universal).
- **Niveles Numéricos de Seguridad (10 a 100):**
  - `superadmin`: 100
  - `national_admin`: 90
  - `territorial_leader`: 80
  - `institution_admin` (Rector): 70
  - `coordinator`: 60
  - `teacher`: 50
  - `student`: 20
  - `guardian`: 10
- **Prevención de Escalamiento Vertical:** Un usuario con nivel $N$ tiene prohibido crear, modificar o asignar cuentas con nivel de rol $\ge N$.
- **Evidencia Técnica:** `backend/app/services/authorization_service.py`, `backend/tests/test_authorization.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.5 Aislamiento Multi-Inquilino (Multi-Tenancy) y Frontera Territorial DANE
- **Particionamiento Lógico de Datos:** Toda entidad de negocio está anclada a un `institution_id`. Las dependencias FastAPI inyectan el contexto institucional obligatorio extraído de los claims criptográficos del JWT, no de parámetros modificables por el cliente.
- **Jerarquía Territorial DANE:** La función `scope_contains()` valida matemáticamente que un usuario pertenezca a la misma institución o tenga jurisdicción territorial superior (Nacional o Departamental) sobre el recurso consultado.
- **Evidencia Técnica:** `backend/app/core/security/interfaces.py`, `backend/tests/test_authorization.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.6 Protección Anti-IDOR y Mecanismo "Blind 404"
- **Vulnerabilidad Prevenida:** Insecure Direct Object References (IDOR). En sistemas tradicionales, si un usuario intenta acceder a `/students/{uuid_ajeno}`, el servidor responde `403 Forbidden`, confirmando al atacante que el identificador existe en el sistema.
- **Blind 404 (404 Ciego):** En PEVN, las consultas en la base de datos incluyen como cláusula `WHERE` tanto el ID del recurso como el `institution_id` del usuario (o la validación de vínculo familiar activo en el portal de acudientes). Si el recurso pertenece a otro colegio o no existe relación parental, la consulta no retorna filas y el servicio lanza `ResourceNotFoundError`, devolviendo al atacante un **`404 Not Found` indistinguible de un identificador inexistente**.
- **Evidencia Técnica:** `backend/app/services/student_portal_service.py`, `backend/app/services/guardian_portal_service.py`, `backend/tests/test_teacher_academic_scope.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.7 Prevención de Ataques de Fuerza Bruta y Ciclo de Vida de Cuentas
- **Bloqueo Progresivo:** Al registrarse 5 intentos fallidos consecutivos de autenticación para una misma cuenta, el campo `failed_login_attempts` dispara el bloqueo temporal de la cuenta por 15 minutos (`is_locked_until = now() + 15 min`).
- **Reseteo Seguro de Contraseña:** Flujo de recuperación mediante tokens criptográficos de alta entropía (256 bits) con vigencia de 1 hora. Al consumirse el token o cambiarse la contraseña, el sistema invalida inmediatamente todas las sesiones y refresh tokens activos del usuario.
- **Revocación Forzosa de Sesiones en Desactivación:** Cuando un directivo desactiva la cuenta de un docente, estudiante o acudiente (`/account/status`), los identificadores de token (JTI) se agregan a la lista de revocación inmediata, impidiendo el uso residual de tokens de acceso vigentes.
- **Evidencia Técnica:** `backend/app/services/auth_service.py`, `backend/tests/test_auth_service.py`, `test_identity_family_lifecycle.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.8 Seguridad en Almacenamiento y Carga de Archivos (Upload Security)
- **Validación de Tipo MIME y Magic Bytes:** La inspección de archivos no confía en la extensión provista por el cliente (`.pdf`). El servicio `FileStorageService` analiza los primeros bytes binarios del archivo (*Magic Bytes*) para confirmar la naturaleza del documento y rechazar archivos ejecutables camuflados (`.exe`, `.elf`, `.bat`, `.ps1`, `.sh`).
- **Restricción de Tamaño:** Límite inflexible de 10 MB por archivo adjunto (máximo 3 archivos por entrega en tareas escolares).
- **Aislamiento de Ruta y Mitigación de Path Traversal:** Los nombres de archivo se reemplazan por identificadores UUID aleatorios en el disco del servidor, almacenándose en rutas estructuradas por `institution_id`. Se valida canónicamente la ruta resultante con respecto a la raíz de almacenamiento permitida.
- **Evidencia Técnica:** `backend/app/core/storage/service.py`, `backend/tests/test_activity_resources_and_storage.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.9 Protección contra Inyección SQL y Validación de Entrada
- **Consultas Parametrizadas:** La interacción con PostgreSQL se efectúa mediante SQLAlchemy 2.0 ORM. Cero concatenación de cadenas SQL en el código de producción.
- **Validación de Esquemas:** Todos los cuerpos de petición HTTP (JSON) se deserializan y validan estrictamente mediante modelos Pydantic v2 con tipado fuerte, límites de longitud y expresiones regulares. Peticiones malformadas son rechazadas en el perímetro por FastAPI con `HTTP 422 Unprocessable Entity`.
- **Evidencia Técnica:** Modelos Pydantic en `backend/app/schemas/`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.10 Cabeceras HTTP de Seguridad (Security Headers Middleware)
Todas las respuestas emitidas por la API incorporan obligatoriamente las siguientes cabeceras gestionadas por `SecurityHeadersMiddleware`:
- `X-Content-Type-Options: nosniff` (Previene ataques de adivinación de tipo MIME).
- `X-Frame-Options: DENY` (Mitiga ataques de Clickjacking impidiendo embeber la plataforma en iframes).
- `Referrer-Policy: strict-origin-when-cross-origin` (Protege de fugas de URLs con parámetros internos).
- `Cross-Origin-Opener-Policy: same-origin` (Mitiga ataques de canales laterales como Spectre).
- `Cross-Origin-Resource-Policy: same-origin` (Protege contra lecturas cruzadas de recursos).
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (En entornos staging/producción).
- `X-XSS-Protection: 0` (Desactiva filtros heredados inseguros del navegador).
- `Content-Security-Policy`: Restringida según entorno.
- **Evidencia Técnica:** `backend/app/middleware/security_headers.py`, `backend/tests/test_health.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.11 CORS y Validación de Host Confiable (Trusted Host)
- **CORS Estricto:** La lista de orígenes permitidos (`CORS_ORIGINS`) se configura explícitamente desde variables de entorno. En modo producción, la presencia de comodines (`*`) o esquemas inseguros (`http://`) provoca la detención inmediata del servidor durante el arranque (*startup validation fail-fast*).
- **Trusted Host Middleware:** Valida la cabecera `Host` HTTP contra una lista blanca para evitar ataques de inyección de Host y envenenamiento de enlaces de reseteo.
- **Evidencia Técnica:** `backend/app/core/config.py`, `backend/tests/test_config.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.12 Auditoría Inmutable y Censura de Secretos (Zero Leakage)
- **Tabla Inmutable:** Registro persistente en `audit_logs` con estampa `clock_timestamp()` tomada directamente del reloj del motor de base de datos.
- **Sanitización Recursiva:** Antes de almacenar el JSON de metadatos de cualquier evento, la función `sanitize_audit_metadata()` censura de manera determinística cualquier clave que contenga contraseñas, tokens JWT, secretos, sales o cookies, sustituyéndolos por la constante `[REDACTED]`.
- **Enmascaramiento de Documentos:** Documentos de identidad de estudiantes y docentes son enmascarados parcialmente en registros de eventos estándar.
- **Evidencia Técnica:** `backend/app/audit/database_service.py`, `backend/tests/test_auth_service.py`.
- **Clasificación:** `IMPLEMENTED & EVIDENCED`.

---

### 2.13 Gestión de Secretos del Sistema
- **Estado Actual en Desarrollo:** Variables almacenadas en archivo `.env` local. El archivo `.gitignore` excluye estrictamente cualquier archivo de entorno real (`.env`, `.env.local`, `.env.production`).
- **Verificación en Arranque:** La clase `Settings` de Pydantic verifica que `JWT_SECRET_KEY` tenga una longitud mínima de 32 caracteres y que no contenga valores por defecto o palabras clave débiles en producción.
- **Requerimiento para Producción Gubernamental:** `REQUIRES INFRASTRUCTURE / INSTITUTIONAL POLICY` — Integración obligatoria con un gestor de secretos de grado gubernamental (HashiCorp Vault o AWS/GCP Secrets Manager) para la inyección dinámica de secretos sin archivos en disco.

---

## 3. Matriz de Cumplimiento OWASP Top 10 (2021)

| Vulnerabilidad OWASP | Riesgo para PEVN | Controles Implementados en PEVN | Nivel de Mitigación |
| :--- | :--- | :--- | :---: |
| **A01: Broken Access Control** | Acceso cruzado entre colegios o entre familias | RBAC por niveles, aislamiento por `institution_id`, regla de contención territorial y Blind 404. | **ALTO (100% CUBIERTO)** |
| **A02: Cryptographic Failures** | Robo o descifrado de contraseñas de docentes/estudiantes | Hashing Argon2id (64 MB), JWT efímero en memoria volátil, tokens de refresco almacenados como SHA-256. | **ALTO (100% CUBIERTO)** |
| **A03: Injection** | Inyección SQL en notas o matrículas | Consultas 100% parametrizadas vía SQLAlchemy 2.0 ORM, cero sentencias SQL concatenadas a mano. | **ALTO (100% CUBIERTO)** |
| **A04: Insecure Design** | Manipulación de notas en períodos cerrados o suplantación | Inmutabilidad de notas al cerrar período (`is_locked`), tope de nivelación forzado en código y auditoría. | **ALTO (100% CUBIERTO)** |
| **A05: Security Misconfiguration** | Cors permisivo o mensajes de error con trazas internas | Fail-fast en startup si CORS tiene `*`, cabeceras HTTP restrictivas, error handlers sanitizados sin stack trace. | **ALTO (100% CUBIERTO)** |
| **A06: Vulnerable & Outdated Components** | Dependencias de terceros con CVEs | Python 3.12, FastAPI 0.110+, React 18, Vite 6, dependencias auditadas sin vulnerabilidades críticas. | **ALTO (100% CUBIERTO)** |
| **A07: Identification & Auth Failures** | Ataques de fuerza bruta y robo de sesión | Bloqueo tras 5 fallos, rotación de refresh tokens con detección de replay (anulación de familia de tokens). | **ALTO (100% CUBIERTO)** |
| **A08: Software & Data Integrity Failures** | Ingesta de ejecutables maliciosos o firmas BBB falsas | Detección de Magic Bytes en archivos, cálculo estricto de checksums SHA-1/256 en BigBlueButton. | **ALTO (100% CUBIERTO)** |
| **A09: Security Logging & Monitoring Failures** | Acciones críticas sin evidencia forense | Tabla `audit_logs` inmutable, correlación UUID en todas las peticiones, censura automática `[REDACTED]`. | **ALTO (100% CUBIERTO)** |
| **A10: Server-Side Request Forgery (SSRF)** | Peticiones maliciosas hacia la red interna o BBB | Adaptador BBB valida endpoints y restringe URLs a destinos configurados en variables de entorno. | **MEDIO / ALTO** |

---

## 4. Controles Pendientes de Validación y Despliegue de Infraestructura

1. **Pruebas de Penetración de Caja Negra / Ética (*Ethical Hacking*):**
   - Se requiere la ejecución formal de un ejercicio de *Penetration Testing* externo ejecutado por un equipo especializado independiente antes de la salida en vivo a nivel nacional.
2. **Web Application Firewall (WAF) y Mitigación DDoS:**
   - Debe desplegarse un WAF gubernamental (Cloudflare Gov, AWS WAF o ModSecurity) frente al proxy inverso para mitigar ataques volumétricos de denegación de servicio distribuido (DDoS) y filtrado de bots.
3. **Cifrado en Reposo de Base de Datos y Almacenamiento:**
   - La base de datos PostgreSQL debe desplegarse sobre volúmenes cifrados mediante algoritmos XTS-AES-256 (LUKS / EBS Encrypted) y la capa de almacenamiento S3 debe exigir políticas de `SSE-S3` o `SSE-KMS`.
4. **Política Institucional de Gestión de Vulnerabilidades:**
   - Definición de los acuerdos de nivel de servicio (SLA) para la aplicación de parches de seguridad críticos en menos de 24-48 horas.
