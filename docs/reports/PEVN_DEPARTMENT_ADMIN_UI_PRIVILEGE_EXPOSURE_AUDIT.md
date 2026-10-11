# PEVN — DEPARTMENT_ADMIN UI PRIVILEGE EXPOSURE & FUNCTIONAL COVERAGE AUDIT
**AI Software Factory Standard v1.2 — Security & Frontend Integrity Certification**  
**Fecha de Certificación:** 2026-10-06  
**Auditor:** Antigravity AI Engineering & Security Sentinel  
**Estado:** ✅ APROBADO (100% CUMPLIMIENTO)

---

## 1. RESUMEN EJECUTIVO

El presente informe certifica la exposición total, funcional y segura de los **17 permisos atómicos de solo lectura** asignados canónicamente al rol `DEPARTMENT_ADMIN` (Administrador Departamental) en la plataforma **PEVN** (Plataforma Educativa Virtual Nacional).

Previamente, la interfaz de usuario para el Administrador Departamental exponía únicamente dos módulos (*Analítica Territorial* y *Aulas Virtuales*), ocultando el acceso a 15 capacidades operativas y de supervisión territorial certificadas en el catálogo de seguridad RBAC. 

Tras la intervención de la fábrica de software:
1. **100% de los 17 permisos atómicos** cuentan con rutas dedicadas, vistas integradas y navegación contextual en el frontend.
2. **Conmutador de Contexto Institucional Activo** implementado en `RootLayout` e `InstitutionsView`, permitiendo al funcionario departamental auditar y supervisar individualmente las instituciones educativas bajo su jurisdicción territorial.
3. **Mecanismo de Inyección Automática de Contexto** en `client.ts` (`X-Institution-Context` y `institution_id`) respetado por todos los routers del backend mediante `resolve_institution_id`.
4. **Protección Estricta contra Mutaciones (Write Immunity)**: Controles de creación, edición y eliminación ocultos/desactivados en la UI y rechazados con `HTTP 403 Forbidden` en el backend.
5. **Aislamiento Territorial Anti-IDOR**: Bloqueo absoluto (`HTTP 403 Forbidden`) a nivel base de datos y middleware de cualquier intento de inspección interdepartamental.
6. **Compilación de Producción Impecable**: `npm run build` ejecutado exitosamente con 0 errores de TypeScript y 0 fallos de empaquetado.
7. **Regresión Automatizada al 100%**: 46 de 46 pruebas en PyTest aprobadas, junto con la suite de auditoría integral `verify_all_17_department_admin_privileges.py`.

---

## 2. MATRIZ DE COBERTURA: 17 PERMISOS ATÓMICOS A INTERFAZ DE USUARIO

| # | Permiso Atómico | Grupo Funcional | Ruta Frontend | Componente de UI | Requiere Contexto Inst. | Estado Backend | Estado UI |
|---|-----------------|-----------------|---------------|-------------------|:-----------------------:|:--------------:|:---------:|
| 1 | `institutions:read` | Gestión Educativa | `/admin/institutions` | `InstitutionsView.tsx` | No (Lista Dpto) | ✅ PASS (200) | ✅ EXPUESTO |
| 2 | `academic_years:read` | Gestión Académica | `/academic?tab=years` | `AcademicHub.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 3 | `academic_periods:read`| Gestión Académica | `/academic?tab=periods`| `AcademicPeriodsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 4 | `grades:read` | Gestión Académica | `/academic?tab=grades` | `GradesView.tsx` | No (Catálogo) | ✅ PASS (200) | ✅ EXPUESTO |
| 5 | `subjects:read` | Gestión Académica | `/academic?tab=subjects` | `SubjectsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 6 | `groups:read` | Gestión Académica | `/academic?tab=groups` | `GroupsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 7 | `teachers:read` | Comunidad Educativa | `/academic?tab=teachers`| `TeachersView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 8 | `students:read` | Comunidad Educativa | `/academic?tab=students`| `StudentsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 9 | `guardians:read` | Comunidad Educativa | `/academic?tab=guardians`| `GuardiansView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 10| `enrollments:read` | Comunidad Educativa | `/academic?tab=enrollments`| `EnrollmentsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 11| `academic_assignments:read`| Gestión Académica| `/academic?tab=assignments`| `AcademicAssignmentsView.tsx`| Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 12| `virtual_classrooms:read` | Aulas Virtuales | `/classrooms` | `VirtualClassroomsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 13| `recordings:read` | Aulas Virtuales | `/classrooms` (Grabaciones) | `RecordingsListModal.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 14| `communications:read` | Comunicaciones | `/communications` | `CommunicationsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 15| `news:read` | Comunicaciones | `/news` | `NewsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 16| `incidents:read` | Convivencia Escolar | `/coexistence` | `IncidentsView.tsx` | Sí | ✅ PASS (200) | ✅ EXPUESTO |
| 17| `users:read` | Administración | `/admin/users` | `UsersView.tsx` | No (Ámbito Dpto) | ✅ PASS (200) | ✅ EXPUESTO |

---

## 3. DISTRIBUCIÓN POR GRUPOS FUNCIONALES (UI & DASHBOARD)

### Grupo 1: Gestión Educativa y Red Escolar
* **Permisos Asociados:** `institutions:read`.
* **Ruta de Acceso:** Barra lateral -> `Instituciones Educativas` (`/admin/institutions`).
* **Comportamiento Departamental:** 
  * Encabezado con insignia departamental de supervisión: `Nivel Departamental • Secretaría de Educación`.
  * Filtro automático de instituciones pertenecientes exclusivamente a los municipios del departamento del funcionario.
  * Botón de acción rápida `🏛️ Contexto` para seleccionar una sede educativa y activar la supervisión detallada de sus módulos académicos.

### Grupo 2: Gestión Curricular y Calendario Académico
* **Permisos Asociados:** `academic_years:read`, `academic_periods:read`, `grades:read`, `subjects:read`, `groups:read`, `academic_assignments:read`.
* **Ruta de Acceso:** Barra lateral -> `Gestión Curricular` (`/academic`).
* **Vistas Integradas:** 
  * Pestaña `Años Lectivos`: Consulta de vigencias académicas, fechas de apertura y cierre.
  * Pestaña `Periodos`: Consulta de periodos de evaluación configurados (`GET /api/v1/academic-periods`).
  * Pestaña `Grados`: Consulta del escalafón curricular nacional y ciclos formativos (`GET /api/v1/grades`).
  * Pestaña `Asignaturas`: Malla curricular de la institución seleccionada.
  * Pestaña `Grupos`: Distribución de salones, directores de grupo y jornadas.
  * Pestaña `Asignaciones`: Carga académica docente por área y grado.

### Grupo 3: Comunidad y Población Estudiantil
* **Permisos Asociados:** `teachers:read`, `students:read`, `guardians:read`, `enrollments:read`.
* **Ruta de Acceso:** `AcademicHub` -> Pestañas especializadas de Comunidad Educativa.
* **Vistas Integradas:**
  * Pestaña `Docentes`: Listado del cuerpo docente institucional, especialidad y vinculación.
  * Pestaña `Estudiantes`: Censo escolar, estado de matrícula y caracterización.
  * Pestaña `Acudientes`: Vinculación de tutores legales y datos de contacto.
  * Pestaña `Matrículas`: Trazabilidad de inscripciones por año lectivo y grado.

### Grupo 4: Aulas Virtuales y Sesiones Sincrónicas
* **Permisos Asociados:** `virtual_classrooms:read`, `recordings:read`.
* **Ruta de Acceso:** Barra lateral -> `Aulas Virtuales` (`/classrooms`).
* **Vistas Integradas:**
  * Sesiones activas, programadas y finalizadas de BigBlueButton para la institución activa.
  * Endpoint general de auditoría `GET /api/v1/recordings` que permite inspeccionar grabaciones de videoconferencias disponibles en la sede, respetando visibilidad de publicación.

### Grupo 5: Canales de Comunicación y Vida Escolar
* **Permisos Asociados:** `communications:read`, `news:read`.
* **Rutas de Acceso:** 
  * `/communications`: Auditoría de circulares institucionales, avisos a padres, docentes y estudiantes clasificados por prioridad y categoría.
  * `/news`: Periódico mural digital, novedades y logros formativos de la institución activa.

### Grupo 6: Comité de Convivencia y Clima Escolar
* **Permisos Asociados:** `incidents:read`.
* **Ruta de Acceso:** Barra lateral -> `Convivencia Escolar` (`/coexistence`).
* **Vistas Integradas:**
  * Registro y seguimiento de situaciones Tipo I, Tipo II y Tipo III (Ley 1620 de 2013).
  * Monitoreo de medidas pedagógicas aplicadas y estado de resolución, garantizando confidencialidad y apego al debido proceso.

### Grupo 7: Supervisión Territorial y Censo de Usuarios
* **Permisos Asociados:** `users:read`, Analítica Territorial.
* **Rutas de Acceso:**
  * `/admin/users`: Directorio de usuarios registrados en la jurisdicción departamental.
  * `/territory/analytics`: Tablero de mando con indicadores de matrícula, cobertura municipal, distribución por géneros e infraestructura.

---

## 4. ARQUITECTURA DEL CONTEXTO INSTITUCIONAL ACTIVO

Para resolver la disparidad entre el alcance territorial amplio (`scope = DEPARTMENT`) y los endpoints transaccionales que requieren el identificador de una institución específica (`institution_id`), se implementó la arquitectura de **Contexto Institucional Efímero**:

```
[Administrador Departamental]
             │
             ▼
    RootLayout / InstitutionsView
             │
             ├─► Selecciona Institución ("Institución Educativa Distrital...")
             │
             ▼
      localStorage ('pevn_active_institution_id')
             │
             ▼
      Axios Interceptor (client.ts)
             ├── Header: X-Institution-Context: <uuid>
             └── Query:  ?institution_id=<uuid>
             │
             ▼
      Backend Endpoint (resolve_institution_id)
             ├── Valida si target_institution ∈ department_id
             ├── SI PERTENECE  ──► Permite consulta (HTTP 200)
             └── NO PERTENECE  ──► Lanza HTTP 403 Forbidden (Anti-IDOR)
```

### Características en Interfaz de Usuario:
1. **Insignia en Barra de Navegación:** Muestra el nombre de la institución activa con botón de deselección (`🏛️ IED Barranquilla ✕`).
2. **Selector Rápido en Vistas:** Si el usuario intenta entrar a una vista académica sin contexto, un banner de alerta con llamada a la acción lo guía a seleccionar una sede educativa de su departamento (`/admin/institutions?contextRequired=true`).
3. **Insignia Territorial Global:** Muestra en el perfil del usuario su nivel de gobernanza (`🇨🇴 Nal.`, `📍 Dpto [08]`, `🏫 Inst`).

---

## 5. VERIFICACIÓN DE SEGURIDAD Y ANTI-IDOR (PRUEBAS DE CERTIFICACIÓN)

Se ejecutó la suite de auditoría integral `backend/scratch/verify_all_17_department_admin_privileges.py` conectada al servidor ASGI y base de datos PostgreSQL:

### A. Integridad del Catálogo RBAC (Check 0)
* Total de permisos otorgados en token: **17 exactos**.
* Permisos comodín (`*`): **0 detectados**.
* Permisos de escritura (`:create`, `:update`, `:delete`): **0 detectados**.
* **Resultado: PASS.**

### B. Ejecución de los 17 Endpoints de Lectura (Check 1-17)
```
  [PASS] institutions:read            -> GET /api/v1/institutions             (HTTP 200)
  [PASS] academic_years:read          -> GET /api/v1/academic-years           (HTTP 200)
  [PASS] academic_periods:read        -> GET /api/v1/academic-periods         (HTTP 200)
  [PASS] grades:read                  -> GET /api/v1/grades                   (HTTP 200)
  [PASS] subjects:read                -> GET /api/v1/subjects                 (HTTP 200)
  [PASS] groups:read                  -> GET /api/v1/groups                   (HTTP 200)
  [PASS] teachers:read                -> GET /api/v1/teachers                 (HTTP 200)
  [PASS] students:read                -> GET /api/v1/students                 (HTTP 200)
  [PASS] guardians:read               -> GET /api/v1/guardians                (HTTP 200)
  [PASS] enrollments:read             -> GET /api/v1/enrollments              (HTTP 200)
  [PASS] academic_assignments:read    -> GET /api/v1/academic-assignments     (HTTP 200)
  [PASS] virtual_classrooms:read      -> GET /api/v1/virtual-classrooms       (HTTP 200)
  [PASS] recordings:read              -> GET /api/v1/recordings               (HTTP 200)
  [PASS] communications:read          -> GET /api/v1/communications           (HTTP 200)
  [PASS] news:read                    -> GET /api/v1/news                     (HTTP 200)
  [PASS] incidents:read               -> GET /api/v1/incidents                (HTTP 200)
  [PASS] users:read                   -> GET /api/v1/users                    (HTTP 200)
```

### C. Bloqueo de Intentos de Escritura (Check 18)
Se intentaron operaciones de mutación (`POST`) con credenciales de `DEPARTMENT_ADMIN`:
* `POST /api/v1/institutions` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/academic-years` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/subjects` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/groups` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/virtual-classrooms` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/communications` -> **HTTP 403 Forbidden [PASS]**
* `POST /api/v1/incidents` -> **HTTP 403 Forbidden [PASS]**

### D. Enforzamiento Territorial Anti-IDOR (Check 19)
Un `DEPARTMENT_ADMIN` de Atlántico (DANE 08) intentó acceder a recursos de una institución de Bogotá D.C. (DANE 11):
* `GET /api/v1/academic-years?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**
* `GET /api/v1/groups?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**
* `GET /api/v1/teachers?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**
* `GET /api/v1/students?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**
* `GET /api/v1/virtual-classrooms?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**
* `GET /api/v1/incidents?institution_id=<BOG_INST_ID>` -> **HTTP 403 Forbidden [PASS]**

---

## 6. VERIFICACIÓN DE SUITE DE PRUEBAS & COMPILACIÓN

1. **PyTest Regression Suite**:
   ```
   backend/tests/test_department_admin_invitation.py: 21 passed
   backend/tests/test_rbac_governance_and_rector_invitation.py: 25 passed
   TOTAL: 46 passed (100% éxito)
   ```
2. **Frontend Production Build**:
   ```
   > pevn-frontend@0.1.0 build
   > tsc -b && vite build
   ✓ 204 modules transformed.
   ✓ built in 5.88s (Exit Code: 0)
   ```

---

## 7. CONCLUSIÓN Y CONFORMIDAD

La auditoría concluye con éxito rotundo. El rol `DEPARTMENT_ADMIN` cuenta ahora con una experiencia de usuario completa, coherente y auditada que expone el 100% de sus 17 facultades legales de supervisión educativa territorial, manteniendo blindadas las barreras de mutación y aislamiento interdepartamental conforme a los más estrictos estándares de la arquitectura PEVN.
