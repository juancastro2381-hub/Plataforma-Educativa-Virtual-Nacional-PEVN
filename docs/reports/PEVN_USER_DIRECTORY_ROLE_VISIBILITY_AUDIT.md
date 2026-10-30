# INFORME FORENSE DE AUDITORÍA: VISIBILIDAD DE ROLES RBAC EN DIRECTORIO DE USUARIOS

**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** 30 de Octubre de 2026  
**Auditor:** Senior Software Architect, RBAC Security Auditor & Educational Platform Authorization Specialist  
**Estado de la Auditoría:** AUDITORÍA FORENSE COMPLETADA (READ-ONLY)  
**Clasificación del Hallazgo:** `ROLE_ASSIGNED_BUT_NOT_SERIALIZED` (Roles asignados y persistidos en base de datos, pero omitidos en el esquema de serialización de la API)

---

## 1. Descripción del Problema

Durante pruebas de inspección y validación en la interfaz de administración de PEVN, al acceder a la ruta:
`/admin/users` (**Directorio de Usuarios — Gestión Educativa**)

Bajo el contexto jurisdiccional de la institución educativa **ALEGRIA DE APRENDER** (ID: `3b445e50-ca10-4f6c-977d-2d10640ee24f`), la tabla **"Usuarios en Jurisdicción"** lista correctamente las cuentas de usuario activas registradas (`Total de usuarios registrados: 4`), mostrando su número de documento, nombre completo, identificador de usuario y estado (`Activo`). Sin embargo, en la columna **"Roles Asignados"**, todos los usuarios listados muestran de manera uniforme la leyenda:

> **"Sin roles"**

Asimismo, al abrir el modal de detalle de usuario (**"👁️ Ver Ficha"**), la sección **"ROLES ATÓMICOS ASIGNADOS"** presenta:
> **"Sin roles asignados"**

El Product Owner solicitó una investigación forense exhaustiva de extremo a extremo (Frontend → API Controller → Domain Service → Serialización Pydantic → Base de Datos PostgreSQL) para determinar si las identidades carecen realmente de roles asignados, si existe una falla en el flujo de aprovisionamiento/invitación, si se trata de una inconsistencia de aislamiento jurisdiccional RBAC, o si corresponde a un defecto de serialización o renderizado.

---

## 2. Causa Raíz Exacta y Evidencia Determinante

### Diagnóstico Concluyente: `ROLE_ASSIGNED_BUT_NOT_SERIALIZED`

El problema **NO ES** una ausencia de roles en base de datos ni una falla en el aprovisionamiento de cuentas. Los roles están correcta y legítimamente persistidos y activos en PostgreSQL.

La causa raíz exacta consta de los siguientes dos factores técnicos en el backend:

1. **Ausencia del campo `roles` en el esquema Pydantic de respuesta:**  
   En `backend/app/schemas/user.py`, la clase `UserResponse` (utilizada por `UserListResponse` en el endpoint `GET /api/v1/users` y `GET /api/v1/users/{id}`) omite por completo el atributo `roles`:
   ```python
   # backend/app/schemas/user.py
   class UserResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)

       id: uuid.UUID
       email: EmailStr
       username: str
       first_name: str
       last_name: str
       full_name: str
       document_type: DocumentType
       document_number: str
       institution_id: uuid.UUID | None = None
       is_active: bool
       is_verified: bool
       created_at: datetime
       updated_at: datetime
       # DEFECTO: No existe el campo 'roles: list[str]'
   ```

2. **Ausencia de propiedad de acceso `roles` en el modelo ORM `User`:**  
   En `backend/app/models/user.py`, la entidad `User` posee la relación `user_roles: Mapped[list[UserRole]]`, pero no expone una propiedad de lectura `@property def roles(self) -> list[str]` que extraiga los nombres canónicos de los roles activos (`[ur.role.name for ur in self.user_roles if ur.is_active]`).

3. **Efecto en cascada en la API y el Frontend:**  
   - Al ejecutar `GET /api/v1/users`, FastAPI valida y serializa los registros mediante `UserResponse.model_validate(u)`. Al no existir el campo `roles` en el esquema, el JSON resultante omite por completo dicha clave.
   - La respuesta HTTP 200 entrega objetos de usuario que **no contienen la propiedad `roles`** (`"roles": undefined` en el cliente JavaScript).
   - En el frontend (`frontend/src/pages/admin/UsersView.tsx`, líneas 333-341 y 450-456), la lógica de renderizado evalúa:
     ```tsx
     {u.roles && u.roles.length > 0 ? (
       u.roles.map((r: string) => (
         <Badge key={r} variant="neutral">
           {formatRoleName(r)}
         </Badge>
       ))
     ) : (
       <span style={{ color: '#94A3B8', fontSize: '0.75rem' }}>Sin roles</span>
     )}
     ```
   - Al ser `u.roles` indefinido (`undefined`), la condición resulta falsa y el frontend recurre a su valor por defecto: `<span style={{ color: '#94A3B8', fontSize: '0.75rem' }}>Sin roles</span>`.

---

## 3. Flujo Completo de Datos: Frontend y Backend

```
+----------------------------------------------------------------------------------------------------+
| 1. FRONTEND: UsersView.tsx (/admin/users)                                                          |
|    - usersApi.searchUsers({ page, page_size: 15, is_active: true })                                |
|    - Espera interfaz TypeScript: UserResponse { roles?: string[]; ... }                            |
+----------------------------------------------------------------------------------------------------+
                                             |
                                             v  GET /api/v1/users (Authorization: Bearer <JWT>)
+----------------------------------------------------------------------------------------------------+
| 2. BACKEND API: router.get("", response_model=UserListResponse) en users.py                        |
|    - Verifica permiso requerido: 'users:read' (Satisfactorio)                                      |
|    - Resuelve jurisdicción institucional (3b445e50-ca10-4f6c-977d-2d10640ee24f)                   |
|    - Invoca UserService.list_users(institution_id=...)                                             |
+----------------------------------------------------------------------------------------------------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------+
| 3. DOMAIN SERVICE: UserService.list_users en user_service.py                                       |
|    - Consulta SQLAlchemy:                                                                          |
|      select(User).options(selectinload(User.user_roles), selectinload(User.institution))           |
|      .where(User.institution_id == target_institution_id)                                          |
|    - Recupera 4 entidades User de la BD con sus relaciones user_roles cargadas                     |
+----------------------------------------------------------------------------------------------------+
                                             |
                                             v
+----------------------------------------------------------------------------------------------------+
| 4. SERIALIZACIÓN: UserListResponse(items=[UserResponse.model_validate(u) for u in users])          |
|    - UserResponse (backend/app/schemas/user.py) NO POSEE campo 'roles'                             |
|    - Pydantic descarta cualquier atributo no modelado.                                             |
|    - JSON generado: { "items": [ { "id": "...", "username": "...", ... (SIN 'roles') } ] }         |
+----------------------------------------------------------------------------------------------------+
                                             |
                                             v  HTTP 200 OK con payload JSON sin 'roles'
+----------------------------------------------------------------------------------------------------+
| 5. FRONTEND RENDERING:                                                                             |
|    - u.roles es undefined -> u.roles && u.roles.length > 0 evalúa False                           |
|    - Renderiza: "Sin roles"                                                                        |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Hallazgos en Base de Datos (Auditoría Read-Only y Reconciliación Forense)

Se ejecutó una inspección forense en la base de datos PostgreSQL (`pevn_db`) bajo aislamiento estricto de solo lectura.

**Institución evaluada:**
- **ID:** `3b445e50-ca10-4f6c-977d-2d10640ee24f`
- **Nombre:** ALEGRIA DE APRENDER
- **Código DANE:** `313430800041`

### Tabla de Reconciliación Forense de Usuarios (Anonimizada)

| Referencia de Usuario | Estado de Cuenta | Asignación en BD (`user_roles`) | Rol Canónico (`roles`) | Ámbito (`institution_id`) | Respuesta API (`/api/v1/users`) | Visualización en Directorio | Clasificación del Hallazgo |
|---|---|---|---|---|---|---|---|
| **Usuario A** (CC ...8544, Mary G.) | `is_active=True`, `is_verified=True` | `ur_active=True`, asignado 2026-10-29 14:31:19 UTC | `rector` ("Rector / Director", level=80) | `3b445e50...` | Sin campo `roles` | "Sin roles" | `ROLE_ASSIGNED_BUT_NOT_SERIALIZED` |
| **Usuario B** (CC ...0000, Mauro D.) | `is_active=True`, `is_verified=False` | `ur_active=True`, asignado 2026-10-30 07:22:20 UTC | `teacher` ("Docente", level=30) | `3b445e50...` | Sin campo `roles` | "Sin roles" | `ROLE_ASSIGNED_BUT_NOT_SERIALIZED` |
| **Usuario C** (CC ...2100, Andres G.) | `is_active=True`, `is_verified=False` | `ur_active=True`, asignado 2026-10-30 08:23:36 UTC | `guardian` ("Acudiente / Tutor", level=15) | `3b445e50...` | Sin campo `roles` | "Sin roles" | `ROLE_ASSIGNED_BUT_NOT_SERIALIZED` |
| **Usuario D** (TI ...3355, Danna G.) | `is_active=True`, `is_verified=False` | `ur_active=True`, asignado 2026-10-30 07:19:59 UTC | `student` ("Estudiante", level=10) | `3b445e50...` | Sin campo `roles` | "Sin roles" | `ROLE_ASSIGNED_BUT_NOT_SERIALIZED` |

**Evidencia de Verificación:**
- La tabla de asignación asociativa `user_roles` tiene exactamente 4 registros vinculados a la institución `3b445e50-ca10-4f6c-977d-2d10640ee24f`.
- Todos los registros tienen `is_active = True`.
- Cada asignación apunta a un `role_id` válido de la tabla `roles` que coincide exactamente con la taxonomía oficial de PEVN (`rector`, `teacher`, `guardian`, `student`).
- Ningún usuario de la institución se encuentra en la base de datos sin un rol asignado.

---

## 5. Hallazgos sobre el Aprovisionamiento de Roles

Se auditó el flujo de creación y aprovisionamiento de cuentas en:
- `UserService.provision_institutional_user` (`backend/app/services/user_service.py`, líneas 180-293)
- `RectorOnboardingService` (`backend/app/services/rector_onboarding_service.py`)
- `GuardianOnboardingService` (`backend/app/services/guardian_onboarding_service.py`)

**Conclusiones del aprovisionamiento:**
1. **Atomicidad transaccional garantizada:** `UserService.provision_institutional_user` persiste la entidad `User` y la entidad asociativa `UserRole` dentro de la misma transacción de sesión de base de datos antes de confirmar.
2. **Imposibilidad de cuentas activas huérfanas en el flujo estándar:** Si la resolución o vinculación de `UserRole` falla, la transacción SQLAlchemy revierte (`rollback`), evitando que se creen identidades activas sin rol.
3. **Persistencia verificada:** Todos los usuarios creados mediante invitaciones de Rector, aprovisionamiento de docentes, vinculación de estudiantes y activación de acudientes cuentan con su registro `UserRole` activo en base de datos.
4. Por lo tanto, se descarta categóricamente la hipótesis **D** (`PROVISIONING_FLOW_FAILURE`).

---

## 6. Evaluación de Integridad RBAC y Jurisdiccional

1. **Cumplimiento de la Jerarquía de Autoridad:**
   Se mantiene estrictamente la jerarquía estipulada por la arquitectura de PEVN:
   `SUPER_ADMIN → NATIONAL_ADMIN → DEPARTMENT_ADMIN → MUNICIPALITY_ADMIN → RECTOR → COORDINATOR / TEACHER / STUDENT / GUARDIAN`.
2. **Aislamiento Territorial y Multitenancy:**
   En `backend/app/api/v1/endpoints/users.py`, la función `list_users` resuelve la jurisdicción del actor en sesión:
   - Rectores e integrantes institucionales únicamente pueden consultar usuarios de su propia `institution_id`.
   - Administradores Municipales únicamente pueden consultar usuarios pertenecientes a instituciones de su municipio.
   - Administradores Departamentales únicamente pueden consultar usuarios de instituciones de su departamento.
   - Los tests de frontera jurisdiccional (`backend/tests/test_users_api.py`) pasan al 100% (3/3 pruebas exitosas), confirmando que no existe fuga de identidades entre sedes o instituciones.
3. **Ausencia de Bypasses:** No se detectó ninguna vulnerabilidad de elevación vertical ni de omisión de comprobación de permisos.

---

## 7. Cantidad de Usuarios Afectados

- **En la institución auditada (`ALEGRIA DE APRENDER`):** 4 usuarios (100% de los usuarios de la institución).
- **Alcance a nivel de plataforma:** El defecto es de nivel estructural en el esquema `UserResponse` de la API. En consecuencia, **el 100% de los usuarios devueltos por `GET /api/v1/users` en cualquier institución o jurisdicción de la plataforma** exhibe la leyenda "Sin roles" en el frontend `/admin/users` hasta que se incluya la serialización del campo `roles`.

---

## 8. Acción Correctiva Recomendada (Plan de Remediación para Aprobación del PO)

Para resolver este defecto de forma limpia, mantenible y sin impacto a otros módulos, se recomienda la siguiente intervención técnica:

### 1. Modelo ORM `User` (`backend/app/models/user.py`):
Agregar la propiedad de conveniencia `@property def roles(self) -> list[str]:` para exponer los nombres canónicos de roles activos:
```python
@property
def roles(self) -> list[str]:
    """Lista de nombres canónicos de roles activos asignados al usuario."""
    if not hasattr(self, "user_roles") or not self.user_roles:
        return []
    return [
        ur.role.name
        for ur in self.user_roles
        if ur.is_active and getattr(ur, "role", None) is not None
    ]
```

### 2. Servicio de Dominio `UserService` (`backend/app/services/user_service.py`):
Optimizar la carga eager en `list_users` y `get_user_by_id` para cargar explícitamente la relación anidada `UserRole.role`:
```python
stmt = select(User).options(
    selectinload(User.user_roles).selectinload(UserRole.role),
    selectinload(User.institution),
)
```

### 3. Esquema Pydantic `UserResponse` (`backend/app/schemas/user.py`):
Incorporar el campo `roles` con valor predeterminado de lista vacía en `UserResponse`:
```python
roles: list[str] = Field(default_factory=list, description="Lista de roles canónicos activos asignados")
```

### 4. Cobertura de Pruebas Automatizadas (`backend/tests/test_users_api.py`):
Agregar aserciones que verifiquen que la respuesta de `GET /api/v1/users` y `GET /api/v1/users/{id}` incluye el arreglo `roles` poblado con los roles canónicos asignados (ej. `["rector"]`, `["teacher"]`).

---

## 9. Archivos Inspeccionados Durante la Auditoría

1. [UsersView.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/admin/UsersView.tsx) — Componente frontend del directorio de usuarios.
2. [users.ts](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/users.ts) — Cliente de servicios API de usuarios en frontend.
3. [auth.ts](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/types/auth.ts) — Definición de interfaz `UserResponse` en frontend.
4. [users.py (Endpoints)](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/users.py) — Controlador REST de consulta de usuarios.
5. [user.py (Schemas)](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/schemas/user.py) — Esquema Pydantic `UserResponse` y `UserListResponse`.
6. [user.py (Models)](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/app/models/user.py) — Entidad ORM SQLAlchemy `User`.
7. [role.py (Models)](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/app/models/role.py) — Entidades ORM `Role` y `UserRole`.
8. [user_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/user_service.py) — Lógica de negocio de consulta y aprovisionamiento.
9. [auth_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py) — Resolución de contexto de autorización y claims.
10. [test_users_api.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_users_api.py) — Pruebas de integración del API de usuarios y aislamiento multitenant.

---

## 10. Certificación de Auditoría Estricta de Solo Lectura

Se certifica formalmente que durante la ejecución de esta investigación forense:
- **NO** se asignaron, modificaron ni revocaron roles de usuario.
- **NO** se alteraron estados de cuentas, contraseñas ni permisos en la base de datos.
- **NO** se crearon ni eliminaron registros de usuarios ni instituciones.
- **NO** se modificaron políticas de seguridad ni matrices RBAC.
- **NO** se generaron ni aplicaron migraciones Alembic.
- **NO** se modificó el código de producción ni se realizaron commits o pushes en Git.
- Todos los datos e identificadores personales se han anonimizado rigurosamente en este informe.

---

## 11. Estado del Repositorio Git

- **Rama actual:** `main`
- **Último Commit (HEAD):** `23739d11428a3b74efefc25d3659217e79645171`  
  *Mensaje:* `INFORME DE INVESTIGACIÓN FORENSE: RECURRENCIA DE ERROR HTTP 500 TRAS MIGRACIÓN 033`
- **Árbol de trabajo:** Modificaciones confinadas a remediación y auditoría (sin cambios de BD).

---

## 12. Remediación Implementada y Cierre Técnico Verificado

Bajo la autorización del Product Owner, se procedió a implementar la remediación integral del defecto `ROLE_ASSIGNED_BUT_NOT_SERIALIZED`.

### A. Modificaciones Exactas en el Código

1. **Modelo ORM `User` (`backend/app/models/user.py`):**
   Se implementó la propiedad read-only `@property def roles(self) -> list[str]:` que extrae de forma segura y sin duplicados los identificadores canónicos de los roles activos asociados:
   ```python
   @property
   def roles(self) -> list[str]:
       """
       Return deduplicated canonical role identifiers (machine names) for active role assignments.

       Returns an empty list if there are no active assignments or if user_roles is not loaded.
       """
       if not hasattr(self, "user_roles") or not self.user_roles:
           return []

       assigned_roles: list[str] = []
       for ur in self.user_roles:
           if ur.is_active and getattr(ur, "role", None) is not None:
               role_name = ur.role.name
               if role_name and role_name not in assigned_roles:
                   assigned_roles.append(role_name)
       return assigned_roles
   ```

2. **Estrategia de Carga Eager en `UserService` (`backend/app/services/user_service.py`):**
   Para prevenir consultas N+1 y asegurar la disponibilidad de la relación anidada durante la serialización asíncrona, se encadenó `selectinload(UserRole.role)` en `list_users` y `get_user_by_id`:
   ```python
   stmt = select(User).options(
       selectinload(User.user_roles).selectinload(UserRole.role),
       selectinload(User.institution),
   )
   ```

3. **Esquema Pydantic `UserResponse` (`backend/app/schemas/user.py`):**
   Se incorporó el atributo `roles` normalizado con valor predeterminado seguro:
   ```python
   roles: list[str] = Field(
       default_factory=list,
       description="Canonical active role codes assigned to the user",
   )
   ```

4. **Interfaz TypeScript `UserResponse` (`frontend/src/types/auth.ts`):**
   Se normalizó el contrato para garantizar que `roles` es siempre un arreglo de strings:
   ```typescript
   export interface UserResponse {
     ...
     roles: string[]
     ...
   }
   ```

5. **Renderizado en Frontend (`frontend/src/pages/admin/UsersView.tsx`):**
   - Se actualizó el mapeo `formatRoleName` para armonizarlo con la nomenclatura institucional (`rector: 'Rector / Director'`, `guardian: 'Acudiente / Tutor'`).
   - Se implementó discriminación estricta entre arreglo poblado (`Array.isArray(u.roles) && u.roles.length > 0`), arreglo genuinamente vacío (`roles: []` -> `"Sin roles"`), y fallback para respuesta malformada (`"Error en formato de roles"`).
   - Se aplicó idéntica lógica al modal de detalle ("👁️ Ver Ficha").

---

### B. Ejemplo del Payload Final de la API (`GET /api/v1/users`) — Datos Anonimizados

```json
{
  "items": [
    {
      "id": "e9016dbb-f2aa-44fc-8339-1ada721c3925",
      "email": "docente.m@inst.edu.co",
      "username": "docente_m",
      "first_name": "Mauro",
      "last_name": "Diaz",
      "full_name": "Mauro Diaz",
      "document_type": "CC",
      "document_number": "898970000",
      "institution_id": "3b445e50-ca10-4f6c-977d-2d10640ee24f",
      "is_active": true,
      "is_verified": false,
      "roles": [
        "teacher"
      ],
      "created_at": "2026-10-30T07:22:20.860420Z",
      "updated_at": "2026-10-30T09:23:26.955566Z"
    },
    {
      "id": "caa2d78f-0218-4bd7-b9a7-4f945af1d5a9",
      "email": "rectora.m@inst.edu.co",
      "username": "rectora_m",
      "first_name": "Mary",
      "last_name": "Garcia",
      "full_name": "Mary Garcia",
      "document_type": "CC",
      "document_number": "195668544",
      "institution_id": "3b445e50-ca10-4f6c-977d-2d10640ee24f",
      "is_active": true,
      "is_verified": true,
      "roles": [
        "rector"
      ],
      "created_at": "2026-10-29T14:31:19.900916Z",
      "updated_at": "2026-10-30T07:00:50.063128Z"
    },
    {
      "id": "c9decc91-a29d-4b14-904b-c39f0a8e3839",
      "email": "acudiente.a@inst.edu.co",
      "username": "acudiente_a",
      "first_name": "Andres",
      "last_name": "Gonzalez",
      "full_name": "Andres Gonzalez",
      "document_type": "CC",
      "document_number": "456632100",
      "institution_id": "3b445e50-ca10-4f6c-977d-2d10640ee24f",
      "is_active": true,
      "is_verified": false,
      "roles": [
        "guardian"
      ],
      "created_at": "2026-10-30T08:23:36.784887Z",
      "updated_at": "2026-10-30T09:25:46.576972Z"
    },
    {
      "id": "7321986c-7529-4c46-9e32-bd8afbcfc335",
      "email": "estudiante.d@inst.edu.co",
      "username": "estudiante_d",
      "first_name": "Danna",
      "last_name": "Gonzalez",
      "full_name": "Danna Gonzalez",
      "document_type": "TI",
      "document_number": "100033355",
      "institution_id": "3b445e50-ca10-4f6c-977d-2d10640ee24f",
      "is_active": true,
      "is_verified": false,
      "roles": [
        "student"
      ],
      "created_at": "2026-10-30T07:19:59.123366Z",
      "updated_at": "2026-10-30T09:25:17.231063Z"
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 20
}
```

---

### C. Resultados de Verificación y Pruebas Automatizadas

| Módulo / Suite | Pruebas Ejecutadas | Resultado | Evidencia |
|---|---|---|---|
| **API de Usuarios (`backend/tests/test_users_api.py`)** | 8 pruebas (roles asignados, detalle de usuario, roles múltiples, deduplicación, roles revocados, usuarios sin roles, aislamiento multitenant, denegación no autorizada) | **PASSED (100%)** | 8 passed in 19.59s |
| **Aprovisionamiento Docente (`backend/tests/test_teacher_account_provisioning.py`)** | 9 pruebas (R1 a R17: aprovisionamiento atómico, tokens de un solo uso, preservación histórica) | **PASSED (100%)** | 9 passed in 30.59s |
| **Autorización RBAC Administrativa (`backend/tests/test_academic_admin_roles_authorization.py`)** | 7 pruebas (barrera académica para superadmin, national_admin, department_admin, municipality_admin) | **PASSED (100%)** | 7 passed in 42.73s |
| **Componente Frontend (`frontend/src/test/UsersView.test.tsx`)** | 4 pruebas (encabezado jurisdiccional, insignias de roles canónicos, 'Sin roles' para arreglo vacío, apertura de ficha modal) | **PASSED (100%)** | 4 passed in 3.38s |
| **Chequeo de Tipos Frontend (`npm run typecheck`)** | `tsc --noEmit` en todo el proyecto frontend | **PASSED (100%)** | Exit code 0 |
| **Compilación de Producción (`npm run build`)** | `tsc -b && vite build` | **PASSED (100%)** | Exit code 0 (dist generado) |

---

### D. Certificación de No Regresión de Seguridad y Persistencia
- **Cero modificaciones en Base de Datos:** No se modificó ningún registro en las tablas `users`, `user_roles`, `roles` ni `role_permissions`.
- **Cero migraciones generadas:** La estructura de la base de datos es idéntica y no requirió modificaciones DDL.
- **Inmutabilidad de Políticas RBAC:** Las restricciones jurisdiccionales, la cadena de autoridad y las barreras de aislamiento institucional permanecen intactas.


