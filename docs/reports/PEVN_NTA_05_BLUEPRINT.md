# PEVN — NTA-05: NATIONAL ADMIN TERRITORIAL CONTROL CENTER
## ARCHITECTURE DESIGN & FORENSIC PREFLIGHT BLUEPRINT (CORRECTED)
**AI Software Factory Standard v1.2 — Read-Only Architecture Audit & Specification**

- **Document Identifier:** `docs/reports/PEVN_NTA_05_BLUEPRINT.md`
- **Execution Date:** 2026-10-06 (Corrected 2026-10-07)
- **Architecture Sentinel:** Antigravity AI Engineering & Security Systems
- **Operational Mode:** STRICT READ-ONLY AUDIT & DESIGN (0 Mutations Executed)
- **Status:** **FINAL BLUEPRINT CORRECTED — READY FOR IMPLEMENTATION AUTHORIZATION**
- **Preceding Phases:** `NTA-02` (DIVIPOLA Foundation), `NTA-03` (Catalog Architecture), `NTA-04` (Provisioning Workflow)
- **Target Implementation Phase:** `NTA-05` (Awaiting Explicit User Implementation Authorization)

---

## 1. RESUMEN EJECUTIVO Y PRINCIPIO ARQUITECTÓNICO FUNDAMENTAL

El objetivo cardinal de la **Fase NTA-05 (National Admin Territorial Control Center)** es diseñar la infraestructura unificada de monitoreo, telemetría y gobernanza territorial para la alta dirección nacional (Ministerio de Educación Nacional - MEN, Administradores Nacionales y Superadministradores de PEVN) y directores territoriales (Secretarías de Educación Departamentales - SED).

### 1.1 Principio Arquitectónico Central
Hasta la culminación de NTA-04, la plataforma PEVN consolidó con éxito:
1. La base territorial DIVIPOLA de 33 departamentos y 1,119 municipios (`NTA-02`).
2. El catálogo oficial inmutable de 18,031 establecimientos y 53,522 sedes (`NTA-03`).
3. El motor de radicación, revisión y aprovisionamiento con máquina de estados (`NTA-04`).

Sin embargo, los directivos de nivel nacional enfrentan una **brecha de visibilidad y fragmentación operativa**:
- La terminología "instituciones" se encuentra sobrecargada y confusa entre el universo oficial del catálogo (18,031), el pipeline en trámite (solicitudes NTA-04), los tenants SaaS activos (31), y los fixtures sintéticos de prueba (27).
- La analítica territorial existente (`/analytics/territorial`) reporta métricas macroscópicas simplistas que no integran el estado del flujo de aprobación ni la cobertura de administradores departamentales por Secretaría de Educación.
- Para gobernar el país educativo, un Administrador Nacional debe alternar entre cuatro vistas inconexas (`/admin/institutions`, `/admin/department-admins`, `/admin/onboarding`, y `/analytics/territorial`).

```
+----------------------------------------------------------------------------------------------------+
|                       NTA-05: CENTRO DE CONTROL TERRITORIAL NACIONAL (PEVN)                        |
+----------------------------------------------------------------------------------------------------+
                                                  |
         +----------------------------------------+----------------------------------------+
         |                                        |                                        |
         v                                        v                                        v
+------------------------+      +----------------------------------+      +------------------------+
| TIER 1: CATÁLOGO MEN   |      | TIER 2: PIPELINE NTA-04          |      | TIER 3: TENANTS PEVN   |
| 18,031 Establecimientos|      | Solicitudes en Trámite:          |      | 34 Colegios Totales    |
| (17,990 Nac + 41 Pil.) |      | SUBMITTED, UNDER_REVIEW,         |      | 31 Activos / 3 Inact.  |
| 53,522 Sedes Oficiales |      | APPROVED, REJECTED, CANCELLED    |      | 7 Reales Enlazados     |
| 33 Dptos / 1,119 Munis |      | Radicados por SED / Nacional     |      | 27 Fixtures Sintéticos |
+------------------------+      +----------------------------------+      +------------------------+
         |                                        |                                        |
         +----------------------------------------+----------------------------------------+
                                                  |
                                                  v
                               +------------------------------------+
                               | TIER 4: GOBERNANZA SED NACIONAL    |
                               | 33 Secretarías de Educación (SED)  |
                               | Cobertura de Dept Admins (10 / 33) |
                               | Matriz Departamental Interactiva   |
                               +------------------------------------+
```

### 1.2 Reglas Inviolables de NTA-05:
1. **Cero mutaciones en la fase de diseño:** No se ejecuta ningún cambio en base de datos ni código de aplicación durante esta auditoría.
2. **Cero migraciones estructurales requeridas:** Todas las entidades requeridas (`departments`, `municipalities`, `official_institution_catalog`, `institutions`, `campuses`, `institution_onboarding_requests`, `user_roles`) ya existen y están certificadas en la base de datos PostgreSQL. NTA-05 es una fase de **orquestación analítica, servicios de consulta agregada y consola directiva UX**.
3. **Preservación estricta de Anti-IDOR y Scope Organizacional:** Un Administrador Nacional ve los 33 departamentos; un Administrador Departamental accede únicamente a su departamento asignado (HTTP 403 Forbidden en caso contrario).
4. **Desambiguación semántica absoluta de las cuatro capas de datos (4-Tier Architecture):** Bajo ninguna circunstancia el UI o la API presentarán los 18,031 establecimientos del catálogo oficial como si fueran colegios operacionales desplegados en PEVN.
5. **Cero métricas departamentales cableadas (Hardcoded):** Todas las métricas mostradas en consola provienen exclusivamente de consultas en tiempo de ejecución ejecutadas contra PostgreSQL a través de la capa de servicios.

---

## 2. FASE 1 — AUDITORÍA FORENSE READ-ONLY (PREFLIGHT)

Se ejecutó una inspección forense exhaustiva de la arquitectura del repositorio y del esquema relacional:

### 2.1 Inspección de Líneas Base Certificadas
- **NTA-02 (DIVIPOLA Foundation):**
  - Migración: `backend/migrations/versions/026_nta02_national_divipola_foundation.py`.
  - Universo: 33 departamentos (código de 2 dígitos) y 1,119 municipios (código de 5 dígitos).
  - Estado: Certificado. Cero municipios huérfanos. Bogotá D.C. (`11`) y San Andrés (`88`) validados.
- **NTA-03 (Catalog ↔ Provisioning Architecture):**
  - Migración: `backend/migrations/versions/027_nta03_catalog_provisioning_architecture.py`.
  - Restricción: `uq_institutions_catalog_institution_id` (índice único parcial donde `catalog_institution_id IS NOT NULL`).
  - Universo Catálogo Canónico: **18,031 establecimientos** y 53,522 sedes en `official_institution_catalog` y `official_campus_catalog`.
    - **Lote Nacional (`a49910c2-fd62-45fa-9feb-32e82e9d063a`):** 17,990 filas válidas (18,076 crudos - 86 rechazados [79 duplicados + 7 malformados]).
    - **Lote Piloto (`33b82da7-edd9-4a71-938a-7eafaffd50c2`):** 41 filas válidas.
    - **Total canónico:** $17,990 + 41 = \mathbf{18,031}$.
  - Tenancy Actual: 34 instituciones (7 enlazadas formalmente al catálogo oficial; 27 fixtures sintéticos preservados con `catalog_institution_id = NULL`).
- **NTA-04 (National Provisioning Workflow):**
  - Migración: `backend/migrations/versions/028_nta04_national_provisioning_workflow.py`.
  - Entidad: `institution_onboarding_requests` con estados (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`, `PROVISIONED`).
  - Restricción: `uq_onboarding_active_catalog_institution` (único parcial para solicitudes activas).
  - Enrutamiento API: `/api/v1/onboarding` (`catalog`, `requests`, `review`, `approve`, `reject`, `provision`).
  - Frontend: `/admin/onboarding` (`OnboardingView.tsx`).

### 2.2 Inspección del Modelo RBAC y Alcance Organizacional (`OrganizationalScope`)
El archivo `backend/app/core/security/authorization.py` define tres niveles de alcance operacional:
1. `NATIONAL`: Otorgado a `SUPERADMIN` y `NATIONAL_ADMIN`. `is_national = True`. No posee restricciones territoriales de consulta ni mutación.
2. `DEPARTMENT`: Otorgado a `DEPARTMENT_ADMIN`. Posee `department_id` no nulo en `user_roles`. Restringe consultas a instituciones, municipios y solicitudes cuyo `department_id` o `department_code` coincida.
3. `INSTITUTION`: Otorgado a `RECTOR`, `TEACHER`, `STUDENT`, `GUARDIAN`. Restringido a `institution_id`.

### 2.3 Inspección de Servicios Analíticos Actuales
En `backend/app/services/territorial_analytics_service.py`:
- `get_national_summary(scope)`:
  - Calcula `dept_count`, `mun_count`, `cat_inst_count` (18,031), `prov_inst_count` (solo activas: 31), `cat_campus_count` (53,522), `active_students`, `active_teachers`, `active_groups`, sector oficial vs no oficial, y zona urbana vs rural.
  - **Limitación identificada:** No reporta instituciones inactivas (3), no reporta fixtures sintéticos (27), no reporta métricas del pipeline de onboarding NTA-04 (`SUBMITTED`, `UNDER_REVIEW`, `APPROVED`), y no reporta cobertura de directores departamentales (Secretarías de Educación con o sin administrador).
- `get_department_distribution(scope)`:
  - Realiza un `GROUP BY OfficialInstitutionCatalog.department_code`.
  - **Limitación identificada:** No incluye el estado de asignación del Administrador Departamental ni el total de trámites en curso.

### 2.4 Inspección del Modelo `Campus` y Terminología Operacional
Inspección forense en `backend/app/models/institution.py` (líneas 122–168):
```python
class Campus(Base):
    __tablename__ = "campuses"
    id: Mapped[uuid.UUID] = ...
    institution_id: Mapped[uuid.UUID] = ...
    dane_sede_code: Mapped[str] = ...
    name: Mapped[str] = ...
    address: Mapped[str | None] = ...
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="Whether the campus is active."
    )
```
**Conclusión Forense de Terminología:**
- El modelo `Campus` **SÍ contiene el atributo de estado booleano `is_active`**.
- La consulta de base de datos `SELECT count(*) FROM campuses;` arroja **18 sedes aprovisionadas totales**.
- La consulta con predicado `SELECT count(*) FROM campuses WHERE is_active = true;` arroja **18 sedes operacionales activas**.
- Para eliminar cualquier ambigüedad, la arquitectura formaliza las métricas:
  - `provisioned_campuses`: Total de sedes aprovisionadas en la plataforma (`SELECT count(*) FROM campuses;` = 18).
  - `active_operational_campuses`: Sedes aprovisionadas con estado activo (`SELECT count(*) FROM campuses WHERE is_active = true;` = 18).

---

## 3. FASE 2 — DETERMINACIÓN DEL PROPÓSITO DE NTA-05

### 3.1 Problema que Resuelve NTA-05
Actualmente, los directivos de PEVN y del Ministerio de Educación carecen de un panel ejecutivo unificado que responda de forma instantánea a las preguntas críticas del despliegue nacional:
1. *¿Cuál es la tasa real de incorporación del catálogo nacional a PEVN por departamento?*
2. *¿Cuántas solicitudes de colegios están estancadas en revisión técnica territorial?*
3. *¿Qué Secretarías de Educación Departamentales (SED) carecen de Administrador Departamental designado y requieren nombramiento urgente?*
4. *¿Cuál es el conteo exacto y diferenciado entre colegios reales incorporados y fixtures sintéticos de prueba?*

### 3.2 Capacidad de Negocio que Introduce NTA-05
**"Centro de Control Territorial Nacional (Territorial Command Center)"**:
- Una consola ejecutiva y directiva de mando unificado para `superadmin` y `national_admin`.
- Tarjetas de indicadores de 4 niveles (*4-Tier Disambiguated Metrics*):
  - **Tier 1 (Catálogo Oficial Nacional):** 18,031 establecimientos (17,990 nacionales + 41 piloto), 53,522 sedes oficiales, 33 departamentos, 1,119 municipios.
  - **Tier 2 (Pipeline NTA-04 en Trámite):** Solicitudes radicadas (`SUBMITTED`), en revisión (`UNDER_REVIEW`), aprobadas (`APPROVED`), aprovisionadas (`PROVISIONED`), rechazadas (`REJECTED`).
  - **Tier 3 (Tenancy SaaS Operacional):** 34 instituciones totales (31 activas, 3 inactivas; 7 reales vinculadas al catálogo oficial, 27 fixtures sintéticos de prueba). Sedes operacionales activas (18).
  - **Tier 4 (Gobernanza Territorial SED):** 33 departamentos, cobertura de directores departamentales (10 cubiertos, 23 vacantes), porcentaje de cobertura nacional.
- Matriz interactiva de los 33 departamentos calculada 100% en tiempo de ejecución con semaforización de cobertura, enlaces de navegación directa y desglose municipal.
- Modo de visualización adaptativa: si accede un `department_admin`, la vista se focaliza automáticamente en su jurisdicción departamental como "Centro de Control Territorial Departamental".

### 3.3 Qué NO Debe Intentar Resolver NTA-05
- **No es una herramienta de edición de catálogos:** Los registros oficiales continúan siendo inmutables.
- **No es una herramienta de sincronización masiva abierta:** La sincronización de catálogos pertenece al subsistema NTA-01/NTA-03.
- **No es un sistema de radicación de matrículas ni gestión académica:** Es un panel de control y gobernanza territorial e institucional.
- **No reemplaza a `OnboardingView.tsx`:** NTA-05 enlaza hacia `OnboardingView` con filtros preconfigurados, pero no replica los formularios de radicación ni aprobación técnica.

---

## 4. FASE 3 — DISEÑO DEL FLUJO FUNCIONAL (WORKFLOW DESIGN)

### 4.1 Actores y Permisos

| Actor / Rol | Alcance Territorial | Permisos Requeridos | Capacidades en el Centro de Control |
| :--- | :--- | :--- | :--- |
| `superadmin` | Nacional (33 Depts) | `institutions:read`, `analytics:read`, `users:read` | Control total, visualización de los 33 departamentos, fixtures sintéticos, reasignaciones y enlaces de gestión. |
| `national_admin` | Nacional (33 Depts) | `institutions:read`, `analytics:read` | Supervisión nacional, matriz de 33 departamentos, monitoreo de pipeline y enlaces de aprovisionamiento. |
| `department_admin` | Departamental (1 Dept) | `institutions:read`, `analytics:read` | Vista contextualizada a su departamento: métricas de su SED, municipios locales, solicitudes en trámite locales. Acceso a departamentos ajenos bloqueado (HTTP 403 Forbidden). |

### 4.2 Arquitectura del Flujo de Datos

```
[Cliente Frontend: /admin/control-center]
                     |
                     | GET /api/v1/analytics/territorial/control-center
                     v
[API Gateway / Router: app/api/v1/endpoints/analytics.py]
                     |
                     | 1. Valida Token JWT & AuthContext
                     | 2. Evalúa OrganizationalScope (NATIONAL vs DEPARTMENT)
                     v
[Servicio de Dominio: TerritorialAnalyticsService]
                     |
                     +---> Query Tier 1: DIVIPOLA & Catálogo Oficial (18,031 / 53,522)
                     +---> Query Tier 2: Pipeline de Solicitudes NTA-04 (Contadores por Estado)
                     +---> Query Tier 3: Tenancy PEVN (31 Activos, 3 Inactivos, 7 Reales, 27 Fixtures, 18 Sedes)
                     +---> Query Tier 4: Cobertura SED (Admins Asignados vs Vacantes por Dept)
                     |
                     +---> Escribe Evento de Auditoría Asíncrono (TERRITORIAL_CONTROL_CENTER_ACCESSED)
                     v
[Respuesta JSON Unificada: TerritorialControlCenterResponse]
                     |
                     v
[Renderizado React: 4-Tier KPI Grid + Matriz 33 Departamentos + Acciones Rápidas]
```

---

## 5. FASE 4 — ANÁLISIS Y DISEÑO DE SEGURIDAD

### 5.1 Garantías de Seguridad Arquitectónica
- **Anti-IDOR Estricto:** La resolución de departamento no confía en parámetros de consulta no autenticados. Si un usuario tiene rol `department_admin`, el servicio extrae imperativamente el `department_id` desde su sesión criptográfica en base de datos (`user_roles.department_id`). Cualquier intento de inyectar `?department_code=XX` ajeno a su jurisdicción resulta en un `403 FORBIDDEN` inmediato.
- **Aislamiento Multitenant:** Los identificadores internos y tokens de invitación nunca son expuestos de forma insegura en respuestas agregadas.
- **Auditabilidad Inmutable de Peticiones GET:**
  - El evento `TERRITORIAL_CONTROL_CENTER_ACCESSED` se emite como la **ÚNICA operación de escritura** generada por la petición.
  - La auditoría es estrictamente lateral y no muta ninguna entidad de catálogo, onboarding, instituciones, usuarios ni territorio.
  - El fallo eventual en la emisión de auditoría se gestiona en bloque transaccional seguro y **NUNCA genera un bypass de autorización**.
  - El payload de auditoría registra obligatoriamente: `user_id`, `created_at` (UTC), `ip_address` (donde esté disponible), `scope_level` aplicado, y `jurisdiction_name`.
  - En accesos de Administradores Departamentales, se registra el alcance departamental forzado por el sistema, ignorando cualquier parámetro malicioso supplied por el cliente.
  - **Cero datos sensibles:** Queda terminantemente prohibido almacenar contraseñas, tokens de invitación, hashes o credenciales en el detalle del log de auditoría.
  - **Idempotencia y Trazabilidad:** Cada petición incluye un `correlation_id` / `request_id` único para correlacionar la telemetría sin riesgo de colisión ni contención de escritura en la tabla `audit_logs`.

### 5.2 Matriz de Amenazas y Mitigaciones (Threat Model)

| ID | Amenaza | Recurso Afectado | Escenario de Ataque | Mitigación Técnica | Capa de Aplicación | Caso de Prueba |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **THR-01** | Burlar Scope Departamental (Cross-Department IDOR) | `/analytics/territorial/control-center` | Un Admin de Cundinamarca pasa `?department_code=08` (Atlántico) esperando ver datos reservados de otra SED. | El backend ignora parámetros de query para roles departamentales y sobreescribe con el `department_id` del token JWT verificado. Si se solicita explícitamente otro, aborta con HTTP 403. | Backend / Service Layer & Dependency Injection | `test_04_department_admin_cannot_access_foreign_control_center` |
| **THR-02** | Confusión de Métricas Catálogo vs Tenancy | Métricas de Gobierno | Un directivo o auditor confunde los 18,031 colegios del catálogo con colegios que usan activamente PEVN. | Desambiguación tipada estricta: los campos JSON se denominan explícitamente `total_establishments` (18,031) vs `total_institutions` (34). | Schema / Data Contract | `test_05_metrics_4tier_disambiguation_integrity` |
| **THR-03** | Exposición de Fixtures Sintéticos como Despliegue Real | Reportes del MEN | Directivos consideran las 27 instituciones de prueba como infraestructura real desplegada en Cundinamarca. | Separación explícita de `catalog_linked_institutions` (7) y `synthetic_fixture_institutions` (27) en el payload JSON y en los badges de la UI. | Domain Service & Frontend | `test_06_synthetic_fixture_isolation_in_reporting` |
| **THR-04** | Degradación de Rendimiento por Agregación Masiva | Base de datos PostgreSQL | Múltiples consultas simultáneas al Centro de Control realizan escaneos completos de 18,031 filas y 53,522 sedes. | Consultas agregadas optimizadas utilizando los índices existentes (`ix_official_inst_dept`, `ix_campuses_institution_id`, `ix_onboarding_dept_status`). | Database Indexes | `test_07_control_center_query_execution_time` |
| **THR-05** | Fuga de Credenciales en Logs de Auditoría | `/audit_logs` | El payload de auditoría del acceso captura parámetros sensibles de la cabecera o sesión. | Filtrado estricto en el servicio de auditoría: solo se persisten identificadores de contexto público (ID, IP, Scope, Jurisdicción). Cero tokens o credenciales. | Audit Service | `test_12_audit_log_emission_sanitization` |

---

## 6. FASE 5 — IMPACTO EN EL MODELO DE DATOS

### 6.1 Evaluación de Esquema: ¡CERO MIGRACIONES REQUERIDAS!
Se concluye formalmente que **NTA-05 NO requiere nuevas tablas, ni nuevas columnas, ni nuevos índices, ni migraciones de base de datos**.

Las tablas existentes soportan completamente los requerimientos:
1. `departments`: Contiene los 33 departamentos (`id`, `code`, `name`).
2. `municipalities`: Contiene los 1,119 municipios vinculados por `department_id`.
3. `official_institution_catalog`: Contiene los 18,031 registros con `department_code`.
4. `official_campus_catalog`: Contiene las 53,522 sedes enlazadas.
5. `institutions`: Contiene los 34 tenants con `municipality_id`, `is_active`, y `catalog_institution_id`.
6. `campuses`: Contiene las 18 sedes con `institution_id`, `dane_sede_code`, e `is_active`.
7. `institution_onboarding_requests`: Contiene todas las solicitudes con `department_id` y `status`.
8. `user_roles`: Contiene los roles `DEPARTMENT_ADMIN` con su `department_id`.
9. `department_admin_invitations`: Contiene las invitaciones departamentales en trámite.

### 6.2 Tipos de Auditoría (Audit Events)
Se define la adición en memoria del enum de auditoría en `backend/app/audit/interfaces.py`:
- `TERRITORIAL_CONTROL_CENTER_ACCESSED`: Registro de acceso de supervisión al panel territorial.

---

## 7. FASE 6 — DISEÑO DE LA API REST (API CONTRACT)

### 7.1 Endpoints Propuestos

#### Endpoint 1: `GET /api/v1/analytics/territorial/control-center`
- **Propósito:** Obtener el estado consolidado de los 4 niveles de telemetría y la matriz de los 33 departamentos.
- **Seguridad:** Requiere permiso `institutions:read` o `analytics:read`. Roles autorizados: `superadmin`, `national_admin`, `department_admin`.
- **Alcance:**
  - `NATIONAL`: Retorna los indicadores consolidados de todo el país y la lista completa de los 33 departamentos.
  - `DEPARTMENT`: Retorna los indicadores limitados a su departamento y una lista de 1 departamento (el propio).

#### Estructura del Esquema de Respuesta: `TerritorialControlCenterResponse`

```python
class Tier1CatalogMetrics(BaseModel):
    total_departments: int = Field(..., description="Cantidad de departamentos en catálogo DIVIPOLA calculada en runtime (Línea base observada: 33)")
    total_municipalities: int = Field(..., description="Cantidad de municipios en catálogo DIVIPOLA calculada en runtime (Línea base observada: 1,119)")
    total_establishments: int = Field(..., description="Establecimientos oficiales canónicos calculados en runtime (Línea base observada: 18,031 [17,990 nacional + 41 piloto])")
    total_campuses: int = Field(..., description="Sedes educativas oficiales en catálogo calculadas en runtime (Línea base observada: 53,522)")
    official_sector_count: int = Field(..., description="Instituciones oficiales (públicas) calculadas en runtime")
    non_official_sector_count: int = Field(..., description="Instituciones privadas calculadas en runtime")
    urban_zone_count: int = Field(..., description="Establecimientos en zona urbana calculados en runtime")
    rural_zone_count: int = Field(..., description="Establecimientos en zona rural calculados en runtime")

class Tier2PipelineMetrics(BaseModel):
    total_requests: int = Field(..., description="Total de radicados en el flujo NTA-04 calculados en runtime")
    submitted: int = Field(..., description="Solicitudes radicadas pendientes de revisión calculadas en runtime")
    under_review: int = Field(..., description="Solicitudes en revisión técnica calculadas en runtime")
    approved: int = Field(..., description="Solicitudes aprobadas pendientes de aprovisionar calculadas en runtime")
    provisioned: int = Field(..., description="Solicitudes aprovisionadas exitosamente calculadas en runtime")
    rejected: int = Field(..., description="Solicitudes rechazadas calculadas en runtime")
    cancelled: int = Field(..., description="Solicitudes canceladas calculadas en runtime")

class Tier3TenancyMetrics(BaseModel):
    total_institutions: int = Field(..., description="Total de tenants registrados en PEVN calculados en runtime (Línea base observada: 34)")
    active_institutions: int = Field(..., description="Tenants activos operacionalmente calculados en runtime (Línea base observada: 31)")
    inactive_institutions: int = Field(..., description="Tenants inactivos o suspendidos calculados en runtime (Línea base observada: 3)")
    catalog_linked_institutions: int = Field(..., description="Tenants reales enlazados al catálogo MEN calculados en runtime (Línea base observada: 7)")
    synthetic_fixture_institutions: int = Field(..., description="Tenants sintéticos de prueba/regresión con catalog_institution_id = NULL calculados en runtime (Línea base observada: 27)")
    provisioned_campuses: int = Field(..., description="Total de sedes aprovisionadas en PEVN calculadas vía SELECT count(*) FROM campuses (Línea base observada: 18)")
    active_operational_campuses: int = Field(..., description="Sedes aprovisionadas activas calculadas vía SELECT count(*) FROM campuses WHERE is_active = true (Línea base observada: 18)")
    total_users: int = Field(..., description="Total de usuarios operacionales calculados dinámicamente en runtime desde PostgreSQL (Línea base observada: 200)")
    active_students: int = Field(..., description="Estudiantes con matrícula activa calculados en runtime")
    active_teachers: int = Field(..., description="Docentes vinculados a instituciones calculados en runtime")

class Tier4GovernanceMetrics(BaseModel):
    total_departments: int = Field(..., description="Jurisdicciones departamentales calculadas en runtime (Línea base observada: 33)")
    department_admin_users_count: int = Field(..., description="Usuarios distintos con asignación activa de rol DEPARTMENT_ADMIN (Línea base observada: 10)")
    covered_departments: int = Field(..., description="Departamentos con al menos una asignación activa de Administrador Departamental (Línea base observada: 10)")
    vacant_departments: int = Field(..., description="Departamentos sin ninguna asignación activa de Administrador Departamental (Línea base observada: 23)")
    pending_invitations: int = Field(..., description="Invitaciones de Dept Admin en curso calculadas en runtime")
    coverage_percentage: float = Field(..., description="Porcentaje de cobertura de gobernanza SED calculado en runtime sobre departamentos (covered_departments / total_departments * 100)")

class DepartmentMatrixRow(BaseModel):
    department_id: uuid.UUID
    department_code: str
    department_name: str
    governance_status: str  # "COVERED", "INVITED", "VACANT"
    admin_name: str | None
    admin_email: str | None
    total_establishments: int
    total_campuses: int
    pipeline_in_progress: int  # SUBMITTED + UNDER_REVIEW + APPROVED
    active_institutions: int
    inactive_institutions: int
    provisioning_rate_percent: float

class TerritorialControlCenterResponse(BaseModel):
    scope_level: str  # "NATIONAL" o "DEPARTMENT"
    jurisdiction_name: str
    tier1_catalog: Tier1CatalogMetrics
    tier2_pipeline: Tier2PipelineMetrics
    tier3_tenancy: Tier3TenancyMetrics
    tier4_governance: Tier4GovernanceMetrics
    department_matrix: list[DepartmentMatrixRow]
    computed_at: datetime
```

#### Endpoint 2: `GET /api/v1/analytics/territorial/control-center/departments/{department_code}`
- **Propósito:** Retorna el desglose exhaustivo de un departamento específico para el drawer/modal de inspección territorial detallada (incluye lista de municipios con contadores de catálogo y tenants).
- **Seguridad:** Requiere `institutions:read`. Si el usuario es `department_admin`, `department_code` debe coincidir estrictamente con su territorio asignado; de lo contrario, responde `403 Forbidden`.

---

## 8. FASE 7 — DISEÑO DE LA EXPERIENCIA DE USUARIO (UX / FRONTEND)

### 8.1 Ubicación y Navegación
- **Ruta Frontend:** `/admin/control-center` (montada en `App.tsx` y enlazada en el menú principal de navegación para `superadmin`, `national_admin`, y `department_admin`).
- **Título de Página:** `Centro de Control Territorial Nacional | PEVN Presidencia & MEN` (para Nacional) / `Centro de Control Territorial — SED {Departamento}` (para Departamental).

### 8.2 Estructura Visual del Tablero (Wireframe Textual)

> [!IMPORTANT]
> **AVISO DE VALORES ILUSTRATIVOS:**
> Todos los valores numéricos y nombres presentados en el wireframe a continuación son **ESTRICTAMENTE ILUSTRATIVOS** con fines de diseño de interfaz. La implementación futura **NUNCA DEBE CABLEAR (HARDCODE)** estos valores. Todas las métricas, nombres de administradores y contadores territoriales se calculan e inyectan **100% en tiempo de ejecución (RUNTIME)** directamente desde PostgreSQL mediante la capa de servicios.

```
====================================================================================================
 [🏛️ PEVN COLOMBIA]  CENTRO DE CONTROL TERRITORIAL NACIONAL           [Rol: SUPERADMIN] [Logout]
 Monitoreo y Gobernanza del Despliegue Educativo Digital
 Jurisdicción: República de Colombia | Cobertura: 33/33 Departamentos | Catálogo Oficial: 18,031
 [VALORES EN TIEMPO REAL CARGADOS DINÁMICAMENTE DESDE POSTGRESQL — NUNCA HARDCODEADOS]
====================================================================================================

[CUADRÍCULA DE 4 NIVELES DE TELEMETRÍA (4-TIER KPI MATRIX)]
+-----------------------------+-----------------------------+-----------------------------+-----------------------------+
| TIER 1: CATÁLOGO OFICIAL    | TIER 2: PIPELINE EN TRÁMITE | TIER 3: TENANTS PEVN        | TIER 4: GOBERNANZA SED      |
| [Total Catálogo Dinámico]   | [Total Radicados Dinámico]  | 34 Colegios Totales         | [SEDs Cubiertas Dinámico]   |
| [Total Sedes Dinámico]      | • Radicadas (Nuevas): N     | • 31 Activos Operacionales  | [SEDs Vacantes Dinámico]    |
| 33 Depts / 1,119 Municipios | • En Revisión Técnica: N    | • 3 Inactivos / Suspendidos | Cobertura Nacional: N%      |
| 🏛️ Oficial | 🏢 Privado     | • Aprobados p/ Aprovision: N| 🔗 7 Reales | 🧪 27 Fixtures | [Gestionar Secretarías]     |
+-----------------------------+-----------------------------+-----------------------------+-----------------------------+

[ACCIONES RÁPIDAS DIRECTIVAS]
 [ + Radicar Onboarding ]    [ 👥 Administradores SED ]    [ 🏫 Colegios Operacionales ]    [ 📥 Exportar Reporte ]

----------------------------------------------------------------------------------------------------
[MATRIZ TERRITORIAL DE COLOMBIA (33 DEPARTAMENTOS CALCULADA DINÁMICAMENTE)]
Filtros: [Buscar departamento / DANE...] [Estado SED: Todos v] [Con Tenants v]  [Descargar CSV]
----------------------------------------------------------------------------------------------------
CÓDIGO | DEPARTAMENTO   | GOBERNANZA SED     | CATÁLOGO OFICIAL | ONBOARDING | TENANTS PEVN | COBERTURA | ACCIONES
-------+----------------+--------------------+------------------+------------+--------------+-----------+--------------------
05     | ANTIOQUIA      | [Estado Dinámico]  | [Catálogo Dpto]  | [En curso] | [Tenants]    | [Tasa %]  | [Ver] [Onboarding]
08     | ATLÁNTICO      | [Estado Dinámico]  | [Catálogo Dpto]  | [En curso] | [Tenants]    | [Tasa %]  | [Ver] [Colegios]
11     | BOGOTÁ D.C.    | [Estado Dinámico]  | [Catálogo Dpto]  | [En curso] | [Tenants]    | [Tasa %]  | [Ver] [Colegios]
13     | BOLÍVAR        | [Estado Dinámico]  | [Catálogo Dpto]  | [En curso] | [Tenants]    | [Tasa %]  | [Asignar Admin]
25     | CUNDINAMARCA   | [Estado Dinámico]  | [Catálogo Dpto]  | [En curso] | [Tenants]    | [Tasa %]  | [Ver] [Colegios]
...    | (Total: 33)    | [Agregado Runtime] | 18,031 Canónico  | [Total ONB]| 34 Totales   | [Prom %]  | 
----------------------------------------------------------------------------------------------------
* NOTA: Cada celda de la tabla se genera dinámicamente mediante la API sin valores quemados en código frontend.
```

### 8.3 Comportamiento Responsivo e Interactividad
1. **Filtro Inmediato:** Búsqueda reactiva por nombre o código DANE sin recargar la página.
2. **Drawer de Detalle Departamental:** Al hacer clic en `[Ver]`, se abre un panel lateral con los municipios del departamento seleccionado, permitiendo ver qué municipios tienen colegios aprovisionados y cuáles están pendientes.
3. **Botones de Conexión Cruzada:**
   - Botón `[Onboarding]`: Redirige a `/admin/onboarding?dept={id}` filtrando el catálogo en ese departamento.
   - Botón `[Asignar Admin]`: Redirige a `/admin/department-admins` abriendo el modal de creación con el departamento preseleccionado.
   - Botón `[Colegios]`: Redirige a `/admin/institutions?department={id}`.

---

## 9. FASE 8 — ESTRATEGIA DE PRUEBAS AUTOMATIZADAS (TEST STRATEGY)

Para garantizar la confiabilidad absoluta de la implementación futura de NTA-05, se especifica una suite dedicada de pruebas en `backend/tests/test_nta05_territorial_control_center.py` con una matriz de 15 pruebas estructuradas:

### 9.1 Matriz de Pruebas Propuesta

| Identificador | Clasificación | Propósito del Test | Criterio de Aceptación |
| :--- | :--- | :--- | :--- |
| `TEST-01` | Happy Path / National | Consulta nacional por `superadmin`. | HTTP 200, `scope_level == "NATIONAL"`, 33 departamentos en matriz, 18,031 catálogo, 34 tenants. |
| `TEST-02` | Happy Path / National Admin | Consulta nacional por `national_admin`. | HTTP 200, mismos contadores consolidados que superadmin. |
| `TEST-03` | Happy Path / Department Admin | Consulta por `department_admin` de Cundinamarca. | HTTP 200, `scope_level == "DEPARTMENT"`, matriz contiene exactamente 1 fila (Cundinamarca). |
| `TEST-04` | Anti-IDOR / Cross-Dept | `department_admin` intenta consultar departamento ajeno vía URL. | HTTP 403 Forbidden. Cero fuga de métricas ajenas. |
| `TEST-05` | Disambiguation / 4-Tier | Verificación matemática de las 4 capas usando nombres canónicos del contrato. | `tier1_catalog.total_establishments == 18031`, `tier3_tenancy.total_institutions == 34 (31 activos + 3 inactivos)`, `tier3_tenancy.catalog_linked_institutions == 7`, `tier3_tenancy.synthetic_fixture_institutions == 27`. |
| `TEST-06` | SED Governance Coverage (Active Assignments) | Verificación del cálculo de gobernanza SED basado exclusivamente en asignaciones activas de administradores departamentales (`role.name = 'department_admin'`, `user_roles.department_id IS NOT NULL`, `user_roles.is_active = TRUE`). | Contadores exactos con semántica de asignación activa: `department_admin_users_count == 10`, `covered_departments == 10`, `vacant_departments == 23`, `total_departments == 33`, `coverage_percentage == 30.3`. |
| `TEST-07` | Pipeline State Integrity | Verificación de contadores de solicitudes NTA-04. | La suma de estados en Tier 2 coincide exactamente con `count(*) from institution_onboarding_requests`. |
| `TEST-08` | Department Detail Endpoint | Consulta de desglose municipal de un departamento válido. | HTTP 200, lista de municipios con contadores de catálogo y tenants. |
| `TEST-09` | Department Detail IDOR | `department_admin` intenta consultar detalle municipal de otro departamento. | HTTP 403 Forbidden. |
| `TEST-10` | Role Isolation | Usuarios con roles institucionales (`rector`, `teacher`, `student`) intentan acceder a `/control-center`. | HTTP 403 Forbidden. |
| `TEST-11` | Unauthenticated Access | Petición anónima sin token JWT. | HTTP 401 Unauthorized. |
| `TEST-12` | Audit Log Emission | Emisión de evento de auditoría tras consulta exitosa y sanitización de credenciales. | Registro en `audit_logs` con `TERRITORIAL_CONTROL_CENTER_ACCESSED`. Cero datos sensibles persistidos. |
| `TEST-13` | Baseline Invariance | Verificación de que la consulta no ejecutó ninguna inserción ni mutación en entidades de dominio. | Conteos de base de datos idénticos antes y después. |
| `TEST-14` | Regression NTA-02 | Verificación de los 33 departamentos y 1,119 municipios. | Cero huérfanos, 100% preservados. |
| `TEST-15` | Regression NTA-03 / NTA-04 | Ejecución de suite de regresión completa (98 pruebas anteriores). | **98/98 PASS, 0 fallos.** |

---

## 10. FASE 9 — CONTRATO DE REGRESIÓN E INVARIANTES ABSOLUTAS

La implementación de NTA-05 suscribe un contrato inviolable de **no regresión**.

### 10.1 Contrato Estricto de Preservación de Pruebas
- Las **98 pruebas automatizadas previas** certificadas en NTA-02, NTA-03 y NTA-04 **DEBEN PERMANECER INTACTAS**.
- Queda terminantemente prohibido borrarlas, debilitarlas, renombrarlas para eludir su ejecución o modificarlas para acomodar NTA-05.
- La aceptación de la futura implementación exige obligatoriamente:
  $$\mathbf{98 / 98 \text{ Pruebas Previas PASS}} + \mathbf{15 / 15 \text{ Pruebas NTA-05 PASS}} = \mathbf{113 / 113 \text{ Pruebas Totales PASS}}$$
- Cualquier falla individual en la suite previa o nueva constituirá un bloqueo inmediato (`BLOCKED`).

### 10.2 Invariantes de Datos en PostgreSQL

> [!NOTE]
> **PRESERVACIÓN DE LÍNEA BASE EXCLUSIVAMENTE PARA DOCUMENTACIÓN Y PRUEBAS:**
> Los valores numéricos reflejados en esta tabla (33 departamentos, 1,119 municipios, 18,031 catálogo, 53,522 sedes, 34 tenants [31 activos, 3 inactivos, 7 enlazados, 27 sintéticos], 18 sedes operacionales [18 activas], 200 usuarios totales y 10 administradores departamentales) corresponden a la línea base certificada para auditoría, trazabilidad, aserciones en pruebas de regresión e informes forenses.
> 
> **BAJO NINGUNA CIRCUNSTANCIA estos valores constituyen valores por defecto (fallback defaults) en esquemas, modelos o servicios en tiempo de ejecución.** La implementación debe calcular cada uno de estos valores de manera 100% dinámica desde PostgreSQL (incluyendo el total de 200 usuarios y las métricas de sedes). Cero valores de base de datos quemados en el código.

| Invariante del Sistema | Valor Esperado Inmutable | Mecanismo de Verificación Forense |
| :--- | :---: | :--- |
| Departamentos DIVIPOLA | **33** | `SELECT count(*) FROM departments;` |
| Municipios DIVIPOLA | **1,119** | `SELECT count(*) FROM municipalities;` |
| Municipios Huérfanos | **0** | `SELECT count(*) FROM municipalities WHERE department_id IS NULL;` |
| Establecimientos Catálogo Oficial | **18,031** | `SELECT count(*) FROM official_institution_catalog;` |
| Sedes Oficiales en Catálogo | **53,522** | `SELECT count(*) FROM official_campus_catalog;` |
| Tenants Institucionales PEVN | **34** | `SELECT count(*) FROM institutions;` |
| Tenants Activos en PEVN | **31** | `SELECT count(*) FROM institutions WHERE is_active = true;` |
| Tenants Inactivos / Suspendidos | **3** | `SELECT count(*) FROM institutions WHERE is_active = false;` |
| Tenants Reales Enlazados al Catálogo | **7** | `SELECT count(*) FROM institutions WHERE catalog_institution_id IS NOT NULL;` |
| Fixtures Sintéticos de Prueba | **27** | `SELECT count(*) FROM institutions WHERE catalog_institution_id IS NULL;` |
| Sedes Operacionales Aprovisionadas | **18** | `SELECT count(*) FROM campuses;` |
| Sedes Operacionales Activas | **18** | `SELECT count(*) FROM campuses WHERE is_active = true;` |
| Usuarios Operacionales Totales | **200** | `SELECT count(*) FROM users;` (Calculado dinámicamente) |
| Usuarios Admin Departamental Activos | **10** | `SELECT count(DISTINCT u.id) FROM users u JOIN user_roles ur ON u.id = ur.user_id JOIN roles r ON ur.role_id = r.id WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL AND ur.is_active = true;` |
| Departamentos Cubiertos (SED con Admin Activo) | **10** | `SELECT count(DISTINCT ur.department_id) FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL AND ur.is_active = true;` |
| Departamentos Vacantes (SED sin Admin Activo) | **23** | `SELECT count(d.id) FROM departments d WHERE d.id NOT IN (SELECT DISTINCT ur.department_id FROM user_roles ur JOIN roles r ON ur.role_id = r.id WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL AND ur.is_active = true);` |
| Lote Nacional de Catálogo (`a49910c2`) | **17,990** | `SELECT count(*) FROM official_institution_catalog WHERE sync_batch_id = 'a49910c2...';` |
| Lote Piloto de Catálogo (`33b82da7`) | **41** | `SELECT count(*) FROM official_institution_catalog WHERE sync_batch_id = '33b82da7...';` |
| Pruebas de Regresión Anteriores | **98 / 98 PASS** | `pytest tests/ -k "not test_nta05"` |

---

## 11. FASE 10 — LÍMITES DE IMPLEMENTACIÓN (BOUNDARIES)

### 11.1 Requerido para NTA-05 (En Alcance Estricto)
1. Creación de esquemas Pydantic `TerritorialControlCenterResponse` y modelos asociados en `backend/app/schemas/analytics.py`.
2. Extensión de `TerritorialAnalyticsService` con `get_territorial_control_center(scope)` y método de detalle municipal departamental.
3. Incorporación de endpoints REST en `backend/app/api/v1/endpoints/analytics.py` (`/control-center` y `/control-center/departments/{code}`).
4. Registro de evento de auditoría `TERRITORIAL_CONTROL_CENTER_ACCESSED` en `backend/app/audit/interfaces.py`.
5. Creación de la vista interactiva `frontend/src/pages/admin/TerritorialControlCenterView.tsx`.
6. Montaje de la ruta `/admin/control-center` en `frontend/src/App.tsx` y enlace directivo en `RootLayout.tsx`.
7. Suite de pruebas automatizadas `tests/test_nta05_territorial_control_center.py` (15 pruebas).

### 11.2 Opcional / Futuro (No Bloqueante para NTA-05)
- Exportación del tablero en formato PDF oficial para reportes al Congreso o Presidencia.
- Mapas SVG interactivos de la geografía de Colombia con renderizado vectorial por departamento.

### 11.3 Fuera de Alcance (Out of Scope)
- Edición de nombres o códigos DANE en el catálogo.
- Migraciones de datos o cambios en el esquema de PostgreSQL.
- Alteración de roles o permisos en la base de datos.
- Modificación del flujo de Onboarding NTA-04 o de aprobación técnica.

### 11.4 Requiere Autorización Exclusiva del Usuario
- El paso de esta fase de diseño a la fase de implementación de código.

### 11.5 Prohibido Implementar (Forbidden)
- Crear territorio en caliente (ad-hoc runtime DIVIPOLA insertion).
- Permitir a un `department_admin` consultar métricas de departamentos ajenos.
- Ocultar o borrar los 27 fixtures sintéticos en lugar de desambiguarlos.
- Quemar (hardcodear) métricas departamentales en el código frontend.

---

## 12. FASE 11 — RECOMENDACIÓN GO / NO-GO Y PLAN DE EJECUCIÓN

### 12.1 Dictamen de Preparación (Readiness Assessment)
**NTA-05 READINESS: READY FOR IMPLEMENTATION**
*(Condicionado estrictamente a la recepción de la autorización formal y explícita del usuario).*

### 12.2 Alcance Exacto de Implementación Futura

#### Archivos a Crear / Modificar:
1. `backend/app/schemas/analytics.py` (Modificado — Adición de esquemas de Control Center).
2. `backend/app/services/territorial_analytics_service.py` (Modificado — Consultas optimizadas de agregación 4-Tier y matriz de 33 departamentos).
3. `backend/app/api/v1/endpoints/analytics.py` (Modificado — Endpoints `/control-center`).
4. `backend/app/audit/interfaces.py` (Modificado — Evento `TERRITORIAL_CONTROL_CENTER_ACCESSED`).
5. `frontend/src/types/analytics.ts` (Modificado o creado — Tipos TypeScript para el Centro de Control).
6. `frontend/src/services/analytics.ts` (Modificado — Método `getControlCenter()`).
7. `frontend/src/pages/admin/TerritorialControlCenterView.tsx` (Creado — Consola directiva unificada).
8. `frontend/src/App.tsx` (Modificado — Registro de ruta `/admin/control-center`).
9. `backend/tests/test_nta05_territorial_control_center.py` (Creado — 15 pruebas automatizadas).

#### Migraciones Esperadas:
- **0 migraciones** (El esquema de datos relacional existente satisface el 100% de los requerimientos).

#### Suite de Regresión Requerida:
- 15 nuevas pruebas NTA-05 + 98 pruebas preexistentes = **113 pruebas totales** con 0 fallos.

#### Orden de Ejecución Recomendado al Autorizarse:
1. **Paso 1:** Contratos de datos (Pydantic schemas y TypeScript types).
2. **Paso 2:** Servicio de dominio analítico y consultas SQL agregadas seguras.
3. **Paso 3:** Controlador API REST con inyección de `OrganizationalScope` y Anti-IDOR.
4. **Paso 4:** Suite de pruebas backend (15 pruebas unitarias/integración).
5. **Paso 5:** Vista frontend (`TerritorialControlCenterView.tsx`) y montaje de rutas.
6. **Paso 6:** Validación cruzada en navegador y prueba de regresión completa (113/113 PASS).
7. **Paso 7:** Reporte final de implementación y certificación NTA-05.

---

## 13. CERTIFICADO MANDATORIO DE CONSISTENCIA FINAL (FINAL CONSISTENCY CERTIFICATE)

```
============================================================
NTA-05 BLUEPRINT FINAL CONSISTENCY CERTIFICATE
============================================================

STATUS:
PASS — FINAL GOVERNANCE CONTRACT VERIFIED

DATABASE MUTATIONS:
0

CODE IMPLEMENTATION:
0

MIGRATIONS EXECUTED:
0

RECORDS INSERTED:
0

RECORDS UPDATED:
0

RECORDS DELETED:
0

TENANTS MODIFIED:
0

HARDCODED TERRITORIAL METRICS:
0

LEGACY METRIC ALIASES REMAINING:
0

ACTIVE DEPARTMENT ADMIN SEMANTICS:
VERIFIED

NTA-02:
PRESERVED (33 Depts, 1,119 Munis, 0 Orphans)

NTA-03:
PRESERVED (18,031 Catalog, 53,522 Campuses, 7 Linked, 27 Fixtures)

NTA-04:
PRESERVED (Workflow Engine, State Machine, OnboardingView, 98/98 Tests Pass)

NTA-05:
BLUEPRINT COMPLETE — READY FOR EXPLICIT USER IMPLEMENTATION AUTHORIZATION

NEXT ACTION:
AWAITING EXPLICIT USER IMPLEMENTATION AUTHORIZATION

STOP.
============================================================
```

---
*Fin del Documento de Especificación Arquitectónica Corregido NTA-05.*
