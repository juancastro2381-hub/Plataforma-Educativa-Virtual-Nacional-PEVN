# Plataforma Educativa Virtual Nacional (PEVN)
## Guía de Arquitectura de Autorización y Aislamiento Multi-Inquilino (Fase 2)

---

### 1. Resumen de Principios de Autorización

El modelo de control de acceso de PEVN implementa un esquema híbrido de **Control de Acceso Basado en Roles y Permisos (RBAC granular)** con **Aislamiento Organizacional Territorial Jerárquico**.

Principios rectores:
1. **Denegación por Defecto (Deny by Default)**: Cualquier recurso o acción no explícitamente permitida es automáticamente rechazada con código `403 Forbidden`.
2. **Principio de Mínimo Privilegio**: Cada rol otorga únicamente las acciones atómicas necesarias sobre los recursos del dominio.
3. **Prevención de Escalamiento Vertical**: Cada rol cuenta con un nivel numérico (`level: 10 - 100`). Un usuario con nivel $N$ no puede crear, modificar ni asignar roles con nivel $\ge N$.
4. **Barrera de Contención Multi-Institucional**: Un usuario autenticado con permiso para consultar instituciones únicamente puede consultar y gestionar recursos correspondientes a su institución o sedes subordinadas, a menos que cuente con alcance de nivel departamental o nacional.

---

### 2. Jerarquía de Roles y Niveles de Seguridad

| Rol (`SystemRole`) | Nivel | Descripción y Alcance |
| :--- | :---: | :--- |
| `superadmin` | 100 | Administrador técnico global de la plataforma (acceso total a configuración y auditoría). |
| `national_admin` | 90 | Administrador a nivel Ministerio de Educación Nacional (MEN). |
| `territorial_leader` | 80 | Secretaría de Educación Departamental / Municipal. |
| `institution_admin` | 70 | Rector / Director de Institución Educativa. |
| `coordinator` | 60 | Coordinador Académico o de Convivencia. |
| `teacher` | 50 | Docente de aula. |
| `student` | 20 | Estudiante matriculado. |
| `guardian` | 10 | Padre de familia / Acudiente legal. |

---

### 3. Sintaxis de Permisos Granulares y Comodines

Los permisos se componen del par `recurso:accion`:
- Recursos: `users`, `institutions`, `roles`, `grades`, `attendance`, `audit_logs`, `system_config`.
- Acciones: `read`, `create`, `update`, `delete`, `export`, `audit`.

**Evaluación de Comodines (Wildcards):**
- `*` o `*:*`: Otorga acceso irrestricto a todos los recursos y acciones (exclusivo para `superadmin`).
- `users:*`: Otorga todas las acciones posibles sobre el recurso `users`.
- `*:read`: Otorga permisos de lectura sobre cualquier recurso en el sistema.

---

### 4. Alcance Organizacional Territorial y Aislamiento Multi-Inquilino

El contexto de autorización (`AuthorizationContext`) contiene un `OrganizationalScope` estructurado según la división político-administrativa de Colombia (DANE):

```
                      +-------------------+
                      |   Nacional (CO)   |  -> SuperAdmin / MEN (scope.is_national == True)
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |   Departamento    |  -> Secretaría Departamental (department_id)
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |    Municipio      |  -> Secretaría Municipal (municipality_id)
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |    Institución    |  -> Rector / Colegio (institution_id)
                      +-------------------+
                                |
                                v
                      +-------------------+
                      |  Sede (Campus)    |  -> Sede Educativa DANE (campus_id)
                      +-------------------+
```

#### Regla de Contención (`scope_contains`):
```python
def scope_contains(
    actor_scope: OrganizationalScope, target_scope: OrganizationalScope
) -> bool:
  # 1. Validación de código de país
  if (
      actor_scope.country_code
      and target_scope.country_code
      and actor_scope.country_code != target_scope.country_code
  ):
    return False

  # 2. Alcance nacional contiene todas las instituciones
  if actor_scope.is_national():
    return True

  # 3. Alcance departamental
  if actor_scope.department_id:
    if actor_scope.department_id != target_scope.department_id:
      return False
    if actor_scope.municipality_id is None:
      return True

  # 4. Alcance municipal
  if actor_scope.municipality_id:
    if actor_scope.municipality_id != target_scope.municipality_id:
      return False
    if actor_scope.institution_id is None:
      return True

  # 5. Alcance institucional
  if actor_scope.institution_id:
    if actor_scope.institution_id != target_scope.institution_id:
      return False  # Intento de acceso cross-tenant bloqueado (403)!

  return True
```

---

### 5. Inyección de Dependencias en FastAPI

```python
@router.get("/institutions/{institution_id}")
async def get_institution_by_id(
    institution_id: uuid.UUID,
    db: SessionDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
) -> InstitutionResponse:
  # Valida automáticamente el permiso y la contención de scope institucional
  target_scope = OrganizationalScope(institution_id=str(institution_id))
  await authorization_service.require(
      auth,
      required_permission=SecurityPermission("institutions", "read"),
      target_scope=target_scope,
  )
  ...
```
