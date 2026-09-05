# PEVN — Informe Forense de Regresiones: Fase 13E.5
## Validación de Parentesco de Acudientes y Creación de Asignación Académica

---

### 1. Resumen Ejecutivo y Veredicto Final

| Métrica | Estado |
| :--- | :--- |
| **Fase** | **13E.5 — Academic Module Regression Forensic** |
| **Fecha de Validación** | 2026-09-01 |
| **Veredicto Final** | **FIXED (100% RESUELTO Y VALIDADO)** |
| **Issue #1 (Acudiente "Abuelo/a")** | Resuelto (Alineación exacta del enum frontend $\leftrightarrow$ backend canonical `ABUELO_A`) |
| **Issue #2 (Asignación Académica HTTP 400)** | Resuelto (Compromiso `await db.commit()` de asignaturas curriculares auto-sembradas) |
| **Suite Completa Backend (`pytest`)** | **349 / 349 Tests Pasados (0 Fallos)** |
| **Frontend Build (`tsc -b && vite build`)** | **Exitoso (0 Errores en 3.51s)** |
| **Aislamiento Multi-Tenant (Fase 13E.4)** | **100% Intacto y Preservado** |
| **Alcance Académico Docente (Fase 13E.1)** | **100% Intacto y Preservado** |
| **Impacto en Esquema de BD** | **0 Cambios de Esquema / 0 Migraciones Nuevas** |

---

### 2. Diagnóstico Forense y Solución: Issue #1 (Acudiente "Abuelo/a")

#### A. Comportamiento Observado
Al registrar un acudiente con parentesco "Abuelo/a", la API retornaba `HTTP 422 Unprocessable Content` con código `VALIDATION_ERROR`, mientras que otros parentescos funcionaban correctamente.

#### B. Traza Forense y Causa Raíz
1. **Frontend (`frontend/src/types/academic.ts` y `GuardiansView.tsx`):**
   - El tipo frontend `GuardianRelationshipType` definía variantes no canónicas como `'ABUELO' | 'ABUELA' | 'TIO' | 'TIA'`.
   - El selector del modal enviaba `<option value="ABUELO">Abuelo/a</option>`.
2. **Backend (`backend/app/models/guardian.py` y `schemas/academic.py`):**
   - El modelo de dominio canónico define:
     ```python
     class GuardianRelationshipType(enum.StrEnum):
         PADRE = "PADRE"
         MADRE = "MADRE"
         ABUELO_A = "ABUELO_A"
         TIO_A = "TIO_A"
         TUTOR_LEGAL = "TUTOR_LEGAL"
         OTRO = "OTRO"
     ```
   - El schema Pydantic `GuardianCreateRequest` valida estrictamente contra este enum.
   - Al recibir el valor `"ABUELO"` (en lugar de `"ABUELO_A"`), Pydantic rechazaba la solicitud con HTTP 422.

#### C. Solución Aplicada
- Se corrigió el tipo TypeScript `GuardianRelationshipType` en `frontend/src/types/academic.ts` para usar los identificadores canónicos: `'PADRE' | 'MADRE' | 'ABUELO_A' | 'TIO_A' | 'TUTOR_LEGAL' | 'OTRO'`.
- Se actualizaron los selectores en `GuardiansView.tsx` (modal de registro y modal de vinculación) para enviar `"ABUELO_A"` y `"TIO_A"`, manteniendo las etiquetas visuales para el usuario: "Abuelo/a" y "Tío/a".
- Cero alteraciones en la base de datos o en reglas de negocio del backend.

#### D. Prueba de Regresión
- Se añadió la prueba `test_phase13e5_guardian_abuelo_and_tio_registration` en `backend/tests/test_academic_api.py`, confirmando el registro exitoso (HTTP 201) de acudientes con parentescos `ABUELO_A` y `TIO_A`.

---

### 3. Diagnóstico Forense y Solución: Issue #2 (Asignación Académica HTTP 400)

#### A. Comportamiento Observado
Al intentar registrar una asignación académica en una institución recién creada (e.g. Docente Adriana Agudelo, Año 2026, Grupo 1, Asignatura "Ciencias Naturales y Educación Ambiental", 4 Horas/Sem), el servidor respondía con `HTTP 400 Bad Request`.

#### B. Respuestas a las 13 Preguntas de la Investigación
1. **¿Qué validación generó el HTTP 400?**  
   `AcademicAssignmentService.create_assignment` en la línea 98 al verificar la existencia y pertenencia de la materia:
   ```python
   if not subject:
       raise AcademicDomainError(f"Materia {subject_id} no pertenece a la institución.")
   ```
2. **¿Qué condición exacta falló?**  
   La consulta `select(Subject).where(Subject.id == subject_id, Subject.institution_id == institution_id)` retornó `None`.
3. **¿La falla fue causada por el alcance académico docente (Fase 13E.1)?**  
   No. La Fase 13E.1 aplica restricciones de lectura al portal del docente (`/api/v1/teacher/...`), mientras que la creación de asignaciones es una operación administrativa de Rectoría.
4. **¿La falla fue causada por el aislamiento de acudientes (Fase 13E.4)?**  
   No. La Fase 13E.4 aisló la entidad `Guardian`.
5. **¿El docente seleccionado pertenecía a la institución?**  
   Sí. Docente Adriana Agudelo pertenecía a la institución con su registro en `teachers`.
6. **¿El grupo seleccionado pertenecía a la institución?**  
   Sí. Grupo 1 pertenecía a la sede principal de la institución.
7. **¿El año lectivo pertenecía a la institución?**  
   Sí. Año 2026 (ACTIVO) pertenecía a la institución.
8. **¿La asignatura seleccionada pertenecía a la institución?**  
   No estaba persistida en la base de datos.
9. **¿Se requería una relación previa no creada en el aprovisionamiento?**  
   No.
10. **¿El backend aplicó reglas de lectura a una creación?**  
    No.
11. **¿Hubo discrepancia de `institution_id` entre entidades existentes?**  
    No.
12. **¿Hubo conflicto de unicidad o regla de negocio oculta?**  
    No.
13. **¿El frontend envió los campos e IDs correctos?**  
    Sí. El frontend envió los UUIDs tal como los recibió del endpoint `GET /api/v1/subjects`.

#### C. Causa Raíz Exacta (Transacción GET sin Commit)
1. Al aprovisionar una nueva institución, no existen registros de asignaturas en la tabla `subjects`.
2. Al abrir la vista de asignaciones académicas, el frontend consulta `GET /api/v1/subjects`.
3. El endpoint invoca `_seed_statutory_subjects_if_needed(db, target_institution_id)` para auto-generar las ~120 asignaturas del currículo estándar colombiano (Ley 115).
4. La función insertaba las asignaturas y ejecutaba `await db.flush()`.
5. **Defecto:** Al tratarse de una petición `GET`, el endpoint `list_subjects` nunca llamaba a `await db.commit()`. Al terminar la petición HTTP, SQLAlchemy y el context manager cerraban la sesión y **descartaban (rollback)** la inserción.
6. El frontend recibió los UUIDs transitorios en la respuesta `200 OK`, pero en PostgreSQL la tabla `subjects` quedó completamente vacía (`0` filas).
7. Cuando el usuario intentaba crear la asignación (`POST /api/v1/academic-assignments`), `AcademicAssignmentService` buscaba el `subject_id` en una nueva sesión y no lo encontraba, elevando `AcademicDomainError` (HTTP 400).

#### D. Solución Aplicada
- En `backend/app/api/v1/endpoints/subjects.py` (función `_seed_statutory_subjects_if_needed`), se sustituyó `await db.flush()` por `await db.commit()`.
- Ahora, cuando se listan o consultan asignaturas para cualquier institución recién provisionada, el plan de estudios estatutario se auto-siembra y **queda confirmado permanentemente en PostgreSQL**.
- Las llamadas posteriores a `POST /api/v1/academic-assignments` localizan la asignatura en la base de datos y crean la asignación exitosamente con HTTP 201 Created.

#### E. Prueba de Regresión
- Se añadió la prueba `test_phase13e5_assignment_creation_with_auto_seeded_curriculum` en `backend/tests/test_academic_api.py`, demostrando el ciclo completo: siembra automática $\rightarrow$ persistencia confirmada $\rightarrow$ asignación académica creada exitosamente.

---

### 4. Verificación de Seguridad y No Regresión

1. **Aislamiento Multi-Tenant (Fase 13E.4):**  
   Se mantuvieron intactos los 10 tests de `tests/test_guardian_tenant_isolation.py`. Una institución A jamás puede ver ni interactuar con datos de una institución B.
2. **Alcance Académico Docente (Fase 13E.1):**  
   Se preservó la cadena de visibilidad `Docente -> Asignación -> Grupo -> Matrícula -> Estudiante`.
3. **Seguridad de Base de Datos:**  
   No se introdujeron migraciones ni cambios de esquema destructivos.

---

### 5. Archivos Modificados

1. [`frontend/src/types/academic.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual%20Nacional%20PEVN/frontend/src/types/academic.ts):
   - Alineación de `GuardianRelationshipType` con los valores canónicos (`'PADRE' | 'MADRE' | 'ABUELO_A' | 'TIO_A' | 'TUTOR_LEGAL' | 'OTRO'`).
2. [`frontend/src/pages/academic/GuardiansView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual%20Nacional%20PEVN/frontend/src/pages/academic/GuardiansView.tsx):
   - Actualización de los selectores de parentesco en modal de registro y modal de vinculación.
3. [`backend/app/api/v1/endpoints/subjects.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/subjects.py):
   - Inclusión de `await db.commit()` en `_seed_statutory_subjects_if_needed` para garantizar persistencia transaccional.
4. [`backend/tests/test_academic_api.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa Virtual%20Nacional%20PEVN/backend/tests/test_academic_api.py):
   - Incorporación de `test_phase13e5_guardian_abuelo_and_tio_registration` y `test_phase13e5_assignment_creation_with_auto_seeded_curriculum`.

---

### 6. Resultados de las Pruebas

- **Backend Pytest Suite:** **349 / 349 tests PASSED** (100% green).
- **Frontend Build (`npm run build`):** **0 errors** (vite build exitoso).
