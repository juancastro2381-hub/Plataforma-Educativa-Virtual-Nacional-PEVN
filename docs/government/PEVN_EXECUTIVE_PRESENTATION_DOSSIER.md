# PEVN — DOSSIER DE PRESENTACIÓN EJECUTIVA GUBERNAMENTAL
## Plataforma Educativa Virtual Nacional para el Sector Oficial Colombiano
### Expediente de Sustentación para Autoridades Nacionales, Territoriales y Comités de Evaluación

**Destinatarios:** Ministerio de Educación Nacional (MEN), Ministerio de Tecnologías de la Información y las Comunicaciones (MinTIC), Secretarías de Educación Departamentales, Distritales y Municipales, Directivos Docentes y Comités Técnicos Evaluadores  
**Marco de Gobernanza:** AI Software Factory v1.2 — Expediente Integral de Presentación Gubernamental (DOC-01)  
**Fecha de Publicación:** 13 de Octubre de 2026 (Actualización Consolidada)  
**Carácter del Documento:** Dossier Ejecutivo de Información Oficial (Read-Only)  
**Licencia Propuesta:** Apache License, Version 2.0 (Código Abierto / $0 COP en Regalías de Software)  

---

## 1. Declaración de Naturaleza e Iniciativa Tecnológica Independiente

La **Plataforma Educativa Virtual Nacional (PEVN)** es una iniciativa tecnológica independiente concebida y desarrollada por ingeniería de software nacional, puesta a disposición del Estado colombiano para su evaluación técnica, funcional, jurídica y de seguridad.

> [!IMPORTANT]
> **ALCANCE Y NATURALEZA DE LA PROPUESTA:**
> El presente dossier tiene un carácter estrictamente informativo, técnico y propositivo. No constituye una aprobación oficial, certificación gubernamental, contrato de adquisición pública ni compromiso de adopción vinculante por parte de ninguna entidad del Estado. La propuesta contempla poner a disposición del Estado colombiano el código fuente íntegro, los esquemas de bases de datos, los manuales y las suites de pruebas automatizadas bajo la licencia permisiva **Apache License 2.0 ($0 COP en costo de licenciamiento)**, sujeta a los convenios interadministrativos y decisiones institucionales que determinen las autoridades competentes.

---

## 2. El Problema Educativo y Estructural que Aborda

El sistema educativo oficial colombiano atiende a más de 8 millones de niños, niñas y jóvenes a través de una red descentralizada de Entidades Territoriales Certificadas (ETC). Históricamente, la operación cotidiana de las instituciones educativas públicas ha enfrentado una profunda fragmentación tecnológica:

1. **Dispersión de Herramientas Desacopladas:** Coexistencia de planillas de cálculo en papel o software monousuario local para el registro de calificaciones, plataformas comerciales extranjeras de videoconferencia, libros físicos o carpetas para el observador de convivencia escolar y aplicaciones informales de mensajería instantánea para la interacción con los acudientes.
2. **Sobrecarga Administrativa Docente:** Los educadores dedican horas sustanciales a la transcripción manual y consolidación de notas, restando tiempo a la mediación pedagógica y al diseño curricular.
3. **Brecha de Información Escuela–Familia:** Dificultad recurrente de los padres y acudientes legales para hacer seguimiento oportuno y preventivo a la asistencia, tareas y convivencia de los estudiantes.
4. **Riesgo de Privacidad de Menores:** La utilización de canales informales expone datos personales sensibles de menores de edad en plataformas comerciales externas no auditadas por el Estado.
5. **Cautiverio Tecnológico (*Vendor Lock-in*):** Dependencia de soluciones privativas cuyos modelos de cobro recurrente por estudiante gravan los presupuestos territoriales sin transferir soberanía técnica ni capacidades al Estado.

---

## 3. Modelo Institucional y Jerarquía Territorial Multi-Inquilino

PEVN fue construida desde sus cimientos para reflejar de forma nativa la organización político-administrativa y territorial de Colombia, garantizando un aislamiento estricto de datos (*multi-tenancy*) entre instituciones y jurisdicciones:

```
NIVEL NACIONAL (Ministerio de Educación Nacional - MEN / MinTIC)
  └── NIVEL DEPARTAMENTAL (Secretarías de Educación Departamentales / 32 Departamentos)
       └── NIVEL MUNICIPAL (Entidades Territoriales Certificadas y No Certificadas / 1,122 Municipios)
            └── INSTITUCIÓN EDUCATIVA (Establecimiento Educativo Oficial / Código DANE 12 dígitos)
                 └── SEDE EDUCATIVA (Sede Principal o Sedes Rurales / Código DANE Sede 12 dígitos)
                      └── AÑO LECTIVO (Calendario Escolar A o B)
                           └── PERÍODOS ACADÉMICOS (Configuración SIEE: 1 a 4 períodos)
                                └── GRADOS, GRUPOS Y JORNADAS (Mañana, Tarde, Única, Nocturna)
```

Cada colegio opera como una entidad soberana e independiente en sus datos mediante el aislamiento riguroso por `institution_id`. Los accesos no autorizados a nivel de interfaz o API responden con el patrón de seguridad `Blind 404 (Not Found)`, impidiendo la fuga de metadatos o la enumeración de recursos entre diferentes instituciones.

---

## 4. Desglose Exhaustivo de los 11 Roles del Sistema

El modelo de control de acceso basado en roles (RBAC) de PEVN delimita con precisión matemática las responsabilidades de cada estamento, totalizando **11 roles canónicos** implementados y verificados:

| Rol Canónico | Identificador | Nivel | Ámbito Territorial / Operativo | Atribuciones Principales |
| :--- | :--- | :---: | :--- | :--- |
| **Superadministrador** | `superadmin` | 100 | Global / Plataforma | Mantenimiento técnico global, diagnóstico operativo de inquilinos, monitoreo de salud del sistema y auditoría inmutable. |
| **Administrador Nacional** | `national_admin` | 90 | Nacional (MEN) | Supervisión macro, gobierno del catálogo oficial DANE, analítica territorial consolidada e incorporación nacional. |
| **Administrador Departamental** | `department_admin` | 80 | Departamental (Secretaría) | Gobernanza departamental, monitoreo de municipios no certificados y colegios oficiales adscritos a su jurisdicción. |
| **Administrador Municipal** | `municipality_admin` | 70 | Municipal (Alcaldía / SEM) | Gobierno territorial municipal, activación e invitación de rectores para establecimientos oficiales de su municipio. |
| **Administrador Institucional** | `institution_admin` | 60 | Institución Educativa | Soporte técnico institucional, parametrización de catálogos y gestión de infraestructura local del colegio. |
| **Rector / Director Rural** | `rector` | 50 | Institución Educativa | Máxima autoridad del colegio: apertura de años lectivos, cierre y sellado de períodos SIEE, gestión de sedes y gobierno escolar. |
| **Coordinador General** | `coordinator` | 40 | Institución Educativa | Gestión escolar delegada, administración de horarios, supervisión convivencial y soporte directivo. |
| **Coordinador Académico** | `academic_coordinator` | 40 | Institución Educativa | Parametrización de asignaturas, distribución de cargas académicas docentes, comisiones de evaluación y planes de estudio. |
| **Docente de Aula** | `teacher` | 30 | Asignaciones del Docente | Gestión pedagógica dentro de su *Teacher Scope*: planillas SIEE, asistencia diaria, actividades, planeación y aulas virtuales. |
| **Estudiante** | `student` | 20 | Ficha y Matrícula Activa | Portal personal: consulta de tareas, entrega de evidencias, calificaciones parciales SIEE, observador, circulares y clases sincrónicas. |
| **Acudiente de Familia** | `guardian` | 10 | Estudiantes Acudidos (N:M) | Portal familiar unificado con selector dinámico de hijos: seguimiento formativo, asistencia, observador y acuses de recibo. |

> [!NOTE]
> **ACLARACIÓN TAXONÓMICA SOBRE EL ROL DE AUDITOR:**
> En estricto apego a la verdad arquitectónica del código, el rol `AUDITOR` **no es un rol configurado en la base de datos ni en las interfaces de seguridad de PEVN**. La función de fiscalización y auditoría técnica es ejecutada de forma integral por los roles `superadmin` y `national_admin` mediante la consola técnica de Diagnóstico de Inquilinos (`/operations/tenant-diagnostics`) y el registro inmutable en la tabla `audit_logs` de PostgreSQL. Presentar `AUDITOR` como un rol independiente de usuario sería una inexactitud funcional que este expediente rechaza categóricamente.

---

## 5. El Rol de Administrador Municipal (`MUNICIPALITY_ADMIN`)

Certificado e integrado en la arquitectura territorial de PEVN, el rol de **Administrador Municipal** resuelve el enlace de gobernanza entre la administración municipal (Alcaldías y Secretarías de Educación Municipales) y los colegios oficiales de su jurisdicción:

1. **Flujo Criptográfico de Invitación:** Los administradores municipales son aprovisionados mediante invitaciones tokenizadas de un solo uso (`single-use token`), con vigencia delimitada y almacenamiento del hash criptográfico SHA-256 en base de datos.
2. **Activación Pública Segura:** La activación de la cuenta se realiza en la interfaz pública `/auth/accept-invitation`, resolviendo determinísticamente el origen único para evitar discrepancias de enrutamiento.
3. **Contención Territorial Estricta:** El administrador municipal queda anclado a su código DIVIPOLA municipal y departamento. Sus consultas e interfaces le permiten visualizar únicamente los colegios oficiales de su municipio en el catálogo DANE.
4. **Cadena Canónica de Autoridad:** Posee la atribución exclusiva de invitar y activar a los Rectores de los colegios de su municipio, respetando la jerarquía institucional sin interferir en los asuntos internos de colegios de otras entidades territoriales.

---

## 6. Integración del Catálogo Oficial DANE / DUE y Trazabilidad Forense

PEVN incorpora la totalidad del catálogo oficial de la infraestructura educativa pública de Colombia, garantizando correspondencia biunívoca con los registros del Departamento Administrativo Nacional de Estadística (DANE) y el Directorio Único de Establecimientos Educativos (DUE) del Ministerio de Educación Nacional:

### 6.1 Cifras Empíricas del Catálogo en Base de Datos (PostgreSQL)

- **18,031 Establecimientos Educativos Oficiales (`official_institution_catalog`):** Colegios y escuelas sede principal debidamente codificados con su código DANE único de 12 dígitos, sector oficial, zona (urbana/rural) y jerarquía territorial.
- **51,521 Sedes Educativas Físicas (`official_campus_catalog`):** Inventario exhaustivo de sedes principales y adscritas (sedes rurales, anexas, multigrado), con código DANE de sede de 12 dígitos.
- **38 Tenants Operacionales Activos (`institutions`):** Instituciones educativas plenamente configuradas en la base de datos operativa para pruebas de ciclo completo, multi-inquilino y demostraciones.
- **10 Lotes de Sincronización Auditados (`official_catalog_sync_batches`):** Trazabilidad completa de procesos de ingesta y reconciliación masiva.

### 6.2 Proveniencia Verificable de los Conjuntos de Datos Abiertos

1. **Directorio de Colegios (EE):** Portal de Datos Abiertos del Estado colombiano (`datos.gov.co/cfw5-qzt5`), Directorio de Establecimientos Educativos Preescolar, Básica y Media 2024 (MEN/DANE).
2. **Directorio de Sedes Educativas:** Portal de Datos Abiertos (`datos.gov.co/x5ay-984n`), Directorio Nacional de Sedes Educativas de Colombia.
3. **Línea Base Semilla:** Conjunto de datos (`datos.gov.co/c36d-tcj8`), que provee una muestra representativa de 41 instituciones educativas en 33 departamentos de Colombia.

### 6.3 Trazabilidad Forense del Elemento de Interfaz: *"Total: colegios en el catálogo"*

Para responder con precisión forense a cualquier auditor técnico o gubernamental, la visualización de los totales del catálogo en la interfaz web de PEVN se encuentra trazada de extremo a extremo:

- **Componentes y Vistas Frontend:**
  - `frontend/src/pages/admin/OnboardingView.tsx` (Línea 593): Etiqueta institucional `Total: <span className="text-white font-semibold">{catalogTotal}</span> colegios en el catálogo`.
  - `frontend/src/pages/admin/InstitutionsView.tsx` (Líneas 1205-1215): Insignias de segmentación `Catálogo Semilla ({total_institutions} EE / {total_campuses} Sedes)` y `Catálogo Nacional Completo`.
  - `frontend/src/pages/admin/InstitutionsView.tsx` (Línea 1421): Tarjeta de métricas `Catálogo Oficial DANE: {catalogSummary.total_catalog} Establecimientos en jurisdicción`.
  - `frontend/src/pages/admin/InstitutionsView.tsx` (Línea 1752): Texto de paginación `Mostrando {catalogItems.length} de {catalogTotal} establecimientos oficiales`.
- **Rutas y Controladores Backend:**
  - `GET /api/v1/onboarding/catalog` (`backend/app/api/v1/endpoints/onboarding.py:60`) invocando `OnboardingService.explore_catalog()`.
  - `GET /api/v1/institutions/catalog-explorer` (`backend/app/api/v1/endpoints/institutions.py:578`) invocando `InstitutionService.list_official_catalog_with_status()`.
  - `GET /api/v1/institutions/catalog/sync-status` (`backend/app/api/v1/endpoints/institutions.py:82`) invocando `OfficialCatalogSyncService.get_sync_status()`.
- **Tablas Relacionales de Persistencia:**
  - `official_institution_catalog` (18,031 registros con índices B-Tree en `dane_code`, `department_code`, `municipality_code`).
  - `official_campus_catalog` (51,521 registros con clave foránea hacia la institución oficial).
  - `institutions` (38 registros operacionales vinculados por `dane_code`).

---

## 7. Motor de Evaluación SIEE (Decreto 1290 de 2009)

El subsistema de evaluación formativa de PEVN implementa de forma rigurosa los mandatos del **Decreto 1290 de 2009**, otorgando a cada institución educativa autonomía técnica para parametrizar su propio Sistema Institucional de Evaluación de los Estudiantes (SIEE):

1. **Cuatro Escalas Nacionales de Valoración:** Mapeo matemático determinístico a las escalas obligatorias del MEN: **Desempeño Superior**, **Desempeño Alto**, **Desempeño Básico** y **Desempeño Bajo** (escala numérica institucional, comúnmente de 1.00 a 5.00 con nota mínima aprobatoria configurable, típicamente 3.00).
2. **Períodos Académicos y Ponderaciones:** Soporte para esquemas de 1 a 4 períodos escolares, con asignación porcentual configurable (ej. 4 períodos de 25% cada uno o trimestres ponderados).
3. **Consolidación Híbrida de Calificaciones:** El sistema computa de forma automática el promedio ponderado de las actividades académicas registradas por el docente, pero faculta al educador para ingresar una nota definitiva ajustada (`final_score`) fundamentada en su criterio formativo. Si la nota ajustada difiere del promedio automático, la plataforma exige **obligatoriamente una justificación escrita** (`adjustment_reason`), la cual queda asentada en la auditoría del sistema.
4. **Planes de Mejoramiento y Nivelaciones con Tope:** Cuando un estudiante reprueba un período, la calificación reprobada original se preserva de manera inalterable en el historial escolar. La prueba de recuperación o nivelación se registra de forma independiente y, en caso de ser superada, la nota oficial se actualiza aplicando el tope máximo parametrizado en el SIEE (típicamente 3.00 / Desempeño Básico).
5. **Cierre y Sellado Inmutable de Períodos:** El Rector o Coordinador ejecuta el cierre formal del período, bloqueando criptográfica y lógicamente cualquier modificación posterior de notas por parte de los docentes. La reapertura extraordinaria requiere autorización directiva con registro obligatorio de justificación en `audit_logs`.
6. **Promoción Anual y Actas:** Algoritmo de promoción que evalúa el número de asignaturas reprobadas y el porcentaje de inasistencias acumuladas frente a los criterios del SIEE institucional, generando la sábana final de notas y el acta de promoción.

---

## 8. Estructuras de Matrícula Compatibles con SIMAT

PEVN no sustituye al Sistema de Matrículas (SIMAT) del Ministerio de Educación Nacional, sino que incorpora **estructuras de datos y modelos de validación plenamente compatibles** con la ficha de matrícula oficial:

- **Ficha Civil y Académica:** Modelado del código SIMAT único del estudiante, tipología documental oficial (Registro Civil, Tarjeta de Identidad, Cédula de Ciudadanía, Permiso de Protección Temporal PPT, Cédula de Extranjería), fecha de nacimiento, género, estrato y condición de vulnerabilidad o discapacidad.
- **Separación de Identidad Digital (Decisión Canónica 3A-01):** La ficha civil del estudiante o acudiente puede ser creada y matriculada en el sistema sin que estos requieran contar previamente con un correo electrónico o cuenta de acceso digital. La cuenta de usuario (`User`) se enlaza de forma desacoplada cuando el usuario realiza el proceso de activación.
- **Control Estricto de Cupos:** Bloqueo preventivo de sobrecupos en grupos escolares para garantizar cumplimiento de los estándares de capacidad física y calidad pedagógica.
- **Preparación Arquitectónica para Interoperabilidad:** La capa de servicios cuenta con contratos de datos preparados para sincronización bidireccional mediante APIs REST o servicios web del MEN, sujeta a la suscripción de los convenios interadministrativos correspondientes.

---

## 9. Integración de Aulas Virtuales Sincrónicas (BigBlueButton)

Para responder a contingencias climáticas, emergencias territoriales o modelos de educación rural híbrida, PEVN incorpora una capa de videoconferencia sincrónica diseñada sobre la plataforma de código abierto **BigBlueButton (BBB)**:

1. **Arquitectura Desacoplada (`IMeetingProvider`):** La plataforma interactúa con los motores de conferencia a través de una interfaz abstracta estándar, implementando el adaptador oficial `BBBAdapter`.
2. **Firma Criptográfica de Enlaces:** Generación segura de llamadas a la API de BigBlueButton firmadas con sumas de comprobación SHA-1 y SHA-256 a partir de secretos institucionales.
3. **Control de Acceso Anclado a la Matrícula:** Únicamente los estudiantes formalmente matriculados en el grupo y la materia pueden unirse como participantes (`Viewer`); el docente asignado ingresa automáticamente con privilegios de moderador (`Moderator`). Estudiantes ajenos al grupo son rechazados con respuesta 403.
4. **Telemetría y Duración de Asistencia:** Registro automático de eventos de conexión (`join`) y desconexión (`leave`), calculando la duración efectiva de asistencia de cada alumno para control pedagógico.
5. **Gestión de Grabaciones:** Sincronización de sesiones grabadas con control de visibilidad en el portal del estudiante.
6. **Declaración Factual de Estado:** La capa de software se encuentra **100% implementada y verificada mediante un proveedor simulado (*Mock Provider*) en las suites de prueba**. Su puesta en marcha en un entorno de producción real **requiere el aprovisionamiento de servidores dedicados BigBlueButton, el balanceador de carga Scalelite y un servidor de relay Coturn (STUN/TURN en puerto TCP 443)** para atravesar cortafuegos escolares y redes rurales bajo CGNAT.

---

## 10. Comunicaciones Institucionales y Acuses de Recibo Electrónicos

PEVN moderniza el canal de divulgación institucional entre la rectoría y la comunidad educativa:

- **Circulares Oficiales Segmentadas:** Emisión de comunicados con filtros de audiencia por sede, jornada, grado escolar, grupo específico o estamento (docentes, estudiantes, acudientes).
- **Acuse de Recibo Electrónico Trazable:** Mecanismo de confirmación de lectura en el portal del acudiente y del estudiante. Cuando el usuario confirma la recepción del comunicado, el sistema registra de forma inmutable la **estampa de tiempo en formato estándar UTC y la dirección IP de origen**.
- **Rigor Terminológico:** En apego a los estándares legales de la Fase 0.1C, este mecanismo se denomina estrictamente *"acuse de recibo electrónico con estampa de tiempo UTC y dirección IP"* o *"registro electrónico trazable de confirmación de lectura"*, evitando el uso de términos inexactos como "firma digital" o "no repudio", los cuales corresponden a marcos normativos específicos de entidades de certificación cerrada.

---

## 11. Convivencia Escolar y Observador del Estudiante (Ley 1620 de 2013)

El módulo de convivencia escolar digitaliza el tradicional Observador del Alumno conforme a los lineamientos de la **Ley 1620 de 2013** (Sistema Nacional de Convivencia Escolar) y su Decreto Reglamentario 1965 de 2013:

1. **Tipificación Canónica de Situaciones:**
   - **Situaciones Tipo I:** Conflictos manejados inadecuadamente y situaciones esporádicas que inciden negativamente en el clima escolar, sin generar daños al cuerpo o a la salud (mediación escolar y acuerdos pedagógicos).
   - **Situaciones Tipo II:** Situaciones de agresión escolar, acoso escolar (*bullying*) o ciberacoso que no revisten las características de la comisión de un delito, pero causan daño a la salud física o psicológica (remisión al Comité de Convivencia y medidas de protección).
   - **Situaciones Tipo III:** Situaciones que presuntamente constituyen la comisión de delitos contra la libertad, integridad y formación sexual, o cualquier otro delito tipificado en la ley penal colombiana (activación inmediata del protocolo intersectorial con ICBF, Comisaría de Familia, Policía de Infancia y Adolescencia y sector salud).
2. **Garantía del Debido Proceso y Formato Restaurativo:** Registro cronológico de los hechos fácticos, versión y descargos del estudiante, medidas formativas adoptadas, compromisos familiares y acuerdos pedagógicos restaurativos con fechas de seguimiento.
3. **Confidencialidad y Reserva Legal Estricta:** Las anotaciones del observador son de carácter reservado. Únicamente son accesibles por el estudiante involucrado, sus acudientes registrados, el docente director de grupo, el coordinador y el rector. Los intentos de acceso por parte de terceros reciben una respuesta `Blind 404`, garantizando la protección del interés superior del menor.

---

## 12. Planeación Curricular y Unidades Didácticas Docentes

El Portal Docente de PEVN integra herramientas para la planeación pedagógica y curricular estructurada:

- **Derechos Básicos de Aprendizaje (DBA) y Estándares del MEN:** Módulo de planeación donde los docentes definen unidades didácticas, objetivos de aprendizaje, competencias ciudadanas y criterios de evaluación articulados con las directrices curriculares nacionales.
- **Cronograma Semanal de Aula:** Organización temporal de contenidos temáticos, actividades pedagógicas y recursos de apoyo vinculados directamente con las tareas y evaluaciones visibles en el portal del estudiante.

---

## 13. Portales Dedicados para la Comunidad Educativa

La plataforma dispone de portales web reactivos e independientes, adaptados a la experiencia de usuario y necesidades de cada rol:

- **Portal del Estudiante (`/student`):** Panel intuitivo que presenta las tareas pendientes con fecha límite y estado de entrega, visor de calificaciones SIEE del período actual con detalle por actividad, registro de asistencias diarias, observador de convivencia formativo, circulares institucionales y acceso directo a clases virtuales programadas.
- **Portal del Acudiente (`/guardian`):** Consola familiar diseñada para el acompañamiento parental con un **selector dinámico de estudiantes**. Si un padre de familia tiene hijos matriculados en diferentes grados o sedes de la institución, puede alternar entre ellos sin cerrar sesión, visualizando alertas tempranas de rendimiento o inasistencia y confirmando acuses de recibo.
- **Portal Docente (`/teacher`):** Entorno de productividad pedagógica: Mis Grupos y Cargas Asignadas, Planilla de Calificaciones SIEE con consolidación automática y justificación de ajustes, Registro de Asistencia Diaria con selector de fecha, Creación de Tareas con recepción de evidencias digitales y Módulo de Planeación Curricular.
- **Consola Directiva de Rectoría y Coordinación (`/academic`):** Tablero de control de la gestión escolar: apertura y configuración de calendarios lectivos, creación de sedes, grados y grupos, asignación de cargas docentes, cierre y sellado de períodos SIEE, emisión de boletines de calificaciones y consolidado general de matrícula.

---

## 14. Arquitectura de Ciberseguridad y Verificación Técnica

PEVN implementa una arquitectura de seguridad por diseño (*Security by Design*) basada en estándares modernos de la industria:

1. **Higiene de Credenciales en Memoria Volátil:** Como medida fundamental de mitigación frente a ataques de robo persistente de credenciales mediante Cross-Site Scripting (XSS), los tokens de acceso JWT **residen exclusivamente en la memoria volátil de JavaScript de React (`AuthContext`)**. No se almacena ningún token en `localStorage`, `sessionStorage` ni `IndexedDB`.
2. **Tokens de Refresco Seguros con Rotación de Familia:** El mantenimiento de sesión se realiza mediante cookies `HttpOnly`, con banderas `SameSite=Strict` y `Secure`. Cada uso del token de refresco emite un nuevo par de credenciales y anula el anterior. Si el sistema detecta la reutilización de un token antiguo (posible ataque de *replay*), se invalida de forma inmediata toda la familia de tokens (`family_id`), cerrando la sesión y generando una alerta de seguridad.
3. **Cifrado Robusto con Argon2id:** Todas las contraseñas de usuarios se procesan mediante el algoritmo **Argon2id** con parámetros de alta resistencia (64 MB de memoria, 3 iteraciones, 16 bytes de sal criptográfica aleatoria), superando los estándares convencionales.
4. **Protección Anti-IDOR (Blind 404):** Todas las consultas verifican la pertenencia del recurso al inquilino del usuario autenticado (`tenant_id`). Las peticiones maliciosas o no autorizadas responden `404 Not Found` en lugar de `403 Forbidden`, evitando ataques de inferencia y enumeración de datos.
5. **Prevención de Inyección SQL y XSS:** Capa de persistencia gobernada por el ORM SQLAlchemy 2.0 con consultas parametrizadas obligatorias. Sanitización estricta de entradas y rechazo binario de archivos ejecutables mediante inspección de firmas de cabecera (*Magic Bytes*).
6. **Trazabilidad Inmutable con Censura de Datos:** Tabla relacional `audit_logs` que registra acciones críticas con dirección IP, agente de usuario y estampa temporal UTC, aplicando censura automática y recursiva (`[REDACTED]`) sobre contraseñas, hashes y datos confidenciales.

---

## 15. Consola Técnica de Diagnóstico de Inquilinos y Auditoría

Para garantizar la supervisión operativa del sistema, la plataforma incluye la consola técnica de **Diagnóstico de Inquilinos** (`/operations/tenant-diagnostics`), accesible exclusivamente por `superadmin` y `national_admin`:

- **Inspección Integral de Salud de la Institución:** Búsqueda en tiempo real de cualquier establecimiento oficial por nombre, código DANE de 12 dígitos o UUID.
- **Métricas de Integridad Operativa:** Conteo en vivo de usuarios activos discriminados por rol, estudiantes matriculados, asignaciones docentes formalizadas, estado de los períodos académicos y lotes de sincronización con el catálogo DANE.
- **Herramientas de Remedición Controlada:** Detección de inconsistencias en la cadena de autoridad o desajustes de alcance territorial con capacidad de análisis forense instantáneo.

---

## 16. Matriz de Clasificación de Capacidades (5 Estados Canónicos)

En estricta conformidad con las directrices de veracidad y transparencia pública, la totalidad de los componentes de PEVN se clasifica bajo los **5 estados canónicos estandarizados**:

| # | Capacidad / Componente | Estado Canónico Oficial | Evidencia Verificable en Repositorio | Justificación y Dependencias |
| :-: | :--- | :---: | :--- | :--- |
| **1** | **Autenticación Argon2id y JWT en Memoria** | `IMPLEMENTED — VERIFIED` | `backend/app/core/security/password.py`, `backend/tests/test_tokens.py` | 100% verificado en tests unitarios e integración. |
| **2** | **Control de Acceso RBAC (11 Roles)** | `IMPLEMENTED — VERIFIED` | `backend/app/services/authorization_service.py`, `test_authorization.py` | Validado en pruebas de backend y frontend con 11 roles activos. |
| **3** | **Aislamiento Multi-Tenant (Anti-IDOR)** | `IMPLEMENTED — VERIFIED` | `backend/app/api/deps.py`, `test_teacher_academic_scope.py` | Enforzado en cada endpoint con respuestas Blind 404. |
| **4** | **Catálogo Oficial DANE / DUE** | `IMPLEMENTED — VERIFIED` | `official_institution_catalog` (18,031 EE), `official_campus_catalog` (51,521) | Base de datos poblada e indexada en PostgreSQL. |
| **5** | **Administrador Municipal (`municipality_admin`)** | `IMPLEMENTED — VERIFIED` | `endpoints/municipality_admin.py`, `MunicipalityAdminsView.tsx` | Ciclo de invitación, activación y limitación territorial funcional. |
| **6** | **Matrícula y Control de Cupos SIMAT** | `IMPLEMENTED — VERIFIED` | `models/enrollment.py`, `test_enrollments_and_assignments.py` | Modelado relacional completo con reglas de capacidad. |
| **7** | **Motor de Evaluación SIEE (D. 1290)** | `IMPLEMENTED — VERIFIED` | `services/evaluation_service.py`, `test_siee_and_evaluations_api.py` | Consolidación híbrida, justificaciones y nivelaciones con tope. |
| **8** | **Asistencia Diaria Docente** | `IMPLEMENTED — VERIFIED` | `DailyAttendance`, `test_teacher_portal_api.py` | Planilla interactiva con persistencia de asistencias y estados. |
| **9** | **Actividades y Entregas Escolares** | `IMPLEMENTED — VERIFIED` | `TeacherActivitiesView.tsx`, `StudentPortalTasksView.tsx` | Estados Borrador/Publicado, entregas de archivo/texto y UTC late flag. |
| **10** | **Comunicaciones y Acuses de Recibo** | `IMPLEMENTED — VERIFIED` | `models/communication.py`, `test_institutional_communications_api.py` | Circulares segmentadas y acuses con timestamp UTC e IP. |
| **11** | **Observador de Convivencia (L. 1620)** | `IMPLEMENTED — VERIFIED` | `models/coexistence_incident.py`, `test_coexistence_incidents_api.py` | Situaciones Tipos I, II, III con debido proceso y reserva legal. |
| **12** | **Planeación Curricular y Didáctica** | `IMPLEMENTED — VERIFIED` | `models/academic_activity.py`, `TeacherCurricularPlanningView.tsx` | Unidades didácticas docentes y vinculación con actividades. |
| **13** | **Portales Estudiante y Acudiente** | `IMPLEMENTED — VERIFIED` | `pages/student/`, `pages/guardian/`, `vitest` (29 suites PASS) | Navegación, visualización de notas y selector dinámico familiar. |
| **14** | **Diagnóstico de Inquilinos (`/operations`)** | `IMPLEMENTED — VERIFIED` | `pages/admin/TenantDiagnosticsView.tsx`, `test_tenant_diagnostics_search.py` | Consola de supervisión con búsqueda DANE y métricas en vivo. |
| **15** | **Auditoría Inmutable (`audit_logs`)** | `IMPLEMENTED — VERIFIED` | `backend/app/audit/database_service.py` | Registro estructurado con censura automática `[REDACTED]`. |
| **16** | **Flujo de Recuperación de Contraseña** | `IMPLEMENTED — VERIFIED` | `PasswordRecovery.tsx`, `test_password_recovery.py` | Generación de tokens y actualización segura de credenciales. |
| **17** | **Generación de Boletines en Web** | `IMPLEMENTED — MANUAL ACCEPTANCE PENDING` | `OfficialReportCard.test.tsx`, `StudentPortalGradesView.tsx` | Visualización en pantalla completada; requiere aceptación visual de formatos. |
| **18** | **Módulo de Periódico Escolar** | `IMPLEMENTED — MANUAL ACCEPTANCE PENDING` | `TeacherCommunicationsAndNews.tsx`, `StudentNewsView.tsx` | Publicación y categorización funcional en espera de validación editorial. |
| **19** | **Almacenamiento de Archivos Local** | `PARTIALLY IMPLEMENTED` | `backend/app/core/storage/service.py` | Opera en almacenamiento particionado en disco; requiere adaptador para S3 en nube. |
| **20** | **Generador Masivo de Boletines PDF** | `PARTIALLY IMPLEMENTED` | `docs/government/pdf/` (motores de exportación) | Requiere integración de cola asíncrona de renderizado para miles de PDFs en lote. |
| **21** | **Aulas Virtuales (BigBlueButton)** | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | `backend/app/core/meeting/bbb_adapter.py`, `test_meeting_provider.py` | Software y firmas listos; requiere servidores físicos BigBlueButton y Coturn TURN. |
| **22** | **Sincronización en Vivo con SIMAT** | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Estructuras de datos compatibles en base de datos | Requiere convenio interadministrativo y acceso a Web Services del MEN. |
| **23** | **Integración de Pasarela OIDC Gov.co** | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Arquitectura desacoplada en `AuthContext` | Requiere convenio de interoperabilidad con MinTIC para Carpeta Ciudadana. |
| **24** | **Servicio de Mensajería SMS / WhatsApp** | `DEPENDENT ON EXTERNAL INFRASTRUCTURE OR AGREEMENT` | Modelo de eventos en `communication.py` | Requiere contratación de pasarela SMS gubernamental o API WhatsApp Business. |
| **25** | **Notificaciones Push en Tiempo Real** | `PROPOSED / NOT YET IMPLEMENTED` | Especificación de eventos en arquitectura | Diseñado para WebSockets / WebPush; no desplegado en versión actual. |
| **26** | **Aplicación Móvil Nativa (Android/iOS)** | `PROPOSED / NOT YET IMPLEMENTED` | Soporte PWA (`vite-plugin-pwa`) implementado | Aplicaciones nativas de tiendas no desarrolladas (opera como PWA responsive). |

---

## 17. Registro Transparente de Limitaciones Técnicas y Operativas

En cumplimiento de los principios de transparencia gubernamental de la Fase 0.1B, se relacionan de forma explícita las limitaciones actuales:

1. **Infraestructura de Videoconferencia:** La integración de BigBlueButton se encuentra programada y verificada mediante un proveedor simulado (*mock*). Su uso en producción requiere que la entidad territorial disponga de servidores dedicados Ubuntu 22.04 LTS y relay Coturn.
2. **Almacenamiento en Clúster:** El gestor de archivos actual almacena evidencias en almacenamiento local particionado; para un despliegue multi-servidor con alta disponibilidad se requiere configurar un bucket S3 o MinIO.
3. **Generación de Boletines en PDF Masivo:** Aunque las notas y sábanas se consultan e imprimen directamente desde la interfaz web, la generación por lotes de miles de archivos PDF en un solo clic para todo un colegio requiere un trabajador en segundo plano (*background worker*) con Celery/Redis.
4. **Pasarela de Correo Electrónico:** La recuperación de contraseñas y notificaciones opera registrando los eventos en base de datos; para envío masivo de correos se requiere enlazar las credenciales del servidor SMTP ministerial.
5. **Pruebas de Estrés a Gran Escala:** La arquitectura de software está diseñada para autoescalado horizontal; sin embargo, las pruebas de concurrencia para cientos de miles de usuarios simultáneos deben realizarse en la infraestructura de computación en la nube que provea el Estado.

---

## 18. Propuesta de Donación y Transferencia Tecnológica al Estado

La presente propuesta se formula bajo las siguientes bases de transferencia soberana:

- **Modelo de Licencia Libre (Apache 2.0):** Se propone la cesión y licenciamiento del software bajo **Apache License, Version 2.0**, otorgando al Estado colombiano la libertad perpetua, irrevocable y no exclusiva de usar, modificar, auditar, desplegar y distribuir la plataforma.
- **Cero Costos de Licenciamiento ($0 COP):** La plataforma no impone cobros de licenciamiento por usuario, estudiante matriculado ni institución educativa.
- **Entrega Integral de Activos de Ingeniería:** El Estado recibiría:
  - Repositorio completo de código fuente (Backend FastAPI y Frontend React).
  - 32 migraciones lineales y determinísticas de base de datos Alembic.
  - Suites completas de pruebas automatizadas (**704 pruebas de backend y 196 pruebas de frontend**).
  - Manual interactivo de usuario, runbooks de despliegue y documentación de arquitectura.
- **Plena Soberanía e Independencia:** El Ministerio o las Secretarías de Educación contarán con total autonomía para alojar la plataforma en sus propios centros de datos o en la nube pública de su elección, asumiendo su operación directamente o contratando soporte con terceros sin cautiverio de proveedor (*no vendor lock-in*).

---

## 19. Hoja de Ruta Recomendada para Despliegue en Tres Fases

Para una adopción técnica controlada, segura y con mitigación de riesgos, se propone un cronograma estructurado en tres fases:

```
FASE 1: PILOTO CONTROLADO ──────► FASE 2: EXPANSIÓN TERRITORIAL ──────► FASE 3: ESCALAMIENTO NACIONAL
(10 a 12 semanas)                 (6 meses)                            (Gradual / 1 a 2 años)
• 5 a 10 Colegios Oficiales       • 50 a 100 Colegios Oficiales        • Adopción en 97 ETC
• 2 Municipios (Urbano y Rural)   • 1 Departamento Certificado         • Enlace en vivo SIMAT / MinTIC
• Validación SIEE y Docente       • Servidores BBB y Coturn en vivo    • Nube Pública Gubernamental
```

- **Fase 1 (Piloto Inicial Controlado - 10 a 12 semanas):** Implementación en 5 a 10 instituciones educativas oficiales de dos municipios (uno urbano y uno rural) durante un período escolar. Validación empírica de la usabilidad docente, adopción del portal familiar, estabilidad de la planilla SIEE y comportamiento en redes de baja conectividad.
- **Fase 2 (Expansión Departamental - 6 meses):** Ampliación a 50 a 100 colegios oficiales de una Secretaría de Educación Departamental certificada. Puesta en marcha de infraestructura física BigBlueButton y Coturn, integración de almacenamiento en nube y pruebas de carga con hasta 10,000 usuarios concurrentes.
- **Fase 3 (Escalamiento y Adopción Nacional):** Despliegue en clúster Kubernetes de la infraestructura de computación pública del Estado, suscripción de acuerdos de sincronización con SIMAT y enlace con Carpeta Ciudadana (Gov.co), ofreciendo PEVN como un servicio digital público a las 97 Secretarías de Educación Certificadas del país.

---

## 20. Descargos Institucionales y Protección de Datos Personales

1. **Entorno de Pruebas y Datos Demostrativos:** Todas las demostraciones, capturas de pantalla, registros de prueba y datos expuestos en este dossier corresponden a **datos de demostración del entorno de pruebas, no correspondientes a un entorno productivo**.
2. **Cumplimiento de la Ley 1581 de 2012 y Ley 1098 de 2006:** En estricta observancia del Régimen General de Protección de Datos Personales (Ley 1581 de 2012) y del Código de la Infancia y la Adolescencia (Ley 1098 de 2006), **ningún dato personal real ni sensible de menores de edad ha sido utilizado, procesado ni expuesto en el desarrollo de estas evaluaciones**.
3. **Carácter No Vinculante:** La presentación de este expediente no constituye aceptación tácita ni expresa por parte de las entidades públicas receptoras, quedando cualquier avance sujeto a los marcos de contratación estatal, convenios de cooperación o voluntades administrativas que la ley colombiana establece.
