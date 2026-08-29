# Informe de Auditoría Pre-Implementación — Fase 7 / Paso 4
## Analítica Territorial & Recuperación de Contraseña para Cuentas Activas

**Fecha:** 2026-08-28  
**Estado:** AUDITORÍA PRE-IMPLEMENTACIÓN COMPLETADA (STOP ANTES DE EJECUCIÓN)  
**Alcance:** FASE 7 — PASO 4 (EXCLUSIVAMENTE AUDITORÍA Y PLANIFICACIÓN)  
**Implementación Ejecutada:** FALSE  
**Modificaciones de Código:** 0  
**Modificaciones de Base de Datos:** 0  
**Mutaciones Canónicas:** 0  
**Gobernanza:** `FINAL_DECISION = PRE-IMPLEMENTATION-AUDIT-ONLY` | `PROMOTION_EXECUTED = FALSE` | `IMPLEMENTATION_AUTHORIZATION_REQUIRED = TRUE`  

---

## 1. Estado de la Auditoría (`AUDIT_STATUS`)
- `AUDIT_STATUS = PRE_IMPLEMENTATION_AUDIT_COMPLETE`
- `STEP_4_SCOPE = AUDITED_AND_MAPPED`
- `CODE_MODIFICATIONS_EXECUTED = 0`
- `DATABASE_MODIFICATIONS_EXECUTED = 0`

---

## 2. Alcance del Paso 4 (`STEP_4_SCOPE`)

El Paso 4 comprende exactamente dos capacidades:

### A. Analítica Territorial (`TERRITORIAL_ANALYTICS_SCOPE`)
- Motor analítico jerárquico acotado por `OrganizationalScope` para los niveles:
  - **Nacional (`is_national`)**: Métricas consolidadas del país (Departamentos, Municipios, Establecimientos Educativos Oficiales/Privados, Sedes Urbanas/Rurales, Instituciones Aprovisionadas, Indicadores de Matrícula).
  - **Departamental (`is_department`)**: Métricas acotadas a la Secretaría de Educación Departamental (SED).
  - **Municipal (`is_municipality`)**: Métricas acotadas a la Secretaría de Educación Municipal (SEM).
  - **Institucional (`is_institution`)**: Indicadores agregados del establecimiento y sus sedes.
- Filtrado estricto contra fuga de datos multi-tenant: ninguna consulta departamental o institucional puede extraer datos ajenos a su jurisdicción.
- Reutilización del permiso canónico existente `institutions:read`.

### B. Recuperación de Contraseña para Cuentas Activas (`PASSWORD_RECOVERY_SCOPE`)
- Flujo criptográfico de autoservicio para usuarios activos:
  - Solicitud pública con mitigación de enumeración (respuesta en tiempo y formato constante).
  - Generación de token criptográfico aleatorio seguro (32 bytes / 48 hex), almacenando únicamente su hash SHA-256 en `PasswordResetToken`.
  - Expiración estricta de 1 hora y uso único (`is_used = True`).
  - Validación previa de token antes de renderizar formulario de reseteo.
  - Actualización de contraseña mediante algoritmo robusto Argon2id.
  - Revocación automática de todas las sesiones activas (`RefreshToken`) del usuario.
  - Auditoría inmutable de eventos `user.password_reset.requested` y `user.password_reset.confirmed`.
  - Formularios accesibles en el frontend (`ForgotPassword.tsx`, `ResetPassword.tsx`) con enlace institucional en `Login.tsx`.

---

## 3. Matriz de Archivos a Modificar vs Archivos Protegidos

### Archivos a Crear / Modificar (`FILES_TO_MODIFY`):
1. **Backend Schemas & Service**:
   - `backend/app/schemas/analytics.py` (Nuevo)
   - `backend/app/services/territorial_analytics_service.py` (Nuevo)
   - `backend/app/api/v1/endpoints/analytics.py` (Nuevo)
   - `backend/app/api/v1/endpoints/auth.py` (Modificar — añadir verificación previa de token)
   - `backend/app/api/v1/api.py` (Modificar — registrar router `/analytics`)
2. **Backend Tests**:
   - `backend/tests/test_territorial_analytics.py` (Nuevo)
   - `backend/tests/test_password_recovery.py` (Nuevo)
3. **Frontend Views & Services**:
   - `frontend/src/pages/auth/ForgotPassword.tsx` (Nuevo)
   - `frontend/src/pages/auth/ResetPassword.tsx` (Nuevo)
   - `frontend/src/pages/analytics/TerritorialAnalyticsView.tsx` (Nuevo)
   - `frontend/src/pages/Login.tsx` (Modificar — agregar enlace "¿Olvidó su contraseña?")
   - `frontend/src/services/auth.ts` (Modificar — añadir verificación de token)
   - `frontend/src/services/analytics.ts` (Nuevo)
   - `frontend/src/App.tsx` (Modificar — agregar rutas de recuperación y analítica)
   - `frontend/src/layouts/RootLayout.tsx` (Modificar — enlace de analítica adaptativo)
4. **Frontend Tests**:
   - `frontend/src/test/PasswordRecovery.test.tsx` (Nuevo)
   - `frontend/src/test/TerritorialAnalytics.test.tsx` (Nuevo)

### Archivos Protegidos (`FILES_TO_PROTECT`):
- `backend/app/core/security/authorization.py` (INVIOLABLE)
- `backend/app/core/security/interfaces.py` (INVIOLABLE)
- `backend/app/services/rector_onboarding_service.py` (INVIOLABLE)
- `backend/app/services/guardian_onboarding_service.py` (INVIOLABLE)
- `backend/app/services/national_catalog_controlled_promotion_service.py` (INVIOLABLE)
- Modelos canónicos existentes en `backend/app/models/` (INVIOLABLES)
- Esquemas de Base de Datos y migraciones Alembic (INVIOLABLES)

---

## 4. Requerimientos de Base de Datos y RBAC

- `DATABASE_CHANGES_REQUIRED = NONE (0)`: Las tablas `departments`, `municipalities`, `institutions`, `campuses`, `official_institution_catalog`, `official_campus_catalog` y `password_reset_tokens` contienen toda la estructura requerida.
- `RBAC_CHANGES_REQUIRED = NONE (0)`: Los 9 roles canónicos y permisos canónicos existentes cubren la totalidad de los flujos mediante `institutions:read` y `OrganizationalScope`.

---

## 5. Impacto en Límite de Seguridad y Multi-Tenant

- `SECURITY_BOUNDARY_IMPACT = PRESERVED`: La autorización continúa siendo ejecutada en el backend mediante guardias FastAPI `require_permission` y validación jerárquica de `OrganizationalScope`.
- `TENANT_ISOLATION_IMPACT = PRESERVED`: Los usuarios departamentales e institucionales solo reciben datos que pertenecen a su alcance territorial. Las consultas analíticas aplican cláusulas `where()` basadas en el `AuthorizationContext`.
- `AUDIT_TRAIL_IMPACT = PRESERVED`: Se auditan todos los eventos de recuperación y consultas analíticas de alto nivel de manera inmutable.

---

## 6. Riesgos de Regresión y Plan de Mitigación

| Riesgo de Regresión | Nivel | Estrategia de Mitigación |
| :--- | :---: | :--- |
| Exposición no autorizada de métricas de otra institución | Alto | Pruebas de integración cruzada (cross-tenant tests) en `test_territorial_analytics.py`. |
| Enumeración de usuarios en recuperación de contraseña | Medio | Respuesta genérica idéntica y tiempo constante en `request_password_reset`. |
| Reutilización de token de recuperación | Alto | Marca inmediata `is_used = True` y verificación estricta en transacción `confirm_password_reset`. |
| Regresión en flujos de Paso 1, 2 o 3 | Crítico | Ejecución obligatoria de la suite completa de 294 pruebas backend y pruebas frontend. |

---

## 7. Plan de Pruebas (`TEST_PLAN`)

1. **Backend Tests**:
   - `test_territorial_analytics.py`: Pruebas de agregación nacional, departamental, aislamiento institucional y denegación de acceso cruzado.
   - `test_password_recovery.py`: Pruebas de solicitud, mitigación de enumeración, expiración de token, consumo de token, hashing Argon2id y revocación de sesiones concurrentes.
   - Suite de regresión global: `python -m pytest tests/ -q` (294+ pruebas pasando al 100%).
2. **Frontend Tests**:
   - `npm run typecheck` (`tsc --noEmit`): 0 errores de tipado.
   - `npm test`: Pruebas de Vitest para vistas de recuperación y analítica territorial.
3. **Pruebas de Automatización de Navegador**:
   - **NO EJECUTADAS** (prohibidas por política de gobernanza).

---

## 8. Bloque Final de Métricas y Estado de Gobernanza

```text
AUDIT_STATUS = PRE_IMPLEMENTATION_AUDIT_COMPLETE
STEP_4_SCOPE = TERRITORIAL_ANALYTICS_AND_PASSWORD_RECOVERY
TERRITORIAL_ANALYTICS_SCOPE = VERIFIED_AND_SCOPED
PASSWORD_RECOVERY_SCOPE = VERIFIED_AND_SECURED
FILES_TO_MODIFY = IDENTIFIED
FILES_TO_PROTECT = CONFIRMED
DATABASE_CHANGES_REQUIRED = NONE
RBAC_CHANGES_REQUIRED = NONE
SECURITY_BOUNDARY_IMPACT = PRESERVED
TENANT_ISOLATION_IMPACT = PRESERVED
AUDIT_TRAIL_IMPACT = PRESERVED
REGRESSION_RISK = LOW_CONTROLLED
TEST_PLAN = DOCUMENTED
IMPLEMENTATION_PLAN = DOCUMENTED
IMPLEMENTATION_AUTHORIZATION_REQUIRED = TRUE
FINAL_DECISION = PRE-IMPLEMENTATION-AUDIT-ONLY
PROMOTION_EXECUTED = FALSE
```
