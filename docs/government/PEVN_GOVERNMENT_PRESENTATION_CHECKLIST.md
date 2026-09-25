# PEVN — LISTA DE VERIFICACIÓN PARA PRESENTACIÓN GUBERNAMENTAL
## GUÍA OPERATIVA ANTES, DURANTE Y DESPUÉS DE LA PRESENTACIÓN INSTITUCIONAL
### Plataforma Educativa Virtual Nacional (PEVN)

---

## 1. INTRODUCCIÓN Y PROPÓSITO

Esta lista de verificación (*Checklist*) establece el protocolo operativo riguroso que debe seguir el equipo técnico de PEVN antes, durante y después de cualquier sesión de presentación oficial ante autoridades colombianas (Ministerio de Educación Nacional, MinTIC, Secretarías de Educación Departamentales/Certificadas, comités técnicos evaluadores o directivos institucionales).

El objetivo es garantizar una demostración impecable, verificable, honesta y sin contratiempos técnicos, asegurando la preservación intacta del estado del producto y los datos de demostración.

---

## 2. ANTES DE LA PRESENTACIÓN (FASE DE PREPARACIÓN)

### 2.1 Servicios e Infraestructura Local / Demostración
- [ ] **Motor de Base de Datos PostgreSQL:**
  - [ ] Servicio de PostgreSQL 15/16 activo y escuchando en el puerto local estándar (`5432`).
  - [ ] Conexión verificada mediante string de conexión local (`DATABASE_URL`).
  - [ ] Acceso de solo lectura validado para evitar transacciones destructivas accidentales.
- [ ] **Backend FastAPI:**
  - [ ] Entorno de ejecución de backend activo con dependencias verificadas.
  - [ ] Servidor de aplicaciones iniciado y en ejecución.
  - [ ] Verificación de endpoint de salud: endpoint `/api/v1/ready` o endpoint raíz devuelve `200 OK`.
  - [ ] Verificación de documentación OpenAPI interactiva accesible en la ruta `/docs`.
- [ ] **Frontend Vite / React:**
  - [ ] Aplicación web compilada o servidor de presentación frontend activo.
  - [ ] Carga inicial de la interfaz en navegador sin errores en consola de desarrollador.

### 2.2 Integridad de Datos de Demostración (Preservación Absoluta)
- [ ] **Verificación de Datos Existentes (Colegio Glenn Doman):**
  - [ ] Sede principal activa: `Colegio Glenn Doman (Entorno Demo)` (DANE: `311001088461`, `[IDENTIFICADOR INSTITUCIONAL DEMO]`).
  - [ ] Sede secundaria para aislamiento: `Institución Educativa Técnica Nacional` (DANE: `111001000001`).
  - [ ] Rectoría configurada: `[CUENTA DEMO RECTORÍA]`.
  - [ ] Coordinación académica configurada: `[CUENTA DEMO COORDINACIÓN]`.
  - [ ] Docente activo asignado: `[CUENTA DEMO DOCENTE]`.
  - [ ] Estudiante matriculado: `[ESTUDIANTE DEMO]` (`[CUENTA DEMO ESTUDIANTE]`, `[IDENTIFICADOR ESTUDIANTE DEMO]`).
  - [ ] Acudiente vinculado: `[ACUDIENTE DEMO]` (`[CUENTA DEMO ACUDIENTE]`, `[IDENTIFICADOR ACUDIENTE DEMO]`, Parentesco: Padre).
  - [ ] Registros precargados confirmados: Circular oficial (`[CIRCULAR DEMO]`), Noticia institucional (`[NOTICIA DEMO]`), Registro formativo de convivencia Tipo I Ley 1620 (`[INCIDENTE DEMO]`).
- [ ] **Regla de No Destrucción:**
  - [ ] Confirmar que **NO** se ejecutarán `reset_db`, `alembic downgrade`, scripts de truncado o re-sembrado de datos.

### 2.3 Respaldo y Mecanismo de Recuperación Rápida
- [ ] **Snapshot de Base de Datos:**
  - [ ] `pg_dump` ejecutado y almacenado como respaldo de seguridad previo a la presentación (`pevn_demo_backup_frozen.sql`).
  - [ ] Script de restauración validado en ambiente aislado en caso de manipulación accidental durante una prueba interactiva.
- [ ] **Git Working Tree Inmaculado:**
  - [ ] Confirmar con `git status` que no existen modificaciones no deseadas en código fuente de backend, frontend o pruebas.

### 2.4 Entorno de Navegación y Perfiles de Demostración
- [ ] **Navegador Web Primario (Google Chrome / Microsoft Edge):**
  - [ ] Ventana 1 en Modo Normal (o perfil 1) para rol **Rector / Coordinador**.
  - [ ] Ventana 2 en Modo Incógnito (o perfil 2) para rol **Docente**.
  - [ ] Ventana 3 en Navegador Secundario (Firefox / Brave) para rol **Estudiante**.
  - [ ] Ventana 4 en Dispositivo Móvil / Emulador para rol **Acudiente**.
  - [ ] *Nota:* Las sesiones separadas eliminan la fricción de cerrar e iniciar sesión repetidamente frente al evaluador.
- [ ] **Marcadores / Bookmarks Preconfigurados:**
  - [ ] `PEVN - Inicio de Sesión` -> Ruta `/login`
  - [ ] `PEVN - Portal Rector` -> Ruta `/dashboard`
  - [ ] `PEVN - Documentación OpenAPI` -> Ruta `/docs`
  - [ ] `PEVN - Monitoreo / Audit Log` -> Ruta de auditoría institucional

### 2.5 Hardware, Audiovisual y Red de Contingencia
- [ ] **Pantalla y Proyector:**
  - [ ] Resolución configurada en 1080p (1920x1080) con escala de visualización al 100% o 125% para legibilidad de tablas y notas.
  - [ ] Modo "No molestar" / Asistente de concentración activado en el sistema operativo para bloquear notificaciones personales.
- [ ] **Autonomía y Conectividad:**
  - [ ] Computador conectado a suministro de energía continua.
  - [ ] Punto de acceso local autónomo (la demostración funcional básica puede operar en circuito cerrado sin requerir salida a internet externa).
  - [ ] Conexión de datos móviles / Tethering lista en caso de requerir acceso a repositorios o documentación remota.

### 2.6 Documentación Impresa o Digital Lista para Entrega
- [ ] Copia digital de `PEVN_ONE_PAGE_EXECUTIVE_SUMMARY.md`.
- [ ] Copia digital de `PEVN_EXECUTIVE_PRESENTATION_DOSSIER.md`.
- [ ] Copia digital de `PEVN_TECHNICAL_PRESENTATION_DOSSIER.md`.
- [ ] Copia digital de `PEVN_TECHNOLOGY_DONATION_PROPOSAL.md`.
- [ ] Tablas de preguntas frecuentes de `PEVN_GOVERNMENT_QA.md` en tableta o segundo monitor para consulta rápida del expositor.

---

## 3. DURANTE LA PRESENTACIÓN (FASE DE EJECUCIÓN)

### 3.1 Cronograma y Manejo del Tiempo
| Tiempo Objetivo | Formato | Foco Principal |
| :--- | :--- | :--- |
| **5 minutos** | Pitch Ejecutivo / Directivo | Problema de desconexión, 5 portales unificados, soberanía tecnológica, oferta de cesión al Estado. |
| **10 minutos** | Demostración Funcional | Recorrido por portales (Rector -> Docente -> Estudiante -> Acudiente), convivencia escolar, informe valorativo. |
| **20 minutos** | Evaluación Técnica Integral | Aislamiento multi-sede por DANE, Anti-IDOR, auditoría legal inmutable, arquitectura FastAPI/PostgreSQL, plan de piloto. |

### 3.2 Secuencia de Demostración Recomendada (Flujo de Vida Escolar)
1. **Inicio y Contexto Institucional (Minuto 0-3):**
   - Iniciar sesión como Rectora (`[CUENTA DEMO RECTORÍA]`).
   - Mostrar el Colegio de demostración con su código DANE oficial (`311001088461`).
   - Resaltar la visión institucional integral: matrícula activa, sedes, grupos y docentes asignados.
2. **Gestión Docente y Calificaciones (Minuto 4-8):**
   - Transicionar a ventana de Docente (`[CUENTA DEMO DOCENTE]`).
   - Entrar al grupo de demostración y asignatura asignada.
   - Mostrar el libro de calificaciones configurado bajo la escala nacional del MEN (Desempeño Superior, Alto, Básico, Bajo).
   - Mostrar registro de asistencia en un solo clic.
3. **Experiencia del Estudiante (Minuto 9-12):**
   - Transicionar a ventana de Estudiante (`[CUENTA DEMO ESTUDIANTE]`).
   - Mostrar la vista limpia de tareas pendientes, cronograma y entrega digital de actividades pedagógicas.
   - Mostrar visualización del observador pedagógico personal y boletín valorativo.
4. **Vínculo Familiar y Convivencia Ley 1620 (Minuto 13-16):**
   - Transicionar a vista de Acudiente (`[CUENTA DEMO ACUDIENTE]`).
   - Mostrar seguimiento integral del estudiante a cargo, notificaciones de novedades y circulares oficiales.
   - Demostrar el registro de convivencia escolar Tipo I (formativo, restaurativo, sin estigmatización punitiva).
5. **Seguridad y Rigor Técnico (Minuto 17-20):**
   - Mostrar la traza de auditoría inmutable donde cada acción realizada quedó registrada con timestamp UTC, usuario y rol.
   - Demostrar el intento de cruce de datos inter-institucional (acceso denegado con código HTTP `404/403` gracias a Anti-IDOR).
   - Abrir `/docs` para evidenciar contratos de API OpenAPI tipados y documentados.

### 3.3 Protocolo de Divulgación Honesta de Limitaciones
Si un evaluador formula preguntas sobre temas en fase de diseño o pendientes de infraestructura, aplicar de inmediato las siguientes declaraciones estandarizadas:
- **Sobre Aulas Virtuales (BigBlueButton):**
  > *"El software implementa y valida la integración lógica con BigBlueButton mediante arquitectura de proveedores y mock verificado en pruebas. La infraestructura de servidores físicos BBB y relay TURN/STUN con alta disponibilidad es un componente de despliegue que la entidad receptora aprovisionará según su escala."*
- **Sobre Capacidad y Concurrencia Nacional:**
  > *"La arquitectura está diseñada para permitir escalamiento horizontal; la capacidad efectiva a escala nacional deberá determinarse mediante pruebas de carga y validación de infraestructura."*
- **Sobre Integración con SIMAT / DUE:**
  > *"PEVN incorpora estructuras de datos y reglas de negocio compatibles con el modelo de matrícula correspondiente y se encuentra arquitectónicamente preparada para una eventual interoperabilidad, sujeta a las interfaces técnicas oficiales, autorizaciones y acuerdos institucionales que determine la entidad competente. No reemplaza al SIMAT ni al DUE."*
- **Sobre Reportes PDF / Correo SMTP / S3:**
  > *"El backend cuenta con la arquitectura de exportación y almacenamiento desacoplado lista. La generación pesada de PDF mediante workers en background, el almacenamiento en S3 y el envío masivo transaccional requieren vincularse a la infraestructura en la nube que la entidad defina para producción."*

---

## 4. DESPUÉS DE LA PRESENTACIÓN (FASE DE SEGUIMIENTO)

### 4.1 Paquete de Entrega Inmediata (Mano o Digital)
- [ ] Enviar por correo institucional o entregar en memoria cifrada:
  1. `PEVN_ONE_PAGE_EXECUTIVE_SUMMARY.md` (PDF/Markdown).
  2. `PEVN_EXECUTIVE_PRESENTATION_DOSSIER.md` (PDF/Markdown).
  3. `PEVN_TECHNICAL_PRESENTATION_DOSSIER.md` (PDF/Markdown).
  4. `PEVN_TECHNOLOGY_DONATION_PROPOSAL.md` (PDF/Markdown).
  5. Enlace al repositorio de código fuente auditado (si aplica bajo acuerdo de confidencialidad o revisión de código abierto).

### 4.2 Registro Minucioso de Preguntas y Requerimientos Institucionales
- [ ] Registrar en bitácora de seguimiento:
  - Nombre, cargo y entidad de cada evaluador participante.
  - Preguntas técnicas específicas formuladas (arquitectura, ciberseguridad, soberanía de datos).
  - Preocupaciones pedagógicas o normativas planteadas (Decreto 1290, Ley 1620, Ley 1581).
  - Documentos o evidencias complementarias solicitadas (reportes de pruebas, esquemas de base de datos).

### 4.3 Determinación del Siguiente Punto de Decisión (*Decision Gate*)
- [ ] Acordar con la entidad el siguiente paso institucional:
  - **Opción A:** Sesión técnica de revisión de código (*Code Walkthrough*) con el equipo de arquitectos de TI / MinTIC.
  - **Opción B:** Auditoría de ciberseguridad y escaneo estático con el equipo de seguridad de la información.
  - **Opción C:** Mesa de trabajo pedagógica con delegados de la Secretaría de Educación para calibrar el SIEE.
  - **Opción D:** Presentación de la propuesta formal de donación/cesión de derechos patrimoniales ante la oficina jurídica de la entidad.

---

## 5. RESUMEN DE RESPONSABILIDADES DEL EXPOSITOR

| Área | Responsabilidad del Expositor |
| :--- | :--- |
| **Integridad de Datos** | No alterar datos existentes; usar las identidades del Colegio Glenn Doman ya verificadas. |
| **Credenciales** | Mantener las contraseñas protegidas; no compartirlas en presentaciones públicas (`[USE EXISTING DEMO CREDENTIAL]`). |
| **Veracidad Técnica** | Diferenciar con total claridad entre lo **implementado y probado** y lo **arquitectónicamente preparado / pendiente de infraestructura**. |
| **Postura Institucional** | Actuar como aliados técnicos y donantes de soberanía tecnológica, no como vendedores comerciales. |
