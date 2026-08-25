# Plataforma Educativa Virtual Nacional (PEVN)
## Guía de Arquitectura de Autenticación (Fase 2)

---

### 1. Resumen Ejecutivo y Principios de Diseño

El sistema de autenticación de PEVN ha sido diseñado bajo los principios de **Seguridad por Diseño (Security by Design)**, **Defensa en Profundidad** y **Privacidad por Diseño (Privacy by Design)** para operar a escala gubernamental en instituciones educativas de Colombia.

Principales políticas implementadas:
- **Cero persistencia de tokens de acceso en el navegador**: Los tokens JWT de acceso residen única y exclusivamente en la memoria volátil de JavaScript (`React in-memory state`). No se almacenan en `localStorage`, `sessionStorage`, `IndexedDB` ni `WebSQL`.
- **Entrega de Refresh Tokens vía HttpOnly Cookie**: Los refresh tokens se transmiten en cookies marcadas con `HttpOnly`, `SameSite=Strict`, `Path=/api/v1/auth`, `Secure` (en producción) y un ciclo de vida de 7 días.
- **Hashing de Contraseñas de Grado Gubernamental (Argon2id)**: Implementación de Argon2id (RFC 9106) con coste de memoria de 64 MB (65,536 KiB), 3 iteraciones de tiempo, paralelismo de 4 hilos y salting criptográfico aleatorio único por registro de 16 bytes.
- **Rotación de Refresh Tokens con Detección de Replay/Breach**: Cada invocación del endpoint de refresco emite un nuevo refresh token y marca el anterior con `replaced_by_token_id`. Si se detecta un intento de reutilización de un token reemplazado o revocado, el sistema invalida automáticamente toda la familia de tokens (`family_id`), registra un evento de auditoría crítico de seguridad (`token.reuse.detected`) y bloquea la sesión inmediatamente.
- **Protección contra Fuerza Bruta Progresiva**: Bloqueo temporal automático de la cuenta por 15 minutos tras 5 intentos fallidos consecutivos de inicio de sesión (`user.account.locked`).
- **Recuperación de Contraseña de Uso Único**: Flujo de restablecimiento mediante tokens criptográficos de un solo uso con caducidad estricta de 1 hora y revocación masiva de sesiones activas tras confirmación.

---

### 2. Endpoints de la API de Autenticación

Todos los endpoints se encuentran expuestos bajo el prefijo `/api/v1/auth`:

| Método | Endpoint | Descripción | Autenticación Requerida |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Autentica credenciales y emite access token (JSON) y refresh token (`HttpOnly` cookie). | Pública (Rate Limited) |
| `POST` | `/api/v1/auth/refresh` | Rota refresh token usando la cookie `pevn_refresh_token` y emite nuevo access token. | Cookie HttpOnly |
| `POST` | `/api/v1/auth/logout` | Revoca la familia del refresh token y limpia la cookie de sesión. | Opcional (Bearer / Cookie) |
| `GET` | `/api/v1/auth/me` | Retorna el perfil autenticado, roles, permisos y contexto territorial del usuario. | Bearer JWT |
| `POST` | `/api/v1/auth/password/change` | Actualiza la contraseña del usuario validando la contraseña actual e invalida sesiones activas. | Bearer JWT |
| `POST` | `/api/v1/auth/password/reset/request` | Inicia recuperación de contraseña (anti-enumeración de usuarios). | Pública (Rate Limited) |
| `POST` | `/api/v1/auth/password/reset/confirm` | Restablece la contraseña usando el token criptográfico de un solo uso. | Pública (Rate Limited) |

---

### 3. Estructura del JWT Access Token

El token de acceso es un JSON Web Token firmado mediante el algoritmo criptográfico `HS256` (HMAC con SHA-256) utilizando la clave secreta `JWT_SECRET_KEY` configurada en el servidor.

**Claims del Payload:**
```json
{
  "sub": "c6b2552e-a133-4d2b-8af9-432c977691d9",
  "username": "profesor_nacional",
  "token_type": "access",
  "roles": ["teacher"],
  "institution_id": "89012345-0000-0000-0000-000000000001",
  "jti": "5a27f8dc-304b-4c07-b24c-e87f87bf3a94",
  "iat": 1787409200,
  "exp": 1787410100
}
```

- `sub`: UUID del usuario.
- `token_type`: `'access'` estricto (rechaza tokens de refresco o recuperación en validadores de acceso).
- `roles`: Lista de roles activos asignados al usuario.
- `institution_id`: Identificador institucional para validación rápida de contexto multi-inquilino.
- `jti`: Identificador único de token para trazabilidad y correlación.
- `exp`: Tiempo de expiración estricto de 15 minutos (900 segundos).

---

### 4. Ciclo de Vida del Refresh Token y Replay Breach Detection

```
Cliente                           Backend                         Base de Datos
   |                                 |                                  |
   |--- POST /auth/login ----------->| (Verifica Argon2id)              |
   |                                 |--- Guarda RefreshToken_1 (Fam A) >|
   |<-- Set-Cookie: pevn_refresh_1 --|                                  |
   |<-- JSON: { access_token_1 } ----|                                  |
   |                                 |                                  |
   | (15 minutos después)            |                                  |
   |--- POST /auth/refresh --------->|                                  |
   |    Cookie: pevn_refresh_1       |--- Consulta RefreshToken_1 ----->|
   |                                 |    Token válido y activo         |
   |                                 |--- Crea RefreshToken_2 (Fam A) ->|
   |                                 |--- Marca Token_1.replaced_by=2 ->|
   |<-- Set-Cookie: pevn_refresh_2 --|                                  |
   |<-- JSON: { access_token_2 } ----|                                  |
   |                                 |                                  |
   | [ESCENARIO DE ATAQUE: REPLAY]   |                                  |
   | Atacante envía pevn_refresh_1 ->|                                  |
   |                                 |--- Consulta RefreshToken_1 ----->|
   |                                 |    DETECTA replaced_by_token_id! |
   |                                 |--- REVOCA TODA LA FAMILIA A ---->|
   |                                 |--- Registra TOKEN_REUSE_DETECTED>|
   |<-- 401 Sesión comprometida -----|                                  |
```

---

### 5. Creación Segura de SuperAdmin (CLI)

En cumplimiento de las condiciones de seguridad gubernamental, **no se permite sembrar contraseñas estáticas ni hardcodeadas** en migraciones o código fuente.

Para inicializar la cuenta administrativa de primer nivel:

```bash
# Modo interactivo (oculta la contraseña en terminal mediante getpass):
python -m app.cli.create_superadmin --username admin_nacional --email admin@pevn.edu.co

# O mediante variables de entorno seguras en pipelines CI/CD:
SUPERADMIN_EMAIL="admin@pevn.edu.co" \
SUPERADMIN_USERNAME="admin_nacional" \
SUPERADMIN_PASSWORD="MiPasswordSuperSegura2026!" \
python -m app.cli.create_superadmin
```
