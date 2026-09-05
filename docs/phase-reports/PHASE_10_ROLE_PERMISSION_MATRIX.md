# MATRIZ FORMAL DE ROLES, PERMISOS, NAVEGACIÓN Y ALCANCE — FASE 10
# PEvN — PLATAFORMA EDUCATIVA VIRTUAL NACIONAL

**Versión:** 1.0 (Auditada en Producción)  
**Fecha:** 2026-08-29  
**Roles Canónicos:** 11  
**Permisos Canónicos:** 59  
**Mappings RBAC DB:** 303  

---

## 1. MATRIZ CANÓNICA DE LOS 11 ROLES

| # | Rol Canónico | Nivel | Ámbito (Scope) | Destino Inicial (Landing) | Rutas UI Autorizadas | Operaciones API Principales | Acciones Prohibidas (403) | Aislamiento Multitenant |
|---|:---|:---:|:---|:---|:---|:---|:---|:---|
| 1 | **`superadmin`** | 100 | Nacional / Global | `/dashboard` | `/*` (Todas) | Catálogos, instituciones, usuarios, RBAC, auditoría | Ninguna (Comodín `*:*`) | Global / Bypass seguro |
| 2 | **`national_admin`** | 90 | Nacional (MEN) | `/dashboard` | `/admin/institutions`, `/analytics/territorial`, `/dashboard` | Provisión colegios, DANE, invitaciones a Rector | Crear docentes/estudiantes de sede directa | Filtrado nacional por parámetros |
| 3 | **`department_admin`** | 80 | Departamental (SED) | `/dashboard` | `/analytics/territorial`, `/dashboard` | Lectura institucional y analítica territorial | Modificación institucional, creación de docentes | Estricto a su Departamento |
| 4 | **`municipality_admin`** | 70 | Municipal (SEM) | `/dashboard` | `/analytics/territorial`, `/dashboard` | Lectura institucional y analítica territorial | Modificación departamental/nacional | Estricto a su Municipio |
| 5 | **`rector`** | 60 | Institución (Sede Principal) | `/dashboard` | `/academic`, `/virtual-classrooms`, `/dashboard` | Años lectivos, salones, docentes, matrículas, clases | Provisión de otros colegios / Operaciones MEN | Estricto a su `institution_id` |
| 6 | **`institution_admin`** | 60 | Institución (Tenant) | `/dashboard` | `/academic`, `/virtual-classrooms`, `/dashboard` | Salones, docentes, matrículas, clases | Aprovisionamiento territorial | Estricto a su `institution_id` |
| 7 | **`coordinator`** | 50 | Sede / Institucional | `/dashboard` | `/academic`, `/virtual-classrooms`, `/dashboard` | Cupos, estudiantes, docentes, traslados | Cierre oficial de año lectivo, invitar rector | Estricto a su `institution_id` |
| 8 | **`academic_coordinator`**| 50 | Sede / Institucional | `/dashboard` | `/academic`, `/virtual-classrooms`, `/dashboard` | Carga horaria, asignaturas, docentes, salones | Cierre oficial de año lectivo, invitar rector | Estricto a su `institution_id` |
| 9 | **`teacher`** | 30 | Asignación / Salón | `/dashboard` | `/virtual-classrooms`, `/academic?tab=students`, `/dashboard` | Dictar clases, consultar estudiantes asignados | Crear docentes, modificar calendarios | Estricto a Carga y Sede |
| 10| **`student`** | 10 | Personal / Matrícula | `/dashboard` | `/virtual-classrooms`, `/dashboard` | Unirse a clases virtuales, consultar calificaciones | Gestión académica, crear docentes | Estricto a su Matrícula |
| 11| **`guardian`** | 10 | Personal / Tutorados | `/dashboard` | `/dashboard` | Monitoreo familiar de tutorados | Modificación escolar, crear salones/años | Estricto a sus Tutorados |

---

## 2. MATRIZ DE RUTAS FRONTEND Y CONTROL DE ACCESO

| Ruta Frontend | Componente | Tipo de Acceso | Roles Permitidos | Permisos Requeridos | Comportamiento si no Autorizado |
|:---|:---|:---:|:---|:---|:---|
| `/` | `ComingSoon` | Público | Todos | Ninguno | N/A |
| `/login` | `Login` | Público | No autenticados | Ninguno | Redirige a `/dashboard` si ya autenticado |
| `/auth/forgot-password` | `ForgotPassword` | Público | No autenticados | Ninguno | N/A |
| `/auth/reset-password` | `ResetPassword` | Público | Token válido | Ninguno | N/A |
| `/auth/accept-invitation` | `AcceptInvitation` | Público | Token invitación | Ninguno | N/A |
| `/dashboard` | `Dashboard` | Privado | Todos autenticados | Sesión activa | Redirige a `/login` |
| `/admin/institutions` | `InstitutionsView` | Privado | `superadmin`, `national_admin` | `institutions:create` | Redirige a `/dashboard` |
| `/analytics/territorial`| `TerritorialAnalyticsView` | Privado | Autorizados | `institutions:read` | Redirige a `/dashboard` |
| `/academic` | `AcademicHub` | Privado | Autorizados | Cualquier `*:read` académico | Muestra primer tab permitido o cero-state |
| `/virtual-classrooms` | `VirtualClassroomsView` | Privado | Autorizados | `virtual_classrooms:read` | Redirige a `/dashboard` |
| `/*` | `NotFound` | Público | Todos | Ninguno | Renderiza vista 404 |

---

## 3. MATRIZ DE PESTAÑAS ACADÉMICAS (`/academic`)

| Pestaña (Tab) | Vista Renderizada | Permiso Requerido | Roles con Acceso Típico | Comportamiento sin Permiso |
|:---|:---|:---|:---|:---|
| `years` | `AcademicYearsView` | `academic_years:read` | `superadmin`, `national_admin`, `rector`, `institution_admin` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `groups` | `GroupsView` | `groups:read` | `rector`, `institution_admin`, `coordinator`, `academic_coordinator` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `students` | `StudentsView` | `students:read` | `rector`, `coordinator`, `academic_coordinator`, `teacher` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `teachers` | `TeachersView` | `teachers:read` | `rector`, `institution_admin`, `coordinator`, `academic_coordinator` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `guardians` | `GuardiansView` | `guardians:read` | `rector`, `coordinator`, `teacher` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `enrollments` | `EnrollmentsView` | `enrollments:read` | `rector`, `coordinator` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `transfers` | `TransfersView` | `enrollments:read` | `rector`, `coordinator` | Tab oculto; si se entra por URL, alerta informativa y fallback |
| `assignments` | `AcademicAssignmentsView` | `academic_assignments:read` | `rector`, `academic_coordinator`, `coordinator` | Tab oculto; si se entra por URL, alerta informativa y fallback |

---

## 4. MATRIZ DE LOS 59 PERMISOS CANÓNICOS

```text
1. Wildcard:
   - *:* (superadmin)
2. Institutions:
   - institutions:read, institutions:create, institutions:update, institutions:delete
3. Users:
   - users:read, users:create, users:create_rector, users:update, users:delete
4. Academic Years & Periods:
   - academic_years:read, academic_years:create, academic_years:update, academic_years:close, academic_years:delete
   - academic_periods:read, academic_periods:create, academic_periods:update, academic_periods:close
5. Grades & Subjects:
   - grades:read, grades:write, grades:manage
   - subjects:read, subjects:create, subjects:update, subjects:delete
6. Groups:
   - groups:read, groups:create, groups:update, groups:delete, groups:assign_director
7. Teachers:
   - teachers:read, teachers:create, teachers:update, teachers:delete
8. Students & Enrollments:
   - students:read, students:create, students:update, students:delete
   - enrollments:read, enrollments:create, enrollments:transfer, enrollments:withdraw, enrollments:delete
9. Guardians:
   - guardians:read, guardians:create, guardians:update, guardians:link_student
10. Academic Assignments:
    - academic_assignments:read, academic_assignments:create, academic_assignments:update, academic_assignments:delete
11. Virtual Classrooms & Recordings:
    - virtual_classrooms:read, virtual_classrooms:create, virtual_classrooms:join, virtual_classrooms:manage
    - recordings:read, recordings:manage, recordings:delete
```
