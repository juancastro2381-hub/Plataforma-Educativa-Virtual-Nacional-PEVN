# PEVN — GUION DE DEMOSTRACIÓN EN VIVO (RUNBOOK)
## SECUENCIAS PASO A PASO PARA PRESENTACIÓN A AUTORIDADES GUBERNAMENTALES (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco Metodológico:** AI Software Factory v1.2 — Live Government Demonstration Protocol  
**Fecha:** 21 de Septiembre de 2026  
**Seguridad de Datos:** Datos 100% sintéticos y anonimizados (cero PII real de menores)  

---

## 1. Normas Generales de la Demostración

1. **Protección Absoluta de Datos:** Bajo ninguna circunstancia se presentarán datos reales de estudiantes, docentes o acudientes. Toda la información en pantalla corresponde a datos semilla de demostración (*QA Seed Data*).
2. **Entorno Controlado:** La demostración puede correr en un entorno local (FastAPI en `:8000`, React Vite en `:3000`, PostgreSQL en `:5433`) o en un servidor de Staging/Piloto con dominio de prueba.
3. **Plan de Contingencia y Fallback:** Cada escenario define un plan de respaldo inmediato por si se presenta lentitud de red, fallos de caché o discrepancias imprevistas.

---

## 2. Escenario A — Demostración Ejecutiva (10 a 15 Minutos)

- **Objetivo:** Demostrar a Ministros, Viceministros, Secretarios de Educación y Directores de Tecnología el valor estratégico de PEVN como plataforma soberana, unificada y multi-inquilino que articula el catálogo nacional de colegios, la soberanía territorial y el acceso diferencial por roles.
- **Audiencia:** Ministros, Viceministros (MEN / MinTIC), Secretarios de Educación, Rectores y Asesores de Despacho.
- **Estado Inicial del Sistema:** Servicios activos (`:8000` y `:3000`), catálogo DANE precargado, colegio demostrativo sembrado: *"Institución Educativa Técnica Nacional (DANE 111001000001)"*.

### 2.1 Cuentas de Acceso para el Escenario A
- `superadmin_demo` / `P3vn.Dem0*2026!` (Rol: SuperAdmin Global / Nivel 100).
- `secretaria_antioquia` / `P3vn.Dem0*2026!` (Rol: Territorial Leader / Nivel 80).
- `rector_nacional` / `P3vn.Dem0*2026!` (Rol: Rector / Nivel 70).

### 2.2 Secuencia de Acciones Ejecutivas

| Minuto | Actor / Vista | Acción a Ejecutar | Resultado Esperado en Pantalla | Evidencia Visible | Plan de Fallback |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **00–03** | `superadmin_demo` en `/admin/institutions` | 1. Iniciar sesión.<br>2. Navegar a *Aprovisionamiento Institucional*.<br>3. Buscar colegio por código DANE oficial (ej. `111001000001`) o nombre. | Se muestra la ficha oficial del colegio con su código DANE, municipio, sedes activas y estado de acreditación de Rectoría. | Tarjeta oficial de la institución con sello DANE y lista de sedes (*campuses*). | Si la búsqueda DANE tarda, utilizar el filtro rápido por departamento "Antioquia" o "Bogotá D.C.". |
| **03–07** | `secretaria_antioquia` en `/analytics/territorial` | 1. Cambiar de usuario a la Secretaría de Educación.<br>2. Mostrar el *Tablero de Analítica Territorial*. | Gráficas agregadas de cobertura escolar por municipios, porcentaje de matrícula y capacidad instalada de aulas sin exponer datos privados de alumnos. | Gráfico de distribución geográfica y tabla de indicadores de retención escolar. | Presentar vista estática de indicadores agregados precargados en caché. |
| **07–12** | `rector_nacional` en `/academic` | 1. Iniciar sesión como Rector institucional.<br>2. Mostrar el *Academic Hub*: Años Lectivos, Sedes, Grados y Padrón SIMAT.<br>3. Demostrar el aislamiento institucional (un colegio no puede ver datos de otro). | Se despliega la consola directiva soberana del colegio con sus sedes físicas, salones, libro de matrículas y docentes nombrados. | Censo oficial del colegio, alertas de capacidad de aula y botón de invitación docente. | Navegar directamente a `/academic/students` si la vista principal demora en cargar tarjetas. |
| **12–15** | Presentador | Conclusiones ejecutivas y apertura a preguntas breves. | Enfatizar: Soberanía nacional, cero costos de licenciamiento privativo y propiedad de los datos por parte del Estado colombiano. | Documento maestro de arquitectura y licencia Apache-2.0. | N/A |

- **Riesgos Identificados:** Desconexión de internet local si los assets de fuentes o CDN no cargan; mitigado mediante Service Worker y caché local PWA.

---

## 3. Escenario B — Demostración Funcional Misional (25 a 35 Minutos)

- **Objetivo:** Mostrar la jornada completa del servicio educativo a través de los cuatro actores clave: **Rector $\rightarrow$ Docente $\rightarrow$ Estudiante $\rightarrow$ Acudiente**, abarcando tareas, entregas de archivos, calificaciones SIEE (Decreto 1290), observador de convivencia (Ley 1620) y circulares con acuse digital.
- **Audiencia:** Directores de Calidad y Cobertura del MEN, Coordinadores Académicos, Directivos Docentes y Líderes Pedagógicos.
- **Estado Inicial del Sistema:** Estudiante ficticio *"Juan Camilo Rodríguez"* matriculado en Grado 10-A. Docente titular *"Prof. Gabriel Restrepo"* asignado a la materia "Filosofía".

### 3.1 Cuentas de Acceso para el Escenario B
- `docente_demo` / `P3vn.Dem0*2026!` (Rol: Teacher / Nivel 50).
- `estudiante_demo` / `P3vn.Dem0*2026!` (Rol: Student / Nivel 20).
- `acudiente_demo` / `P3vn.Dem0*2026!` (Rol: Guardian / Nivel 10).
- `rector_demo` / `P3vn.Dem0*2026!` (Rol: Rector / Nivel 70).

### 3.2 Secuencia de Acciones Funcionales

| Minuto | Actor / Vista | Acción a Ejecutar | Resultado Esperado en Pantalla | Evidencia Visible | Plan de Fallback |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **00–07** | `docente_demo` en `/teacher/activities` | 1. Ingresar al Portal Docente.<br>2. Ver carga académica y salones asignados.<br>3. Crear una actividad académica: *"Taller de Ética y Ciudadanía"*, modalidad `FILE`, ponderación 20%, plazo UTC.<br>4. Guardar borrador y luego pulsar **"Publicar Actividad"**. | La actividad transiciona a estado `PUBLISHED` y queda inmediatamente visible en la planilla y para los alumnos del grupo 10-A. | Tarjeta de actividad con insignia verde "Publicada", contador de entregas `0 / 32` y modal de persistencia. | Si el docente olvida completar la ponderación, el formulario valida en rojo indicando el campo requerido. |
| **07–15** | `estudiante_demo` en `/student` | 1. Abrir sesión del alumno en pestaña de incógnito.<br>2. El Dashboard muestra la alerta de nueva tarea pendiente.<br>3. Abrir la tarea, ver instrucciones y cargar un archivo PDF de entrega (`taller_filosofia_camilo.pdf`).<br>4. Pulsar **"Realizar Entrega Formal"**.<br>5. Ir a *Circulares*: Leer circular sobre "Salida Pedagógica" y firmar **Acuse de Recibo**. | 1. La tarea cambia a estado `SUBMITTED` con estampa de tiempo en verde.<br>2. La circular recibe el sello *"Acuse de recibo firmado digitalmente"*. | Sello digital con fecha/hora UTC y bloqueo del botón para evitar firmas duplicadas. | Si el archivo de prueba supera 10 MB, el modal alerta de forma amigable el límite de tamaño. |
| **15–23** | `docente_demo` en `/teacher/activities` | 1. Regresar a la vista docente.<br>2. El botón de la actividad ahora muestra `📥 Entregas (1)`.<br>3. Abrir modal de entregas, previsualizar entrega del estudiante.<br>4. Simular devolución pedagógica (`RETURNED`) solicitando complementar o asignar nota directa (ej. `4.50` - Desempeño Superior).<br>5. Ir a *Calificaciones SIEE* y verificar la integración en la planilla de notas. | La nota ingresa a la planilla oficial. El sistema calcula automáticamente el promedio ponderado y mapea a la escala nacional (*Superior*). | Planilla con nota definitiva, semáforo de colores SIEE y registro de autoría docente. | Usar el selector de filtro por período si la planilla no selecciona el período 1 por defecto. |
| **23–29** | `acudiente_demo` en `/guardian` | 1. Iniciar sesión como la madre/padre del alumno.<br>2. Mostrar el **Selector de Hijos** (conmuta entre 2 hijos si existen).<br>3. Ver el progreso de tareas del hijo y la nota recientemente asentada.<br>4. Ir a *Observador de Convivencia*: Inspeccionar una anotación Tipo I con compromiso restaurativo.<br>5. Firmar acuse familiar de la circular escolar. | La familia tiene visibilidad transparente y en tiempo real del desempeño de su hijo, reforzando la corresponsabilidad educativa (Ley 1620). | Tarjeta del estudiante con notas, asistencias, observador y sello de firma parental. | Si el acudiente tiene un solo hijo vinculado, mostrar cómo la vista se adapta sin error. |
| **29–35** | `rector_demo` en `/academic/evaluations` | 1. Ingresar como Rector.<br>2. Demostrar el cierre oficial del período académico.<br>3. Mostrar cómo las notas se sellan de forma inmutable (`is_locked=True`).<br>4. Visualizar el **Boletín Oficial de Calificaciones** consolidado con ranking del grupo. | El boletín se renderiza estructurado por áreas fundamentales, materias, logros, inasistencias y puesto en el salón. | Visor reactivo de boletín institucional oficial conforme al Decreto 1290 de 2009. | Mostrar la sábana de notas grupal si se desea ver el consolidado de todo el curso. |

---

## 4. Escenario C — Demostración Técnica y de Ciberseguridad (20 a 30 Minutos)

- **Objetivo:** Demostrar a los oficiales de seguridad de la información (CISO / ColCERT / MinTIC), arquitectos de software y auditores forenses la solidez de los controles técnicos, la ausencia de vulnerabilidades comunes, el aislamiento de memoria de tokens, la protección Anti-IDOR y la trazabilidad inmutable.
- **Audiencia:** Oficiales de Ciberseguridad, Auditores de Sistemas de la Contraloría/Procuraduría, Ingenieros DevSecOps y Arquitectos de TI.
- **Estado Inicial del Sistema:** Herramientas de desarrollador abiertas (F12 / Network / Console) y terminal con base de datos PostgreSQL accesible.

### 4.1 Secuencia de Acciones Técnicas

| Minuto | Vector Auditado | Acción Técnica en Vivo | Evidencia Demostrada | Veredicto Técnico |
| :---: | :--- | :--- | :--- | :---: |
| **00–05** | **Higiene de Tokens en Navegador** | 1. Abrir DevTools $\rightarrow$ *Application* $\rightarrow$ *Local Storage*, *Session Storage*, *IndexedDB*.<br>2. Demostrar que están completamente vacíos.<br>3. Abrir *Cookies*: Mostrar la cookie `pevn_refresh_token` marcada con `HttpOnly`, `SameSite=Strict`, `Path=/api/v1/auth`. | Se demuestra que **el Access Token JWT solo vive en memoria JavaScript**, impidiendo el robo masivo de credenciales por ataques XSS. | **PASS** |
| **05–10** | **Detección Activa de Replay de Sesión** | 1. Capturar un refresh token en una petición HTTP.<br>2. Ejecutar un refresco legítimo (el servidor rota el token y emite uno nuevo).<br>3. Reenviar mediante cURL o Postman el refresh token antiguo (simulando un atacante que interceptó el token previo). | El servidor detecta `replaced_by_token_id`, revoca de inmediato **toda la familia de tokens**, rechaza la petición con `HTTP 401` y expulsa al usuario activo. | **PASS** |
| **10–15** | **Barrera Anti-IDOR (Blind 404)** | 1. Estando autenticado como Docente del Colegio A, tomar el UUID de un estudiante del Colegio B.<br>2. Hacer una petición directa a `GET /api/v1/students/{uuid_colegio_b}`. | El servidor responde **`404 Not Found`** (no 403), imposibilitando al atacante deducir si el ID existe en otra institución del país. | **PASS** |
| **15–20** | **Criptografía BigBlueButton** | 1. Abrir el código de `BBBAdapter.py` en vivo.<br>2. Mostrar el cálculo determinístico de firma: `checksum = SHA(call_name + query + secret)`.<br>3. Ejecutar la prueba unitaria en terminal: `pytest tests/test_meeting_provider.py -v`. | 13 de 13 pruebas aprueban en milisegundos, evidenciando el cumplimiento exacto del protocolo internacional de BigBlueButton. | **PASS** |
| **20–25** | **Auditoría Inmutable (Zero-Secrets)** | 1. En terminal, consultar la tabla `audit_logs` en PostgreSQL.<br>2. Inspeccionar los metadatos JSON de inicios de sesión y cambios de contraseña.<br>3. Demostrar que los campos sensibles aparecen estrictamente como `"[REDACTED]"`. | Trazabilidad inmutable forense sin violación de la Ley 1581 de 2012 de protección de datos. | **PASS** |
| **25–30** | **Calidad y No-Regresión** | 1. Ejecutar el linter y tipado estricto en vivo: `ruff check backend`, `mypy backend/app`.<br>2. Mostrar que no existen warnings ni errores de tipado en código fuente. | Cero deuda técnica detectable; conformidad con estándares de la industria. | **PASS** |

---

## 5. Matriz de Riesgos y Acciones de Mitigación en Vivo

| Riesgo Durante la Demo | Causa Potencial | Acción Inmediata de Mitigación |
| :--- | :--- | :--- |
| **Fallo de inicio de sesión** | Contraseña mal escrita o bloqueo por 5 intentos fallidos previos. | Usar el comando CLI para desbloquear usuario o reiniciar sesión con otra cuenta de prueba. |
| **Página en blanco al recargar** | Pérdida del token de memoria tras recarga manual en navegador. | El Axios interceptor refresca automáticamente la sesión mediante la cookie HttpOnly en menos de 300 ms. |
| **Lentitud en respuesta de API** | Base de datos local ejecutando vacuum o cold-start de Docker. | Ejecutar previamente el script `check_env.sh` para calentar la caché y confirmar conectividad en `/api/v1/ready`. |
| **Pregunta capciosa sobre BigBlueButton** | Evaluador pregunta si el aula virtual que ve en pantalla es un servidor real. | **Responder con total honestidad:** Indicar que la prueba en pantalla opera mediante el Mock Provider verificado y mostrar la especificación de hardware lista para el despliegue del servidor físico. |
