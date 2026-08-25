# ESPECIFICACIÓN DE CONTRATOS API REST — FASE 3A
# Plataforma Educativa Virtual Nacional (PEVN)

> **ESTADO:** DISEÑO ARQUITECTÓNICO — ESPECIFICACIÓN DE ENDPOINTS  
> **LÍNEA BASE DE SEGURIDAD:** TODOS LOS ENDPOINTS EXIGEN AUTENTICACIÓN JWT EN CABECERA Y EVALUACIÓN DE SCOPE TERRITORIAL.

---

## 1. Estándares Globales de la API

1. **Autenticación:** `Authorization: Bearer <jwt_access_token>`.
2. **Paginación Estandarizada:** `page` (default 1), `page_size` (default 20, max 100). Retorna `total`, `page`, `page_size`, `total_pages`, `items`.
3. **Formato de Respuesta de Error:**
   ```json
   {
     "error": {
       "code": "PERMISSION_DENIED",
       "message": "No tiene permisos para modificar la matrícula en esta institución.",
       "correlation_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
     }
   }
   ```

---

## 2. Endpoints de Años y Períodos Lectivos

### `GET /api/v1/academic-years`
- **Permiso:** `academic_years:read`
- **Filtros:** `institution_id` (opcional si es admin nacional), `status`, `year`.
- **Respuesta:** Lista de años lectivos con conteo de grupos y matrículas.

### `POST /api/v1/academic-years`
- **Permiso:** `academic_years:create`
- **Body:** `{ "institution_id": UUID, "year": 2026, "name": "Año 2026", "calendar_type": "CALENDAR_A", "start_date": "2026-02-01", "end_date": "2026-11-30" }`
- **Validaciones:** `start_date < end_date`, año no duplicado en el tenant.

### `PATCH /api/v1/academic-years/{id}/status`
- **Permiso:** `academic_years:close` o `academic_years:update`
- **Body:** `{ "status": "ACTIVE" | "CLOSED" | "ARCHIVED" }`
- **Auditoría:** Registra evento `academic_year.status_changed`.

---

## 3. Endpoints de Grupos y Cursos

### `GET /api/v1/groups`
- **Permiso:** `groups:read`
- **Filtros:** `campus_id`, `academic_year_id`, `grade_id`, `shift`.
- **Respuesta:** Lista paginada con cupos totales y matriculados actuales.

### `POST /api/v1/groups`
- **Permiso:** `groups:create`
- **Body:** `{ "campus_id": UUID, "academic_year_id": UUID, "grade_id": UUID, "name": "10-01", "shift": "MANANA", "capacity_limit": 40, "group_director_teacher_id": UUID | null }`

---

## 4. Endpoints de Matrícula (Enrollments)

### `GET /api/v1/enrollments`
- **Permiso:** `enrollments:read`
- **Filtros:** `group_id`, `student_id`, `academic_year_id`, `status`.

### `POST /api/v1/enrollments`
- **Permiso:** `enrollments:create`
- **Body:** `{ "student_id": UUID, "group_id": UUID, "academic_year_id": UUID, "enrollment_date": "2026-02-05" }`
- **Validaciones Inviolables:**
  - Verifica que el estudiante no tenga otra matrícula `ACTIVE` en el mismo `academic_year_id`.
  - Verifica que el grupo no supere su `capacity_limit`.
- **Auditoría:** Registra `enrollment.created`.

### `POST /api/v1/enrollments/{id}/transfer`
- **Permiso:** `enrollments:transfer`
- **Body:** `{ "new_group_id": UUID, "reason": "Cambio de jornada solicitado por acudiente" }`
- **Comportamiento:** Actualiza el `group_id`, valida cupo en nuevo grupo y genera entrada en `group_transfer_history`.
- **Auditoría:** Registra `enrollment.transferred`.

---

## 5. Endpoints de Asignación Docente (Carga Académica)

### `POST /api/v1/academic-assignments`
- **Permiso:** `academic_assignments:create`
- **Body:** `{ "teacher_id": UUID, "subject_id": UUID, "group_id": UUID, "academic_year_id": UUID, "weekly_hours": 4 }`
- **Validaciones:**
  - Verifica que el docente pertenezca a la misma institución.
  - Verifica que la asignatura y el grupo correspondan al mismo grado y año escolar.
  - Valida unicidad (evita dos titulares simultáneos en la misma materia/grupo).
- **Auditoría:** Registra `academic_assignment.created`.
