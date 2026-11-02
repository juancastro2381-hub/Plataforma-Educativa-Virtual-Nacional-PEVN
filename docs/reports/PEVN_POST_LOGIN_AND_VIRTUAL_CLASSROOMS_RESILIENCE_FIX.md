# PEVN — INFORME DE RESOLUCIÓN TÉCNICA: REDIRECCIÓN POST-LOGIN Y RESILIENCIA DE AULAS VIRTUALES

**Documento:** `docs/reports/PEVN_POST_LOGIN_AND_VIRTUAL_CLASSROOMS_RESILIENCE_FIX.md`  
**Plataforma:** Plataforma Educativa Virtual Nacional (PEVN) — República de Colombia  
**Fecha:** 1 de Noviembre de 2026  
**Responsable:** Arquitecto Principal de Software, Especialista FastAPI/React y Confiabilidad  
**Estado:** **IMPLEMENTADO, VERIFICADO Y CERTIFICADO**

---

## 1. RESUMEN EJECUTIVO

El presente informe documenta la investigación forense, remediación y verificación empírica de dos incidentes de experiencia de usuario y resiliencia funcional en la Plataforma Educativa Virtual Nacional (**PEVN**):

1. **Problema 1 (Redirección Mandatoria Post-Login al Dashboard de Bienvenida):**  
   Tras un inicio de sesión interactivo exitoso, los usuarios eran dirigidos de forma errática a rutas previas fallidas o protegidas (por ejemplo, `/virtual-classrooms`), eludiendo el panel de bienvenida institucional (`/dashboard`) donde se visualizan los roles, sedes y accesos del usuario autenticado. Se reestructuró el flujo para garantizar que todo login interactivo aterrice obligatoriamente en `/dashboard`.

2. **Problema 2 (Resiliencia de Aulas Virtuales sin Conectividad BigBlueButton):**  
   Al acceder a `/virtual-classrooms`, la plataforma arrojaba un error `HTTP 500` ("Error en Aulas Virtuales"), bloqueando tanto el listado como la programación de clases virtuales cuando el servidor de videoconferencia BigBlueButton (BBB) no estaba aprovisionado o presentaba credenciales incompletas. Se desacopló la gestión y consulta de sesiones programadas (Capacidades A y B) de la ejecución en vivo de videoconferencias (Capacidad C), garantizando respuestas `HTTP 200` para listado/creación y manejando la ausencia de proveedor con `HTTP 503 BBB_NOT_CONFIGURED` informativo y controlado.

3. **Dictamen Adicional (Aislamiento de Períodos Académicos y Replicación de Notas):**  
   Se verificó forensemente la integridad de la matriz de calificaciones en el Portal Estudiantil y el Informe Final Acumulado (`/student?tab=grades`), confirmando que las notas de Período 1 (Ciencias Naturales $3.37$ y Matemáticas $3.50$) permanecen estrictamente aisladas en P1 y que las columnas P2 y P3 muestran su estado pendiente (`—`), de acuerdo con la máquina de estados de ciclo de vida de períodos de Decreto 1290 y SIEE.

---

## 2. CAUSA RAÍZ FORENSE

### 2.1 Causa Raíz de la Redirección Post-Login
En `frontend/src/components/auth/RequireAuth.tsx`, el componente interceptaba a usuarios no autenticados y redirigía a `/login` inyectando en el estado del historial la ruta de origen:
```tsx
// Código anterior que causaba la fuga hacia rutas fallidas:
<Navigate to="/login" state={{ from: location }} replace />
```
Posteriormente, en `frontend/src/pages/Login.tsx`, tras un inicio de sesión interactivo exitoso, el formulario consultaba `locationState?.from?.pathname` y forzaba la redirección a dicha ruta. Si el usuario había experimentado un error previo (como el fallo en `/virtual-classrooms`), quedaba atrapado en un ciclo que lo devolvía a la página con fallo en lugar de mostrar su panel institucional de bienvenida.

### 2.2 Causa Raíz del Error HTTP 500 en Aulas Virtuales
Durante la remediación previa de seguridad en el commit `fd84e3b` (`SEC-010: Validación de esquemas URL y Anti-XSS en Aulas Virtuales`), se introdujo un bloque de validación de `redirect_url` de manera accidental en los endpoints de listado, creación, consulta y finalización de aulas en `backend/app/api/v1/endpoints/virtual_classrooms.py`.

Dado que dichos endpoints no declaran el argumento `redirect_url` en su firma, la ejecución de:
```python
if redirect_url:
    ...
```
disparaba en tiempo de ejecución un `NameError: name 'redirect_url' is not defined`. Starlette capturaba este error no manejado y emitía una respuesta genérica `HTTP 500 INTERNAL_SERVER_ERROR`.

---

## 3. MATRIZ DE DESACOPLAMIENTO DE CAPACIDADES EN AULAS VIRTUALES

Para conferir alta disponibilidad a la plataforma frente a dependencias externas, se separaron las tres capacidades operativas del subsistema de Aulas Virtuales:

| Capacidad | Descripción Operativa | Dependencia Externa | Comportamiento sin BBB | Código HTTP |
|---|---|---|---|:---:|
| **Capacidad A: Programación y Gestión** | Agendar, editar y cancelar clases virtuales vinculadas a asignaturas académicas. | PostgreSQL (Base de datos local) | Operativa 100%. Persiste la sesión en base de datos. Si BBB no está configurado, registra advertencia y permite agendar. | `201 CREATED` / `200 OK` |
| **Capacidad B: Consulta y Visualización** | Listar aulas programadas, en curso o finalizadas, con filtros de estado y asignación. | PostgreSQL (Base de datos local) | Operativa 100%. Retorna colección de aulas con metadatos del estado del proveedor (`provider_configured: false`). | `200 OK` |
| **Capacidad C: Ejecución en Vivo (BBB)** | Iniciar reunión (*Launch*) u obtener URL de acceso para docentes y alumnos (*Join*). | Servidor BigBlueButton externo | Controlada y tipada. Retorna excepción controlada `BBBNotConfiguredError` o `MeetingProviderConnectionError`. | `503 SERVICE UNAVAILABLE` |

---

## 4. DETALLE DE CAMBIOS IMPLEMENTADOS EN BACKEND

### 4.1 Excepciones y Adaptador de Videoconferencia
- **`backend/app/core/meeting/exceptions.py`**:
  Se incorporó `BBBNotConfiguredError(MeetingProviderError)` tipada con código `"BBB_NOT_CONFIGURED"` y estado `HTTPStatus.SERVICE_UNAVAILABLE` (503).
- **`backend/app/core/meeting/bbb_adapter.py`**:
  Al calcular checksums sin un `_shared_secret` válido configurado, lanza `BBBNotConfiguredError` en lugar de fallar con errores de codificación criptográfica.
- **`backend/app/core/meeting/factory.py`**:
  Se implementó la función `check_meeting_provider_status()`, que evalúa la presencia de credenciales (`BBB_BASE_URL` y `BBB_SHARED_SECRET`) y retorna un estado descriptivo sin levantar excepciones no controladas.

### 4.2 Esquemas Pydantic y Servicio de Dominio
- **`backend/app/schemas/virtual_classroom.py`**:
  Se agregaron los campos `provider_configured: bool = True`, `provider_status: str = "CONFIGURED"` y `provider_message: str | None = None` a `VirtualClassroomListResponse`.
- **`backend/app/services/virtual_classroom_service.py`**:
  - `create_virtual_classroom`: Permite agendar sesiones en PostgreSQL de manera resiliente si el proveedor BBB no está disponible en el momento del agendamiento.
  - `launch_virtual_classroom` y `generate_join_url`: Verifican la disponibilidad del proveedor y retornan `BBBNotConfiguredError` (503) controlado sin exponer rutas internas ni cadenas de conexión.
  - `end_virtual_classroom`: Permite marcar la sesión como finalizada en la base de datos aun si el nodo BBB no responde.

### 4.3 Endpoints FastAPI
- **`backend/app/api/v1/endpoints/virtual_classrooms.py`**:
  - Se eliminaron los bloques `if redirect_url:` huérfanos de los métodos `create_virtual_classroom`, `list_virtual_classrooms`, `get_virtual_classroom`, `launch_virtual_classroom`, `end_virtual_classroom` y `list_classroom_attendances`.
  - Se añadió el endpoint `GET /api/v1/virtual-classrooms/provider-status` con control de permisos RBAC para inspección proactiva del frontend.
  - Se expuso el estado del proveedor en la respuesta del listado principal.

---

## 5. DETALLE DE CAMBIOS IMPLEMENTADOS EN FRONTEND

### 5.1 Enrutamiento y Autenticación
- **`frontend/src/components/auth/RequireAuth.tsx`**:
  Se eliminó `state={{ from: location }}` en la redirección hacia `/login`. Las solicitudes no autenticadas envían al usuario limpiamente a la pantalla de acceso.
- **`frontend/src/pages/Login.tsx`**:
  Tanto en el submit interactivo del formulario como en la verificación de sesión ya autenticada (`useEffect`), el destino forzoso es `/dashboard`:
  ```tsx
  navigate('/dashboard', { replace: true })
  ```

### 5.2 Tipos y Servicios
- **`frontend/src/types/virtual_classroom.ts`**:
  Se expandió `VirtualClassroomListResponse` con `provider_configured`, `provider_status` y `provider_message`.
- **`frontend/src/services/virtualClassroom.ts`**:
  Se agregó el cliente `getProviderStatus()` consumiendo `/api/v1/virtual-classrooms/provider-status`.

### 5.3 Vista de Aulas Virtuales (`VirtualClassroomsView.tsx`)
- **Banner Informativo Institucional:** Si `!isProviderConfigured`, se despliega un panel estilizado en azul/índigo notificando amigablemente:
  > *"Estado: Servicio de videoconferencias pendiente de habilitación. La programación y consulta de clases permanecen operativas. Las funciones de unión e inicio se activarán una vez configurado el servidor institucional de videoconferencias."*
- **Estado Vacío Amigable en Español:** Cuando no existen clases agendadas, se presenta el mensaje institucional:
  > *"Aulas Virtuales — Todavía no hay clases virtuales programadas para tu institución. Las clases programadas aparecerán aquí cuando estén disponibles."*
- **Botones de Acción Protegidos:** Los botones "Unirse" e "Iniciar Clase" se deshabilitan con tooltip explicativo cuando el proveedor no está activo, impidiendo clics ciegos que deriven en alertas de error rojas.
- **Manejo Resiliente de Errores 503:** Las respuestas `BBB_NOT_CONFIGURED` disparan notificaciones informativas no intrusivas en lugar de alertas rojas de fallo sistémico.

---

## 6. VERIFICACIÓN FORENSE: AISLAMIENTO DE PERÍODOS ACADÉMICOS Y CALIFICACIONES

En respuesta a la revisión forense del Portal Estudiantil (`localhost:3000/student?tab=grades`):

1. **Investigación de Datos en Base de Datos Real (`pevn_db`):**
   - Para la estudiante de prueba Danna González (SIMAT: SIMAT-2026-004, Institución ALEGRÍA DE APRENDER, Grupo 101, Año 2027), se verificó el registro en la base de datos PostgreSQL:
     * Ciencias Naturales: $3.37$ registrado exclusivamente para el Período 1.
     * Matemáticas: $3.50$ consolidado para el Período 1 a partir de actividades calificadas en el LMS.
     * En la tabla `period_subject_grades` **no existen registros para Período 2 ni Período 3**.
2. **Ejecución del Motor de Aislamiento de Ciclo de Vida:**
   - La función `resolve_period_lifecycle_status(period, all_periods)` evalúa la secuencia cronológica de los términos de evaluación:
     * Período 1: `ACTIVE` (primer período abierto).
     * Período 2: `SCHEDULED` (período futuro no iniciado).
     * Período 3: `SCHEDULED` (período futuro no iniciado).
3. **Cero Replicación en Períodos Futuros:**
   - La API `/api/v1/evaluations/report-cards/student/{student_id}/year-end` retorna:
     ```json
     {
       "period_grades": {
         "1": { "score": 3.37, "weight": 33.33 }
       }
     }
     ```
   - El componente `OfficialYearEndReportCard.tsx` renderiza `pGrade ? pGrade.score.toFixed(2) : '—'`. Dado que las claves `"2"` y `"3"` no existen en `period_grades`, las columnas P2 y P3 muestran estrictamente `'—'`, eliminando por completo cualquier replicación anómala.
4. **Estado Provisional de Fin de Año:**
   - Dado que el año lectivo se encuentra activo y los períodos 2 y 3 no han concluido, la nota definitiva anual permanece como `None` (`Pendiente`) y el dictamen de promoción se mantiene en estado `PENDIENTE` bajo el Decreto 1290 de 2009.

---

## 7. RESULTADOS DE PRUEBAS AUTOMATIZADAS

### 7.1 Backend — Suite de Resiliencia de Aulas Virtuales (`test_virtual_classrooms_resilience.py`)
Comando: `pytest backend/tests/test_virtual_classrooms_resilience.py -v`
- `test_01_classroom_listing_succeeds_without_bbb_configuration`: **PASSED**
- `test_02_empty_classroom_listing_returns_http_200`: **PASSED**
- `test_03_existing_scheduled_classrooms_remain_visible_without_bbb`: **PASSED**
- `test_04_create_scheduled_classroom_succeeds_without_bbb`: **PASSED**
- `test_05_bbb_join_returns_controlled_bbb_not_configured_503`: **PASSED**
- `test_06_bbb_launch_returns_controlled_bbb_not_configured_503`: **PASSED**
- `test_07_provider_outage_returns_controlled_503`: **PASSED**
- `test_08_database_failure_is_not_masked`: **PASSED**
- `test_09_unauthorized_users_remain_blocked`: **PASSED**
- `test_10_tenant_isolation_remains_enforced`: **PASSED**
- `test_11_get_provider_status_endpoint`: **PASSED**

**Resultado Total Backend:** **11/11 PASSED (100%)**

### 7.2 Backend — Regresión de Aislamiento de Períodos y Currículo (`test_academic_curriculum_and_report_cards.py`)
Comando: `pytest backend/tests/test_academic_curriculum_and_report_cards.py -v`
- 14 pruebas de aislamiento de notas, no replicación en P2/P3 e idempotencia curricular: **14/14 PASSED (100%)**

### 7.3 Frontend — Suites de Autenticación, Aulas Virtuales y Boletines
- `src/test/Auth.test.tsx`: **6/6 PASSED**
- `src/test/VirtualClassrooms.test.tsx`: **6/6 PASSED**
- `src/test/OfficialReportCard.test.tsx`: **10/10 PASSED**
- `tsc --noEmit` (Verificación estricta de tipos TypeScript): **0 errores**
- `vite build` (Compilación limpia de producción): **Completada con éxito**

---

## 8. PROCEDIMIENTO DE VERIFICACIÓN MANUAL

Para comprobar manualmente el comportamiento en el entorno local:

1. **Verificación de Redirección Post-Login:**
   - Inicie sesión con cualquier usuario en `http://localhost:3000/login`.
   - Confirme que el navegador siempre aterriza en `http://localhost:3000/dashboard`, mostrando el saludo institucional personalizado (*"Bienvenido, Mauro Díaz"* o el nombre correspondiente).
   - Compruebe que la navegación interna a otros módulos funciona fluidamente.

2. **Verificación de Aulas Virtuales sin BBB:**
   - Acceda a `http://localhost:3000/virtual-classrooms`.
   - Constatar que no se emite error `HTTP 500`.
   - Visualizar el banner informativo azul indicando que el servicio de videoconferencia está pendiente de habilitación.
   - Constatar el estado vacío con texto institucional en español (*"Aulas Virtuales — Todavía no hay clases virtuales..."*).
   - Compruebe que un docente puede agendar una nueva clase sin que se produzca una excepción.

3. **Verificación del Aislamiento de Calificaciones:**
   - Inicie sesión como estudiante o ingrese a `http://localhost:3000/student?tab=grades`.
   - Seleccione la pestaña *"🎓 Informe Final y Promoción"*.
   - Verifique que Ciencias Naturales tiene $3.37$ en P1 y que las columnas P2 y P3 exhiben `'—'`.
   - Verifique que Matemáticas tiene $3.50$ en P1 y que P2 y P3 exhiben `'—'`.
   - Verifique que la columna Definitiva indica *"Pendiente"* y que la promoción señala *"Año lectivo en curso — Dictamen provisional"*.

---

## 9. CONCLUSIÓN Y DICTAMEN DE LIBERACIÓN

Las dos fallas operativas reportadas han sido solventadas de raíz en el código fuente, preservando de manera estricta el modelo de control de acceso RBAC, la seguridad multi-inquilino y el aislamiento de datos curriculares del SIEE.

$$\mathbf{DICTAMEN\ TÉCNICO:}\quad \mathbf{APROBADO\ PARA\ OPERACIÓN\ LOCAL\ Y\ DESPLIEGUE}$$

Las modificaciones se encuentran verificadas contra bases de datos aisladas y en memoria, listas para ser consolidadas cuando el usuario lo autorice explícitamente.

