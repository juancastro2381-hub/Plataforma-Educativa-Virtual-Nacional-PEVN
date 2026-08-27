# INFORME DE AUDITORÍA ARQUITECTÓNICA DE APROVISIONAMIENTO INSTITUCIONAL — FASE 3C

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN / PEVE)  
**Fase:** Fase 3C — Auditoría de Arquitectura de Aprovisionamiento Institucional  
**Tipo de Documento:** Auditoría Arquitectónica y Especificación de Diseño (Sin cambios de código)  
**Fecha:** 2026-08-25  
**Estado:** `[FASE 3C: AUDITORÍA ARQUITECTÓNICA COMPLETA — LÍNEA BASE FASE 3B PRESERVADA]`  

---

## 1. Resumen Ejecutivo (Executive Summary)

La plataforma PEVN completó y certificó con éxito la línea base de la Fase 3B (**109/109 pruebas de backend superadas, 0 fallas, 100% PASS**). Dicha línea base garantiza el aislamiento multi-inquilino (*tenant isolation*), el control de acceso basado en roles (RBAC) y la integridad de las reglas del negocio educativo (e.g., obligatoriedad de año escolar activo para matrículas).

El presente informe constituye una **auditoría de arquitectura y análisis de código estricto (Analysis Only — No Code Changes)** para determinar la solución técnica, segura y normativa del **Módulo de Aprovisionamiento Institucional y Cuentas de Rector** operado por el Administrador Nacional (Ministerio de Educación Nacional / Operador Central).

---

## 2. Arquitectura Institucional Actual (Current Institution Architecture)

### 2.1. Modelo de Dominio `Institution`
- **Archivo:** [`backend/app/models/institution.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/institution.py)
- **Tabla en Base de Datos:** `institutions` (Migración `002_phase3_academic_foundation.py`)
- **Definición de Campos:**
  - `id: UUID` (Clave Primaria, generación automática `gen_random_uuid()`).
  - `municipality_id: UUID` (FK hacia `municipalities.id`, regla `ON DELETE RESTRICT`, indexado).
  - `dane_code: String(20)` (Código DANE de 12 dígitos oficial del MEN, `unique=True`, indexado).
  - `name: String(255)` (Nombre oficial de la Institución Educativa / IED / IE).
  - `email: String(255)` (Correo electrónico institucional de contacto).
  - `phone: String(50) | None` (Teléfono de contacto, opcional).
  - `address: String(255) | None` (Dirección física de la sede central, opcional).
  - `is_active: Boolean` (Estado booleano de operatividad en la plataforma, por defecto `True`).
  - `created_at: DateTime(timezone=True)` (Auditoría de creación automática `func.now()`).
  - `updated_at: DateTime(timezone=True)` (Auditoría de última modificación `func.now()`).

### 2.2. Modelo de Dominio `Campus` (Sedes Educativas)
- **Archivo:** [`backend/app/models/institution.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/institution.py)
- **Tabla:** `campuses`
- **Definición de Campos:**
  - `id: UUID` (PK).
  - `institution_id: UUID` (FK `institutions.id`, regla `ON DELETE CASCADE`).
  - `dane_sede_code: String(20)` (Código DANE de sede, `unique=True`).
  - `name: String(255)` (Nombre de la sede, e.g. "Sede Principal", "Sede Rural El Porvenir").
  - `address: String(255) | None` (Dirección física).
  - `is_active: Boolean` (Por defecto `True`).

### 2.3. Restricciones e Invariantes de Base de Datos
1. `uq_institutions_dane_code`: Impide la duplicidad de códigos DANE institucionales en todo el territorio nacional.
2. `uq_campuses_dane_sede_code`: Impide la duplicidad de códigos DANE de sedes.
3. `fk_institutions_municipality_id`: Garantiza que toda institución pertenezca a un municipio válido y registrado en el catálogo DANE.

---

## 3. Arquitectura de Usuarios y Rol Rector (Current User/Rector Architecture)

### 3.1. Modelo `User`
- **Archivo:** [`backend/app/models/user.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/user.py)
- **Afiliación Institucional:** `User.institution_id` (FK `institutions.id`, `nullable=True`).
  - Para usuarios institucionales (Rector, Docente, Estudiante), `institution_id` contiene el UUID del colegio.
  - Para usuarios nacionales (SuperAdmin, NationalAdmin), `institution_id` es `NULL`.
- **Restricción de Identidad:** `UniqueConstraint("document_type", "document_number", name="uq_users_document")`. No pueden existir dos usuarios con el mismo tipo y número de documento.
- **Seguridad:** Contraseñas hasheadas exclusivamente con **Argon2id** (`hashed_password`).

### 3.2. Representación del Rol `RECTOR`
- **Enum en Código:** `SystemRole.RECTOR = "rector"` ([`app/core/security/interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/interfaces.py)).
- **Jerarquía:** Nivel de jerarquía `level = 50`.
- **Tabla en BD:** Registro en tabla `roles` con `name = "rector"` y `display_name = "Rector / Director"`.
- **Asociación Usuario-Rol-Institución:** Tabla `user_roles` con:
  - `user_id = <UUID_usuario>`
  - `role_id = <UUID_rol_rector>`
  - `institution_id = <UUID_institución>`
  - `is_active = True`

---

## 4. Arquitectura de Control de Acceso RBAC (Current RBAC Architecture)

El modelo de autorización de PEVN opera bajo el principio estricto de **Denegación por Defecto (Deny-by-Default)** evaluado en cuatro dimensiones:

$$\text{ACCESO PERMITIDO} \iff \begin{cases} 
\text{1. Usuario Autenticado (JWT válido)} \\
\text{2. Rol Activo en Jerarquía Suficiente} \\
\text{3. Permiso Atómico Explícito (e.g. } \texttt{academic\_years:create}\text{)} \\
\text{4. Alcance Organizacional (Scope) Válido para el Inquilino Objetivo} 
\end{cases}$$

- **Servicio Central:** `CentralizedAuthorizationService` ([`app/core/security/authorization.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py)).
- **Constructor de Contexto:** `AuthService.build_auth_context(user)` genera un `AuthorizationContext` inmutable que contiene roles activos, lista de permisos y el `OrganizationalScope`.

---

## 5. Arquitectura de Aislamiento Multi-Inquilino (Current Tenant Isolation Architecture)

1. **Barrera de Inquilino (*Tenant Isolation Boundary*):** La entidad `Institution` define la frontera de datos.
2. **Evaluación de Alcance (*Scope Containment*):**
   - Si `actor_scope.is_national() == True` $\implies$ El usuario puede operar sobre cualquier institución si especifica explícitamente el `institution_id` objetivo.
   - Si `actor_scope.institution_id == 'A'` y el recurso objetivo pertenece a `'B'` $\implies$ La solicitud es rechazada inmediatamente con **HTTP 404 Not Found** (*Blind 404 Barrier*), impidiendo la enumeración de recursos ajenos.
3. **Resolución de Contexto en Endpoints (`_resolve_institution_id`):**
   - Los endpoints institucionales resuelven la institución a partir del usuario en sesión (`current_user.institution_id`).
   - Si el usuario es de nivel Nacional (`institution_id = None`), el endpoint exige un parámetro de consulta explícito `?institution_id=<UUID>`. Si no se provee, retorna `403 Forbidden: Contexto institucional no disponible`.

---

## 6. Capacidad Actual de Administración Nacional (Current National Administration Capability)

### 6.1. Existencia del Rol
- **`SystemRole.SUPERADMIN` (Nivel 100):** Operador técnico global de la plataforma.
- **`SystemRole.NATIONAL_ADMIN` (Nivel 90):** Administrador del Ministerio de Educación Nacional.

### 6.2. Alcance Organizacional
- Ambos roles son reconocidos por `AuthService.build_auth_context` como `is_national = True`.
- `OrganizationalScope` asignado: `country_code="CO"`, `department_id=None`, `municipality_id=None`, `institution_id=None`.

### 6.3. Estado Actual de la Interfaz y Endpoints
- **Backend:** [`institutions.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py) solo contiene `GET /api/v1/institutions/me` y `GET /api/v1/institutions/{id}`.
- **Frontend:** No existen vistas ni formularios para que el Administrador Nacional liste, filtre, cree o desactive colegios ni vincule rectores desde la web.

---

## 7. Mecanismo Actual de Aprovisionamiento Institucional (Current Provisioning Mechanism)

En las Fases 1 a 4, el aprovisionamiento de instituciones y rectores se concibió como:
1. **Poblado Inicial por Migración:** Migración `002_phase3_academic_foundation.py` inicializa catálogos nacionales (grados, áreas de conocimiento estatutarias).
2. **Comandos CLI Administrativos:** Script `create_superadmin.py` para la cuenta central.
3. **Poblado de Pruebas Automatizadas:** Fixtures en `conftest.py` y suites E2E instancian `Institution`, `Campus`, `User` y `UserRole` de forma programática.
4. **Brecha Actual:** Falta la superficie API y la interfaz de usuario para que el Administrador Nacional gestione el ciclo de vida institucional desde el portal web.

---

## 8. Restricciones de Seguridad Inviolables (Security Constraints)

Cualquier módulo futuro de aprovisionamiento institucional **DEBE CUMPLIR OBLIGATORIAMENTE**:

1. **No elusión de `CentralizedAuthorizationService`:** Todo endpoint de creación debe exigir el permiso `institutions:create` y `users:create_rector`.
2. **Jerarquía Estricta:** Un Administrador Nacional (nivel 90) o SuperAdmin (nivel 100) solo puede crear roles de nivel inferior (Rector = nivel 50).
3. **Unicidad de Identificadores:** Validación atómica en base de datos del Código DANE (12 dígitos numéricos) y del documento de identidad del Rector (`uq_users_document`).
4. **Trazabilidad de Auditoría:** Registro obligatorio en `audit_logs` mediante `audit_service` para eventos `INSTITUTION_CREATED`, `RECTOR_ASSIGNED`, `RECTOR_INVITED`, `INSTITUTION_STATUS_CHANGED`.
5. **Cero Divulgación de Credenciales:** Prohibición absoluta de generar contraseñas en texto claro visibles por el Administrador Nacional o registradas en logs.

---

## 9. Brechas Arquitectónicas Identificadas (Identified Architectural Gaps)

| Componente | Estado Actual (`EXISTING`) | Elemento Faltante (`MISSING`) |
|---|---|---|
| **Servicio de Instituciones** | No existe clase de servicio (`MISSING`). Las consultas se hacen inline en los endpoints. | Se requiere un `InstitutionService` formal con lógica transaccional, validaciones DANE y auditoría. |
| **API de Instituciones** | Solo lectura (`GET /me`, `GET /{id}`). | Faltan endpoints `POST /institutions`, `GET /institutions` (listado paginado para Admin Nacional) y `PATCH /institutions/{id}/status`. |
| **Aprovisionamiento de Rector** | Creación directa en base de datos. | Falta endpoint `POST /institutions/{id}/rector` o flujo de invitación segura. |
| **Ciclo de Vida Institucional** | Booleano `is_active: bool`. | Se recomienda un enum `InstitutionStatus` (`ACTIVE`, `INACTIVE`, `SUSPENDED`, `ARCHIVED`). |
| **Frontend Nacional** | Vistas institucionales (`/academic`, `/virtual-classrooms`). | Falta la vista `/admin/institutions` para el Administrador Nacional. |

---

## 10. Flujo Recomendado de Aprovisionamiento Institucional (Recommended Provisioning Flow)

```
[ Administrador Nacional (Frontend) ]
                 │
                 ▼ POST /api/v1/admin/institutions
      [ CentralizedAuthorizationService ] ──(Exige institutions:create + Alcance Nacional)
                 │
                 ▼
        [ InstitutionService ]
                 │
        ┌────────┴──────────────────────────┐
        ▼                                   ▼
  1. Valida DANE único              2. Valida Municipio DANE
  3. Inserta Institution             4. Inserta Campus "Sede Principal"
        │                                   │
        └────────────────┬──────────────────┘
                         ▼
             [ AuditService.record() ]
        (Evento: INSTITUTION_CREATED)
                         │
                         ▼
              Retorna HTTP 201 Created
```

---

## 11. Flujo Recomendado de Onboarding del Rector (Rector Account Onboarding Flow)

### Análisis Comparativo de Opciones:
- **Opción A (Contraseña manual asignada por el Administrador):** `[NO RECOMENDADA — INSEGURA]`. Viola la privacidad de credenciales y permite que el Administrador conozca la contraseña del Rector.
- **Opción B (Contraseña temporal):** `[ACEPTABLE PERO SUBÓPTIMA]`. Requiere transmitir la contraseña temporal por canales inseguros.
- **Opción C (Invitación Segura / Enlace de Activación Tokenizado) — `[RECOMENDADA]`:
  1. El Administrador Nacional registra los datos del Rector (Nombre, Correo, Tipo/Número de Documento).
  2. El sistema crea el `User` en estado inactivo/no verificado (`is_verified = False`) y le asocia el rol `Rector` en la institución.
  3. El sistema genera un token criptográfico de un solo uso con expiración (usando la infraestructura existente `PasswordResetToken` / `InvitationToken`).
  4. Se envía un correo electrónico al Rector con el enlace de bienvenida (`/auth/accept-invitation?token=...`).
  5. El Rector define su propia contraseña segura bajo Argon2id.
  6. El usuario pasa a `is_verified = True`, `is_active = True`.
  7. **Cero fuga de credenciales.**

---

## 12. Superficie API Requerida — DISEÑO CONCEPTUAL (DESIGN ONLY)

*Nota: Ninguno de estos endpoints está implementado en la línea base actual.*

### 12.1. Gestión Institucional (Solo Administrador Nacional / SuperAdmin)
- `POST /api/v1/admin/institutions`: Crea una nueva Institución Educativa y su Sede Principal.
  - *Payload:* `dane_code`, `name`, `email`, `phone`, `address`, `municipality_id`, `main_campus_name`.
  - *Permiso:* `institutions:create`.
- `GET /api/v1/admin/institutions`: Lista paginada de instituciones con filtros por departamento, municipio, estado y búsqueda por nombre/DANE.
  - *Permiso:* `institutions:read`.
- `PATCH /api/v1/admin/institutions/{id}/status`: Modifica el estado operativo de la institución (`ACTIVE`, `SUSPENDED`, `INACTIVE`).
  - *Permiso:* `institutions:update`.

### 12.2. Gestión de Rector Institucional
- `POST /api/v1/admin/institutions/{id}/rector/invite`: Genera la invitación y registro previo del Rector.
  - *Payload:* `email`, `first_name`, `last_name`, `document_type`, `document_number`, `phone_number`.
  - *Permiso:* `users:create_rector`.
- `POST /api/v1/admin/institutions/{id}/rector/replace`: Realiza el traspaso formal de la rectoría desactivando el rol del rector anterior y vinculando al nuevo titular con registro de auditoría.
  - *Permiso:* `users:assign_role`.

---

## 13. Superficie Frontend Requerida — DISEÑO CONCEPTUAL (DESIGN ONLY)

*Nota: Ninguna de estas vistas está implementada en la línea base actual.*

1. **Ruta `/admin/institutions` (Panel de Administración Nacional de Instituciones):**
   - Tabla de colegios registrados a nivel nacional con paginación, filtros territoriales y estado.
   - Botón `+ Registrar Nueva Institución Educativa`.
2. **Modal/Formulario de Creación de Institución:**
   - Selección de Departamento $\rightarrow$ Municipio.
   - Código DANE (12 dígitos con validación de máscara).
   - Nombre de la Institución y datos de contacto.
   - Datos iniciales de la Sede Principal.
3. **Sección de Asignación y Onboarding de Rector:**
   - Formulario de datos de identidad del Rector (Cédula, Nombres, Correo Oficial).
   - Botón `Enviar Invitación de Activación`.
   - Indicador de estado de la cuenta del Rector: `Invitación Pendiente`, `Activo`, `Bloqueado`.
4. **Selector de Contexto Institucional en Barra Superior:**
   - Para el Administrador Nacional, un selector tipo dropdown con autocompletado para elegir qué institución educativa está inspeccionando activamente, inyectando el `institution_id` en las vistas de Gestión Académica.

---

## 14. Cambios Requeridos en Base de Datos — DISEÑO CONCEPTUAL (DESIGN ONLY)

*Nota: La base de datos actual ya cuenta con los modelos fundamentales. Para una fase futura de aprovisionamiento avanzado se sugieren únicamente extensiones no destructivas:*

1. **Tipo Enum de Estado Institucional:**
   ```sql
   CREATE TYPE institution_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'ARCHIVED');
   ALTER TABLE institutions ADD COLUMN status institution_status DEFAULT 'ACTIVE';
   ```
2. **Tabla de Invitaciones de Usuarios (`user_invitations`):**
   ```sql
   CREATE TABLE user_invitations (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
       institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
       token_hash VARCHAR(255) NOT NULL UNIQUE,
       expires_at TIMESTAMPTZ NOT NULL,
       is_used BOOLEAN NOT NULL DEFAULT FALSE,
       created_at TIMESTAMPTZ NOT NULL DEFAULT now()
   );
   ```

---

## 15. Requisitos de Auditabilidad (Auditability Requirements)

Todo evento del ciclo de vida de aprovisionamiento debe emitir un `AuditEvent` síncrono registrado en la tabla `audit_logs`:
- `INSTITUTION_CREATED`: Registra `actor_id` (Admin Nacional), `dane_code`, `municipality_id`.
- `INSTITUTION_STATUS_CHANGED`: Registra estado anterior, nuevo estado y motivo administrativo.
- `RECTOR_INVITED`: Registra `actor_id`, `target_user_id`, `institution_id`.
- `RECTOR_ACTIVATED`: Registra cuando el Rector completa su clave y activa su cuenta.
- `RECTOR_REPLACED`: Registra el cambio de titularidad de la rectoría institucional.

---

## 16. Matriz de Riesgos y Mitigaciones (Risks and Mitigations)

| Riesgo | Impacto | Severidad | Mitigación Arquitectónica |
|---|---|---|---|
| **Creación de Colegios Fantasma o Códigos DANE inválidos** | Alto | Alta | Validación estricta de formato DANE y validación cruzada con catálogo de municipios. |
| **Suplantación de Rector o Robo de Invitación** | Crítico | Crítica | Tokens de invitación criptográficos de alta entropía (256 bits), de un solo uso y expiración corta (24-48 horas). |
| **Escalamiento Vertical de Privilegios** | Crítico | Crítica | `CentralizedAuthorizationService` valida que un rol no pueda asignar roles de nivel $\ge$ al propio. |
| **Colisión de Documentos de Identidad** | Medio | Media | Restricción `uq_users_document` captura duplicados antes de la inserción y retorna `409 Conflict`. |

---

## 17. Mapa de Dependencias Arquitectónicas (Dependency Map)

```
[ Catálogo Territorial (DANE) ]
              │
              ▼
[ Módulo de Aprovisionamiento Institucional ] ──► [ AuditService ]
              │
              ▼
[ Creación de Sede Principal ] ──► [ Invitación Segura de Rector ]
                                                │
                                                ▼
                                  [ Activación de Rector (Argon2id) ]
                                                │
                                                ▼
                                  [ Desbloqueo de Gestión Académica (Fase 3B) ]
```

---

## 18. Secuencia Recomendada de Implementación para una Fase Futura

Si la gobernanza del proyecto aprueba la implementación del aprovisionamiento web:
1. **Paso 1:** Crear `InstitutionService` en el backend con validaciones DANE y auditoría.
2. **Paso 2:** Crear endpoints REST administrativos en `endpoints/institutions.py`.
3. **Paso 3:** Implementar el servicio y endpoints de invitación segura de usuarios (`user_invitations`).
4. **Paso 4:** Desarrollar las pruebas unitarias y de integración del servicio institucional (manteniendo el baseline 109/109 verde).
5. **Paso 5:** Desarrollar las interfaces visuales en el Frontend (`/admin/institutions` y Selector de Contexto).
6. **Paso 6:** Ejecutar pruebas de regresión completa y emitir el informe final.

---

## 19. Sección Explícita de No Implementación (NOT IMPLEMENTED)

En cumplimiento estricto de las directrices de gobernanza y del protocolo de congelamiento de línea base:

- ❌ **NO se crearon archivos de código fuente de aplicación.**
- ❌ **NO se crearon nuevos endpoints en el backend.**
- ❌ **NO se crearon pantallas ni componentes en el frontend.**
- ❌ **NO se crearon migraciones ni modificaciones en la base de datos.**
- ❌ **NO se alteraron pruebas unitarias ni suites de regresión.**
- ❌ **La totalidad de este documento es de naturaleza estrictamente analítica, arquitectónica y de diseño conceptual.**

---

```
========================================================================================
                                  PHASE 3C STATUS
========================================================================================
ARCHITECTURE AUDIT:                    COMPLETE
PRODUCTION CODE CHANGES:               0
DATABASE CHANGES:                      0
TEST SUITE CHANGES:                    0
PHASE 3B BASELINE (109/109 PASS):      PRESERVED & FROZEN
========================================================================================
```
