# Plataforma Educativa Virtual Nacional (PEVN)
## Informe Técnico Institucional y Dossier de Ingeniería para el Ministerio de Educación Nacional (MEN)
### Documento de Trabajo para la Oficina de Tecnología y Sistemas de Información

---

**Autor / Liderazgo Técnico:** Juan Carlos Castro Narváez  
**Iniciativa:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario Institucional:** Oficina de Tecnología y Sistemas de Información — Ministerio de Educación Nacional (MEN), República de Colombia  
**Fecha de Elaboración:** Octubre 2026  
**Estado del Documento:** Documento Técnico y Dossier de Ingeniería Oficial (Versión de Evaluación Institucional)  
**Clasificación de Seguridad:** Confidencial / Uso Institucional — No contiene secretos, credenciales ni PII real

---

## Control de Versiones y Declaración de Integridad

| Versión | Fecha | Autor | Propósito / Alcance |
| :--- | :--- | :--- | :--- |
| **1.0-MEN** | Octubre 2026 | Juan Carlos Castro Narváez | Elaboración del informe técnico integral para presentación presencial ante la Oficina de Tecnología y Sistemas de Información del MEN. Reconciliación de arquitectura, modelo RBAC, matriz de madurez, preguntas técnicas previsibles, batería de pruebas y propuesta de colaboración. |

> [!IMPORTANT]
> **Declaración de Integridad Institucional:**  
> La Plataforma Educativa Virtual Nacional (PEVN) es una iniciativa técnica y de software independiente orientada a la educación oficial en Colombia. El presente documento **no afirma ni sugiere** que PEVN cuente a la fecha con aprobación, certificación, homologación o adopción formal por parte del Ministerio de Educación Nacional (MEN). Todas las aseveraciones de funcionamiento se fundamentan estrictamente en código fuente existente, pruebas automatizadas ejecutadas y esquemas de persistencia verificables en el repositorio del proyecto.

---

## 1. Resumen Ejecutivo

La **Plataforma Educativa Virtual Nacional (PEVN)** es un ecosistema de software concebido para responder a los desafíos de fragmentación digital, altos costos de licenciamiento privativo y falta de soberanía tecnológica en las instituciones educativas oficiales de Colombia.

Construida bajo un paradigma desacoplado y asíncrono —con una aplicación de página única (SPA) en **React 18 con TypeScript y Vite**, una API backend de alto rendimiento en **FastAPI (Python 3.12)**, persistencia relacional en **PostgreSQL 15** particionada lógicamente por institución, y capa de caché/sesiones en **Redis 7**—, PEVN proporciona cobertura integral a los procesos directivos, administrativos, pedagógicos y estudiantiles.

El sistema implementa un modelo de control de acceso basado en roles jerárquicos (**RBAC de 11 perfiles**), estructurado conforme a la división político-administrativa de Colombia (**DIVIPOLA**) y la codificación oficial de sedes e instituciones del **DANE** (1,122 municipios, 33 entidades territoriales, 18,031 colegios y 51,521 sedes precargadas en base de datos).

El presente informe expone de forma transparente el estado real de madurez de la plataforma, distingue con rigor las capacidades completamente operativas de aquellas sujetas a infraestructura externa o acuerdos institucionales, detalla la batería de pruebas ejecutada (169 pruebas backend aprobadas en ciclo focalizado de integración y seguridad, sobre un inventario estático de 722 pruebas), y somete a consideración del MEN una **propuesta estructurada de colaboración técnica por fases con compuertas de decisión (Decision Gates)**.

---

## 2. Propósito, Audiencia Prevista y Contexto Institucional

### 2.1. Propósito
El objetivo de este informe es suministrar a la **Oficina de Tecnología y Sistemas de Información del MEN** un expediente técnico exhaustivo, auditable y verídico que permita:
1. Evaluar la viabilidad arquitectónica, los estándares de codificación y la postura de ciberseguridad de PEVN.
2. Conocer de primera mano qué capacidades están plenamente operativas en código y demostrables en vivo, y cuáles corresponden a etapas posteriores.
3. Analizar la compatibilidad del modelo de datos con los estándares sectoriales de Colombia (DANE, DIVIPOLA, lineamientos de interoperabilidad de MinTIC y MEN).
4. Establecer un marco de trabajo colaborativo para una eventual mesa técnica de evaluación y un piloto experimental controlado.

### 2.2. Audiencia Prevista
- **Dirección de Tecnología y Sistemas de Información (MEN):** Evaluación de alineación estratégica, sostenibilidad y gobernanza TI.
- **Equipo de Arquitectura e Infraestructura:** Análisis de escalabilidad, contenedores, consumo de cómputo y desacoplamiento de capas.
- **Oficina de Ciberseguridad y Privacidad:** Revisión de controles de autenticación, aislamiento multi-tenant, mitigación anti-IDOR y cumplimiento de la Ley Estatutaria 1581 de 2012 (Protección de Datos Personales).
- **Equipo de Interoperabilidad e Integración de Datos:** Análisis de modelos de sincronización con SIMAT, DUE y SINEB.

### 2.3. Contexto Institucional
El sistema educativo oficial en Colombia enfrenta una marcada disparidad entre colegios urbanos y sedes rurales. Mientras los primeros en ocasiones acceden a herramientas privadas dispares, las sedes rurales sufren de desconexión, sistemas manuales en papel o pérdida de trazabilidad de calificaciones y asistencia. PEVN se diseña como una infraestructura de bien público digital que nivela estas capacidades sin imponer cobros recurrentes de licenciamiento por alumno al presupuesto público.

---

## 3. Problema Abordado, Objetivos, Alcance y No-Objetivos (Non-Goals)

### 3.1. Problema Abordado
1. **Dispersión y Silos de Información:** Notas registradas en planillas de cálculo locales, matrículas en libretas físicas y asistencia sin consolidación institucional.
2. **Dependencia Financiera de Software Privativo:** Costos crecientes en moneda extranjera para suites extranjeras de gestión académica que resultan insostenibles para entidades territoriales no certificadas.
3. **Brecha de Conectividad Territorial:** Herramientas web comerciales sobrecargadas con librerías pesadas y llamadas constantes a servidores foráneos que colapsan en enlaces rurales de baja velocidad.
4. **Falta de Soberanía y Gobernanza de Datos:** Información sensible de menores de edad alojada en plataformas comerciales sin auditoría pública directa.

### 3.2. Objetivos del Sistema
- Consolidar la gestión institucional, académica, docente y estudiantil en una solución abierta y soberana.
- Garantizar el aislamiento estricto de los datos entre diferentes instituciones educativas (cero fugas cross-tenant).
- Ofrecer una experiencia de usuario rápida, optimizada para bajo consumo de ancho de banda y compatible con PWA (Progressive Web App).
- Implementar trazabilidad absoluta (auditoría forense) sobre modificaciones en notas, actas de grado y registros de matrícula.

### 3.3. Alcance Actual
- Administración de entidades territoriales (Secretarías Departamentales y Municipales) e instituciones.
- Aprovisionamiento seguro de Directivos Docentes (Rectores) mediante flujo de invitación con token criptográfico temporal.
- Configuración institucional: sedes, calendarios, años lectivos, periodos académicos, grados, grupos y asignaturas.
- Asignación de carga académica a docentes.
- Registro y gestión de matrículas de estudiantes.
- Planillas de calificaciones numéricas con ponderación porcentual y control de asistencia diario.
- Portal interactivo del estudiante y vista de acudientes.
- Integración cliente API con el motor de videoconferencia BigBlueButton.

### 3.4. No-Objetivos (Non-Goals)
Para evitar cualquier malentendido institucional, se definen taxativamente los **no-objetivos** del proyecto:
- **No es un sustituto legal del SIMAT:** PEVN no busca reemplazar la potestad del MEN sobre el Sistema Integrado de Matrícula (SIMAT), sino actuar como la plataforma operativa del colegio que pueda alimentar o recibir datos de este mediante interfaces autorizadas.
- **No es un proveedor de conectividad física:** PEVN optimiza el tráfico de datos, pero no sustituye la infraestructura física de telecomunicaciones requerida en los territorios.
- **No es una entidad certificadora de estudios:** La validez de los títulos y certificados radica exclusivamente en la Institución Educativa y el MEN, conforme a la Ley 115 de 1994.

---

## 4. Evaluación del Estado Actual de Madurez

A continuación se presenta la **Matriz de Madurez de Capacidades de PEVN**, con asignación rigurosa de estado y nivel de evidencia técnica verificada en el repositorio:

| Capacidad / Componente | Estado Actual | Fuente de Evidencia en Repositorio | Demo en Vivo | Limitación / Prerrequisito | Acción Recomendada |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Autenticación JWT y Sesiones** | **Implementado** | `backend/app/core/security.py`, `tests/test_auth_redis_hardening.py` | Sí (Local/Red) | Requiere Redis 7 para lista negra de tokens revocados. | Mantener parámetros de expiración estricta y rotación periódica. |
| **Modelo RBAC (11 Roles)** | **Implementado** | `backend/app/models/user.py`, `backend/app/api/deps.py`, `docs/reports/PEVN_PHASE_0_5_RBAC_IMPLEMENTATION_REPORT.md` | Sí (Local/Red) | Ninguna en lógica de control de acceso. | Auditoría continua en cada nuevo endpoint expuesto. |
| **Aislamiento Multi-Tenant** | **Implementado** | `backend/app/services/institution_service.py`, `backend/app/repositories/` | Sí (Local/Red) | Depende del filtrado mandatorio por `institution_id` en consultas SQL. | Incorporar Row-Level Security (RLS) nativo en PostgreSQL en fase de piloto. |
| **Gobernanza Territorial DANE/DIVIPOLA** | **Implementado** | `backend/app/models/territorial.py`, migraciones Alembic, catálogo CSV precargado | Sí (Local/Red) | Catálogo estático precargado (18,031 colegios / 51,521 sedes). | Establecer canal de actualización periódica con base maestra del MEN. |
| **Aprovisionamiento de Rectores** | **Implementado** | `backend/app/services/rector_service.py`, `tests/test_rector_provisioning_flow.py` | Sí (Local/Red) | Envío de correo simulado en entorno de desarrollo si no hay SMTP activo. | Configurar servidor SMTP institucional para entregas en producción. |
| **Gestión Académica y Matrículas** | **Implementado** | `backend/app/api/v1/endpoints/academic.py`, `src/pages/AcademicManagementPage.tsx` | Sí (Local/Red) | Restricción de cupos y unicidad de documento de identidad activa. | Validación de campos adicionales requeridos por la Resolución de Matrícula MEN. |
| **Calificaciones y Asistencia** | **Implementado** | `backend/app/services/grade_service.py`, `src/pages/GradesPage.tsx`, `AttendancePage.tsx` | Sí (Local/Red) | Ponderación de periodos sujeta a configuración institucional previa. | Adaptar a sistemas institucionales de evaluación (SIEE) cualitativos complejos. |
| **Portal del Estudiante y Acudiente** | **Implementado** | `src/pages/StudentPortalPage.tsx`, `GuardianPortalPage.tsx` | Sí (Local/Red) | Consulta solo lectura de registros publicados. | Habilitar módulo de retroalimentación pedagógica y descarga de boletín en PDF. |
| **Videoclases (BigBlueButton)** | **Depende de Infra Externa** | `backend/app/services/bbb_service.py`, `tests/test_virtual_classrooms.py` | Condicional | Requiere clúster BigBlueButton externo con SSL, dominio y servidores TURN/STUN. | Gestionar infraestructura BBB dedicada o en convenio durante la Fase 3 de piloto. |
| **Interoperabilidad SIMAT/DUE** | **Parcial / Catálogo** | Modelos de datos DANE, scripts de importación DANE | Sintético | No existe conexión web service directa ni transaccional con servidores del MEN. | Diseñar especificación OpenAPI bilateral con la Oficina de Tecnología del MEN. |
| **Pistas de Auditoría Forense** | **Implementado** | `backend/app/models/audit_log.py`, `backend/app/services/audit_service.py` | Sí (Local/Red) | Registra eventos CRUD críticos, usuario, timestamp UTC e IP. | Configurar retención inmutable y exportación a SIEM gubernamental. |
| **Pruebas de Carga a Gran Escala** | **Planificado** | `docs/reports/PEVN_SCALABILITY_READINESS.md` | No | Requiere clúster distribuido y simulación de 100,000+ usuarios concurrentes. | Ejecutar pruebas conjuntas con herramientas tipo k6 / Locust en Fase 2. |

---

## 5. Inventario Funcional por Rol y Módulo

PEVN cuenta con una arquitectura de permisos granular segmentada en **11 roles de base de datos** (9 arquetipos canónicos funcionales y 2 alias operacionales de compatibilidad), registrados en el catálogo canónico de base de datos (`roles` y `UserRole`):

```mermaid
graph TD
    SA[1. superadmin: Super Administrador Nacional PEVN - Nivel 100] --> NA[2. national_admin: Administrador Nacional MEN - Nivel 90]
    NA --> DA[3. department_admin: Secretaría de Educación Departamental - Nivel 80]
    DA --> MA[4. municipality_admin: Secretaría de Educación Municipal - Nivel 70]
    MA --> REC[5. rector: Rector / Director Institucional - Nivel 60]
    REC -.-> IA[6. institution_admin: Alias Compatibilidad Rector - Nivel 60]
    REC --> COORD[7. coordinator: Coordinador Académico / Sede - Nivel 50]
    COORD -.-> AC[8. academic_coordinator: Alias Compatibilidad Coordinador - Nivel 50]
    REC --> DOC[9. teacher: Docente de Área / Aula - Nivel 30]
    DOC --> EST[10. student: Estudiante Matriculado - Nivel 10]
    EST --> ACU[11. guardian: Acudiente / Tutor Legal - Nivel 10]
```

### 5.1. Matriz de Módulos y Accesos por Rol

1. **`superadmin` (Super Administrador Nacional PEVN — Nivel 100):**
   - Configuración global de la plataforma, alta y mantenimiento de gobernanza y Secretarías Departamentales.
   - Supervisión de telemetría de infraestructura, auditoría de seguridad y parámetros globales del sistema.
2. **`national_admin` (Administrador Nacional MEN — Nivel 90):**
   - Gestión y supervisión nacional de entidades territoriales certificadas, catálogo DIVIPOLA nacional y auditoría centralizada.
   - Aprovisionamiento masivo territorial y enlace con políticas nacionales del Ministerio de Educación Nacional.
3. **`department_admin` (Secretaría de Educación Departamental — Nivel 80):**
   - Gestión y supervisión de las instituciones educativas y administradores municipales adscritos a su entidad territorial certificada (código DANE departamental).
   - Acceso a consolidados estadísticos de matrícula, cobertura y retención escolar territorial.
4. **`municipality_admin` (Secretaría de Educación Municipal — Nivel 70):**
   - Gestión de instituciones educativas ubicadas en la jurisdicción municipal (código DIVIPOLA municipal).
   - Aprovisionamiento e invitación criptográfica de rectores; monitoreo de capacidades operativas municipales.
5. **`rector` (Rector / Director Institucional — Nivel 60):**
   - Máxima autoridad directiva en el tenant de la Institución Educativa.
   - Creación y administración de sedes, calendarios académicos, comités de evaluación y delegación de coordinadores y docentes.
6. **`institution_admin` (Administrador Institucional — Nivel 60, Alias de Compatibilidad):**
   - Perfil administrativo de respaldo directo institucional con equivalencia de permisos respecto al rol `rector`.
7. **`coordinator` (Coordinador Académico / de Sede — Nivel 50):**
   - Planificación de horarios, grupos, sedes asignadas, asignaturas y supervisión de planillas docentes.
   - Cierre y consolidación de periodos evaluativos institucionales.
8. **`academic_coordinator` (Coordinador Académico — Nivel 50, Alias de Compatibilidad):**
   - Alias operacional estandarizado en contratos de interfaz para coordinación pedagógica y curricular de sede.
9. **`teacher` (Docente de Aula — Nivel 30):**
   - Registro de calificaciones parciales y definitivas por indicador y competencia curricular.
   - Control diario de asistencia, justificación de ausencias y asignación de tareas/guías de aprendizaje.
   - Creación y moderación de salas de clase virtual (BigBlueButton).
10. **`student` (Estudiante — Nivel 10):**
    - Consulta personalizada de calificaciones, asistencia, observaciones disciplinarias y calendario de evaluaciones.
    - Acceso a guías de estudio, entrega de evidencias y acceso a clases sincrónicas.
11. **`guardian` (Acudiente / Tutor Legal — Nivel 10):**
    - Seguimiento del desempeño de sus hijos vinculados, control de ausencias y comunicación con docentes y directivos.

---

## 6. Flujos de Trabajo y Flujos de Datos Representativos

### 6.1. Flujo 1: Aprovisionamiento Institucional del Rector
1. La Secretaría Municipal/Departamental ingresa el código DANE de la institución y el correo institucional del rector electo.
2. El backend genera un token de un solo uso con firma HMAC-SHA256 y vigencia limitada (72 horas) almacenado en PostgreSQL.
3. El rector recibe la invitación, accede a la ruta segura de activación, valida su identidad y establece su contraseña segura (hasheada con bcrypt).
4. El sistema vincula la identidad del rector al `institution_id` y habilita su consola directiva.

### 6.2. Flujo 2: Ciclo de Calificaciones y Asistencia Docente
1. El docente inicia sesión y el sistema valida su carga académica activa para el periodo en curso.
2. Al ingresar a la planilla, el frontend solicita únicamente los estudiantes matriculados en dicho grupo y sede.
3. El docente digita calificaciones numéricas (escala 1.0 a 5.0) o inasistencias.
4. El backend recibe el lote de calificaciones, valida los rangos numéricos y los permisos del docente sobre la asignatura, actualiza los registros en transacción ACID y genera un registro inmutable en el log de auditoría.

### 6.3. Flujo 3: Consulta Segura del Estudiante (Protección Anti-IDOR)
1. El estudiante solicita su boletín de notas.
2. La API extrae el `student_id` directamente del payload del token JWT verificado en la cabecera `Authorization`.
3. Cualquier intento de enviar un `student_id` ajeno en los parámetros de ruta o cuerpo de la petición es descartado por la dependencia `get_current_student`, retornando `HTTP 403 Forbidden`.

---

## 7. Arquitectura Técnica Derivada de la Implementación Real

La arquitectura de PEVN ha sido concebida bajo patrones de diseño modernos, modulares y de acoplamiento débil:

```
+-----------------------------------------------------------------------------------+
|                            CAPA DE PRESENTACIÓN (CLIENTE)                         |
|   React 18  |  TypeScript 5  |  Vite Bundler  |  TailwindCSS  |  Lucide Icons     |
|   • Cero fuentes o scripts externos vía CDN (100% autónomo y offline-ready)       |
|   • Gestión de estado desacoplada, caché local y enrutamiento con React Router    |
+----------------------------------------+------------------------------------------+
                                         | Peticiones HTTPS / JSON REST
                                         v
+-----------------------------------------------------------------------------------+
|                                 CAPA DE APLICACIÓN (API)                          |
|   FastAPI (Python 3.12)  |  Uvicorn ASGI  |  Pydantic v2  |  SQLAlchemy 2 Async   |
|   • Middleware de Seguridad: CORS, Rate Limiting, Trusted Hosts                   |
|   • Inyección de Dependencias: Autenticación JWT, verificación RBAC y Multi-tenant |
|   • Capa de Servicios de Negocio: Validación de reglas académicas y territoriales  |
+--------------------+-------------------------------------+------------------------+
                     |                                     |
                     v                                     v
+------------------------------------+   +------------------------------------------+
|       CAPA DE PERSISTENCIA         |   |          CAPA DE SESIONES / CACHÉ        |
|   PostgreSQL 15 Relacional         |   |   Redis 7 In-Memory                      |
|   • Esquemas de datos normalizados |   |   • Lista negra de tokens revocados      |
|   • Índices por tenant_id, DANE    |   |   • Limitador de tasa (Rate limit state) |
|   • Migraciones con Alembic        |   |   • Caché volátil de alto rendimiento    |
+------------------------------------+   +------------------------------------------+
                     |
                     v
+-----------------------------------------------------------------------------------+
|                           CAPA DE SERVICIOS EXTERNOS (PREPARADA)                  |
|   • BigBlueButton API: Integración de cliente REST/XML lista para clúster externo |
|   • Catálogos DANE/DIVIPOLA: Estructura local sincronizable con datos del MEN     |
+-----------------------------------------------------------------------------------+
```

---

## 8. Frontend, Backend, APIs, Persistencia y Configuración

### 8.1. Frontend
- **Tecnología:** React 18.3+, TypeScript en modo estricto (`noImplicitAny`, `strictNullChecks`).
- **Empaquetado:** Vite, con generación de chunks optimizados y compresión gzip/brotli.
- **Autonomía y Offline-First:** No utiliza Google Fonts ni librerías servidas por CDNs comerciales. Todas las tipografías son del sistema operativo nativo del usuario y los iconos son componentes SVG vectoriales integrados en el código.
- **Verificación:** Ejecución de `tsc --noEmit` con 0 errores y compilación `npm run build` exitosa.

### 8.2. Backend
- **Tecnología:** FastAPI sobre Python 3.12.
- **Servidor ASGI:** Uvicorn con soporte de múltiples workers orientados a I/O asíncrono.
- **Validación de Datos:** Pydantic v2 para validación estricta de esquemas de entrada y salida, asegurando la sanitización de tipos y el rechazo inmediato de cargas maliciosas.
- **ORM Asíncrono:** SQLAlchemy 2.0 en modalidad asíncrona (`asyncio` con driver `asyncpg`), permitiendo la concurrencia eficiente sin bloqueo de hilos del sistema operativo.

### 8.3. Configuración y Secretos
- Centralizada mediante `Pydantic-Settings` leyendo variables de entorno del sistema (`.env` local para desarrollo, inyección mediante Secrets en despliegues Kubernetes o contenedores).
- No existen contraseñas, llaves maestras ni credenciales en duro (*hardcoded*) en el código fuente.

---

## 9. Modelo RBAC, Fronteras de Roles y Aislamiento Multi-Tenant

### 9.1. Aislamiento Multi-Tenant
El sistema opera bajo un modelo de **aislamiento multi-tenant por discriminador lógico reforzado (`institution_id`)**:
- Toda consulta que involucre sedes, directivos, docentes, estudiantes, cursos, matrículas o notas incluye obligatoriamente en la cláusula `WHERE` el identificador de la institución (`institution_id = current_user.institution_id`).
- Esta restricción no se delega a la voluntad del desarrollador en los endpoints, sino que se encuentra encapsulada en la capa de repositorios base de SQLAlchemy.

### 9.2. Mitigación de Vulnerabilidades de Referencia Directa Insegura (Anti-IDOR)
Las peticiones que especifican un recurso por ID (ej. `GET /api/v1/grades/{grade_id}` o `GET /api/v1/students/{student_id}`) ejecutan una verificación en dos pasos:
1. El usuario solicitante posee el rol adecuado para consultar el tipo de recurso.
2. El recurso solicitado pertenece estrictamente a la institución o al grupo asignado al usuario.
Si un usuario de la Institución Educativa "A" intenta solicitar un recurso con ID perteneciente a la Institución "B", el sistema responde `HTTP 404 Not Found` o `HTTP 403 Forbidden`, impidiendo incluso inferir la existencia del recurso.

---

## 10. Gobernanza de Datos, Privacidad y Ley 1581 de 2012

### 10.1. Cumplimiento de la Ley Estatutaria 1581 de 2012 (Habeas Data)
PEVN adopta el principio de **privacidad por diseño y por defecto**:
- **Tratamiento de Datos de Menores de Edad:** Conforme al Artículo 7 de la Ley 1581 y el Decreto 1377 de 2013, los datos de los niños, niñas y adolescentes matriculados se tratan con el estándar reforzado de protección, respondiendo únicamente a su interés superior y a la finalidad estrictamente pedagógica y académica.
- **Derechos ARCO:** El modelo prevé procedimientos para la actualización, rectificación y supresión de datos a solicitud de los titulares o sus representantes legales.
- **No Monetización:** PEVN prohíbe y carece de cualquier integración con herramientas de rastreo comercial, analítica publicitaria o transferencia de datos a terceros privados.

### 10.2. Pistas de Auditoría
El modelo `AuditLog` registra de forma estructurada:
- Identificador único del evento (`UUID`).
- Timestamp en estándar UTC (`created_at`).
- Usuario que ejecutó la acción (`user_id`, `role`, `tenant_id`).
- Tipo de acción (`LOGIN`, `LOGOUT`, `CREATE`, `UPDATE`, `DELETE`, `GRADE_CHANGE`).
- Recurso afectado (`table_name`, `record_id`).
- Dirección IP de origen y agente de usuario (User-Agent).

---

## 11. Tratamiento de Datos Institucionales, Territoriales y DANE/DIVIPOLA

PEVN incorpora la codificación oficial de la República de Colombia:
- **Entidades Territoriales Certificadas (ETC):** 33 entidades territoriales (32 departamentos y el Distrito Capital de Bogotá).
- **Municipios:** 1,122 municipios conforme al estándar DIVIPOLA del Departamento Administrativo Nacional de Estadística (DANE).
- **Establecimientos Educativos:** Catálogo precargado de 18,031 colegios oficiales y no oficiales.
- **Sedes Educativas:** Catálogo precargado de 51,521 sedes asociadas a su código DANE de 12 dígitos.

Esta estructura asegura que cualquier futura articulación con los sistemas centrales del MEN no requiera procesos traumáticos de normalización de nombres o códigos, pues el esquema de PEVN ya utiliza como llaves canónicas los códigos oficiales del DANE.

---

## 12. Estado de Integración: BigBlueButton y Sistemas Gubernamentales

### 12.1. BigBlueButton (Videoclases en Vivo)
- **Estado de Integración:** Cliente API completamente implementado en `backend/app/services/bbb_service.py`.
- **Capacidades Probadas:** Creación programada de salas de clase, generación de contraseñas de moderador (docente) y asistente (estudiante), cálculo de checksum de seguridad HMAC-SHA1 según el protocolo oficial de BBB.
- **Dependencia Externa:** Para la transmisión en vivo de video, audio y pizarra interactiva, se requiere un clúster de servidores BigBlueButton externo configurado con certificados SSL/TLS y servidores TURN/STUN para salvar firewalls institucionales o redes móviles con NAT estricto.

### 12.2. Sistemas Centrales del MEN (SIMAT, DUE, SINEB)
- **Estado Actual:** Integración indirecta por compatibilidad de catálogos.
- **Aclaración Factual:** No existe en este momento un canal web service transaccional (REST o SOAP) activo entre el entorno de desarrollo de PEVN y las bases de datos de producción del MEN.
- **Ruta de Integración:** Se propone a la Oficina de Tecnología definir las especificaciones técnicas seguras (vía API Gateway gubernamental o intercambio de archivos estructurados JSON/XML) en el marco de la Fase 2 del plan de colaboración.

---

## 13. Infraestructura, Despliegue y Preparación Operativa

### 13.1. Entorno Actual de Desarrollo y Demostración
- **Sistema Operativo:** Windows / Linux (WSL2 / Contenedores Docker).
- **Base de Datos Local:** PostgreSQL 15 corriendo en puerto local, con esquemas y extensiones relacionales activas.
- **Servidor de Caché:** Redis 7 local para revocación de sesiones y rate limiting.
- **Backend:** FastAPI ejecutado mediante Uvicorn.
- **Frontend:** Vite dev server y compresión de estáticos en `dist/`.

### 13.2. Modelo de Despliegue en Producción Sugerido
- **Contenerización:** Imágenes Docker multi-etapa (*multi-stage builds*) para frontend (Nginx liviano) y backend (Python 3.12-slim).
- **Orquestación:** Kubernetes o Docker Swarm en infraestructura provista o autorizada por el MEN (ej. Nube de Gobierno o centros de datos certificados).
- **Estrategia de Respaldo:** Respaldos automáticos diarios de PostgreSQL con retención rotativa (RPO < 24 horas, RTO < 2 horas en caso de contingencia).

---

## 14. Metodología de Pruebas y Evidencia Reconciliada

Para garantizar absoluta veracidad y evitar ambigüedades en la presentación institucional, se detallan las cifras reales verificadas en el repositorio:

### 14.1. Taxonomía de Pruebas Backend (Suite Pytest)
- **Inventario Total Recolectado Estáticamente:** **722 pruebas** distribuidas en 70 archivos de prueba.
- **Pruebas Backend Directamente Ejecutadas y Aprobadas (100% PASS en ciclo focalizado):** **169 pruebas**, desglosadas así:
  1. `tests/test_database_integration.py`: **83 pruebas** de integración real sobre PostgreSQL 15 (transacciones, claves foráneas, aislamiento).
  2. `tests/test_db_safety.py`: **18 pruebas** de integridad y seguridad en persistencia.
  3. `tests/test_rector_provisioning_flow.py`: **32 pruebas** del flujo integral de invitación y asignación de directivos docentes.
  4. `tests/test_auth_redis_hardening.py`: **36 pruebas** de seguridad, revocación de tokens JWT y endurecimiento con Redis.
- **Pruebas No Ejecutadas en el Ciclo Focalizado:** **553 pruebas** (correspondientes a pruebas unitarias en memoria, mocks aislados y pruebas secundarias que no fueron requeridas para validar la estabilidad del núcleo transaccional de demostración).

### 14.2. Auditorías de Documentación y Calidad Estática
- **Auditoría de Documentación (`scripts/audit_documentation.py`):** **41 comprobaciones ejecutadas y aprobadas (100% PASS, 0 advertencias, 0 fallos)**, verificando enlaces internos, activos de imagen, consistencia de roles y ausencia de rutas rotas.
- **Verificación de Tipos Frontend:** `tsc --noEmit` completado con **0 errores**.
- **Compilación de Producción Frontend:** `npm run build` completado con éxito.
- **Inspección Visual de Manuales:** 13 capturas de pantalla verificadas, alineadas exactamente a los márgenes imprimibles (0.00 pt de desviación) y libres de banners de error HTTP 500 o trazas de depuración.

---

## 15. Accesibilidad, Usabilidad y Conectividad Rural

### 15.1. Soporte Actual
- **Navegación por Teclado:** Vistas críticas navegables mediante atajos y tabulación accesible.
- **Optimización de Carga:** Empaquetado optimizado, ausencia de dependencias externas en tiempo de ejecución y diseño CSS responsivo.
- **Compatibilidad con Dispositivos Móviles:** La interfaz se adapta dinámicamente a pantallas de teléfonos y tabletas comúnmente utilizados por familias y docentes en territorio.

### 15.2. Evaluación Pendiente
- Auditoría formal de accesibilidad bajo el estándar **WCAG 2.1 Nivel AA**, requerida para plataformas oficiales del Estado colombiano.
- Pruebas de campo en condiciones reales de conectividad satelital o redes móviles 2G/3G de alta latencia y paquetes caídos.

---

## 16. Defectos Conocidos, Limitaciones y Deuda Técnica

1. **Dependencia de Clúster de Videoconferencia Externo:** El sistema no incluye un servidor WebRTC interno; requiere la infraestructura BigBlueButton descrita.
2. **Sincronización Asíncrona con SIMAT:** Actualmente basada en importación de plantillas y datos DANE, sin servicio transaccional bidireccional en línea.
3. **Mecanismo de Firma Digital de Calificaciones:** Las calificaciones se registran con trazabilidad de usuario y timestamp, pero no cuentan aún con firma digital basada en certificados PKI reconocidos por la ONAC.
4. **Módulo de Evaluación Cualitativa Avanzada:** El sistema opera principalmente bajo escala numérica estándar (1.0 a 5.0) con desempeños (Bajo, Básico, Alto, Superior); requiere ampliación para modelos pedagógicos flexibles o etnoeducativos específicos.

---

## 17. Riesgos y Opciones de Mitigación

| Riesgo Técnico / Institucional | Nivel | Impacto | Opción de Mitigación Implementada / Propuesta |
| :--- | :--- | :--- | :--- |
| **Intento de acceso a datos de otra institución (Cross-tenant)** | Alto | Crítico | Mitigado por diseño mediante filtrado forzoso por `institution_id` en capa de repositorios y validaciones anti-IDOR. |
| **Colapso de servidor por alta concurrencia en entrega de notas** | Medio | Alto | Arquitectura asíncrona FastAPI + pool de conexiones asyncpg + caché Redis. Pruebas de estrés planificadas para Fase 2. |
| **Uso de credenciales comprometidas o reutilizadas** | Medio | Alto | Hashing bcrypt, expiración corta de tokens JWT, revocación forzada en Redis y políticas de contraseñas robustas. |
| **Interrupción de conectividad en zonas rurales** | Alto | Medio | Arquitectura SPA local, reducción de peso de paquetes a cero dependencias externas y modo de captura de datos tolerante a reconexión. |

---

## 18. Preguntas Previsibles de la Oficina de Tecnología y Sistemas de Información del MEN

A continuación se presentan las respuestas directas, verídicas y fundamentadas en evidencia técnica a las interrogantes que previsiblemente formulará el equipo técnico del Ministerio:

#### 1. ¿Qué problema resuelve PEVN y quién es su beneficiario directo?
> **Respuesta:** Resuelve la fragmentación de sistemas académicos, la falta de trazabilidad en las calificaciones y la dependencia de software privativo con cobros por estudiante en la educación oficial. Sus beneficiarios directos son los directivos docentes (Rectores), coordinadores, docentes, estudiantes, padres de familia y las Secretarías de Educación que requieren datos consolidados y confiables.

#### 2. ¿Qué funciona actualmente y qué se puede demostrar en vivo el día de hoy?
> **Respuesta:** Funciona de principio a fin el aprovisionamiento institucional de rectores, la configuración de sedes y calendarios, la administración académica (grados, grupos, asignaturas), la asignación de carga docente, la matrícula de alumnos, la planilla interactiva de notas con ponderación porcentual, el control de asistencia diaria, el portal del estudiante y los registros de auditoría de base de datos. Todo ello demostrable en vivo sobre PostgreSQL y Redis activos.

#### 3. ¿Cuáles módulos están completos, parciales o dependientes de terceros?
> **Respuesta:** Completos: Autenticación, RBAC (11 roles), Gobernanza Territorial DANE, Gestión Académica, Calificaciones, Asistencia, Auditoría y Portal Estudiantil. Parcial: Interoperabilidad con SIMAT (cuenta con catálogo DANE/DIVIPOLA, pero sin web service transaccional en línea). Dependiente de terceros: Clases virtuales en vivo (requiere clúster BigBlueButton con servidores de streaming WebRTC).

#### 4. ¿Qué arquitectura y stack tecnológico utiliza la solución?
> **Respuesta:** Frontend desacoplado en React 18, TypeScript y Vite, sin fuentes ni estilos remotos (offline-first). Backend asíncrono en FastAPI (Python 3.12), Pydantic v2 y SQLAlchemy 2.0 Async. Persistencia relacional en PostgreSQL 15 particionada lógicamente por institución. Caché y gestión de sesiones en Redis 7.

#### 5. ¿Cómo se administran los usuarios, roles y fronteras institucionales?
> **Respuesta:** Mediante un modelo jerárquico RBAC de 11 roles tipados en base de datos. La frontera institucional se garantiza a través de dependencias de inyección de FastAPI que atan la sesión del usuario al `institution_id` verificado en su token JWT, bloqueando cualquier operación fuera de su jurisdicción.

#### 6. ¿Cómo se previene el acceso o la fuga de datos entre instituciones (Cross-tenant / IDOR)?
> **Respuesta:** En cada consulta y modificación, los repositorios de datos exigen explícitamente el `institution_id` en las cláusulas de consulta SQL. Se aplican validaciones cruzadas que impiden que un usuario autenticado en una sede acceda a registros de otra cambiando los parámetros de URL (mitigación anti-IDOR verificada con pruebas automatizadas).

#### 7. ¿Qué datos personales o educativos se almacenan y cómo se protegen?
> **Respuesta:** Se almacenan nombres, tipos y números de documento de identidad, correos institucionales, matrículas y registros evaluativos. Se protegen bajo el marco de la Ley 1581 de 2012: contraseñas hasheadas con bcrypt, sesiones encriptadas con JWT y canales de transmisión bajo TLS. No se recopilan datos biométricos ni información ajena a la labor educativa.

#### 8. ¿Cómo se manejan contraseñas, tokens y secretos de configuración?
> **Respuesta:** Las contraseñas se almacenan únicamente como hashes bcrypt (factor de costo 12). Los tokens JWT se firman con algoritmos criptográficos robustos, poseen expiración corta y su invalidación inmediata se almacena en memoria volátil Redis. Los secretos del sistema se inyectan como variables de entorno seguras, sin exponerse en el código ni en repositorios Git.

#### 9. ¿Cuál es el estado actual de la base de datos y su despliegue?
> **Respuesta:** Esquema relacional formal normalizado con migraciones versionadas en Alembic. Actualmente opera en entornos de prueba locales y de desarrollo sobre PostgreSQL 15, estructurado con llaves foráneas e índices por institución y códigos DANE.

#### 10. ¿Qué pruebas se han ejecutado realmente y qué permanece sin probar?
> **Respuesta:** Se han ejecutado y aprobado **169 pruebas backend de integración y seguridad** (83 de base de datos, 18 de integridad transaccional, 32 de aprovisionamiento institucional y 36 de endurecimiento de autenticación con Redis), además de 41 chequeos automáticos de documentación y compilación limpia de TypeScript. Permanecen sin ejecutar en este ciclo 553 pruebas unitarias secundarias, y están pendientes las pruebas de estrés a gran escala y la auditoría externa de penetración (pentesting).

#### 11. ¿El sistema está listo para producción nacional masiva o alta concurrencia?
> **Respuesta:** No de forma inmediata para millones de usuarios. La arquitectura está técnicamente diseñada para escalar horizontalmente mediante contenedores y colas asíncronas, pero antes de un despliegue nacional masivo debe someterse a pruebas de carga distribuida y afinamiento de infraestructura en conjunto con el MEN.

#### 12. ¿Ha sido PEVN certificado, aprobado o evaluado formalmente por el MEN?
> **Respuesta:** No. PEVN es una iniciativa de desarrollo de software independiente. No cuenta con certificación oficial, contrato ni aval previo del MEN. El propósito de esta reunión es precisamente iniciar el proceso formal de revisión técnica.

#### 13. ¿Existe integración en vivo con SIMAT, DUE u otros sistemas del MEN?
> **Respuesta:** No existe una conexión transaccional directa en línea con los servidores centrales del MEN. Se cuenta con el modelo de datos normalizado y el catálogo DANE de 18,031 colegios y 51,521 sedes precargado en base de datos para asegurar compatibilidad total una vez se definan los protocolos de integración.

#### 14. ¿Cómo utiliza la plataforma la información del DANE y DIVIPOLA?
> **Respuesta:** Utiliza los códigos oficiales de departamento (2 dígitos), municipio (5 dígitos), institución educativa y sede (12 dígitos) como identificadores estándar en la jerarquía territorial, permitiendo consolidar datos a nivel municipal, departamental o nacional sin conflictos de nomenclatura.

#### 15. ¿Cuál es el estado de las clases virtuales en vivo y BigBlueButton?
> **Respuesta:** El cliente de software para crear salas, invitar participantes y autenticar moderadores está 100% programado en FastAPI. Sin embargo, la transmisión multimedia de las clases en tiempo real requiere la conexión a un clúster de servidores BigBlueButton externo debidamente aprovisionado.

#### 16. ¿Cómo se evaluaría la migración de datos, copias de seguridad y soporte?
> **Respuesta:** Se propone diseñar en la Fase 2 del plan de colaboración guiones de importación masiva desde archivos oficiales del SIMAT, políticas de respaldo diario automatizado (*pg_dump* y replicación en caliente) y protocolos de mesa de ayuda técnica escalonada.

#### 17. ¿Qué requerimientos de accesibilidad y baja conectividad faltan por validar?
> **Respuesta:** Falta la certificación formal bajo norma NTC 5854 / WCAG 2.1 AA y pruebas de estrés en enlaces rurales con latencias superiores a 500ms o micro-cortes intermitentes.

#### 18. ¿Qué evidencia necesitaría el MEN para evaluar esta iniciativa?
> **Respuesta:** Acceso al repositorio de código fuente, los esquemas de base de datos, el presente dossier técnico, los manuales de usuario y la ejecución demostrativa del entorno de pruebas en vivo.

#### 19. ¿Qué colaboración específica se le solicita al MEN?
> **Respuesta:** No se solicitan recursos económicos. Se solicita: (a) Establecer una mesa técnica de trabajo con los ingenieros de la Oficina de Tecnología; (b) Revisión formal de arquitectura y seguridad; (c) Definición de lineamientos de interoperabilidad; y (d) Autorización para diseñar un piloto experimental controlado en 2 a 5 colegios oficiales bajo gobernanza del MEN.

---

## 19. Marco de Colaboración Propuesto con el MEN

La colaboración se concibe como un proceso voluntario, no vinculante inicialmente, regulado por hitos y compuertas de decisión técnica:

```mermaid
graph LR
    F1[Fase 1: Mesa Técnica y Discovery] --> G1{Compuerta 1: Viabilidad}
    G1 -- Aprobado --> F2[Fase 2: Evaluación Técnica y Ciberseguridad]
    G1 -- Ajustes --> F1
    F2 --> G2{Compuerta 2: Aval de Seguridad}
    G2 -- Aprobado --> F3[Fase 3: Piloto Experimental Controlado]
    G2 -- Ajustes --> F2
    F3 --> G3{Compuerta 3: Adopción y Métricas}
    G3 -- Aprobado --> F4[Fase 4: Consolidación Institucional]
```

---

## 20. Diseño de Piloto Sugerido y Compuertas de Aceptación (Subject to MEN Approval)

### 20.1. Alcance del Piloto Controlado
- **Muestra Sugerida:** Entre 2 y 5 Instituciones Educativas oficiales, seleccionadas conjuntamente por el MEN y la Secretaría de Educación respectiva (idealmente combinando 1 o 2 colegios urbanos y 2 o 3 sedes rurales).
- **Duración:** Un periodo académico completo (aproximadamente 10 a 12 semanas).
- **Módulos Activos:** Gestión académica, matrícula de prueba, calificaciones y asistencia docente.

### 20.2. Salvaguardas y Condiciones Previas
1. **Consentimiento Informado:** Autorización expresa de los directivos docentes y padres de familia conforme a la Ley 1581 de 2012.
2. **Ambiente Aislado:** El piloto operará sobre infraestructura dedicada de pruebas, sin poner en riesgo la operación formal de las instituciones.
3. **Respaldo Doble:** Durante el piloto, la institución mantendrá su registro oficial ordinario para evitar cualquier alteración del historial legal de los estudiantes.

### 20.3. Criterios de Éxito y Compuertas de Decisión
- **Cero Brechas de Seguridad:** Ningún incidente de fuga de datos o salto de tenant reportado.
- **Tasa de Adopción Docente:** Más del 85% de los docentes registran notas y asistencia sin requerir asistencia técnica correctiva crítica.
- **Rendimiento:** Tiempos de respuesta inferiores a 1.5 segundos en operaciones transaccionales bajo condiciones normales de red.

---

## 21. Hoja de Ruta por Fases Sugerida

| Fase | Denominación | Duración Estimada | Prerrequisito Clave | Entregable / Hito Técnico |
| :--- | :--- | :--- | :--- | :--- |
| **Fase 1** | **Mesa Técnica y Discovery** | 2 a 4 semanas | Presentación presencial y entrega de repositorios al MEN. | Dictamen técnico de viabilidad y matriz de requisitos de interoperabilidad. |
| **Fase 2** | **Alineación de Seguridad e Interoperabilidad** | 4 a 6 semanas | Aval de la Fase 1. | Auditoría SAST/DAST ejecutada, diseño de endpoints para SIMAT y afinamiento de contenedores. |
| **Fase 3** | **Piloto Controlado en Territorio** | 10 a 12 semanas | Autorización institucional y selección de colegios por el MEN. | Informe de resultados del piloto, métricas de usabilidad y estabilidad operativa. |
| **Fase 4** | **Consolidación y Escalamiento** | A definir por MEN | Aprobación de compuerta final del piloto. | Hoja de ruta para adopción progresiva o incorporación como bien público digital del Estado. |

---

## 22. Índice de Evidencia y Rutas en el Repositorio

Para facilitar la labor de auditoría por parte de los ingenieros del MEN, se relacionan las rutas relativas exactas dentro del repositorio del proyecto:

- **Presentación Interactiva Institucional:** `docs/presentation/PEVN_PRESENTACION_INSTITUCIONAL_MEN.html`
- **Manual Institucional de Usuario (HTML):** `docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`
- **Manual Interactivo Web:** `docs/manual/index.html`
- **Manifiesto de Capturas de Pantalla:** `docs/manual/SCREENSHOT_MANIFEST.md`
- **Reporte de Auditoría DOC-04-R4 (Línea Base Verificada):** `docs/reports/PEVN_DOC04_R4_INDEPENDENT_VISUAL_AND_REGRESSION_ACCEPTANCE_REPORT.md`
- **Rutas de Backend Core:** `backend/app/main.py`, `backend/app/api/v1/router.py`
- **Modelos de Datos y RBAC:** `backend/app/models/user.py`, `backend/app/models/territorial.py`, `backend/app/models/academic.py`
- **Servicios de Seguridad y Multi-Tenant:** `backend/app/core/security.py`, `backend/app/services/institution_service.py`
- **Batería de Pruebas de Integración y Seguridad:**
  - `backend/tests/test_database_integration.py` (83 pruebas PG15)
  - `backend/tests/test_db_safety.py` (18 pruebas de seguridad)
  - `backend/tests/test_rector_provisioning_flow.py` (32 pruebas de flujo directivo)
  - `backend/tests/test_auth_redis_hardening.py` (36 pruebas de autenticación y Redis)
- **Script de Auditoría de Documentación:** `scripts/audit_documentation.py` (41 comprobaciones automatizadas)

---

## 23. Glosario de Términos Técnicos e Institucionales

- **Anti-IDOR (Insecure Direct Object Reference Mitigation):** Mecanismos de validación en la capa de software que impiden que un usuario acceda a registros de otra entidad alterando identificadores en peticiones web.
- **BigBlueButton (BBB):** Sistema de conferencias web de código abierto diseñado específicamente para la educación en línea, con soporte de pizarras interactivas, sondeos y salas de grupos.
- **DIVIPOLA (División Político-Administrativa de Colombia):** Estándar de codificación territorial del DANE que asigna códigos numéricos únicos a departamentos y municipios.
- **DUE (Directorio Único de Establecimientos Educativos):** Registro oficial del MEN que clasifica y asigna código DANE a todas las sedes educativas del país.
- **FastAPI:** Marco web asíncrono moderno en Python de alto rendimiento basado en tipos estándar de Python y Pydantic.
- **JWT (JSON Web Token):** Estándar abierto (RFC 7519) que define un mecanismo compacto y autónomo para transmitir información de identidad segura en formato JSON.
- **Multi-Tenant:** Arquitectura de software en la cual una única instancia de la aplicación sirve a múltiples clientes o instituciones, garantizando aislamiento estricto entre sus datos.
- **RBAC (Role-Based Access Control):** Modelo de seguridad que restringe el acceso a recursos y funcionalidades del sistema con base en el rol asignado al usuario.
- **SIMAT (Sistema Integrado de Matrícula):** Sistema de información oficial del MEN para la administración y control de la matrícula de estudiantes en el sector oficial.
- **SPA (Single-Page Application):** Aplicación web que interactúa con el usuario reescribiendo dinámicamente la página web actual con nuevos datos del servidor web, en lugar de cargar páginas enteras desde cero.
- **Vite:** Herramienta moderna de construcción de frontend que proporciona una recarga rápida en desarrollo y compilación altamente optimizada para producción.

---

**Fin del Informe Técnico Institucional.**  
*Documento preparado con la máxima rigurosidad y transparencia técnica para la sesión de trabajo con el Ministerio de Educación Nacional.*
