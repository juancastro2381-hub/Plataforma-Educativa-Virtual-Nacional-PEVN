# PEVN — Manifiesto Oficial de Capturas de Pantalla Auténticas (Screenshot Manifest)

**Plataforma Educativa Virtual Nacional (PEVN)**  
**Directorio Base:** `docs/manual/assets/screenshots/`  
**Fecha de Validación y Saneamiento:** 14 de Octubre de 2026  
**Auditoría y Trazabilidad:** DOC-04 — Verificación Forense y Reconciliación de Evidencia  
**Política de Capturas Reales:** Todas las imágenes contenidas en este catálogo corresponden a ejecuciones directas de la interfaz web de PEVN, normalizadas sin barras de navegador, extensiones ni paneles de inspección, y procesadas a nivel de píxel para garantizar datos 100% sintéticos (cero PII de menores ni docentes reales).

---

## 1. Resumen Ejecutivo del Inventario Visual

| Métrica del Inventario | Valor Auditado | Observación Técnica |
|---|---|---|
| **Total de Capturas en Disco** | 13 archivos PNG | Todas legibles, formato PNG, dimensiones entre 695×488 y 1920×912 px. |
| **Integradas en Guía Institucional HTML** | 13 de 13 (100%) | `docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`. Reconciliado en DOC-04 (Figuras 1.1 a 9.3). |
| **Integradas en Manual Operativo HTML** | 13 de 13 (100%) | `docs/manual/index.html`. Embebidas en las secciones operativas por rol. |
| **Integradas en PDF Guía Institucional** | 13 de 13 (100%) | `docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE.pdf` (9 páginas A4). |
| **Integradas en PDF Manual Interactivo** | 13 de 13 (100%) | `docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf` (9 páginas A4). |
| **Estado de Datos Personales (PII)** | Cero PII Real (100% Sintético) | Verificado en auditorías DOC-02-R1 y DOC-04. Nombres, correos, documentos y notas ficticios. |
| **Fabricación / Mockups Falsos** | 0% (Ninguna fabricada) | Capturadas del runtime real de React/Vite en navegador Chromium. |

---

## 2. Ficha Técnica Detallada por Captura de Pantalla

---

### Captura 01: Portal Institucional de Inicio y Bienvenida
- **Archivo:** `docs/manual/assets/screenshots/01_portal_inicio.png`
- **Dimensiones y Tamaño:** 1024 × 490 píxeles · 86.8 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Público general / Visitante / Ciudadano
- **Ruta de la Interfaz:** `/` (Home institucional)
- **Funcionalidad y Paso de Flujo:** Presentación pública de la Plataforma Educativa Virtual Nacional, acceso unificado a los módulos de autenticación, visualización de principios rectores y oferta institucional.
- **Autenticidad de la Captura:** Captura real del runtime frontend (`src/pages/LandingPage.tsx`).
- **Contexto Temporal / Versión:** Baseline DOC-01 normalizada en DOC-02-R1 / DOC-04.
- **Confirmación de Datos Sintéticos:** Sin datos sensibles; utiliza logotipos institucionales y textos explicativos públicos de la República de Colombia.
- **Referencias en Guía Institucional HTML:** Figura 1.1 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Bienvenida (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.1, Pág. 3).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 1.1, Pág. 2).
- **Resultado de Validación Visual:** Aprobado. Contraste óptimo, tipografía clara, libre de elementos de depuración.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 02: Pantalla de Autenticación Centralizada y Login
- **Archivo:** `docs/manual/assets/screenshots/02_autenticacion_login.png`
- **Dimensiones y Tamaño:** 1920 × 912 píxeles · 81.5 KB · Formato PNG (RGB)
- **Rol de Usuario:** Todos los roles canónicos (`superadmin`, `national_admin`, `department_admin`, `municipality_admin`, `rector`, `coordinator`, `teacher`, `student`, `guardian`)
- **Ruta de la Interfaz:** `/login`
- **Funcionalidad y Paso de Flujo:** Formulario oficial de inicio de sesión con validación de credenciales, protección contra fuerza bruta y enlaces seguros de recuperación.
- **Autenticidad de la Captura:** Captura real del componente `src/pages/Login.tsx`.
- **Contexto Temporal / Versión:** Baseline DOC-01 verificado en DOC-02-R1 / DOC-04.
- **Confirmación de Datos Sintéticos:** Formulario con campos en blanco y texto demostrativo seguro (`[REDACTED DEVELOPMENT CREDENTIAL]` neutralizado).
- **Referencias en Guía Institucional HTML:** Figura 1.2 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Autenticación (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.2, Pág. 3).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 1.2, Pág. 2).
- **Resultado de Validación Visual:** Aprobado. Resolución alta, nitidez perfecta en campos y botones de acción.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 03: Centro de Operaciones Técnicas y Diagnóstico de Inquilinos
- **Archivo:** `docs/manual/assets/screenshots/03_operaciones_diagnostico_inquilino.png`
- **Dimensiones y Tamaño:** 1024 × 491 píxeles · 77.8 KB · Formato PNG (RGBA)
- **Rol de Usuario:** SuperAdmin (`superadmin`, Nivel 100)
- **Ruta de la Interfaz:** `/operations/diagnostics`
- **Funcionalidad y Paso de Flujo:** Consola de soporte técnico para auditoría de latencia de base de datos, estado relacional de inquilinos y verificación de la tabla inmutable `audit_logs`.
- **Autenticidad de la Captura:** Captura real del módulo `src/pages/admin/TenantDiagnosticsView.tsx`.
- **Contexto Temporal / Versión:** Validada en auditoría SA-02 y DOC-03.
- **Confirmación de Datos Sintéticos:** Los inquilinos auditados corresponden a identificadores sintéticos de demostración (`tenant-demo-01`, `tenant-demo-02`) con métricas simuladas.
- **Referencias en Guía Institucional HTML:** Figura 2.4 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo SuperAdmin (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.4, Pág. 4).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 5.1, Pág. 8).
- **Resultado de Validación Visual:** Aprobado. Tablas legibles, tarjetas de telemetría claras, sin fugas de secretos.
- **Limitaciones Pendientes:** El monitoreo en vivo de la base PostgreSQL requiere que el contenedor local en puerto 5433 esté levantado; en ausencia del servicio, el backend aplica *fail-closed*.

---

### Captura 04: Administración Territorial e Invitación de Rectores
- **Archivo:** `docs/manual/assets/screenshots/04_administracion_municipal_invitacion.png`
- **Dimensiones y Tamaño:** 1024 × 488 píxeles · 113.0 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Administrador Territorial / Municipal (`municipality_admin`, Nivel 70) o Departamental (`department_admin`, Nivel 80)
- **Ruta de la Interfaz:** `/admin/institutions/invite`
- **Funcionalidad y Paso de Flujo:** Despacho de invitaciones oficiales y trazabilidad de tokens criptográficos con expiración para el nombramiento de Rectores de instituciones educativas de la jurisdicción.
- **Autenticidad de la Captura:** Captura real del componente `src/pages/admin/InstitutionsView.tsx` y diálogo de invitación.
- **Contexto Temporal / Versión:** Implementada en NTA-09 y NTA-10; saneada en DOC-02-R1.
- **Confirmación de Datos Sintéticos:** Nombres de instituciones oficiales catalogadas del DUE (`Colegio Departamental San José`) y correos ficticios (`rectoria.sanjose@pevn.gov.co`). Cero PII real.
- **Referencias en Guía Institucional HTML:** Figura 2.1 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Administración Territorial (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.3, Pág. 4).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 2.1, Pág. 3).
- **Resultado de Validación Visual:** Aprobado. Campos de formulario nítidos, botones de envío y tabla de trazabilidad perfectamente legibles.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 05: Tablero Principal de Rectoría
- **Archivo:** `docs/manual/assets/screenshots/05_rectoria_dashboard.png`
- **Dimensiones y Tamaño:** 1024 × 487 píxeles · 77.7 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Rector / Director Rural (`rector`, Nivel 60)
- **Ruta de la Interfaz:** `/rector-dashboard`
- **Funcionalidad y Paso de Flujo:** Panel de control de gobierno escolar institucional: resumen de matrícula, sedes activas, docentes vinculados y accesos directos al SIEE y gestión de períodos.
- **Autenticidad de la Captura:** Captura real de `src/pages/rector/RectorDashboard.tsx`.
- **Contexto Temporal / Versión:** Baseline NTA-10-R4, normalizada en DOC-02-R1.
- **Confirmación de Datos Sintéticos:** Institución sintética "IED San José", cifras agregadas de demostración (320 estudiantes, 14 docentes, 2 sedes).
- **Referencias en Guía Institucional HTML:** Figura 2.5 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Rectoría (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.5, Pág. 5).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 3.1, Pág. 4).
- **Resultado de Validación Visual:** Aprobado. Métricas numéricas legibles, tarjetas de resumen bien distribuidas.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 06: Configuración del Calendario y Períodos Académicos SIEE
- **Archivo:** `docs/manual/assets/screenshots/06_gestion_academica_periodos.png`
- **Dimensiones y Tamaño:** 1024 × 512 píxeles · 73.7 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Rector (`rector`) / Coordinador Académico (`coordinator`, Nivel 50)
- **Ruta de la Interfaz:** `/academic/periods`
- **Funcionalidad y Paso de Flujo:** Definición del año lectivo institucional, apertura y cierre de períodos académicos (I, II, III, IV) y asignación de ponderaciones porcentuales bajo el Decreto 1290 de 2009 (suma exacta 100%).
- **Autenticidad de la Captura:** Captura real de `src/pages/academic/AcademicPeriodsView.tsx`.
- **Contexto Temporal / Versión:** Verificada en NTA-10-R7.
- **Confirmación de Datos Sintéticos:** Fechas demostrativas del año 2026, porcentajes canónicos (25%, 25%, 25%, 25%).
- **Referencias en Guía Institucional HTML:** Figura 2.6 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Coordinación Académica (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.6, Pág. 5).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 3.2, Pág. 4).
- **Resultado de Validación Visual:** Aprobado. Grilla de períodos clara, botones de estado activo/cerrado funcionales.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 07: Padrón de Estudiantes Matriculados (Contexto SIMAT)
- **Archivo:** `docs/manual/assets/screenshots/07_gestion_academica_estudiantes_simat.png`
- **Dimensiones y Tamaño:** 1024 × 490 píxeles · 79.8 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Rector / Coordinador Académico
- **Ruta de la Interfaz:** `/academic/enrollments`
- **Funcionalidad y Paso de Flujo:** Consulta de estudiantes matriculados en grados y sedes, verificación del código identificador demostrativo SIMAT y estado lectivo activo.
- **Autenticidad de la Captura:** Captura real de `src/pages/academic/EnrollmentsView.tsx`.
- **Contexto Temporal / Versión:** Sanitizada en DOC-02-R1 (erradicación completa de nombres y tarjetas de identidad reales de menores).
- **Confirmación de Datos Sintéticos:** Nombres sintéticos validados: "Camilo Andrés Torres", "Valentina Ríos Gómez", documentos ficticios (TI 1.098.765.432).
- **Referencias en Guía Institucional HTML:** Figura 2.7 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Matrícula (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.7, Pág. 6).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 3.3, Pág. 5).
- **Resultado de Validación Visual:** Aprobado. Tabla limpia, columnas de grado y grupo perfectamente alineadas.
- **Limitaciones Pendientes:** El sistema PEVN no se conecta en vivo al servidor central del SIMAT; los datos mostrados son de ingesta demostrativa local.

---

### Captura 08: Vinculación Legal de Acudientes y Tutores
- **Archivo:** `docs/manual/assets/screenshots/08_gestion_academica_acudientes.png`
- **Dimensiones y Tamaño:** 1024 × 493 píxeles · 45.8 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Coordinador Académico / Rector
- **Ruta de la Interfaz:** `/academic/guardians`
- **Funcionalidad y Paso de Flujo:** Registro formal de padres de familia y acudientes autorizados, vinculación al estudiante por documento legal y definición de teléfono de contacto institucional.
- **Autenticidad de la Captura:** Captura real de `src/pages/academic/GuardiansView.tsx`.
- **Contexto Temporal / Versión:** Sanitizada en DOC-02-R1.
- **Confirmación de Datos Sintéticos:** Nombres y cédulas ficticias: "Esperanza Gómez Valencia" (CC 52.345.678), parentesco "Madre", teléfono ficticio `310 987 6543`. Cero datos de contacto reales.
- **Referencias en Guía Institucional HTML:** Figura 2.8 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Acudientes (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.8, Pág. 6).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 3.4, Pág. 5).
- **Resultado de Validación Visual:** Aprobado. Tipografía nítida, badges de parentesco claros.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 09: Portal y Tablero Principal del Docente
- **Archivo:** `docs/manual/assets/screenshots/09_portal_docente_dashboard.png`
- **Dimensiones y Tamaño:** 1024 × 492 píxeles · 83.6 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Docente de Aula (`teacher`, Nivel 40)
- **Ruta de la Interfaz:** `/teacher-portal`
- **Funcionalidad y Paso de Flujo:** Vista principal del profesor con listado de asignaturas y grupos asignados, indicadores de tareas por calificar y accesos directos al planeador y planilla SIEE.
- **Autenticidad de la Captura:** Captura real de `src/pages/teacher/TeacherDashboard.tsx`.
- **Contexto Temporal / Versión:** DOC-02 (mejora de contraste tipográfico y legibilidad de tarjetas de asignaturas).
- **Confirmación de Datos Sintéticos:** Docente ficticio "Prof. Carlos Mendoza", asignaturas demostrativas (Ciencias Naturales 8-A, Biología 9-B).
- **Referencias en Guía Institucional HTML:** Figura 2.9 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo del Docente (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.9, Pág. 7).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 4.1, Pág. 6).
- **Resultado de Validación Visual:** Aprobado. Contraste accesible WCAG AAA, textos oscuros sobre fondo claro sin aberraciones.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 10: Planeación Curricular del Docente
- **Archivo:** `docs/manual/assets/screenshots/10_portal_docente_planeacion.png`
- **Dimensiones y Tamaño:** 750 × 497 píxeles · 71.8 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Docente de Aula (`teacher`)
- **Ruta de la Interfaz:** `/teacher/planning`
- **Funcionalidad y Paso de Flujo:** Formulación y publicación de unidades temáticas, definición de competencias, derechos básicos de aprendizaje (DBA) y creación de actividades evaluativas.
- **Autenticidad de la Captura:** Captura real de `src/pages/teacher/CurricularPlanningView.tsx`.
- **Contexto Temporal / Versión:** DOC-02 / DOC-03.
- **Confirmación de Datos Sintéticos:** Contenido curricular demostrativo: "Unidad 1: Genética y Herencia Mendeliana", cronograma ficticio del primer período.
- **Referencias en Guía Institucional HTML:** Figura 2.10 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo Curricular (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.10, Pág. 7).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 4.2, Pág. 6).
- **Resultado de Validación Visual:** Aprobado. Interfaz compacta, botones de acción nítidos.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 11: Muro de Comunicados Oficiales del Estudiante
- **Archivo:** `docs/manual/assets/screenshots/11_portal_estudiante_comunicados.png`
- **Dimensiones y Tamaño:** 700 × 488 píxeles · 58.9 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Estudiante (`student`, Nivel 10) / Acudiente (`guardian`)
- **Ruta de la Interfaz:** `/student-portal/communications`
- **Funcionalidad y Paso de Flujo:** Consulta de circulares rectorales, notificaciones institucionales y citaciones a padres de familia con registro automático de acuse de lectura.
- **Autenticidad de la Captura:** Captura real de `src/pages/student/CommunicationsView.tsx`.
- **Contexto Temporal / Versión:** Normalizada en DOC-02 y verificada en DOC-03.
- **Confirmación de Datos Sintéticos:** Circulares ficticias de rectoría ("Circular 012: Convivencia y Jornada Lúdica"), fechas simuladas.
- **Referencias en Guía Institucional HTML:** Figura 2.11 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo Estudiantil (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.11, Pág. 8).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 4.3, Pág. 7).
- **Resultado de Validación Visual:** Aprobado. Muro de lectura claro con distinción cromática por categoría de aviso.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 12: Cartelera Escolar y Periódico Digital Institucional
- **Archivo:** `docs/manual/assets/screenshots/12_portal_estudiante_noticias.png`
- **Dimensiones y Tamaño:** 695 × 491 píxeles · 54.4 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Estudiante (`student`) / Comunidad Educativa
- **Ruta de la Interfaz:** `/student-portal/news`
- **Funcionalidad y Paso de Flujo:** Consulta de artículos culturales, noticias científicas del plantel, convocatorias a eventos deportivos y proyectos de aula.
- **Autenticidad de la Captura:** Captura real de `src/pages/student/SchoolNewsView.tsx`.
- **Contexto Temporal / Versión:** DOC-02 / DOC-03.
- **Confirmación de Datos Sintéticos:** Titulares demostrativos ("Semana de la Ciencia Escolar 2026: Energías Renovables"), imágenes sin menores identificables.
- **Referencias en Guía Institucional HTML:** Figura 2.12 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Noticias (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.12, Pág. 8).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 4.4, Pág. 7).
- **Resultado de Validación Visual:** Aprobado. Formato tipo blog escolar dinámico y legible.
- **Limitaciones Pendientes:** Ninguna.

---

### Captura 13: Modal de Entrega de Tareas y Retroalimentación
- **Archivo:** `docs/manual/assets/screenshots/13_portal_estudiante_entrega_tarea.png`
- **Dimensiones y Tamaño:** 735 × 507 píxeles · 56.1 KB · Formato PNG (RGBA)
- **Rol de Usuario:** Estudiante (`student`)
- **Ruta de la Interfaz:** `/student-portal/assignments/:id`
- **Funcionalidad y Paso de Flujo:** Ventana modal para subir archivos de tareas, redactar comentarios al docente, consultar fecha límite de recepción y revisar observaciones del profesor al devolver el trabajo.
- **Autenticidad de la Captura:** Captura real de `src/components/student/TaskSubmissionModal.tsx`.
- **Contexto Temporal / Versión:** Verificada en auditoría funcional B3-H12 / B3-H13 y DOC-03.
- **Confirmación de Datos Sintéticos:** Tarea demostrativa ("Taller 1: Ecosistemas Colombianos"), fecha de entrega ficticia y archivo de prueba `taller_ecosistemas.pdf`. Cero datos de autoría reales.
- **Referencias en Guía Institucional HTML:** Figura 2.13 (`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`).
- **Referencias en Manual Operativo HTML:** Módulo de Entrega de Tareas (`docs/manual/index.html`).
- **Inclusión en Documentos PDF:**
  - `PEVN_INSTITUTIONAL_USER_GUIDE.pdf`: Incluido (Figura 2.13, Pág. 8).
  - `PEVN_INTERACTIVE_USER_MANUAL.pdf`: Incluido (Figura 4.5, Pág. 7).
- **Resultado de Validación Visual:** Aprobado. Estado de entrega (Entregado / Calificado), área de subida y comentarios nítidos.
- **Limitaciones Pendientes:** Ninguna.

---

## 3. Matriz de Coherencia de Documentación Visual

| # | Archivo PNG | Guía Institucional HTML | Manual Interactivo HTML | PDF Guía Institucional | PDF Manual Interactivo | Validación Forense |
|---|---|---|---|---|---|---|
| **01** | `01_portal_inicio.png` | Figura 1.1 | Módulo Inicio | Figura 2.1 | Figura 1.1 | Auténtica · Sintética · Legible |
| **02** | `02_autenticacion_login.png` | Figura 1.2 | Módulo Login | Figura 2.2 | Figura 1.2 | Auténtica · Sintética · Legible |
| **03** | `03_operaciones_diagnostico_inquilino.png` | Figura 2.4 | Módulo SuperAdmin | Figura 2.4 | Figura 5.1 | Auténtica · Sintética · Legible |
| **04** | `04_administracion_municipal_invitacion.png` | Figura 2.1 | Módulo Territorial | Figura 2.3 | Figura 2.1 | Auténtica · Sintética · Legible |
| **05** | `05_rectoria_dashboard.png` | Figura 2.5 | Módulo Rectoría | Figura 2.5 | Figura 3.1 | Auténtica · Sintética · Legible |
| **06** | `06_gestion_academica_periodos.png` | Figura 2.6 | Módulo Períodos | Figura 2.6 | Figura 3.2 | Auténtica · Sintética · Legible |
| **07** | `07_gestion_academica_estudiantes_simat.png` | Figura 2.7 | Módulo Matrícula | Figura 2.7 | Figura 3.3 | Auténtica · Sintética · Legible |
| **08** | `08_gestion_academica_acudientes.png` | Figura 2.8 | Módulo Acudientes | Figura 2.8 | Figura 3.4 | Auténtica · Sintética · Legible |
| **09** | `09_portal_docente_dashboard.png` | Figura 2.9 | Módulo Docente | Figura 2.9 | Figura 4.1 | Auténtica · Sintética · Legible |
| **10** | `10_portal_docente_planeacion.png` | Figura 2.10 | Módulo Planeación | Figura 2.10 | Figura 4.2 | Auténtica · Sintética · Legible |
| **11** | `11_portal_estudiante_comunicados.png` | Figura 2.11 | Módulo Comunicados | Figura 2.11 | Figura 4.3 | Auténtica · Sintética · Legible |
| **12** | `12_portal_estudiante_noticias.png` | Figura 2.12 | Módulo Noticias | Figura 2.12 | Figura 4.4 | Auténtica · Sintética · Legible |
| **13** | `13_portal_estudiante_entrega_tarea.png` | Figura 2.13 | Módulo Tareas | Figura 2.13 | Figura 4.5 | Auténtica · Sintética · Legible |

**Conclusión del Manifiesto:**  
Queda formalmente reconciliada la discrepancia previa (13 en disco frente a 11 en HTML y 10 en PDF). Todas las capturas se encuentran al 100% integradas, documentadas y verificadas visualmente en los 4 artefactos de consulta de la plataforma PEVN.
