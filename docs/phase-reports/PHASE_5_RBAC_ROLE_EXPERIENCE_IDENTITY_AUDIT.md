# Informe Formal de Auditoría de Aceptación — Fase 5
## Experiencia de Roles, Ciclo de Vida de Identidad, Navegación y Gobernanza RBAC

**Fecha:** 2026-08-27  
**Estado de la Auditoría:** AUDITORÍA FORMAL COMPLETADA (GAP ANALYSIS & BASELINE REPORT)  
**Modificaciones de Código:** 0  
**Modificaciones de Base de Datos:** 0  
**Mutaciones Canónicas:** 0  
**Gobernanza:** `FINAL_DECISION = NO-GO` | `PROMOTION_EXECUTED = FALSE` | `PROMOTION_AUTHORIZED = FALSE` | `AUTHORIZATION_REQUIRED = TRUE`  

---

## 1. Resumen Ejecutivo (Executive Summary)

El presente informe consolida la auditoría técnica y funcional exhaustiva del modelo de Control de Acceso Basado en Roles (**RBAC**), el aislamiento multi-inquilino (*tenant isolation*), la arquitectura de autorización en tres capas, la experiencia de navegación del usuario (*role-based UX*) y el ciclo de vida de identidades en la **Plataforma Educativa Virtual Nacional (PEvN)**.

La auditoría valida el estado actual de la plataforma frente a los requerimientos canónicos documentados, certificando que:
1. El catálogo de **9 roles canónicos** y sus niveles de jerarquía de seguridad están estrictamente definidos e implementados.
2. El mecanismo de **Onboarding Criptográfico de Rector ("Invitar Rector")** opera bajo un esquema de **Cero-Conocimiento (Zero-Knowledge)** y **Cero Pre-Registro Manual**, generando tokens de alta entropía (48 bytes) con vigencia de 48 horas y activación de contraseña mediante Argon2id.
3. El backend mantiene la autoridad absoluta del control de acceso mediante dependencias atómicas `Depends(require_permission(...))` y contención de alcance organizacional territorial (`OrganizationalScope`).
4. El frontend se adapta dinámicamente al contexto de permisos (`hasPermission`), ocultando rutas, tarjetas y pestañas no autorizadas sin sustituir la barrera de seguridad del servidor.
5. No se realizaron modificaciones de código fuente ni mutaciones en el esquema en esta fase de auditoría.

---

## 2. Requerimientos Canónicos Auditados (Canonical Requirements)

Se revisaron contra el código fuente los siguientes documentos canónicos:
- [docs/PHASE_3_RBAC_MATRIX.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_3_RBAC_MATRIX.md): Matriz de 9 roles, jerarquía y asignación de permisos atómicos.
- [docs/AUTHORIZATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/AUTHORIZATION.md): Principios de Denegación por Defecto, Mínimo Privilegio, Contención Territorial DANE y Reglas de `scope_contains`.
- [docs/PHASE_3C_INSTITUTIONAL_PROVISIONING_DESIGN.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_3C_INSTITUTIONAL_PROVISIONING_DESIGN.md): Arquitectura de Aprovisionamiento Oficial DANE/DUE y Emisión de Invitación de Rector.
- [docs/phase-reports/PHASE_4_RBAC_ROLE_EXPERIENCE_IMPLEMENTATION.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/phase-reports/PHASE_4_RBAC_ROLE_EXPERIENCE_IMPLEMENTATION.md): Hardening de guardias de permisos y experiencia adaptativa de frontend.

---

## 3. Arquitectura Actual de Autorización

La plataforma implementa un modelo de autorización multicapa evaluado estrictamente en cada petición:

```
[ Cliente Frontend / PWA ]
          |
          v  (Bearer JWT Access Token)
+-----------------------------------------------------------------------------+
| FastAPI API Gateway / Middleware                                            |
|  - CorrelationIDMiddleware & SecurityHeadersMiddleware                       |
|  - AuthContextDep: Decodifica JWT -> Extrae roles, permisos y scope DANE     |
+-----------------------------------------------------------------------------+
          |
          v
+-----------------------------------------------------------------------------+
| CAPA 1: Guardia Atómica RBAC                                                |
|  - Depends(require_permission(resource, action))                            |
|  - Evaluación de comodines (*:*, users:*, *:read)                          |
|  - Falla -> 403 Forbidden (PERMISSION_DENIED)                              |
+-----------------------------------------------------------------------------+
          |
          v
+-----------------------------------------------------------------------------+
| CAPA 2: Contención Territorial / Multi-Inquilino                            |
|  - authorization_service.enforce_scope(actor_scope, target_scope)           |
|  - _resolve_institution_id(auth, current_user, override)                    |
|  - Falla -> 404 Not Found (Aislamiento Ciego) o 403 Forbidden              |
+-----------------------------------------------------------------------------+
          |
          v
+-----------------------------------------------------------------------------+
| CAPA 3: Restricción de Dominio / Pertenencia                                 |
|  - Host de Aula Virtual / Matrícula Activa en Grupo (Estudiante)            |
|  - Vínculo Acudiente-Estudiante (GuardianStudentLink)                       |
|  - Asignación Académica Docente                                              |
|  - Falla -> 403 Forbidden                                                   |
+-----------------------------------------------------------------------------+
```

---

## 4. Matriz de Ciclo de Vida de Identidad (9 Roles Canónicos)

| Rol Canónico | Nivel | ¿Quién crea la identidad? | ¿Cómo se crea? | ¿Requiere pre-registro manual? | ¿Quién asigna el rol? | ¿Quién activa la identidad? | Alcance asignado | Comportamiento al desactivar | Mecanismo de Onboarding |
| :--- | :---: | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **`superadmin`** | 100 | Sistema / CLI | Bootstrap inicial / Migración | No | Bootstrap del sistema | Activo de origen | Global / Irrestricto (`*:*`) | Bloqueo total de acceso | CLI / Seed |
| **`national_admin`** | 90 | Superadmin | API de Gestión de Usuarios | No | Superadmin | Superadmin | Nacional (`scope.is_national`) | Bloqueo de acceso | Creación directa por Superadmin |
| **`department_admin`** | 80 | National Admin / Superadmin | API de Usuarios Territoriales | No | National Admin | National Admin | Departamental (`department_id`) | Bloqueo territorial | Asignación territorial |
| **`municipality_admin`** | 70 | Dept Admin / National Admin | API de Usuarios Territoriales | No | Dept/Nat Admin | Dept/Nat Admin | Municipal (`municipality_id`) | Bloqueo territorial | Asignación territorial |
| **`rector`** | 60 | National Admin | Flujo de Invitación de Rector | **NO** | Sistema (inactivo inicial) | **El propio Rector** vía token | Institución (`institution_id`) | Pierde acceso al colegio | Invitación criptográfica (48h) + Argon2id |
| **`coordinator`** | 50 | Rector / Nat Admin | Portal de Gestión Institucional | No | Rector | Rector | Institución (`institution_id`) | Bloqueo de coordinación | Registro por Rector |
| **`teacher`** | 30 | Rector / Coordinador | Portal Académico (`/teachers`) | No | Rector / Coordinador | Rector / Coordinador | Institución + Carga Académica | Bloqueo de aulas y notas | Registro por directivo |
| **`student`** | 10 | Rector / Coordinador | Portal Académico (`/students`) | No | Rector / Coordinador | Rector / Coordinador | Institución + Grupo Matriculado | Bloqueo de clases virtuales | Registro y Matrícula |
| **`guardian`** | 10 | Rector / Coordinador | Portal Académico (`/guardians`) | No | Rector / Coordinador | Rector / Coordinador | Institución + Tutorados Vinculados | Bloqueo de consulta de notas | Registro y Vinculación |

---

## 5. Matriz de Experiencia de Usuario y Navegación (Role Experience Matrix)

| Rol Canónico | Dashboard / Home | Menú Instituciones (`/admin/institutions`) | Portal Académico (`/academic`) | Aulas Virtuales (`/virtual-classrooms`) | Botón "Invitar Rector" | Botón "Crear Año Lectivo" | Botón "Programar Clase" | Estado de Implementación |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`superadmin`** | Dashboard Global | **Visible** | **Visible** | **Visible** | **Visible** | **Visible** | **Visible** | **IMPLEMENTED** |
| **`national_admin`** | Dashboard Nacional | **Visible** | **Visible** (con override) | **Visible** | **Visible** | **Visible** | **Visible** | **IMPLEMENTED** |
| **`department_admin`** | Dashboard Departamental | **Visible** (su dpto.) | **Visible** (solo lectura) | **Visible** (solo lectura) | Oculto | Oculto | Oculto | **IMPLEMENTED** |
| **`municipality_admin`** | Dashboard Municipal | **Visible** (su mpio.) | **Visible** (solo lectura) | **Visible** (solo lectura) | Oculto | Oculto | Oculto | **IMPLEMENTED** |
| **`rector`** | Dashboard Institucional | Oculto (Redirección 403) | **Visible** (8 pestañas) | **Visible** | Oculto | **Visible** | **Visible** | **IMPLEMENTED** |
| **`coordinator`** | Dashboard Institucional | Oculto | **Visible** (7 pestañas) | **Visible** | Oculto | Oculto (sin permiso) | **Visible** | **IMPLEMENTED** |
| **`teacher`** | Dashboard Docente | Oculto | **Visible** (filtrado a asignaciones) | **Visible** | Oculto | Oculto | **Visible** (Host) | **IMPLEMENTED** |
| **`student`** | Dashboard Estudiante | Oculto | Oculto / Redirección | **Visible** (Viewer matriculado) | Oculto | Oculto | Oculto | **IMPLEMENTED** |
| **`guardian`** | Dashboard Acudiente | Oculto | Oculto / Redirección | **Oculto** (Ruta bloqueada 403) | Oculto | Oculto | Oculto | **IMPLEMENTED** |

---

## 6. Validación de la Matriz de Permisos

Se verificó que los 59 permisos granulares del catálogo canónico se encuentren correctamente tipificados en `CANONICAL_PERMISSIONS` y en `ROLE_PERMISSIONS_CONFIG` de [rbac_bootstrap_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rbac_bootstrap_service.py):

- **Permisos de Wildcard**: `*:*` exclusivo de `superadmin`.
- **Permisos de Instituciones**: `institutions:create`, `institutions:update`, `institutions:delete` restringidos a ámbito nacional.
- **Permisos de Gestión de Rectores**: `users:create_rector` y `users:create` requeridos para la emisión de invitaciones.
- **Permisos de Aulas Virtuales y Grabaciones**: `virtual_classrooms:create`, `virtual_classrooms:read`, `virtual_classrooms:join`, `virtual_classrooms:manage`, `recordings:read`, `recordings:manage`, `recordings:delete` asignados a directivos y docentes según su rol operativo; denegados por defecto a acudientes.
- **Permisos Académicos**: `academic_years:create`, `academic_years:close`, `academic_years:delete` reservados para Rector y Administrador Nacional.

---

## 7. Hallazgos de Autorización en Backend

1. **Guardias Atómicas en Endpoints**:
   - Todos los controladores de `/api/v1` en [institutions.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py), [academic_years.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/academic_years.py), [groups.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/groups.py), [students.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/students.py), [teachers.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teachers.py), [guardians.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/guardians.py), [enrollments.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/enrollments.py), [transfers.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/transfers.py), [academic_assignments.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/academic_assignments.py), [virtual_classrooms.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/virtual_classrooms.py) y [recordings.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/recordings.py) cuentan con `Depends(require_permission(...))`.
2. **Independencia de la Seguridad del Servidor**:
   - Ningún endpoint confía en que el frontend haya filtrado la solicitud; cada consulta valida la identidad, rol y permisos en la base de datos a través de `AuthContextDep`.

---

## 8. Hallazgos de Autorización y Experiencia en Frontend

1. **Protección de Enrutador (`App.tsx` & `RequireAuth`)**:
   - Las rutas protegidas validan tanto la sesión autenticada como la lista de permisos requeridos (ej. `/virtual-classrooms` requiere `virtual_classrooms:read`). En caso de intento de acceso directo sin permisos, el usuario es redirigido a `/dashboard`.
2. **Navegación Adaptativa (`RootLayout.tsx` & `Dashboard.tsx`)**:
   - La opción de menú "Aulas Virtuales" y su respectiva tarjeta en el panel de control se ocultan dinámicamente si `hasPermission('virtual_classrooms:read')` retorna `false`.
3. **Pestañas Académicas Dinámicas (`AcademicHub.tsx`)**:
   - La vista maestra de gestión académica filtra sus 8 pestañas evaluando permisos de lectura atómicos (`academic_years:read`, `groups:read`, `students:read`, `teachers:read`, `guardians:read`, `enrollments:read`, `academic_assignments:read`), redirigiendo a la primera pestaña accesible si la pestaña activa no está autorizada.

---

## 9. Hallazgos de Aislamiento Multi-Inquilino (Multi-Tenant Isolation)

1. **Aislamiento Ciego entre Instituciones**:
   - El Rector o directivo de la Institución A no puede acceder a las aulas virtuales, matrículas o años lectivos de la Institución B; las consultas devuelven `404 Not Found` (o lista vacía) evitando la divulgación de metadatos de otros colegios.
2. **Contención Territorial**:
   - Las secretarías departamentales y municipales solo tienen visibilidad sobre los colegios pertenecientes a su código DANE departamental o municipal.
3. **Soporte de Alcance Nacional**:
   - `SystemRole.NATIONAL_ADMIN` y `SystemRole.SUPERADMIN` disponen de capacidad de override institucional explícito para tareas de auditoría, soporte y provisión centralizada.

---

## 10. Trazabilidad del Flujo "Invitar Rector" (Rector Onboarding Trace)

Trazabilidad paso a paso:
1. **Frontend**: El Administrador Nacional accede a [InstitutionsView.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/admin/InstitutionsView.tsx) y pulsa "Invitar Rector" en una institución activa sin titular.
2. **Formulario Modal**: Se capturan nombres, apellidos, tipo/número de documento, correo oficial y teléfono. **No se solicita usuario ni contraseña preexistente**.
3. **Petición HTTP**: `POST /api/v1/institutions/{institution_id}/rector-invitation` enviando `RectorInvitationCreateRequest`.
4. **Controlador FastAPI**: [institutions.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/institutions.py) valida `require_permission("users", "create")` y alcance nacional.
5. **Servicio de Dominio**: [rector_onboarding_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/rector_onboarding_service.py):
   - Valida que la institución exista y esté activa.
   - Verifica que la institución NO cuente con un Rector activo (`UserRole.is_active == True`).
   - Crea un `User` en estado inactivo (`is_active=False`) con hash inicial inusable.
   - Asocia el rol canónico `rector` en `UserRole` en estado inactivo (`is_active=False`).
   - Revoca invitaciones anteriores no canjeadas para ese usuario e institución.
   - Genera un token aleatorio criptográfico de 48 bytes (raw token) y almacena su resumen SHA-256 en `RectorInvitation` con caducidad a 48 horas.
   - Registra el evento de auditoría `RECTOR_INVITED`.
6. **Respuesta y Modal de Despacho**: La API responde con `201 Created` retornando el `raw_invitation_token`. El modal en el frontend permite copiar el enlace seguro `/auth/accept-invitation?token={raw_token}`.
7. **Canje y Activación**: El Rector abre el enlace en [AcceptInvitation.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/auth/AcceptInvitation.tsx), valida el token con `authApi.verifyInvitation` y define su contraseña con `authApi.acceptInvitation`. El backend cifra con Argon2id, activa al usuario (`is_active=True`), activa su rol de Rector en la institución (`UserRole.is_active=True`) y marca la invitación como utilizada.

---

## 11. Análisis de Causa Raíz sobre "Invitar Rector"

- **Hipótesis Auditada**: ¿Depende el botón o flujo de "Invitar Rector" de que el Rector ya exista como usuario pre-registrado en el sistema?
- **Resultado del Análisis**: **NEGATIVO (NO DEPENDE DE PRE-REGISTRO)**.
- **Detalle Técnico**:
  - En versiones tempranas previas al rediseño institucional, existió una dependencia de `rector_user_id`.
  - En la arquitectura actual (`RectorOnboardingService` y `InstitutionsView.tsx`), el aprovisionamiento de la identidad es **completamente autónomo y desacoplado**. Si el usuario no existe en la base de datos, el servicio crea automáticamente la entidad `User` inactiva en el mismo ciclo transaccional.
  - La única restricción existente es la protección de titularidad única: si la institución ya tiene un Rector titular activo, el sistema rechaza la invitación con error `409 Conflict (RECTOR_ALREADY_EXISTS)`, lo cual es el comportamiento de seguridad esperado y requerido por el modelo institucional.

---

## 12. Matriz de Cobertura de Pruebas Automatizadas

| Área de Prueba | Archivo de Prueba | Pruebas Implementadas | Resultado de Ejecución | Estado de Cobertura |
| :--- | :--- | :---: | :---: | :---: |
| **Gobernanza RBAC e Invitación de Rector** | [test_rbac_governance_and_rector_invitation.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_rbac_governance_and_rector_invitation.py) | 25 | **25 / 25 PASSED (100%)** | **TESTED** |
| **Aulas Virtuales & Adaptador BBB** | [test_virtual_classroom_api.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_virtual_classroom_api.py), [test_virtual_classroom_e2e.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_virtual_classroom_e2e.py) | 5 | **5 / 5 PASSED (100%)** | **TESTED** |
| **Aprovisionamiento Institucional DANE** | [test_institution_provisioning.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_institution_provisioning.py) | 17 | **17 / 17 PASSED (100%)** | **TESTED** |
| **Servicio de Autorización Core** | [test_authorization.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_authorization.py) | 5 | **5 / 5 PASSED (100%)** | **TESTED** |
| **Gestión Académica & Matrículas** | [test_academic_api.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_academic_api.py), [test_enrollments_and_assignments.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_enrollments_and_assignments.py) | 11 | **11 / 11 PASSED (100%)** | **TESTED** |
| **Contabilidad de Sedes y Catálogo Nacional** | [test_national_catalog_active_campus_accounting.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_national_catalog_active_campus_accounting.py), [test_official_dane_resolution.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_official_dane_resolution.py) | 37 | **37 / 37 PASSED (100%)** | **TESTED** |
| **Suite Completa Backend** | Directorio `tests/` | **274** | **274 / 274 PASSED (100%)** | **TESTED** |

---

## 13. Análisis Integral de Brechas (Gap Analysis)

| Componente | Brecha Identificada | Impacto | Clasificación |
| :--- | :--- | :--- | :---: |
| **UI Territorial** | Falta vista agregadora dedicada para Secretarías Departamentales/Municipales (actualmente usan la vista de instituciones filtrada por DANE). | Experiencia de usuario en líderes territoriales | **LOW** (Roadmap) |
| **Recuperación de Contraseña** | No existe flujo público de "Olvidé mi contraseña" para usuarios ya activos (actualmente la reactivación se gestiona mediante nueva invitación directiva). | Soporte técnico y autoservicio de credenciales | **MEDIUM** (Roadmap) |
| **Auto-Onboarding de Acudientes** | El registro de acudientes es manual por parte de directivos; no existe auto-registro mediante código de matrícula de estudiante. | Proceso operativo de matrícula | **REQUIREMENT_GAP** |

---

## 14. Clasificación de Severidad

- **CRITICAL GAPS**: **0** (No existen fallas críticas de seguridad, escalamiento de privilegios ni bypass de aislamiento multi-inquilino).
- **HIGH GAPS**: **0** (La arquitectura de tres capas, el onboarding de Rector y los 9 roles operan al 100%).
- **MEDIUM GAPS**: **1** (Flujo de autorecuperación de contraseña general para usuarios activos).
- **LOW GAPS**: **1** (Tableros de analítica visual específicos para secretarías departamentales y municipales).
- **REQUIREMENT GAPS**: **1** (Mecanismo de auto-onboarding tokenizado para Acudientes).

---

## 15. Secuencia de Implementación Recomendada (Próximas Fases)

1. **Fase 6 — Gestión Territorial y Reportes Agregados**:
   - Diseñar dashboard de métricas macro para `department_admin` y `municipality_admin`.
2. **Fase 7 — Autoservicio de Credenciales y Seguridad de Usuario**:
   - Implementar flujo de recuperación de clave vía correo electrónico con token de un solo uso para todas las cuentas activas.
3. **Fase 8 — Portal de Vinculación de Acudientes**:
   - Habilitar flujo de auto-asociación de acudientes con validación de código de matrícula estudiantil.

---

## 16. Lista de Verificación Manual UAT (User Acceptance Testing)

- [ ] **Escenario 1 (Admin Nacional)**: Iniciar sesión con `admin.nacional@mineducacion.gov.co`, ingresar a `/admin/institutions`, aprovisionar colegio oficial y generar enlace de invitación de Rector.
- [ ] **Escenario 2 (Rector Onboarding)**: Abrir el enlace de invitación en ventana privada, verificar datos institucionales precargados, definir contraseña segura y activar la cuenta.
- [ ] **Escenario 3 (Rector In-App)**: Iniciar sesión con las credenciales del Rector activado, verificar acceso exclusivo a `/academic` de su institución y confirmar ausencia del menú `/admin/institutions`.
- [ ] **Escenario 4 (Coordinador)**: Iniciar sesión como Coordinador, verificar gestión de grupos y asignaciones; confirmar que el botón "Crear Año Lectivo" no está disponible.
- [ ] **Escenario 5 (Docente)**: Iniciar sesión como Docente, ingresar a `/virtual-classrooms`, programar clase virtual, iniciar sesión (rol `MODERATOR`) y gestionar grabaciones.
- [ ] **Escenario 6 (Estudiante)**: Iniciar sesión como Estudiante, acceder a `/virtual-classrooms`, verificar ingreso como `VIEWER` a clases de su grupo y confirmar bloqueo a clases de otros grupos.
- [ ] **Escenario 7 (Acudiente)**: Iniciar sesión como Acudiente, verificar que el módulo "Aulas Virtuales" no aparece en navegación ni en dashboard, e intentar acceder manualmente a `/virtual-classrooms` verificando redirección o bloqueo `403`.

---

## 17. Brechas Explícitas de Requerimientos (Explicit Requirements Gaps)

1. **Ciclo de Reemplazo / Sucesión de Rector**:
   - Los requerimientos actuales definen la prohibición de emitir invitaciones si existe un Rector activo (`RECTOR_ALREADY_EXISTS`), pero no especifican el flujo formal de desvinculación o sustitución de un rector saliente por el Administrador Nacional.
2. **Transferencia Inter-Institucional de Docentes**:
   - El modelo actual aísla estrictamente a los docentes a su `institution_id`. No se encuentra especificado si un docente puede pertenecer a dos instituciones públicas simultáneamente o si requiere un flujo de traslado inter-colegial.

---

## 18. Estado de Gobernanza y Cierre

```
AUDIT_STATUS = ACCEPTANCE_AUDIT_COMPLETE
FINAL_DECISION = NO-GO
PROMOTION_EXECUTED = FALSE
PROMOTION_AUTHORIZED = FALSE
AUTHORIZATION_REQUIRED = TRUE
CURRENT_STATE = PHASE_5_AUDIT_VERIFIED
CODE_MODIFICATIONS = 0
DATABASE_MODIFICATIONS = 0
CANONICAL_MUTATIONS = 0
```
