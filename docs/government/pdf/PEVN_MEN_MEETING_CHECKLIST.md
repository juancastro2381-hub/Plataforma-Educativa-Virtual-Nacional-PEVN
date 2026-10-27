# Plataforma Educativa Virtual Nacional (PEVN)
## Lista de Verificación y Protocolo para la Sesión con el MEN
### Guía Operativa para la Reunión Presencial con la Oficina de Tecnología y Sistemas de Información

---

**Iniciativa:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario:** Delegación Técnica PEVN / Oficina de Tecnología y Sistemas de Información — MEN  
**Fecha:** Octubre 2026 | **Versión:** 1.0-FINAL-MEN  
**Ubicación:** Sede Central del Ministerio de Educación Nacional, CAN, Bogotá D.C.  

---

## 1. Objetivos Estratégicos de la Sesión

1. **Presentar con rigor factual la arquitectura y madurez técnica de PEVN:** Demostrar que el sistema no es una promesa en papel, sino una plataforma de software real con código auditable y pruebas reproducibles.
2. **Establecer una diferenciación transparente de estados:** Distinguir claramente lo que está IMPLEMENTADO en código de lo que requiere clústeres externos (BigBlueButton) o acuerdos interinstitucionales (SIMAT/DUE).
3. **Proponer un marco estructurado de trabajo por fases:** Someter a consideración del MEN la ruta de 4 fases con compuertas de decisión técnica (Decision Gates), sin solicitar recursos económicos.
4. **Instalar una Mesa Técnica de Trabajo:** Acordar el canal formal para la revisión profunda del repositorio y el diseño conjunto de un piloto experimental controlado en 2 a 5 colegios oficiales.

---

## 2. Evidencias y Artefactos a Llevar a la Sesión

### A. Material Impreso y Dossiers Técnicos
- [ ] **Informe Técnico Integral:** 3 copias encuadernadas de `PEVN_INFORME_TECNICO_INTEGRAL_PARA_REVISION_MEN.pdf` (15 páginas con las 27 secciones completas).
- [ ] **Resumen Ejecutivo:** 5 copias impresas de `PEVN_MEN_EXECUTIVE_BRIEF.pdf` para entrega a directores y asesores.
- [ ] **Presentación Institucional:** Copias impresas o visualizador listo de `PEVN_PRESENTACION_INSTITUCIONAL_MEN.pptx` y `.pdf` (22 diapositivas).
- [ ] **Copia del Repositorio en Medio Digital Seguro:** Memoria USB cifrada con el snapshot íntegro del repositorio Git en el commit de referencia `a7ecbed460283bdd55f1ab53f96b315012288876`.

### B. Entorno de Demostración en Vivo (Demo Standalone)
- [ ] **Equipo Portátil de Demostración:** Batería cargada al 100%, cargador, adaptador HDMI y configuración de pantalla duplicada lista.
- [ ] **Servicios Locales Pre-Iniciados y Verificados:**
  - PostgreSQL 15 activo con base de datos de prueba precargada con catálogo DANE (18,031 colegios y 51,521 sedes).
  - Redis 7 activo en puerto local estándar (6379) para control de sesiones.
  - Backend FastAPI corriendo en `http://localhost:8000` con documentación interactiva Swagger (`/docs`) y ReDoc (`/redoc`) operativas.
  - Frontend SPA en React/TypeScript compilado y corriendo en `http://localhost:5173`.
- [ ] **Cuentas de Prueba Pre-Aprovisionadas y Verificadas:**
  - `superadmin`: Para mostrar configuración global y telemetría territorial.
  - `department_admin` / `municipality_admin`: Para mostrar gobierno municipal y creación de colegios por DANE.
  - `rector`: Para mostrar activación institucional, sedes, periodos y comités evaluativos.
  - `coordinator`: Para mostrar asignación de cursos y la política de delegación controlada por el rector.
  - `teacher`: Para mostrar el diligenciamiento ágil de la planilla de calificaciones (1.0-5.0) y asistencia.
  - `student` / `guardian`: Para mostrar la consulta protegida contra vulnerabilidades IDOR.
- [ ] **Modo de Contingencia Offline:** Verificar que la demostración funcione al 100% desconectando el Wi-Fi (cero dependencias de CDNs externas).

---

## 3. Banco de Preguntas Críticas y Respuestas Factuales

### P1. ¿Qué es PEVN y qué busca el proyecto con el MEN?
> **Respuesta:** PEVN es una plataforma abierta y soberana de gestión escolar concebida para superar la fragmentación y los costos de software comercial en colegios oficiales. No buscamos contratos comerciales ni venta de licencias; proponemos transferir la tecnología como un Bien Público Digital para el Estado, iniciando con una mesa técnica de trabajo y un piloto controlado en 2 a 5 colegios bajo rectoría del MEN.

### P2. ¿Está el sistema certificado o aprobado por alguna entidad del Estado?
> **Respuesta:** No. PEVN es un desarrollo técnico independiente. No cuenta a la fecha con homologación, contrato ni certificación formal del MEN o MinTIC. El propósito de esta reunión es precisamente abrir la puerta para que el equipo de ingeniería del MEN audite el código y determine su viabilidad.

### P3. ¿Existe integración en vivo hoy con el SIMAT o el DUE?
> **Respuesta:** No existe una conexión web service transaccional activa con las bases de datos centrales del MEN. Lo que tenemos implementado es compatibilidad total en el modelo de datos, ya que el sistema utiliza los códigos oficiales DANE de departamento, municipio, colegio y sede (12 dígitos). La especificación de los web services seguros es uno de los temas propuestos para la Fase 2.

### P4. ¿Cómo se protege la información de menores de edad (Ley 1581 de 2012)?
> **Respuesta:** Aplicamos privacidad por diseño: las contraseñas se almacenan con Argon2id / bcrypt, las sesiones se protegen con JWT en cabeceras Bearer validadas en Redis, y el sistema carece totalmente de rastreadores comerciales o analítica foránea. Además, la base de datos registra una pista inmutable de auditoría forense (`AuditLog`) con marca de tiempo UTC y dirección IP para cada cambio en notas o matrículas.

### P5. ¿Cómo garantizan que un colegio no vea las notas o estudiantes de otro (Cross-Tenant / IDOR)?
> **Respuesta:** El aislamiento no se delega a los programadores en cada vista; está forzado en la capa base de repositorios de SQLAlchemy, donde toda consulta inyecta obligatoriamente `WHERE institution_id = :current_user_institution_id`. Cualquier intento de modificar el identificador en la URL responde con `HTTP 403 Forbidden` o `HTTP 404 Not Found`.

### P6. ¿Qué pruebas se han realizado realmente sobre el sistema?
> **Respuesta:** En la suite Pytest contamos con un censo dinámico de **747 pruebas recolectadas en 72 archivos**, de las cuales **83 son pruebas de integración real contra PostgreSQL 15** y **664 son pruebas unitarias y en memoria**. En el ciclo de control más reciente ejecutamos **57 pruebas focalizadas con 100% de éxito**, validando el hardening de conexiones (cierre seguro de descriptores en bloque `finally`), sanitización de errores de base de datos y flujos de aprovisionamiento.

---

## 4. Decisiones Concretas Solicitadas a la Mesa Técnica del MEN

1. **Aprobación de la Fase 1 (Mesa Técnica de Arquitectura):** Designación formal de un líder técnico del MEN para coordinar la inspección del repositorio y resolver dudas de arquitectura.
2. **Definición de Lineamientos de Interoperabilidad:** Establecimiento del canal y formato preferido por el MEN (REST OpenAPI, intercambio de archivos estructurados JSON/XML) para la articulación futura con SIMAT y DUE.
3. **Criterios de Ciberseguridad y Hosting:** Indicación de las guías de seguridad digital de MinTIC y estándares de nube oficial que PEVN deberá satisfacer en la Fase 2.
4. **Viabilidad de Piloto Experimental Controlado (Fase 3):** Explorar la viabilidad de autorizar conjuntamente con una Secretaría de Educación certificada un piloto de 1 periodo escolar en 2 a 5 colegios oficiales, operando en paralelo con los registros ordinarios.

---

## 5. Compromisos y Formato de Seguimiento Posterior (Minuta)

Al finalizar la sesión, asegurar la redacción de una minuta formal que consigne:
- [ ] Nombres, cargos y correos electrónicos de los asistentes por parte del MEN (OTSI, Arquitectura, Seguridad).
- [ ] Dictamen preliminar de la OTSI respecto al planteamiento de arquitectura presentado.
- [ ] Cronograma acordado para la entrega y apertura de repositorios Git a los evaluadores del Ministerio.
- [ ] Fecha tentativa para la segunda sesión técnica (revisión de hallazgos y especificaciones SIMAT).
- [ ] Responsable asignado en el MEN para canalizar comunicaciones institucionales.

---

*Lista de verificación de uso operativo interno para la delegación técnica de PEVN en la sesión oficial de trabajo con el MEN.*
