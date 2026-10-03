# PEVN — Landing Page Current-State Forensic Audit
## RECONCILIACIÓN FORENSE DE ESTADO PÚBLICO VS. LÍNEA BASE CERTIFICADA
### AUDITORÍA DE SÓLO LECTURA — SIN MODIFICACIÓN DE CÓDIGO PRODUCTIVO

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Documento:** Auditoría Forense de la Página de Inicio / Landing Pública (`/`)  
**Fecha:** 3 de Octubre de 2026  
**Carácter:** Read-Only Audit Evidence  
**Marco de Gobernanza:** AI Software Factory v1.2 — Transparent Public Truth Baseline  
**Veredicto Formal de Gate:** **CONDITIONAL PASS** (Aprobado con Requerimiento de Correcciones Editoriales Documentadas)

---

## 1. Audit Scope

La presente auditoría forense examinó de manera exhaustiva y de estricta **sólo lectura** la totalidad de elementos visibles, textos, afirmaciones técnicas, indicadores de estado, tarjetas de características y componentes del roadmap presentes en la página pública de inicio (Landing Page / Home) de la **Plataforma Educativa Virtual Nacional (PEVN)** accesible en la ruta raíz (`/`).

### Objetivos Específicos:
1. Contrastar cada afirmación de la página pública frente a la documentación autoritativa congelada del proyecto (Fases 1 a 16, B1–B3, H2/H13, matrices de capacidades y dossiers gubernamentales).
2. Determinar la exactitud fáctica de los estados de fase ("COMPLETADA" vs. "PENDIENTE").
3. Identificar contradicciones directas entre los mensajes de la interfaz pública y las capacidades reales implementadas y certificadas.
4. Establecer la línea base documental para una futura intervención correctiva controlada, sin modificar código en esta fase.

---

## 2. Landing Page Source Map

La página de inicio pública se encuentra implementada en los siguientes archivos y símbolos dentro del repositorio:

| Propiedad | Definición Técnica en el Repositorio |
| :--- | :--- |
| **Ruta URL Pública** | `/` (Ruta raíz / Index Route) |
| **Componente Principal de Vista** | [`ComingSoon`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/ComingSoon.tsx) (`export function ComingSoon()`) |
| **Archivo Fuente del Componente** | `frontend/src/pages/ComingSoon.tsx` (276 líneas) |
| **Shell / Layout Contenedor** | [`RootLayout`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/layouts/RootLayout.tsx) (`export function RootLayout()`) |
| **Archivo Fuente del Layout** | `frontend/src/layouts/RootLayout.tsx` (274 líneas) |
| **Definición de Rutas** | [`App.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/App.tsx) (Líneas 50–59: `createBrowserRouter` mapeando `/` a `RootLayout` con `ComingSoon` como `index`) |
| **Configuración de Entorno** | [`frontend/src/config/index.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/config/index.ts) (`config.appName`, `config.version`) |
| **Constantes de Datos en Vista** | `FEATURES: Feature[]` (Líneas 232–250 en `ComingSoon.tsx`)<br>`PHASES: PhaseItem[]` (Líneas 252–273 en `ComingSoon.tsx`) |
| **Iconografía Local** | `ShieldIcon`, `UsersIcon`, `DeviceIcon` (SVG locales en `ComingSoon.tsx`) |

### Hallazgo Estructural Crítico:
- **Contenido 100% Cableado (*Hardcoded*):** Toda la información del roadmap (`PHASES`), las características (`FEATURES`), la píldora de estado ("Fase 1 y Fase 2 — Completadas y Aprobadas") y el banner de estado ("Infraestructura base completada...") están **estáticamente codificados en el archivo JSX** `frontend/src/pages/ComingSoon.tsx`.
- **Cero Fuentes Dinámicas:** No existe consumo de API ni archivo de configuración central que sincronice el roadmap con el estado real del backend o de la base de datos.
- **Inexistencia de Duplicados:** No existen otros componentes compitiendo por la ruta `/`; `ComingSoon.tsx` es la única fuente activa.

---

## 3. Current Landing Page Claims

Evaluación forense de cada afirmación y elemento textual visible en la página pública:

| Ubicación | Reclamación Actual en UI | Clasificación | Evidencia Autoritativa | Notas Técnicas y Forenses |
| :--- | :--- | :---: | :--- | :--- |
| **Header (Barra de Bandera)** | Tricolor colombiano (Amarillo 50%, Azul 25%, Rojo 25%) | **ACCURATE** | `RootLayout.tsx` L21-25 | Identidad institucional del Estado colombiano, neutral y sin proselitismo político. |
| **Header (Logo & Marca)** | `PEVN` \| `Plataforma Educativa Virtual Nacional` | **ACCURATE** | `RootLayout.tsx` L70-81, `README.md` L1 | Nombre institucional consistente en todo el repositorio. |
| **Header (Navegación Pública)** | Botón `Iniciar Sesión` $\rightarrow$ `/login` | **ACCURATE** | `RootLayout.tsx` L208-221, `Login.tsx` | El subsistema de autenticación está 100% operativo en `/login`. |
| **Hero (Píldora Superior)** | `Fase 1 y Fase 2 — Completadas y Aprobadas` | **OUTDATED** | `docs/reports/PROJECT_MASTER_STATUS.md` L36-55 | Desactualizado por 14 fases. Fases 1 a 16, B3 y H13 están congeladas y aprobadas. |
| **Hero (Título H1)** | `Plataforma Educativa Virtual Nacional` | **ACCURATE** | `ComingSoon.tsx` L43-50 | Identidad institucional principal. |
| **Hero (Subtítulo)** | `Sistema de Gestión Educativa para las Instituciones Públicas de Colombia` | **ACCURATE** | `ComingSoon.tsx` L53-55, `ARCHITECTURE.md` | Define fielmente el dominio misional del software. |
| **Hero (Descripción)** | `Una plataforma educativa segura, accesible y moderna para docentes, estudiantes, directivos y administradores del sistema educativo colombiano.` | **INCOMPLETE** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` L35-46 | Omite a los **Acudientes (padres de familia)** y a las **Autoridades Territoriales (MEN / Secretarías de Educación)**, perfiles con portales y analítica ya desarrollados. |
| **Tarjeta 1 (Seguridad)** | `Seguridad por Diseño`: *Arquitectura con seguridad como prioridad, aislamiento institucional y auditoría completa.* | **ACCURATE** | `SECURITY.md`, `test_authorization.py`, `audit_logs` | Cumple controles estrictos (Argon2id, JWT en memoria, cookies HttpOnly, Blind 404, auditoría inmutable). Pendiente pentest externo formal (LIM-14). |
| **Tarjeta 2 (Multi-Tenancy)** | `Multi-Institucional`: *Soporte para todas las instituciones educativas públicas del territorio colombiano.* | **POTENTIALLY MISLEADING** | `PEVN_CURRENT_LIMITATIONS_REGISTER.md` LIM-24 | La arquitectura multi-tenant y la caché DANE (53.000+ sedes) existen; pero afirmar soporte nacional activo puede interpretarse erróneamente como un despliegue en producción ya efectuado. |
| **Tarjeta 3 (Accesibilidad)** | `Accesible y Móvil`: *Diseñado para dispositivos de gama baja y conectividad limitada. WCAG AA.* | **POTENTIALLY MISLEADING** | `PEVN_CURRENT_LIMITATIONS_REGISTER.md` LIM-18 | La UI es ligera y responsiva; pero **no existe una certificación formal WCAG 2.1 AA emitida por un tercero**, y LIM-18 confirma que no hay sincronización offline completa. |
| **Banner de Estado (Alert)** | `Infraestructura base completada. Las funcionalidades educativas estarán disponibles en fases posteriores.` | **OUTDATED** | `PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md` (40 capacidades listas) | **Contradicción flagrante.** Las funcionalidades educativas (académicas, evaluativas, SIEE, portales, tareas, asistencias, convivencia, circulares) ya están implementadas y operativas. |
| **Roadmap (Título)** | `Roadmap de Desarrollo` | **ACCURATE** | `ComingSoon.tsx` L107 | Encabezado estándar de sección. |
| **Roadmap (Fase 1)** | `Fase 1: Fundación` — `✓ COMPLETADA` | **ACCURATE** | `PHASE_1_FINAL_GATE.md` | Hito cerrado el 2026-08-21. |
| **Roadmap (Fase 2)** | `Fase 2: Autenticación y Autorización` — `✓ COMPLETADA` | **ACCURATE** | `PHASE_2_FINAL_GATE.md` | Hito cerrado el 2026-08-21. |
| **Roadmap (Fase 3)** | `Fase 3: Gestión Académica` — `3 PENDIENTE` | **OUTDATED** | `PHASE_3B_FINAL_REGRESSION_REPORT.md`, `PHASE_3C_...` | **Falso negativo severo.** Fase 3 (Instituciones, docentes, estudiantes, cursos y matrículas) está 100% implementada, certificada y navegable en `/academic`. |
| **Roadmap (Fase 4)** | `Fase 4: Aulas Virtuales` — `4 PENDIENTE` | **POTENTIALLY MISLEADING** | `VIRTUAL_CLASSROOMS_FORENSIC_COMPLETENESS_AUDIT.md`, `PEVN_VIRTUAL_CLASSROOM_READINESS.md` | Omite que la capa de software, API, adaptadores BBB y vistas web están 100% terminadas y verificadas. Solo el servidor físico está pendiente. |
| **Footer (Copyright)** | `© 2026 Plataforma Educativa Virtual Nacional. República de Colombia.` | **ACCURATE** | `RootLayout.tsx` L263-265 | Conforme con la fecha local (2026) y naturaleza del proyecto. |
| **Footer (Versión)** | `v0.1.0` | **OWNER DECISION** | `package.json`, `config/index.ts` | Fiel a la variable `VITE_APP_VERSION`, pero proyecta una imagen de prototipo inicial incompatible con 16 fases de desarrollo cerrado. |

---

## 4. Roadmap Audit

Comparación detallada entre lo que muestra el Roadmap público y el estado técnico real congelado en los reportes maestros:

| Fase en Landing UI | Estado en Landing UI | Descripción en UI | Estado Técnico Real Certificado | Evidencia Autoritativa en Repositorio | Clasificación |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **Fase 1: Fundación** | `✓ COMPLETADA` | Infraestructura base, arquitectura y configuración del entorno completadas. | **FROZEN & VERIFIED** | `PHASE_1_FINAL_GATE.md` (2026-08-21). Docker, Postgres 16, Redis 7, Alembic. | **ACCURATE** |
| **Fase 2: Autenticación y Autorización** | `✓ COMPLETADA` | Autenticación, autorización, RBAC, aislamiento multi-institucional y auditoría de seguridad. | **FROZEN & VERIFIED** | `PHASE_2_FINAL_GATE.md` (2026-08-21). Argon2id, JWT en memoria, cookies HttpOnly rotativas. | **ACCURATE** |
| **Fase 3: Gestión Académica** | `PENDIENTE` | Instituciones, docentes, estudiantes, cursos y matrículas. | **FROZEN & VERIFIED** | `PHASE_3B_FINAL_REGRESSION_REPORT.md`, `PHASE_3C_OFFICIAL_DANE_INSTITUTION_RESOLUTION.md`, 131/131 tests PASS. | **OUTDATED** |
| **Fase 4: Aulas Virtuales** | `PENDIENTE` | Integración BigBlueButton, grabaciones y herramientas de colaboración en tiempo real. | **SOFTWARE FROZEN & VERIFIED — INFRAESTRUCTURA FÍSICA PENDIENTE** | `VIRTUAL_CLASSROOMS_FORENSIC_COMPLETENESS_AUDIT.md`, `PEVN_VIRTUAL_CLASSROOM_READINESS.md`, 25 tests PASS. | **POTENTIALLY MISLEADING** |
| **Fases 5 a 16 (Omitidas en UI)** | *No visibles* | *Completamente ausentes del roadmap público.* | **FROZEN & VERIFIED** | Ver listado en Sección 4.1. | **INCOMPLETE** |

### 4.1 Resumen de Fases Existentes Omitidas en la Landing Actual:
1. **Fase 3C:** Ingesta y resolución de catálogo nacional DANE / DUE con 53.000+ sedes y aprovisionamiento criptográfico de Rectores.
2. **Fases 5 a 10:** Estrategia de Staging BBB, auditorías de protocolos WebRTC/Coturn y paquete de handoff de infraestructura física.
3. **Fase 11:** Tableros de Analítica Territorial (departamental/municipal) y recuperación de contraseñas autoservicio.
4. **Fase 12:** Aprovisionamiento dinámico y seguro de usuarios docentes y estudiantes vinculados a matrícula SIMAT.
5. **Fase 13:** Academic Hub dinámico, asignaciones docentes y gestión multi-sede.
6. **Fases 13D.5 / 13D.6:** Portal Soberano del Docente (`/teacher`), actividades, planilla de asistencia, planeación curricular y entrega segura de credenciales.
7. **Fase 14:** Identidad familiar desacoplada, auto-activación de acudientes y portales independientes para Estudiantes (`/student`) y Familias (`/guardian`).
8. **Fase 15:** Comunicaciones oficiales con acuse de recibo inmutable (IP/UTC), periódico escolar digital y observador/convivencia escolar bajo la Ley 1620 de 2013.
9. **Fase 16:** Sistema Institucional de Evaluación (SIEE, Decreto 1290 de 2009), notas híbridas justificadas, nivelaciones con tope legal, consolidación de boletines y actas de promoción anual.
10. **Tracks B3 / H13:** Entregas de tareas por estudiantes (*Submissions* con archivos y textos) y calificación docente en tiempo real.

---

## 5. Feature/Capability Audit

Auditoría de correspondencia entre capacidades del producto y la presentación pública:

| Capacidad Funcional | Afirmación en Landing Page | Estado Técnico Real | Evidencia en el Repositorio | Clasificación |
| :--- | :--- | :--- | :--- | :---: |
| **Gestión Institucional y Sedes** | Declarada como "Pendiente" en Fase 3 | **100% Operativa.** Catálogo DANE, creación de colegios y sedes. | `/api/v1/institutions`, `InstitutionsView.tsx` | **OUTDATED** |
| **Padrón de Docentes y Estudiantes** | Declarada como "Pendiente" en Fase 3 | **100% Operativa.** Fichas SIMAT, vinculación institucional y aprovisionamiento. | `/api/v1/teachers`, `/students`, vistas en `/academic` | **OUTDATED** |
| **Cursos, Grupos y Matrículas** | Declarada como "Pendiente" en Fase 3 | **100% Operativa.** Control de cupos máximos, traslados y grupos por jornada. | `/api/v1/groups`, `/enrollments`, `/transfers` | **OUTDATED** |
| **Tareas y Entregas Escolares** | Indicada como "Disponible en fases posteriores" | **100% Operativa.** Tareas docentes, entregas de estudiantes (archivo/texto), estados de entrega y tardanza. | `B3-H13_IMPLEMENTATION_REPORT.md`, `TeacherActivitiesView.tsx` | **OUTDATED** |
| **Planilla de Asistencia Diaria** | Indicada como "Disponible en fases posteriores" | **100% Operativa.** Control de asistencia por fecha, porcentaje de inasistencias y persistencia multi-sesión. | `/api/v1/teacher/groups/{id}/attendance`, `TeacherAttendanceView.tsx` | **OUTDATED** |
| **Evaluaciones y SIEE (D.1290)** | No mencionada en la Landing Page | **100% Operativa.** Escalas 1.00-5.00, notas aprobatorias, nivelaciones con tope, cierre de período y actas de promoción. | `phase16b_domain_services_report.md`, `DirectiveEvaluationManagementView.tsx` | **INCOMPLETE** |
| **Observador del Estudiante (L.1620)** | No mencionada en la Landing Page | **100% Operativa.** Situaciones Tipo I, II y III, descargos, acuerdos pedagógicos y confidencialidad parental. | `AUDITORIA_FASE15_COMUNICACIONES_NOTICIAS_CONVIVENCIA.md`, `StudentIncidentsView.tsx` | **INCOMPLETE** |
| **Comunicaciones y Circulares** | No mencionada en la Landing Page | **100% Operativa.** Circulares oficiales con segmentación y firma electrónica de acuse de recibo (IP/UTC). | `/api/v1/communications`, `StudentCommunicationsView.tsx` | **INCOMPLETE** |
| **Portales Soberanos (8 Roles)** | Solo se menciona "docentes, estudiantes, directivos y administradores" | **100% Operativa.** 8 portales especializados con redirección contextual post-login. | `App.tsx`, `StudentPortal.tsx`, `TeacherPortal.tsx`, `GuardianPortal.tsx` | **INCOMPLETE** |
| **Clases Virtuales (BigBlueButton)** | Declarada como "Pendiente" en Fase 4 | **Software listo; Servidor físico pendiente.** Adaptador BBB, URLs firmadas SHA, telemetría y grabaciones listas con Mock. | `backend/app/core/meeting/bbb_adapter.py`, `VirtualClassroomsView.tsx` | **POTENTIALLY MISLEADING** |

---

## 6. Contradictions Found

Se identificaron **seis (6) contradicciones estructurales severas** entre la Landing Page y el estado real del repositorio:

### Contradicción 1: Estado de las Funcionalidades Educativas
* **Texto en Landing:** *"Infraestructura base completada. Las funcionalidades educativas estarán disponibles en fases posteriores."*
* **Realidad Técnica:** La infraestructura base se completó hace más de un mes (2026-08-21). En la actualidad, **las funcionalidades educativas están plenamente implementadas, verificadas y en funcionamiento** (matrícula, calificaciones SIEE, tareas, entregas de estudiantes, asistencia, observador de convivencia, circulares y portales de alumnos y familias).

### Contradicción 2: Estado de la Fase 3 (Gestión Académica)
* **Texto en Landing:** *"Fase 3: Gestión Académica — PENDIENTE (Instituciones, docentes, estudiantes, cursos y matrículas)."*
* **Realidad Técnica:** La Fase 3 (3A, 3B, 3C) está **COMPLETADA, CERTIFICADA Y CONGELADA** con 131 pruebas automatizadas pasando al 100%. Todos los submódulos descritos (instituciones, sedes, docentes, estudiantes, cursos y libro de matrículas) son plenamente interactivos en la ruta `/academic`.

### Contradicción 3: Estado de la Fase 4 (Aulas Virtuales)
* **Texto en Landing:** *"Fase 4: Aulas Virtuales — PENDIENTE (Integración BigBlueButton, grabaciones y herramientas de colaboración en tiempo real)."*
* **Realidad Técnica:** La integración por software con BigBlueButton está **100% terminada, probada y certificada**. Incluye generación de checksums criptográficos, pasarela de telemetría de asistencia y gestión de grabaciones. Presentarla simplemente como "Pendiente" anula e invisibiliza el software desarrollado.

### Contradicción 4: Alcance de Fases Aprobadas
* **Texto en Landing:** *"Fase 1 y Fase 2 — Completadas y Aprobadas"*
* **Realidad Técnica:** El proyecto ha completado y congelado formalmente **16 fases y sub-tracks de ingeniería** (Fases 1 a 16, B1–B3, H2/H13). Declarar que solo las Fases 1 y 2 están completadas es falso respecto a la línea base actual.

### Contradicción 5: Cobertura Nacional vs. Estado de Despliegue
* **Texto en Landing:** *"Multi-Institucional: Soporte para todas las instituciones educativas públicas del territorio colombiano."*
* **Realidad Técnica:** Aunque la arquitectura es soberana y multi-tenant con caché DANE de cobertura nacional, la plataforma opera actualmente en entorno local/staging. Afirmar en la portada que brinda soporte activo a todas las instituciones puede ser interpretado por evaluadores como una afirmación de despliegue nacional activo no respaldada por la realidad de infraestructura.

### Contradicción 6: Acreditación de Accesibilidad WCAG AA
* **Texto en Landing:** *"Diseñado para dispositivos de gama baja y conectividad limitada. WCAG AA."*
* **Realidad Técnica:** Aunque el diseño de interfaz sigue buenas prácticas de semántica y accesibilidad, **no existe una certificación formal de conformidad WCAG 2.1 AA emitida por entidad certificadora**. Además, el soporte sin internet (modo offline) no está implementado (LIM-18).

---

## 7. BigBlueButton Status

Para evitar cualquier tergiversación ante el Ministerio de Educación Nacional (MEN) o MinTIC, se establece la distinción rigurosa de cuatro niveles:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 ESTADO REAL DEL SUBSISTEMA DE AULAS VIRTUALES               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Implementación de Software (Software Layer)     : 100% COMPLETADA (PASS) │
│ 2. Pruebas Técnicas de Integración (Mock Provider) : 100% COMPLETADA (PASS) │
│ 3. Comisionamiento de Servidores Físicos BBB/TURN  : 0% PENDIENTE (BLOCKER) │
│ 4. Validación Audiovisual con Clases Reales en Vivo: 0% PENDIENTE (BLOCKER) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dictamen Específico:
1. **Lo que SÍ existe:**
   - Interfaz abstracta `IMeetingProvider`.
   - Adaptador `BBBAdapter` con cálculo de firmas criptográficas SHA-1 y SHA-256 según el protocolo oficial de BigBlueButton.
   - Orquestador `VirtualClassroomService` con protección de acceso basada en matrícula oficial (SIMAT Gating).
   - Telemetría de asistencia (`AttendanceService`) con registro de segundos conectados.
   - Sincronización y reproductor de grabaciones (`RecordingService`).
   - Pantalla interactiva en `/virtual-classrooms` y vistas en portales de alumno y familia.
2. **Lo que NO existe (Bloqueantes Externos BLK-01 a BLK-06):**
   - No se ha instalado ni encendido un servidor físico con Ubuntu 22.04 LTS y BigBlueButton 2.7+.
   - No se ha desplegado el servidor Coturn TURN en puerto TCP 443 para atravesar firewalls escolares o redes CGNAT.
   - No se han emitido certificados SSL ni registros DNS públicos (`bbb.pevn.gov.co`).
3. **Recomendación para la Landing Page:**
   - La página pública **no debe marcar Aulas Virtuales como "Pendiente" genérica**, ni tampoco como "Completada" sin reservas.
   - **Formulación Recomendada:**  
     `Software e Integración BigBlueButton completados — Comisionamiento de servidores físicos en curso / pendiente.`

---

## 8. Government Presentation Consistency

Al contrastar la Landing Page frente a los documentos preparados para el Gobierno (`docs/government/` y `docs/reports/`):

| Concepto Evaluado | Declaración en Dossiers Gubernamentales | Presentación en Landing Actual | Dictamen de Coherencia |
| :--- | :--- | :--- | :---: |
| **Disponibilidad de Producción** | *En entorno de desarrollo / staging local; requiere despliegue en infraestructura pública.* | Indica "Pendiente" para funcionalidades que ya operan localmente, pero afirma "soporte para todas las instituciones". | **INCOHERENTE** |
| **BigBlueButton** | *Software listo y probado con mock; requiere provisión de servidor físico por la entidad pública.* | Marcada como simplemente "Pendiente" en Fase 4. | **SUB-DECLARADA** (Invisibiliza el software existente) |
| **Funcionalidades Académicas** | *100% operativas y listas para demostración en vivo (Escenarios A, B y C).* | Declara que "estarán disponibles en fases posteriores". | **CONTRADICTORIA** |
| **Integración SIMAT** | *Modelo relacional compatible; interoperabilidad en vivo requiere convenio interinstitucional.* | No se menciona en Landing. | **NEUTRO** |
| **Protección de Datos** | *Aislamiento lógico estricto; términos jurídicos y autorización parental pendientes.* | Menciona "Seguridad por Diseño". | **ALINEADO EN INTENCIÓN** |
| **Accesibilidad** | *Diseño ligero; requiere evaluación formal de accesibilidad.* | Afirma tajantemente "WCAG AA". | **SOBRE-DECLARADA** |

**Regla de Oro Gubernamental:** La Landing Page pública nunca debe ser más débil que la realidad del producto (falsos negativos), ni hacer promesas que excedan la evidencia legal y técnica existente (sobre-declaración).

---

## 9. Security / Accessibility Claims

### 9.1 Seguridad por Diseño
- **Afirmación:** *"Arquitectura con seguridad como prioridad, aislamiento institucional y auditoría completa."*
- **Evidencia Técnica Comprobada:**
  - Hashing de contraseñas con **Argon2id** (64 MB de memoria, 3 iteraciones, 4 hilos) — `backend/app/core/security/password.py`.
  - Tokens JWT de acceso efímeros (15 minutos) almacenados exclusivamente en la memoria volátil de React (cero almacenamiento en `localStorage` o `sessionStorage`).
  - Cookies de refresco HttpOnly, Secure, SameSite=Strict con rotación obligatoria y revocación por familia de sesión ante detección de reuso.
  - Aislamiento multi-inquilino estricto en ORM (`institution_id`) con política Blind 404 (retorna 404 en lugar de 403 para evitar escaneo de recursos ajenos).
  - Trazabilidad inmutable en la tabla `audit_logs` con censura recursiva de campos sensibles (`[REDACTED]`).
- **Limitación Documentada:** No se ha ejecutado un pentesting formal de caja negra por un tercero independiente (LIM-14). La afirmación es legítima a nivel de arquitectura interna, pero debe evitar presentarse como certificación de seguridad externa.

### 9.2 Accesibilidad y Movilidad (WCAG AA)
- **Afirmación:** *"Diseñado para dispositivos de gama baja y conectividad limitada. WCAG AA."*
- **Evidencia Técnica Comprobada:**
  - Estructura semántica HTML5 con roles ARIA (`banner`, `main`, `contentinfo`).
  - Jerarquía tipográfica consistente y paleta institucional con contrastes adecuados sobre fondo oscuro.
  - Paquete de frontend optimizado con Vite (bundle estático ligero).
- **Limitación Documentada:**
  - **No existe informe formal de conformidad WCAG 2.1 nivel AA**.
  - Si bien el peso del código es bajo, la plataforma no cuenta con motor de sincronización offline con IndexedDB (LIM-18). No se puede garantizar operatividad en escenarios de "conectividad limitada" si se pierde la conexión de red.
  - **Recomendación:** Matizar la redacción a *"Diseñado bajo estándares de accesibilidad e inclusión digital y optimizado para dispositivos móviles"*, retirando el distintivo formal "WCAG AA" hasta contar con la auditoría certificada.

---

## 10. Footer / Version / Branding

| Elemento | Valor Actual | Evaluación Forense | Riesgo / Recomendación |
| :--- | :--- | :--- | :--- |
| **Versión** | `v0.1.0` | Derivado de `VITE_APP_VERSION` en `.env` y `package.json`. | **Riesgo reputacional:** Proyecta la imagen de un prototipo embrionario cuando el sistema cuenta con 16 fases cerradas. Requiere decisión del propietario sobre versionado semántico institucional (ej. `v0.16.0` o `v1.0.0-rc1`). |
| **Año** | `2026` | Calculado dinámicamente: `new Date().getFullYear()`. | **Impecable.** Alineado con el año en curso del proyecto. |
| **Copyright** | `Plataforma Educativa Virtual Nacional. República de Colombia.` | Texto institucional sobrio y representativo. | **Conforme.** No requiere modificaciones. |
| **Colores / Identidad** | Azul institucional (`#0F172A`, `#010066`), Oro (`#FCD116`), Blanco. | Paleta solemne, representativa del servicio público educativo. | **Conforme.** Cumple pautas gubernamentales de sobriedad. |

---

## 11. Recommended Corrections

> [!IMPORTANT]
> **REGLA DE NO-INTERVENCIÓN:**  
> Las siguientes recomendaciones son de naturaleza **estrictamente editorial y declarativa**. Se presentan aquí exclusivamente como guía fundamentada para la futura tarea de implementación. **No han sido aplicadas en el código.**

### 11.1 Píldora de Estado Superior (Hero Badge)
- **Texto Actual:** `Fase 1 y Fase 2 — Completadas y Aprobadas`
- **Propuesta de Corrección:**  
  `Plataforma Integral — Gestión Académica, Portales y Convivencia Implementados`  
  *(o: `Fases 1 a 16 — Arquitectura, Gestión Académica y Portales Verificados`)*

### 11.2 Nota Informativa de Estado (Development Status Note)
- **Texto Actual:** `Infraestructura base completada. Las funcionalidades educativas estarán disponibles en fases posteriores.`
- **Propuesta de Corrección:**  
  `Módulos de Gestión Académica, Evaluación SIEE, Portales Institucionales y Convivencia 100% operativos. Aulas Virtuales con integración BigBlueButton implementada en software.`

### 11.3 Reestructuración del Roadmap Público
Se recomienda **abandonar la enumeración de fases técnicas de desarrollo interno (Fases 1 a 16, B3, H13)** en la portada pública y adoptar un **modelo de capacidades o macro-módulos institucionales**:

| Macro-Módulo Propuesto | Estado Público Sugerido | Descripción Propuesta |
| :--- | :---: | :--- |
| **1. Fundación & Seguridad** | `✓ COMPLETADA` | Arquitectura soberana, autenticación Argon2id, RBAC, aislamiento multi-tenant y auditoría. |
| **2. Gestión Académica & SIEE** | `✓ COMPLETADA` | Catálogo DANE, matrículas SIMAT, asignaciones docentes, evaluación Decreto 1290 y boletines. |
| **3. Convivencia & Portales** | `✓ COMPLETADA` | Observador Ley 1620, circulares con acuse digital, periódico escolar y portales independientes. |
| **4. Aulas Virtuales (BigBlueButton)** | `● SOFTWARE LISTO` | Integración de videoclases y grabaciones implementada; comisionamiento de servidores físicos en curso. |

*Si el propietario decide mantener la numeración de 4 fases:*
- Fase 3 (Gestión Académica): Actualizar inmediatamente a `✓ COMPLETADA`.
- Fase 4 (Aulas Virtuales): Actualizar a `● SOFTWARE LISTO / INFRAESTRUCTURA EN COMISIONAMIENTO`.

### 11.4 Matización de Tarjetas de Características
- **Multi-Institucional:** Mantener el enfoque de capacidad: *"Arquitectura multi-inquilino preparada para la integración territorial de instituciones oficiales."*
- **Accesible y Móvil:** Reemplazar *"WCAG AA"* por *"Diseño accesible e intuitivo, optimizado para smartphones y conexiones móviles."*

---

## 12. Product Integrity

Se certifica de manera categórica que durante la ejecución de esta auditoría forense:
- **Código de Producto:** CERO (0) archivos modificados en `frontend/` ni `backend/`.
- **Rutas y Componentes:** Inalterados; `frontend/src/pages/ComingSoon.tsx`, `RootLayout.tsx` y `App.tsx` permanecen intactos.
- **Base de Datos:** CERO (0) mutaciones, escrituras o alteraciones en PostgreSQL ni SQLite.
- **Migraciones:** CERO (0) ejecuciones de `alembic upgrade` o `downgrade`.
- **Herramientas de Formato:** No se ejecutó `prettier`, `black`, `ruff --fix` ni ninguna herramienta que altere el árbol de trabajo.

---

## 13. Git Safety

- **Commits:** CERO (0) commits generados.
- **Push:** CERO (0) operaciones de envío a repositorios remotos.
- **Operaciones Destructivas:** Ninguna.
- **Único Artefacto Producido:** La creación exclusiva del presente informe:  
  `docs/reports/PEVN_LANDING_PAGE_CURRENT_STATE_FORENSIC_AUDIT.md`.

---

## 14. Final Audit Gate

### Dictamen Final: **CONDITIONAL PASS**

**Justificación:**
1. **El software de PEVN se encuentra en un estado funcional y de madurez técnica muy superior a lo que su página de portada comunica.**
2. La Landing Page actual padece de **falsos negativos severos**, **afirmaciones obsoletas** y **contradicciones flagrantes** heredadas del hito fundacional (Fase 1/2), invisibilizando 14 fases de trabajo ya certificado.
3. El proyecto califica para **CONDITIONAL PASS** porque no existen bloqueos técnicos ni dudas sobre la línea base autoritativa de verdad; únicamente se requiere una intervención editorial y de presentación pública para reconciliar la interfaz con la realidad del producto.

**Condición para el Gate de Implementación:**  
La actualización de la Landing Page debe ejecutarse mediante una tarea controlada independiente, ciñéndose estrictamente a las recomendaciones documentadas en la Sección 11 de este informe y preservando la regla de verdad transparente ante el Gobierno Nacional.
