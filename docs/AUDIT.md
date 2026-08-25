# Plataforma Educativa Virtual Nacional (PEVN)
## Guía de Auditoría de Seguridad Persistente (Fase 2)

---

### 1. Marco de Auditoría y Cumplimiento Normativo

El módulo de auditoría de PEVN implementa un registro inmutable, no repudiable y persistente de todas las acciones sensibles de seguridad en la tabla `audit_logs` de PostgreSQL, en cumplimiento con la normativa colombiana de protección de datos personales (**Ley Estatutaria 1581 de 2012**) y estándares de seguridad para software del sector público.

---

### 2. Esquema de la Tabla `audit_logs`

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_ip VARCHAR(45) NOT NULL,
    actor_user_agent VARCHAR(500),
    target_id VARCHAR(100),
    target_type VARCHAR(50),
    institution_id UUID REFERENCES institutions(id) ON DELETE SET NULL,
    correlation_id VARCHAR(100),
    success BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

-- Índices de consulta de alta velocidad
CREATE INDEX ix_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX ix_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX ix_audit_logs_institution_id ON audit_logs(institution_id);
CREATE INDEX ix_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX ix_audit_logs_occurred_at ON audit_logs(occurred_at DESC);
```

---

### 3. Política Estricta de Sanitización de Metadatos (Zero PII / Secrets)

El servicio `DatabaseAuditService` pasa todos los diccionarios de metadatos por la función recursiva `sanitize_audit_metadata()` antes de persistirlos en base de datos.

Campos automáticamente censurados con `[REDACTED]`:
- `password`, `current_password`, `new_password`, `confirm_password`
- `access_token`, `refresh_token`, `raw_token`, `token`
- `secret`, `jwt_secret`, `key`, `authorization`, `cookie`
- `document_number` (enmascarado parcialmente si se incluye en logs estructurados)

---

### 4. Inventario de Eventos de Auditoría de Fase 2

| Código de Evento (`AuditEventType`) | Nivel | Descripción |
| :--- | :---: | :--- |
| `user.login.success` | INFO | Inicio de sesión exitoso de un usuario institucional. |
| `user.login.failure` | WARN | Intento de inicio de sesión con credenciales inválidas. |
| `user.account.locked` | SECURITY | Bloqueo temporal por 15 minutos tras 5 intentos fallidos consecutivos. |
| `token.refresh.success` | INFO | Rotación exitosa de access token y refresh token. |
| `token.reuse.detected` | CRITICAL | Intento de reutilización de refresh token (brecha detectada, familia revocada). |
| `user.logout` | INFO | Cierre voluntario de sesión y revocación de refresh tokens. |
| `user.password.changed` | INFO | Cambio exitoso de contraseña con invalidación de sesiones previas. |
| `user.password.reset.requested` | INFO | Solicitud de restablecimiento de contraseña. |
| `user.password.reset.confirmed` | INFO | Confirmación y actualización de contraseña mediante token único. |
| `user.access_denied` | WARN | Intento de acceso sin permisos suficientes o violación de scope multi-inquilino. |
| `suspicious_activity.detected` | SECURITY | Detección de token malformado, manipulado o sospechoso. |
