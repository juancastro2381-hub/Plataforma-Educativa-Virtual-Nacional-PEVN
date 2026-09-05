# PEVN — Fase 13D.4: Informe Final de Cierre y Certificación Técnica
## Diagnóstico Forense y Remediación de Asignación de Carga Académica Docente (HTTP 422 / VALIDATION_ERROR)

---

### 1. Resumen Ejecutivo (Executive Summary)

Durante las pruebas funcionales de integración del módulo de **Gestión Académica** (posterior a la finalización exitosa de las Fases 13D.2 de Provisión Unificada de Estudiantes y 13D.3 de Formalización de Matrículas), se detectó un fallo sistemático al intentar asignar la carga académica de un docente:

- **Ruta fallida:** `POST http://localhost:3000/api/v1/academic-assignments`
- **Código HTTP:** `422 Unprocessable Content`
- **Mensaje Frontend:** `Error: VALIDATION_ERROR — Request validation failed. Check the request and try again.`
- **Valores en el formulario:**
  - Docente: `Juan Carlos Castro`
  - ID Asignatura: `3000022`
  - ID Grupo / Salón: `003332`
  - Año Lectivo: `2026`
  - Horas / Sem: `5`

El diagnóstico forense demostró que la interfaz de usuario en `AcademicAssignmentsView.tsx` disponía de campos de entrada de texto libre (`<input type="text">`) para la asignatura, el grupo y el año escolar, lo que ocasionaba que el operador ingresara códigos o textos descriptivos en lugar de identificadores canónicos `UUIDv4`. Al enviarse al backend, la capa de validación de Pydantic (`AcademicAssignmentCreateRequest`) rechazó los valores no conformes a UUID con `HTTP 422`. Adicionalmente, el backend carecía de un endpoint REST formal para listar y autoinicializar el catálogo curricular de asignaturas (`GET /api/v1/subjects`).

Se implementó la remediación arquitectónica canónica en dos capas:
1. **Backend:** Se creó el controlador `backend/app/api/v1/endpoints/subjects.py` (`GET /api/v1/subjects` y `POST /api/v1/subjects`) con soporte para autoinicialización del currículo nacional obligatorio (Ley 115 de 1994) para los 12 grados curriculares bajo aislamiento multi-tenant y permisos RBAC `subjects:read` / `subjects:create`.
2. **Frontend:** Se reemplazaron todos los campos de texto libre de `AcademicAssignmentsView.tsx` por selectores desplegables dinámicos contextuales vinculados a los UUIDs canónicos de Docentes, Años Lectivos, Grupos y Asignaturas, incorporando resolución de nombres legibles en la tabla de asignaciones.

La verificación estática y dinámica certificó el 100% de éxito: **309 pruebas de backend superadas**, **47 pruebas de vitest de frontend superadas** y **0 errores de TypeScript**.

---

### 2. Objetivo de la Fase (Phase Objective)

- Realizar el diagnóstico forense completo de la falla de validación `HTTP 422 Unprocessable Content` en el flujo de asignación de carga académica docente (`POST /api/v1/academic-assignments`).
- Diseñar e implementar la resolución de referencias canónicas en el frontend sin vulnerar el tipado estricto de Pydantic ni debilitar las reglas de integridad de claves foráneas de PostgreSQL.
- Proporcionar la infraestructura de lectura/creación del catálogo de asignaturas requerida por la interfaz.
- Garantizar la preservación de todos los invariantes académicos: docente titular único por materia/grupo/año (`uq_academic_assignments_single_active`), aislamiento multi-tenant estricto y auditoría atómica.

---

### 3. Contexto y Problema Inicial (Initial Problem / Context)

Al formalizar una asignación académica para el docente "Juan Carlos Castro" en el año 2026 con intensidad horaria de 5 horas semanales, el operador ingresaba los identificadores de negocio visibles ("3000022" para la asignatura, "003332" para el grupo y "2026" para el año lectivo).

El formulario ejecutaba una petición directa con el payload:
```json
{
  "teacher_id": "3044caf0-260d-4909-ac4c-02e6d8eb4e65",
  "subject_id": "3000022",
  "group_id": "003332",
  "academic_year_id": "2026",
  "weekly_hours": 5,
  "is_active": true
}
```

El servidor FastAPI respondía con `HTTP 422 Unprocessable Content` debido a que Pydantic exige que `subject_id`, `group_id` y `academic_year_id` sean instancias válidas de `uuid.UUID`.

---

### 4. Análisis de Causa Raíz (Root Cause Analysis)

1. **Falta de selectores contextuales en el modal de creación:**
   En `frontend/src/pages/academic/AcademicAssignmentsView.tsx`, mientras que el campo `teacher_id` contaba con un `<select>` condicional básico, los campos `subject_id`, `group_id` y `academic_year_id` eran cajas de texto libre `<input type="text">` que incitaban al operador a ingresar nombres o códigos numéricos arbitrarios.
2. **Carencia de endpoint para Asignaturas (`/api/v1/subjects`):**
   A diferencia de los catálogos de sedes, años, grupos y grados (implementados en Fases 13B y 13D), no existía una ruta `GET /api/v1/subjects` para consultar el plan de estudios institucional filtrado por grado y área de conocimiento.
3. **Ausencia de inicialización automática del plan de estudios institucional:**
   Las instituciones recién creadas o auditadas en la base de datos no contaban con registros de asignaturas en la tabla `subjects`, requiriendo un mecanismo transparente que garantice la existencia de las asignaturas obligatorias y fundamentales de la educación formal colombiana.

---

### 5. Archivos Modificados (Exact Files Modified)

| Capa | Archivo | Acción | Propósito |
| :--- | :--- | :--- | :--- |
| **Backend** | `backend/app/schemas/academic.py` | Modificado | Agregadas definiciones de `SubjectResponse`, `SubjectListResponse` y `SubjectCreateRequest`. |
| **Backend** | `backend/app/schemas/__init__.py` | Modificado | Exportados esquemas de Asignaturas y Grados en el paquete raíz de esquemas. |
| **Backend** | `backend/app/api/v1/endpoints/subjects.py` | Creado | Endpoints `GET /api/v1/subjects` y `POST /api/v1/subjects` con auto-seeding estatutario y validación tenant. |
| **Backend** | `backend/app/api/v1/router.py` | Modificado | Registro del router `subjects.router` en la API v1. |
| **Backend** | `backend/tests/test_academic_api.py` | Modificado | Agregadas pruebas de API para `GET /subjects`, `POST /subjects` y asignación académica con rechazo de duplicados e invalid UUIDs. |
| **Frontend** | `frontend/src/types/academic.ts` | Modificado | Agregadas interfaces TypeScript `SubjectResponse`, `SubjectListResponse` y `SubjectCreateRequest`. |
| **Frontend** | `frontend/src/services/academic.ts` | Modificado | Agregados métodos `listSubjects()` y `createSubject()` en `academicApi`. |
| **Frontend** | `frontend/src/pages/academic/AcademicAssignmentsView.tsx` | Modificado | Reemplazados inputs de texto libre por selectores dinámicos para Docente, Año Lectivo, Grupo y Asignatura; mapas de renderizado en tabla. |
| **Frontend** | `frontend/src/test/Academic.test.tsx` | Modificado | Agregados mocks y pruebas unitarias de renderizado de selectores de asignación académica. |

---

### 6. Cambios Detallados de Implementación (Detailed Implementation Changes)

#### A. Backend (`app/api/v1/endpoints/subjects.py`)
- Se implementó `GET /api/v1/subjects`:
  - Aislamiento multi-tenant validando `current_user.institution_id` con soporte de override para administradores nacionales.
  - Filtros opcionales `grade_id` y `knowledge_area_id`.
  - Mecanismo de autoinicialización `_seed_statutory_subjects_if_needed`: Si la institución no posee asignaturas en base de datos, inicializa automáticamente las asignaturas canónicas obligatorias para todos los niveles (Preescolar, Primaria, Secundaria y Media Técnica/Académica) mapeadas a las 9 áreas fundamentales del conocimiento.
  - Permiso RBAC: `subjects:read`.
- Se implementó `POST /api/v1/subjects`:
  - Permite a coordinadores y rectores registrar asignaturas adicionales o complementarias.
  - Permiso RBAC: `subjects:create`.

#### B. Frontend (`AcademicAssignmentsView.tsx`)
- Se incluyeron hooks de carga paralela (`loadCatalogs`) para `teachers`, `subjects`, `groups` y `academicYears`.
- Se añadieron filtros reactivos:
  - Los grupos mostrados en el selector se restringen al año lectivo seleccionado (`academicYearId`).
  - Las asignaturas mostradas en el selector se priorizan de acuerdo con el grado escolar del grupo seleccionado (`groupId`).
  - Al seleccionar una asignatura, el campo de horas semanales se precompleta automáticamente con el valor predeterminado de intensidad horaria de dicha materia.
- En la tabla de asignaciones académicas, se añadieron diccionarios `teacherMap`, `subjectMap`, `groupMap` y `yearMap` para presentar nombres amigables en lugar de UUIDs truncados.

---

### 7. Cambios de Base de Datos y Migraciones (Database / Migration Changes)

- **No se requirieron nuevas migraciones DDL.** Las tablas `subjects`, `knowledge_areas`, `academic_assignments` y los índices parciales de exclusión `uq_academic_assignments_single_active` creados en las migraciones de la Fase 3B fueron reutilizados íntegramente.

---

### 8. Reglas de Negocio Afectadas y Preservadas (Business Rules)

1. **Titularidad Única Activa (Single-Active Teacher Invariant):** Preservada al 100%. Solo puede existir un docente titular activo por asignatura, grupo y año escolar. Intentar crear una asignación duplicada activa retorna `HTTP 409 Conflict` (`ACADEMIC_ASSIGNMENT_DUPLICATE_ACTIVE`).
2. **Sustitución Atómica de Docentes:** Preservada. La acción de sustitución desactiva la asignación vigente y crea la nueva asignación en una única transacción de base de datos.
3. **Validación Estricta de Horas Semanales:** La intensidad horaria semanal debe ser un entero positivo entre 1 y 40 (`Field(..., ge=1, le=40)`).
4. **Validación de Identidad y Tipado UUID:** El backend mantiene la validación estricta `uuid.UUID` en todos los esquemas Pydantic.

---

### 9. Pruebas Ejecutadas y Resultados (Tests Executed & Test Results)

#### A. Suite Backend (Pytest)
- **Comando:** `pytest tests/ -q`
- **Resultado:** **309 PASSED, 0 FAILED** (100% de la suite completa superada).
- **Pruebas específicas de API y Asignaciones Académicas:**
  - `test_academic_endpoints_require_authentication`: PASSED
  - `test_academic_year_crud_and_lifecycle_api`: PASSED
  - `test_teachers_and_groups_api`: PASSED
  - `test_students_and_guardians_api`: PASSED
  - `test_enrollments_transfers_and_assignments_api`: PASSED
  - `test_cross_tenant_isolation_barrier`: PASSED
  - `test_list_grades_api`: PASSED
  - `test_unified_student_provisioning_api`: PASSED
  - `test_subjects_api_and_academic_assignments`: PASSED

#### B. Suite Frontend (Vitest & TypeScript)
- **Comando de Verificación de Tipos:** `npm run typecheck` (`tsc --noEmit`)
  - **Resultado:** **0 errores de compilación TypeScript**.
- **Comando de Pruebas Unitarias:** `npm test` (`vitest run`)
  - **Resultado:** **8 archivos de prueba superados, 47 pruebas superadas, 0 fallos**.

---

### 10. Matriz de Verificación de Criterios de Aceptación

| # | Criterio de Aceptación | Estado | Evidencia |
| :- | :--- | :---: | :--- |
| 1 | Docente existente seleccionable vía dropdown | **CERTIFICADO** | Selector poblado con `academicApi.listTeachers()`. |
| 2 | Asignatura existente seleccionable vía dropdown | **CERTIFICADO** | Selector poblado con `academicApi.listSubjects()`. |
| 3 | Grupo existente seleccionable vía dropdown | **CERTIFICADO** | Selector contextual filtrado por año lectivo. |
| 4 | Año lectivo 2026 seleccionable/resuelto | **CERTIFICADO** | Auto-selección del año lectivo en estado `ACTIVE`. |
| 5 | Horas / Semana = 5 aceptado | **CERTIFICADO** | Validación `weekly_hours` (1-40) conforme a Pydantic y DB check. |
| 6 | Asignación creada exitosamente con UUIDs canónicos | **CERTIFICADO** | `POST /api/v1/academic-assignments` retorna `201 Created`. |
| 7 | Asignación duplicada rechazada con respuesta de negocio | **CERTIFICADO** | Retorna `409 Conflict` (`DuplicateActiveAssignmentError`). |
| 8 | Identificadores inválidos rechazados de forma segura | **CERTIFICADO** | Retorna `422 Unprocessable Content` en Pydantic sin error 500. |
| 9 | Funcionalidad de matrículas previa intacta | **CERTIFICADO** | Suite completa de matrículas pasa al 100%. |
| 10 | Provisión unificada de estudiantes previa intacta | **CERTIFICADO** | Suite completa de estudiantes pasa al 100%. |

---

### 11. Estado Final (Final Status)

**ROOT CAUSE IDENTIFIED — FIX IMPLEMENTED — VERIFIED**
