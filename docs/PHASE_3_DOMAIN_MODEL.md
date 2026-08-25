# MODELO DE DOMINIO ACADÉMICO — FASE 3A
# Plataforma Educativa Virtual Nacional (PEVN)

> **ESTADO:** DISEÑO ARQUITECTÓNICO — LECTURA EXCLUSIVA  
> **LÍNEA BASE DE SEGURIDAD:** REUTILIZA EL MOTOR DE AUTORIZACIÓN Y TENANCY DE FASE 2 SIN MODIFICACIONES.

---

## 1. Clasificación y Taxonomía de Entidades del Dominio

Para optimizar la integridad referencial y el rendimiento del sistema, las entidades se clasifican en cinco categorías arquitectónicas:

```
+---------------------------------------------------------------------------------------+
|                               CLASIFICACIÓN DE ENTIDADES                              |
+---------------------------------------------------------------------------------------+
| 1. ENTIDADES NÚCLEO (Core Entities)                                                   |
|    - AcademicYear (Año Lectivo)                                                       |
|    - AcademicPeriod (Período Académico / Bimestre / Trimestre)                        |
|    - Grade (Grado / Nivel Curricular)                                                 |
|    - Group (Grupo / Curso / Salón)                                                    |
|    - Subject (Asignatura Curricular)                                                  |
|    - Student (Estudiante)                                                             |
|    - Teacher (Docente)                                                                |
|    - Enrollment (Matrícula)                                                           |
|    - AcademicAssignment (Asignación Académica Docente)                                |
+---------------------------------------------------------------------------------------+
| 2. ENTIDADES DE SOPORTE (Supporting Entities)                                         |
|    - KnowledgeArea (Área Fundamental del Conocimiento)                                |
|    - Guardian (Acudiente / Padre / Madre / Tutor Legal)                               |
|    - StudentGuardian (Relación de Parentesco y Responsabilidad Legal)                 |
+---------------------------------------------------------------------------------------+
| 3. ENTIDADES DE CATÁLOGO / REFERENCIA (Reference Catalogs)                            |
|    - EducationalLevelEnum (Preescolar, Primaria, Secundaria, Media)                   |
|    - AcademicCalendarEnum (Calendario A, Calendario B)                                |
|    - ShiftEnum (Jornada: Mañana, Tarde, Completa, Nocturna, Única)                    |
|    - EnrollmentStatusEnum (Pre-matriculado, Activo, Retirado, Graduado, Trasladado)   |
|    - AcademicYearStatusEnum (Planificación, Activo, Cerrado, Archivado)               |
+---------------------------------------------------------------------------------------+
| 4. ENTIDADES DE ASOCIACIÓN (Association Entities)                                     |
|    - GroupStudentMembership (Vinculación actual de estudiante al grupo)               |
|    - GroupDirector (Docente Director de Grupo)                                        |
+---------------------------------------------------------------------------------------+
| 5. ENTIDADES HISTÓRICAS / TRAZABILIDAD (Historical Entities)                          |
|    - GroupTransferHistory (Historial de traslados de salón dentro del año lectivo)    |
|    - EnrollmentStatusHistory (Bitácora de cambios de estado de matrícula)             |
+---------------------------------------------------------------------------------------+
```

---

## 2. Definición Detallada de Entidades del Dominio

### 2.1. Estructura Temporal y Calendario

#### `AcademicYear` (Año Lectivo)
- **Propósito:** Representa el período anual oficial en el que se imparten las clases (e.g. 2026).
- **Alcance Tenant:** Perteneciente a una `Institution`. Permite que distintas instituciones gestionen sus calendarios según Calendario A o B.
- **Invariantes:**
  - Solo puede existir **un (1) año lectivo en estado `ACTIVO`** simultáneamente por institución.
  - La fecha de inicio (`start_date`) debe ser estrictamente anterior a la fecha de finalización (`end_date`).
  - No puede eliminarse físicamente si contiene matrículas o asignaciones asociadas.

#### `AcademicPeriod` (Período Académico)
- **Propósito:** Subdivisiones evaluativas del año lectivo (e.g., 4 períodos de 25% cada uno o 3 trimestres de 33.3%).
- **Alcance Tenant:** Perteneciente a un `AcademicYear`.
- **Invariantes:**
  - La sumatoria de las ponderaciones porcentuales de los períodos de un año lectivo debe ser exactamente igual al **100%**.
  - Los rangos de fechas de los períodos de un mismo año no pueden solaparse.

---

### 2.2. Estructura Curricular

#### `KnowledgeArea` (Área del Conocimiento)
- **Propósito:** Agrupación curricular mayor según lineamientos del MEN (e.g., *Matemáticas*, *Ciencias Naturales y Educación Ambiental*, *Humanidades*).
- **Alcance Tenant:** Puede ser **Catálogo Nacional** (predefinido por el MEN) o institucional para áreas complementarias.

#### `Subject` (Asignatura)
- **Propósito:** Materia curricular específica (e.g., *Cálculo*, *Química Orgánica*, *Inglés*).
- **Alcance Tenant:** Perteneciente a una `Institution` y asociada a un `KnowledgeArea`.
- **Invariantes:** Intensidad horaria semanal mayor a cero.

#### `Grade` (Grado)
- **Propósito:** Nivel educativo formal estandarizado (Transición, 1° a 11°).
- **Alcance:** **Catálogo Nacional Compartido** (sin `institution_id`). Estructura inmutable regulada por el MEN para garantizar coherencia curricular en todo el país.

---

### 2.3. Estructura Organizativa y Grupos

#### `Group` (Grupo / Curso)
- **Propósito:** Unidad organizativa de estudiantes en una sede física o virtual (e.g., "Grado 10 - Grupo 10-02 - Jornada Mañana - Sede Principal").
- **Alcance Tenant:** Perteneciente a un `Campus` (`campus_id`), asociado a un `Grade` del catálogo nacional y a un `AcademicYear`.
- **Atributos:**
  - `name`: Código o identificador del grupo (e.g. "10-02", "11-A").
  - `shift`: Jornada escolar (`ShiftEnum`).
  - `capacity_limit`: Cupo máximo de estudiantes para control de hacinamiento.
  - `group_director_id`: Docente asignado como director de grupo.

---

### 2.4. Actores Educativos y Perfiles

#### `Student` (Estudiante)
- **Propósito:** Perfil académico y socio-demográfico del estudiante.
- **Relación con Identidad:** Vinculado `1:1` con `User` (`user_id`).
- **Atributos:**
  - `code_simat`: Código único de estudiante asignado por el SIMAT.
  - `birth_date`, `gender`, `blood_type`, `rh`.
  - `eps_health_provider`, `stratum` (Estrato socioeconómico 1-6).
  - `has_disability`, `disability_type` (Inclusión educativa MEN).

#### `Teacher` (Docente)
- **Propósito:** Perfil profesional del docente.
- **Relación con Identidad:** Vinculado `1:1` con `User` (`user_id`).
- **Atributos:**
  - `specialty_area`: Área de especialización pedagógica.
  - `escalafon_grade`: Grado en el escalafón docente (Decreto 2277 de 1979 o Decreto 1278 de 2002).
  - `contract_type`: Nombramiento en propiedad, provisionalidad, o temporal.

#### `Guardian` (Acudiente / Tutor Legal)
- **Propósito:** Perfil del representante legal del estudiante menor de edad.
- **Relación con Identidad:** Vinculado `1:1` opcional con `User` (`user_id` nullable).
- **Atributos:** Teléfono de emergencia, dirección de residencia, nivel de escolaridad y parentesco (Padre, Madre, Abuelo, Tutor Legal).

---

### 2.5. Operaciones de Matrícula y Asignación

#### `Enrollment` (Matrícula)
- **Propósito:** Vínculo jurídico y académico que formaliza el derecho del estudiante a cursar un grado en una institución durante un año lectivo.
- **Invariantes Críticas:**
  - **REGLA DE ORO 1 (Matrícula Activa Única):** Un estudiante solo puede tener **una (1) matrícula en estado `ACTIVE` en un mismo año lectivo**.
  - **Invariante en Base de Datos:** Protegida mediante índice único parcial PostgreSQL:  
    `CREATE UNIQUE INDEX uq_enrollments_single_active_per_year ON enrollments (student_id, academic_year_id) WHERE status = 'ACTIVE';`
  - **Preservación Histórica:** Si un estudiante se traslada o retira, el registro anterior pasa a `TRANSFERRED` o `WITHDRAWN`, permitiendo crear una nueva matrícula activa sin violar la restricción y conservando la trazabilidad completa.
  - Toda matrícula debe estar asociada a un `Group` específico dentro del `AcademicYear`.

#### `AcademicAssignment` (Carga Académica Docente)
- **Propósito:** Asignación de un `Teacher` a una `Subject` específica en un `Group` determinado para un `AcademicYear`.
- **Invariantes:**
  - **Docente Titular Activo Único:** Protegida por índice único parcial:  
    `CREATE UNIQUE INDEX uq_academic_assignments_single_active ON academic_assignments (subject_id, group_id, academic_year_id) WHERE is_active = TRUE;`
  - Permite a la Fase 4 (BigBlueButton) determinar quién es el moderador/profesor legítimo del aula virtual.

---

## 3. Ciclo de Vida de Entidades Principales

```
[AcademicYear Lifecycle]
PLANIFICACIÓN (Registro inicial de fechas y períodos)
      │
      ▼
ACTIVO (Año lectivo en curso, matrículas y clases activas)
      │
      ▼
CERRADO (Cierre de notas y promoción de estudiantes)
      │
      ▼
ARCHIVADO (Inmutable para consultas históricas y certificaciones)

---------------------------------------------------------------------------------

[Enrollment Lifecycle]
PRE_MATRICULADO (Inscripción inicial y validación documental)
      │
      ▼
ACTIVO (Estudiante matriculado y asignado a grupo)
      │
      ├───────────────────────┬────────────────────────┐
      ▼                       ▼                        ▼
RETIRADO (Abandono)     TRASLADADO (Cambio SED)   GRADUADO / PROMOVIDO (Fin de ciclo)
```

---

## 4. Decisiones Arquitectónicas Abiertas (Open Architectural Decisions)

Las siguientes definiciones requieren confirmación de negocio con el Ministerio de Educación Nacional / Product Owner antes de iniciar la Fase 3B:

1. **`[OPEN-DECISION-3A-01]` — Manejo de Acudientes sin Correo Electrónico Único:**  
   *Contexto:* En zonas rurales colombianas, acudientes de múltiples hermanos pueden no poseer correo electrónico personal o compartir el mismo teléfono.  
   *Opciones:* (A) Permitir creación de acudientes con documento de identidad como identificador primario sin cuenta de login interactiva obligatoria; (B) Exigir cuenta `User` para todo acudiente.  
   *Recomendación:* Opción A para garantizar máxima inclusión territorial.

2. **`[OPEN-DECISION-3A-02]` — Traslado Inter-Institucional Automático vs. Manual:**  
   *Contexto:* Flujo cuando un estudiante se matricula en una institución B mientras está activo en la institución A.  
   *Opciones:* (A) La nueva institución solicita liberación y la institución origen debe aprobar; (B) Los administradores municipales/departamentales autorizan el traslado directamente.

3. **`[OPEN-DECISION-3A-03]` — Escalas Evaluativas Personalizadas:**  
   *Contexto:* Decreto 1290 de 2009 permite a cada colegio definir su Sistema Institucional de Evaluación de los Estudiantes (SIEE) homologado a la escala nacional (Bajo, Básico, Alto, Superior).  
   *Alcance Fase 3:* Se modela la estructura de períodos y ponderaciones; las escalas numéricas específicas se integrarán en el módulo de calificaciones.
