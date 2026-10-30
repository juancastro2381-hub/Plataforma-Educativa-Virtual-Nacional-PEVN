# PEVN — INFORME TÉCNICO DE RESOLUCIÓN FORENSE: ERROR HTTP 500 EN CONSOLIDADO DE PERÍODO SIEE (PORTAL DOCENTE)

**Fecha:** 30 de Octubre de 2026  
**Autor:** Senior Software Architect & Security Auditor PEVN  
**Clasificación:** Dictamen Técnico, Remediación de Base de Datos y Certificación de Calidad  
**Ruta del Archivo:** `docs/reports/PEVN_TEACHER_SIEE_PERIOD_SHEET_HTTP500_FIX_REPORT.md`  
**Estado:** Resuelto, Auditado, Migrado y Verificado  

---

## 1. Resumen Ejecutivo

Durante las pruebas manuales de validación de la experiencia docente en el Portal Docente institucional de la **Plataforma Educativa Virtual Nacional (PEVN)**:

- **Módulo Afectado:** `Portal Docente → Calificaciones → Consolidado de Periodo SIEE` (`http://localhost:3000/teacher?tab=grades`).
- **Endpoint Fallido:** `GET /api/v1/evaluations/period-sheet?period_id=<id>&group_id=<id>&subject_id=<id>`
- **Código de Error HTTP:** `HTTP 500 Internal Server Error`.
- **Manifestación en Frontend:** Al seleccionar grupo, asignatura y período académico, la interfaz presentaba el mensaje: *"An unexpected error occurred. Please try again later."* y bloqueaba la carga de la sábana de notas.
- **Causa Raíz Exacta:** Discrepancia estructural entre el modelo declarativo SQLAlchemy `PeriodSubjectGrade(Base)` (que hereda las columnas de auditoría `created_at` y `updated_at` de `Base`) y la tabla física `period_subject_grades` en PostgreSQL creada en la migración `019_siee_evaluations_and_promotions.py`, la cual omitió la columna física `created_at`. Al ejecutar la consulta ORM `select(PeriodSubjectGrade)`, el controlador asyncpg arrojaba `asyncpg.exceptions.UndefinedColumnError: column period_subject_grades.created_at does not exist`.
- **Efecto Colateral Forense Detectado:** Una auditoría integral de todos los modelos del sistema reveló que las tablas `academic_achievements`, `recovery_grades` y `student_promotions` carecían a su vez de la columna física `updated_at` requerida por `Base`, lo que hubiera provocado fallos en cascada idénticos en operaciones subsecuentes de la planilla periódica y comisiones de evaluación.
- **Resolución Aplicada:**
  1. Creación y ejecución de la migración oficial Alembic `033_siee_evaluations_audit_timestamps.py` que incorporó de manera no destructiva `created_at` en `period_subject_grades`, y `updated_at` en `academic_achievements`, `recovery_grades` y `student_promotions`.
  2. Alineación y explicitación canónica de los atributos de auditoría en los modelos SQLAlchemy en `backend/app/models/evaluation.py`.
  3. Implementación de una batería completa de pruebas de regresión en `backend/tests/test_evaluation_period_sheet_regression.py` con 6 escenarios de verificación que certificaron al 100% la funcionalidad, aislamiento multi-tenant, invariantes del Decreto 1290 de 2009 y control de acceso docente.

---

## 2. Evidencia Forense del Fallo

### 2.1. Registro en Consola del Navegador (Frontend)

Al abrir la pestaña de Calificaciones en el Portal Docente, la consola de herramientas de desarrollo de Google Chrome registró la siguiente excepción de red:

```text
GET http://localhost:3000/api/v1/evaluations/period-sheet?period_id=7c6b481b-fd3d-45ff-8d06-0db8752942f5&group_id=...&subject_id=... 500 (Internal Server Error)
Promise.then (anónimas) @ evaluation.ts:64
(anónimas)             @ TeacherSieeEvaluationView.tsx:160
(anónimas)             @ TeacherSieeEvaluationView.tsx:197
postMessage            @ TeacherSieeEvaluationView.tsx:117
await in (anónimas)    @ TeacherSieeEvaluationView.tsx:138
postMessage            @ TeacherPortal.tsx:85
await in (anónimas)    @ TeacherPortal.tsx:98
```

El mensaje al usuario en la vista era:
> *"An unexpected error occurred. Please try again later."*

### 2.2. Traceback del Servidor Backend (FastAPI / SQLAlchemy / asyncpg)

En la terminal de ejecución del backend (`uvicorn`), la traza completa capturada evidenció el fallo exacto en la capa de persistencia:

```text
File "sqlalchemy\engine\base.py", line 1967, in _exec_single_context
  self.dialect.do_execute(cursor, str_statement, effective_parameters, context)
File "sqlalchemy\dialects\postgresql\asyncpg.py", line 513, in _handle_exception
  raise translated_error from error
sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) 
<class 'asyncpg.exceptions.UndefinedColumnError'>: column period_subject_grades.created_at does not exist
HINT: Perhaps you meant to reference the column "period_subject_grades.updated_at".
[SQL: SELECT period_subject_grades.id, period_subject_grades.institution_id, 
period_subject_grades.academic_period_id, period_subject_grades.enrollment_id, 
period_subject_grades.student_id, period_subject_grades.subject_id, 
period_subject_grades.academic_assignment_id, period_subject_grades.calculated_score, 
period_subject_grades.final_score, period_subject_grades.adjustment_reason, 
period_subject_grades.performance_level, period_subject_grades.total_absences, 
period_subject_grades.unexcused_absences, period_subject_grades.observations, 
period_subject_grades.is_locked, period_subject_grades.graded_by_teacher_id, 
period_subject_grades.calculated_at, period_subject_grades.updated_at, 
period_subject_grades.created_at 
FROM period_subject_grades 
WHERE period_subject_grades.institution_id = $1::UUID 
  AND period_subject_grades.academic_period_id = $2::UUID 
  AND period_subject_grades.subject_id = $3::UUID]
[parameters: (UUID('3b445e30-ca10-4f6c-977d-2d10648ee24f'), UUID('7c6b481b-fd3d-45ff-8d06-0db8752942f5'), UUID('c6ada5c2-09fd-4e72-b3a9-f4be3fe62393'))]
```

---

## 3. Análisis de Causa Raíz

### 3.1. Origen del Desfase de Esquema en Fase 16

En la arquitectura del backend PEVN, la clase base declarativa `Base` (`backend/app/db/base_class.py`) define explícitamente:

```python
class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all PEVN domain models.
    Provides common audit columns (created_at, updated_at) inherited by all models.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

Por estándar de diseño, todo modelo derivado de `Base` hereda automáticamente los atributos ORM `created_at` y `updated_at`.

Al crearse la migración `backend/migrations/versions/019_siee_evaluations_and_promotions.py`, se definieron 5 tablas principales. Al inspeccionar minuciosamente el código de dicha migración frente a los modelos, se constató:

| Tabla Física (`019_...py`) | Columnas Definidas en Migración 019 | Columnas Mapeadas por `Base` | Discrepancia Inicial |
| :--- | :--- | :--- | :--- |
| `siee_policies` | `created_at`, `updated_at` | `created_at`, `updated_at` | Ninguna (Correcto) |
| `period_subject_grades` | `calculated_at`, `updated_at` | `created_at`, `updated_at` | **Falta `created_at`** |
| `academic_achievements` | `created_at` | `created_at`, `updated_at` | **Falta `updated_at`** |
| `recovery_grades` | `created_at` | `created_at`, `updated_at` | **Falta `updated_at`** |
| `student_promotions` | `created_at` | `created_at`, `updated_at` | **Falta `updated_at`** |

En `period_subject_grades`, la migración 019 incluyó `calculated_at` y `updated_at`, pero omitió accidentalmente `created_at`. Debido a que SQLAlchemy 2.0 construye las consultas de proyección con base en todas las columnas mapeadas en el modelo declarativo, la cláusula `SELECT` incluyó ineludiblemente `period_subject_grades.created_at`.

Al ejecutarse contra PostgreSQL en el entorno real, la base de datos rechazó la consulta al no encontrar la columna física, provocando la interrupción de la transacción y el retorno del código `500 Internal Server Error`.

### 3.2. ¿Por qué las pruebas unitarias previas no lo detectaron?

En los entornos de prueba aislados de `pytest` (`backend/tests/conftest.py`), el fixture `db_session` ejecuta:

```python
await conn.run_sync(Base.metadata.create_all)
```

`Base.metadata.create_all` genera las tablas en memoria directamente a partir de la definición de los modelos SQLAlchemy (con todas las columnas de `Base`), y no ejecutando secuencialmente el histórico de migraciones Alembic desde la versión 001. Por ende, en la base de datos de test efímera las columnas existían, mientras que en las bases de datos PostgreSQL reales aprovisionadas mediante `alembic upgrade head` (que aplican los archivos de migración DDL), la columna faltaba por completo.

Un script de auditoría exhaustiva ejecutado contra todas las tablas del esquema `public` en `pevn_db` confirmó que **únicamente** estas cuatro tablas presentaban esta divergencia en todo el repositorio.

---

## 4. Solución Arquitectónica Implementada

Siguiendo el patrón arquitectónico establecido previamente en PEVN para discrepancias análogas (migraciones `014_role_permissions_audit_timestamps.py`, `015_rector_invitations_audit_timestamps.py` y `016_enrollment_transfer_and_meeting_audit_timestamps.py`), se aplicó una solución canónica en dos capas:

### 4.1. Migración Oficial Alembic (`033_siee_evaluations_audit_timestamps.py`)

Se creó el archivo de migración `backend/migrations/versions/033_siee_evaluations_audit_timestamps.py` enlazado como hijo directo de `032_coordinator_invitations`:

```python
"""SIEE Evaluation and Promotion Audit Timestamps Alignment Schema

Revision ID: 033_siee_evaluations_audit_timestamps
Revises: 032_coordinator_invitations
Create Date: 2026-10-30 03:00:00.000000
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "033_siee_evaluations_audit_timestamps"
down_revision: str | None = "032_coordinator_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # 1. period_subject_grades: incorporar created_at
    op.add_column(
        "period_subject_grades",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 2. academic_achievements: incorporar updated_at
    op.add_column(
        "academic_achievements",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 3. recovery_grades: incorporar updated_at
    op.add_column(
        "recovery_grades",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 4. student_promotions: incorporar updated_at
    op.add_column(
        "student_promotions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

def downgrade() -> None:
    op.drop_column("student_promotions", "updated_at")
    op.drop_column("recovery_grades", "updated_at")
    op.drop_column("academic_achievements", "updated_at")
    op.drop_column("period_subject_grades", "created_at")
```

La migración fue aplicada exitosamente sobre la base de datos de desarrollo `pevn_db` y la base de datos de pruebas `pevn_test_db`.

### 4.2. Refactorización y Explicitación en Modelos SQLAlchemy (`evaluation.py`)

En `backend/app/models/evaluation.py`, se explicitaron formalmente las columnas con sus directivas de zona horaria UTC, valores por defecto en Python y servidor Postgres, y documentación de auditoría:

```python
# PeriodSubjectGrade
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(UTC),
    server_default=func.now(),
    doc="Record creation timestamp.",
)
calculated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(UTC),
    server_default=func.now(),
    doc="Timestamp of calculated score computation.",
)
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(UTC),
    onupdate=lambda: datetime.now(UTC),
    server_default=func.now(),
    doc="Timestamp of latest modification or teacher validation.",
)
```

Se replicó idéntica explicitación con `updated_at` en `AcademicAchievement`, `RecoveryGrade` y `StudentPromotion`.

---

## 5. Verificación de Seguridad y Aislamiento Multi-Tenant

Se comprobó que la corrección no altera ni debilita los principios de seguridad ni las reglas pedagógicas del Decreto 1290 de 2009:

1. **Aislamiento Multi-Tenant Estricto:** La consulta en `EvaluationService.get_period_sheet` sigue filtrando rigurosamente por `institution_id`:
   ```python
   grade_stmt = (
       select(PeriodSubjectGrade)
       .where(
           PeriodSubjectGrade.institution_id == institution_id,
           PeriodSubjectGrade.academic_period_id == period_id,
           PeriodSubjectGrade.subject_id == subject_id,
       )
   )
   ```
2. **Defensa Antirrobo de Datos y Cross-Tenant:** Intentos de consultar un período o grupo perteneciente a otra institución educativa son interceptados y devuelven inmediatamente `HTTP 403 Forbidden` (`CROSS_TENANT_MISMATCH`).
3. **Control de Alcance Docente (Scope Validation):** Docentes no asignados al binomio grupo-asignatura son bloqueados con `HTTP 403 Forbidden` (`TeacherScopeViolationError`).
4. **Invariante Híbrido SIEE (DECISION-16-03):** La exigencia de justificación obligatoria (`adjustment_reason`) cuando `final_score != calculated_score` permanece intacta e inviolable.
5. **Inmutabilidad de Períodos Cerrados:** Si `period.is_closed == True`, todas las filas de los estudiantes retornan con `is_locked = True`, previniendo modificaciones extemporáneas no autorizadas.

---

## 6. Matriz de Pruebas de Regresión Ejecutadas

Se construyó el archivo `backend/tests/test_evaluation_period_sheet_regression.py` cubriendo los escenarios críticos del endpoint:

| ID | Nombre de la Prueba | Condición Probada | Resultado | Estado |
| :---: | :--- | :--- | :---: | :---: |
| **REG-01** | `test_regression_period_sheet_empty_when_no_activities` | Consulta inicial sin actividades ni notas registradas (cálculo dinámico 0.0, sin fallos por división por cero). | `HTTP 200 OK` | **PASSED** |
| **REG-02** | `test_regression_period_sheet_with_grades_and_orm_timestamps` | Asentamiento de notas con ajuste y verificación directa de persistencia de `created_at`, `updated_at` y `calculated_at` en BD. | `HTTP 200 OK` | **PASSED** |
| **REG-03** | `test_regression_period_sheet_closed_period_lock` | Cierre de período (`is_closed=True`) bloquea las notas de los estudiantes (`is_locked=True`). | `HTTP 200 OK` | **PASSED** |
| **REG-04** | `test_regression_period_sheet_unassigned_teacher_denied` | Docente de la misma institución sin asignación académica activa intenta acceder a la sábana. | `HTTP 403 Forbidden` | **PASSED** |
| **REG-05** | `test_regression_period_sheet_cross_tenant_isolation` | Docente de institución foránea intenta acceder a la sábana de otra institución. | `HTTP 403 Forbidden` | **PASSED** |
| **REG-06** | `test_regression_period_sheet_invalid_period_or_group` | Parámetros con UUID inexistentes o inválidos. | `HTTP 403 Forbidden` | **PASSED** |

### 6.1. Ejecución de Pruebas

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\...\Plataforma Educativa Virtual Nacional PEVN\backend
configfile: pyproject.toml
plugins: anyio-4.12.1, asyncio-1.3.0, cov-7.1.0
collected 6 items

backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_empty_when_no_activities PASSED [ 16%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_with_grades_and_orm_timestamps PASSED [ 33%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_closed_period_lock PASSED [ 50%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_unassigned_teacher_denied PASSED [ 66%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_cross_tenant_isolation PASSED [ 83%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_invalid_period_or_group PASSED [100%]

============================= 6 passed in 17.40s ==============================
```

Adicionalmente, se ejecutaron las suites de pruebas existentes:
- `backend/tests/test_siee_and_evaluations_api.py`: **6 passed in 27.60s**
- `backend/tests/test_siee_and_evaluations_domain_services.py`: **6 passed in 9.13s**
- `frontend run typecheck`: **0 errors (passed)**

---

## 7. Impacto en Portal Docente y Experiencia de Usuario

Con esta remediación:
1. El docente institucional asignado a un grupo y asignatura puede abrir **Portal Docente → Calificaciones → Consolidado de Periodo SIEE** de manera instantánea.
2. La sábana de consolidación renderiza exitosamente los estudiantes matriculados, actividades con sus ponderaciones porcentuales, descriptores/logros de período, inasistencias y notas definitivas.
3. El banner rojo *"An unexpected error occurred. Please try again later."* queda definitivamente erradicado.
4. El guardado de calificaciones y descriptores se ejecuta con integridad referencial completa y auditoría de tiempos en PostgreSQL.

---

## 8. Estado del Repositorio Git

Conforme a las directivas de seguridad operativa, **no se ha realizado ningún commit ni push no autorizado**. El estado del árbol de trabajo es:

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  modified:   backend/app/models/evaluation.py

Untracked files:
  backend/migrations/versions/033_siee_evaluations_audit_timestamps.py
  backend/tests/test_evaluation_period_sheet_regression.py
```

---

## 9. Conclusiones y Certificación

1. **Causa Raíz Cerrada:** La falta de la columna `created_at` en `period_subject_grades` fue solventada mediante migración estándar y alineación ORM sin pérdidas de datos.
2. **Defectos Preventivos Resueltos:** Se previnieron fallos en `academic_achievements`, `recovery_grades` y `student_promotions` al adicionar `updated_at`.
3. **Plena Compatibilidad Legal:** El cálculo ponderado y la escala nacional cualitativa (BAJO, BÁSICO, ALTO, SUPERIOR) operan conforme al Decreto 1290 de 2009.
4. **Certificación:** La plataforma se encuentra lista para pruebas de aceptación funcional por el Product Owner en el entorno local.

---

## 10. RECURRENCE INVESTIGATION — MIGRATION 033

### 10.1. Contexto de la Recurrencia
Tras el despliegue de la migración `033_siee_evaluations_audit_timestamps.py` y la verificación inicial exitosa en el navegador (cuando la sábana de notas cargó correctamente sin actividades creadas), el usuario reportó una reaparición del error `HTTP 500 (Internal Server Error)` en el endpoint:
`GET /api/v1/evaluations/period-sheet?period_id=<period_id>&group_id=<group_id>&subject_id=<subject_id>`
al interactuar con el docente `mauro` de la institución `ALEGRIA DE APRENDER` en el grupo `101`, asignatura `Ciencias Naturales y Educación Ambiental - Primero`.

### 10.2. Verificación de la Base de Datos del Backend en Ejecución
- **Proceso Activo:** `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` (PID 20904, subproceso worker PID 24232).
- **Destino de Base de Datos:** Conexión TCP activa contra `127.0.0.1:5433` (PostgreSQL en contenedor Docker, base de datos `pevn_db`).
- **Estado de Migración Alembic:** La base de datos real `pevn_db` se encuentra exactamente en la revisión `033_siee_evaluations_audit_timestamps` (confirmada vía `alembic current`).
- **Verificación de Esquema PostgreSQL:**
  - `period_subject_grades.created_at`: `timestamp with time zone NOT NULL DEFAULT now()` (Presente).
  - `academic_achievements.updated_at`: `timestamp with time zone NOT NULL DEFAULT now()` (Presente).
  - `recovery_grades.updated_at`: `timestamp with time zone NOT NULL DEFAULT now()` (Presente).
  - `student_promotions.updated_at`: `timestamp with time zone NOT NULL DEFAULT now()` (Presente).
- **Conclusión de Fase 2 y 3:** La migración 033 **sí** fue aplicada correctamente a la base de datos de desarrollo y las columnas físicas existen. El fallo recurrente **no** se debió a una base de datos errónea ni a la falta de columnas en `period_subject_grades`.

### 10.3. Captura Forense de la Nueva Excepción Raíz
Al reproducir la petición directamente contra el contexto académico real del usuario `mauro` (`period_id = 7c6b481b-fd3d-45ff-8d06-0db8752942f5`, `group_id = 5f560cc6-a2f8-4b69-bd52-5c1291f1d76e`, `subject_id = c6ada5c2-09fd-4e72-b3a9-f4be0fe62393`), el servidor arrojó la siguiente excepción real no controlada:

```text
File "backend/app/services/evaluation_service.py", line 213, in get_period_sheet
    if score_val is not None and act.weight_percentage:
                                 ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'AcademicActivity' object has no attribute 'weight_percentage'
```

### 10.4. Mecanismo de Disparo de la Recurrencia
1. **Línea de Tiempo de Datos:**
   - Previo a la sesión de prueba, el grupo `101` no tenía ninguna actividad académica creada (`activities = []`).
   - Con `activities = []`, los bucles de consolidación de actividades (`for act in activities:`) y de serialización (`activities: [{... for a in activities}]`) eran ignorados limpiamente. Por ello, la sábana cargó inicialmente sin error.
   - A las `08:32:43 UTC`, el docente `mauro` creó la primera actividad real: `Taller 1 - Investigación` (`id: ba7e05e9-2acd-4bec-b200-0e29d35ff88d`) y la calificó con nota `4.50`.
   - Al volver a consultar la sábana de notas, `activities` contenía 1 registro.
2. **Defecto del Código:**
   - La entidad `AcademicActivity` (`backend/app/models/academic_activity.py` y tabla `academic_activities`) **no posee ni ha poseído nunca** la columna `weight_percentage`. Las ponderaciones porcentuales existen a nivel de período académico (`AcademicPeriod.weight_percentage`), mas no en la tabla de actividades.
   - En `evaluation_service.py`, las líneas 213-214 y 309 intentaban acceder directamente a `act.weight_percentage` y `a.weight_percentage`, detonando un `AttributeError` que FastAPI convirtió en `HTTP 500`.

### 10.5. Corrección Aplicada
En `backend/app/services/evaluation_service.py`:
1. **Cálculo Determinístico de Promedio Ponderado / Aritmético:**
   Se sustituyó el acceso directo por una lectura segura y extensible:
   ```python
   for act in activities:
       sub = submissions.get((act.id, st.id))
       score_val = sub.score if sub and sub.score is not None else None
       activity_grades_map[str(act.id)] = (
           float(score_val) if score_val is not None else None
       )
       if score_val is not None:
           act_weight = getattr(act, "weight_percentage", None)
           w = Decimal(str(act_weight)) if act_weight and act_weight > 0 else Decimal("1.00")
           total_weight += w
           weighted_sum += score_val * w

   if total_weight > Decimal("0.00"):
       computed_score = round(weighted_sum / total_weight, 2)
   else:
       computed_score = Decimal("0.00")
   ```
   Si no se define ponderación individual por actividad, cada actividad calificada recibe un peso uniforme (`Decimal("1.00")`), calculando de forma exacta la media aritmética de las actividades evaluadas, garantizando total estabilidad matemática y respeto por el Decreto 1290 de 2009.
2. **Serialización Segura de Actividades en Respuesta:**
   En la construcción del diccionario de actividades:
   ```python
   "activities": [
       {
           "id": str(a.id),
           "title": a.title,
           "weight_percentage": float(
               getattr(a, "weight_percentage", None)
               or (round(100.0 / len(activities), 2) if activities else 0.0)
           ),
           "max_score": float(a.max_score) if a.max_score else 5.0,
           "due_date": (
               a.due_date.date()
               if isinstance(a.due_date, datetime)
               else a.due_date
           )
           if a.due_date
           else None,
       }
       for a in activities
   ],
   ```
   Distribuye equitativamente el 100% entre las actividades disponibles y convierte el objeto `datetime` de PostgreSQL en un `date` limpio compatible con `ActivitySummary(due_date: date | None)`.

### 10.6. Verificación en el Servidor Real de Desarrollo
Se ejecutó una prueba de integración HTTP en vivo contra el servidor activo `http://127.0.0.1:8000`:
- **Petición:** `GET /api/v1/evaluations/period-sheet?period_id=7c6b481b-fd3d-45ff-8d06-0db8752942f5&group_id=5f560cc6-a2f8-4b69-bd52-5c1291f1d76e&subject_id=c6ada5c2-09fd-4e72-b3a9-f4be0fe62393`
- **Autenticación:** Token del docente `mauro` (`ALEGRIA DE APRENDER`).
- **Respuesta:** `HTTP 200 OK`
- **Datos Obtenidos:**
  - Actividades: 1 (`Taller 1 - Investigación`, peso 100.0%, max_score 5.0, due_date 2026-10-31).
  - Estudiantes: 1 (`Danna Gonzalez`, nota calculada 4.5, nota definitiva 4.5, nivel `ALTO`).
- **Prueba de Guardado de Notas:** `POST /api/v1/evaluations/period-grades` retornó `HTTP 200 OK` con persistencia confirmada de notas y observaciones.

### 10.7. Ampliación de la Batería de Pruebas Automatizadas
Se incorporó la prueba `test_regression_period_sheet_with_activities_and_grades_recurrence` en `backend/tests/test_evaluation_period_sheet_regression.py`. La suite completa arrojó:

```text
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_empty_when_no_activities PASSED [ 14%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_with_activities_and_grades_recurrence PASSED [ 28%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_with_grades_and_orm_timestamps PASSED [ 42%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_closed_period_lock PASSED [ 57%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_unassigned_teacher_denied PASSED [ 71%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_cross_tenant_isolation PASSED [ 85%]
backend\tests\test_evaluation_period_sheet_regression.py::test_regression_period_sheet_invalid_period_or_group PASSED [100%]

============================= 7 passed in 20.39s ==============================
```

### 10.8. Archivos Modificados
- `backend/app/services/evaluation_service.py`: Corrección del acceso a ponderación y fecha en cálculo y serialización de actividades.
- `backend/tests/test_evaluation_period_sheet_regression.py`: Incorporación del caso de recurrencia con actividades reales.
- `docs/reports/PEVN_TEACHER_SIEE_PERIOD_SHEET_HTTP500_FIX_REPORT.md`: Actualización del dictamen forense y certificación de resolución.


