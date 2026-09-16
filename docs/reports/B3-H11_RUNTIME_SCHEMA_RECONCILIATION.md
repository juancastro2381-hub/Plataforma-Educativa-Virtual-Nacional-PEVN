# INFORME TÉCNICO DE RECONCILIACIÓN DE ESQUEMA Y RUNTIME — FASE B3-H11
## RESOLUCIÓN DE BLOQUEO: `UndefinedTableError: relation "activity_resources" does not exist`
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** 12 de Septiembre de 2026  
**Estado del Gate:**
* **`B3-H11 RUNTIME SCHEMA RECONCILIATION = PASS`**
* **`B3-H11 TECHNICAL VERIFICATION = PASS`**
* **`B3-H11 HUMAN VALIDATION = READY TO RESUME (PAUSED PENDING USER CONFIRMATION)`**

---

## 1. RESUMEN EJECUTIVO Y CAUSA RAÍZ

Durante la validación funcional humana en el navegador del Portal Docente (`http://localhost:3000/teacher`), la petición HTTP a `GET /api/v1/teacher/activities` retornó un error `HTTP 500 (Internal Server Error)`.

### 1.1 Causa Raíz Identificada
* En la implementación técnica de B3-H11 se creó la migración Alembic `022_activity_resources_and_storage.py` y el modelo SQLAlchemy `ActivityResource`.
* Las pruebas automatizadas previas de verificación se ejecutaron contra el fixture de prueba de SQLite en memoria (que invoca dinámicamente `Base.metadata.create_all`).
* La base de datos relacional PostgreSQL activa del entorno de desarrollo (`pevn_db` en el puerto `5433`) se encontraba en la revisión `021_phase15_communications_news_incidents` y **aún no había recibido el comando oficial de migración `alembic upgrade head`**.
* Al acceder al Portal Docente, la consulta con eager loading `selectinload(AcademicActivity.resources)` intentó consultar la tabla `activity_resources` en PostgreSQL, disparando la excepción:
  `asyncpg.exceptions.UndefinedTableError: relation "activity_resources" does not exist`.

---

## 2. PREFLIGHT Y DIAGNÓSTICO FORENSE (READ-ONLY)

Antes de cualquier alteración en la base de datos se ejecutó una inspección exhaustiva de solo lectura:

### 2.1 Identificación del Runtime y DSN de Conexión
* **Variable:** `DATABASE_URL`
* **DSN Efectivo:** `postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db`
* **Host:** `localhost`
* **Puerto:** `5433`
* **Base de Datos:** `pevn_db`
* **Usuario:** `pevn_app`
* **Confirmación:** Corresponde exactamente a la instancia PostgreSQL activa en Docker utilizada por el backend en desarrollo local.

### 2.2 Estado de la Cadena Alembic Previo a la Corrección
* **`alembic current`:** `021_phase15_communications_news_incidents`
* **`alembic heads`:** `022_activity_resources_and_storage (head)`
* **`alembic history`:** Cadena lineal y continua sin bifurcaciones:
  `001 -> ... -> 020_guardian_invitations -> 021_phase15_communications_news_incidents -> 022_activity_resources_and_storage (head)`
* **Tabla `activity_resources` en PostgreSQL:** `False` (no existía en `information_schema.tables`).
* **Valor en tabla `alembic_version`:** `['021_phase15_communications_news_incidents']`.
* **Diagnóstico de situación:** **Situación A** (la base de datos estaba legítimamente retrasada por una revisión; la migración 022 ya existía, pertenecía a la cadena y no había migraciones previas pendientes).

---

## 3. CORRECCIÓN CONTROLADA APLICADA

Se aplicó la migración oficial de Alembic sin modificar modelos ni alterar lógica funcional:

### 3.1 Comando Ejecutado
```powershell
python -m alembic upgrade head
```

### 3.2 Salida de Ejecución
```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 021_phase15_communications_news_incidents -> 022_activity_resources_and_storage, Activity Pedagogical Resources & Secure Storage Schema (Phase B3-H11)
```

---

## 4. EVIDENCIA POST-MIGRACIÓN DE ESQUEMA E INTEGRIDAD

### 4.1 Estado de Versión Alembic
* **`alembic current`:** `022_activity_resources_and_storage (head)`
* **`alembic_version` en `pevn_db`:** `['022_activity_resources_and_storage']`

### 4.2 Inspección Estructural de la Tabla `activity_resources`

| Columna | Tipo de Dato (PostgreSQL) | Nullable | Valor por Defecto |
| :--- | :--- | :---: | :--- |
| `id` | `uuid` | `NO` | `gen_random_uuid()` |
| `activity_id` | `uuid` | `NO` | `None` |
| `institution_id` | `uuid` | `NO` | `None` |
| `resource_type` | `USER-DEFINED` (`activity_resource_type_enum`) | `NO` | `'URL'::activity_resource_type_enum` |
| `title` | `character varying` | `NO` | `None` |
| `url` | `character varying` | `YES` | `None` |
| `file_path` | `character varying` | `YES` | `None` |
| `original_filename` | `character varying` | `YES` | `None` |
| `file_size_bytes` | `bigint` | `YES` | `None` |
| `mime_type` | `character varying` | `YES` | `None` |
| `created_at` | `timestamp with time zone` | `NO` | `now()` |
| `updated_at` | `timestamp with time zone` | `NO` | `now()` |

### 4.3 Llaves Primarias, Foráneas y Restricciones
* **Primary Key:** `activity_resources_pkey` sobre columna `id`.
* **Foreign Key 1:** `activity_resources_activity_id_fkey` (`activity_id` $\rightarrow$ `academic_activities.id`) con `on_delete=CASCADE`.
* **Foreign Key 2:** `activity_resources_institution_id_fkey` (`institution_id` $\rightarrow$ `institutions.id`) con `on_delete=RESTRICT`.
* **Check Constraint:** `ck_activity_resources_type_fields`:
  `CHECK (((resource_type = 'URL'::activity_resource_type_enum) AND (url IS NOT NULL)) OR ((resource_type = 'FILE'::activity_resource_type_enum) AND (file_path IS NOT NULL) AND (original_filename IS NOT NULL)))`
* **Índices Creados:**
  - `activity_resources_pkey` (UNIQUE btree sobre `id`)
  - `ix_activity_resources_activity_id` (btree sobre `activity_id`)
  - `ix_activity_resources_institution_id` (btree sobre `institution_id`)

### 4.4 Verificación de Preservación de Datos Existentes
Se comprobó el conteo de registros en las tablas principales de `pevn_db` antes y después de la migración:
* `users`: 188 registros intactos.
* `institutions`: 33 registros intactos.
* `academic_activities`: 1 registro intacto (`B3 — Prueba Persistencia DRAFT EDITADA`).
* `groups`: 7 registros intactos.
* `teachers`: 13 registros intactos.
* **Pérdida de datos:** **0% (Cero pérdida de datos)**.

---

## 5. PRUEBAS DE VERIFICACIÓN FUNCIONAL Y ENDPOINTS HTTP

### 5.1 Verificación de la Consulta Anteriormente Fallida
Se ejecutó directamente sobre `pevn_db` la consulta SQL exacta que disparaba el `UndefinedTableError`:
```sql
SELECT activity_resources.activity_id AS activity_resources_activity_id,
       activity_resources.id AS activity_resources_id,
       ...
FROM activity_resources
WHERE activity_resources.activity_id IN ('81f97b82-fe92-41f1-b36e-0e62546d03bc')
ORDER BY activity_resources.created_at;
```
* **Resultado:** Ejecutada en `0.01s`, retornó 0 filas sin ningún error.

### 5.2 Verificación HTTP de Endpoints contra PostgreSQL en Vivo
Utilizando la aplicación FastAPI completa autenticada como la docente `natalia.castro@colegio.edu.co`:

1. **`GET /api/v1/teacher/activities`:**
   - **Código HTTP:** `200 OK`
   - **Duración:** `1222.74 ms`
   - **Cuerpo:** 1 actividad retornada con array de `resources` inicializado en 0.
2. **`GET /api/v1/teacher/activities/81f97b82-fe92-41f1-b36e-0e62546d03bc/resources`:**
   - **Código HTTP:** `200 OK`
   - **Duración:** `627.69 ms`
   - **Cuerpo:** `total=0`, `items=[]`.
   - **Resultado:** **Cero errores 500, cero excepciones `UndefinedTableError`**.

### 5.3 Suites Automatizadas de Regresión
* **Suite Focalizada B3-H11:**
  `pytest tests/test_activity_resources_and_storage.py -v`: **5/5 PASSED (100%) en 8.81s**.
* **Suite Combinada Portales + Storage:**
  `pytest tests/test_teacher_portal_api.py tests/test_student_portal_api.py tests/test_activity_resources_and_storage.py -v`:
  **32/32 PASSED (100%) en 85.96s**.
* **Frontend Typecheck:**
  `npm run typecheck` (`tsc --noEmit`): **0 errores (Code 0)**.
* **Frontend Linting:**
  `npx eslint src/...` (archivos B3-H11): **0 errores / 0 warnings (Code 0)**.
* **Frontend Production Build:**
  `npm run build` (`tsc -b && vite build`): **Exitoso (Code 0)**.

---

## 6. MATRIZ DE ARCHIVOS Y COMANDOS

### 6.1 Archivos Modificados
* **Ningún archivo de modelo o lógica funcional fue alterado.**
* Se mantuvieron estrictamente inalterados los modelos de datos, endpoints y componentes de UI certificados.

### 6.2 Comandos Ejecutados
1. `python -m alembic current`
2. `python -m alembic heads`
3. `python -m alembic history`
4. `python -m alembic upgrade head`
5. `pytest tests/test_activity_resources_and_storage.py -v`
6. `pytest tests/test_teacher_portal_api.py tests/test_student_portal_api.py tests/test_activity_resources_and_storage.py -v`
7. `npm run typecheck`
8. `npx eslint src/pages/teacher/TeacherActivitiesView.tsx src/components/student/StudentTaskDetailModal.tsx src/services/teacher.ts src/services/student.ts src/types/teacher.ts src/types/student.ts`
9. `npm run build`

---

## 7. CONCLUSIÓN Y ESTADO DEL GATE

La inconsistencia de esquema en la base de datos PostgreSQL de desarrollo (`pevn_db`) ha sido remediada de forma segura mediante la aplicación oficial de la migración `022_activity_resources_and_storage`.

Los endpoints `GET /api/v1/teacher/activities` y `GET /api/v1/teacher/activities/{activity_id}/resources` operan con normalidad (`HTTP 200 OK`) y la base de datos cuenta con todas las tablas, llaves foráneas, índices y constraints requeridos sin ninguna pérdida de datos existentes.

* **`B3-H11 RUNTIME SCHEMA RECONCILIATION = PASS`**
* **`B3-H11 TECHNICAL VERIFICATION = PASS`**
* **`B3-H11 HUMAN VALIDATION = READY TO RESUME`**

> [!NOTE]
> De conformidad con las instrucciones de la tarea, **no se ha iniciado la validación humana de forma automática ni se ha avanzado a B3-H12**. El sistema queda detenido a la espera de que el usuario proceda a continuar la validación manual en el navegador.
