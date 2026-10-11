# PEVN — Auditoría Técnica de Cumplimiento de Alcance Territorial
## Evaluación Forense de Scope Runtime para el Rol `DEPARTMENT_ADMIN`

**Fecha:** 5 de Octubre de 2026  
**Entorno:** Staging / Local Certified Baseline  
**Cuenta Auditada:** `department_admin` (`department_admin@pevn.edu.co`)  
**Rol RBAC Asignado:** `department_admin` (Nivel Jerárquico: 80)  
**Jurisdicción Esperada:** Código DANE 11 — CAPITAL BOGOTÁ, D.C.  
**Estado del Gate:** **`FAIL`** *(Defecto real de autorización y aislamiento territorial en lecturas; mutaciones estrictamente bloqueadas por RBAC)*

---

## 1. Resumen Ejecutivo y Veredicto de Gate

Durante la validación manual del usuario `department_admin` provisionado para la Secretaría de Educación Distrital de Bogotá (DANE 11), se detectó que la interfaz gráfica (UI) y las respuestas de la API reflejaban un alcance territorial **Nacional**:
- **Dashboard UI:** *"Nivel de Alcance: Nacional (Todo el Territorio)"*
- **Tablero de Analítica Territorial:** *"Jurisdicción: República de Colombia"* | *"Alcance: NATIONAL"*

### Veredicto del Gate de Certificación
```
========================================================================================
GATE STATUS: FAIL
========================================================================================
Motivo: El usuario DEPARTMENT_ADMIN puede acceder a través de la API a instituciones y
usuarios correspondientes a departamentos distintos al suyo (acceso cross-department).
El alcance NATIONAL no es un defecto cosmético de frontend ni un valor por defecto
hardcodeado en React: es emitido activamente por el backend (/api/v1/auth/me y
/api/v1/analytics/territorial/summary) debido a una omisión estructural en la
persistencia y propagación del OrganizationalScope.
========================================================================================
```

### Hallazgos Clave de Seguridad
1. **Mutaciones Protegidas (RBAC 100% Intacto):**  
   El usuario posee exactamente 17 permisos atómicos, todos de lectura (`:read`). Cualquier intento de mutación, creación, actualización o promoción administrativa (`POST /institutions`, `PATCH /institutions/{id}/status`, `POST /catalog/sync`, `POST /catalog/promotion/authorize`) es rechazado de inmediato con **`403 Forbidden` (`PERMISSION_DENIED`)**.
2. **Defecto de Aislamiento en Lectura (Cross-Department Leakage):**  
   Debido a que `department_id`, `municipality_id` e `institution_id` son `None`, el método `scope.is_national()` evalúa a `True`. En consecuencia, el motor de autorización (`scope_contains`) considera al usuario con alcance nacional, permitiéndole listar y consultar registros institucionales de Antioquia, Cundinamarca u otros departamentos.

---

## 2. Trazabilidad Completa del Flujo de Autorización y Scope

```
[1. LOGIN] POST /api/v1/auth/login
       │
       ▼
[2. AUTHENTICATE] AuthService.authenticate_user()
       │  Verifica credenciales Argon2id y carga User + UserRole
       ▼
[3. TOKEN EMISSION] TokenService.create_access_token()
       │  Claims emitidos: {"sub": user_id, "username": "...", "roles": ["department_admin"], "institution_id": null}
       │  *NOTA*: No existe claim 'department_id' ni 'department_code' en el JWT.
       ▼
[4. CURRENT USER] GET /api/v1/auth/me -> deps.get_current_user()
       │  Carga entidad User de la base de datos
       ▼
[5. RBAC & SCOPE RESOLUTION] AuthService.build_auth_context(user)
       │  • active_roles = [SystemRole.DEPARTMENT_ADMIN]
       │  • permissions = 17 permisos canónicos (:read)
       │  • is_national = any(r in {SUPERADMIN, NATIONAL_ADMIN}) -> False
       │  • user.institution_id -> None
       │  • scope = OrganizationalScope(country_code="CO", department_id=None, municipality_id=None, institution_id=None)
       │  *CRÍTICO*: scope.department_id se inicializa HARDCODEADO en None.
       ▼
[6. SCOPE EVALUATION] OrganizationalScope.is_national()
       │  self.department_id is None and self.municipality_id is None and self.institution_id is None
       │  -> EVALÚA A TRUE (Defecto semántico de fallback)
       ▼
[7. BACKEND SERVICE AUTHORIZATION]
       │  • scope_contains(actor_scope, target_scope):
       │      if actor_scope.is_national(): return True  <-- Omite validación de frontera departamental
       │  • TerritorialAnalyticsService.get_national_summary(scope):
       │      if scope.is_national(): return "scope_level": "NATIONAL", "jurisdiction_name": "República de Colombia"
       ▼
[8. API RESPONSES]
       │  • GET /api/v1/auth/me -> scope.is_national: true
       │  • GET /api/v1/analytics/territorial/summary -> scope_level: "NATIONAL", jurisdiction: "República de Colombia"
       │  • GET /api/v1/institutions -> Retorna instituciones de TODOS los departamentos (33 registradas)
       ▼
[9. FRONTEND RENDERING]
          • Dashboard.tsx: user.scope.is_national ? 'Nacional (Todo el Territorio)' : 'Institucional'
          • TerritorialAnalyticsView.tsx: summary.jurisdiction_name ("República de Colombia")
```

---

## 3. Fuentes Exactas del Scope y Discrepancias

### 3.1. Origen del Scope `NATIONAL` Visualizado
* **Archivo:** [`backend/app/services/auth_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py#L86-L92)
  ```python
  scope = OrganizationalScope(
      country_code="CO",
      department_id=None,
      municipality_id=None,
      institution_id=None if is_national else institution_id_str,
      campus_id=None,
  )
  ```
* **Archivo:** [`backend/app/core/security/interfaces.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/interfaces.py#L117-L123)
  ```python
  def is_national(self) -> bool:
      """True if the scope covers all institutions in the country."""
      return (
          self.department_id is None
          and self.municipality_id is None
          and self.institution_id is None
      )
  ```
  Al ser `institution_id=None` (propio de administradores territoriales que no pertenecen a un colegio individual) y al no existir asignación de `department_id`, la condición `is_national()` retorna `True`.

### 3.2. Origen del Scope `DEPARTMENT 11`
* **Persistencia Real:** Durante el aprovisionamiento mediante [`backend/app/cli/create_department_admin.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/create_department_admin.py#L154-L160), el código DANE 11 fue almacenado **únicamente en los metadatos del registro de auditoría (`audit_logs.metadata`)**.
* **Base de Datos Operativa:** Ni la tabla `users` ni la tabla `user_roles` cuentan con una columna `department_id` o `department_code`. Por lo tanto, el departamento 11 no existe en la identidad relacional del usuario a nivel de base de datos transaccional.

---

## 4. Relevancia de Componentes Técnicos Auditados

### 4.1. Claims de Sesión y Token JWT
* **Claims actuales emitidos:**
  ```json
  {
    "sub": "dd44ceb4-f5ca-4b5c-a801-0b4490125258",
    "username": "department_admin",
    "roles": ["department_admin"],
    "institution_id": null,
    "type": "access",
    "exp": 1728160000
  }
  ```
* **Diagnóstico:** El token no contiene claims relativos al territorio (`department_id`, `department_code`).

### 4.2. Funciones y Servicios de Autorización Backend
1. **`CentralizedAuthorizationService.authorize()`** ([`authorization.py:75`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py#L75)):  
   Valida primero permisos granulares (17 de lectura). Pasa exitosamente. Luego invoca `scope_contains()`.
2. **`scope_contains(actor_scope, target_scope)`** ([`authorization.py:30`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/authorization.py#L30)):  
   Línea 49: `if actor_scope.is_national(): return True`. Al evaluar a True, autoriza de manera incondicional cualquier `target_scope` institucional o departamental.
3. **`TerritorialAnalyticsService.get_national_summary()`** ([`territorial_analytics_service.py:86`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/territorial_analytics_service.py#L86)):  
   Evalúa `if scope.is_national():` antes que `if scope.is_department():`, ejecutando la consulta agregada de la República de Colombia.

### 4.3. Endpoints de API Relevantes
* `GET /api/v1/auth/me`: Retorna `scope.is_national = true`.
* `GET /api/v1/analytics/territorial/summary`: Retorna métricas nacionales en vez de métricas de Bogotá D.C.
* `GET /api/v1/analytics/territorial/departments`: Retorna todos los 45 departamentos en vez de filtrar por Bogotá D.C.
* `GET /api/v1/institutions`: No aplica restricción obligatoria por departamento si el actor posee `scope.is_national() == True`.
* `GET /api/v1/institutions/{id}`: Permite lectura directa de colegios fuera de Bogotá D.C.

### 4.4. Esquema de Base de Datos y Filtros SQL
* **Campos existentes:**
  - `users`: `id`, `email`, `username`, `institution_id` (NULL), `first_name`, `last_name`, `document_type`, `document_number`, `is_active`, `is_verified`...
  - `user_roles`: `id`, `user_id`, `role_id`, `institution_id` (NULL), `campus_id` (NULL), `is_active`...
  - `departments`: `id`, `code`, `name`
* **Campos ausentes:** No existe `department_id` en `users` ni en `user_roles`.
* **Filtros SQL ejecutados:**
  - En `list_institutions`:  
    `SELECT institutions.* FROM institutions WHERE institutions.department_id = :dept_id` solo se activa si el cliente envía manualmente el query param `department_id`. Si no se envía, se ejecuta `SELECT * FROM institutions LIMIT 20` sin filtro territorial.

---

## 5. Resultados de las 10 Pruebas de Seguridad Obligatorias

Todas las pruebas fueron ejecutadas directamente contra el backend mediante cliente HTTP autenticado con el token real de la cuenta `department_admin`:

| # | Prueba de Seguridad | Endpoint / Operación | Resultado Obtenido | Estado | Observación Forense |
|---|-------------------|----------------------|--------------------|--------|---------------------|
| **TEST 1** | Lectura de instituciones en Dpto 11 (Bogotá) | `GET /api/v1/institutions?department_id=7b77...` | **HTTP 200 OK** (32 instituciones) | **ALLOWED** | Autorizado bajo permiso `institutions:read`. |
| **TEST 2** | Lectura de instituciones en otro departamento (Cundinamarca 25) | `GET /api/v1/institutions?department_id=9aea...` y `GET /api/v1/institutions` sin filtro | **HTTP 200 OK** (1 institución en Cundinamarca / 33 total nacional) | **FAIL (UNRESTRICTED)** | La cuenta pudo consultar instituciones fuera de Bogotá por falta de filtro forzado en backend. |
| **TEST 3** | Enumeración de todos los departamentos | `GET /api/v1/analytics/territorial/departments` | **HTTP 200 OK** (45 registros departamentales devueltos) | **ALLOWED** | Permiso `institutions:read` permite la llamada, pero debería acotarse al Dpto 11 según el diseño del servicio. |
| **TEST 4** | Acceso directo por ID a institución fuera de Bogotá (Cundinamarca) | `GET /api/v1/institutions/1fb1a84a-4647...` | **HTTP 200 OK** (`COL CRISTIANO INTEGRAL`) | **FAIL (UNRESTRICTED)** | `scope_contains` permitió el acceso cross-tenant porque `is_national()` fue True. |
| **TEST 5** | Modificación de institución fuera de Bogotá | `PATCH /api/v1/institutions/1fb1a84a.../status` | **HTTP 403 Forbidden** (`PERMISSION_DENIED`) | **DENIED** | Bloqueado por RBAC: el rol carece de `institutions:update`. |
| **TEST 6** | Modificación de institución dentro de Bogotá | `PATCH /api/v1/institutions/2dcc7e47.../status` | **HTTP 403 Forbidden** (`PERMISSION_DENIED`) | **DENIED** | Bloqueado por RBAC: el rol carece de permisos de mutación operativa. |
| **TEST 7** | Acceso a operaciones reservadas de `NATIONAL_ADMIN` | `POST /api/v1/institutions` y `POST /api/v1/institutions/catalog/sync` | **HTTP 403 Forbidden** (`PERMISSION_DENIED`) | **DENIED** | Bloqueado por RBAC: carece de `institutions:create`. |
| **TEST 8** | Acceso a operaciones de `SUPER_ADMIN` | `POST /api/v1/institutions/catalog/promotion/authorize` | **HTTP 403 Forbidden** (`PERMISSION_DENIED`) | **DENIED** | Bloqueado por RBAC: carece de permisos y rol SuperAdmin. |
| **TEST 9** | Verificación de presentación en Frontend | `GET /api/v1/auth/me` | **HTTP 200 OK** (`scope.is_national = true`) | **CONFIRMED BACKEND SOURCE** | La UI no hardcodea `NATIONAL`; reproduce fidedignamente el payload del backend. |
| **TEST 10** | Inspección directa de Analítica Territorial | `GET /api/v1/analytics/territorial/summary` | **HTTP 200 OK** (`scope_level: "NATIONAL"`, `jurisdiction_name: "República de Colombia"`) | **CLASSIFICATION: F** | El backend ignora el alcance departamental porque `scope.department_id` no fue provisto en la sesión. |

---

## 6. Clasificación de Riesgo

* **Clasificación Global:** **`MEDIUM-HIGH`**
* **Vector de Ataque:** Falla de Aislamiento Territorial en Operaciones de Lectura (Confidentiality / Multi-Tenancy Boundary).
* **Integridad (Mutaciones):** **`SECURE` (Riesgo Bajo)**. No hay riesgo de manipulación de datos entre departamentos porque `department_admin` carece absolutamente de permisos de escritura o mutación (17 permisos estrictamente de solo lectura).
* **Confidencialidad (Lecturas):** **`EXPOSED` (Riesgo Medio-Alto)**. Permite a un administrador departamental listar colegios y enumerar usuarios de otras entidades territoriales certificadas (por ejemplo, `GET /api/v1/users` retornó 189 usuarios nacionales).

---

## 7. Plan de Remediación Mínima Recomendado (Propuesta Técnica)

> [!IMPORTANT]
> En estricto cumplimiento de las directivas, **no se ha modificado ningún archivo de código ni base de datos**. La siguiente propuesta describe la remediación mínima requerida para someter a aprobación antes de su implementación.

### Diagnóstico de la Brecha
El modelo relacional soporta pertenencia institucional (`institution_id`) pero no soporta pertenencia departamental ni municipal para administradores territoriales (`department_admin`, `municipality_admin`). Al ser `institution_id = NULL`, el sistema confunde la ausencia de colegio con alcance nacional.

### Plan de 3 Pasos Mínimos

1. **Persistencia de Alcance Territorial:**
   * Agregar columna opcional `department_id: UUID | None` (Foreign Key a `departments.id`) en `user_roles` (o en `users`).
   * Alternativamente, vincular en `user_roles.department_id` para permitir delegaciones territoriales por rol.

2. **Resolución en `AuthService.build_auth_context`:**
   * Modificar la construcción de `OrganizationalScope` para asignar:
     ```python
     department_id = str(user_role.department_id) if user_role and user_role.department_id else None
     ```
   * Si el rol es `DEPARTMENT_ADMIN`, poblar `scope.department_id`.

3. **Cierre de Frontera en Endpoints y Filtros:**
   * En `list_institutions`: Si `auth.scope.is_department()`, forzar que la consulta SQL filtre obligatoriamente por `department_id = auth.scope.department_id`, ignorando o rechazando peticiones que intenten consultar otros departamentos.
   * En `TerritorialAnalyticsService`: Ya implementa soporte nativo para `if scope.is_department():` ([línea 195](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/territorial_analytics_service.py#L195)); al recibir `scope.department_id = "11"` (o el UUID correspondiente), resolverá automáticamente:
     - `scope_level = "DEPARTMENT"`
     - `jurisdiction_name = "CAPITAL BOGOTÁ, D.C."`
     - Métricas acotadas a las 32 instituciones y municipios de Bogotá.

---

## 8. Conclusión

El rol `department_admin` cumple a cabalidad con el principio de mínimo privilegio en lo concerniente a permisos atómicos (17 permisos de lectura certificados, cero mutaciones). Sin embargo, el gate de certificación de alcance territorial no puede darse por cerrado en `PASS` debido a que la frontera de lectura no está acotada al Departamento 11.

**Estado Final para el Comité de Certificación:**
`GATE STATUS: FAIL` — A la espera de autorización para implementar la remediación mínima de alcance territorial.
