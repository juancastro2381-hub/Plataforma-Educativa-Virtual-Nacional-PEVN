# PEVN — DOSSIER DE PRESENTACIÓN EJECUTIVA GUBERNAMENTAL
## Plataforma Educativa Virtual Nacional para el Sector Oficial Colombiano
### Expediente de Sustentación para Autoridades Nacionales, Territoriales y Comités de Evaluación

**Destinatarios:** Ministerio de Educación Nacional (MEN), Ministerio de Tecnologías de la Información y las Comunicaciones (MinTIC), Secretarías de Educación Departamentales, Distritales y Municipales, Directivos Docentes y Comités Técnicos Evaluadores  
**Marco de Gobernanza:** AI Software Factory v1.2 — 11 principales artefactos de presentación gubernamental + 1 informe de cierre de la Fase 0.1  
**Fecha de Publicación:** 21 de Septiembre de 2026  
**Carácter del Documento:** Dossier Ejecutivo de Información Oficial (Read-Only)  
**Licencia Propuesta:** Apache License, Version 2.0 (Código Abierto)  

---

## 1. ¿Qué es PEVN?

La **Plataforma Educativa Virtual Nacional (PEVN)** es un sistema de información integral y modular, diseñado bajo un enfoque de soberanía tecnológica, concebido específicamente para la gestión académica, pedagógica, convivencial, administrativa y sincrónica de las instituciones educativas oficiales de Colombia.

A diferencia de los sistemas genéricos de gestión de cursos (*LMS*) o de aplicaciones administrativas importadas, PEVN fue proyectada desde su arquitectura fundacional para reflejar de forma nativa la **organización institucional, territorial y regulatoria del Estado colombiano**, incorporando la jerarquía de las Entidades Territoriales Certificadas (ETC), el Directorio Único de Establecimientos Educativos (DANE / DUE), el Sistema de Matrículas (SIMAT), el Sistema Institucional de Evaluación de los Estudiantes (Decreto 1290 de 2009) y el régimen de convivencia escolar (Ley 1620 de 2013).

PEVN incorpora estructuras de datos y reglas de negocio compatibles con el modelo de matrícula correspondiente y se encuentra arquitectónicamente preparada para una eventual interoperabilidad, sujeta a las interfaces técnicas oficiales, autorizaciones y acuerdos institucionales que determine la entidad competente. No reemplaza al SIMAT, al DUE ni a los sistemas del DANE, sino que armoniza con los estándares rectores del Estado.

---

## 2. ¿Por qué se desarrolló PEVN?

El sistema educativo oficial de Colombia ha enfrentado históricamente una profunda dispersión tecnológica:
- Los directivos y docentes se ven obligados a operar múltiples herramientas desacopladas: planillas de cálculo en papel o software local para notas, plataformas externas comerciales para videoclases, libros físicos para el observador de convivencia y canales informales (como aplicaciones de mensajería instantánea) para comunicarse con las familias.
- Esta fragmentación incrementa la carga administrativa de los educadores, genera asimetrías de información con los padres de familia y expone datos personales de menores de edad en canales no auditables ni protegidos por el Estado.
- PEVN nació como una respuesta de ingeniería de software pública para dotar al país de una **plataforma unificada, diseñada bajo un enfoque de soberanía tecnológica y libre de costos de licenciamiento privativo**, capaz de funcionar como infraestructura pública digital.

---

## 3. El Problema Educativo que Resuelve

1. **Desarticulación entre Matrícula, Aula y Calificación:** Falta de trazabilidad en tiempo real entre el registro civil/académico del estudiante y su desempeño en clase.
2. **Brecha de Información Escuela–Familia:** Dificultad de los padres de familia y acudientes legales para monitorear oportunamente la asistencia, las tareas y la convivencia de sus acudidos.
3. **Complejidad en la Aplicación del Decreto 1290 de 2009 (SIEE):** Dificultad para parametrizar de forma justa, transparente y auditable las políticas evaluativas autónomas de cada institución educativa (escalas valorativas, nivelaciones, topes y promoción anual).
4. **Falta de Trazabilidad en Situaciones de Convivencia Escolar (Ley 1620 de 2013):** Registro precario de las situaciones Tipos I, II y III, afectando el debido proceso, los descargos de los menores y el seguimiento de acuerdos pedagógicos y restaurativos.
5. **Riesgo de Dependencia y Cautiverio Tecnológico (*Vendor Lock-in*):** Dependencia de herramientas propietarias externas o licenciamientos comerciales recurrentes no adaptados a la normatividad educativa del país.

---

## 4. Usuarios Destinatarios y Comunidad Educativa

La plataforma articula armónicamente a todos los estamentos de la comunidad escolar colombiana:
- **Estudiantes Oficiales:** Acceso a sus materias, tareas, horarios, clases virtuales en vivo, calificaciones parciales, observador personal y boletines.
- **Padres de Familia y Acudientes:** Acompañamiento parental, seguimiento formativo de notas y asistencia, firma de circulares oficiales y observador de convivencia.
- **Docentes de Aula:** Gestión de carga académica asignada, creación de actividades, calificación ágil, control de asistencia diaria, planeación curricular y clases sincrónicas.
- **Coordinadores Académicos y de Convivencia:** Supervisión pedagógica, asignación de cargas, atención de situaciones escolares (Ley 1620) y consolidación de períodos.
- **Rectores y Directores Rurales:** Soberanía institucional, gestión de sedes, apertura de calendarios, cierre y sellado de períodos, actas de promoción y estructuras de matrícula compatibles con el modelo oficial.
- **Líderes de Secretarías de Educación (ETC):** Analítica territorial de cobertura, retención y monitoreo de establecimientos educativos de su jurisdicción.
- **Ministerio de Educación Nacional (MEN):** Visión analítica macro, catálogo nacional de instituciones y gobierno soberano de estándares.

---

## 5. Modelo Institucional y Jerarquía Territorial

PEVN estructura los datos respetando la división político-administrativa del Estado colombiano:

```
NIVEL NACIONAL (Ministerio de Educación Nacional - MEN)
  └── DEPARTAMENTO (Secretaría de Educación Departamental)
       └── MUNICIPIO (Entidad Territorial Certificada o No Certificada)
            └── INSTITUCIÓN EDUCATIVA (Colegio Oficial / Código DANE 12 dígitos)
                 └── SEDE EDUCATIVA (Sede Principal o Sede Rural / Código DANE Sede)
                      └── AÑO LECTIVO (Calendario Escolar Activo)
                           └── PERÍODOS ACADÉMICOS (1, 2, 3 o 4 períodos)
                                └── GRADOS Y GRUPOS (Jornada Mañana, Tarde, Única)
```

Cada colegio opera como una entidad soberana e independiente en sus datos, garantizando que ninguna institución pueda visualizar o modificar información de otra.

---

## 6. Capacidades Principales del Sistema

1. **Gestión Escolar Completa:** Sedes, grados, grupos, asignaturas y jornadas escolares.
2. **Padrón SIMAT e Identidad Desacoplada:** Separación técnica entre la ficha civil del estudiante/acudiente y la cuenta de acceso digital.
3. **Portal Docente Integrado:** Actividades académicas, recepción de evidencias digitales, control de asistencia diaria y planeación curricular.
4. **Sistema SIEE (Decreto 1290 de 2009):** Políticas institucionales configurables, consolidación híbrida de calificaciones, justificación obligatoria de notas ajustadas, nivelaciones formativas con tope y promoción anual.
5. **Comunicaciones con Firma Digital:** Circulares segmentadas y acuses de recibo con estampa de tiempo UTC y dirección IP.
6. **Convivencia Escolar (Ley 1620 de 2013):** Observador del estudiante Tipos I, II y III con descargos y compromisos restaurativos.
7. **Periódico Escolar y Divulgación:** Noticias pedagógicas, científicas, culturales y deportivas.
8. **Aulas Virtuales Sincrónicas:** Capa de software lista para integración con BigBlueButton con telemetría de conexión y control de grabaciones.
9. **Trazabilidad Inmutable:** Auditoría técnica estricta con censura automática de secretos y datos sensibles (`[REDACTED]`).

---

## 7. Portales Especializados por Rol

PEVN ofrece interfaces web dedicadas y optimizadas para cada actor:
- **Portal del Estudiante (`/student`):** Visualización clara de tareas pendientes, entregas, notas del período, boletines, horarios y observador formativo.
- **Portal del Acudiente (`/guardian`):** Panel familiar con selector dinámico de hijos para acompañar a múltiples estudiantes desde una sola cuenta.
- **Portal del Docente (`/teacher`):** Espacio de trabajo centrado en la labor pedagógica: Mis Grupos, Actividades, Calificaciones SIEE, Asistencia y Planeación.
- **Portal de Gestión Académica y Rectoría (`/academic`):** Consola para el Rector y Coordinador que centraliza matrículas, docentes, asignaciones y políticas SIEE.
- **Portal de Analítica Territorial (`/analytics/territorial`):** Tableros estadísticos agregados para Secretarías de Educación y el MEN.
- **Portal de Administración Nacional (`/admin/institutions`):** Gestión del directorio nacional DANE/DUE e incorporación de colegios.

---

## 8. Gestión Académica

La gestión académica modela de manera exacta la realidad de las instituciones educativas públicas:
- Configuración de sedes principales y anexas (sedes rurales multigrado o urbanas).
- Apertura formal del año lectivo (ej. 2026) con delimitación de fechas de inicio y finalización.
- Segmentación por períodos académicos regulares y períodos extraordinarios de recuperación.
- Definición de áreas obligatorias y fundamentales según la Ley General de Educación (Ley 115 de 1994) y asignaturas optativas institucionales.

---

## 9. Gestión de Estudiantes y Matrícula SIMAT

- Registro de fichas civiles de estudiantes con número de documento, tipo de documento nacional o de extranjería (C.C., T.I., R.C., PPT), fecha de nacimiento y código único SIMAT.
- Control estricto de cupos y capacidad máxima de aula para prevenir sobrecupos en salones.
- Libro de matrículas formal que asocia al estudiante con un grupo y sede en el año lectivo activo.
- Soporte para novedades de matrícula: retiros, traslados entre sedes o cambio de institución conservando el historial evaluativo.

---

## 10. Gestión Docente y Carga Académica

- Padrón institucional de docentes vinculados con identificación, título profesional y tipo de vinculación.
- Asignación Académica (*Academic Assignment*): Vinculación estricta de Docente + Asignatura + Grupo + Intensidad Horaria Semanal.
- **Principio de Ámbito Docente (*Teacher Scope*):** El docente únicamente tiene acceso y visibilidad sobre los estudiantes y salones que tiene formalmente asignados en su carga académica, blindando la privacidad de los demás alumnos de la institución.

---

## 11. Interacción Familiar y Acudientes (Decisión Canónica 3A-01)

PEVN resuelve una de las mayores dificultades de los colegios colombianos mediante la **Identidad Desacoplada**:
- La ficha civil del acudiente puede existir en el colegio sin que este disponga de conectividad inicial o correo electrónico.
- Relación N:M: Un estudiante puede tener múltiples acudientes registrados (madre, padre, abuelo), y un acudiente puede monitorear a varios hijos en diferentes grados desde una misma cuenta unificada.
- Auto-onboarding público seguro: El acudiente puede solicitar la activación digital de su cuenta validando su documento y correo contra la ficha registrada previamente por la institución.

---

## 12. Evaluación Formativa y SIEE (Decreto 1290 de 2009)

El subsistema de evaluación de PEVN es uno de los componentes más maduros del sistema:
- **Parametrización Autónoma (`SieePolicy`):** Cada colegio define sus escalas, notas aprobatorias y topes sin cables duros en código.
- **Consolidación Híbrida:** El sistema calcula automáticamente el promedio ponderado de las actividades realizadas, pero permite al docente realizar un ajuste pedagógico razonado (`final_score`). Si la nota definitiva difiere del cálculo automático, el sistema exige de forma obligatoria una justificación escrita (`adjustment_reason`).
- **Nivelaciones y Planes de Mejoramiento:** La nota reprobada original permanece inalterable en el historial (no se destruye). La prueba de recuperación se registra de forma independiente y la nota oficial se ajusta aplicando el tope institucional parametrizado (ej. 3.00 - Desempeño Básico).
- **Cierre y Sellado de Período:** El rector o coordinador formaliza el cierre de período, bloqueando de forma inmutable cualquier alteración posterior de notas. La reapertura requiere justificación directiva auditada.
- **Boletines Oficiales:** Emisión estructurada de boletines periódicos, acumulativo final y sábanas de notas grupales con puesto en el salón.
- **Promoción Escolar Anual:** Evaluación algorítmica de los criterios SIEE (asignaturas reprobadas, inasistencias injustificadas) y generación de actas oficiales de promoción y graduación.

---

## 13. Control de Asistencia Diaria

- Planilla digital de registro rápido por grupo y fecha (`Presente`, `Ausente`, `Justificado`, `Retardo`).
- Alertas inmediatas para docentes y directivos ante ausencias reiteradas.
- Visualización transparente en el portal familiar para combatir la deserción y el ausentismo escolar.

---

## 14. Actividades Académicas y Entregas de Estudiantes (Fase B3)

- Creación y edición de actividades en estado Borrador (`DRAFT`) antes de su divulgación.
- Tres modalidades de entrega: `TEXT` (respuesta escrita en plataforma), `FILE` (archivos adjuntos) y `TEXT_AND_FILE`.
- Almacenamiento seguro con análisis binario de tipo de archivo (Magic Bytes) para rechazar ejecutables maliciosos y límite de 10 MB.
- Detección determinística de entregas tardías en UTC (`is_late = True`).
- Ciclo de revisión docente con devoluciones pedagógicas (`RETURNED`) para corrección y reintentos versionados.

---

## 15. Convivencia Escolar y Observador del Estudiante (Ley 1620 de 2013)

- Tipificación estricta de situaciones escolares conforme a la ley colombiana:
  - **Tipo I:** Conflictos cotidianos manejados mediante mediación escolar.
  - **Tipo II:** Situaciones de agresión, acoso escolar (*bullying*) o ciberacoso que no revisten características de delito.
  - **Tipo III:** Situaciones que presuntamente constituyen delitos contra la libertad, integridad y formación sexual o cualquier otro delito según la ley penal.
- Garantía del debido proceso: Registro formal de la descripción fáctica, descargos del estudiante, medidas formativas y acuerdos restaurativos.
- Confidencialidad absoluta: Las anotaciones solo son visibles por el estudiante involucrado, su acudiente y el comité de convivencia de la institución. Blind 404 estricto para terceros.

---

## 16. Comunicaciones Institucionales y Periódico Escolar

- Emisión de circulares y directrices oficiales con segmentación de audiencia por sede, grado, grupo o rol.
- **Acuse de Recibo Electrónico:** Mecanismo de confirmación de lectura con estampa de tiempo UTC y dirección IP registrada, generando evidencia digital no repudiable de notificación a padres y docentes.
- Periódico escolar digital clasificado por categorías temáticas (académica, cultural, deportiva, científica).

---

## 17. Clases Virtuales Sincrónicas (BigBlueButton)

- Capa de software completa basada en el protocolo estándar `IMeetingProvider` con adaptador oficial para BigBlueButton (`BBBAdapter`).
- Generación criptográfica de URLs firmadas con sumas de comprobación SHA-1 y SHA-256.
- Control de ingreso restringido por matrícula SIMAT (un alumno no puede ingresar a una clase de otro salón).
- Telemetría de conexión: Registro de horas de ingreso, salida y duración efectiva de asistencia.
- Gestión de grabaciones con visibilidad controlada por el profesor.
- **Posición Factual Honesta:** El software está terminado y verificado mediante un simulador en memoria (*Mock Provider*); **el servicio en vivo requiere el comisionamiento de servidores físicos BigBlueButton y relay Coturn TURN**.

---

## 18. Arquitectura y Controles de Seguridad Técnicamente Verificados

La plataforma implementa una arquitectura de seguridad con controles verificables. No se identificaron vulnerabilidades críticas dentro del alcance de la auditoría técnica realizada (análisis estático, análisis de dependencias y pruebas de integración):
- **Cero Contraseñas Planas:** Cifrado con **Argon2id** (64 MB de memoria, 3 iteraciones, salting aleatorio de 16 bytes).
- **Higiene de Tokens JWT:** Los tokens de acceso residen única y exclusivamente en la **memoria volátil de JavaScript de React**. No se almacena ningún token en `localStorage` ni `sessionStorage`, como medida de mitigación frente al robo persistente de credenciales mediante XSS.
- **Cookies de Sesión Seguras:** Refresh tokens rotativos en cookies `HttpOnly`, `SameSite=Strict`, `Secure` y vigencia de 7 días.
- **Detección Activa de Replay:** Si un atacante intercepta y reutiliza un token de refresco antiguo, el backend anula inmediatamente toda la familia de tokens (`family_id`), cierra la sesión activa y emite una alerta crítica.
- **Protección Anti-IDOR (Blind 404):** Intentos de manipulación de identificadores UUID responden `404 Not Found` en lugar de revelar existencia con 403.
- **Auditoría Inmutable:** Tabla `audit_logs` en PostgreSQL con censura automática y recursiva de datos sensibles (`[REDACTED]`).
- **Estado de Certificación:** No se aducen certificaciones gubernamentales formales, las cuales deberán formar parte del ciclo de evaluación y acreditación institucional.

---

## 19. Arquitectura Multi-Institucional y Aislamiento de Datos

- Todas las tablas de datos y consultas de base de datos incorporan la clave `institution_id`.
- Principio *Deny-by-Default*: Ningún usuario puede consultar o alterar registros fuera de su colegio, a menos que cuente con alcance territorial o nacional expreso (SuperAdmin o MEN).
- El aislamiento se ejecuta a nivel de lógica de dominio y ORM, garantizando la soberanía de la información de cada municipio y departamento.

---

## 20. Modelo de Integración DANE / DUE

- Ingesta estructurada y caché local del Directorio Único de Establecimientos Educativos de Colombia.
- Normalización de nombres oficiales, códigos DANE institucionales de 12 dígitos y códigos DANE de sedes.
- Proceso de acreditación criptográfica de rectores enlazados de forma unívoca a su código DANE correspondiente.

---

## 21. Estado Técnico Actual del Producto

```
========================================================================================
                      ESTADO TÉCNICO VERIFICADO DE PEVN (FASE 0)
========================================================================================
Backend API             : FastAPI 0.110+ / Python 3.12 / SQLAlchemy 2.0 Async
Frontend SPA            : React 18 / Vite / TypeScript / Tailwind CSS / PWA
Base de Datos           : PostgreSQL 16 con 23 migraciones lineales Alembic
Caché / Sesiones        : Redis 7
Pruebas Automatizadas   : 432 pruebas backend (100% PASS) / 119 pruebas frontend (96.7% PASS)
Análisis Estático       : 0 errores mypy, 0 errores ruff, 0 errores tsc
Entorno Actual          : Contenedores Docker de desarrollo y pruebas locales
========================================================================================
```

---

## 22. Limitaciones Actuales Transparentes

En apego a la transparencia pública, se declaran los aspectos que actualmente requieren desarrollo complementario, validación o infraestructura:
1. **Servidores Físicos BigBlueButton:** No desplegados actualmente en infraestructura de producción (integración de software implementada y verificada mediante proveedor simulado Mock).
2. **Servidor Coturn (STUN/TURN en TCP 443):** No desplegado (requerido para saltar cortafuegos escolares y CGNAT rural).
3. **Almacenamiento de Objetos S3:** Opera actualmente en disco local particionado; requiere conexión a bucket S3/MinIO para clústeres multi-servidor.
4. **Exportador Masivo a PDF:** Los boletines se visualizan reactivamente en web; falta el motor de generación masiva de PDFs oficiales para impresión con código QR.
5. **Notificaciones Push y Correo SMTP:** Se almacenan en base de datos; falta conectar pasarela de correo gubernamental y WebSockets.
6. **Enlace en Vivo con SIMAT:** Opera por importación de archivos estructurados; falta convenio para API en tiempo real con el MEN.
7. **Capacidad y Concurrencia Nacional:** La arquitectura está diseñada para permitir escalamiento horizontal; la capacidad efectiva a escala nacional deberá determinarse mediante pruebas de carga y validación de infraestructura.

---

## 23. Requerimientos para una Fase Piloto (5 a 10 Colegios)

Para llevar a cabo un piloto controlado y exitoso con acompañamiento de una Secretaría de Educación o el MEN, se requiere:
- **1 Servidor Web/API y Base de Datos:** Instancia en la nube de 8 vCPU, 32 GB RAM y 200 GB SSD (alberga FastAPI, React, PostgreSQL 16 y Redis 7).
- **1 Servidor Físico BigBlueButton + Coturn:** Servidor dedicado Ubuntu 22.04 LTS (16 vCPU, 32 GB RAM, 500 GB NVMe, 1 Gbps) para clases virtuales.
- **Nombres de Dominio:** Subdominios oficiales de prueba (ej. `piloto.pevn.gov.co`, `bbb-piloto.pevn.gov.co`).
- **Certificados SSL/TLS:** Certificados de servidor web (Let's Encrypt o corporativos).
- **Acompañamiento Humano:** Designación de un enlace técnico institucional por parte de la Secretaría participante.

---

## 24. Requerimientos para una Operación en Producción Nacional

Para atender la escala requerida por la comunidad de estudiantes y docentes del sector oficial:
- Clúster de contenedores Kubernetes con autoescalado horizontal (HPA).
- Distribución de frontend estático a través de una Red de Entrega de Contenidos (CDN) gubernamental.
- Clúster de base de datos PostgreSQL 16 de Alta Disponibilidad (Multi-AZ) con réplicas de lectura y PgBouncer.
- Clúster distribuido de servidores BigBlueButton gestionado mediante el balanceador de carga **Scalelite**.
- Sistema centralizado de gestión de secretos corporativo (HashiCorp Vault o equivalente).
- Plan de respaldos continuos (WAL archiving) con RPO < 15 minutos y RTO < 2 horas.
- Auditoría de penetración (*Ethical Hacking*) y Web Application Firewall (WAF) ministerial.

---

## 25. Proceso Propuesto de Evaluación Gubernamental

Se sugiere a las autoridades interesadas seguir un proceso estructurado de cuatro fases:
1. **Sesión Técnica de Demostración en Vivo:** Presentación de los flujos de trabajo utilizando el guion formalizado en la Guía de Demostración Operativa (`PEVN_GOVERNMENT_DEMONSTRATION_RUNBOOK.md`).
2. **Mesa Técnica de Inspección de Código y Ciberseguridad:** Revisión independiente del repositorio, arquitectura y pruebas por parte de ingenieros de MinTIC y ColCERT.
3. **Mesa Jurídica e Institucional:** Revisión de la política de tratamiento de datos personales de menores de edad y armonización con las tablas de retención documental.
4. **Acuerdo de Prueba Piloto:** Formalización de la infraestructura para el despliegue experimental en una Entidad Territorial Certificada.

---

## 26. Concepto y Alcance de la Prueba Piloto

- **Duración Recomendada:** Un período académico escolar (aproximadamente 10 a 12 semanas).
- **Alcance Poblacional:** 5 a 10 colegios oficiales (combinando sedes urbanas y rurales).
- **Objetivos de Medición:** Usabilidad docente, adopción familiar, estabilidad de la planilla SIEE, rendimiento en redes escolares de baja conectividad y retroalimentación pedagógica directa.

---

## 27. Propuesta Técnica de Donación y Transferencia Tecnológica al Estado

- **Naturaleza de la Propuesta:** El presente documento constituye una **propuesta técnica de donación y transferencia tecnológica**, sujeta a revisión jurídica y a los acuerdos institucionales que determine la entidad competente. No constituye un contrato vinculante ni perfecciona transferencia alguna de derechos; su ejecución estará sujeta al instrumento jurídico que determine la entidad pública receptora.
- **Modelo de Licenciamiento Propuesto:** Se propone la entrega de los activos tecnológicos bajo la licencia de código abierto **Apache 2.0**.
- **Cero Costos de Licencia:** La plataforma no genera regalías, cobros por estudiante matriculado ni ataduras comerciales para el Ministerio ni las Secretarías de Educación ($0 COP en licenciamiento de software).
- **Soberanía y Código Fuente:** El Estado recibiría el código fuente completo, las migraciones de base de datos, la documentación de arquitectura, los manuales de despliegue y las suites de pruebas automatizadas.
- **Independencia Operativa:** La entidad pública adquiere plena autonomía para alojar el sistema en sus propios centros de datos, contratar soporte técnico o asumir el mantenimiento mediante sus propios equipos de ingeniería.

---

## 28. Declaración Final de Cierre

La Plataforma Educativa Virtual Nacional (PEVN) se encuentra en un estado de **madurez técnica comprobada y lista para ser evaluada formalmente por las autoridades del sector educativo y tecnológico de Colombia**. 

Representa una oportunidad histórica para dotar a la educación pública del país de una herramienta digital moderna, segura y digna, construida con los más altos estándares de ingeniería y concebida como un bien público digital al servicio de la infancia, la juventud y el magisterio colombiano.
