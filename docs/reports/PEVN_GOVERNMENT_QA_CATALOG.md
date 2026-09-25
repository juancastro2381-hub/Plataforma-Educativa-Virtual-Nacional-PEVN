# PEVN — CATÁLOGO FORENSE DE PREGUNTAS Y RESPUESTAS GUBERNAMENTALES (Q&A)
## BANCO DE PREGUNTAS PARA EVALUADORES PÚBLICOS, AUDITORES Y MESAS TÉCNICAS (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatarios:** Evaluadores de MEN, MinTIC, Secretarías de Educación, Organismos de Control y Jurídicos  
**Marco Metodológico:** AI Software Factory v1.2 — Factual Evidence Protocol  
**Fecha:** 21 de Septiembre de 2026  
**Regla de Oro:** Cero respuestas especulativas. Todo se sustenta en código, pruebas o limitaciones documentadas.  

---

## 1. Categoría: PRODUCTO (Product)

### Q-PROD-01: ¿Qué problemas concretos del sistema educativo oficial colombiano resuelve PEVN?
- **Evidencia Disponible:** `docs/ARCHITECTURE.md`, `docs/reports/PEVN_FUNCTIONAL_CAPABILITY_MATRIX.md`.
- **Respuesta Factual Actual:** Resuelve la fragmentación de herramientas en los colegios oficiales. Unifica en un único sistema: el directorio DANE/DUE de sedes, el libro de matrículas SIMAT, las asignaciones docentes, el Sistema Institucional de Evaluación (SIEE, Decreto 1290), las clases sincrónicas en tiempo real, el observador de convivencia (Ley 1620) y la comunicación bidireccional con las familias mediante portales web dedicados.
- **Asunto Abierto (*Open Issue*):** La plataforma carece actualmente de módulos de gestión financiera (fondos de servicios docentes) e inventario físico escolar.
- **Acción Futura Requerida:** Delimitar el alcance en la presentación: PEVN es una plataforma académica, pedagógica y de convivencia, no un ERP contable.

### Q-PROD-02: ¿Está la plataforma lista para ser utilizada por los colegios mañana mismo?
- **Evidencia Disponible:** `docs/reports/PEVN_GOVERNMENT_PRESENTATION_READINESS_AUDIT.md`.
- **Respuesta Factual Actual:** Funcional y lógicamente el software está completo y verificado. No obstante, **operativamente requiere el aprovisionamiento de infraestructura de servidores de producción**, enlaces DNS gubernamentales (`.gov.co`) y el comisionamiento de los servidores físicos BigBlueButton para las clases virtuales.
- **Asunto Abierto:** Falta la infraestructura física que debe proveer la entidad gubernamental.
- **Acción Futura Requerida:** Proponer el despliegue inmediato de una Fase Piloto en 5 a 10 instituciones antes del despliegue masivo.

---

## 2. Categoría: PEDAGOGÍA Y EVALUACIÓN (Pedagogy)

### Q-PED-01: ¿Cómo se adapta PEVN a la autonomía curricular de cada colegio según el Decreto 1290 de 2009?
- **Evidencia Disponible:** `backend/app/models/evaluation.py`, `docs/phase16b_domain_services_report.md`.
- **Respuesta Factual Actual:** Mediante la entidad `SieePolicy`. No existe una regla fija universal codificada en duro. Cada institución educativa define de manera autónoma sus escalas de calificación (ej. 1.0 a 5.0), notas mínimas aprobatorias, topes de nivelación y criterios de promoción anual (número de materias reprobadas permitidas y porcentaje mínimo de asistencia).
- **Asunto Abierto:** Las políticas SIEE se configuran por año lectivo; los colegios con calendarios mixtos (Calendario A y B) requieren parametrización independiente.
- **Acción Futura Requerida:** Validar las políticas SIEE típicas de 3 Secretarías de Educación diferentes durante la fase piloto.

### Q-PED-02: ¿Cómo maneja el sistema la escala nacional de valoración (Bajo, Básico, Alto, Superior)?
- **Evidencia Disponible:** `backend/app/services/siee_policy_service.py` (`map_score_to_performance_level`).
- **Respuesta Factual Actual:** El motor traduce de forma determinística las calificaciones numéricas institucionales a los cuatro niveles de desempeño nacionales del Decreto 1290, incorporando descriptores cualitativos de logros y dificultades en los boletines oficiales periódicos.
- **Asunto Abierto:** Ninguno a nivel de software.
- **Acción Futura Requerida:** Ninguna.

---

## 3. Categoría: TECNOLOGÍA Y ARQUITECTURA (Technology)

### Q-TECH-01: ¿Qué stack tecnológico utiliza PEVN y por qué se eligió?
- **Evidencia Disponible:** `backend/pyproject.toml`, `frontend/package.json`, `docs/ARCHITECTURE.md`.
- **Respuesta Factual Actual:** Backend en **Python 3.12 con FastAPI** (estándar moderno de alto rendimiento asíncrono y tipado estricto), **PostgreSQL 16** (motor relacional ACID de grado empresarial), **Redis 7** (caché y gestión de concurrencia) y Frontend en **React 18 con TypeScript y Vite** (interfaz SPA rápida, accesible y desacoplada).
- **Asunto Abierto:** Ninguno. Se seleccionaron tecnologías de código abierto maduras, con amplio soporte global y sin ataduras a proveedores privativos (*no vendor lock-in*).
- **Acción Futura Requerida:** Mantener las dependencias actualizadas semestralmente.

### Q-TECH-02: ¿Por qué no utilizar un CMS o un LMS prediseñado como Moodle?
- **Evidencia Disponible:** `docs/ARCHITECTURE.md`.
- **Respuesta Factual Actual:** Las plataformas tradicionales como Moodle fueron concebidas para educación superior o cursos aislados; no modelan de forma nativa la jerarquía del Estado colombiano (DANE $\rightarrow$ Departamentos $\rightarrow$ Municipios $\rightarrow$ Sedes $\rightarrow$ Jornadas $\rightarrow$ SIMAT), ni el régimen de convivencia escolar (Ley 1620) ni el SIEE. PEVN fue diseñado específicamente para la estructura misional del colegio oficial colombiano.
- **Asunto Abierto:** Moodle tiene mayor variedad de plugins pedagógicos de terceros.
- **Acción Futura Requerida:** Diseñar a futuro un protocolo de integración LTI (Learning Tools Interoperability) para enlazar contenidos Moodle si una institución lo requiere.

---

## 4. Categoría: CIBERSEGURIDAD (Security)

### Q-SEC-01: ¿Cómo se protegen las contraseñas de los usuarios contra ataques de descifrado?
- **Evidencia Disponible:** `backend/app/core/security/password.py`, `backend/tests/test_password_hasher.py`.
- **Respuesta Factual Actual:** Se utiliza el algoritmo **Argon2id** (RFC 9106), ganador de la *Password Hashing Competition*. Utiliza 64 MB de memoria RAM por operación de hashing, 3 iteraciones de tiempo y 4 hilos en paralelo, con un salt criptográfico aleatorio de 16 bytes por registro. Es inmune a ataques acelerados por GPU y circuitos ASIC.
- **Asunto Abierto:** Ninguno.
- **Acción Futura Requerida:** Mantener los parámetros en concordancia con las recomendaciones periódicas de OWASP y NIST.

### Q-SEC-02: ¿Cómo garantiza PEVN que un docente o hacker del Colegio A no pueda ver datos del Colegio B (Anti-IDOR)?
- **Evidencia Disponible:** `backend/app/services/guardian_portal_service.py`, `backend/tests/test_teacher_academic_scope.py`.
- **Respuesta Factual Actual:** Mediante una doble barrera:
  1. Aislamiento Multi-Tenant estricto: Las consultas ORM filtran obligatoriamente por el `institution_id` extraído criptográficamente del token JWT.
  2. Mecanismo **Blind 404 (404 Ciego)**: Si un usuario manipula un identificador UUID en la URL para intentar consultar un recurso ajeno, el backend devuelve `404 Not Found` en lugar de `403 Forbidden`, evitando revelar la existencia del registro en otra institución.
- **Asunto Abierto:** Requiere pruebas de penetración de caja negra por una firma de ciberseguridad externa antes del lanzamiento nacional.
- **Acción Futura Requerida:** Contratar auditoría ética de seguridad previa al paso a producción.

---

## 5. Categoría: PROTECCIÓN DE DATOS PERSONALES (Data Protection)

### Q-DAT-01: ¿Cómo cumple PEVN con la Ley 1581 de 2012 y el tratamiento de datos de menores de edad?
- **Evidencia Disponible:** `docs/reports/PEVN_DATA_PROTECTION_READINESS.md`.
- **Respuesta Factual Actual:** Cumple los principios de **finalidad pedagógica legítima**, **acceso y circulación restringida** (los datos de un alumno solo los ven sus directivos, docentes asignados y sus acudientes vinculados) y **seguridad reforzada**. En la auditoría técnica, las contraseñas y datos sensibles se censuran automáticamente en logs (`[REDACTED]`).
- **Asunto Abierto:** Falta la formalización jurídica de la Política de Tratamiento de Datos del MEN y el formato de consentimiento parental informado.
- **Acción Futura Requerida:** El equipo jurídico del MEN/MinTIC debe redactar los términos y condiciones institucionales.

---

## 6. Categoría: INFRAESTRUCTURA Y SERVIDORES (Infrastructure)

### Q-INF-01: ¿Qué servidores físicos se requieren para atender a 10 colegios en una fase piloto?
- **Evidencia Disponible:** `docs/reports/PEVN_INFRASTRUCTURE_READINESS.md`.
- **Respuesta Factual Actual:** Se requieren dos instancias principales:
  1. Servidor Web/API + BD: Instancia de 8 vCPU, 32 GB RAM y 200 GB SSD (alberga FastAPI, React Nginx, PostgreSQL 16 y Redis 7).
  2. Servidor Dedicado BigBlueButton: Servidor físico bare-metal en Ubuntu 22.04 LTS con 16 vCPU, 32 GB RAM, 500 GB NVMe y 1 Gbps dedicado para videoclases y Coturn TURN.
- **Asunto Abierto:** La provisión de este hardware depende del presupuesto asignado por la entidad pública.
- **Acción Futura Requerida:** Entregar la cotización y especificaciones técnicas al equipo de TI ministerial.

---

## 7. Categoría: ESCALABILIDAD (Scalability)

### Q-SCA-01: ¿Cuántos usuarios concurrentes puede soportar la plataforma en su estado actual?
- **Evidencia Disponible:** `docs/reports/PEVN_SCALABILITY_READINESS.md`.
- **Respuesta Factual Actual:** Arquitectónicamente el backend es *stateless* y el frontend se distribuye vía CDN, lo que permite crecer horizontalmente. Sin embargo, **actualmente no se cuenta con métricas empíricas de concurrencia máxima porque no se han ejecutado pruebas de estrés (k6/Locust) en un entorno de producción**.
- **Asunto Abierto:** Capacidad empírica no homologada.
- **Acción Futura Requerida:** Ejecutar jornada formal de pruebas de carga masiva durante la fase piloto.

---

## 8. Categoría: INTEROPERABILIDAD (Interoperability)

### Q-INT-01: ¿Se conecta PEVN directamente con el SIMAT del Ministerio de Educación?
- **Evidencia Disponible:** `backend/app/models/enrollment.py`, `backend/app/models/student.py`.
- **Respuesta Factual Actual:** Los modelos de datos de PEVN son 100% compatibles con la estructura y campos de SIMAT (códigos de matrícula, tipos de documento, identificador de sede). No obstante, **actualmente opera mediante ingesta local de archivos estructurados**, dado que el MEN no expone un web service público abierto sin un convenio interinstitucional previo.
- **Asunto Abierto:** Ausencia de API oficial en vivo de SIMAT.
- **Acción Futura Requerida:** Formalizar mesa técnica con la Oficina de Tecnología del MEN para el enlace de web services seguros.

---

## 9. Categoría: ACCESIBILIDAD (Accessibility)

### Q-ACC-01: ¿Cumple la interfaz con las directrices de accesibilidad web (WCAG 2.1 / Resolución 1519 de 2020 de MinTIC)?
- **Evidencia Disponible:** `frontend/src/components/ui/`, `frontend/src/styles/`.
- **Respuesta Factual Actual:** El frontend utiliza elementos semánticos de HTML5, contraste cromático optimizado (Tailwind CSS), soporte para navegación por teclado, foco visible y atributos ARIA en componentes interactivos (modales y alertas).
- **Asunto Abierto:** Requiere auditoría formal de conformidad con herramientas de escaneo de accesibilidad (Axe / Lighthouse / WAVE) y pruebas con lectores de pantalla (NVDA / JAWS).
- **Acción Futura Requerida:** Ejecutar auditoría formal de accesibilidad WCAG 2.1 Nivel AA en Fase Piloto.

---

## 10. Categoría: ASPECTOS LEGALES (Legal)

### Q-LEG-01: ¿Quién ostenta la responsabilidad legal de las anotaciones en el Observador del Estudiante?
- **Evidencia Disponible:** `backend/app/models/coexistence_incident.py`, Ley 1620 de 2013.
- **Respuesta Factual Actual:** Técnicamente la plataforma garantiza la autoría inalterable del docente o directivo que registra la anotación (`created_by_user_id`) y la fecha UTC. Jurídicamente, la responsabilidad disciplinaria y formativa recae sobre el funcionario y el Comité Escolar de Convivencia de cada establecimiento educativo.
- **Asunto Abierto:** Ninguno técnico.
- **Acción Futura Requerida:** Socializar los manuales de convivencia institucional en la adopción escolar.

---

## 11. Categoría: PROPIEDAD INTELECTUAL Y LICENCIAMIENTO (Intellectual Property)

### Q-IP-01: ¿Bajo qué licencia se distribuye el software y quién es el dueño del código fuente?
- **Evidencia Disponible:** `LICENSE` en raíz del repositorio, `THIRD_PARTY_LICENSES.md`.
- **Respuesta Factual Actual:** El software cuenta con la licencia de código abierto **Apache License, Version 2.0**. Esto otorga al Estado colombiano plena libertad de uso, modificación, inspección, auditoría y distribución sin cobro de regalías ni ataduras a empresas privadas.
- **Asunto Abierto:** Redacción del acta formal de donación o entrega técnica de los derechos patrimoniales si el Estado desea la titularidad exclusiva de marcas.
- **Acción Futura Requerida:** Revisión con la Dirección Jurídica del Ministerio.

---

## 12. Categoría: OPERACIONES Y CONTINUIDAD (Operations)

### Q-OPE-01: ¿Cómo se garantiza la continuidad del servicio ante una caída del servidor?
- **Evidencia Disponible:** `docs/OPERATIONS.md`, `docs/reports/PEVN_INFRASTRUCTURE_READINESS.md`.
- **Respuesta Factual Actual:** En la arquitectura recomendada de producción, se contempla el despliegue multi-zona de los contenedores backend, balanceo de carga automático y clúster de base de datos PostgreSQL con réplica de respaldo caliente (*Hot Standby*). El objetivo operativo es RPO < 15 minutos y RTO < 2 horas.
- **Asunto Abierto:** La infraestructura de alta disponibilidad debe ser provista por la entidad pública.
- **Acción Futura Requerida:** Configurar el monitoreo y alertas en el NOC/SOC ministerial.

---

## 13. Categoría: COSTOS Y PRESUPUESTO (Cost)

### Q-CST-01: ¿Cuánto le cuesta al Estado colombiano el uso de licencias de software de PEVN?
- **Evidencia Disponible:** `LICENSE`, `THIRD_PARTY_LICENSES.md`.
- **Respuesta Factual Actual:** **CERO PESOS ($0 COP) en licenciamiento de software.** Todo el código base y sus dependencias (Python, FastAPI, React, PostgreSQL, Redis, BigBlueButton) son de código abierto. Los únicos costos corresponden a la **infraestructura de cómputo (servidores/nube)** y a los **servicios humanos de soporte técnico y mantenimiento**.
- **Asunto Abierto:** Ninguno.
- **Acción Futura Requerida:** Presentar el modelo de ahorro en comparación con plataformas privativas comerciales.

---

## 14. Categoría: SOSTENIBILIDAD Y MANTENIMIENTO (Sustainability)

### Q-SUS-01: ¿Cómo se garantiza que el software no quede obsoleto en 2 o 3 años?
- **Evidencia Disponible:** `backend/pyproject.toml`, `frontend/package.json`.
- **Respuesta Factual Actual:** La plataforma está construida sobre los frameworks más adoptados a nivel mundial (FastAPI y React). No utiliza tecnologías propietarias o en vía de desuso. Dispone de más de 430 pruebas automatizadas que permiten actualizar versiones de Python o librerías garantizando la no-regresión matemática y funcional del sistema.
- **Asunto Abierto:** Requiere la conformación de un equipo de mantenimiento técnico en la entidad estatal.
- **Acción Futura Requerida:** Incluir un plan de transferencia tecnológica en la entrega.

---

## 15. Categoría: IMPLEMENTACIÓN Y DESPLIEGUE (Implementation)

### Q-IMP-01: ¿Cuánto tiempo toma implementar PEVN en una Secretaría de Educación certificada?
- **Evidencia Disponible:** `docs/phase-reports/PHASE_3C_OFFICIAL_DANE_INSTITUTION_RESOLUTION.md`.
- **Respuesta Factual Actual:** La ingesta del catálogo de colegios y sedes toma minutos mediante el importador de datos DANE. El aprovisionamiento de rectores y docentes se efectúa en 1 a 2 semanas. El cronograma integral para un piloto funcional en una Secretaría se estima en **4 a 6 semanas**.
- **Asunto Abierto:** Depende de la calidad y actualización previa de las bases de datos de docentes y alumnos de la Secretaría.
- **Acción Futura Requerida:** Establecer una lista de chequeo de datos pre-implementación.

---

## 16. Categoría: SOPORTE Y MESA DE AYUDA (Support)

### Q-SUP-01: ¿Cómo se gestiona el soporte a docentes o familias que olvidan su contraseña o tienen problemas técnicos?
- **Evidencia Disponible:** `backend/app/api/v1/endpoints/auth.py`, `docs/AUTHENTICATION.md`.
- **Respuesta Factual Actual:**
  1. Nivel 1 (Autoservicio): Módulo de recuperación de contraseñas por correo electrónico seguro de un solo uso.
  2. Nivel 2 (Institucional): Los rectores y coordinadores pueden reiniciar credenciales y emitir nuevos tokens directamente desde el censo escolar de la institución sin necesidad de elevar un ticket a nivel nacional.
  3. Nivel 3 (Nacional): Mesa de ayuda técnica ministerial para incidencias de infraestructura.
- **Asunto Abierto:** Integración de canal telefónico o chatbot de WhatsApp institucional.
- **Acción Futura Requerida:** Evaluar canal de atención ciudadana complementario.

---

## 17. Categoría: GOBERNANZA DEL PROYECTO (Governance)

### Q-GOV-01: ¿Cómo se administran los cambios y nuevas funcionalidades en el proyecto?
- **Evidencia Disponible:** `docs/reports/`, `.agents/rules/delivery_reports.md`, directrices AI Software Factory v1.2.
- **Respuesta Factual Actual:** El proyecto opera bajo la metodología estricta **AI Software Factory v1.2**: Cada cambio requiere un informe de descubrimiento, un plan de implementación, desarrollo sin alterar líneas base congeladas, 100% de cobertura de pruebas, verificación estática y **aprobación humana explícita (*Human-in-the-Loop*)** antes de cerrar cualquier fase o pasar a producción.
- **Asunto Abierto:** Ninguno.
- **Acción Futura Requerida:** Transferir la documentación de gobernanza al equipo directivo del Ministerio.
