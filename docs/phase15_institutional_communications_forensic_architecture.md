# PEVN — Fase 15: Arquitectura Funcional, Descubrimiento Forense y Diseño Canónico de Comunicados Institucionales, Noticias, Convivencia Escolar y Notificaciones

**Documento:** Informe de Descubrimiento Forense, Arquitectura del Dominio y Plan de Implementación  
**Fase:** Fase 15 — Comunicados Institucionales, Noticias, Convivencia Escolar / Incidentes y Notificaciones  
**Estado:** 📋 **ARQUITECTURA Y DISEÑO FORENSE COMPLETADO (SOLO PLANIFICACIÓN / CERO CÓDIGO MODIFICADO)**  
**Fecha:** Septiembre 2026  
**Clasificación:** Confidencial / Arquitectura de Software PEVN  

---

## 1. Resumen Ejecutivo (Executive Summary)

La **Fase 15** de la **Plataforma Educativa Virtual Nacional (PEVN)** tiene como objetivo diseñar la arquitectura canónica para la comunicación oficial de la comunidad educativa, la divulgación de vida escolar, la gestión del Observador del Estudiante y la convivencia escolar (alineada a la Ley 1620 de 2013 de Colombia), y el sistema de seguimiento de lectura y notificaciones.

Bajo las directivas de este análisis forense:
- **Cero Modificación de Código Previa a la Aprobación**: No se ha alterado ningún esquema de base de datos, servicio backend, ruta API, componente de interfaz ni prueba automatizada.
- **Aislamiento Multi-Inquilino y Anti-IDOR Estricto**: Todo acceso se deriva exclusivamente del token JWT de la sesión autenticada y de la pertenencia institucional/vínculo legal `StudentGuardian`. Ningún identificador suministrado por el cliente es aceptado a ciegas.
- **Separación de Responsabilidades y No Redundancia**: Se diferencian claramente los **Comunicados Oficiales** (direccionales, vinculantes, con vigencia y confirmación de lectura), las **Noticias Institucionales** (divulgación comunitaria, logros y eventos) y las **Situaciones de Convivencia Escolar / Incidentes** (información sensible y confidencial con acceso estrictamente restringido al comité de convivencia, directivos, docentes autorizados y acudientes del estudiante involucrado).
- **Preservación de Portales Certificados**: El Portal del Estudiante (`/student`), el Portal de Acudientes (`/guardian`), el Portal Docente y los módulos administrativos existentes mantienen intacta su funcionalidad certificada (Mis Tareas, Calificaciones, Asistencia, Clases Virtuales, Grabaciones y Aprovisionamiento).

---

## 2. Hallazgos del Descubrimiento Forense (Existing Architecture Findings)

Tras una inspección exhaustiva del repositorio PEVN (backend FastAPI/SQLAlchemy y frontend React/Vite), se constata el estado actual del sistema:

### 2.1. Backend
1. **Identidad Canónica Centralizada (`User`)** ([`backend/app/models/user.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/user.py)):
   - La tabla `users` es la única entidad de autenticación y credenciales (`hashed_password` Argon2id, `is_active`, `must_change_password`, `institution_id`).
   - No existen tablas duplicadas como `StudentUser` ni `GuardianUser`.
2. **Modelo de Estudiante (`Student`)** ([`backend/app/models/student.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/student.py)):
   - Perfil pedagógico vinculado 1:1 de forma estricta con `User.id` (`user_id`). Contiene código nacional SIMAT y metadatos de inclusión.
3. **Modelo de Acudiente y Tutela (`Guardian` & `StudentGuardian`)** ([`backend/app/models/guardian.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/guardian.py)):
   - `Guardian.user_id` es opcional (nullable), soportando acudientes de zonas rurales o sin conectividad (`OPEN-DECISION-3A-01`).
   - `StudentGuardian` modela la relación M:N con atributos canónicos: `relationship_type` (PADRE, MADRE, ABUELO_A, TIO_A, TUTOR_LEGAL, OTRO), `is_primary_contact`, `is_authorized_pickup`.
4. **Dominio Académico y Pedagógico**:
   - `AcademicActivity` y `ActivityGrade` gestionan tareas, talleres y calificaciones formativas.
   - `DailyAttendance` gestiona el registro diario de asistencia escolar.
   - `VirtualClassroom` y `Recording` gestionan sesiones sincrónicas y grabaciones.
5. **Estado de Comunicaciones y Convivencia en Backend**:
   - **No existen modelos ni tablas previas** para Comunicados, Noticias o Incidentes en `backend/app/models/`. La base de datos está limpia y lista para la introducción canónica de estas entidades sin conflictos de esquemas heredados.
   - El catálogo de permisos RBAC en `app/services/rbac_bootstrap_service.py` cuenta con la estructura jerárquica lista para incorporar los nuevos recursos.

### 2.2. Frontend
1. **Portal de Acudientes (`/guardian`)**:
   - Cuenta con una arquitectura dirigida por URL (`GuardianPortal.tsx` con `GuardianNavbar.tsx`).
   - Las pestañas `communications`, `news` e `incidents` se encuentran actualmente enrutadas a un componente visual de reserva controlado ([`GuardianPlaceholderView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/guardian/GuardianPlaceholderView.tsx)) señalizado con el badge honesto `Fase 15`.
   - La selección de hijos (`GuardianStudentSwitcher.tsx`) purga los datos obsoletos antes de cambiar de contexto.
2. **Portal del Estudiante (`/student`)**:
   - Contiene 7 subpestañas operativas (`dashboard`, `subjects`, `tasks`, `grades`, `attendance`, `virtual-classes`, `profile`).
   - Listo para integrar los módulos de comunicados y noticias en su barra de navegación y panel de inicio.
3. **Consola Administrativa y Dashboard (`/dashboard`, `/academic`)**:
   - Estructura modular basada en tarjetas de capacidades según roles y permisos RBAC del usuario en sesión.

---

## 3. Capacidades Existentes Reutilizadas (Existing Capabilities Reused)

| Componente Existente | Ubicación | Modo de Reutilización en Fase 15 |
| :--- | :--- | :--- |
| **`User` (Identidad)** | `backend/app/models/user.py` | Identidad canónica del autor, receptor y emisor de confirmación de lectura. |
| **`Student` & `Guardian`** | `backend/app/models/student.py`, `guardian.py` | Entidades de dominio para contextualización de incidentes y destinatarios de comunicados. |
| **`StudentGuardian`** | `backend/app/models/guardian.py` | Validación estricta Anti-IDOR para restringir la visibilidad de incidentes solo a tutores legales autorizados. |
| **`Institution` & `Campus`** | `backend/app/models/institution.py` | Límite estricto de inquilino (`institution_id`) y alcance de sede (`campus_id`) para segmentación de audiencia. |
| **`Group` & `Grade`** | `backend/app/models/group.py`, `grade.py` | Segmentación granular de audiencia (comunicado dirigido a grado 9° o grupo 10-A). |
| **`AuditService`** | `backend/app/audit/` | Registro inmutable de eventos de publicación, modificación, cierre y consulta de incidentes. |
| **`GuardianStudentSwitcher`** | `frontend/src/components/guardian/` | Selector de contexto de hijo para filtrar incidentes específicos y comunicados de grupo del estudiante activo. |
| **`AcademicActivity`** | `backend/app/models/academic_activity.py` | Preservado intacto para tareas escolares de estudiantes y monitoreo de solo lectura de acudientes. |
| **`VirtualClassroom`** | `backend/app/models/virtual_classroom.py` | Preservado intacto para clases sincrónicas y grabaciones. |

---

## 4. Capacidades Faltantes a Diseñar (Missing Capabilities)

1. **Entidad de Comunicados Oficiales (`InstitutionalCommunication`)**: Gestión de circulares, convocatorias, vigencias, niveles de urgencia y control de destinatarios.
2. **Entidad de Noticias Escolares (`InstitutionalNews`)**: Publicación de vida institucional, proyectos, eventos deportivos/culturales con soporte de portadas multimedia.
3. **Entidad de Convivencia Escolar / Observador (`StudentIncident` y `IncidentFollowUp`)**: Registro formal de situaciones de convivencia escolar tipificadas (Tipo I, II, III según Ley 1620 de 2013), compromisos pedagógicos, descargos y resoluciones.
4. **Mecanismo de Acuse de Recibo y Notificaciones (`CommunicationReceipt`)**: Rastreo de lectura y confirmación de recepción (`read_at`, `acknowledged_at`) sin duplicar contenido en la base de datos.
5. **Control de Audiencia Granular**: Capacidad de segmentar envíos a toda la institución, a un rol específico, a una sede, a un grado o a un grupo puntual.
6. **Endpoints REST Seguros**: Controladores protegidos para gestión administrativa y consulta contextualizada para estudiantes y acudientes.
7. **Vistas de Frontend Reales**: Reemplazo de los placeholders de la Fase 14C en el Portal de Acudientes, incorporación en el Portal del Estudiante y creación de la consola administrativa directiva.

---

## 5. Alcance Funcional General (Functional Scope)

```
                               ┌────────────────────────────────────────────────────────┐
                               │             PEVN FASE 15: VIDA INSTITUCIONAL           │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
          ┌───────────────────────────────────────────────┼───────────────────────────────────────────────┐
          │                                               │                                               │
          ▼                                               ▼                                               ▼
┌──────────────────┐                            ┌──────────────────┐                            ┌──────────────────┐
│   COMUNICADOS    │                            │     NOTICIAS     │                            │   CONVIVENCIA    │
│  INSTITUCIONALES │                            │  INSTITUCIONALES │                            │     ESCOLAR      │
├──────────────────┤                            ├──────────────────┤                            ├──────────────────┤
│• Circulares      │                            │• Logros acad.    │                            │• Situaciones I   │
│• Convocatorias   │                            │• Eventos cult.   │                            │• Situaciones II  │
│• Avisos direct.  │                            │• Vida escolar    │                            │• Situaciones III │
│• Prioridades     │                            │• Galerías/Media  │                            │• Observador      │
│• Audiencia       │                            │• Comunitario     │                            │• Compromisos     │
│• Acuse de recibo │                            │• Sin acuse       │                            │• Confidencial    │
└─────────┬────────┘                            └─────────┬────────┘                            └─────────┬────────┘
          │                                               │                                               │
          └───────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                          │
                                                          ▼
                                          ┌───────────────────────────────┐
                                          │      RECIBOS Y AUDITORÍA      │
                                          ├───────────────────────────────┤
                                          │• CommunicationReceipt         │
                                          │• Notificaciones no leídas     │
                                          │• Trazabilidad inmutable Audit │
                                          └───────────────────────────────┘
```

---

## 6. Arquitectura de Comunicados Institucionales (Communications Architecture)

### 6.1. Propósito y Características
Los **Comunicados Institucionales** representan la voz formal y directiva de la Institución Educativa. Son vinculantes, tienen validez temporal, pueden exigir confirmación de lectura y poseen distintos niveles de prioridad.

### 6.2. Tipología Canónica
- `CIRCULAR_OFICIAL`: Directivas oficiales de rectoría o secretaría de educación.
- `CONVOCATORIA_REUNION`: Citaciones a asambleas de padres, comités de evaluación o entrega de informes.
- `AVISO_ACADEMICO`: Modificaciones de horarios, períodos de nivelación o cronogramas de pruebas.
- `AVISO_ADMINISTRATIVO`: Jornadas pedagógicas, trámites de secretaría o pagos de matrícula.
- `RECORDATORIO`: Avisos preventivos sobre fechas límite.
- `EMERGENCIA_INSTITUCIONAL`: Alertas urgentes de fuerza mayor, suspensión imprevista de clases o contingencias sanitarias/climáticas.

### 6.3. Niveles de Prioridad
- `BAJA`: Información de cortesía general.
- `MEDIA`: Comunicación ordinaria estándar.
- `ALTA`: Notificación destacada con distintivo visual relevante.
- `URGENTE`: Notificación prioritaria emergente que se muestra inmediatamente en la cabecera de los portales y requiere acuse de recibo.

### 6.4. Ciclo de Vida del Comunicado
```
BORRADOR (Draft) ──► PUBLICADO (Published) ──► EXPIRADO (Expired - Automático por fecha) ──► ARCHIVADO (Archived)
```

---

## 7. Arquitectura de Noticias Institucionales (News Architecture)

### 7.1. Distinción Fundamental: Comunicados vs. Noticias
Para evitar duplicidad conceptual y garantizar claridad al usuario:

| Criterio | Comunicados Institucionales | Noticias Institucionales |
| :--- | :--- | :--- |
| **Carácter** | Formal, vinculante, directivo | Informativo, cultural, divulgativo |
| **Emisor** | Rectoría / Coordinación / Secretaría | Comunidad escolar / Comité de prensa / Directivos |
| **Destinatarios** | Segmentados estrictamente por audiencia | Toda la comunidad educativa de la institución |
| **Acuse de Recibo** | Sí (opcional u obligatorio según prioridad) | No (lectura libre) |
| **Vigencia** | Crítica (fecha límite / expiración) | Abierta (archivo cronológico histórico) |
| **Multimedia** | Archivos PDF/documentos adjuntos oficiales | Portada gráfica, galerías de fotos, enlaces de video |

### 7.2. Categorías de Noticias
- `LOGRO_ACADEMICO`: Premiaciones, resultados en pruebas de estado (SABER), ferias de ciencia.
- `EVENTO_CULTURAL`: Obras de teatro, danzas, concursos artísticos, día de la familia.
- `EVENTO_DEPORTIVO`: Juegos intercolegiados, torneos deportivos internos.
- `PROYECTO_INSTITUCIONAL`: Proyectos ambientales escolares (PRAE), iniciativas comunitarias.
- `NOTICIA_GENERAL`: Novedades de infraestructura, salutaciones institucionales.

---

## 8. Arquitectura de Convivencia Escolar / Incidentes (School Coexistence)

### 8.1. Marco Legal Colombiano (Ley 1620 de 2013 y Decreto 1965 de 2013)
En Colombia, la convivencia escolar se rige por el Sistema Nacional de Convivencia Escolar. Toda anotación en el Observador del Estudiante o registro disciplinario debe respetar el debido proceso, la tipificación legal y la estricta reserva de la información de menores de edad.

### 8.2. Tipificación de Situaciones
- `TIPO_I`: Conflictos manejados inadecuadamente y situaciones esporádicas que inciden negativamente en el clima escolar, sin generar daños al cuerpo o a la salud física/mental (ej. desatención reiterada, discusiones verbales menores). Manejo: Mediación pedagógica y compromisos en aula.
- `TIPO_II`: Situaciones de agresión escolar, acoso escolar (bullying) o ciberacoso que no revistan las características de la comisión de un delito y que causen daño al cuerpo o a la salud sin generar incapacidad. Manejo: Remisión al Comité de Convivencia Escolar, acciones restaurativas y comunicación obligatoria a los acudientes.
- `TIPO_III`: Situaciones de agresión escolar que sean constitutivas de presuntos delitos contra la libertad, integridad y formación sexual o cualquier otro delito según la ley penal colombiana. Manejo: Remisión inmediata a autoridades competentes (ICBF, Policía de Infancia y Adolescencia, Fiscalía) y activación de protocolos de protección.
- `OBSERVACION_POSITIVA`: Reconocimiento formativo al mérito, liderazgo y mejoramiento en convivencia (refuerzo positivo en el Observador del Estudiante).

### 8.3. Modelo de Estados del Incidente
```
REGISTRADO (Open) ──► EN_SEGUIMIENTO (In Progress) ──► CON_COMPROMISOS (With Agreements) ──► RESUELTO_CERRADO (Closed)
```

### 8.4. Reglas Estrictas de Visibilidad y Confidencialidad
- **Rector / Directivos / Comité de Convivencia**: Acceso total de lectura, creación, actualización y cierre de incidentes de toda la institución.
- **Coordinador Académico / Convivencia**: Gestión operativa y seguimiento de acuerdos.
- **Docente / Director de Grupo**: Puede registrar situaciones y ver el historial de los estudiantes de sus grupos asignados.
- **Acudiente**: Acceso de **solo lectura** estrictamente limitado a los incidentes donde su hijo/tutorado legal es la parte involucrada, **únicamente si el estado de visibilidad hacia la familia ha sido habilitado por la institución**. No puede ver incidentes de otros estudiantes bajo ninguna circunstancia.
- **Estudiante**: Acceso controlado a sus propias observaciones pedagógicas según la directriz del manual de convivencia institucional.

---

## 9. Arquitectura de Notificaciones y Acuses de Recibo (Notification Model)

Para evitar crear una segunda base de datos o duplicar mensajes:
1. **Unificación de Estado de Lectura (`CommunicationReceipt`)**:
   - Cada vez que un usuario accede a un comunicado dirigido a su perfil, se genera/actualiza un registro ligero en `communication_receipts`:
     - `read_at`: Marca temporal de visualización.
     - `acknowledged_at`: Marca temporal cuando el usuario pulsa "Confirmar que he leído y acepto este comunicado".
2. **Contador de No Leídos en Tiempo Real**:
   - Los endpoints de los portales (`/student/dashboard`, `/guardian/overview`) calculan los comunicados no leídos mediante un `LEFT JOIN` con `communication_receipts WHERE read_at IS NULL AND expires_at >= NOW()`.
3. **Badges en la Interfaz**:
   - Muestra insignias dinámicas (pills) con el número de comunicados pendientes en la barra de navegación del estudiante y del acudiente.

---

## 10. Integración con el Portal del Estudiante (Student Portal)

El **Portal del Estudiante (`/student`)** incorpora:
1. **Pestaña "Comunicados" (`/student?tab=communications`)**:
   - Listado de circulares y avisos oficiales dirigidos a su grado, grupo o a toda la institución.
   - Modal de lectura detallada con opción de confirmar lectura.
2. **Pestaña "Noticias" (`/student?tab=news`)**:
   - Revista digital de vida estudiantil, eventos culturales, deportivos y proyectos pedagógicos.
3. **Widget de Alertas en Dashboard (`/student?tab=dashboard`)**:
   - Tarjeta destacada con comunicados urgentes no leídos antes de la lista de tareas.
4. **Preservación Total de Tareas y Clases**:
   - "Mis Tareas" (`/student?tab=tasks`) y "Clases Virtuales" (`/student?tab=virtual-classes`) se mantienen 100% inalteradas.

---

## 11. Integración con el Portal de Acudientes (Guardian Portal)

El **Portal de Acudientes (`/guardian`)** transforma los placeholders de la Fase 14C en vistas activas conectadas a la API:
1. **Pestaña "Comunicados" (`/guardian?tab=communications`)**:
   - Visualiza comunicados generales de la institución y comunicados específicos del grado/grupo del hijo activo seleccionado.
   - Botón de confirmación formal de lectura para padres de familia.
2. **Pestaña "Noticias" (`/guardian?tab=news`)**:
   - Muestra las novedades comunitarias del colegio.
3. **Pestaña "Convivencia" (`/guardian?tab=incidents`)**:
   - Observador del estudiante contextualizado al hijo seleccionado en el switcher.
   - Muestra situaciones Tipo I/II/III reportadas, acuerdos pedagógicos pactados, fecha de seguimiento y estado del caso.
   - Si el acudiente cambia de hijo en el selector superior, el estado previo se purga inmediatamente y se consulta el observador del nuevo estudiante previa validación server-side de `StudentGuardian`.
4. **Preservación de Tareas y Clases**:
   - "Tareas" (`/guardian?tab=tasks`) se mantiene como monitor de solo lectura (sin botones de entrega).

---

## 12. Integración Administrativa (Admin / Rector Dashboard)

Para el Rector, Administrador Institucional y Coordinador, se diseña el **Módulo de Comunicaciones y Convivencia** dentro de la consola administrativa (`/academic` o `/admin/communications`):
1. **Gestor de Comunicados**:
   - Formulario de redacción con selector de categoría, prioridad, fechas de vigencia y audiencia destinataria.
   - Panel de control de publicaciones (Borrador, Publicado, Expirado) y métricas de lectura (% de acudientes que han leído la circular).
2. **Gestor de Noticias**:
   - Publicación de noticias institucionales con carga de imagen de portada y formato enriquecido.
3. **Libro Digital de Convivencia y Observador**:
   - Directorio de incidentes por estudiante, grupo o sede.
   - Registro de situaciones de convivencia con tipificación Ley 1620, relatoría de hechos, descargos, medidas pedagógicas y control de visibilidad a padres.
   - Generación de reportes institucionales para el Comité de Convivencia Escolar.

---

## 13. Propuesta de Modelo de Datos (Data Model Proposal)

Se propone la creación de **5 entidades SQLAlchemy canónicas** y **3 tablas asociativas de audiencia**:

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    institutions                        │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │ 1:N
                    ┌─────────────────────────────────────┼─────────────────────────────────────┐
                    │                                     │                                     │
                    ▼ 1:N                                 ▼ 1:N                                 ▼ 1:N
     ┌──────────────────────────────┐      ┌──────────────────────────────┐      ┌──────────────────────────────┐
     │ institutional_communications │      │      institutional_news      │      │      student_incidents       │
     ├──────────────────────────────┤      ├──────────────────────────────┤      ├──────────────────────────────┤
     │ id: UUID (PK)                │      │ id: UUID (PK)                │      │ id: UUID (PK)                │
     │ institution_id: UUID (FK)    │      │ institution_id: UUID (FK)    │      │ institution_id: UUID (FK)    │
     │ title: String(200)           │      │ title: String(200)           │      │ student_id: UUID (FK)        │
     │ summary: String(500)         │      │ summary: String(500)         │      │ reporter_user_id: UUID (FK)  │
     │ content: Text                │      │ content: Text                │      │ situation_type: Enum         │
     │ category: Enum               │      │ category: Enum               │      │ incident_date: DateTime      │
     │ priority: Enum               │      │ cover_image_url: String(500) │      │ location: String(150)        │
     │ target_scope: Enum           │      │ status: Enum                 │      │ description: Text            │
     │ published_at: DateTime       │      │ published_at: DateTime       │      │ pedagogical_measures: Text   │
     │ expires_at: DateTime (Null)  │      │ author_user_id: UUID (FK)    │      │ status: Enum                 │
     │ requires_acknowledgment: Bool│      │ created_at: DateTime         │      │ is_visible_to_guardian: Bool │
     │ status: Enum                 │      │ updated_at: DateTime         │      │ is_visible_to_student: Bool  │
     │ author_user_id: UUID (FK)    │      └──────────────────────────────┘      │ closed_at: DateTime (Null)   │
     │ created_at: DateTime         │                                            │ created_at: DateTime         │
     │ updated_at: DateTime         │                                            │ updated_at: DateTime         │
     └──────────────┬───────────────┘                                            └──────────────┬───────────────┘
                    │                                                                           │
         ┌──────────┴──────────┐                                                     ┌──────────┴──────────┐
         │ 1:N                 │ 1:N                                                 │ 1:N                 │
         ▼                     ▼                                                     ▼                     ▼
┌──────────────────┐  ┌───────────────────────┐                             ┌──────────────────┐  ┌──────────────────┐
│communication_    │  │communication_receipts │                             │incident_follow_  │  │incident_         │
│audiences         │  ├───────────────────────┤                             │ups               │  │commitments       │
├──────────────────┤  │ id: UUID (PK)         │                             ├──────────────────┤  ├──────────────────┤
│ communication_id │  │ communication_id (FK) │                             │ id: UUID (PK)    │  │ id: UUID (PK)    │
│ role_name (Null) │  │ user_id (FK)          │                             │ incident_id (FK) │  │ incident_id (FK) │
│ campus_id (Null) │  │ read_at: DateTime     │                             │ user_id (FK)     │  │ compromisario    │
│ grade_id (Null)  │  │ acknowledged_at: Date │                             │ note: Text       │  │ compromiso: Text │
│ group_id (Null)  │  │ created_at: DateTime  │                             │ created_at: Date │  │ fecha_limite     │
└──────────────────┘  └───────────────────────┘                             └──────────────────┘  │ cumplido: Bool   │
                                                                                                  └──────────────────┘
```

### 13.1. Esquema DDL / Atributos de Entidades

#### 1. `InstitutionalCommunication` (`institutional_communications`)
- `id`: `UUID`, Primary Key, `gen_random_uuid()`.
- `institution_id`: `UUID`, FK `institutions.id`, Not Null, Index.
- `author_user_id`: `UUID`, FK `users.id`, Not Null, Index.
- `title`: `String(200)`, Not Null.
- `summary`: `String(500)`, Not Null.
- `content`: `Text`, Not Null (soporte Markdown seguro).
- `category`: `Enum(CommunicationCategory)`: `CIRCULAR_OFICIAL`, `CONVOCATORIA_REUNION`, `AVISO_ACADEMICO`, `AVISO_ADMINISTRATIVO`, `RECORDATORIO`, `EMERGENCIA_INSTITUCIONAL`.
- `priority`: `Enum(CommunicationPriority)`: `BAJA`, `MEDIA`, `ALTA`, `URGENTE`.
- `target_scope`: `Enum(TargetScopeType)`: `TODOS_INSTITUCION`, `SOLO_ESTUDIANTES`, `SOLO_ACUDIENTES`, `SOLO_DOCENTES`, `POR_SEDE`, `POR_GRADO`, `POR_GRUPO`.
- `attachment_url`: `String(500)`, Nullable (archivo PDF oficial).
- `requires_acknowledgment`: `Boolean`, Default `False`.
- `status`: `Enum(PublishingStatus)`: `BORRADOR`, `PUBLICADO`, `ARCHIVADO`.
- `published_at`: `DateTime(timezone=True)`, Nullable.
- `expires_at`: `DateTime(timezone=True)`, Nullable.
- `created_at`, `updated_at`: `DateTime(timezone=True)`.

#### 2. `CommunicationAudience` (`communication_audiences`)
- `id`: `UUID`, Primary Key.
- `communication_id`: `UUID`, FK `institutional_communications.id`, Not Null.
- `campus_id`: `UUID`, FK `campuses.id`, Nullable.
- `grade_id`: `UUID`, FK `official_grades.id`, Nullable.
- `group_id`: `UUID`, FK `groups.id`, Nullable.
- `role_name`: `String(50)`, Nullable (`student`, `guardian`, `teacher`).

#### 3. `CommunicationReceipt` (`communication_receipts`)
- `id`: `UUID`, Primary Key.
- `communication_id`: `UUID`, FK `institutional_communications.id`, Not Null.
- `user_id`: `UUID`, FK `users.id`, Not Null.
- `read_at`: `DateTime(timezone=True)`, Not Null.
- `acknowledged_at`: `DateTime(timezone=True)`, Nullable.
- `client_ip`: `String(50)`, Nullable.
- **Restricción Única**: `(communication_id, user_id)`.

#### 4. `InstitutionalNews` (`institutional_news`)
- `id`: `UUID`, Primary Key.
- `institution_id`: `UUID`, FK `institutions.id`, Not Null, Index.
- `author_user_id`: `UUID`, FK `users.id`, Not Null.
- `title`: `String(200)`, Not Null.
- `summary`: `String(500)`, Not Null.
- `content`: `Text`, Not Null.
- `category`: `Enum(NewsCategory)`: `LOGRO_ACADEMICO`, `EVENTO_CULTURAL`, `EVENTO_DEPORTIVO`, `PROYECTO_INSTITUCIONAL`, `NOTICIA_GENERAL`.
- `cover_image_url`: `String(500)`, Nullable.
- `status`: `Enum(PublishingStatus)`: `BORRADOR`, `PUBLICADO`, `ARCHIVADO`.
- `published_at`: `DateTime(timezone=True)`, Nullable.
- `created_at`, `updated_at`: `DateTime(timezone=True)`.

#### 5. `StudentIncident` (`student_incidents`)
- `id`: `UUID`, Primary Key.
- `institution_id`: `UUID`, FK `institutions.id`, Not Null, Index.
- `student_id`: `UUID`, FK `students.id`, Not Null, Index.
- `reporter_user_id`: `UUID`, FK `users.id`, Not Null (docente o directivo que reporta).
- `situation_type`: `Enum(CoexistenceSituationType)`: `TIPO_I`, `TIPO_II`, `TIPO_III`, `OBSERVACION_POSITIVA`.
- `incident_date`: `DateTime(timezone=True)`, Not Null.
- `location`: `String(150)`, Nullable (aula, patio, virtual, transporte).
- `description`: `Text`, Not Null (relato objetivo de los hechos).
- `student_version`: `Text`, Nullable (descargos / versión del estudiante).
- `pedagogical_measures`: `Text`, Not Null (acciones formativas / restaurativas acordadas).
- `status`: `Enum(IncidentStatus)`: `ABIERTO`, `EN_SEGUIMIENTO`, `CON_COMPROMISOS`, `CERRADO`.
- `is_visible_to_guardian`: `Boolean`, Default `True`.
- `is_visible_to_student`: `Boolean`, Default `True`.
- `closed_at`: `DateTime(timezone=True)`, Nullable.
- `closed_by_user_id`: `UUID`, FK `users.id`, Nullable.
- `created_at`, `updated_at`: `DateTime(timezone=True)`.

#### 6. `IncidentFollowUp` (`incident_follow_ups`)
- `id`: `UUID`, Primary Key.
- `incident_id`: `UUID`, FK `student_incidents.id`, Not Null, Index.
- `author_user_id`: `UUID`, FK `users.id`, Not Null.
- `follow_up_date`: `DateTime(timezone=True)`, Not Null.
- `notes`: `Text`, Not Null.
- `created_at`: `DateTime(timezone=True)`.

---

## 14. Propuesta de Contratos de API REST (API Contract Proposal)

### 14.1. Módulo Administrativo y General

| Método | Endpoint | Rol Mínimo | Permiso Requerido | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/communications` | Docente / Directivo | `communications:read` | Listar comunicados institucionales con filtros. |
| `POST` | `/api/v1/communications` | Directivo / Rector | `communications:create` | Crear comunicado (Borrador o Publicado). |
| `GET` | `/api/v1/communications/{id}` | Docente / Directivo | `communications:read` | Consultar detalle y estadísticas de lectura. |
| `PUT` | `/api/v1/communications/{id}` | Directivo / Rector | `communications:update` | Editar contenido o vigencia del comunicado. |
| `POST` | `/api/v1/communications/{id}/publish` | Directivo / Rector | `communications:publish` | Publicar comunicado borrador. |
| `POST` | `/api/v1/communications/{id}/archive` | Directivo / Rector | `communications:delete` | Archivar o despublicar comunicado. |
| `GET` | `/api/v1/news` | Público / Todos | `news:read` | Listar noticias institucionales publicadas. |
| `POST` | `/api/v1/news` | Directivo / Rector | `news:create` | Redactar noticia institucional. |
| `PUT` | `/api/v1/news/{id}` | Directivo / Rector | `news:update` | Actualizar noticia institucional. |
| `POST` | `/api/v1/news/{id}/publish` | Directivo / Rector | `news:publish` | Publicar noticia institucional. |
| `GET` | `/api/v1/incidents` | Directivo / Docente | `incidents:read` | Listar incidentes escolares según alcance pedagógico. |
| `POST` | `/api/v1/incidents` | Directivo / Docente | `incidents:create` | Registrar situación de convivencia en el Observador. |
| `GET` | `/api/v1/incidents/{id}` | Directivo / Docente | `incidents:read` | Consultar detalle completo y descargos. |
| `POST` | `/api/v1/incidents/{id}/follow-ups` | Directivo / Docente | `incidents:update` | Agregar nota de seguimiento y compromisos. |
| `POST` | `/api/v1/incidents/{id}/close` | Directivo / Rector | `incidents:close` | Resolver y cerrar formalmente el incidente. |

---

### 14.2. Módulo de Estudiantes (`/student/*`)

| Método | Endpoint | Rol Mínimo | Descripción y Reglas de Seguridad |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/student/communications` | `student` | Obtiene comunicados dirigidos al estudiante o a su grupo matriculado. Retorna indicador `is_read` e `is_acknowledged`. |
| `GET` | `/api/v1/student/communications/{id}` | `student` | Obtiene detalle de comunicado. Registra automáticamente `read_at` en `CommunicationReceipt`. |
| `POST` | `/api/v1/student/communications/{id}/acknowledge` | `student` | Confirma formalmente acuse de recibo del comunicado. |
| `GET` | `/api/v1/student/news` | `student` | Listado de noticias institucionales publicadas en el colegio. |
| `GET` | `/api/v1/student/incidents` | `student` | Observador personal del estudiante (solo incidentes donde `is_visible_to_student = True`). |

---

### 14.3. Módulo de Acudientes y Familias (`/guardian/*`)

| Método | Endpoint | Rol Mínimo | Descripción y Reglas de Seguridad |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/guardian/communications` | `guardian` | Obtiene comunicados institucionales y de los grupos de sus hijos matriculados. |
| `GET` | `/api/v1/guardian/communications/{id}` | `guardian` | Detalle del comunicado y registro automático de lectura `read_at`. |
| `POST` | `/api/v1/guardian/communications/{id}/acknowledge` | `guardian` | Acuse de recibo parental firmado digitalmente con timestamp. |
| `GET` | `/api/v1/guardian/news` | `guardian` | Noticias de la institución educativa. |
| `GET` | `/api/v1/guardian/students/{student_id}/incidents` | `guardian` | **Observador del Estudiante de su hijo**: Valida `guardian.user_id == current_user.id` AND relación activa en `StudentGuardian`. Retorna incidentes con `is_visible_to_guardian = True`. Retorna 404 Anti-IDOR si el estudiante no le pertenece. |
| `GET` | `/api/v1/guardian/students/{student_id}/incidents/{incident_id}` | `guardian` | Detalle del incidente, acuerdos pedagógicos y seguimiento. |

---

## 15. Matriz Canónica de Roles y Permisos RBAC (Role / Permission Matrix)

| Recurso / Acción | Superadmin | Rector / Admin Inst. | Coordinador | Docente | Estudiante | Acudiente |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `communications:create` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:read` | ✅ | ✅ | ✅ | ✅ (Institucional) | ✅ (Filtrado) | ✅ (Filtrado) |
| `communications:update` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:publish` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `communications:delete` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `news:create` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `news:read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `news:publish` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `incidents:create` | ✅ | ✅ | ✅ | ✅ (Sus grupos) | ❌ | ❌ |
| `incidents:read` | ✅ | ✅ | ✅ | ✅ (Sus grupos) | ✅ (Propios) | ✅ (Hijos autorizados) |
| `incidents:update` | ✅ | ✅ | ✅ | ✅ (Reportante) | ❌ | ❌ |
| `incidents:close` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 16. Modelo de Seguridad Multi-Inquilino y Análisis Anti-IDOR

### 16.1. Vectores de Ataque Analizados y Mitigaciones
1. **Intento de Acceso a Comunicados de otra Institución**:
   - *Ataque*: Usuario de Institución A consulta `GET /api/v1/communications/{id_inst_b}`.
   - *Defensa*: `_resolve_institution_id` deriva el tenant del JWT. La consulta SQL incluye `WHERE institution_id == current_user.institution_id`. Retorna `404 Not Found`.
2. **Manipulación de `student_id` por parte de un Acudiente Malicioso**:
   - *Ataque*: Acudiente A solicita incidentes de `student_B` (`GET /api/v1/guardian/students/{student_B_id}/incidents`).
   - *Defensa*: El servicio consulta la tabla `StudentGuardian` exigiendo coincidencia con el `guardian.id` vinculado al `current_user.id`. Si no existe relación de tutela legal activa, retorna un `404 Not Found` determinista sin revelar si el estudiante existe.
3. **Fuga de Incidentes Confidenciales a Terceros**:
   - *Ataque*: Un estudiante o acudiente intenta listar incidentes generales a través de endpoints administrativos.
   - *Defensa*: Los endpoints administrativos exigen el permiso `incidents:read` y roles directivos/docentes. Los roles `student` y `guardian` son bloqueados con `403 Forbidden` en la capa de dependencias FastAPI (`require_permission`).
4. **Manipulación de Visibilidad Familiar**:
   - *Ataque*: Un docente intenta ocultar una situación grave Tipo III a los acudientes sin aval directivo.
   - *Defensa*: La política institucional exige que toda situación Tipo II y III tenga por defecto `is_visible_to_guardian = True`. Solo el Rector o el Comité de Convivencia pueden modificar esta bandera mediante auditoría inmutable.

---

## 17. Trazabilidad y Auditoría (Audit Model)

Se registran en la tabla inmutable `audit_logs` los siguientes eventos:
- `COMMUNICATION_CREATED`: Creación de borrador de comunicado.
- `COMMUNICATION_PUBLISHED`: Publicación oficial de comunicado y activación de notificaciones.
- `COMMUNICATION_ARCHIVED`: Cierre o archivo de comunicado.
- `COMMUNICATION_ACKNOWLEDGED`: Acuse de recibo de acudiente o estudiante con timestamp e IP.
- `NEWS_PUBLISHED`: Publicación de noticia institucional.
- `INCIDENT_RECORDED`: Registro inicial de situación de convivencia en el Observador.
- `INCIDENT_UPDATED`: Incorporación de descargos o compromisos formativos.
- `INCIDENT_CLOSED`: Resolución y cierre de situación de convivencia.
- `INCIDENT_VIEWED_BY_GUARDIAN`: Lectura de situación de convivencia por parte del acudiente.

---

## 18. Arquitectura de Frontend y Experiencia de Usuario (Frontend UX)

### 18.1. Integración en Portal de Acudientes (`/guardian`)
- **Pestaña Comunicados**:
  - Filtro por categoría y estado (No leídos / Todos).
  - Tarjeta con badge de prioridad (`Urgente` en rojo brillante con icono de sirena 🚨, `Alta` en naranja, `Media` en azul).
  - Modal de lectura oficial con botón "Firmar / Confirmar Acuse de Recibo".
- **Pestaña Noticias**:
  - Cuadrícula responsive con portada gráfica, fecha, categoría y botón "Leer Noticia Completa".
- **Pestaña Convivencia (Observador)**:
  - Timeline cronológico del Observador del hijo seleccionado.
  - Tarjeta de incidente con pill de tipificación (`Tipo I` amarillo, `Tipo II` naranja, `Tipo III` rojo, `Positiva` verde).
  - Acordeón con relatoría, descargos del estudiante, compromisos suscritos y estado del caso.

### 18.2. Integración en Portal del Estudiante (`/student`)
- Incorporación de subpestañas `communications` y `news` en `StudentNavbar.tsx`.
- Banner emergente en Dashboard para avisos urgentes.

---

## 19. Matriz de Capacidades (Capability Matrix)

| Capacidad | Existente | Parcial | Faltante | Reutiliza | Trabajo Nuevo Requerido | Sensibilidad de Seguridad |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tareas de Estudiantes** | ✅ | ❌ | ❌ | `AcademicActivity` | Ninguno (Preservar) | Media |
| **Monitoreo Tareas Acudiente** | ✅ | ❌ | ❌ | Solo lectura | Ninguno (Preservar) | Media |
| **Clases Virtuales y Grabaciones** | ✅ | ❌ | ❌ | `VirtualClassroom` | Ninguno (Preservar) | Media |
| **Comunicados Institucionales** | ❌ | ❌ | ✅ | `User`, `Institution` | Modelo, Endpoints, UI | Media-Alta |
| **Noticias Institucionales** | ❌ | ❌ | ✅ | `Institution` | Modelo, Endpoints, UI | Baja (Pública inst.) |
| **Convivencia / Observador** | ❌ | ❌ | ✅ | `StudentGuardian` | Modelo, Endpoints, UI | **Crítica (Confidencial)** |
| **Acuse de Recibo / Notificaciones**| ❌ | ❌ | ✅ | `User` | `CommunicationReceipt`| Media |
| **Segmentación de Audiencia** | ❌ | ❌ | ✅ | `Group`, `Grade` | `CommunicationAudience`| Alta (Multi-tenant) |
| **Trazabilidad y Auditoría** | ✅ | ❌ | ❌ | `AuditService` | Nuevos Eventos | Alta |

---

## 20. Decisiones Abiertas que Requieren Aprobación (Open Decisions)

> [!IMPORTANT]
> A continuación se detallan las decisiones de diseño arquitectónico y de negocio que deben ser ratificadas por el usuario antes de la fase de codificación:

### DECISION-15-01: ¿Deben los estudiantes ver sus propios incidentes de convivencia en el Portal del Estudiante?
- **Opción A (Recomendada)**: **Sí, con control de visibilidad (`is_visible_to_student = True`)**. Permite que el Observador del Estudiante cumpla su función formativa y pedagógica, permitiendo al estudiante consultar los compromisos suscritos. Para casos de extrema sensibilidad o investigaciones en curso, el directivo puede marcar `is_visible_to_student = False`.
- **Opción B**: Solo visible para acudientes y directivos.
- *Razón de recomendación*: El debido proceso escolar en Colombia (Sentencias Corte Constitucional) exige que el menor conozca las anotaciones en su observador y participe en los acuerdos restaurativos.

### DECISION-15-02: ¿Expiración automática de comunicados?
- **Opción A (Recomendada)**: **Sí, mediante campo `expires_at` opcional**. Si un comunicado tiene fecha de expiración superada, deja de contabilizarse en los contadores de no leídos y pasa a la sección de archivo histórico.
- **Opción B**: Expiración exclusivamente manual por parte del rector.
- *Razón de recomendación*: Evita saturación de avisos caducados a los padres de familia.

### DECISION-15-03: ¿Entidad separada para Noticias vs. Comunicados?
- **Opción A (Recomendada)**: **Entidades separadas (`InstitutionalCommunication` e `InstitutionalNews`)**. Permite que los comunicados tengan lógica de acuse de recibo, urgencia, fechas de vencimiento y segmentación de audiencia, mientras las noticias se mantienen ligeras y públicas para toda la institución.
- **Opción B**: Una sola tabla `contents` con discriminador de tipo.
- *Razón de recomendación*: La separación de esquemas simplifica las consultas, evita campos nulos innecesarios y optimiza el rendimiento de los índices.

### DECISION-15-04: ¿Quiénes pueden reportar situaciones de convivencia?
- **Opción A (Recomendada)**: **Docentes (para sus grupos asignados), Coordinadores y Rectores**.
- **Opción B**: Exclusivamente Coordinadores de Convivencia y Rectores.
- *Razón de recomendación*: Refleja la realidad operativa de los colegios colombianos donde el docente de aula es el primer respondiente en situaciones Tipo I.

---

## 21. Secuencia Recomendada de Implementación (Implementation Sequence)

Para una ejecución ordenada y con cero regresiones cuando se autorice la Fase 15:

1. **Fase 15A — Modelos de Datos y Migraciones Backend**:
   - Creación de modelos SQLAlchemy: `InstitutionalCommunication`, `CommunicationAudience`, `CommunicationReceipt`, `InstitutionalNews`, `StudentIncident`, `IncidentFollowUp`.
   - Registro de permisos en `RbacBootstrapService`.
2. **Fase 15B — Servicios de Dominio Backend**:
   - `CommunicationService`: Publicación, segmentación y acuses de recibo.
   - `NewsService`: Gestión de noticias y eventos.
   - `CoexistenceIncidentService`: Registro de observador, seguimiento y validación Anti-IDOR.
3. **Fase 15C — Controladores y Endpoints REST Backend**:
   - Controladores `/api/v1/communications`, `/api/v1/news`, `/api/v1/incidents`.
   - Controladores contextuales `/api/v1/student/*` y `/api/v1/guardian/*`.
   - Pruebas unitarias e integración Pytest.
4. **Fase 15D — Integración Frontend Portal de Acudientes (`/guardian`)**:
   - Reemplazo de `GuardianPlaceholderView.tsx` por vistas completas de Comunicados, Noticias y Observador de Convivencia.
5. **Fase 15E — Integración Frontend Portal del Estudiante (`/student`)**:
   - Incorporación de subpestañas de comunicados y noticias.
6. **Fase 15F — Módulo Administrativo y Consola Directiva**:
   - Consola de redacción, publicación y gestión de convivencia escolar.
7. **Fase 15G — Verificación y Certificación Final**:
   - Pruebas de regresión completas y validación de seguridad Anti-IDOR.

---

## 22. Criterios de Aceptación (Acceptance Criteria)

- [ ] Las circulares oficiales pueden publicarse, segmentarse por audiencia y exigir acuse de recibo.
- [ ] Los acudientes pueden consultar comunicados generales y de los grados específicos de sus hijos.
- [ ] La confirmación de lectura registra de forma inmutable el usuario, fecha e IP del firmante.
- [ ] El Observador de Convivencia tipifica situaciones según la Ley 1620 de 2013 (Tipo I, II, III).
- [ ] El acudiente solo puede consultar los incidentes de sus propios hijos vinculados en `StudentGuardian`.
- [ ] Cualquier intento de acceso cruzado entre instituciones o entre estudiantes ajenos retorna `404 Not Found`.
- [ ] Las tareas del estudiante y el monitoreo de tareas de acudientes permanecen 100% inalterados.
- [ ] Las clases virtuales y grabaciones permanecen 100% inalteradas.
- [ ] La suite de pruebas existente permanece 100% verde sin regresiones.
