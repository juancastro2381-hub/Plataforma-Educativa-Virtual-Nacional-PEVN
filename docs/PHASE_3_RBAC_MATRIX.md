# MATRIZ DE AUTORIZACIÓN Y ROLES ACADÉMICOS (RBAC) — FASE 3A
# Plataforma Educativa Virtual Nacional (PEVN)

> **ESTADO:** DISEÑO ARQUITECTÓNICO — ESPECIFICACIÓN DE CONTROL DE ACCESO  
> **LÍNEA BASE DE SEGURIDAD:** REUTILIZA EL MOTOR CENTRALIZADO `CentralizedAuthorizationService` DE FASE 2.

---

## 1. Jerarquía de Roles y Niveles de Seguridad (Level Hierarchy)

Para prevenir la escalación de privilegios horizontal y vertical, cada rol posee un **Nivel Numérico Inmutable** y un **Alcance Territorial Máximo**:

```
+---------------------+-------+------------------------+------------------------------------+
| ROL DE SISTEMA      | NIVEL | ALCANCE TERRITORIAL    | PROPÓSITO Y RESPONSABILIDAD        |
+---------------------+-------+------------------------+------------------------------------+
| superadmin          |  100  | Nacional (Bypass)      | Operador técnico del Estado / Root |
| national_admin      |   90  | Nacional               | Ministerio de Educación Nacional   |
| department_admin    |   80  | Departamental (SED)    | Secretaría de Educación Departam.  |
| municipality_admin  |   70  | Municipal (SEM)        | Secretaría de Educación Municipal  |
| rector              |   60  | Institucional (Tenant) | Rector / Director de la I.E.       |
| coordinator         |   50  | Institucional / Sede   | Coordinador Académico o de Sede    |
| teacher             |   30  | Grupo / Asignatura     | Docente de Aula / Titular          |
| student             |   10  | Propio (Ownership)     | Estudiante Matriculado             |
| guardian            |   10  | Hijos / Tutorados      | Padre / Madre / Acudiente Legal    |
+---------------------+-------+------------------------+------------------------------------+
```

---

## 2. Catálogo de Permisos Granulares de la Fase 3 (`recurso:accion`)

```
Recurso: academic_years
  - academic_years:read
  - academic_years:create
  - academic_years:update
  - academic_years:close
  - academic_years:delete

Recurso: academic_periods
  - academic_periods:read
  - academic_periods:create
  - academic_periods:update
  - academic_periods:close

Recurso: grades
  - grades:read
  - grades:manage (solo nacional)

Recurso: subjects
  - subjects:read
  - subjects:create
  - subjects:update
  - subjects:delete

Recurso: groups
  - groups:read
  - groups:create
  - groups:update
  - groups:delete
  - groups:assign_director

Recurso: teachers
  - teachers:read
  - teachers:create
  - teachers:update
  - teachers:delete

Recurso: students
  - students:read
  - students:create
  - students:update
  - students:delete

Recurso: guardians
  - guardians:read
  - guardians:create
  - guardians:update
  - guardians:link_student

Recurso: enrollments
  - enrollments:read
  - enrollments:create
  - enrollments:transfer
  - enrollments:withdraw
  - enrollments:delete

Recurso: academic_assignments
  - academic_assignments:read
  - academic_assignments:create
  - academic_assignments:update
  - academic_assignments:delete
```

---

## 3. Matriz Completa de Roles y Permisos (CRUD & Operaciones)

*Convenciones:*  
- **GLOBAL:** Permitido en todo el país.  
- **SCOPE:** Permitido estrictamente dentro de la jurisdicción DANE (`scope_contains`).  
- **OWN:** Permitido exclusivamente sobre sus propios registros o tutorados directos.  
- **DENY:** Bloqueado por defecto (`403 Forbidden`).

| Recurso / Operación | SuperAdmin | National Admin | Dept/Mun Admin | Rector | Coordinador | Docente | Estudiante | Acudiente |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Años Lectivos (Lectura)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | SCOPE | SCOPE | SCOPE |
| **Años Lectivos (Crear/Modificar)** | GLOBAL | GLOBAL | DENY | SCOPE | DENY | DENY | DENY | DENY |
| **Años Lectivos (Cierre Anual)** | GLOBAL | GLOBAL | DENY | SCOPE | DENY | DENY | DENY | DENY |
| **Períodos (Gestión/Cierre)** | GLOBAL | GLOBAL | DENY | SCOPE | SCOPE | DENY | DENY | DENY |
| **Grados Curriculares (Lectura)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | SCOPE | SCOPE | SCOPE |
| **Asignaturas (Crear/Modificar)** | GLOBAL | GLOBAL | DENY | SCOPE | SCOPE | DENY | DENY | DENY |
| **Grupos (Crear/Editar/Asignar Director)** | GLOBAL | GLOBAL | DENY | SCOPE | SCOPE | DENY | DENY | DENY |
| **Docentes (Crear/Vincular)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | DENY | DENY | DENY |
| **Docentes (Lectura Perfil)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | SCOPE | OWN | OWN |
| **Estudiantes (Crear/Editar Datos)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | DENY | DENY | DENY |
| **Estudiantes (Lectura)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | SCOPE (Cursos) | OWN | OWN |
| **Matrículas (Crear/Asignar Salón)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | DENY | DENY | DENY |
| **Matrículas (Traslado/Retiro)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | DENY | DENY | DENY |
| **Asignación Carga Docente** | GLOBAL | GLOBAL | DENY | SCOPE | SCOPE | DENY | DENY | DENY |
| **Acudientes (Vincular Estudiante)** | GLOBAL | GLOBAL | SCOPE | SCOPE | SCOPE | DENY | DENY | OWN |

---

## 4. Reglas de Validación en Tres Capas

Toda petición académica pasa secuencialmente por tres barreras de seguridad:

1. **Barrera 1 — Verificación RBAC:**  
   ¿Posee el rol del usuario el permiso `recurso:accion` requerido?  
   *Si no:* `403 Forbidden (PERMISSION_DENIED)`.
2. **Barrera 2 — Aislamiento de Tenancy (`scope_contains`):**  
   ¿Está el recurso solicitado (`institution_id` / `campus_id`) dentro del alcance territorial del actor?  
   *Si no:* `403 Forbidden (SCOPE_MISMATCH)`.
3. **Barrera 3 — Restricción de Dominio / Ownership:**  
   Si es estudiante o acudiente, ¿es este registro su propio perfil o el de su hijo matriculado?  
   *Si no:* `403 Forbidden (OWNERSHIP_REQUIRED)`.
