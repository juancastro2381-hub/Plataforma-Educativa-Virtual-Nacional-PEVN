# PEVN — INFORME TÉCNICO DE PROTECCIÓN DE DATOS PERSONALES
## INVENTARIO DE DATOS PERSONALES Y SENSIBLES, ANÁLISIS DE CUSTODIA Y PUNTOS DE REVISIÓN INSTITUCIONAL (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco de Referencia:** Ley Estatutaria 1581 de 2012, Decreto 1377 de 2013, Sentencia C-748 de 2011, Ley 1098 de 2006 (Código de la Infancia y la Adolescencia)  
**Fecha:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Technical Assessment (No constituye dictamen legal vinculante)  

---

## 1. Alcance y Advertencia Metodológica

El presente documento constituye un **inventario técnico y operativo de los datos personales y de menores de edad** recolectados, tratados y almacenados en las bases de datos y sistemas de archivos de la Plataforma Educativa Virtual Nacional (PEVN).

> [!IMPORTANT]
> **ADVERTENCIA DE GOBERNANZA:** Este informe **no emite conceptos jurídicos concluyentes ni sustituye el criterio de las autoridades legales competentes**. Su finalidad es proporcionar a los asesores jurídicos del Ministerio de Educación Nacional, Secretarías de Educación y la Superintendencia de Industria y Comercio la radiografía técnica exacta de los flujos de datos para la formalización del marco de gobernanza, política de privacidad y tratamiento de datos personales previo a una adopción gubernamental masiva.

---

## 2. Inventario y Clasificación de Datos Personales Tratados

En cumplimiento de los principios de **finalidad, libertad, veracidad, transparencia, acceso y circulación restringida, seguridad y confidencialidad**, se presenta la clasificación exhaustiva de los datos gestionados por PEVN:

### 2.1 Categoría A: Datos de Identidad de Niñas, Niños y Adolescentes (Estudiantes)
- **Naturaleza Jurídica:** Datos personales de menores de edad con especial protección constitucional y legal reforzada (Art. 7, Ley 1581 de 2012; Art. 12, Decreto 1377 de 2013).
- **Atributos Almacenados:**
  - Código único SIMAT (Sistema de Matrículas del MEN).
  - Nombres y apellidos completos.
  - Tipo y número de documento de identidad (Registro Civil, Tarjeta de Identidad, Permiso de Protección Temporal PPT, Cédula de Extranjería).
  - Fecha de nacimiento y edad calculada.
  - Género / Sexo biológico.
  - Estado de matrícula (`ACTIVE`, `TRANSFERRED`, `GRADUATED`, `INACTIVE`).
  - Grado escolar, grupo y sede a la que pertenece.
- **Ubicación de Almacenamiento:** Tabla relacional `students` y tabla de usuarios `users` en PostgreSQL.
- **Matriz de Acceso:**
  - Rector(a) y Coordinador(a): Acceso completo dentro del colegio.
  - Docentes Asignados: Lectura del listado de estudiantes únicamente de los salones y materias formalmente asignados en su carga académica.
  - Estudiante Titular: Lectura exclusiva de su propia ficha.
  - Acudiente Legal Vinculado: Lectura de las fichas de sus hijos legalmente vinculados mediante la tabla `student_guardians`.
  - Terceros / Otros Estudiantes: **Acceso totalmente bloqueado.** Intentos devuelven Blind 404.
- **Frontera Multi-Tenant:** `institution_id` obligatorio.
- **Auditabilidad:** Modificaciones, traslados y creación de cuentas emiten registros en `audit_logs`.

### 2.2 Categoría B: Datos de Identidad y Contacto de Padres y Acudientes (Guardians)
- **Naturaleza Jurídica:** Datos personales privados y de contacto de adultos responsables.
- **Atributos Almacenados:**
  - Nombres y apellidos.
  - Tipo y número de documento de identificación (C.C., C.E., Pasaporte, PPT).
  - Número telefónico / celular de contacto de emergencia.
  - Dirección de correo electrónico personal.
  - Parentesco o relación jurídica con el menor (Padre, Madre, Abuelo, Tutor Legal).
  - Condición de representante legal principal (`is_primary_guardian`).
- **Ubicación de Almacenamiento:** Tablas `guardians`, `student_guardians`, `users` y `guardian_invitations`.
- **Matriz de Acceso:**
  - Rector(a) y Coordinador(a): Consulta del directorio familiar para efectos de citaciones y emergencias escolares.
  - Docente Titular: Datos de contacto básicos para entrega de informes o seguimiento convivencial.
  - Acudiente Titular: Acceso exclusivo a su propio perfil y el de sus hijos vinculados.
- **Frontera Multi-Tenant:** `institution_id` obligatorio.

### 2.3 Categoría C: Datos de Identidad y Laborales del Personal Docente y Directivo
- **Naturaleza Jurídica:** Datos personales y laborales de servidores públicos o contratistas de la educación.
- **Atributos Almacenados:**
  - Nombres y apellidos.
  - Número de cédula de ciudadanía.
  - Correo electrónico institucional y personal.
  - Título académico / especialidad pedagógica.
  - Asignaciones académicas vigentes (materias y grupos a cargo).
- **Ubicación de Almacenamiento:** Tablas `teachers`, `academic_assignments` y `users`.
- **Matriz de Acceso:**
  - Directivos: Gestión de asignaciones y planta docente.
  - Docente Titular: Consulta y gestión de su propia carga académica.
  - Estudiantes y Familias: Consulta del nombre del docente y asignatura a cargo en su horario escolar.
- **Frontera Multi-Tenant:** `institution_id` obligatorio.

### 2.4 Categoría D: Datos del Historial Académico y Evaluativo (SIEE)
- **Naturaleza Jurídica:** Expediente académico oficial del estudiante regulado por el Decreto 1290 de 2009.
- **Atributos Almacenados:**
  - Calificaciones parciales de actividades, talleres y exámenes.
  - Notas definitivas de período y acumuladas anuales.
  - Juicios valorativos en escala nacional (*Desempeño Bajo, Básico, Alto, Superior*).
  - Justificaciones docentes de ajustes de nota (`adjustment_reason`).
  - Pruebas y notas de nivelación/recuperación formativa (`recovery_grades`).
  - Observaciones pedagógicas de boletín.
  - Actas de promoción escolar de fin de año y condición de graduación.
- **Ubicación de Almacenamiento:** Tablas `activity_grades`, `period_subject_grades`, `recovery_grades`, `student_promotions`.
- **Matriz de Acceso:**
  - Docente Titular: Calificación y registro de notas de sus asignaturas asignadas.
  - Rector(a) y Coordinación: Supervisión de planillas, cierre de períodos y emisión de boletines.
  - Estudiante y Acudiente Vinculado: Consulta de sus propias notas y boletines oficiales emitidos.
- **Frontera Multi-Tenant:** `institution_id` obligatorio.
- **Auditabilidad:** Todo cambio de nota ajustado o reapertura de período cerrado queda registrado de forma inmutable con actor, fecha y motivo.

### 2.5 Categoría E: Datos de Asistencia y Telemetría Escolar
- **Naturaleza Jurídica:** Registro de control de presencia física y sincrónica del menor.
- **Atributos Almacenados:**
  - Asistencia diaria a clase presencial (`PRESENT`, `ABSENT`, `JUSTIFIED`, `LATE`).
  - Registro de conexión a aulas virtuales sincrónicas (`joined_at`, `left_at`, `duration_seconds`).
  - Porcentaje acumulado de inasistencias en el período y año lectivo.
- **Ubicación de Almacenamiento:** Tablas `daily_attendances` y `meeting_attendances`.
- **Matriz de Acceso:** Docente de la clase, Rectoría, Coordinación, Estudiante y Acudiente.

### 2.6 Categoría F: Datos del Observador del Estudiante y Convivencia Escolar (Sensibles)
- **Naturaleza Jurídica:** **DATOS ALTAMENTE SENSIBLES**. Contienen descripciones sobre conducta escolar, descargos de los menores y medidas pedagógicas bajo el marco de la Ley 1620 de 2013 y el Decreto 1965 de 2013.
- **Atributos Almacenados:**
  - Clasificación de la situación escolar (Tipo I: Conflictos cotidianos; Tipo II: Acoso escolar/bullying o ciberacoso que no revisten delito; Tipo III: Hechos que presuntamente constituyen delitos según la ley penal).
  - Descripción narrativa de los hechos ocurridos en el ámbito escolar.
  - Descargos y versión libre expresada por el estudiante.
  - Acuerdos pedagógicos, compromisos restaurativos y plazos de seguimiento.
  - Registro de remisión a entidades externas (Comisaría de Familia, ICBF, Centro de Salud) en situaciones Tipo III.
- **Ubicación de Almacenamiento:** Tablas `student_incidents` e `incident_follow_ups`.
- **Matriz de Acceso:**
  - Rector(a) y Comité de Convivencia Escolar: Acceso institucional restringido.
  - Coordinador(a) de Convivencia y Docente Implicado: Gestión del caso.
  - Estudiante Involucrado y su Acudiente Legal: Visualización de sus propias anotaciones formativas y acuerdos.
  - Terceros / Otros Estudiantes / Otras Familias: **ACCESO ABSOLUTAMENTE VEDADO.** Blind 404 estricto.

### 2.7 Categoría G: Archivos y Evidencias de Tareas (Submissions)
- **Naturaleza Jurídica:** Producciones académicas, textos, ensayos y archivos cargados por los estudiantes.
- **Atributos Almacenados:** Documentos PDF, imágenes de talleres, archivos de texto y observaciones de retroalimentación docente.
- **Ubicación de Almacenamiento:** Sistema de archivos (`backend/data/storage/{institution_id}/...`) particionado por colegio y alumno.
- **Matriz de Acceso:** Estudiante autor, docente calificador y directivos institucionales.

### 2.8 Categoría H: Registros de Auditoría Técnica y Trazabilidad (Audit Logs)
- **Naturaleza Jurídica:** Metadatos técnicos de seguridad y eventos de acceso.
- **Atributos Almacenados:** Identificador de usuario actuante (`actor_id`), dirección IP de origen, cabecera User-Agent del navegador, tipo de evento, identificador de recurso afectado, código de correlación UUID y estampa de tiempo UTC.
- **Ubicación de Almacenamiento:** Tabla inmutable `audit_logs`.
- **Sanitización de Seguridad:** Zero-Secrets / Zero-PII. Las contraseñas, secretos, tokens y cookies son censurados automáticamente con `[REDACTED]`.

---

## 3. Matriz de Ciclo de Vida del Dato y Tratamiento Técnico

| Categoría de Datos | Dónde Reside | Quién Puede Acceder | Límite Multi-Tenant | Nivel de Auditoría | Retención Recomendada | Consideración de Eliminación / Supresión |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Identidad Estudiante** | PostgreSQL (`students`) | Directivos, Docente Asignado, Familia | `institution_id` | `ALTO` | Permanente (Expediente Escolar) | Conservación histórica obligatoria; anonimización sólo por orden judicial. |
| **Identidad Acudiente** | PostgreSQL (`guardians`) | Directivos, Docente Titular, Acudiente | `institution_id` | `ALTO` | Mientras dure la patria potestad / matrícula | Desvinculación de la cuenta al graduarse el menor; datos civiles retenidos en archivo. |
| **Identidad Docente** | PostgreSQL (`teachers`) | Directivos, Docente Titular, Estudiantes | `institution_id` | `ALTO` | Conforme a la legislación laboral pública | Supresión de acceso al cesar nombramiento; historial académico inalterable. |
| **Notas y SIEE** | PostgreSQL (`evaluation_*`) | Docente de la materia, Directivo, Familia | `institution_id` | `CRÍTICO` | Permanente (Libros de Calificaciones) | **Ineliminable**. Constituye documento público oficial del Estado colombiano. |
| **Asistencia** | PostgreSQL (`attendances`) | Docente, Directivo, Familia | `institution_id` | `MEDIO` | 5 años tras finalizar el año lectivo | Archivo pasivo una vez consolidada la promoción escolar. |
| **Convivencia (Observador)**| PostgreSQL (`incidents`) | Comité Convivencia, Docente, Familia | `institution_id` | `CRÍTICO` | Términos de prescripción legal (Decreto 1965/13) | Alta confidencialidad; acceso reservado fuera del colegio. |
| **Archivos de Tareas** | Disco Local / S3 Bucket | Estudiante y Docente Calificador | `institution_id` | `MEDIO` | 1 año lectivo | Depuración de adjuntos al cerrar el año para optimización de almacenamiento. |
| **Auditoría Técnica** | PostgreSQL (`audit_logs`) | SuperAdmin y Auditores Forenses | Global / Filtrado | `MÁXIMO` | Mínimo 3 a 5 años | Tabla append-only; inmutable y no borrable por usuarios operativos. |

---

## 4. Áreas que Requieren Revisión y Decisión Institucional / Legal

Antes de formalizar un despliegue nacional, los equipos legales del Estado colombiano deben definir:

1. **Definición Formal del Responsable y Encargado del Tratamiento:**
   - Establecer con precisión si el **Ministerio de Educación Nacional** actúa como "Responsable del Tratamiento" a nivel macro y las Secretarías de Educación / Colegios como "Encargados", o si cada establecimiento educativo mantiene la titularidad del tratamiento con PEVN como operador tecnológico de la infraestructura.
2. **Autorización Expresa de Tratamiento de Datos de Menores:**
   - Redacción de la cláusula de consentimiento informado que los padres o representantes legales deben suscribir en el acto de matrícula o mediante el módulo de auto-onboarding del portal familiar, garantizando el respeto de los derechos prevalentes de los menores consagrados en el Código de la Infancia y la Adolescencia (Ley 1098 de 2006).
3. **Mecanismo de Ejercicio de Derechos de Habeas Data:**
   - Procedimiento operativo estandarizado para la atención de solicitudes de consulta, rectificación, actualización o supresión de datos conforme al artículo 15 de la Ley 1581 de 2012.
4. **Tablas de Retención Documental (TRD) y Archivo General de la Nación:**
   - Armonización de los plazos de conservación física y digital de los registros evaluativos (boletines, libros de calificaciones y actas de grado) para asegurar su validez como títulos académicos oficiales a perpetuidad.
5. **Protocolo de Manejo y Notificación de Brechas de Seguridad:**
   - Procedimiento de comunicación formal ante la Delegatura de Protección de Datos Personales de la Superintendencia de Industria y Comercio (SIC) en caso de incidentes de seguridad que comprometan la confidencialidad de la información escolar.
