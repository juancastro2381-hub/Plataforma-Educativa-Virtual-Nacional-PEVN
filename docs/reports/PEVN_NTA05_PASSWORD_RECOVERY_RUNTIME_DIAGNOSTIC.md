# PEVN — NTA-05 Password Recovery Runtime Diagnostic Report
**AI Software Factory Standard v1.2**  
**Phase:** NTA-05 Runtime Diagnostic & Root Cause Analysis  
**Classification:** CONTROLLED DIAGNOSTIC REPORT  
**Date:** 2026-10-08  
**Status:** ROOT CAUSE IDENTIFIED

---

## 1. Executive Summary & Objective

During local manual verification, the Password Recovery page at `http://localhost:3000/auth/forgot-password` returned only the generic confirmation notice (*"Instrucciones Enviadas"*) and did **not** display the expected development fallback panel (*"ENLACE DE DESARROLLO"*), even though the automated test suite passed.

This diagnostic investigated the end-to-end runtime behavior across the operating system processes, active network ports, loaded configuration files, backend endpoint branching, and frontend response handlers to determine the exact failure mechanism.

---

## 2. Runtime Environment & Process Discovery

Inspection of active system processes and TCP listening ports:

| Target Port | Process Name | PID | Command Line / CWD |
|:---|:---|:---|:---|
| **8000** | `python.exe` | 23804 | `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` |
| **3000** | `node.exe` | 18372 | `vite.js --port 3000` |
| **5433** | `postgres.exe` | 20840 / 24044 | PostgreSQL 16 (Local `pevn_db`) |
| **6379** | `redis-server.exe` | 20840 / 24044 | Redis (Cache & Rate Limiting) |

Both backend and frontend development servers are actively running and reachable.

---

## 3. Runtime Configuration Inspection

Direct inspection of `get_settings()` within the active Python runtime environment yielded:

```python
ENVIRONMENT:                  Environment.DEVELOPMENT
settings.is_production:       False
settings.is_development:      True
AUTH_PASSWORD_RESET_DEV_LINK: False   # <--- ROOT CAUSE DEFICIENCY
SMTP_HOST:                    None
EMAIL_DELIVERY_ENABLED:       False
FRONTEND_URL:                 "http://localhost:3000"
```

### Analysis of Configuration Sources:
1. `backend/.env`: Present and loaded by Uvicorn. However, `AUTH_PASSWORD_RESET_DEV_LINK` was **not defined** in the file.
2. Root workspace `.env`: Present, but `AUTH_PASSWORD_RESET_DEV_LINK` was also **not defined**.
3. [app/core/config.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py): The field is declared as:
   ```python
   AUTH_PASSWORD_RESET_DEV_LINK: bool = Field(default=False)
   ```
   In accordance with the mandatory security principle of **secure defaults**, the field defaults to `False`.
4. Because the variable was omitted from `.env`, Pydantic assigned `False` to the singleton `Settings` instance.

---

## 4. Live API Endpoint Execution & Captured Response

A direct HTTP POST request was executed against the running backend server on port 8000 for an active database account (`admin@pevn.edu.co`):

```http
POST /api/v1/auth/forgot-password HTTP/1.1
Host: localhost
Content-Type: application/json

{"email": "admin@pevn.edu.co"}
```

### Actual JSON Response Received:
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Si la dirección de correo electrónico se encuentra registrada, se han enviado las instrucciones de recuperación.",
  "development_recovery_url": null,
  "development_recovery_link": null
}
```

The response keys `development_recovery_url` and `development_recovery_link` were present (confirming the running process corresponds to the updated source tree), but both values evaluated to `null`.

---

## 5. Branch Execution Analysis

In [backend/app/api/v1/endpoints/auth.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py#L280-L305):

```python
if raw_token:
    base_url = settings.FRONTEND_URL.rstrip("/")
    reset_url = f"{base_url}/auth/reset-password?token={raw_token}"
    if email_svc.is_configured():
        # Evaluated to FALSE: SMTP_HOST is None
        await email_svc.send_password_reset_email(...)
    elif (
        not settings.is_production                     # TRUE
        and settings.ENVIRONMENT != Environment.PRODUCTION # TRUE
        and settings.is_development                    # TRUE
        and settings.AUTH_PASSWORD_RESET_DEV_LINK      # FALSE!
    ):
        dev_recovery_url = reset_url
```

### Result:
- **Branch C was executed:** `SMTP unavailable + fallback disabled (AUTH_PASSWORD_RESET_DEV_LINK=False)`.
- `dev_recovery_url` remained `None`.

---

## 6. Frontend Execution Analysis

In [frontend/src/pages/auth/ForgotPassword.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/auth/ForgotPassword.tsx#L35-L42):

```typescript
const response = await authApi.requestPasswordReset({ email: email.trim() })
const devUrl =
  response?.development_recovery_url ||
  response?.development_recovery_link ||
  null
setDevRecoveryUrl(devUrl) // Received null
setSubmitted(true)
```

And in JSX:
```tsx
{devRecoveryUrl && (
  <div role="region" aria-label="Enlace de Desarrollo" ...>
    ...
  </div>
)}
```

Because `devRecoveryUrl` was `null`, the frontend conditional block evaluated to false and only rendered the green alert:
> *"Instrucciones Enviadas: Si la dirección de correo electrónico se encuentra registrada y activa, recibirá un enlace seguro con instrucciones para restablecer su contraseña."*

The frontend behaved completely as designed; it did not render the panel because the backend explicitly returned `development_recovery_url: null`.

---

## 7. Root Cause Identification

**Classification:** **Configuration & Environment Synchronization Gap.**

1. **Missing Environment Setting:** `AUTH_PASSWORD_RESET_DEV_LINK=true` was specified in the manual validation documentation, but was never written to `backend/.env` or root `.env`.
2. **Secure Default Enforcement:** The backend correctly initialized `AUTH_PASSWORD_RESET_DEV_LINK=False` by default, satisfying security invariance but failing closed in development.
3. **Uvicorn Reload Scope:** Uvicorn with `--reload` watches Python source files (`.py`), but does not watch `.env` files or invalidate Python's `@lru_cache` for `get_settings()` without a process restart.

---

## 8. Security Impact Assessment

- **Production Security:** **UNAFFECTED.** The fail-closed behavior confirms that in any environment without explicit opt-in, recovery URLs are never exposed.
- **Enumeration Protection:** **UNAFFECTED.** Identical generic messages and HTTP 200 responses are returned.
- **Development Usability:** Degraded in local manual development until the environment configuration is explicitly supplied and loaded.

---

## 9. Recommended Remediation Plan

1. **Populate Environment Configuration:**
   Add `AUTH_PASSWORD_RESET_DEV_LINK=true` to `backend/.env` and root `.env`.
2. **Document in Template:**
   Add `AUTH_PASSWORD_RESET_DEV_LINK=false` to `.env.example` with clear development documentation.
3. **Resilient Env Path Resolution:**
   In [app/core/config.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py), configure `SettingsConfigDict` to look for both `.env` and `backend/.env` so configuration is loaded irrespective of launch CWD.
4. **Restart Backend Dev Server:**
   Restart Uvicorn process so that `get_settings()` cache and environment variables are cleanly loaded with `AUTH_PASSWORD_RESET_DEV_LINK=true`.
5. **End-to-End Validation:**
   Verify against the live running API on port 8000 and through Vite proxy on port 3000.
