# ADR-002: Arquitectura de Autenticación, Autorización y Aislamiento Multi-Inquilino

## Estado
**Aprobado e Implementado (Fase 2)**

## Fecha
2026-08-22

## Contexto
La Plataforma Educativa Virtual Nacional (PEVN) requiere una infraestructura robusta de identidad, autenticación, autorización y auditoría de seguridad para operar de manera segura a nivel nacional en instituciones educativas de Colombia.

Requisitos críticos:
1. Protección total contra ataques XSS y robo de tokens en clientes web.
2. Protección contra ataques de fuerza bruta y suplantación de identidad.
3. Aislamiento institucional estricto (multi-tenancy) basado en la estructura territorial DANE.
4. Trazabilidad inmutable de eventos de seguridad sin almacenar credenciales en texto claro ni en logs.
5. Inicialización de cuentas administrativas sin credenciales estáticas ni hardcodeadas.

## Decisiones de Arquitectura

### 1. Entrega de Tokens (Opción A Aprobada)
- **Access Token**: JWT firmado con `HS256`, 15 minutos de caducidad, almacenado **estrictamente en memoria volátil de React** (`in-memory state`).
- **Refresh Token**: Cadena de alta entropía (48 bytes), transmitida en cookie `HttpOnly`, `SameSite=Strict`, `Secure` (en producción), con expiración de 7 días.
- **Rotación y Detección de Replay**: Cada refresco rota el token y almacena el hash SHA-256 en base de datos. La reutilización de un token previo revoca automáticamente toda la familia (`family_id`).

### 2. Algoritmo de Hashing de Contraseñas
- **Argon2id** (RFC 9106) con parámetros seguros: `memory_cost=65536` (64 MB), `time_cost=3`, `parallelism=4`, `salt_len=16`.
- Política de bloqueo progresivo tras 5 intentos fallidos consecutivos (15 minutos de congelamiento).

### 3. Modelo de Autorización Híbrido (RBAC + Territorial Scoping)
- Permisos atómicos (`recurso:accion`) y soporte para comodines (`users:*`, `*:read`, `*`).
- Niveles de rol jerárquicos (`level: 10 - 100`) para evitar escalamiento vertical de privilegios.
- Servicio centralizado `CentralizedAuthorizationService` con evaluación jerárquica `scope_contains()` según la división DANE (Nacional $\rightarrow$ Departamento $\rightarrow$ Municipio $\rightarrow$ Institución $\rightarrow$ Sede).

### 4. Inicialización de SuperAdmin
- Implementación de herramienta CLI `python -m app.cli.create_superadmin` con lectura segura vía `getpass` o variables de entorno del sistema. Cero credenciales en código fuente o semillas estáticas.

### 5. Auditoría Persistente
- Servicio `DatabaseAuditService` con persistencia en tabla `audit_logs` en PostgreSQL y sanitización recursiva de secretos (`sanitize_audit_metadata`).

## Consecuencias y Beneficios
- **Seguridad Robusta**: Mitigación integral contra vectores de ataque comunes (XSS, CSRF, Replay, Cross-Tenant Leaks).
- **Escalabilidad**: Capacidad de operar miles de colegios en una arquitectura multi-inquilino lógicamente aislada.
- **Auditoría y Cumplimiento**: Registro inmutable de eventos para auditorías regulatorias y forenses.
