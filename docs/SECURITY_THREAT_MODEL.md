# Plataforma Educativa Virtual Nacional (PEVN)
## Modelo de Amenazas de Seguridad (STRIDE) — Fase 2 (Identidad, Autenticación y Autorización)

---

### 1. Metodología de Análisis

El modelo de amenazas de Fase 2 utiliza la taxonomía **STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) para identificar vectores de ataque contra el sistema de identidad y definir controles de mitigación arquitectónicos.

---

### 2. Matriz de Amenazas y Mitigaciones STRIDE

| Categoría STRIDE | Vector de Amenaza Identificado | Severidad | Mitigación Arquitectónica Implementada en Fase 2 |
| :--- | :--- | :---: | :--- |
| **S** - *Spoofing* (Suplantación) | Robo de JWT Access Token mediante scripts XSS maliciosos en el navegador. | ALTA | **Zero-Storage en Cliente**: El Access Token vive únicamente en memoria de React (`in-memory state`). No existe en `localStorage` ni `IndexedDB`. El Refresh Token vive en cookie `HttpOnly`, `SameSite=Strict`. |
| **S** - *Spoofing* (Suplantación) | Robo e interceptación de Refresh Token para mantener sesiones permanentes. | CRÍTICA | **Rotación Forzada + Detección de Replay**: Cada refresco genera un nuevo token. Si un token usado se vuelve a presentar, el sistema revoca inmediatamente toda la familia de tokens (`token.reuse.detected`). |
| **T** - *Tampering* (Manipulación) | Modificación de claims de roles o ID de institución en el payload del JWT. | ALTA | **Firma Criptográfica HS256**: Los tokens son firmados con clave secreta de alta entropía. La manipulación del payload invalida la firma criptográfica (`tampered_token_rejected`). |
| **R** - *Repudiation* (Repudio) | Usuario o administrador niega haber modificado credenciales, cerrado sesiones o consultado registros. | MEDIA | **Auditoría Persistente Inmutable**: Tabla `audit_logs` con `actor_id`, `actor_ip`, `actor_user_agent`, `correlation_id` y marcas de tiempo `TIMESTAMPTZ` de alta precisión. |
| **I** - *Information Disclosure* (Divulgación) | Filtración de contraseñas por volcado de base de datos o exposición en logs. | CRÍTICA | **Argon2id + Sanitización de Logs**: Contraseñas hasheadas con Argon2id (64 MB, 3 iteraciones, salting aleatorio único). `sanitize_audit_metadata` censura automáticamente cualquier campo sensible antes de guardar o loguear. |
| **I** - *Information Disclosure* (Divulgación) | Enumeración de cuentas de correo mediante respuestas diferenciadas en restablecimiento de contraseña. | MEDIA | **Anti-Enumeración Uniforme**: El endpoint `POST /password/reset/request` siempre retorna respuesta exitosa genérica sin revelar si el correo existe o no en la base de datos. |
| **D** - *Denial of Service* (Denegación) | Ataques de fuerza bruta contra contraseñas o endpoints de login. | ALTA | **Bloqueo Progresivo de Cuentas**: Bloqueo temporal por 15 minutos al acumular 5 intentos fallidos consecutivos (`user.account.locked`), combinado con rate limiting por IP. |
| **E** - *Elevation of Privilege* (Escalamiento) | Acceso de un docente o directivo a la información de otra institución educativa (cross-tenant breach). | CRÍTICA | **Aislamiento Organizacional Jerárquico**: `CentralizedAuthorizationService` valida `scope_contains(actor_scope, target_scope)`. Intentos cross-tenant son rechazados con `403 Forbidden` (`PERMISSION_DENIED`). |
| **E** - *Elevation of Privilege* (Escalamiento) | Creación o asignación de roles superiores (ej. docente asignándose rol rector o superadmin). | CRÍTICA | **Jerarquía Numérica de Roles**: Cada rol tiene un `level` estricto (10 a 100). Ningún usuario puede asignar roles con nivel igual o superior al suyo. |

---

### 3. Conclusión y Estado de Mitigación

Todas las amenazas de severidad Alta y Crítica identificadas en el modelo STRIDE para la Fase 2 cuentan con mitigaciones activas y verificadas mediante pruebas automatizadas unitarias y de integración.
