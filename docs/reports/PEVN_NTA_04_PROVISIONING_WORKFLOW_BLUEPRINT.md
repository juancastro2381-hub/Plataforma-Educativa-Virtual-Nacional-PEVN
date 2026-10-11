# PEVN — NTA-04: NATIONAL PROVISIONING WORKFLOW
## ARCHITECTURE DESIGN & FORENSIC PREFLIGHT BLUEPRINT
**AI Software Factory Standard v1.2 — Read-Only Architecture Audit & Specification**

- **Document Identifier:** `docs/reports/PEVN_NTA_04_PROVISIONING_WORKFLOW_BLUEPRINT.md`
- **Execution Date:** 2026-10-06
- **Architecture Sentinel:** Antigravity AI Engineering & Security Systems
- **Operational Mode:** STRICT READ-ONLY AUDIT & DESIGN (0 Mutations Executed)
- **Status:** **DESIGN CERTIFIED — READY FOR AUTHORIZATION**
- **Preceding Phase:** `NTA-03` (Certified PASS — Catalog ↔ Provisioning Architecture)
- **Target Implementation Phase:** `NTA-04` (Pending Explicit User Authorization)

---

## 1. RESUMEN EJECUTIVO Y PRINCIPIO ARQUITECTÓNICO FUNDAMENTAL

El objetivo cardinal de la **Fase NTA-04 (National Provisioning Workflow)** es establecer y formalizar la máquina de estados y el flujo de trabajo controlado que transforma un establecimiento educativo oficial del catálogo nacional del Ministerio de Educación Nacional (MEN / DUE) y DANE (DIREDU) en un tenant institucional operacional con gobernanza territorial y rectoral en PEVN.

```
+-------------------------------------------------------------------------+
|                  UNIVERSO DE REFERENCIA OFICIAL                         |
|         official_institution_catalog (18,031 Establecimientos)          |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    SOLICITUD DE APROVISIONAMIENTO                       |
|           institution_onboarding_requests (DRAFT / SUBMITTED)           |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     GOBERNANZA Y AUTORIZACIÓN                           |
|        Territorial / National Review (UNDER_REVIEW / APPROVED)          |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    APROVISIONAMIENTO DE TENANT                          |
|         institutions + campuses (catalog_institution_id linked)         |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    DESIGNACIÓN DE AUTORIDAD RECTORAL                    |
|      rector_invitations (SHA-256 Token / Inactive Pre-Registration)     |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    COLEGIO OPERACIONAL ACTIVO EN PEVN                   |
+-------------------------------------------------------------------------+
```

### Reglas Inviolables de Separación:
1. **El catálogo oficial es estrictamente de lectura y referencia.** Nunca se convierte automáticamente un registro del catálogo en tenant de PEVN.
2. **El tenant de PEVN es una entidad SaaS operacional.** Representa una comunidad educativa viva, con sus sedes, rector, coordinadores, docentes, estudiantes y acudientes.
3. **Cero creación de territorio en tiempo de ejecución.** Todo aprovisionamiento consume la jerarquía DIVIPOLA ya establecida en NTA-02 (33 departamentos, 1,119 municipios).
4. **Aislamiento Anti-IDOR territorial absoluto.** Un Administrador Departamental no puede solicitar, revisar, autorizar ni aprovisionar instituciones fuera de su jurisdicción territorial oficial (HTTP 403 Forbidden).

---

## 2. AUDITORÍA FORENSE DEL MODELO DE DATOS ACTUAL

A la fecha de cierre de NTA-03, la base de datos operacional (`pevn_db` PostgreSQL 16) presenta el siguiente estado estructural verificado:

### 2.1 Tablas Relevantes y Restricciones Vigentes

| Tabla | Clave Primaria | Clave de Negocio / Única | Claves Foráneas Relevantes | Restricciones & Índices |
| :--- | :--- | :--- | :--- | :--- |
| `official_institution_catalog` | `id` (UUID) | `dane_code` (VARCHAR(12), UNIQUE) | Ninguna (Catálogo maestro) | `ix_official_inst_dane`, `ix_official_inst_dept`, `ix_official_inst_muni` |
| `institutions` | `id` (UUID) | `dane_code` (VARCHAR(20), UNIQUE) | `municipality_id` $\to$ `municipalities.id` (RESTRICT)<br>`catalog_institution_id` $\to$ `official_institution_catalog.id` (SET NULL) | `uq_institutions_catalog_institution_id` (`WHERE catalog_institution_id IS NOT NULL`)<br>`ix_institutions_dane_code` |
| `campuses` | `id` (UUID) | `dane_sede_code` (VARCHAR(20)) | `institution_id` $\to$ `institutions.id` (CASCADE) | `ix_campuses_institution_id`, `ix_campuses_dane_sede_code` |
| `departments` | `id` (UUID) | `code` (VARCHAR(10), UNIQUE) | Ninguna | 33 registros (32 departamentos + Bogotá D.C.) |
| `municipalities` | `id` (UUID) | `code` (VARCHAR(10), UNIQUE) | `department_id` $\to$ `departments.id` (CASCADE) | 1,119 registros (Cero huérfanos) |
| `users` | `id` (UUID) | `email`, `username` (UNIQUE) | `institution_id` $\to$ `institutions.id` (CASCADE, nullable) | 200 usuarios operacionales |
| `user_roles` | `id` (UUID) | Compuesta lógica | `user_id` $\to$ `users.id`<br>`role_id` $\to$ `roles.id`<br>`department_id` $\to$ `departments.id` | 10 Department Admins con `department_id` asignado y auditado |
| `rector_invitations` | `id` (UUID) | `token_hash` (VARCHAR(64), UNIQUE) | `institution_id` $\to$ `institutions.id`<br>`user_id` $\to$ `users.id`<br>`invited_by_id` $\to$ `users.id` | Tokens efímeros SHA-256 (Expiración 48h, de un solo uso) |
| `department_admin_invitations` | `id` (UUID) | `token_hash` (VARCHAR(64), UNIQUE) | `department_id` $\to$ `departments.id`<br>`user_id` $\to$ `users.id` | Tokens efímeros SHA-256 (Expiración 48h, de un solo uso) |

### 2.2 Hallazgo Estructural (Gap Previo a NTA-04)
Actualmente, el endpoint `POST /api/v1/institutions` ejecuta una inserción directa y desregulada sin máquina de estados intermedia:
- Solo admite solicitudes directas de nivel nacional (`NATIONAL_ADMIN` o `SUPERADMIN`).
- No existe trazabilidad formal de "solicitud territorial $\to$ revisión técnica $\to$ visto bueno $\to$ aprovisionamiento".
- Los administradores departamentales (`DEPARTMENT_ADMIN`) carecen de una interfaz y de endpoints para solicitar o impulsar el onboarding de los colegios de su Secretaría de Educación.

---

## 3. ESPECIFICACIÓN DE LA ENTIDAD `institution_onboarding_requests`

Para gobernar el ciclo de vida de aprovisionamiento, NTA-04 introducirá la entidad formal `InstitutionOnboardingRequest`.

### 3.1 Diccionario de Datos Propuesto

```python
class OnboardingRequestStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PROVISIONED = "PROVISIONED"
```

| Columna | Tipo de Dato | Nulo | Descripción / Regla de Integridad |
| :--- | :--- | :---: | :--- |
| `id` | `UUID` | NO | Clave primaria (`gen_random_uuid()`). |
| `request_number` | `VARCHAR(32)` | NO | Código de radicado amigable y único (ej. `ONB-2026-00042`). |
| `catalog_institution_id` | `UUID` | NO | FK $\to$ `official_institution_catalog.id` (`ON DELETE RESTRICT`). |
| `dane_code` | `VARCHAR(12)` | NO | Código DANE oficial de 12 dígitos del establecimiento. Indexado. |
| `department_id` | `UUID` | NO | FK $\to$ `departments.id` (`ON DELETE RESTRICT`). Jurisdicción territorial. |
| `municipality_id` | `UUID` | NO | FK $\to$ `municipalities.id` (`ON DELETE RESTRICT`). Municipio sede principal. |
| `requested_by_id` | `UUID` | NO | FK $\to$ `users.id` (`ON DELETE RESTRICT`). Usuario solicitante. |
| `requester_role` | `VARCHAR(50)` | NO | Rol del solicitante al momento de radicar (`DEPARTMENT_ADMIN`, `NATIONAL_ADMIN`). |
| `status` | `VARCHAR(30)` | NO | Estado de la máquina de estados (default: `SUBMITTED`). Indexado. |
| `institution_id` | `UUID` | SÍ | FK $\to$ `institutions.id` (`ON DELETE SET NULL`). Se enlaza al aprovisionar. |
| `contact_email` | `VARCHAR(255)` | NO | Correo institucional oficial designado para la institución en PEVN. |
| `contact_phone` | `VARCHAR(50)` | SÍ | Teléfono de contacto institucional. |
| `proposed_rector_name` | `VARCHAR(255)` | SÍ | Nombre del rector propuesto para encadenar invitación inmediata. |
| `proposed_rector_email` | `VARCHAR(255)` | SÍ | Correo electrónico del rector propuesto para despacho de credenciales. |
| `proposed_rector_doc_type`| `VARCHAR(20)` | SÍ | Tipo de documento (`CC`, `CE`). |
| `proposed_rector_doc_num` | `VARCHAR(50)` | SÍ | Número de documento del rector. |
| `justification` | `TEXT` | SÍ | Justificación administrativa del requerimiento. |
| `reviewed_by_id` | `UUID` | SÍ | FK $\to$ `users.id` (`ON DELETE SET NULL`). Revisor técnico asignado. |
| `reviewed_at` | `TIMESTAMPTZ` | SÍ | Fecha/hora de inicio de revisión. |
| `review_notes` | `TEXT` | SÍ | Observaciones o hallazgos técnicos durante la revisión. |
| `approved_by_id` | `UUID` | SÍ | FK $\to$ `users.id` (`ON DELETE SET NULL`). Autoridad que aprobó la solicitud. |
| `approved_at` | `TIMESTAMPTZ` | SÍ | Fecha/hora de aprobación formal. |
| `rejected_by_id` | `UUID` | SÍ | FK $\to$ `users.id` (`ON DELETE SET NULL`). Autoridad que rechazó la solicitud. |
| `rejected_at` | `TIMESTAMPTZ` | SÍ | Fecha/hora del rechazo. |
| `rejection_reason` | `TEXT` | SÍ | Causal formal y obligatoria de rechazo administrativo. |
| `cancelled_by_id` | `UUID` | SÍ | FK $\to$ `users.id` (`ON DELETE SET NULL`). Quien desistió de la solicitud. |
| `cancelled_at` | `TIMESTAMPTZ` | SÍ | Fecha/hora de cancelación. |
| `cancellation_reason` | `TEXT` | SÍ | Motivo del desistimiento. |
| `provisioned_by_id` | `UUID` | SÍ | FK $\to$ `users.id` (`ON DELETE SET NULL`). Operador que ejecutó la creación. |
| `provisioned_at` | `TIMESTAMPTZ` | SÍ | Fecha/hora exacta de creación del tenant en `institutions`. |
| `lock_version` | `INTEGER` | NO | Control de concurrencia optimista (default: `0`). |
| `idempotency_key` | `VARCHAR(64)` | SÍ | Llave de idempotencia provista por el cliente para prevenir dobles envíos. |
| `created_at` | `TIMESTAMPTZ` | NO | `server_default=func.now()`. |
| `updated_at` | `TIMESTAMPTZ` | NO | `server_default=func.now(), onupdate=func.now()`. |

### 3.2 Restricciones e Índices Mandatorios en PostgreSQL
1. **Índice Único Parcial Anti-Duplicados Activos:**
   ```sql
   CREATE UNIQUE INDEX uq_onboarding_active_catalog_institution
   ON institution_onboarding_requests (catalog_institution_id)
   WHERE status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED');
   ```
   *Garantía Matemática:* Es físicamente imposible que existan dos solicitudes activas simultáneas para la misma institución del catálogo. Solo si una solicitud es `REJECTED` o `CANCELLED` queda habilitado el catálogo para radicar una nueva.
2. **Índice Compuesto de Desempeño Territorial:**
   ```sql
   CREATE INDEX ix_onboarding_department_status
   ON institution_onboarding_requests (department_id, status);
   ```
3. **Índice de Radicado Único:**
   ```sql
   CREATE UNIQUE INDEX uq_onboarding_request_number
   ON institution_onboarding_requests (request_number);
   ```

---

## 4. MÁQUINA DE ESTADOS (LIFECYCLE STATE MACHINE)

```
                       +-------------------+
                       |       DRAFT       |
                       +-------------------+
                         |               |
               (submit)  |               | (cancel)
                         v               v
                   +-----------+   +-----------+
                   | SUBMITTED |   | CANCELLED | (Terminal)
                   +-----------+   +-----------+
                     |   |   |
     (take review)   |   |   | (reject)
     +---------------+   |   +-----------------------+
     |                   | (direct approve)          |
     v                   v                           v
+--------------+   +----------+                +----------+
| UNDER_REVIEW |-->| APPROVED |                | REJECTED | (Terminal)
+--------------+   +----------+                +----------+
     |                   |                           ^
     | (reject)          | (provision)               |
     +-------------------+---------------------------+
                         v
                  +-------------+
                  | PROVISIONED | (Terminal - Tenant Creado)
                  +-------------+
```

### 4.1 Matriz de Transiciones Formales

| Estado Origen | Estado Destino | Acción | Rol Autorizado | Condiciones & Validaciones |
| :--- | :--- | :--- | :--- | :--- |
| **NONE** | `DRAFT` | `create_draft` | `DEPARTMENT_ADMIN`, `NATIONAL_ADMIN` | Colegio del catálogo no debe tener tenant ni solicitud activa. |
| **NONE** | `SUBMITTED` | `submit_direct` | `DEPARTMENT_ADMIN`, `NATIONAL_ADMIN` | Datos de contacto completos; validación DIVIPOLA territorial. |
| `DRAFT` | `SUBMITTED` | `submit_draft` | Creador de la solicitud, `NATIONAL_ADMIN` | Validación de campos obligatorios (`contact_email`). |
| `DRAFT` | `CANCELLED` | `cancel_draft` | Creador de la solicitud, `NATIONAL_ADMIN` | Desistimiento voluntario. |
| `SUBMITTED` | `UNDER_REVIEW` | `start_review` | `DEPARTMENT_ADMIN` (su depto), `NATIONAL_ADMIN` | Asigna `reviewed_by_id = actor.id`, fija `reviewed_at`. |
| `SUBMITTED` | `APPROVED` | `approve_direct`| `NATIONAL_ADMIN`, `SUPERADMIN` | Visto bueno inmediato sin etapa intermedia de revisión. |
| `SUBMITTED` | `REJECTED` | `reject_request`| `DEPARTMENT_ADMIN` (su depto), `NATIONAL_ADMIN` | Requiere `rejection_reason` no vacío ($\ge 10$ caracteres). |
| `SUBMITTED` | `CANCELLED` | `cancel_request`| Creador de la solicitud | Desistimiento antes de revisión. |
| `UNDER_REVIEW` | `APPROVED` | `approve_review`| `DEPARTMENT_ADMIN` (su depto), `NATIONAL_ADMIN` | Dictamen favorable de revisión. |
| `UNDER_REVIEW` | `REJECTED` | `reject_review` | `DEPARTMENT_ADMIN` (su depto), `NATIONAL_ADMIN` | Requiere `rejection_reason` formal. |
| `UNDER_REVIEW` | `SUBMITTED` | `release_review`| Revisor asignado, `NATIONAL_ADMIN` | Libera el bloqueo de revisión nuevamente a la cola. |
| `APPROVED` | `PROVISIONED` | `execute_provision`| `DEPARTMENT_ADMIN` (su depto), `NATIONAL_ADMIN` | **Transacción atómica**: Crea tenant, sedes e invita rector. |
| `APPROVED` | `CANCELLED` | `revoke_approval`| `NATIONAL_ADMIN`, `SUPERADMIN` | Revocatoria extraordinaria antes de ejecutar aprovisionamiento. |

### 4.2 Transiciones Estrictamente Prohibidas
- `PROVISIONED` $\to$ Cualquier estado (Estado final inmutable. El tenant ya existe operacionalmente).
- `REJECTED` $\to$ `APPROVED` (Prohibido reactivar rechazos. Se debe radicar una nueva solicitud).
- `CANCELLED` $\to$ `APPROVED` (Prohibido reactivar cancelaciones).
- `DRAFT` $\to$ `PROVISIONED` (Prohibido el bypass de la etapa de visto bueno y aprobación).
- Transición interdepartamental por un `DEPARTMENT_ADMIN` ajeno (Bloqueado por Anti-IDOR con HTTP 403).

---

## 5. MODELO DE AUTORIZACIÓN Y MATRIZ RBAC

Se definen los nuevos permisos atómicos institucionales para la gobernanza del onboarding:

1. `onboarding:discover` — Capacidad de explorar el catálogo de establecimientos para fines de incorporación.
2. `onboarding:create` — Radicar una solicitud de incorporación.
3. `onboarding:review` — Tomar una solicitud para revisión técnica.
4. `onboarding:approve` — Aprobar formalmente la solicitud de incorporación.
5. `onboarding:reject` — Rechazar formalmente una solicitud de incorporación.
6. `onboarding:cancel` — Desistir de una solicitud radicada.
7. `onboarding:provision` — Ejecutar la materialización del tenant institucional en el SaaS.

### Matriz de Roles y Alcances (Scope Matrix)

| Rol del Sistema | Alcance Territorial | Descubrir Catálogo | Radicar Solicitud | Revisar | Aprobar | Rechazar | Cancelar | Aprovisionar | Invitar Rector |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SUPERADMIN** | Nacional (33 Deptos) | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ |
| **NATIONAL_ADMIN** | Nacional (33 Deptos) | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ | SÍ |
| **DEPARTMENT_ADMIN**| Scoped (`department_id`)| SÍ (Solo su Depto) | SÍ (Solo su Depto) | SÍ (Solo su Depto)| SÍ (Solo su Depto)*| SÍ (Solo su Depto)| SÍ (Solo suyas) | SÍ (Solo su Depto)| Delegado post-onb |
| **RECTOR** | Institucional | NO | NO | NO | NO | NO | NO | NO | NO |
| **COORDINATOR / DOCENTE** | Institucional | NO | NO | NO | NO | NO | NO | NO | NO |

*\*Nota de Gobernanza:* Un Administrador Departamental puede aprobar solicitudes de su propia jurisdicción cuando cuente con delegación territorial de la Secretaría de Educación, garantizando autonomía descentralizada bajo supervisión del Administrador Nacional.

---

## 6. SEGURIDAD TERRITORIAL Y GARANTÍA ANTI-IDOR

NTA-04 extenderá la verificación matemática de aislamiento departamental probada en NTA-01 y NTA-02 a todos los endpoints de onboarding.

### 6.1 Reglas Anti-IDOR Inquebrantables
1. **Filtro Automático en Catálogo:** Cuando un `DEPARTMENT_ADMIN` asignado al departamento $d_A$ (ej. Atlántico `08`) consulta el catálogo para incorporar colegios:
   - El sistema sobreescribe forzosamente el parámetro territorial: `query.where(OfficialInstitutionCatalog.department_code == auth.user_department_code)`.
   - Si el cliente envía en la URL `?department_id=<Bogotá_UUID>`, el controlador lanza **HTTP 403 Forbidden** (`PERMISSION_DENIED`).
2. **Validación en Radicación:** Al radicar `POST /api/v1/onboarding/requests`:
   - El servicio lee el establecimiento del catálogo por `catalog_institution_id`.
   - Si `catalog.department_code != auth.user_department_code`: El backend aborta inmediatamente con **HTTP 403 Forbidden** (*"No está autorizado para iniciar incorporación de un establecimiento fuera de su jurisdicción departamental"*).
3. **Validación en Cola de Aprobación y Acciones:** Al invocar `/onboarding/requests/{id}/approve` (o `reject`, `review`, `provision`):
   - El servicio carga la solicitud y verifica:
     ```python
     target_scope = OrganizationalScope(
         country_code="CO",
         department_id=str(request.department_id),
     )
     await authorization_service.require(
         auth,
         required_permission=Permission(resource="onboarding", action="approve"),
         target_scope=target_scope,
     )
     ```
   - Si un Administrador Departamental de Atlántico intenta operar una solicitud de Cundinamarca o Bogotá, el motor de autorización evalúa $d_A \neq d_B$ y responde **HTTP 403 Forbidden**.

---

## 7. PROTECCIÓN CONTRA CONCURRENCIA, CARRERAS E IDEMPOTENCIA

### 7.1 Escenario Crítico de Concurrencia
> **Escenario:** Dos administradores (ej. el Administrador Departamental en Barranquilla y el Administrador Nacional en Bogotá) observan simultáneamente una solicitud aprobada para el *"CENTRO DE EDUCACION BASICA # 201"* y hacen clic en *"Aprovisionar Tenant"* en el mismo milisegundo.

### 7.2 Arquitectura de Bloqueo a Cuatro Capas (Four-Tier Defense)

```
[Petición Concurrente A]                     [Petición Concurrente B]
          |                                            |
          v                                            v
+-------------------------------------------------------------------------+
| CAPA 1: PESSIMISTIC LOCK (SELECT ... FOR UPDATE en Onboarding Request)  |
| - A adquiere bloqueo de fila exclusivo.                                 |
| - B se suspende en espera de liberación de bloqueo.                     |
+-------------------------------------------------------------------------+
          |
          v
+-------------------------------------------------------------------------+
| CAPA 2: EVALUACIÓN DE ESTADO EN MEMORIA                                 |
| - A verifica: status == 'APPROVED' -> Procede.                          |
| - A inserta en institutions y actualiza status = 'PROVISIONED'.         |
| - A hace COMMIT (Libera bloqueo).                                       |
+-------------------------------------------------------------------------+
                                                       |
                                                       v
+-------------------------------------------------------------------------+
| CAPA 3: DESPERTAR DE B BAJO ESTADO MUTADO                               |
| - B adquiere el bloqueo.                                                |
| - B lee la fila fresca: status == 'PROVISIONED'.                        |
| - B detecta violación de precondición: status != 'APPROVED'.            |
| - B aborta limpiamente con HTTP 409 Conflict.                           |
+-------------------------------------------------------------------------+
                                                       | (Si hubiera bypass)
                                                       v
+-------------------------------------------------------------------------+
| CAPA 4: RESTRICCIÓN FÍSICA POSTGRESQL (ÚLTIMA LÍNEA DE DEFENSA)         |
| - uq_institutions_catalog_institution_id rechaza duplicado (Error 23505)|
| - Rollback forzado e inocuo en PostgreSQL.                              |
+-------------------------------------------------------------------------+
```

---

## 8. INTEGRIDAD DEL CATÁLOGO Y MANEJO DE CASOS DE BORDE (EDGE CASES)

| Caso de Borde | Comportamiento del Sistema PEVN | Código HTTP / Excepción | Acción en UI |
| :--- | :--- | :---: | :--- |
| **Establecimiento no aprovisionado** | Flujo nominal permitido. | 200 OK / 201 Created | Muestra botón verde *"Incorporar a PEVN"*. |
| **Establecimiento ya es tenant en PEVN** | Bloqueo preventivo. Detecta coincidencia por `catalog_institution_id` o `dane_code`. | **HTTP 409 Conflict** (`INSTITUTION_ALREADY_PROVISIONED`) | Badge azul *"Ya Aprovisionado"* con botón de enlace directo al perfil del colegio. |
| **Establecimiento ya tiene solicitud activa** | Bloqueo por índice único parcial `uq_onboarding_active_catalog_institution`. | **HTTP 409 Conflict** (`ACTIVE_REQUEST_EXISTS`) | Badge amarillo *"En Trámite"* con enlace al número de radicado. |
| **Establecimiento INACTIVO en catálogo** | Establecimiento oficial reportado como cerrado/inactivo por el MEN (`is_active = False`). | **HTTP 422 Unprocessable** (`CATALOG_INSTITUTION_INACTIVE`) | Requiere flag explícito de justificación nacional (`allow_inactive_override=True`). |
| **Inconsistencia territorial en catálogo** | Código de municipio del catálogo no coincide con DIVIPOLA operacional. | **HTTP 422 Unprocessable** (`TERRITORIAL_DIVIPOLA_MISMATCH`) | Se notifica advertencia para validación DIVIPOLA previa. |
| **Establecimiento no existe en catálogo** | Código DANE o UUID no hallado en `official_institution_catalog`. | **HTTP 404 Not Found** (`CATALOG_RECORD_NOT_FOUND`) | Mensaje formal de registro no encontrado en el universo MEN. |
| **Catálogo muta durante el onboarding** | Si el dataset del MEN cambia durante el trámite. | Audit Warning `CATALOG_METRICS_UPDATED` | Se evalúa contra el snapshot capturado al radicar la solicitud. |

---

## 9. LÍMITE TRANSACCIONAL DEL APROVISIONAMIENTO (TENANT CREATION BOUNDARY)

El aprovisionamiento de un nuevo colegio se ejecuta de forma estricta dentro de un **único límite transaccional atómico** gestionado por SQLAlchemy y PostgreSQL:

```python
async with session.begin():
    # 1. Bloqueo pesimista de la solicitud
    req = await session.execute(
        select(InstitutionOnboardingRequest)
        .where(InstitutionOnboardingRequest.id == request_id)
        .with_for_update()
    ).scalar_one()
    
    assert req.status == OnboardingRequestStatus.APPROVED
    
    # 2. Materialización del Tenant Institucional
    institution = Institution(
        catalog_institution_id=req.catalog_institution_id,
        municipality_id=req.municipality_id,
        dane_code=req.dane_code,
        name=catalog_record.name,
        email=req.contact_email,
        phone=req.contact_phone,
        address=catalog_record.official_address,
        is_active=True,
    )
    session.add(institution)
    await session.flush()  # Obtiene institution.id
    
    # 3. Materialización de la Sede Principal y Sedes Anexas
    for cat_campus in catalog_record.campuses:
        campus = Campus(
            institution_id=institution.id,
            dane_sede_code=cat_campus.dane_sede_code,
            name=cat_campus.name,
            is_active=cat_campus.is_active,
        )
        session.add(campus)
        
    # 4. Transición de la Solicitud de Onboarding
    req.status = OnboardingRequestStatus.PROVISIONED
    req.institution_id = institution.id
    req.provisioned_by_id = actor.id
    req.provisioned_at = datetime.now(UTC)
    
    # 5. Encadenamiento Criptográfico de Rector (si fue provisto)
    if req.proposed_rector_email:
        await rector_service.invite_rector_internal(
            session=session,
            institution_id=institution.id,
            email=req.proposed_rector_email,
            name=req.proposed_rector_name,
            doc_type=req.proposed_rector_doc_type,
            doc_num=req.proposed_rector_doc_num,
            actor_id=actor.id,
        )
        
    # 6. Registro Inmutable de Auditoría
    await audit_service.record(
        AuditEvent(
            event_type=AuditEventType.INSTITUTION_PROVISIONED_FROM_ONBOARDING,
            actor_id=str(actor.id),
            target_id=str(institution.id),
            target_type="Institution",
            metadata={
                "request_id": str(req.id),
                "dane_code": req.dane_code,
                "catalog_id": str(req.catalog_institution_id),
            }
        ),
        session=session
    )
# COMMIT ATÓMICO: Si cualquier paso falla, se revierte al 100%. Cero tenants a medias.
```

---

## 10. IDENTIDAD INSTITUCIONAL Y VINCULACIÓN DEL RECTOR

1. **Principio Rectoral:** Un colegio en Colombia no puede operar sin su representante legal y autoridad académica ante el MEN y la Secretaría de Educación.
2. **Encadenamiento Seguro de Credenciales:**
   - Si la solicitud incluye los datos del rector propuesto, el aprovisionamiento invoca de manera transparente el servicio verificado `RectorOnboardingService`.
   - Se crea el usuario en estado `is_active = False` con rol `rector`.
   - Se genera un token criptográfico de 48 bytes URL-safe.
   - Se persiste **únicamente el hash SHA-256** en `rector_invitations`.
   - Se genera el correo de invitación o el enlace seguro de activación.
3. **Escenario sin Rector Inmediato:**
   - Si la solicitud no incluye rector (ej. vacancia directiva), el tenant se crea en estado operacional normal pero sin directivo asignado.
   - El sistema emite la alerta `PENDING_RECTOR_ASSIGNMENT`, habilitando al Administrador Nacional o Departamental para emitir la invitación posteriormente mediante el endpoint existente `POST /api/v1/institutions/{id}/rector-invitation`.

---

## 11. AUDITORÍA INMUTABLE Y TRAZABILIDAD

Se incorporarán los siguientes eventos en `AuditEventType` (`backend/app/audit/interfaces.py`):

1. `ONBOARDING_REQUEST_CREATED` (`onboarding.request.created`)
2. `ONBOARDING_REQUEST_SUBMITTED` (`onboarding.request.submitted`)
3. `ONBOARDING_REQUEST_REVIEW_STARTED` (`onboarding.request.review_started`)
4. `ONBOARDING_REQUEST_APPROVED` (`onboarding.request.approved`)
5. `ONBOARDING_REQUEST_REJECTED` (`onboarding.request.rejected`)
6. `ONBOARDING_REQUEST_CANCELLED` (`onboarding.request.cancelled`)
7. `INSTITUTION_PROVISIONED_FROM_ONBOARDING` (`institution.provisioned_from_onboarding`)

Cada registro de auditoría almacena:
- `timestamp`: UTC auditado por base de datos.
- `actor_id`: UUID del usuario ejecutor.
- `actor_role`: Rol en sesión.
- `actor_ip`: Dirección IP del cliente.
- `department_id`: Jurisdicción territorial.
- `target_id`: UUID de la solicitud o de la institución creada.
- `metadata`: Diccionario JSON estructurado con estado anterior, estado nuevo, código DANE, y justificación.

---

## 12. TRATAMIENTO DE LOS 27 FIXTURES SINTÉTICOS DE PRUEBAS

En la Fase NTA-03 se clasificaron formalmente 27 instituciones como:
`SYNTHETIC FIXTURE (NULL)` con `catalog_institution_id = NULL`.

### Política de Convivencia e Inmunidad en NTA-04:
1. **Inmunidad:** Las 27 instituciones sintéticas no se borran, no se mutan y no se reclasifican durante NTA-04.
2. **Imposibilidad de Colisión:**
   - El flujo de onboarding NTA-04 **exige de manera obligatoria** una clave foránea válida `catalog_institution_id` apuntando a `official_institution_catalog.id`.
   - Dado que los 27 fixtures no existen en el catálogo, es físicamente imposible radicar solicitudes de onboarding asociadas a ellos.
   - Cuando un administrador busca en el catálogo colegios para incorporar, la consulta se hace sobre `official_institution_catalog`, el cual tiene 0 coincidencias con los 27 fixtures.
3. **Distinción Visual en la Plataforma:**
   - En las vistas administrativas, los colegios respaldados por el catálogo oficial ostentan la insignia `OFICIAL DANE / MEN` (verificado 1:1).
   - Los fixtures de prueba ostentan la etiqueta `FIXTURE DE PRUEBA (DESARROLLO)`.

---

## 13. DISEÑO DE EXPERIENCIA DE USUARIO (UI / UX WORKFLOW)

La arquitectura de interfaz para NTA-04 se estructurará en tres módulos integrados:

### 13.1 Módulo 1: Explorador del Catálogo y Lanzador de Onboarding (`/admin/territory/catalog`)
- **Buscador Universal:** Búsqueda rápida por nombre o código DANE de 12 dígitos.
- **Filtros Territoriales:** Selector de Departamento y Municipio (pre-filtrado y bloqueado para `DEPARTMENT_ADMIN` según su jurisdicción; selector completo de 33 departamentos para `NATIONAL_ADMIN`).
- **Estado de Incorporación en Tiempo Real:**
  - `Incorporable`: Botón verde *"Iniciar Incorporación"*.
  - `En Trámite`: Badge ámbar *"Solicitud en Proceso (# ONB-...)"*.
  - `Ya en Plataforma`: Badge azul *"Operacional en PEVN"*.

### 13.2 Módulo 2: Formulario de Radicación de Solicitud (Modal / Drawer)
- **Tarjeta Resumen del Catálogo (Solo Lectura):** Nombre oficial, DANE 12 dígitos, Departamento, Municipio, Dirección oficial, Sector (Oficial / No Oficial), Número de sedes oficiales adscritas.
- **Campos Operacionales de PEVN:**
  - Correo institucional oficial de contacto (obligatorio).
  - Teléfono institucional (opcional).
  - Sección *"Designación de Rector Inicial"* (Nombre, Documento, Correo).
  - Justificación administrativa de radicación.
- **Acciones:** *"Guardar como Borrador"* / *"Radicar Solicitud Oficial"*.

### 13.3 Módulo 3: Bandeja de Gestión y Aprobación (`/admin/onboarding-requests`)
- **Pestañas de Estado:** `Todas` | `Pendientes de Aprobación` | `En Revisión` | `Aprobadas (Listas para Aprovisionar)` | `Histórico`.
- **Acciones Rápidas por Fila:**
  - `Tomar Revisión`: Asigna la solicitud al revisor.
  - `Aprobar`: Abre confirmación de aprobación.
  - `Rechazar`: Abre modal con campo obligatorio de motivo de rechazo.
  - `Aprovisionar Ahora`: Para solicitudes aprobadas, ejecuta la materialización inmediata del tenant SaaS.

---

## 14. ESPECIFICACIÓN DEL CONTRATO DE API REST

Todos los endpoints propuestos se ubicarán bajo el prefijo `/api/v1/onboarding`:

### 14.1 `GET /api/v1/onboarding/catalog`
- **Descripción:** Explora el catálogo oficial enriquecido con el estado de incorporación en PEVN.
- **Permiso:** `onboarding:discover`.
- **Alcance:** Scoped por `department_id` para `DEPARTMENT_ADMIN`; Global para `NATIONAL_ADMIN`.
- **Query Params:** `dane_code`, `name`, `department_id`, `municipality_id`, `onboarding_status` (`AVAILABLE`, `IN_PROGRESS`, `PROVISIONED`), `page`, `page_size`.
- **Respuesta 200:** `CatalogExplorerListResponse`.

### 14.2 `POST /api/v1/onboarding/requests`
- **Descripción:** Crea y radica una nueva solicitud de incorporación.
- **Permiso:** `onboarding:create`.
- **Payload:** `OnboardingRequestCreatePayload` (`catalog_institution_id`, `contact_email`, `contact_phone`, `proposed_rector_email`, etc.).
- **Errores:** `403 Forbidden` (Territorio ajeno), `409 Conflict` (Colegio ya aprovisionado o con solicitud activa), `422 Unprocessable` (Establecimiento inactivo en catálogo).
- **Respuesta 201:** `OnboardingRequestDetailResponse`.

### 14.3 `GET /api/v1/onboarding/requests`
- **Descripción:** Lista las solicitudes de incorporación con filtros de estado y territorio.
- **Permiso:** `onboarding:read`.
- **Alcance:** Scoped territorialmente según usuario.
- **Respuesta 200:** `OnboardingRequestListResponse`.

### 14.4 `GET /api/v1/onboarding/requests/{id}`
- **Descripción:** Detalle completo de la solicitud, incluyendo snapshot del catálogo, datos del rector propuesto y bitácora de transiciones.
- **Permiso:** `onboarding:read`.
- **Errores:** `403 Forbidden` (Anti-IDOR interdepartamental), `404 Not Found`.

### 14.5 `POST /api/v1/onboarding/requests/{id}/start-review`
- **Descripción:** Pasa la solicitud de `SUBMITTED` a `UNDER_REVIEW`.
- **Permiso:** `onboarding:review`.

### 14.6 `POST /api/v1/onboarding/requests/{id}/approve`
- **Descripción:** Otorga aprobación administrativa (`APPROVED`).
- **Permiso:** `onboarding:approve`.
- **Payload:** `OnboardingApprovalPayload` (`notes`).

### 14.7 `POST /api/v1/onboarding/requests/{id}/reject`
- **Descripción:** Rechaza formalmente la solicitud (`REJECTED`).
- **Permiso:** `onboarding:reject`.
- **Payload:** `OnboardingRejectionPayload` (`rejection_reason` obligatorio).

### 14.8 `POST /api/v1/onboarding/requests/{id}/cancel`
- **Descripción:** Desiste de la solicitud (`CANCELLED`).
- **Permiso:** `onboarding:cancel`.

### 14.9 `POST /api/v1/onboarding/requests/{id}/provision`
- **Descripción:** Ejecuta la creación del tenant operacional, creación de sedes y despacho de invitación de rector.
- **Permiso:** `onboarding:provision`.
- **Errores:** `409 Conflict` (Si ya fue aprovisionado concurrentemente o estado no es `APPROVED`).
- **Respuesta 201:** `OnboardingProvisionResultResponse` (`institution_id`, `rector_invitation_id`, `activation_url`).

---

## 15. PLAN DE MIGRACIÓN ALEMBIC (PROPOSED MIGRATION 028)

- **Nombre de Revisión:** `028_nta04_national_provisioning_workflow.py`
- **Revisión Previa (`down_revision`):** `027_nta03_catalog_provisioning_architecture`

### 15.1 Estructura del Script de Migración
```python
def upgrade() -> None:
    # 1. Crear tabla institution_onboarding_requests
    op.create_table(
        "institution_onboarding_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_number", sa.String(length=32), nullable=False),
        sa.Column("catalog_institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("official_institution_catalog.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("dane_code", sa.String(length=12), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("municipality_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("municipalities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requester_role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUBMITTED"),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("proposed_rector_name", sa.String(length=255), nullable=True),
        sa.Column("proposed_rector_email", sa.String(length=255), nullable=True),
        sa.Column("proposed_rector_doc_type", sa.String(length=20), nullable=True),
        sa.Column("proposed_rector_doc_num", sa.String(length=50), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("provisioned_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provisioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Índices
    op.create_index("uq_onboarding_request_number", "institution_onboarding_requests", ["request_number"], unique=True)
    op.create_index("ix_onboarding_department_status", "institution_onboarding_requests", ["department_id", "status"])
    op.create_index("ix_onboarding_status_created", "institution_onboarding_requests", ["status", "created_at"])
    op.create_index("ix_onboarding_dane_code", "institution_onboarding_requests", ["dane_code"])

    # 3. Índice único parcial anti-solicitudes activas duplicadas
    op.create_index(
        "uq_onboarding_active_catalog_institution",
        "institution_onboarding_requests",
        ["catalog_institution_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED')")
    )

def downgrade() -> None:
    op.drop_table("institution_onboarding_requests")
```

### 15.2 Estrategia de Reversión (Rollback Inocuo)
- La migración solo crea una tabla independiente.
- No modifica ni elimina tablas operacionales existentes.
- El rollback (`alembic downgrade 027_nta03_catalog_provisioning_architecture`) elimina exclusivamente la tabla `institution_onboarding_requests`, preservando intactos el 100% de los tenants, usuarios, roles, sedes y catálogo.

---

## 16. MATRIZ DEL PLAN DE PRUEBAS DE NTA-04

Para la fase de implementación de NTA-04 se diseñarán 18 pruebas automatizadas específicas:

| ID Prueba | Escenario de Prueba | Resultado Esperado |
| :---: | :--- | :--- |
| `TEST-01` | **Happy Path Onboarding:** Radicación $\to$ Aprobación $\to$ Aprovisionamiento completo. | HTTP 201 Created; Tenant en `institutions`; Sede principal creada; Estado `PROVISIONED`. |
| `TEST-02` | **Encadenamiento de Rector:** Radicación con datos de rector propuesto. | Rector creado inactivo; `RectorInvitation` generada; Token SHA-256 verificado. |
| `TEST-03` | **Onboarding sin Rector Inmediato:** Solicitud aprobada sin datos de rector. | Tenant aprovisionado; Estado de rectoría `PENDING_ASSIGNMENT`. |
| `TEST-04` | **Anti-Duplicidad Solicitudes Activas:** Dos solicitudes simultáneas para el mismo colegio. | Segunda solicitud rechazada con **HTTP 409 Conflict** (Violación índice parcial). |
| `TEST-05` | **Anti-Duplicidad Tenant Existente:** Intento de onboarding sobre colegio ya aprovisionado. | Rechazo preventivo inmediato con **HTTP 409 Conflict** (`ALREADY_PROVISIONED`). |
| `TEST-06` | **Anti-IDOR Radicación:** Department Admin de Atlántico intenta radicar colegio de Bogotá. | **HTTP 403 Forbidden** (`PERMISSION_DENIED`). |
| `TEST-07` | **Anti-IDOR Aprobación:** Department Admin de Atlántico intenta aprobar solicitud de Bogotá. | **HTTP 403 Forbidden** (`PERMISSION_DENIED`). |
| `TEST-08` | **Anti-IDOR Consulta:** Department Admin de Atlántico intenta listar solicitudes de otro depto. | **HTTP 403 Forbidden** o lista filtrada estrictamente a su departamento. |
| `TEST-09` | **Autonomía Departamental Válida:** Department Admin de Atlántico aprueba solicitud de Atlántico. | **HTTP 200 OK**; Estado avanza a `APPROVED`. |
| `TEST-10` | **Autoridad Nacional Global:** National Admin aprueba solicitud de cualquier departamento. | **HTTP 200 OK** en los 33 departamentos. |
| `TEST-11` | **Rechazo con Motivo Obligatorio:** Solicitud rechazada sin motivo o con motivo vacío. | **HTTP 422 Unprocessable** (`REJECTION_REASON_REQUIRED`). |
| `TEST-12` | **Cancelación Autorizada:** Solicitante cancela su propia solicitud antes de aprobación. | **HTTP 200 OK**; Estado avanza a `CANCELLED`. |
| `TEST-13` | **Cancelación no Autorizada:** Usuario ajeno intenta cancelar solicitud de otro. | **HTTP 403 Forbidden**. |
| `TEST-14` | **Transición Prohibida:** Intento de aprobar solicitud previamente cancelada o rechazada. | **HTTP 409 Conflict** (Transición ilegal de máquina de estados). |
| `TEST-15` | **Concurrencia de Aprovisionamiento:** Dos peticiones paralelas de aprovisionar en el mismo ms. | Primera retorna HTTP 201; Segunda retorna **HTTP 409 Conflict**. Exactamente 1 tenant creado. |
| `TEST-16` | **Colegio Inactivo en Catálogo:** Intento de onboarding de colegio cerrado/inactivo en MEN. | **HTTP 422 Unprocessable** salvo override nacional explícito. |
| `TEST-17` | **Colegio Inexistente:** UUID inexistente en `official_institution_catalog`. | **HTTP 404 Not Found**. |
| `TEST-18` | **Preservación de Fixtures Sintéticos:** Ninguno de los 27 fixtures se altera ni colisiona. | Los 27 fixtures se mantienen con `catalog_institution_id = NULL` intactos. |

---

## 17. CRITERIOS OBJETIVOS DE ACEPTACIÓN (NTA-04 ACCEPTANCE CRITERIA)

La implementación futura de NTA-04 solo podrá ser certificada como **PASS** si satisface el 100% de los siguientes criterios:

- [ ] Modelo `InstitutionOnboardingRequest` y migración 028 creados y aplicados limpiamente.
- [ ] Índice único parcial `uq_onboarding_active_catalog_institution` activo y verificado en PostgreSQL.
- [ ] Máquina de estados gobernada y transiciones ilegales rechazadas con HTTP 409.
- [ ] Anti-IDOR territorial estricto (HTTP 403) para solicitudes, aprobaciones y consultas fuera de jurisdicción.
- [ ] Aprovisionamiento transaccional atómico (Creación simultánea de tenant, sedes y actualización de solicitud).
- [ ] Encadenamiento automático con `RectorInvitation` y conservación del esquema de tokens SHA-256.
- [ ] Prevención total de dobles aprovisionamientos ante condiciones de carrera (Race Conditions).
- [ ] Registros de auditoría generados para cada transición de estado en `audit_logs`.
- [ ] Preservación del 100% de la línea base preexistente (34 instituciones, 18 sedes, 200 usuarios, 33 depts, 1,119 munis).
- [ ] Inmunidad total para los 27 fixtures sintéticos de pruebas heredados.
- [ ] Suite de pruebas de regresión completa al 100% Green ($\ge 98$ tests pasando: 80 existentes + 18 de NTA-04).
- [ ] Estrategia de rollback validada e inocua.

---

## 18. CERTIFICACIÓN DE CERO MUTACIONES (ZERO-MUTATION CERTIFICATE)

De conformidad con el mandato estricto de la autorización de auditoría y diseño preflight para **Phase NTA-04**:

```
============================================================
PEVN NTA-04 PREFLIGHT & DESIGN AUDIT CERTIFICATE
============================================================

STATUS:
    PASS — ARCHITECTURE BLUEPRINT COMPLETE & CERTIFIED

DATABASE MUTATIONS:
    0

CODE CHANGES:
    0

ALEMBIC MIGRATIONS EXECUTED:
    0

RECORDS INSERTED:
    0

RECORDS UPDATED:
    0

RECORDS DELETED:
    0

OPERATIONAL DEPARTMENTS:
    33 (Preserved)

OPERATIONAL MUNICIPALITIES:
    1,119 (Preserved)

PEVN TENANTS:
    34 (Preserved: 31 active / 3 inactive)

CAMPUSES:
    18 (Preserved)

USERS:
    200 (Preserved)

SCOPED DEPARTMENT ADMINS:
    10 (Preserved)

NTA-04 STATUS:
    AUDIT & ARCHITECTURE BLUEPRINT COMPLETE
    AWAITING EXPLICIT USER AUTHORIZATION FOR IMPLEMENTATION

NEXT AUTHORIZED ACTION:
    STOP AND WAIT FOR USER INSTRUCTION.
    DO NOT IMPLEMENT NTA-04 AUTOMATICALLY.
    DO NOT BEGIN NTA-05.

============================================================
END OF NTA-04 AUDIT & DESIGN CERTIFICATION
============================================================
```
