# PEVN — GUION DE DEMOSTRACIÓN GUBERNAMENTAL EN VIVO (RUNBOOK)
## SECUENCIA PASO A PASO BASADA EN DATOS DE DEMOSTRACIÓN PREEXISTENTES (FASE 0.1)

**Destinatarios:** Evaluadores Gubernamentales, Equipos de Innovación Educativa, Rectores y Oficiales de Ciberseguridad  
**Marco Metodológico:** AI Software Factory v1.2 — Live Government Demonstration Protocol  
**Fecha:** 21 de Septiembre de 2026  
**Regla de Seguridad de Credenciales:** Todas las credenciales de acceso se referencian como `[CUENTA DEMO]` y `[USE EXISTING DEMO CREDENTIAL]`. Ninguna contraseña o identificador personal de producción es expuesto en este documento.  
**Regla de Datos:** Se utilizan **EXCLUSIVAMENTE los registros de demostración preexistentes en la base de datos**. No se crean bases de datos alternas ni se resiembran registros.  
**Protección de Datos de Menores:** Todos los registros corresponden a datos sintéticos de demostración preexistentes en el entorno de pruebas. La presentación ante autoridades gubernamentales no expone datos personales reales de menores de edad, en cumplimiento de la Ley 1581 de 2012 y el principio del interés superior de los niños, niñas y adolescentes (Ley 1098 de 2006).

---

## 1. Inventario de Entidades y Datos de Demostración Preexistentes

La demostración se sustenta en los registros sintéticos de demostración preexistentes en el sistema:

| Tipo de Entidad | Registro en Entorno de Demostración | Identificador / Detalle Institucional |
| :--- | :--- | :--- |
| **Institución Educativa** | `Colegio Glenn Doman (Entorno Demo)` | Código DANE Oficial: `311001088461` / `[IDENTIFICADOR INSTITUCIONAL DEMO]` |
| **Institución Secundaria** | `Institución Educativa Técnica Nacional` | Código DANE Oficial: `111001000001` (Aislamiento multi-tenant) |
| **Cuenta Rectoría** | Rectora Titular | `[CUENTA DEMO RECTORÍA]` / Rol: `rector` |
| **Cuenta Coordinación** | Coordinador Académico / Convivencia | `[CUENTA DEMO COORDINACIÓN]` / Rol: `coordinator` |
| **Cuenta Docente** | Docente Titular de Asignatura | `[CUENTA DEMO DOCENTE]` / Rol: `teacher` |
| **Cuenta Estudiante** | `[ESTUDIANTE DEMO]` (Ramiro) | `[CUENTA DEMO ESTUDIANTE]` / `[IDENTIFICADOR ESTUDIANTE DEMO]` |
| **Cuenta Acudiente** | `[ACUDIENTE DEMO]` (Alberto) | `[CUENTA DEMO ACUDIENTE]` / `[IDENTIFICADOR ACUDIENTE DEMO]` |
| **Grupo Académico Activo** | Grupo Escolar de Grado Activo | `[GRUPO ACADÉMICO DEMO]` |
| **Circular Existente** | Circular Oficial: Actividades Pedagógicas | `[CIRCULAR DEMO]` (`[QA-F15-20260907]`) |
| **Noticia Existente** | Logro Destacado en Feria de Ciencia | `[NOTICIA DEMO]` (`[QA-F15-20260907]`) |
| **Incidente Convivencia** | Registro Formativo Tipo I (Ley 1620) | `[INCIDENTE DEMO]` (`[QA-F15-20260907]`) |

---

## 2. Secuencia de Demostración Paso a Paso (23 Hitos)

---

### Hito 1: Autenticación y Entrada Segura (Login)
- **Rol:** Cualquier rol institucional (inicio con Rectoría).
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/login`.
- **Acción:** Ingresar credenciales institucionales de prueba y presionar "Iniciar Sesión".
- **Pantalla y Resultado Esperado:** Acceso inmediato con código HTTP 200. Se emite el token de acceso en memoria volátil de React y la cookie segura `pevn_refresh_token` (`HttpOnly`, `SameSite=Strict`). Redirección automática al `/dashboard`.
- **Qué Debe Observar el Evaluador:** Rapidez de carga, ausencia de parpadeo y verificación en DevTools de que el token JWT no se almacena en `localStorage`.
- **Por Qué Importa:** Demuestra controles de seguridad técnicamente verificados conforme a los lineamientos del Estado.
- **Fuente de Evidencia:** `backend/app/api/v1/endpoints/auth.py`, `frontend/src/context/AuthContext.tsx`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 2: Estructura Institucional y Catálogo DANE/DUE
- **Rol:** Rectoría.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** Barra superior $\rightarrow$ *Gestión Académica* (`/academic`).
- **Acción:** Visualizar las sedes (*campuses*) y la vinculación con el código DANE oficial de la institución (`311001088461`).
- **Pantalla y Resultado Esperado:** Tarjeta informativa del colegio de prueba con su dirección, código DANE de 12 dígitos, municipio y listado de sedes activas.
- **Qué Debe Observar el Evaluador:** Correspondencia exacta con la nomenclatura oficial del Directorio Único de Establecimientos Educativos.
- **Por Qué Importa:** Garantiza interoperabilidad con los censos del Ministerio de Educación Nacional.
- **Fuente de Evidencia:** `docs/phase-reports/PHASE_3C_OFFICIAL_DANE_INSTITUTION_RESOLUTION.md`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 3: Consola de Rectoría
- **Rol:** Rectoría.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.
- **Acción:** Inspeccionar los accesos directos de Rectoría: Años Lectivos, Sedes, Grados, Grupos, Docentes, Estudiantes, Acudientes, Matrículas y Políticas SIEE.
- **Pantalla y Resultado Esperado:** Tablero central con indicadores agregados del colegio y pestañas operativas restringidas al personal directivo.
- **Qué Debe Observar el Evaluador:** Gobierno completo del establecimiento educativo sin necesidad de intervención externa.
- **Por Qué Importa:** Consolida la autonomía institucional consagrada en la Ley 115 de 1994.
- **Fuente de Evidencia:** `frontend/src/pages/academic/AcademicHub.tsx`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 4: Consola de Coordinación
- **Rol:** Coordinación.
- **Cuenta de Demostración:** `[CUENTA DEMO COORDINACIÓN]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.
- **Acción:** Iniciar sesión como Coordinador y revisar permisos restringidos (ej. no puede revocar rectores ni crear colegios).
- **Pantalla y Resultado Esperado:** Vista operativa orientada a la supervisión de estudiantes, asignaciones docentes y convivencia escolar.
- **Qué Debe Observar el Evaluador:** Aplicación del principio de mínimo privilegio en los menús de navegación.
- **Por Qué Importa:** Mitiga riesgos de escalamiento de privilegios y separación de funciones directivas.
- **Fuente de Evidencia:** `docs/phase-reports/PHASE_10_ROLE_PERMISSION_MATRIX.md`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 5: Portal Docente y Dashboard
- **Rol:** Docente.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** Redirección automática a `/teacher` tras login.
- **Acción:** Inspeccionar el resumen de carga académica, grupos a cargo, tareas activas y accesos rápidos a asistencia y planeación.
- **Pantalla y Resultado Esperado:** Banner de bienvenida con especialidad docente, año lectivo activo y tarjetas informativas interactivas.
- **Qué Debe Observar el Evaluador:** Interfaz limpia, centrada en la labor pedagógica y libre de menús administrativos irrelevantes.
- **Por Qué Importa:** Disminuye la sobrecarga administrativa del magisterio.
- **Fuente de Evidencia:** `frontend/src/pages/teacher/TeacherDashboardView.tsx`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 6: Portal del Estudiante
- **Rol:** Estudiante.
- **Cuenta de Demostración:** `[CUENTA DEMO ESTUDIANTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** Redirección automática a `/student`.
- **Acción:** Mostrar el tablero del alumno con materias matriculadas, tareas pendientes, horario escolar y avisos institucionales.
- **Pantalla y Resultado Esperado:** Panel intuitivo adaptado para escolares con alertas visuales de tareas próximas a vencer.
- **Qué Debe Observar el Evaluador:** Autonomía formativa para el estudiante sin acceso a planillas docentes ni datos ajenos.
- **Por Qué Importa:** Fomenta la responsabilidad académica y la autogestión del aprendizaje.
- **Fuente de Evidencia:** `frontend/src/pages/student/`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 7: Portal del Acudiente y Selector de Hijos
- **Rol:** Acudiente.
- **Cuenta de Demostración:** `[CUENTA DEMO ACUDIENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** Redirección automática a `/guardian`.
- **Acción:** Inspeccionar la ficha del estudiante y demostrar el selector dinámico de acudidos.
- **Pantalla y Resultado Esperado:** Panel familiar con resumen de asistencia, tareas entregadas/pendientes y calificaciones del acudido.
- **Qué Debe Observar el Evaluador:** Si el acudiente tuviese más de un estudiante a cargo, puede alternar entre ellos con un solo clic.
- **Por Qué Importa:** Cumple el mandato de corresponsabilidad familiar en el proceso formativo.
- **Fuente de Evidencia:** `docs/reports/IDENTITY_FAMILY_LIFECYCLE_FINAL_AUDIT_REPORT.md`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 8: Matrícula y Validación de Cupos Máximos
- **Rol:** Rectoría.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ Pestaña *Matrículas* (`/academic/enrollments`).
- **Acción:** Consultar la matrícula activa de `[ESTUDIANTE DEMO]` en el grupo escolar de demostración.
- **Pantalla y Resultado Esperado:** Ficha de matrícula con estado `ACTIVE`, validación de campos compatibles con matrícula oficial y control de cupo ocupado en el salón.
- **Qué Debe Observar el Evaluador:** El sistema no permite sobrepasar la capacidad física registrada para el salón.
- **Por Qué Importa:** Control de calidad de la infraestructura educativa y auditoría de cobertura escolar.
- **Fuente de Evidencia:** `backend/app/models/enrollment.py`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 9: Asignación Académica Docente
- **Rol:** Rectoría o Coordinación.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ Pestaña *Asignaciones* (`/academic/assignments`).
- **Acción:** Mostrar la vinculación del Docente con la asignatura y el grupo de demostración con su intensidad horaria semanal.
- **Pantalla y Resultado Esperado:** Tabla de asignaciones donde se evidencia la terna: Docente + Materia + Salón.
- **Qué Debe Observar el Evaluador:** Cómo esta asignación es la base que habilita la visibilidad en el portal docente.
- **Por Qué Importa:** Soporte para la distribución de la planta docente según los marcos laborales del sector educativo.
- **Fuente de Evidencia:** `backend/app/models/academic_assignment.py`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 10: Grupos y Salones Escolares
- **Rol:** Rectoría.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ Pestaña *Grupos* (`/academic/groups`).
- **Acción:** Inspeccionar la configuración del grupo activo: grado, jornada escolar, sede y director de grupo.
- **Pantalla y Resultado Esperado:** Listado de grupos con desglose de cupos disponibles y ocupados.
- **Qué Debe Observar el Evaluador:** Flexibilidad para jornadas Mañana, Tarde, Completa o Nocturna.
- **Por Qué Importa:** Representación fiel de la estructura de salones en colegios colombianos.
- **Fuente de Evidencia:** `backend/app/models/group.py`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 11: Asignaturas y Áreas Fundamentales (Ley 115)
- **Rol:** Rectoría.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ Subsección de Plan de Estudios.
- **Acción:** Mostrar las asignaturas agrupadas por sus Áreas Obligatorias y Fundamentales de Conocimiento.
- **Pantalla y Resultado Esperado:** Estructura curricular con ponderaciones y estándares.
- **Qué Debe Observar el Evaluador:** Cumplimiento de los artículos 23 y 31 de la Ley General de Educación (Ley 115 de 1994).
- **Por Qué Importa:** Coherencia curricular requerida por las Secretarías de Educación.
- **Fuente de Evidencia:** `backend/app/models/subject.py`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 12: Creación y Edición de Actividades Académicas (Fase B3)
- **Rol:** Docente.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher` $\rightarrow$ Pestaña *Actividades* (`/teacher/activities`).
- **Acción:** Mostrar las actividades del grupo en estado `PUBLISHED` o `DRAFT`, filtros por estado y modal de edición.
- **Pantalla y Resultado Esperado:** Tabla reactiva con títulos, fechas de entrega en UTC, tipo de entrega (`FILE` / `TEXT`) y contador de entregas recibidas.
- **Qué Debe Observar el Evaluador:** Capacidad de guardar en borrador sin publicar anticipadamente a los alumnos.
- **Por Qué Importa:** Flexibilidad pedagógica para el docente antes de asignar tareas.
- **Fuente de Evidencia:** `docs/reports/B3_IMPLEMENTATION_REPORT.md`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 13: Entrega de Tareas por el Estudiante (Submissions)
- **Rol:** Estudiante.
- **Cuenta de Demostración:** `[CUENTA DEMO ESTUDIANTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/student` $\rightarrow$ Pestaña *Tareas y Entregas*.
- **Acción:** Abrir una actividad asignada, mostrar el modal de entrega, visualización de tardanza UTC y subida de archivos seguros (máx. 10 MB, Magic Bytes).
- **Pantalla y Resultado Esperado:** Modal adaptativo según modalidad, botón de entrega formal y confirmación en pantalla.
- **Qué Debe Observar el Evaluador:** Rechazo automático de ejecutables maliciosos y registro de fecha exacta de entrega.
- **Por Qué Importa:** Canal seguro de entrega institucional para los trabajos escolares.
- **Fuente de Evidencia:** `docs/reports/B3-H13_IMPLEMENTATION_REPORT.md`.
- **Tiempo Estimado:** 2 minutos.

---

### Hito 14: Calificación y Devolución Docente
- **Rol:** Docente.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher/activities` $\rightarrow$ Botón `📥 Entregas`.
- **Acción:** Abrir el modal de entregas recibidas, inspeccionar la evidencia del estudiante y demostrar la devolución formativa (`RETURNED`) con observaciones.
- **Pantalla y Resultado Esperado:** Detalle de intentos de entrega, visualizador de texto y formulario de retroalimentación pedagógica.
- **Qué Debe Observar el Evaluador:** Evaluación formativa real: la devolución permite al alumno corregir su trabajo antes de la nota final.
- **Por Qué Importa:** Alineación con las directrices de evaluación formativa del sector oficial.
- **Fuente de Evidencia:** `backend/tests/test_student_submissions_api.py`.
- **Tiempo Estimado:** 2 minutos.

---

### Hito 15: Planilla de Asistencia Diaria
- **Rol:** Docente.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher` $\rightarrow$ Pestaña *Asistencia* (`/teacher/attendance`).
- **Acción:** Seleccionar grupo, fecha y registrar asistencia en bloque (`Presente`, `Ausente`, `Justificado`, `Retardo`) con persistencia confirmada.
- **Pantalla y Resultado Esperado:** Matriz de estudiantes con botones de marcado rápido y cálculo de inasistencias acumuladas.
- **Qué Debe Observar el Evaluador:** Agilidad en el registro de asistencia.
- **Por Qué Importa:** Control de permanencia escolar y soporte para el requisito de asistencia del SIEE.
- **Fuente de Evidencia:** `backend/app/models/academic_activity.py` (`DailyAttendance`).
- **Tiempo Estimado:** 1 minuto.

---

### Hito 16: Planilla SIEE y Consolidación Híbrida (Decreto 1290 de 2009)
- **Rol:** Docente.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher` $\rightarrow$ Pestaña *Calificaciones SIEE* (`/teacher/siee-evaluation`).
- **Acción:** Mostrar la planilla del período: Promedio calculado automático (`calculated_score`), ajuste docente (`final_score`) y justificación obligatoria (`adjustment_reason`) al diferir.
- **Pantalla y Resultado Esperado:** Planilla con mapeo automático a la escala nacional (*Bajo, Básico, Alto, Superior*) y semáforo visual.
- **Qué Debe Observar el Evaluador:** Si el docente cambia la nota calculada, el sistema bloquea el guardado hasta que ingrese una justificación pedagógica válida.
- **Por Qué Importa:** Transparencia y trazabilidad en la asignación de calificaciones.
- **Fuente de Evidencia:** `docs/phase16b_domain_services_report.md`.
- **Tiempo Estimado:** 2.5 minutos.

---

### Hito 17: Boletines Oficiales de Calificaciones
- **Rol:** Rectoría o Acudiente.
- **Cuenta de Demostración:** `[CUENTA DEMO RECTORÍA]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ Pestaña *Evaluaciones SIEE* $\rightarrow$ *Boletín Oficial*.
- **Acción:** Renderizar el boletín de calificaciones periódico y acumulativo del estudiante de demostración.
- **Pantalla y Resultado Esperado:** Boletín institucional estructurado por áreas, asignaturas, fallas acumuladas, juicio valorativo nacional y puesto en el grupo.
- **Qué Debe Observar el Evaluador:** Formato oficial limpio, preparado para consulta web y conforme a los lineamientos del Decreto 1290 de 2009.
- **Por Qué Importa:** Instrumento formal de comunicación del rendimiento escolar a las familias.
- **Fuente de Evidencia:** `frontend/src/test/OfficialReportCard.test.tsx`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 18: Observador del Estudiante y Convivencia Escolar (Ley 1620 de 2013)
- **Rol:** Rectoría y Acudiente.
- **Cuenta de Demostración:** `[CUENTA DEMO ACUDIENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ Pestaña *Observador*.
- **Acción:** Inspeccionar el registro de demostración tipificado como **Tipo I**.
- **Pantalla y Resultado Esperado:** Visualización de la descripción formativa, descargos del alumno, compromisos restaurativos suscritos y seguimiento tutorial.
- **Qué Debe Observar el Evaluador:** Rigor en el respeto al debido proceso disciplinario escolar.
- **Por Qué Importa:** Trazabilidad documental frente a requerimientos de autoridades competentes.
- **Fuente de Evidencia:** `docs/reports/PHASE_15_FORENSIC_FUNCTIONAL_AUDIT_REPORT.md`.
- **Tiempo Estimado:** 2 minutos.

---

### Hito 19: Comunicaciones Institucionales y Circulares
- **Rol:** Estudiante o Acudiente.
- **Cuenta de Demostración:** `[CUENTA DEMO ACUDIENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ Pestaña *Circulares*.
- **Acción:** Visualizar la circular oficial de demostración (`[CIRCULAR DEMO]`).
- **Pantalla y Resultado Esperado:** Comunicado oficial emitido por la Rectoría con insignia institucional y contenido formal.
- **Qué Debe Observar el Evaluador:** Notificación formal trazable sin riesgo de dispersión.
- **Por Qué Importa:** Comunicación oficial transparente entre la escuela y la familia.
- **Fuente de Evidencia:** `backend/app/models/communication.py`.
- **Tiempo Estimado:** 1 minuto.

---

### Hito 20: Firma de Acuse de Recibo Electrónico
- **Rol:** Acudiente.
- **Cuenta de Demostración:** `[CUENTA DEMO ACUDIENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ Detalle de la circular.
- **Acción:** Pulsar el botón **"Confirmar Lectura / Firmar Acuse de Recibo"**.
- **Pantalla y Resultado Esperado:** El botón se inhabilita y se estampa la confirmación: *"Acuse de recibo confirmado el [Fecha UTC] por [ACUDIENTE DEMO]"*.
- **Qué Debe Observar el Evaluador:** Se registra en la base de datos la estampa de tiempo UTC, identificador de usuario y dirección IP del firmante.
- **Por Qué Importa:** Evidencia fehaciente de enteramiento de directrices escolares.
- **Fuente de Evidencia:** `backend/app/models/communication.py` (`CommunicationReceipt`).
- **Tiempo Estimado:** 1 minuto.

---

### Hito 21: Aulas Virtuales Sincrónicas (Integración BigBlueButton)
- **Rol:** Docente y Estudiante.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/virtual-classrooms`.
- **Acción:** Mostrar la sala de clase del grupo, lanzamiento (`launch`), validación de matrícula y generación de URL firmada mediante el Mock Provider verificado.
- **Pantalla y Resultado Esperado:** Apertura controlada de la sesión con rol Moderador para docente y Asistente para estudiante, con telemetría de conexión.
- **Qué Debe Observar el Evaluador:** **Claridad técnica:** La capa de integración de software se encuentra implementada y verificada mediante un proveedor simulado (*mock*); se declara con total transparencia que la operación en vivo requerirá comisionar servidores físicos dedicados BigBlueButton y el servidor de relay Coturn (STUN/TURN en TCP 443) provistos por la entidad pública.
- **Por Qué Importa:** Capacidad de clases híbridas o remotas ante contingencias de fuerza mayor.
- **Fuente de Evidencia:** `docs/reports/PEVN_VIRTUAL_CLASSROOM_READINESS.md`.
- **Tiempo Estimado:** 2 minutos.

---

### Hito 22: Auditoría Técnica y Censura de Secretos
- **Rol:** Auditor Técnico / SuperAdmin.
- **Cuenta de Demostración:** Inspección técnica de la tabla `audit_logs`.
- **Ruta de Navegación:** Vista técnica de auditoría.
- **Acción:** Consultar los registros de auditoría generados durante la sesión anterior.
- **Pantalla y Resultado Esperado:** Filas inmutables con `event_type`, `actor_id`, `correlation_id` y metadatos JSON con claves sensibles censuradas como `"[REDACTED]"`.
- **Qué Debe Observar el Evaluador:** Trazabilidad de operaciones sin riesgo de exposición de secretos ni contraseñas.
- **Por Qué Importa:** Requisito indispensable para órganos de control y comités de seguridad de la información.
- **Fuente de Evidencia:** `backend/app/audit/database_service.py`.
- **Tiempo Estimado:** 1.5 minutos.

---

### Hito 23: Aislamiento Multi-Tenant y Barrera Anti-IDOR
- **Rol:** Docente o Estudiante del colegio de demostración.
- **Cuenta de Demostración:** `[CUENTA DEMO DOCENTE]` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** Solicitud HTTP de prueba o navegación.
- **Acción:** Intentar consultar un recurso perteneciente a otra institución (ej. `Institución Educativa Técnica Nacional`, DANE `111001000001`).
- **Pantalla y Resultado Esperado:** El sistema responde **`404 Not Found` (Blind 404)**, imposibilitando confirmar si el identificador existe en otro colegio.
- **Qué Debe Observar el Evaluador:** La aplicación no responde 403 (que confirmaría la existencia del registro en otra institución), sino 404 ciego.
- **Por Qué Importa:** Protección estricta del aislamiento de los datos entre diferentes municipios y colegios.
- **Fuente de Evidencia:** `backend/tests/test_teacher_academic_scope.py`.
- **Tiempo Estimado:** 1.5 minutos.

---

## 3. Resumen de Tiempos del Runbook

- **Recorrido Completo (23 Hitos):** ~32 a 38 minutos.
- **Recorrido Sintético (Hitos Clave 1, 3, 5, 6, 7, 12, 13, 16, 17, 18, 20):** ~15 a 18 minutos.
- **Recorrido Técnico Especializado (Hitos 1, 8, 16, 21, 22, 23):** ~12 a 15 minutos.
