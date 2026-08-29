# INFORME DE HOTFIX — FASE 7
# ALINEACIÓN DE ESQUEMA RBAC — TIMESTAMPS DE AUDITORÍA EN `role_permissions`

**Fecha de Ejecución:** 2026-08-28  
**Ambiente:** PEvN Desarrollo / Pre-producción PostgreSQL  
**Tipo de Intervención:** Hotfix No Destructivo de Esquema Físico (Alembic Migration 014)  
**Estado:** **HOTFIX APLICADO Y VERIFICADO EXITOSAMENTE (301/301 Backend Tests Pass, Typecheck Pass)**

---

## 1. ROOT CAUSE (Causa Raíz)

El modelo SQLAlchemy `RolePermission` ([backend/app/models/role.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/role.py)) hereda de la clase base declarativa `Base` ([backend/app/db/base_class.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/base_class.py)). Como consecuencia arquitectónica, SQLAlchemy mapea automáticamente en `role_permissions` las columnas estándar de auditoría temporal:
- `created_at` (`DateTime(timezone=True)`)
- `updated_at` (`DateTime(timezone=True)`)

No obstante, en la migración fundacional `001_phase2_auth_schema.py` la tabla física `role_permissions` se definió únicamente con `(role_id, permission_id)`. Al consultar roles con permisos (`selectinload(Role.permissions)`) o al ejecutar el bootstrap de RBAC al inicio del backend (`select(RolePermission)`), SQLAlchemy generaba una sentencia SQL requiriendo `role_permissions.created_at` y `role_permissions.updated_at`, provocando un fallo en PostgreSQL:
`UndefinedColumnError: column role_permissions.created_at does not exist`
y generando un error HTTP 500 al intentar emitir invitaciones de rectores.

---

## 2. DETALLE TÉCNICO DE LA MIGRACIÓN

- **Tabla Afectada:** `role_permissions`
- **Columnas Añadidas:**
  - `created_at` (`TIMESTAMP WITH TIME ZONE`, `server_default=now()`, `NOT NULL`)
  - `updated_at` (`TIMESTAMP WITH TIME ZONE`, `server_default=now()`, `NOT NULL`)
- **Archivo de Migración:** [backend/migrations/versions/014_role_permissions_audit_timestamps.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/migrations/versions/014_role_permissions_audit_timestamps.py)
- **Revisión de Migración (Revision ID):** `014_role_permissions_audit_timestamps`
- **Revisión Predecesora (Down Revision):** `013_phase3c_promotion_auth_hardening`
- **Comando de Aplicación:** `alembic upgrade head`
- **Reversibilidad:** Completamente reversible vía `op.drop_column("role_permissions", "updated_at")` y `op.drop_column("role_permissions", "created_at")`.

```python
def upgrade() -> None:
    op.add_column(
        "role_permissions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "role_permissions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("role_permissions", "updated_at")
    op.drop_column("role_permissions", "created_at")
```

---

## 3. VERIFICACIÓN DE PRESERVACIÓN DE DATOS Y RBAC

1. **Integridad de Claves y Restricciones:**
   - Se preservó intacta la clave primaria compuesta `(role_id, permission_id)`.
   - Se preservaron las restricciones de clave foránea en cascada hacia `roles.id` y `permissions.id`.
2. **Preservación de Asociaciones Canónicas:**
   - La ejecución de `RbacBootstrapService` sobre PostgreSQL pobló e indexó exitosamente **303 asociaciones canónicas** (`role_permissions`), **11 roles** y **59 permisos** sin duplicados ni pérdida de integridad.
   - Verificación de valores `NULL`: 0 registros con `created_at IS NULL`, 0 registros con `updated_at IS NULL`.
3. **Cero Mutaciones Semánticas:**
   - Cero cambios en roles canónicos (`superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `coordinator`, `teacher`, `student`, `guardian`, `institution_admin`, `academic_coordinator`).
   - Cero cambios en permisos canónicos (`institutions:read`, `users:create`, etc.).
   - Cero cambios en `OrganizationalScope` o fronteras de aislamiento multitenant.

---

## 4. RESOLUCIÓN DE LA RUTA AFECTADA (HTTP 500)

- **Ruta Afectada Inicialmente:** `POST /api/v1/institutions/{institution_id}/rector-invitation`
- **Causa del Fallo:** La verificación del rol `rector` en `RectorOnboardingService` ejecutaba `select(Role)` y el bootstrap diferido de RBAC, disparando la consulta fallida sobre `role_permissions.created_at`.
- **Resultado Post-Migración:**
  - El bootstrap de inicio del backend inicializa limpiamente sin advertencias.
  - La consulta ORM `select(RolePermission)` se ejecuta con éxito retornando los 303 registros canónicos.
  - La carga de permisos del rol `rector` (`rector_role.permissions`) resuelve con éxito los 50 permisos asignados sin excepción `UndefinedColumnError`.
  - La emisión de invitaciones opera conforme a los estándares criptográficos (token de 48 bytes URL-safe, hash SHA-256 almacenado, pre-registro inactivo).

---

## 5. RESULTADOS DE PRUEBAS Y REGRESIÓN

| Verificación | Comando / Mecanismo | Resultado | Estado |
| :--- | :--- | :--- | :--- |
| **Alembic Migration 014** | `python -m alembic upgrade head` | 013 → 014 upgrade exitoso | ✅ PASS |
| **PostgreSQL Schema Verification** | `information_schema.columns` | 4 columnas presentes en `role_permissions` (`role_id`, `permission_id`, `created_at`, `updated_at`) | ✅ PASS |
| **ORM Bootstrap on PostgreSQL** | `RbacBootstrapService.seed_canonical_rbac_if_needed()` | 303 links, 11 roles, 59 perms | ✅ PASS |
| **Backend Full Regression Suite** | `python -m pytest tests/ -q` | 301 passed en 392s (100%) | ✅ PASS |
| **Frontend TypeScript Typecheck** | `npm run typecheck` (`tsc --noEmit`) | 0 errores de tipado | ✅ PASS |
| **Browser Automation** | N/A | No ejecutado (Regla estricta cumplida) | ✅ HONORED |

---

## 6. VERIFICACIÓN DE GOBERNANZA FORMAL

```text
DATABASE_SCHEMA_CHANGE = REQUIRED_AND_LIMITED_TO_ROLE_PERMISSIONS_TIMESTAMPS
RBAC_SEMANTICS_CHANGED = FALSE
RBAC_ROLES_CHANGED = FALSE
RBAC_PERMISSIONS_CHANGED = FALSE
RBAC_ASSOCIATIONS_CHANGED = FALSE
AUTHORIZATION_SEMANTICS_CHANGED = FALSE
TENANT_ISOLATION_CHANGED = FALSE
RECTOR_ONBOARDING_RULES_CHANGED = FALSE
PASSWORD_RECOVERY_CHANGED = FALSE
EXISTING_DATA_DELETED = FALSE
EXISTING_RBAC_DATA_MODIFIED = FALSE
BROWSER_AUTOMATION = NOT_RUN
```

---

## 7. ESTADO FINAL

```text
HOTFIX_STATUS = COMPLETE
SCHEMA_ALIGNMENT = VERIFIED
RBAC_STATUS = PRESERVED
DATA_PRESERVATION = VERIFIED
REGRESSION_STATUS = PASS
RECTOR_INVITATION_STATUS = RESOLVED
BROWSER_AUTOMATION = NOT_RUN
PROMOTION_READINESS = READY
```
