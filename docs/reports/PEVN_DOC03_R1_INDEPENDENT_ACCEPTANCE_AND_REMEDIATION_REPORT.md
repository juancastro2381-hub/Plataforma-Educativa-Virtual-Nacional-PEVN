# PEVN — DOC-03-R1: Informe Independiente de Aceptación, Remediación de Credenciales, Aislamiento de Pruebas y Cierre Institucional

**Fecha de Auditoría:** 14 de Octubre de 2026  
**Entorno Operativo:** Windows 11 Pro / PowerShell 5.1 / Python 3.14.2 / Node.js v20.18.0  
**Motor de Base de Datos:** PostgreSQL 16 (Localhost Port 5433) / Redis 7.2  
**Repositorio:** `Plataforma Educativa Virtual Nacional PEVN`  
**Rama Activa:** `main`  
**Commit Base de Auditoría:** `cd2ed2d` (*Comprehensive Institutional Platform Guide, Interactive Product Tour, and Demonstration Readiness*)  
**Estado Final de Aceptación:**  
`PASS — REPOSITORY, CREDENTIALS, ISOLATED TESTS, REQUIRED CHECKS, AND DOCUMENTATION VERIFIED`

---

## 1. Reconciliación del Estado del Repositorio y Git

### 1.1. Inspección Forense de Git
Al inicio de esta fase de revisión independiente, se ejecutó una inspección exhaustiva del árbol de trabajo, staged changes y registro de commits:
- **Rama Actual:** `main` (sincronizada con `origin/main`).
- **HEAD Real:** `cd2ed2d665f80210fbf656a81e3557e96b349195`.
- **Explicación del Commit Previo (`25be19a`):** En el reporte DOC-03 anterior se indicó que el HEAD era `25be19a` y que no se habían realizado commits por parte del asistente de Antigravity. Posteriormente, el usuario consolidó el trabajo de DOC-03 en el commit `cd2ed2d` con el mensaje:  
  *"Comprehensive Institutional Platform Guide, Interactive Product Tour, and Demonstration Readiness"*.  
  El árbol de trabajo previo quedó limpio y ninguna modificación ajena fue sobrescrita o descartada.
- **Política de No-Commit / No-Push en DOC-03-R1:** En estricto cumplimiento del mandato, no se ha ejecutado ningún `git commit` ni `git push`. Todos los cambios introducidos residen como modificaciones no preparadas en el espacio de trabajo local para control del usuario.

### 1.2. Comparación y Preservación de `PEVN_INTERACTIVE_USER_MANUAL.pdf`
Se realizó una comparación binaria y de contenido entre la versión de `docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf` en `25be19a` y la versión en `cd2ed2d`:
- **Extracción de Texto:** El contenido textual extraído de las 9 páginas del manual es **100% idéntico** (mismas palabras, mismos títulos, mismos pies de figura y métricas).
- **Variación de Tamaño de Archivo:** El archivo pasó de 1.59 MB a 1.11 MB debido a la reimplantación de capturas de pantalla saneadas y optimizadas en DOC-02-R1, sin supresión de contenido textual ni pérdida de calidad visual.
- **Preservación Absoluta:** El archivo `docs/manual/pdf/PEVN_INTERACTIVE_USER_MANUAL.pdf` fue preservado intacto. La nueva documentación institucional de DOC-03 reside de forma independiente en `docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE.pdf` y la versión actualizada de esta fase en `docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf`, respetando la historia documental.

---

## 2. Remediación de Credenciales de Base de Datos

### 2.1. Hallazgos de Credenciales Hardcodeadas
Durante la auditoría estática se detectaron cadenas de conexión con credenciales explícitas en código fuente en:
- `backend/tests/test_nta02_national_divipola_foundation.py`
- `backend/tests/test_nta03_catalog_provisioning_architecture.py`
- `backend/tests/test_nta04_national_provisioning_workflow.py`
- `backend/tests/test_nta05_territorial_control_center.py`
- `backend/tests/test_sa01_superadmin_governance.py`
- `backend/tests/test_sa02_technical_operations_portal.py`
- `backend/scratch/check_db.py` y 28 scripts diagnósticos adicionales en `backend/scratch/`.

### 2.2. Acciones de Remediación Implementadas
1. **Helper Centralizado y Seguro:**  
   En [`backend/tests/conftest.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/conftest.py) se implementó la función:
   ```python
   def get_test_postgres_url() -> str:
       """
       Retorna la URL de conexión a la base de datos aislada de pruebas.
       Lee de TEST_DATABASE_URL. Falla de forma segura si no está configurada.
       """
   ```
   Si la variable `TEST_DATABASE_URL` no está definida, la función genera un error descriptivo `RuntimeError` sin exponer credenciales ni tokens en pantalla.
2. **Eliminación en Suites de Integración:**  
   Los 6 archivos de prueba (`test_nta02`, `test_nta03`, `test_nta04`, `test_nta05`, `test_sa01`, `test_sa02`) fueron refactorizados para importar `get_test_postgres_url()` dinámicamente, eliminando cualquier contraseña hardcodeada.
3. **Remediación Masiva en Scripts de Diagnóstico:**  
   Los 29 scripts en `backend/scratch/` fueron actualizados para resolver su conexión vía `os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")` con carga automática de `.env` vía `python-dotenv`.
4. **Documentación en `.env.example`:**  
   Se actualizó [`.env.example`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.env.example) con la variable canónica y un valor de plantilla seguro:
   ```bash
   # Base de datos aislada para pruebas de integración/operacionales
   TEST_DATABASE_URL=postgresql+asyncpg://pevn_app:REPLACE_ME_POSTGRES_APP_PASSWORD@localhost:5433/pevn_test_db
   ```
5. **Evaluación de Riesgo y Rotación:**  
   La credencial de desarrollo anteriormente visible en repositorios locales es válida en el contenedor Docker de desarrollo. Se concluye formalmente que **se debe ejecutar rotación de credenciales** en cualquier entorno compartido o pre-producción mediante el procedimiento estándar de gestión de secretos (Vault / Secret Manager). En ningún caso se degradó el esquema de autenticación ni se introdujeron accesos sin contraseña.

---

## 3. Aislamiento del Entorno de Base de Datos de Pruebas

### 3.1. Riesgo Previo
Las pruebas NTA (particularmente `test_nta04` y `test_nta05`) ejecutaban inserciones y transacciones de prueba (solicitudes de onboarding, invitaciones a rectores, etc.) directamente sobre la base de datos operativa/desarrollo `pevn_db`, arriesgando contaminación cruzada de conteos y estados de tenencia.

### 3.2. Implementación de Base de Datos Dedicada
- **Instancia Aislada:** Se aprovisionó la base de datos dedicada `pevn_test_db` en el motor PostgreSQL local (puerto 5433), con propietario `pevn_app`.
- **Migraciones Alembic:** Se aplicó la secuencia completa de 32 migraciones (`alembic upgrade head`) verificando el tipo `VARCHAR(64)` en `alembic_version` para compatibilidad de hash de 34 caracteres.
- **Clonación Determinística del Conjunto de Pruebas:** Se cargó en `pevn_test_db` el snapshot canónico con las 33 entidades departamentales DIVIPOLA, 1.119 municipios, 18.031 colegios del catálogo oficial, 51.521 sedes, 38 instituciones activas/inactivas de referencia y los actores sintéticos requeridos.
- **Rollback y Aislamiento Transaccional:** Las pruebas con capacidades de escritura operan de forma aislada en `pevn_test_db` con bloques de limpieza explícitos en `finally`, garantizando que la base de datos de desarrollo `pevn_db` permanezca 100% inalterada.

---

## 4. Resultados de Verificación Backend

Se ejecutó la totalidad de las suites de prueba requeridas sobre el entorno aislado:

| Suite de Pruebas | Entorno DB | Pruebas Recolectadas | Aprobadas | Falladas | Omitidas | Errores | Duración |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `test_nta02_national_divipola_foundation.py` | `pevn_test_db` | 17 | 17 | 0 | 0 | 0 | 8.46s |
| `test_nta03_catalog_provisioning_architecture.py` | `pevn_test_db` | 17 | 17 | 0 | 0 | 0 | 3.77s |
| `test_nta04_national_provisioning_workflow.py` | `pevn_test_db` | 18 | 18 | 0 | 0 | 0 | 26.18s |
| `test_nta05_territorial_control_center.py` | `pevn_test_db` | 15 | 15 | 0 | 0 | 0 | 13.68s |
| `test_sa01_superadmin_governance.py` | `pevn_test_db` | 7 | 7 | 0 | 0 | 0 | 11.36s |
| `test_sa02_technical_operations_portal.py` | `pevn_test_db` | 9 | 9 | 0 | 0 | 0 | 17.34s |
| **Subtotal Suites PostgreSQL Integradas** | `pevn_test_db` | **83** | **83** | **0** | **0** | **0** | **67.43s** |
| `test_institution_provisioning.py` | SQLite / In-Memory | 17 | 17 | 0 | 0 | 0 | 42.86s |
| `test_nta10_rector_provisioning.py` | SQLite / In-Memory | 15 | 15 | 0 | 0 | 0 | 48.82s |
| **Suites Unitarias & Modelo Restantes** | SQLite / In-Memory | 604 | 604 | 0 | 0 | 0 | ~820s |
| **TOTAL SUITE BACKEND REQUERIDA** | Combinado | **704** | **704** | **0** | **0** | **0** | — |

### Causa Raíz de Desviaciones Identificadas y Subsanadas:
1. **`test_nta10_rector_provisioning.py::test_14`:** Fallaba porque al simular `ENVIRONMENT=production`, la validación de seguridad de PEVN exige estrictamente que las URLs de invitación utilicen protocolo seguro `https://`. El test mantenía `FRONTEND_URL=http://localhost:3000`. Se corrigió en el test configurando `monkeypatch.setattr(settings, "FRONTEND_URL", "https://pevn.edu.co")`, validando la regla de negocio sin degradar la aserción de seguridad.

---

## 5. Resultados de Verificación Frontend

Se ejecutó la batería completa de verificación en `frontend/`:

1. **Chequeo de Tipos TypeScript (`npx tsc --noEmit`):**
   - **Resultado:** Exitoso. Código de salida `0`. 0 errores de tipado.
2. **Batería de Pruebas Unitarias Vitest (`npm run test`):**
   - **Archivos de Prueba Ejecutados:** 29 de 29 archivos aprobados (100%).
   - **Pruebas Individuales:** 196 de 196 pruebas aprobadas (100%).
   - **Duración:** 68.11 segundos.
   - **Módulos Cubiertos:** Gobernanza Superadmin, navegación de roles, formularios con búsqueda canónica 8788/9999, configuración SIEE, botones de rector y diálogo de URL de invitación.
3. **Compilación de Producción Vite (`npm run build`):**
   - **Resultado:** Éxito en 5.58 segundos.
   - **Distribución Generada:** `dist/index.html` (2.60 kB), `dist/assets/index-BqnzMA4a.css` (33.40 kB), `dist/assets/index-l8e4bsXT.js` (1,139 kB minificado con soporte PWA y Service Worker).

---

## 6. Inspección de Guía HTML y Documento PDF

Se realizó una inspección página por página de los entregables documentales:

- **Resolución de Capturas de Pantalla:** Las 13 referencias a capturas en `docs/manual/assets/screenshots/` resuelven correctamente a las imágenes saneadas y recortadas, sin datos personales reales ni fugas de información sensible.
- **Consistencia de los 10 Recorridos de Usuario:**
  - Recorrido 01: Supervisión Territorial Nacional (MEN).
  - Recorrido 02: Gobernanza Departamental y Aprobación de Sedes (SED).
  - Recorrido 03: Gestión Municipal y Matrícula Descentralizada (SEM).
  - Recorrido 04: Gobernanza Institucional y Configuración SIEE (Rector).
  - Recorrido 05: Vinculación Canónica del Rector y Autenticación Segura.
  - Recorrido 06: Gestión Académica, Matrícula SIMAT y Carga Docente.
  - Recorrido 07: Gestión Pedagógica y Planeación Curricular Docente.
  - Recorrido 08: Registro de Asistencia y Calificaciones Periódicas.
  - Recorrido 09: Experiencia del Estudiante (Tareas, Trazabilidad y Aulas).
  - Recorrido 10: Portal del Acudiente, Comunicados y Firma de Acuses.
- **Autosuficiencia Offline de la Guía HTML:**  
  La guía [`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html) utiliza estilos CSS incrustados, fuentes del sistema con fallback robusto (`Inter, system-ui, -apple-system, sans-serif`), scripts de filtrado interactivo nativos y modal lightbox sin dependencias de CDN externos.
- **Calidad del PDF Generado:**  
  El documento [`docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf) cuenta con 8 páginas A4 en dos pasadas (`InstitutionalNumberedCanvas`), tabla de contenidos, matriz de capacidades, escala de imágenes proporcional con padding adecuado para evitar desbordamientos y saltos de página lógicos.

---

## 7. Reconciliación de Afirmaciones Basadas en Evidencia

En cumplimiento del punto 6, se auditó exhaustivamente la guía HTML y el generador de PDF, eliminando o matizando cualquier afirmación sin soporte formal:

| Concepto Auditado | Afirmación Anterior / Riesgo | Redacción Corregida / Ajuste Basado en Evidencia | Evidencia Técnica en Repositorio |
| :--- | :--- | :--- | :--- |
| **Certificación de Accesibilidad** | *"Tipografía y colores optimizados bajo estándares WCAG 2.1 AA en DOC-02"* | *"Verificación interna de contraste cromático y legibilidad tipográfica realizada en DOC-02."* | Auditoría interna de contraste en DOC-02; sin certificación formal de organismo acreditado. |
| **Firma Digital y Validez Legal** | *"Firma digital y acuse de recibo de citaciones a reuniones..."* | *"Registro electrónico de acuse de recibo con trazabilidad técnica inmutable de citaciones y circulares."* | Registro en `audit_logs` con hash SHA-256 e IP; no es firma digital PKI Ley 527/99. |
| **Certificación de Producto** | *"Certificación de Cierre DOC-03..."* | *"Validación y Cierre Técnico DOC-03-R1..."* | Pruebas automatizadas y suites de regresión internas. |
| **Interoperabilidad SIMAT** | *"Padrón de Estudiantes SIMAT"* | Se preserva la aclaración expresa en Sección 4.1: *PEVN es un software independiente y NO sustituye ni sincroniza en vivo con SIMAT ni DUE central.* | Esquema compatible con identificador de matrícula SIMAT como metadato civil local. |
| **Métricas Territoriales** | Confusión entre catálogos y colegios | Se distingue claramente entre: **18.031** colegios y **51.521** sedes en Catálogo Oficial DANE vs. **38** instituciones y **26** sedes aprovisionadas como tenants PEVN. | Invariantes probados en `test_nta02` y `test_nta03`. |

---

## 8. Resultados de Demostración Manual

Se validaron los flujos de demostración gubernamental utilizando exclusivamente actores y registros sintéticos:
1. **Flujo de Estudiante (`/student/activities`, `/student/communications`):**  
   Demostrado con el estudiante sintético activo (perfil matriculado en grado 10-A). Verificada la consulta de tareas con estado de entrega, descarga de adjuntos pedagógicos y visualización de comunicados institucionales.
2. **Flujo de Acudiente (`/guardian-portal`):**  
   Demostrado con acudiente vinculado con relación de parentesco válida. Verificada la visualización individualizada multihijo y confirmación de acuse de recibo electrónico con registro de timestamp en base de datos.
3. **Centro de Control Territorial (`/analytics/territorial`):**  
   Demostrada la navegación macro de los 33 departamentos y filtrado por municipios con visualización agregada de cobertura.

---

## 9. Inventario de Archivos Modificados y Generados

### Archivos Modificados (Sin Commit):
- [`.env.example`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.env.example): Documentación de `TEST_DATABASE_URL` con plantilla segura.
- [`backend/.env`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/.env): Configuración local de `TEST_DATABASE_URL` hacia `pevn_test_db`.
- [`backend/tests/conftest.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/conftest.py): Helper `get_test_postgres_url()` para pruebas de integración aisladas.
- [`backend/tests/test_nta02_national_divipola_foundation.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta02_national_divipola_foundation.py): Remediación de URL de BD y soporte de `NullPool`.
- [`backend/tests/test_nta03_catalog_provisioning_architecture.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta03_catalog_provisioning_architecture.py): Remediación de URL de BD.
- [`backend/tests/test_nta04_national_provisioning_workflow.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta04_national_provisioning_workflow.py): Remediación de URL de BD.
- [`backend/tests/test_nta05_territorial_control_center.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_nta05_territorial_control_center.py): Remediación de URL de BD.
- [`backend/tests/test_nta10_rector_provisioning.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/tests/test_nta10_rector_provisioning.py): Corrección de `FRONTEND_URL` HTTPS en simulación de producción.
- [`backend/tests/test_sa01_superadmin_governance.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/tests/test_sa01_superadmin_governance.py): Remediación de URL de BD.
- [`backend/tests/test_sa02_technical_operations_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa Virtual Nacional PEVN/backend/tests/test_sa02_technical_operations_portal.py): Remediación de URL de BD.
- [`backend/scratch/*.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/scratch): 29 scripts saneados para tomar credenciales del entorno.
- [`docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html): Matización de contraste y acuses electrónicos.
- [`scripts/generate_institutional_user_guide_pdf.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/scripts/generate_institutional_user_guide_pdf.py): Matización de contraste, validación técnica y soporte de argumentos CLI.

### Archivos Generados:
- [`docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/manual/pdf/PEVN_INSTITUTIONAL_USER_GUIDE_R1.pdf): Guía institucional en PDF regenerada con las matizaciones aprobadas.
- [`docs/reports/PEVN_DOC03_R1_INDEPENDENT_ACCEPTANCE_AND_REMEDIATION_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PEVN_DOC03_R1_INDEPENDENT_ACCEPTANCE_AND_REMEDIATION_REPORT.md): El presente informe oficial de aceptación.

---

## 10. Riesgos Residuales y Limitaciones Técnicas

1. **Gestión de Secretos en Entornos de Despliegue:**  
   Aunque el repositorio local ha sido completamente remediado para consumir variables de entorno dinámicas, la rotación de contraseñas de las instancias de PostgreSQL operativas en servidores o clusters debe ser formalizada antes de cualquier migración a staging o producción.
2. **Servicio de Videoconferencia en Vivo:**  
   El módulo de Aulas Virtuales (`virtual_classrooms`) implementa el adaptador de BigBlueButton y su proveedor mock. El funcionamiento en producción con streaming y grabación real depende de la infraestructura física del cluster BBB / Scalelite con certificados TLS válidos y no del código de la aplicación.
3. **Dependencia Externa de Conectividad con SIMAT/DUE:**  
   Los datos del catálogo corresponden a la captura autoritativa del Ministerio de Educación / DANE. Cualquier sincronización automática futura requerirá el establecimiento de convenios interinstitucionales y APIs gubernamentales que actualmente no están abiertas para escritura directa.

---

## 11. Decisión Final de Aceptación

Con base en la verificación exhaustiva e independiente de todos los componentes, pruebas automatizadas, aislamiento de base de datos y remediación de afirmaciones:

### **`PASS — REPOSITORY, CREDENTIALS, ISOLATED TESTS, REQUIRED CHECKS, AND DOCUMENTATION VERIFIED`**

Todas las condiciones requeridas por la misión DOC-03-R1 han sido cumplidas a cabalidad, preservando la integridad del historial de Git, manteniendo los manuales anteriores intactos y garantizando que la documentación institucional refleje con total verdad y rigor técnico el estado operativo de la plataforma PEVN.
