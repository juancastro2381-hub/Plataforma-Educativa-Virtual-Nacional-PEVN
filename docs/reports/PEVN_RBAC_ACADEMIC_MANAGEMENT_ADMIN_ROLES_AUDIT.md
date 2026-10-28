# AUDITORÍA FORENSE DE CONTROL DE ACCESOS RBAC
## Módulo de Gestión Académica e Institucional para Roles Administrativos

**Plataforma:** Plataforma Educativa Virtual Nacional (PEVN)  
**Fecha:** 28 de Octubre de 2026  
**Auditor:** Senior Software Architect, RBAC Security Auditor & Educational Platform Specialist  
**Estado:** ✅ DICTAMEN EMITIDO, REMEDIACIÓN APLICADA Y CIERRE DE SEGURIDAD BACKEND COMPLETADO  

---

## 1. Resumen Ejecutivo

A solicitud de la Dirección de Producto (Product Owner) y conforme a los principios de mínimo privilegio y separación de poderes institucionales consagrados en la arquitectura de la PEVN, se ejecutó una auditoría exhaustiva sobre la legitimidad de acceso de los cuatro roles administrativos de gobierno y plataforma al módulo **"Gestión Académica e Institucional"** (`AcademicHub` / `/academic`):

1. **`SUPERADMIN`** (`superadmin`, alias frontend `super_admin`)
2. **`NATIONAL_ADMIN`** (`national_admin`)
3. **`DEPARTMENT_ADMIN`** (`department_admin`)
4. **`MUNICIPALITY_ADMIN`** (`municipality_admin`)

### Regla de Decisión del Product Owner
> *"Si la auditoría no encuentra documentación explícita y vinculante que apruebe el acceso a la 'Gestión Académica e Institucional' para un rol, se debe remover la visibilidad de dicho módulo para ese rol y bloquear el acceso directo no autorizado mediante la ruta frontend y los endpoints backend pertinentes."*

### Dictamen Principal
**NINGUNO** de los cuatro roles administrativos cuenta con mandato documental ni autorización institucional para gestionar la vida académica ordinaria de las sedes educativas (creación/edición de años lectivos, periodos, asignaturas, grados, grupos, planta docente, matrículas SIMAT, acudientes, asignaciones académicas o calificaciones).

Por el contrario, la documentación normativa institucional de la plataforma (`docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md` §9 y `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3) califica expresamente el acceso a `/academic` para estos cuatro roles como **`Intended: ❌ (NO DEBE VER)`**.

Se identificó una divergencia (*code drift*) en el frontend donde `national_admin`, `department_admin` y `municipality_admin` recibían visibilidad en el menú de navegación (`RootLayout.tsx`), acceso directo en la guarda de ruta (`App.tsx`), tarjetas en el panel principal (`Dashboard.tsx`) y habilitación de pestañas en `AcademicHub.tsx`.

La remediación ha sido **implementada, verificada y blindada** en el código fuente, eliminando toda visibilidad y acceso no autorizado para estos roles, preservando íntegramente la operación directiva institucional (`rector`, `institution_admin`, `coordinator`, `academic_coordinator`) y validando el 100% de la suite de pruebas (200 pruebas frontend y 31 pruebas backend aprobadas).

---

## 2. Nombres Canónicos y Tratamiento de Alias

En el modelo de datos backend (`backend/app/models/user.py`, `backend/app/schemas/role.py`, `backend/app/services/rbac_bootstrap_service.py`) y en las directivas de seguridad de la plataforma, los roles se definen de manera canónica como enumeraciones estrictas (`SystemRole`):

| Nombre Canónico Backend (`SystemRole`) | Nivel Jerárquico | Alias Detectados en Código | Naturaleza y Jurisdicción |
| :--- | :---: | :--- | :--- |
| `superadmin` | Nivel 100 | `super_admin` (Frontend AuthContext / TypeScript types) | Operador técnico global y DevOps de infraestructura de plataforma. |
| `national_admin` | Nivel 90 | Ninguno | Autoridad nacional del Ministerio de Educación Nacional (MEN). |
| `department_admin` | Nivel 80 | Ninguno | Autoridad territorial de Secretaría de Educación Departamental (SED). |
| `municipality_admin` | Nivel 70 | Ninguno | Autoridad territorial de Secretaría de Educación Municipal (SEM). |

*Nota técnica:* Para prevenir evasiones basadas en inconsistencias tipográficas entre guiones bajos y cadenas unificadas, todas las reglas de control de acceso frontend evalúan tanto el nombre canónico como el alias histórico: `['superadmin', 'super_admin']`.

---

## 3. Matriz de Evidencia Documental y Decisión

| Rol | ¿Autorización Documental Explícita? | Visibilidad de Menú Existente | Autorización de Ruta Existente | Autorización Backend / API | Evidencia y Fuentes Documentales | Decisión Final y Justificación |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **`SUPERADMIN`** (`super_admin`) | **NO** | ❌ Oculto en navbar (`!isSuperAdmin`) | ⚠️ **SÍ** (`App.tsx:172` permitía `superadmin`) | ⚠️ `*:*` técnico con `?institution_id=` (Phase 3B integration test); 403 sin contexto | • `docs/reports/PEVN_SA02_SUPER_ADMIN_TECHNICAL_OPERATIONS_PORTAL.md`<br>• `docs/reports/PEVN_SA01_SUPER_ADMIN_GLOBAL_GOVERNANCE_AND_CERTIFICATION.md`<br>• `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md` §9 | **REMOVER ACCESO Y BLINDAR.**<br>El SuperAdmin es una consola técnica de telemetría y contingencia (SA-02). No forma parte de la jerarquía educativa. Su acceso a `/academic` ha sido revocado en UI y guardas de ruta. Se escala a Dirección la política del comodín técnico `*:*`. |
| **`NATIONAL_ADMIN`** | **NO** | ⚠️ **SÍ** (`RootLayout.tsx:52` por rol y permiso de lectura) | ⚠️ **SÍ** (`App.tsx:172` permitía `national_admin`) | Lectura analítica (`rbac_bootstrap_service.py`); 403 sin contexto institucional | • `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.2<br>• `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md` §9 (`Intended: ❌`)<br>• `docs/AUTHORIZATION.md` | **REMOVER ACCESO Y BLINDAR.**<br>El rol MEN tiene soberanía macro-estadística y aprovisionamiento institucional (`/admin/institutions`, `/admin/onboarding`), pero el documento §3.2 prohíbe taxativamente la manipulación o gestión de la vida académica escolar local. |
| **`DEPARTMENT_ADMIN`** | **NO** | ⚠️ **SÍ** (`RootLayout.tsx:52` por rol y permiso de lectura) | ⚠️ **SÍ** (`App.tsx:172` permitía `department_admin`) | Lectura analítica (`rbac_bootstrap_service.py`); 403 sin contexto departamental | • `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.3<br>• `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md` §9 (`Intended: ❌`)<br>• `docs/PHASE_3_RBAC_MATRIX.md` | **REMOVER ACCESO Y BLINDAR.**<br>La Secretaría Departamental ejerce supervisión macro-territorial mediante `/analytics/territorial` y el Centro de Control `/admin/control-center`. Carece de fuero para gestionar currículo escolar directo. |
| **`MUNICIPALITY_ADMIN`** | **NO** | ⚠️ **SÍ** (`RootLayout.tsx:52` por rol y permiso de lectura) | ⚠️ **SÍ** (`App.tsx:172` permitía `municipality_admin`) | Lectura analítica (`rbac_bootstrap_service.py`); 403 sin contexto municipal | • `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` §3.4<br>• `docs/reports/PEVN_ROLE_VISIBILITY_RBAC_FORENSIC_AUDIT.md` §9 (`Intended: ❌`)<br>• `docs/PHASE_3_RBAC_MATRIX.md` | **REMOVER ACCESO Y BLINDAR.**<br>La Secretaría Municipal ejerce supervisión sobre colegios de su municipio mediante `/analytics/territorial`. La autonomía académica interna reside exclusivamente en el Rector y Consejo Directivo del plantel. |

---

## 4. Trazabilidad Completa del Flujo de Autorización

### 4.1 Frontend — Barra Superior de Navegación (`RootLayout.tsx`)
- **Estado previo al hallazgo:** La variable `canAccessAcademic` evaluaba:
  ```tsx
  const canAccessAcademic = !isSuperAdmin && (
    isInstitutionalDirective ||
    hasRole(['national_admin', 'department_admin', 'municipality_admin']) ||
    hasPermission('academic_years:read')
  )
  ```
  Dado que los administradores territoriales poseían `academic_years:read` en su token para la lectura agregada de vigencias, el enlace **"Académica"** aparecía en la barra superior.
- **Corrección ejecutada:**
  ```tsx
  const canAccessAcademic = !isSuperAdmin && isInstitutionalDirective
  ```
  Únicamente directivos institucionales autorizados (`rector`, `institution_admin`, `coordinator`, `academic_coordinator`) visualizan el acceso.

### 4.2 Frontend — Guarda de Ruta Principal (`App.tsx`)
- **Estado previo al hallazgo:** La ruta `/academic` declaraba explícitamente en su lista de roles permitidos a todos los administradores técnicos y territoriales:
  ```tsx
  roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator', 'superadmin', 'super_admin', 'national_admin', 'department_admin', 'municipality_admin']}
  ```
- **Corrección ejecutada:**
  ```tsx
  roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator']}
  ```
  Cualquier intento de navegación directa por parte de roles administrativos es interceptado por `RequireAuth`, provocando una redirección inmediata y segura a `/dashboard`.

### 4.3 Frontend — Tarjetas de Acceso en Dashboard (`Dashboard.tsx`)
- **Estado previo al hallazgo:** La condición `isPlatformAdminWithContext` habilitaba la tarjeta máster "Módulo de Gestión Académica" y sus 8 accesos directos a `national_admin` y `department_admin` si existía un `activeInstitutionId` en memoria o localStorage.
- **Corrección ejecutada:** Se eliminó por completo `isPlatformAdminWithContext`, restringiendo la renderización de la tarjeta de gestión académica estrictamente a `isInstitutionalDirective`.

### 4.4 Frontend — Pestañas y Acciones Internas en el Hub Académico (`AcademicHub.tsx`)
- **Estado previo al hallazgo:** Las comprobaciones de rol interno `isDirective` y las restricciones de pestañas sensibles (`coordinators`, `settings`) incluían a `superadmin`, `national_admin`, `department_admin` y `municipality_admin`.
- **Corrección ejecutada:** En cumplimiento del principio de defensa en profundidad, `isDirective` se blindó para aceptar únicamente directivos de sede (`rector`, `coordinator`, `academic_coordinator`, `institution_admin`), y las pestañas `coordinators` y `settings` quedaron limitadas a `['rector', 'institution_admin']`.

### 4.5 Backend — Inyección de Dependencias y Resolución de Contexto (`deps.py`)
- Los endpoints académicos en `backend/app/api/v1/endpoints/` (`academic_years.py`, `grades.py`, `subjects.py`, `groups.py`, `students.py`, `teachers.py`, `enrollments.py`, `academic_assignments.py`) invocan la función `resolve_institution_id()`.
- Cuando un usuario administrativo sin sede fija (`institution_id = None`) invoca un endpoint académico sin proveer explícitamente un contexto de institución validado en su jurisdicción, el backend falla cerrado arrojando `HTTP 403 (PERMISSION_DENIED / INSTITUTION_CONTEXT_REQUIRED)`.
- Adicionalmente, el servicio `rbac_bootstrap_service.py` no asigna permisos de escritura (`academic_years:create`, `grades:create`, `students:create`, etc.) a `national_admin`, `department_admin` ni `municipality_admin`, garantizando la imposibilidad de mutaciones no autorizadas.

---

## 5. Preservación del Acceso Legítimo a Nivel Institucional

Se verificó minuciosamente que la eliminación de acceso a los roles macro-administrativos no afecte las operaciones de los roles educativos legítimos:

1. **Rector / Director Institucional (`rector`, `institution_admin`):**
   - Retiene acceso total a todas las pestañas de `AcademicHub`.
   - Control exclusivo de la habilitación de delegación operativa para coordinadores (`coordinator_delegation_enabled`).
   - Acceso exclusivo a la pestaña "Configuración Institucional" y asignación de coordinadores.
2. **Coordinadores (`coordinator`, `academic_coordinator`):**
   - Retienen acceso a años lectivos, periodos, grados, asignaturas, grupos, estudiantes SIMAT, planta docente, acudientes, matrículas, traslados, carga académica y evaluaciones.
   - Restricción de pestañas no delegadas (`coordinators`, `settings`).
3. **Docentes (`teacher`):**
   - Mantienen su acceso independiente al Portal Docente (`/teacher`), libros de calificaciones SIEE, asistencia, aulas virtuales y observaciones disciplinarias.
4. **Estudiantes y Acudientes (`student`, `guardian`):**
   - Mantienen acceso exclusivo a sus respectivos portales protegidos (`/student`, `/guardian`), boletines y aulas virtuales.
5. **Módulos No Afectados para Roles Administrativos:**
   - Se mantiene intacto el acceso de los administradores a sus consolas asignadas:
     - Analítica Territorial: `/analytics/territorial`
     - Centro de Control Territorial: `/admin/control-center`
     - Catálogo Nacional y Aprovisionamiento: `/admin/institutions`, `/admin/onboarding`
     - Directorio Territorial de Usuarios: `/admin/users`
     - Operaciones Técnicas Globales (SuperAdmin): `/operations/*`

---

## 6. Escalación Técnica sobre el Comodín de SuperAdmin en Backend

Durante la inspección del backend se identificó que el rol `superadmin` cuenta con el permiso universal técnico `*:*`.
- En la prueba de integración de Fase 3B (`test_academic_e2e_integration.py` líneas 770-777), se valida explícitamente que el `superadmin` pueda consultar registros de una institución específica utilizando el parámetro de consulta `?institution_id=`.
- **Análisis de Riesgo:**
  - En el frontend, el SuperAdmin ha quedado estrictamente desprovisto de rutas, menús, enlaces y paneles de gestión académica, canalizándose su experiencia exclusivamente hacia el Portal de Operaciones Técnicas (SA-02: salud de plataforma, métricas Prometheus, auditoría de seguridad, soporte técnico y diagnósticos de inquilino).
  - En la API backend, el comodín `*:*` existe actualmente para tareas de mantenimiento de bajo nivel, soporte de emergencia y recuperación ante desastres (*break-glass*).
- **Recomendación y Escalación al Product Owner:**
  - Mantener la separación estricta en el Frontend UI ya implementada.
  - Solicitar al Product Owner decisión formal sobre si se desea mantener el acceso técnico `*:*` en la API backend para contingencias de soporte o si se requiere introducir un filtro que bloquee al `superadmin` incluso en los endpoints REST académicos a menos que se use una cabecera de auditoría explícita (`X-PEVN-Break-Glass: emergency`).

---

## 7. Verificación Automatizada y Resultados de Pruebas

Para asegurar la no-regresión y certificar la efectividad de las protecciones, se ejecutaron suites de pruebas automáticas en frontend y backend:

### 7.1 Pruebas Frontend (Vitest & React Testing Library)
- **`CrossRoleNavigationAudit.test.tsx` (9/9 pruebas aprobadas):**
  - Confirma que `MUNICIPALITY_ADMIN` intentando acceder a `/academic` es rechazado y redirigido a `/dashboard`.
  - Confirma que `DEPARTMENT_ADMIN` intentando acceder a `/academic` es rechazado y redirigido a `/dashboard` incluso con contexto institucional activo en sesión.
  - Confirma que `RECTOR` con contexto activo accede satisfactoriamente a `AcademicHub`.
  - Confirma que `DEPARTMENT_ADMIN` accediendo a `/virtual-classrooms` sin contexto es redirigido a selección de contexto preservando `returnTo`.
  - Confirma bloqueo de accesos maliciosos y parámetros de redirección abierta.
- **`RoleNavigationFunctional.test.tsx` (16/16 pruebas aprobadas):**
  - Confirma que la barra de navegación no expone "Académica" a administradores territoriales (`department_admin`, `national_admin`, etc.).
  - Confirma que la barra de navegación expone "Académica" a directivos escolares (`rector`, `academic_coordinator`).
  - Confirma que el panel principal no renderiza tarjetas académicas para administradores territoriales aún con contexto activo.
  - Confirma que `RequireAuth` bloquea el acceso directo a `/academic` para el `superadmin`.
- **Suite Completa Frontend:**
  - `npm run typecheck`: **0 errores** de tipado TypeScript.
  - `npm run test`: **29/29 suites de prueba aprobadas**, **200/200 pruebas aprobadas** en 20.30s.
  - `npm run build`: Compilación para producción en Vite exitosa (código minificado y PWA generada en 5.54s).

### 7.2 Pruebas Backend (Pytest)
- **`pytest test_academic_api.py test_academic_e2e_integration.py`:**
  - **15/15 pruebas aprobadas** en 66.56s.
  - Verificación de barreras multi-tenant, ciclo de vida de años lectivos, grupos, docentes, estudiantes y asignaciones académicas.
- **`pytest test_sa01_superadmin_governance.py test_sa02_technical_operations_portal.py`:**
  - **16/16 pruebas aprobadas** en 25.84s.
  - Verificación de la estricta separación de responsabilidades del SuperAdmin en la consola de operaciones técnicas.

---

## 8. Archivos Modificados en la Remediación

1. `frontend/src/layouts/RootLayout.tsx`
   - Remoción de roles administrativos y de permisos globales de lectura en `canAccessAcademic`.
2. `frontend/src/App.tsx`
   - Restricción estricta de la guarda de ruta `/academic` a los cuatro roles directivos escolares institucionales.
3. `frontend/src/pages/Dashboard.tsx`
   - Eliminación del bypass `isPlatformAdminWithContext` en la visualización de tarjetas de gestión académica.
4. `frontend/src/pages/academic/AcademicHub.tsx`
   - Saneamiento de `isDirective` y remoción de roles administrativos en las pestañas `coordinators` y `settings`.
5. `frontend/src/test/CrossRoleNavigationAudit.test.tsx`
   - Actualización de aserciones de navegación y validación de rechazo de roles administrativos a `/dashboard`.
6. `frontend/src/test/RoleNavigationFunctional.test.tsx`
   - Incorporación de pruebas exhaustivas de visibilidad en menú, renderizado condicional en dashboard y guarda de ruta `/academic`.

---

## 9. Conclusión del Auditor

La plataforma PEVN queda blindada con respecto a la separación funcional entre la gobernanza macro-territorial/técnica y la autonomía operativa de las instituciones educativas. 

Los cuatro roles administrativos (`SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`) no tienen visibilidad ni acceso a la gestión académica escolar, cerrando de forma concluyente cualquier vector de extralimitación de funciones en conformidad con las directrices del Product Owner y la normativa del Ministerio de Educación Nacional.

---

## 10. Seguimiento y Cierre Definitivo de Seguridad: Blindaje de API Backend Académica (Least Privilege)

### 10.1 Antecedentes del Hallazgo Residual
Tras la remediación exitosa del frontend (menús, rutas, tarjetas y pestañas), la auditoría forense identificó una preocupación residual en la capa de autorización backend:
1. El rol `superadmin` poseía el permiso comodín universal `*:*`, y el método `authorize()` en `CentralizedAuthorizationService` contenía un bypass incondicional (`if SystemRole.SUPERADMIN in context.roles: return True`) que le permitía ejecutar consultas y mutaciones sobre endpoints académicos si proporcionaba `?institution_id=` o cabeceras de contexto (`X-Institution-Context`).
2. Los roles territoriales (`national_admin`, `department_admin`, `municipality_admin`) mantenían en `ROLE_PERMISSIONS_CONFIG` (`backend/app/services/rbac_bootstrap_service.py`) permisos de lectura sobre entidades académicas locales (`academic_years:read`, `academic_periods:read`, `subjects:read`, `groups:read`, `teachers:read`, `students:read`, `guardians:read`, `enrollments:read`, `academic_assignments:read`, `coordinators:read`), permitiéndoles teóricamente invocar directamente las API REST de consulta institucional.

### 10.2 Decisión Vinculante del Product Owner
En estricta consonancia con el principio de mínimo privilegio (*least privilege*) y la doctrina de separación de poderes de la PEVN:
- **Ninguno de los cuatro roles administrativos** (`SUPERADMIN`, `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN`, `MUNICIPALITY_ADMIN`) debe tener acceso ordinario (ni lectura ni escritura) a los endpoints protegidos de Gestión Académica e Institucional.
- El comodín técnico `*:*` **no debe eludir** la restricción específica del módulo académico escolar.
- La protección debe ser implementada de forma centralizada y consistente en el motor de autorización, preservando intactos los flujos educativos de directivos institucionales (`rector`, `institution_admin`, `coordinator`, `academic_coordinator`, `teacher`, `student`, `guardian`) y la operatividad técnica y territorial de los administradores (`operations`, `institutions`, `analytics/territorial`, `virtual_classrooms`).

### 10.3 Arquitectura de la Remediación Backend Implementada

1. **Definición Centralizada de Recursos Académicos y Roles Educativos (`authorization.py`):**
   - Se definieron los conjuntos inmutables:
     - `ACADEMIC_MANAGEMENT_RESOURCES`: `{'academic_years', 'academic_periods', 'academic_assignments', 'academic_promotions', 'subjects', 'groups', 'teachers', 'students', 'guardians', 'enrollments', 'siee_policies', 'evaluations', 'report_cards', 'promotions', 'coordinators', 'activities', 'submissions', 'attendance', 'planning'}`.
     - `INSTITUTIONAL_EDUCATIONAL_ROLES`: `{'rector', 'institution_admin', 'coordinator', 'academic_coordinator', 'teacher', 'student', 'guardian'}`.

2. **Blindaje del Motor Centralizado de Autorización (`CentralizedAuthorizationService.authorize`):**
   - **Regla Estricta de Rol Institucional:** Si el recurso solicitado pertenece a `ACADEMIC_MANAGEMENT_RESOURCES`, se exige taxativamente que el usuario cuente con al menos un rol de `INSTITUTIONAL_EDUCATIONAL_ROLES`. Usuarios con roles exclusivamente administrativos son rechazados de inmediato (`return False`) con log de advertencia y auditoría forense (`HTTP 403 PERMISSION_DENIED`).
   - **Contención del Comodín SuperAdmin:** El bypass global de superadmin fue acotado: `if SystemRole.SUPERADMIN in context.roles and not is_academic_resource: return True`.
   - **Restricción de Coincidencia de Permiso Comodín:** La comprobación granular impide que el comodín `*` cubra recursos académicos: `(perm.resource == required_permission.resource or (perm.resource == "*" and not is_academic_resource))`.

3. **Saneamiento del Bootstrap de Permisos (`rbac_bootstrap_service.py`):**
   - Se removieron todos los permisos de lectura académica (`academic_years:read`, `subjects:read`, `teachers:read`, `students:read`, `enrollments:read`, etc.) de las configuraciones de `NATIONAL_ADMIN`, `DEPARTMENT_ADMIN` y `MUNICIPALITY_ADMIN`.

4. **Depuración de Helpers y Controladores Académicos:**
   - `academic_scope_helper.py`: Se restringió `DIRECTIVE_ROLES` exclusivamente a directivos de sede (`INSTITUTION_ADMIN`, `RECTOR`, `COORDINATOR`, `ACADEMIC_COORDINATOR`), suprimiendo el bypass de nivel nacional y superadmin.
   - `evaluation_grades.py`: Se removió el bypass directo de `superadmin` y `national_admin` en `_resolve_institution_id` y `DIRECTIVE_ROLES`.
   - `deps.py`: La verificación de delegación rectoral `assert_coordinator_delegation_allowed` evalúa estrictamente `{'rector', 'institution_admin'}`, excluyendo roles administrativos externos.

### 10.4 Evaluación del Mecanismo de Emergencia Técnica (*Break-Glass*)
- **Inspección de Mecanismos Preexistentes:** La auditoría constató que el repositorio posee un mecanismo documentado para la recuperación de la cadena de autoridad institucional (`SUPERADMIN_EMERGENCY_ROLE_PROVISIONING` para aprovisionamiento de emergencia de Rector o Administrador Municipal). Sin embargo, **NO** existe ningún mecanismo de emergencia aprobado ni documentado para la gestión académica ordinaria (calificaciones, matrículas, años lectivos).
- **Tratamiento del Acceso:** En estricto cumplimiento del mandato de auditoría, **no se inventó ningún mecanismo no aprobado**. Todo acceso ordinario por parte de los 4 roles administrativos falla cerrado con `HTTP 403 Forbidden`.
- **Propuesta Sometida a Decisión del Product Owner:**
  - *Si en el futuro se aprobara un protocolo de contingencia L3 para soporte técnico*, este deberá exigir:
    1. Cabecera criptográfica explícita: `X-PEVN-Break-Glass-Signature`.
    2. Identificador de ticket de soporte validado en Jira/ITSM: `X-PEVN-Emergency-Ticket-ID`.
    3. Registro inmutable sincrónico en base de datos con `AuditEventType.BREAK_GLASS_ACTIVATED`.
    4. Ventana de tiempo restringida (Time-To-Live de 15 minutos).
  - *Hasta tanto no sea formalmente aprobado por el Product Owner, la política permanece en fallo cerrado absoluto (Closed by Default).*

### 10.5 Matriz de Decisión y Verificación Backend por Rol

| Rol Administrativo | Lectura Académica API con `?institution_id=` | Escritura Académica API con `?institution_id=` | Estado de Cierre | Justificación Técnica |
| :--- | :---: | :---: | :---: | :--- |
| **`SUPERADMIN`** | ❌ **403 FORBIDDEN** | ❌ **403 FORBIDDEN** | **CERRADO** | Comodín `*:*` neutralizado para recursos académicos; denegado por falta de rol educativo institucional. |
| **`NATIONAL_ADMIN`** | ❌ **403 FORBIDDEN** | ❌ **403 FORBIDDEN** | **CERRADO** | Permisos de lectura revocados en RBAC bootstrap; denegado en motor de autorización. |
| **`DEPARTMENT_ADMIN`** | ❌ **403 FORBIDDEN** | ❌ **403 FORBIDDEN** | **CERRADO** | Permisos de lectura revocados en RBAC bootstrap; denegado en motor de autorización. |
| **`MUNICIPALITY_ADMIN`** | ❌ **403 FORBIDDEN** | ❌ **403 FORBIDDEN** | **CERRADO** | Permisos de lectura revocados en RBAC bootstrap; denegado en motor de autorización. |

*Contraste con roles educativos autorizados:*
- **`RECTOR` / `INSTITUTION_ADMIN`:** Retiene acceso total a lectura (`HTTP 200 OK`) y mutación (`HTTP 201 Created`) dentro de su institución asignada, manteniendo blindaje de frontera contra instituciones ajenas (`HTTP 403 Forbidden`).
- **Módulos Administrativos Autorizados:** `superadmin` conserva acceso íntegro a Operaciones Técnicas (`/system/operations/health` -> `200 OK`), y las autoridades territoriales a Catálogo Nacional y Analítica Territorial (`/institutions`, `/analytics/territorial/summary` -> `200 OK`).

### 10.6 Evidencia Automatizada de Cierre

1. **`backend/tests/test_academic_admin_roles_authorization.py` (7/7 APROBADAS):**
   - `test_01_superadmin_denied_academic_read_and_write`: SuperAdmin recibe 403 en `GET /academic-years` y `POST /academic-years`.
   - `test_02_national_admin_denied_academic_read_and_write`: National Admin recibe 403 en lectura y escritura.
   - `test_03_department_admin_denied_academic_read_and_write`: Department Admin recibe 403 en lectura y escritura.
   - `test_04_municipality_admin_denied_academic_read_and_write`: Municipality Admin recibe 403 en lectura y escritura.
   - `test_05_rector_retains_academic_management_access`: Rector crea y lee años lectivos con 201 y 200.
   - `test_06_tenant_isolation_rector_cannot_access_foreign_institution`: Rector de Institución A no puede acceder a Institución B.
   - `test_07_authorized_administrative_modules_remain_functional`: Operaciones del sistema, analítica territorial y catálogo de instituciones continúan 100% funcionales para los roles administrativos.

2. **`backend/tests/test_academic_e2e_integration.py` (2/2 APROBADAS):**
   - Se actualizó el paso 5 de frontera RBAC verificando que `superadmin`, `national_admin`, `department_admin` y `municipality_admin` sean unánimemente rechazados (403) al intentar leer o crear años lectivos en una institución inquilina.

3. **`backend/tests/test_sa01_superadmin_governance.py` & `test_sa02_technical_operations_portal.py` (16/16 APROBADAS):**
   - Certifica que la gobernanza global del SuperAdmin y la consola de operaciones técnicas operan con normalidad, y que el intento de consultar `/academic-years` incluso con `X-Institution-Context` es rechazado con 403 conforme a la política de mínimo privilegio.

4. **Suite Completa Backend Certificada:**
   - **38 pruebas backend ejecutadas y aprobadas (100% éxito)** sin regresiones.


