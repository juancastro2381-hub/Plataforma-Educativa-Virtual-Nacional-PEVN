# PEVN Security Policy

**Plataforma Educativa Virtual Nacional — Security Documentation**  
**Phase:** 1 — Foundation  
**Classification:** Internal Technical Documentation  
**Last Updated:** 2026-08-21

---

## 1. Security Philosophy

The PEVN platform is built on **Security by Design** principles. Security is not an afterthought — it is embedded into every architectural decision from the first line of code.

The platform processes sensitive data belonging to:
- Children and minors (students)
- Teachers and educational staff
- Public educational institutions
- Government administrative entities

This data is protected by Colombian law (Ley 1581 de 2012 — Ley de Protección de Datos Personales) and requires the highest standard of technical care.

---

## 2. Security Principles

### 2.1 Security by Design
Every feature is designed with security implications considered from the start. Security requirements are not retrofitted.

### 2.2 Least Privilege
Every component, user, and process operates with the minimum privileges required to perform its function:
- The application database user has only `SELECT`, `INSERT`, `UPDATE`, `DELETE` — no `CREATE`, `DROP`, `SUPERUSER`
- API tokens (Phase 2) will carry only the permissions needed for the specific operation
- Docker containers run as non-root users (UID 1001)

### 2.3 Defense in Depth
Multiple independent security layers protect against single-layer failures:
- Network level: container network isolation
- Transport level: TLS in production (infrastructure responsibility)
- Application level: security headers, CORS, trusted host middleware
- API level: input validation, rate limiting
- Data level: parameterized queries, ORM protection
- Authentication level: credential verification (Phase 2)
- Authorization level: RBAC + permissions + scope (Phase 2)
- Audit level: event logging (Phase 2)

### 2.4 Secure Defaults
All default configuration settings are secure. Insecure configurations require explicit opt-in:
- `DEBUG=False` by default
- No wildcard CORS by default
- OpenAPI documentation disabled in production
- All environment variables default to safe values

### 2.5 Institutional Data Isolation
A user belonging to Institution A **must never** access protected resources belonging to Institution B, unless explicitly granted a higher-level administrative scope. This is enforced by the `OrganizationalScope` mechanism defined in `app/core/security/interfaces.py`.

### 2.6 Privacy by Design
Personal data is treated as sensitive by default:
- Passwords are never logged under any circumstances
- Tokens and session identifiers are never logged
- Authorization header values are never logged
- Request/response bodies containing PII are not logged
- Error messages never expose personal data
- Database connection strings are masked in all logs

### 2.7 Auditability
All security-relevant events will be recorded in an immutable audit log. The audit taxonomy is defined in `app/audit/interfaces.py`. Phase 2 implements persistent storage.

### 2.8 Secrets Management
- No secrets are committed to the repository
- The `.env.example` file contains only placeholder values
- Production secrets must come from a dedicated secret management system (HashiCorp Vault, cloud provider secrets manager)
- The application validates production configuration at startup and refuses to run with unsafe defaults

---

## 3. Implemented Security Controls (Phase 1)

### 3.1 HTTP Security Headers
All API responses include the following headers (applied by `SecurityHeadersMiddleware`):

| Header | Value | Protection |
|--------|-------|------------|
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing attacks |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer information leakage |
| `Permissions-Policy` | (restrictive) | Browser feature abuse |
| `Cross-Origin-Opener-Policy` | `same-origin` | Spectre-class attacks |
| `Cross-Origin-Resource-Policy` | `same-origin` | Cross-origin data leakage |
| `X-XSS-Protection` | `0` | Legacy XSS filter vulnerabilities |
| `Content-Security-Policy` | (environment-appropriate) | XSS, content injection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | (staging/production only) |

### 3.2 CORS Configuration
- Configured explicitly from environment variable `CORS_ORIGINS`
- Wildcard (`*`) origins are **rejected at startup** in production
- `credentials=False` by default

### 3.3 Trusted Host Validation
- `TrustedHostMiddleware` validates the `Host` header against an explicit allowlist
- Prevents HTTP Host header injection attacks

### 3.4 Input Validation
- All API inputs validated by Pydantic v2 with strict type checking
- Validation errors return a safe, structured response without internal details

### 3.5 Safe Error Handling
- Stack traces are never included in API responses
- SQL error messages are never exposed to clients
- Internal file paths are never exposed
- Environment-aware verbosity: development may include more detail, production is always safe

### 3.6 Request Correlation IDs
- Every request receives a UUID4 correlation ID
- Included in log records for server-side tracing
- Echoed in response header `X-Correlation-ID`
- Client-provided IDs are validated against a strict regex before use

### 3.7 Database Security
- Application uses a dedicated, least-privilege database user (`pevn_app`)
- All queries use SQLAlchemy ORM or parameterized `text()` — no string concatenation
- Connection pooling with `pool_pre_ping=True` to detect stale connections
- Connection timeout enforced: 60 seconds maximum per query

### 3.8 Structured Secure Logging
- Logs never contain: passwords, tokens, auth headers, connection strings, API keys
- A `_sanitize_sensitive_fields` processor automatically redacts known sensitive field names
- JSON format in production for log aggregation system compatibility

### 3.9 Non-Root Container Execution
- Backend container runs as user `pevn` (UID 1001, no shell, no home directory)
- Frontend container runs as user `pevn` (UID 1001)
- Docker containers have minimal installed packages

### 3.10 Rate Limiting Architecture
- SlowAPI is configured and ready for activation (Phase 2)
- Rate limit backend configurable: `memory://` (development) or Redis URL (production)

---

## 4. Security Controls Planned for Future Phases

### Phase 2: Authentication & Authorization
- [ ] Argon2id password hashing (via the `IPasswordHasher` interface)
- [ ] JWT access tokens (short-lived, signed) + refresh tokens
- [ ] Token revocation via Redis blocklist
- [ ] Account lockout after N failed login attempts
- [ ] MFA foundation (TOTP)
- [ ] Full RBAC + Permission + Scope implementation
- [ ] Persistent audit log (append-only database table)
- [ ] Session security (HttpOnly cookies or memory-only token storage)

### Phase 3: Operational Security
- [ ] BigBlueButton API secret rotation procedure
- [ ] Recording access control (per-user, per-institution)
- [ ] File upload security (type validation, size limits, storage isolation)

### Phase 4: Infrastructure Security
- [ ] TLS certificate management
- [ ] Network segmentation (database not reachable from public network)
- [ ] Secrets manager integration (Vault / cloud provider)
- [ ] Dependency SBOM generation
- [ ] Penetration testing

### Phase 5: Monitoring & Response
- [ ] Security event alerting
- [ ] Anomaly detection
- [ ] Incident response procedures
- [ ] Vulnerability disclosure policy

---

## 5. Dependency Security

- Python dependencies are scanned with `pip-audit` in the CI pipeline
- Frontend dependencies are scanned with `npm audit` in the CI pipeline
- All dependencies are pinned to minor version ranges to allow security patches
- Floating `latest` tags are never used in production Docker images

---

## 6. Known Limitations (Phase 1)

The following security controls are **not yet implemented** and represent accepted risk for the development phase:

1. **Authentication**: No user authentication exists. The API is unauthenticated in Phase 1. **This platform must not be exposed to the public internet in Phase 1.**
2. **Authorization**: The `IAuthorizationService` interface is defined but not implemented.
3. **Audit persistence**: The `NoOpAuditService` does not persist audit records.
4. **Rate limiting enforcement**: Rate limiting middleware is configured but not yet actively applied to route handlers.
5. **HTTPS enforcement**: TLS is an infrastructure responsibility; the application assumes it runs behind a TLS terminator in production.

---

## 7. Logging Security Policy

**MUST NEVER log:**
- Passwords or authentication credentials
- JWT tokens or session identifiers
- Authorization header values
- Database connection strings with credentials
- API keys or service secrets
- Private cryptographic material
- Colombian national ID numbers (cédula) unnecessarily
- Full request or response bodies

**Logging policy is enforced by:**
- The `_sanitize_sensitive_fields` structlog processor
- Code review requirements
- The request logging middleware which explicitly excludes sensitive headers

---

## 8. Incident Response Foundation

In Phase 1, the incident response process is:

1. **Detect**: Monitor application logs for error-level events
2. **Report**: Report all security incidents to the project lead immediately
3. **Assess**: Determine scope and affected data
4. **Contain**: Stop the affected service if necessary
5. **Document**: Record the incident timeline and findings

A formal Incident Response Plan will be developed in Phase 4.

---

## 9. Contact

Security concerns should be reported directly to the project technical lead. Do not file public GitHub issues for security vulnerabilities.
