# PEVN — NTA-09-R2: INFORME DE ENDURECIMIENTO DE INVITACIÓN, ACTIVACIÓN Y CICLO DE VIDA DE CREDENCIALES DE ADMINISTRADORES MUNICIPALES

**Estándar:** AI Software Factory Standard v1.2  
**Módulo / Hito:** NTA-09-R2 (`MUNICIPALITY_ADMIN` Provisioning Hardening)  
**Fecha de Ejecución:** 2026-10-09  
**Agente Responsable:** Antigravity  
**Estado:** **CONDITIONAL PASS — MANUAL VALIDATION REQUIRED**  
**Control de Versiones:** Sin commits ni pushes en Git. Árbol de trabajo y modificaciones no relacionadas estrictamente preservadas.

---

## 1. Causa Raíz y Evidencia Observada

### 1.1 Causa Raíz
Durante las pruebas de aceptación manual de NTA-09-R1, el formulario de aprovisionamiento en `/admin/municipality-admins`:
1. Aceptaba un campo `password` opcional definido por el operador administrativo.
2. Si se suministraba o por defecto, la cuenta se creaba directamente activa (`is_active=True`, `is_verified=True`).
3. Esto permitía eludir el flujo institucional de activación y definición autónoma de credenciales por parte del usuario invitado.
4. En ausencia de un servidor SMTP configurado en el entorno de desarrollo, el sistema dependía de contraseñas asignadas manualmente por el operador o de activaciones inmediatas.

### 1.2 Evidencia Forense
- **Esquema Pydantic legacy:** `MunicipalityAdminCreateRequest` exponía `password: str | None = None` y `is_active: bool = True`.
- **Frontend legacy:** `MunicipalityAdminsView.tsx` renderizaba un campo `Contraseña inicial (opcional)` con valor predeterminado y permitía enviar la contraseña en el cuerpo JSON de `POST /api/v1/municipality-admins`.
- **Base de Datos:** Se detectó la creación de la cuenta de prueba `Admin_municipio_Juan` (`CC 123456`, `juanprb@colegio.edu.co`) con una contraseña asignada por el operador, activa de forma inmediata.

---

## 2. Arquitectura de Invitación Existente Reutilizada

Para cumplir el principio de reutilización y coherencia arquitectónica de PEVN, se inspeccionaron los componentes existentes de onboarding e invitación:
- **Modelo de Invitación Departamental (`DepartmentAdminInvitation`):** Almacenamiento seguro mediante hash SHA-256 del token, expiración configurable (48 horas), un solo uso atómico (`is_used`), revocación explícita (`is_revoked`) y vinculación territorial foreign-key a la entidad jurisdiccional.
- **Servicio de Despacho de Correo (`EmailService`):** Detección automática del estado SMTP (`EMAIL_NOT_CONFIGURED`, `EMAIL_SENT`, `EMAIL_SEND_FAILED`) sin exponer secretos ni registrar tokens en texto claro.
- **Endpoints Públicos de Canje (`/api/v1/auth/verify-invitation` y `/api/v1/auth/accept-invitation`):**
  - Validación con enmascaramiento de identidad (`_mask_email`).
  - Hashing de contraseñas exclusivamente con Argon2id.
  - Activación atómica con revocación en cascada de tokens previos.

### 2.1 Extensión Canónica para Administradores Municipales
Se replicó con precisión el patrón arquitectónico sin crear sistemas paralelos:
- **Migración 031 (`031_municipality_admin_invitations`):** Tabla `municipality_admin_invitations` vinculada a `municipality_id` y `user_id`, con índices únicos sobre `token_hash`.
- **Modelo `MunicipalityAdminInvitation`:** Entidad SQLAlchemy que hereda de `Base` e implementa `is_expired`, `token_hash`, `invited_by_id`, `expires_at`, `used_at`, `revoked_at`.
- **Delegación en Auth Controller:** Los endpoints `/verify-invitation` y `/accept-invitation` delegan en `MunicipalityAdminService` cuando el token pertenece a un administrador municipal.

---

## 3. Archivos Modificados y Propósito de Cada Cambio

| Archivo | Propósito del Cambio |
| :--- | :--- |
| `backend/migrations/versions/031_municipality_admin_invitations.py` | Migración Alembic para la tabla física `municipality_admin_invitations` con llaves foráneas a `municipalities` y `users`. |
| `backend/app/models/invitation.py` | Modelo de dominio `MunicipalityAdminInvitation` con propiedades de vigencia y relaciones SQLAlchemy. |
| `backend/app/models/__init__.py` | Exportación canónica del modelo `MunicipalityAdminInvitation`. |
| `backend/app/audit/interfaces.py` | Definición de nuevos tipos de eventos de auditoría: `MUNICIPALITY_ADMIN_INVITED`, `MUNICIPALITY_ADMIN_INVITATION_SENT`, `MUNICIPALITY_ADMIN_ONBOARDING_COMPLETED`, `MUNICIPALITY_ADMIN_INVITATION_RESENT`, `MUNICIPALITY_ADMIN_REMEDIATED`. |
| `backend/app/schemas/municipality_admin.py` | Eliminación de `password` e `is_active` de `MunicipalityAdminCreateRequest` con `extra = "forbid"`. Nuevos esquemas de respuesta para invitación. |
| `backend/app/schemas/invitation.py` | Soporte de metadatos municipales (`municipality_name`, `municipality_code`) en `VerifyInvitationResponse`. |
| `backend/app/services/municipality_admin_service.py` | Implementación del ciclo de vida seguro: creación inactiva/no verificada con dummy hash, generación de token de 48 bytes URL-safe con hash SHA-256, canje atómico con `with_for_update`, bloqueo de activación manual de cuentas pendientes, invalidación en deactivación/reasignación, y método de remediación. |
| `backend/app/api/v1/endpoints/auth.py` | Integración de `MunicipalityAdminService.verify_invitation` y `accept_invitation` en el flujo público de onboarding. |
| `backend/app/api/v1/endpoints/municipality_admins.py` | Endpoint `POST /{user_id}/resend-invitation` protegido por RBAC y alcance territorial. |
| `frontend/src/types/municipalityAdmin.ts` | Eliminación de `password` e `is_active` del contrato TypeScript de creación; adición de campos de invitación. |
| `frontend/src/types/institution.ts` | Soporte de atributos municipales en la respuesta de verificación. |
| `frontend/src/services/municipalityAdmin.ts` | Método cliente `resendInvitation(userId)`. |
| `frontend/src/pages/admin/MunicipalityAdminsView.tsx` | Eliminación de inputs de contraseña; banner informativo de activación segura; modal de resultado con mensaje explícito sobre SMTP y enlace de un solo uso en desarrollo; acción de "Regenerar invitación". |
| `frontend/src/pages/auth/AcceptInvitation.tsx` | Adaptación de la pantalla pública de onboarding para el rol `municipality_admin` con identificación territorial DIVIPOLA. |
| `backend/tests/test_nta09_municipality_admin_provisioning.py` | Suite exhaustiva de 22 pruebas que validan los 15 escenarios de seguridad requeridos. |

---

## 4. Resultado Exacto de la Remediación de la Cuenta de Prueba

Se ejecutó la remediación dirigida sobre la tupla de identidad exacta reportada en el manual testing:
- **Usuario:** `Admin_municipio_Juan`
- **Correo:** `juanprb@colegio.edu.co`
- **Documento:** `CC` `123456`
- **ID de Usuario Localizado:** `1727a8ca-f73d-4091-b829-8791e6f72749`

### Acciones Aplicadas y Verificadas:
1. **Revocación de Sesiones:** Todos los tokens de actualización (`RefreshToken`) asociados fueron revocados de inmediato (`is_revoked = True`).
2. **Imposibilidad de Autenticación:** La contraseña anterior ingresada manualmente fue sustituida por un hash aleatorio e inútil generado criptográficamente (`password_hasher.hash(generate_raw_token(32))`).
3. **Estado de la Cuenta:** Fijado a `is_active = False` y `is_verified = False`.
4. **Política de Credenciales:** `must_change_password = True`.
5. **Invalidación de Tokens:** Cualquier invitación o token de activación previo fue marcado como `is_revoked = True`.
6. **Preservación Territorial:** Se conservó intacta la asignación municipal original del usuario y su rol en `UserRole`.
7. **Auditoría:** Se registró el evento `AuditEventType.MUNICIPALITY_ADMIN_REMEDIATED` sin registrar secretos ni contraseñas.

---

## 5. Invariantes de Seguridad y Ciclo de Vida del Token

### 5.1 Invariante de Aprovisionamiento
- Ningún parámetro de contraseña es aceptado en el contrato de aprovisionamiento.
- Cualquier solicitud que intente enviar `password` o `is_active` es rechazada inmediatamente con `HTTP 422 Unprocessable Entity` (`extra="forbid"`).
- La cuenta se crea con contraseña inútil y en estado `is_active=False`, `is_verified=False`.
- El endpoint de actualización de estado (`PATCH /{id}/status`) rechaza con `HTTP 409 Conflict` cualquier intento de activar manualmente una cuenta con `is_verified=False`.

### 5.2 Ciclo de Vida del Token de Invitación
1. **Generación:** Token de alta entropía de 48 bytes URL-safe (`secrets.token_urlsafe(48)`).
2. **Persistencia Segura:** En la base de datos se almacena únicamente el hash SHA-256 (`token_hash`), nunca el token en texto claro.
3. **Vigencia:** 48 horas exactas desde su emisión (`expires_at = datetime.now(UTC) + timedelta(hours=48)`).
4. **Canje Único Atómico:** La aceptación ejecuta un update condicional atómico que garantiza que sólo una solicitud concurrente pueda marcar `is_used=True`, previniendo replay attacks y doble activación.
5. **Invalidación en Cascada:**
   - La regeneración de invitación revoca tokens anteriores.
   - La desactivación de la cuenta revoca tokens pendientes.
   - La reasignación territorial revoca tokens pendientes (evitando que se active con un municipio anterior).
6. **Ausencia de Secretos:** Los logs, eventos de auditoría y endpoints de listado o detalle nunca contienen el token ni la contraseña.

---

## 6. Flujo de Trabajo con SMTP No Disponible (Entorno de Desarrollo)

Dado que el entorno de desarrollo carece de servidor SMTP:
1. Al aprovisionar o reenviar invitación, `EmailService` detecta la ausencia de host SMTP y retorna `EmailDeliveryStatus.EMAIL_NOT_CONFIGURED`.
2. El sistema **NO** activa la cuenta automáticamente ni genera contraseñas por defecto.
3. En entornos no productivos (`settings.is_development == True`), la respuesta del endpoint de creación o reenvío incluye de forma transitoria el enlace directo de activación (`invitation_url`) y el token para uso del operador de desarrollo.
4. En producción o staging (`ENVIRONMENT in ('production', 'staging')`), el backend garantiza server-side que `raw_invitation_token` e `invitation_url` retornan `None`.
5. En la interfaz web:
   - Se muestra un modal de un solo uso indicando claramente que el correo no está disponible.
   - El operador puede copiar el enlace de activación para entregarlo manualmente al usuario invitado.
   - Al cerrar el modal, el enlace se descarta de la memoria del cliente web.
   - En las tablas y listados generales, el token nunca es visible.

---

## 7. Comandos de Validación Ejecutados y Resultados Reales

### 7.1 Pruebas Automatizadas de Backend (NTA-09-R2)
Comando:
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_nta09_municipality_admin_provisioning.py -v
```
**Resultado:**
```text
======================= 22 passed, 5 warnings in 49.55s =======================
```
Escenarios certificados:
1. `test_01_dept_admin_provisions_in_own_department`: Aprovisionamiento sin contraseña crea cuenta inactiva con UserRole municipal.
2. `test_02_dept_admin_cannot_provision_outside_department`: Aislamiento departamental estricto (403).
3. `test_03_national_admin_supervisory_provisioning`: Supervisión nacional permitida.
4. `test_04_superadmin_emergency_provisioning`: Anulación de emergencia superadmin permitida.
5. `test_05_unauthorized_roles_rejected`: Roles no autorizados (coordinador, etc.) rechazados (403).
6. `test_06_peer_provisioning_rejected`: Administrador municipal no puede crear pares (403).
7. `test_07_invalid_municipality_rejected`: Municipio inexistente rechazado (404).
8. `test_08_duplicate_uniqueness_conflicts`: Detección de duplicados en correo, usuario y documento (409).
9. `test_09_status_lifecycle_and_session_revocation`: Revocación de sesiones en desactivación.
10. `test_10_reassign_municipality_lifecycle`: Reasignación territorial con validación intradepartamental.
11. `test_11_audit_events_logged`: Registro de `MUNICIPALITY_ADMIN_CREATED` y `MUNICIPALITY_ADMIN_INVITED`.
12. `test_12_validation_error_structured_format_and_spanish_feedback`: Rechazo estricto (422) de campos de contraseña e `is_active` en la solicitud.
13. `test_13_lifecycle_activation_and_password_policy`: Ciclo completo: inactivo en creación -> no puede autenticarse -> canje por token establece contraseña Argon2id -> activación exitosa -> token no reutilizable (409).
14. `test_14_cross_municipality_isolation_and_peer_protection`: Aislamiento entre administradores municipales.
15. `test_15_administrative_user_directory_visibility`: Visibilidad consistente en directorio con estado pendiente de activación.
16. `test_16_token_error_matrix`: Rechazo seguro de tokens inválidos (404), expirados (410), revocados (409) y usados (409). Contraseñas débiles o dispares no consumen el token.
17. `test_17_atomic_claim_prevents_double_redemption`: Reclamación atómica previene doble activación concurrente.
18. `test_18_deactivation_and_reassignment_invalidate_invitation`: Desactivación y reasignación invalidan invitaciones pendientes; bloqueo de bypass de activación en status endpoint.
19. `test_19_resend_authorization_and_active_account_protection`: Reenvío protegido por RBAC y bloqueo de reenvío sobre cuentas ya activadas (previene toma de control).
20. `test_20_no_secrets_in_logs_audit_or_routine_responses`: Ausencia total de tokens y contraseñas en logs, auditorías y listados.
21. `test_21_non_development_environments_never_disclose_invitation[production]`: Servidor en producción nunca expone el token ni el enlace.
22. `test_21_non_development_environments_never_disclose_invitation[staging]`: Servidor en staging nunca expone el token ni el enlace.

### 7.2 Pruebas de Regresión Cruzada
Comando:
```powershell
$env:PYTHONPATH='.'; python -m pytest tests/test_municipality_admin_rbac.py tests/test_department_admin_invitation.py -v
```
**Resultado:**
```text
======================= 23 passed, 2 warnings in 45.11s =======================
```

### 7.3 Verificación de Tipos Frontend
Comando:
```powershell
npm run typecheck
```
**Resultado:**
```text
> pevn-frontend@0.1.0 typecheck
> tsc --noEmit
(Exit Code: 0 - Cero errores de TypeScript)
```

---

## 8. Procedimiento de Aceptación Manual para el Product Owner

Para certificar el hito en la aplicación en ejecución (`http://localhost:3000`):

1. **Aprovisionamiento sin contraseña:**
   - Inicie sesión como Administrador Departamental o Nacional.
   - Navegue a `/admin/municipality-admins`.
   - Haga clic en **"➕ Asignar administrador municipal"**.
   - Verifique que **NO** existe ningún campo de contraseña inicial en el formulario.
   - Complete los datos personales y seleccione un municipio. Haga clic en **"Crear cuenta e invitar"**.
2. **Verificación del estado inactivo y entrega de invitación:**
   - Se abrirá el diálogo modal **"Invitación de activación"** indicando que la cuenta está en estado `Inactivo / Pendiente de activación`.
   - Debido a que SMTP no está configurado, el diálogo mostrará el aviso amarillo y el enlace de activación de desarrollo.
   - Copie el enlace haciendo clic en **"📋 Copiar enlace"**. Cierre el modal.
   - Verifique en la tabla que el nuevo administrador aparece con la insignia amarilla: `Inactivo / Pendiente de activación`.
3. **Imposibilidad de inicio de sesión previo a la activación:**
   - En una ventana de incógnito, vaya a `/login` e intente iniciar sesión con el usuario recién creado y cualquier contraseña.
   - Confirme que el acceso es denegado (HTTP 401).
4. **Activación y definición autónoma de credenciales:**
   - En la ventana de incógnito, pegue el enlace de activación copiado (`/auth/accept-invitation?token=...`).
   - Verifique que la pantalla muestra el encabezado `Onboarding Administrador Municipal • PEVN` con el municipio asignado y el correo enmascarado.
   - Ingrese una contraseña segura que cumpla las políticas (mínimo 8 caracteres) y confírmela.
   - Haga clic en **"Activar Cuenta y Establecer Contraseña"**.
   - Confirme la pantalla de éxito indicando que la cuenta ha sido activada exitosamente.
5. **Comprobación de no reutilización del enlace:**
   - Intente recargar o enviar nuevamente el formulario con el mismo enlace.
   - Confirme que el sistema rechaza la reutilización indicando que la invitación ya fue utilizada.
6. **Inicio de sesión exitoso:**
   - Inicie sesión en `/login` con el usuario y la contraseña recién establecida.
   - Confirme acceso exitoso al panel de control correspondiente al alcance municipal.
7. **Verificación de la cuenta remediada (`Admin_municipio_Juan`):**
   - Intente iniciar sesión con `Admin_municipio_Juan` y la contraseña temporal que se le asignó en la prueba anterior.
   - Confirme que el inicio de sesión es rechazado.

---

## 9. Dependencias de Despliegue SMTP y Riesgos Residuales

1. **Configuración de SMTP en Producción:**
   - En producción, es imperativo configurar las variables de entorno `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `EMAILS_FROM_EMAIL`.
   - Al configurar dichas variables, el envío de correos pasará automáticamente a `EMAIL_SENT` y el backend omitirá cualquier retorno de enlace directo en las respuestas JSON.
2. **Entorno de Desarrollo:**
   - El mecanismo de divulgación controlada de un solo uso está restringido exclusivamente a `ENVIRONMENT=development` mediante validación estricta en el backend (`settings.is_development`).

---

## 10. Puerta de Salida (Exit Gate)

```text
================================================================================
DICTAMEN DEL HITO NTA-09-R2:
CONDITIONAL PASS — MANUAL VALIDATION REQUIRED
================================================================================
```
*Justificación:* Todos los controles automatizados de backend (22/22 pruebas unitarias e integrales NTA-09 y 23/23 pruebas de regresión RBAC/invitación), el chequeo de tipos TypeScript y la remediación dirigida de la cuenta de prueba han pasado con 100% de éxito. Conforme al Estándar AI Software Factory v1.2, se requiere la validación manual del Product Owner en el navegador antes de elevar el estado a `CERTIFIED — PASS`.
