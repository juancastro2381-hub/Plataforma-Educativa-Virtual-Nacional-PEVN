# INFORME DE RESULTADOS — FASE 13E.1
## TEACHER ACADEMIC SCOPE ENFORCEMENT (ANTI-IDOR / LEAST PRIVILEGE)

**Fecha de Ejecución:** 31 de Agosto de 2026  
**Sistema:** Plataforma Educativa Virtual Nacional (PEVN)  
**Módulo:** Ámbito Académico Docente & Control de Acceso Basado en Carga Académica  
**Estado:** ✅ **COMPLETADO CON ÉXITO (337/337 TESTS PASSED — 100% SUCCESS)**

---

## 1. Resumen Ejecutivo

En la **Fase 13E.1**, se implementó el aislamiento estricto del ámbito académico docente (*Teacher Academic Scope Enforcement*) en la capa backend de la plataforma PEVN, eliminando cualquier vector de IDOR (*Insecure Direct Object Reference*) o sobre-exposición de datos entre docentes de una misma institución educativa o entre diferentes instituciones.

### Principio de Mínimo Privilegio (*Least Privilege*)
- Un docente autenticado **únicamente** tiene visibilidad sobre:
  1. Los grupos donde tenga una asignación académica activa (`AcademicAssignment.is_active = True`).
  2. Los grupos donde haya sido designado Director de Grupo (`Group.group_director_teacher_id = Teacher.id`).
  3. Los estudiantes matriculados activamente (`Enrollment.status = ACTIVE`) en dichos grupos autorizados.
  4. Las matrículas correspondientes a dichos grupos autorizados.
- Un docente nuevo sin asignación académica o sin dirección de grupo **recibe exactamente 0 grupos y 0 estudiantes** (lista vacía `[]`), impidiendo que reciba el censo institucional completo.
- Un docente no puede consultar datos individuales de estudiantes o grupos ajenos mediante llamadas directas a `/api/v1/students/{student_id}`, `/api/v1/groups/{group_id}` o `/api/v1/enrollments/{enrollment_id}` (retorna `404 Not Found` en lugar de `403 Forbidden` para evitar la enumeración y fuga de existencia de recursos ajenos).
- **Preservación Total de Roles Directivos:** El Rector, Administradores Institucionales, Coordinadores, Coordinadores Académicos y Administradores Nacionales conservan su visibilidad institucional completa e irrestricta.
- **Cero migraciones de base de datos:** El modelo canónico existente (`AcademicAssignment`, `Group`, `Enrollment`, `Student`, `Teacher`) se mantuvo intacto como fuente canónica de la verdad.

---

## 2. Arquitectura de Scoping Canónico

### 2.1 Cadena de Visibilidad Canónica
$$\text{Teacher} \xrightarrow{\text{user\_id}} \text{Teacher Profile} \xrightarrow{\text{is\_active}=\text{True}} \text{AcademicAssignment} \cup \text{Group.director} \xrightarrow{} \text{Group IDs} \xrightarrow{\text{status}=\text{ACTIVE}} \text{Enrollment} \xrightarrow{} \text{Student}$$

### 2.2 Separación entre Actores Directivos y Actores Educativos Acotados

```mermaid
flowchart TD
    Req[Solicitud HTTP entrante a /students, /groups, /enrollments] --> Auth[Autenticación JWT & Contexto de Autorización]
    Auth --> CheckDir{¿Actor Directivo?<br/>Rector / Admin / Coordinador / Superadmin}
    CheckDir -- Sí --> InstScope[Visibilidad Institucional Completa<br/>WHERE institution_id == target_institution_id]
    CheckDir -- No --> CheckTeach{¿Rol Docente?}
    CheckTeach -- Sí --> DerivScope[Derivar Grupos Autorizados:<br/>1. AcademicAssignment is_active=True<br/>2. Group.group_director_teacher_id]
    DerivScope --> HasGroups{¿Tiene grupos autorizados?}
    HasGroups -- No --> EmptyRes[Retornar lista vacía []<br/>o 404 en consulta por ID]
    HasGroups -- Sí --> FilterQuery[JOIN Enrollment WHERE group_id IN authorized_group_ids<br/>AND Enrollment.status == ACTIVE]
    FilterQuery --> Out[Retornar Recursos Autorizados]
```

---

## 3. Matriz de Pruebas de Autorización (Fase 13E.1)

Se diseñó e implementó la suite completa de pruebas en `backend/tests/test_teacher_academic_scope.py`:

| ID Prueba | Caso de Prueba | Escenario Validado | Resultado |
| :--- | :--- | :--- | :---: |
| **TEST-SCOPE-01** | `test_scope_01_teacher_a_assigned_to_grade_3a_sees_only_grade_3a_students` | Docente A asignado a Grado 3-A solo ve estudiantes de 3-A (2 estudiantes) y no ve los de 5-B ni 4-A. | **PASSED** |
| **TEST-SCOPE-02** | `test_scope_02_teacher_b_assigned_to_grade_5b_sees_only_grade_5b_students` | Docente B asignado a Grado 5-B solo ve estudiantes de 5-B (1 estudiante) y no ve los de 3-A ni 4-A. | **PASSED** |
| **TEST-SCOPE-03** | `test_scope_03_new_teacher_with_no_assignments_sees_zero_students_and_groups` | Docente C recién creado sin asignaciones académicas recibe lista vacía `[]` en `/students`, `/groups` y `/enrollments`. | **PASSED** |
| **TEST-SCOPE-04** | `test_scope_04_teacher_a_attempts_get_student_for_teacher_b_student_is_denied` | Docente A intenta acceder directamente a `/api/v1/students/{student_b_id}` por ID y el endpoint deniega con `404 Not Found`. | **PASSED** |
| **TEST-SCOPE-05** | `test_scope_05_rector_retains_full_institutional_visibility` | Rector de la institución conserva visibilidad completa sobre todos los estudiantes (3-A, 4-A, 5-B) y todos los grupos. | **PASSED** |
| **TEST-SCOPE-06** | `test_scope_06_group_director_requests_students_of_their_group` | Docente E como Director de Grupo de 4-A (sin asignación de materia específica) accede legítimamente a los estudiantes de 4-A. | **PASSED** |
| **TEST-SCOPE-07** | `test_scope_07_teacher_assigned_to_multiple_groups_returns_union` | Docente F asignado a 3-A y 5-B recibe la unión exacta de los estudiantes de ambos grupos (3 estudiantes). | **PASSED** |
| **TEST-SCOPE-08** | `test_scope_08_cross_tenant_access_is_denied` | Docente A intenta acceder a estudiante de otra institución (`inst2`) y es estrictamente denegado con `404 Not Found`. | **PASSED** |
| **TEST-SCOPE-09** | `test_scope_09_two_teachers_in_same_group_both_see_group_students` | Docente A y Docente D asignados a distintas materias en el mismo grupo 3-A ven ambos los estudiantes de 3-A de forma compartida y legítima. | **PASSED** |
| **TEST-SCOPE-10** | `test_scope_10_teacher_cannot_access_unauthorized_groups_or_enrollments` | Docente A intenta consultar `/api/v1/groups/{group_5b_id}` y `/api/v1/enrollments/{enrollment_5b_id}` y es denegado con `404 Not Found`. | **PASSED** |

---

## 4. Resultados Globales de la Suite de Pruebas

Se ejecutó la suite completa de pruebas automatizadas del backend de PEVN:

```
================= 337 passed, 8 warnings in 384.96s (0:06:24) =================
```

### Detalle por Módulos Clave:
1. `tests/test_teacher_academic_scope.py`: **10/10 PASSED** (100%)
2. `tests/test_teacher_portal_api.py`: **9/9 PASSED** (100%)
3. `tests/test_teacher_account_provisioning.py`: **9/9 PASSED** (100%)
4. `tests/test_academic_api.py`: **11/11 PASSED** (100%)
5. `tests/test_domain_services.py`: **5/5 PASSED** (100%)
6. `tests/test_enrollments_and_assignments.py`: **5/5 PASSED** (100%)
7. `tests/test_rbac_governance_and_rector_invitation.py`: **18/18 PASSED** (100%)
8. `tests/test_virtual_classroom_api.py` & `services`: **15/15 PASSED** (100%)
9. `tests/test_national_catalog_*.py`: **118/118 PASSED** (100%)

---

## 5. Archivos Modificados y Creados

1. [`backend/app/services/academic_scope_helper.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/academic_scope_helper.py)
   - Módulo desacoplado para determinar roles directivos y calcular dinámicamente los grupos autorizados para un docente a partir de `AcademicAssignment(is_active=True)` y `Group(group_director_teacher_id)`.
2. [`backend/app/services/student_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/student_service.py)
   - Filtrado estricto por matrícula activa en grupos autorizados en `list_students`, `get_student_by_id`, `get_student_by_simat` y `get_student_guardians`.
3. [`backend/app/api/v1/endpoints/students.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/students.py)
   - Delegación de endpoints a `StudentService` pasando el usuario y contexto de autorización.
4. [`backend/app/services/group_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/group_service.py)
   - Filtrado de grupos por `Group.id.in_(authorized_group_ids)` en `list_groups` y validación de membresía en `get_group_by_id`.
5. [`backend/app/api/v1/endpoints/groups.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/groups.py)
   - Delegación de endpoints `/groups` y `/groups/{id}` a `GroupService`.
6. [`backend/app/services/enrollment_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/enrollment_service.py)
   - Filtrado de matrículas por `Enrollment.group_id.in_(authorized_group_ids)` en `list_enrollments` y validación en `get_enrollment_by_id`.
7. [`backend/app/api/v1/endpoints/enrollments.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/enrollments.py)
   - Delegación de endpoints `/enrollments` y `/enrollments/{id}` a `EnrollmentService`.
8. [`backend/tests/test_teacher_academic_scope.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_teacher_academic_scope.py)
   - Suite de 10 pruebas de integración anti-IDOR para la Fase 13E.1.
