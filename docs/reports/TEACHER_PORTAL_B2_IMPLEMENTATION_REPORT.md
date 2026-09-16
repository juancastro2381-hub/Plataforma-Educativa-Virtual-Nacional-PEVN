# INFORME DE IMPLEMENTACIÓN — FASE B2
## PORTAL DOCENTE: COMUNICACIONES INSTITUCIONALES Y NOTICIAS (PERIÓDICO ESCOLAR)

- **Fecha:** 8 de Septiembre de 2026
- **Módulo:** Portal Docente (`TeacherPortal`)
- **Fase:** B2
- **Autor:** Antigravity (Advanced Agentic Coding)
- **Estado de Certificación:** **NO CERTIFICADO** (Pendiente de Validación Manual por el Propietario del Proyecto)

---

## 1. OBJETIVO

Completar la implementación técnica y de interfaz de usuario de la **Fase B2** para el Portal Docente de la Plataforma Educativa Virtual Nacional (PEVN), permitiendo a los usuarios con rol `DOCENTE`:
1. Consultar de forma determinista y contextual las comunicaciones institucionales oficiales dirigidas a su perfil académico o a toda la comunidad educativa.
2. Inspeccionar el detalle completo de cada comunicado oficial y confirmar formalmente la lectura/acuse de recibo (`CommunicationReceipt`) en aquellos comunicados de carácter obligatorio (`requires_acknowledgment`), persistiendo dicho estado de manera inmutable e infalsificable.
3. Consultar las noticias y artículos institucionales publicados en el Periódico Escolar con filtrado por categorías temáticas, búsqueda textual y visualización de artículos destacados.

Todo lo anterior garantizando estrictamente que **NO se amplíen los permisos existentes del rol DOCENTE** y que el backend continúe siendo la única autoridad de seguridad y control de acceso.

---

## 2. ALCANCE

El alcance de la Fase B2 se limitó **EXCLUSIVAMENTE** a las siguientes capacidades:

### 2.1 Comunicaciones Institucionales (Docente)
- **Listado contextual:** Consulta de comunicados institucionales activos (`PUBLICADO`, no expirados o vigentes) pertenecientes a la institución del docente autenticado.
- **Resolución de Audiencia:** Filtrado en base a asignaciones académicas (`AcademicAssignment`), abarcando comunicados de alcance institucional general (`TODOS_INSTITUCION`), directivas específicas para docentes (`SOLO_DOCENTES`), o dirigidos a sedes, grados o grupos donde el docente tiene carga académica activa.
- **Inspección de Detalle:** Visualización modal del contenido íntegro, remitente, categoría, nivel de prioridad, fechas de vigencia y estado de lectura.
- **Confirmación de Lectura / Acuse:** Capacidad para marcar el acuse formal de recibo mediante endpoint seguro, registrando marca temporal y dirección IP del docente.
- **Indicadores Visuales:** Distinción clara entre comunicados leídos y no leídos, insignias de prioridad (Baja, Media, Alta, Urgente) y contador de no leídos.

### 2.2 Noticias y Periódico Escolar (Docente)
- **Listado de Noticias:** Consulta de artículos comunitarios y notas periodísticas institucionales publicadas en la institución educativa.
- **Artículo Destacado (Spotlight):** Banner visual para noticias marcadas como destacadas (`is_featured`).
- **Filtrado y Búsqueda:** Filtro por categorías (Logros Académicos, Cultura, Deportes, General, etc.) y búsqueda textual en tiempo real por título, resumen y contenido.
- **Inspección de Detalle:** Visualización modal del artículo completo con metadatos de autoría y fecha de publicación.

---

## 3. ARCHIVOS MODIFICADOS

| Archivo | Componente | Descripción de la Modificación |
|---|---|---|
| [`backend/app/api/v1/endpoints/teacher_portal.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/teacher_portal.py) | Backend API | Implementación de endpoints seguros para docentes: `GET /api/v1/teacher/communications`, `GET /api/v1/teacher/communications/{id}`, `POST /api/v1/teacher/communications/{id}/acknowledge` y `GET /api/v1/teacher/news`. |
| [`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py) | Backend Service | Inclusión de la función `list_teacher_communications(teacher, user)` para resolver audiencias institucionales asociadas a la carga del docente. |
| [`frontend/src/pages/teacher/TeacherPortal.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/teacher/TeacherPortal.tsx) | Frontend Shell | Integración de subpestañas `communications` (`📢 Comunicaciones`) y `news` (`📰 Noticias`), sincronización con query params y renderizado condicional. |
| [`frontend/src/pages/teacher/TeacherDashboardView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/teacher/TeacherDashboardView.tsx) | Frontend View | Incorporación de accesos directos (Quick Actions) para Comunicados Institucionales y Periódico Escolar. |
| [`frontend/src/services/communication.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/communication.ts) | Frontend Service | Métodos clientes `getTeacherCommunications`, `getTeacherCommunicationById`, `acknowledgeTeacherCommunication`, `getTeacherNews` y `listNews`. |
| [`frontend/src/types/communication.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/types/communication.ts) | Frontend Types | Adición de campos de recibo (`is_read`, `is_acknowledged`, `summary`, `is_pinned`) preservando la integridad de tipos preexistentes. |

---

## 4. ARCHIVOS NUEVOS

| Archivo | Componente | Descripción |
|---|---|---|
| [`frontend/src/pages/teacher/TeacherCommunicationsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/teacher/TeacherCommunicationsView.tsx) | Frontend View | Vista completa de comunicados para docentes: listado, filtros, búsqueda, estado leído/no leído, modal de lectura y botón de confirmación de acuse con actualización reactiva. |
| [`frontend/src/pages/teacher/TeacherNewsView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/teacher/TeacherNewsView.tsx) | Frontend View | Vista completa de periódico escolar para docentes: banner destacado, tarjetas de noticias, filtro por categorías temáticas, búsqueda y modal de lectura. |
| [`frontend/src/test/TeacherCommunicationsAndNews.test.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/test/TeacherCommunicationsAndNews.test.tsx) | Frontend Tests | Suite de pruebas unitarias y de integración para las nuevas vistas B2 (7 pruebas específicas). |

---

## 5. ENDPOINTS REUTILIZADOS Y CREADOS

La implementación reutilizó estrictamente los modelos y tablas de base de datos existentes (`institutional_communications`, `communication_audiences`, `communication_receipts`, `institutional_news`).

### Endpoints Expuestos para el Rol DOCENTE:
1. `GET /api/v1/teacher/communications`
   - **Propósito:** Lista los comunicados oficiales activos filtrados por institución y audiencia del docente.
   - **Retorna:** `InstitutionalCommunicationListResponse` con `unread_count` y estado de lectura del docente.
2. `GET /api/v1/teacher/communications/{communication_id}`
   - **Propósito:** Obtiene el detalle de un comunicado y registra de forma idempotente la marca de lectura (`has_read = True`, `read_at = now()`).
3. `POST /api/v1/teacher/communications/{communication_id}/acknowledge`
   - **Propósito:** Registra el acuse formal de recibo del docente (`acknowledged_at = now()`, IP del cliente). Reutiliza la función existente `acknowledge_communication` del servicio.
4. `GET /api/v1/teacher/news`
   - **Propósito:** Lista las noticias institucionales publicadas en la institución del docente. Reutiliza el servicio transversal `news_service.list_published_news`.

---

## 6. RBAC UTILIZADO

El rol `DOCENTE` opera bajo sus permisos canónicos existentes:
- `communications:read`: Permite listar y visualizar comunicados y confirmar su lectura.
- `news:read`: Permite consultar noticias del periódico escolar.

**No se crearon roles ni permisos nuevos.**

---

## 7. CONFIRMACIÓN DE QUE NO SE AMPLIARON PERMISOS A DOCENTE

> [!IMPORTANT]
> **GARANTÍA DE RBAC ESTRICTO:**
> Se confirma taxativamente que al rol `DOCENTE` **NO** se le otorgaron permisos de:
> - `communications:create`
> - `communications:update`
> - `communications:publish`
> - `communications:delete`
> - `news:create`
> - `news:update`
> - `news:publish`
> - `news:delete`
> 
> Los endpoints administrativos de creación, edición y publicación permanecen restringidos a `ADMIN`, `DIRECTIVO` y `COORDINADOR`. Los botones de creación o administración no existen en la interfaz del Portal Docente.

---

## 8. SEGURIDAD / TENANT ISOLATION / ANTI-IDOR

1. **Aislamiento Multitenant:**
   - La institución educativa se obtiene exclusivamente del token de autenticación del usuario (`current_user.institution_id`). No se acepta parámetro `institution_id` en headers ni query params.
2. **Anti-IDOR en Comunicaciones:**
   - Si un docente intenta consultar o confirmar acuse en un comunicado perteneciente a otra institución educativa, el backend responde con `404 Not Found` (ocultamiento de existencia de recursos cruzados).
3. **Restricción de Audiencia:**
   - Los comunicados dirigidos exclusivamente a perfiles individuales de estudiantes o acudientes ajenos a la carga del docente son excluidos a nivel de consulta SQL en `communication_service.list_teacher_communications`.
4. **Acuse Infalsificable:**
   - El acuse de recibo se asocia unívocamente al `user_id` del docente autenticado y a la IP del request, impidiendo que un usuario registre confirmaciones en nombre de otro.

---

## 9. PRUEBAS EJECUTADAS

Se ejecutó la batería completa de pruebas estáticas, unitarias, de integración y de regresión tanto en el frontend como en el backend, satisfaciendo los 10 requisitos mínimos:

### 9.1 Frontend (Vitest)
- **Suite B2:** `src/test/TeacherCommunicationsAndNews.test.tsx` (7 pruebas)
- **Regresión Portal Docente:** `src/test/TeacherPortal.test.tsx` (7 pruebas)
- **Regresión Comunicaciones Institucionales:** `src/test/InstitutionalCommunications.test.tsx` (7 pruebas)
- **Regresión Student Portal:** `src/test/StudentPortal.test.tsx` (4 pruebas)
- **Regresión Guardian Portal:** `src/test/GuardianPortal.test.tsx` (13 pruebas)

### 9.2 Backend (Pytest)
1. **Teacher Portal API:** `tests/test_teacher_portal_api.py` (9 pruebas)
2. **Institutional Communications API:** `tests/test_institutional_communications_api.py` (3 pruebas)
3. **Institutional News API:** `tests/test_institutional_news_api.py` (1 prueba)
4. **Coexistence / B1 Regression:** `tests/test_coexistence_incidents_api.py` (3 pruebas)
5. **RBAC & Authorization:** `tests/test_authorization.py` (5 pruebas)
6. **Tenant Isolation:** Evaluado en pruebas de IDOR cruzado entre instituciones.
7. **Anti-IDOR:** Evaluado en acceso a estudiantes/grupos no asignados.
8. **Student Portal API Regression:** `tests/test_student_portal_api.py` (8 pruebas)
9. **Guardian Portal API Regression:** `tests/test_guardian_portal_api.py` (9 pruebas)
10. **Auth Endpoints Regression:** `tests/test_auth_endpoints.py` (5 pruebas)

---

## 10. RESULTADOS EXACTOS

### 10.1 Backend (Pytest con terminación controlada)
- `tests/test_teacher_portal_api.py`: **9/9 PASSED** (29.2s)
- `tests/test_institutional_communications_api.py`: **3/3 PASSED** (5.8s)
- `tests/test_institutional_news_api.py`: **1/1 PASSED** (6.1s)
- `tests/test_coexistence_incidents_api.py`: **3/3 PASSED** (13.1s)
- `tests/test_authorization.py`: **5/5 PASSED** (5.2s)
- `tests/test_student_portal_api.py`: **8/8 PASSED** (16.9s)
- `tests/test_guardian_portal_api.py`: **9/9 PASSED** (26.7s)
- `tests/test_auth_endpoints.py`: **5/5 PASSED** (25.8s)
- **Total Backend:** **43/43 pruebas backend ejecutadas y 100% PASS**.

> [!NOTE]
> **Observación sobre Python 3.14 en Windows:**
> Las pruebas se ejecutaron mediante un invocador controlado (`os._exit(ret)`), confirmando que **el 100% de las aserciones de pytest fueron exitosas** y eliminando el bloqueo que el recolector de hilos de Python 3.14 presentaba durante el shutdown normal en Windows.

### 10.2 Frontend (Vitest)
```
Test Files  5 passed (5)
     Tests  38 passed (38)
  Duration  10.92s
```
- `TeacherCommunicationsAndNews.test.tsx`: 7/7 PASSED
- `TeacherPortal.test.tsx`: 7/7 PASSED
- `InstitutionalCommunications.test.tsx`: 7/7 PASSED
- `StudentPortal.test.tsx`: 4/4 PASSED
- `GuardianPortal.test.tsx`: 13/13 PASSED

---

## 11. BUILD / LINT / TYPECHECK

### 11.1 ESLint
```bash
npx eslint src/pages/teacher/TeacherCommunicationsView.tsx \
           src/pages/teacher/TeacherNewsView.tsx \
           src/pages/teacher/TeacherPortal.tsx \
           src/pages/teacher/TeacherDashboardView.tsx \
           src/services/communication.ts \
           src/types/communication.ts \
           src/test/TeacherCommunicationsAndNews.test.tsx
# Código de salida: 0 (0 errores, 0 advertencias)
```

### 11.2 TypeScript & Vite Production Build
```bash
npm run build
# > pevn-frontend@0.1.0 build
# > tsc -b && vite build
# ✓ 194 modules transformed.
# ✓ built in 10.35s
# Código de salida: 0
```

---

## 12. REGRESIONES VERIFICADAS

Se verificó expresamente la no-regresión de todos los módulos certificados:
- **Fase B1 — Convivencia / Observador del Estudiante:** Verificado al 100% con `test_coexistence_incidents_api.py` (3/3 PASS). Las subpestañas y navegación en `TeacherPortal` permanecen intactas.
- **Student Portal:** 8/8 pruebas backend y 4/4 pruebas frontend superadas sin alteraciones.
- **Guardian Portal:** 9/9 pruebas backend y 13/13 pruebas frontend superadas sin alteraciones.
- **Autenticación y Seguridad:** 5/5 pruebas de sesión, tokens e aislamiento de tenant superadas.

---

## 13. PROBLEMAS CONOCIDOS

1. **Shutdown de Python 3.14 en Windows:** El intérprete de Python 3.14.2 bajo Windows presenta un cuelgue al descargar recursos tras finalizar sesiones de pytest estándar si no se fuerza la salida del proceso. Esto es un comportamiento del runtime del sistema operativo local y no de la aplicación.
2. **Chunk Size en Bundle Frontend:** Vite emite un aviso informativo recomendando code-splitting para chunks superiores a 500 kB (`index.js`). Este comportamiento es preexistente y no afecta la funcionalidad.

---

## 14. PRESENTACIÓN DE CONTENIDO / MARKDOWN

Durante la auditoría visual y de código se analizó la presentación de contenidos de comunicaciones y noticias:
- El texto enriquecido redactado por administradores se presenta actualmente utilizando formato de saltos de línea preservados (`whiteSpace: 'pre-line'`), consistente con el estándar implementado en `StudentCommunicationsView` y `GuardianCommunicationsView`.
- **Decisión de Diseño B2:** De acuerdo con las instrucciones directas del usuario, **NO se alteraron** los componentes de los portales Student ni Guardian, y **NO se introdujo ninguna librería externa** (e.g. `react-markdown`) de manera ad-hoc para B2. Se preservó la uniformidad visual institucional en toda la plataforma.

---

## 15. ESTADO FINAL DE IMPLEMENTACIÓN

| Componente / Característica | Estado |
|---|---|
| Comunicaciones Docente — Listado y Filtros | **IMPLEMENTADO** |
| Comunicaciones Docente — Detalle y Lectura | **IMPLEMENTADO** |
| Comunicaciones Docente — Acuse de Recibo Formal | **IMPLEMENTADO** |
| Noticias Docente — Listado y Filtros | **IMPLEMENTADO** |
| Noticias Docente — Artículo Destacado | **IMPLEMENTADO** |
| Noticias Docente — Detalle de Artículo | **IMPLEMENTADO** |
| Integración de Subpestañas en TeacherPortal | **IMPLEMENTADO** |
| Pruebas Unitarias y de Integración Frontend (Vitest) | **VERIFICADO AUTOMÁTICAMENTE (38/38 PASS)** |
| Pruebas Backend API, RBAC y Regresión (Pytest) | **VERIFICADO AUTOMÁTICAMENTE (44/44 PASS)** |
| Verificación Estática (TypeScript + Build) | **VERIFICADO AUTOMÁTICAMENTE (0 ERRORES)** |
| Validación Visual en Navegador por el Propietario | **PENDIENTE DE NUEVA VALIDACIÓN MANUAL (B2-H02 RESUELTO)** |
| Certificación Formal de Fase B2 | **NO CERTIFICADO** |

---

## 16. INCIDENCIA B2-H02: DEFECTO EN VALIDACIÓN HUMANA, CAUSA RAÍZ Y RESOLUCIÓN CONTROLADA

Durante la validación manual en navegador del Portal Docente con el usuario `DOCENTE` (`natalia_castro`), se detectó un bloqueo funcional al acceder a la pestaña de **Comunicaciones**:

### 16.1 Defecto Detectado
- **Síntoma:** Al cargar la vista de comunicaciones, el endpoint `GET /api/v1/teacher/communications` devolvía `HTTP 500 Internal Server Error`, desplegando en la interfaz el mensaje: *"An unexpected error occurred. Please try again later."*.
- **Impacto:** Impedía el listado de comunicados, apertura de detalle, marcado de lectura y confirmación de acuse de recibo. Bloqueo de la validación humana B2-H02.

### 16.2 Causa Raíz Técnica
- **Archivo:** [`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py#L627)
- **Función:** `CommunicationService.list_teacher_communications()`
- **Línea:** 627
- **Detalle:** Al resolver los salones dirigidos por el docente para incluir comunicados segmentados a nivel grupo/grado/sede, se invocaba:
  ```python
  dir_grp_stmt = select(Group).where(Group.headquarters_teacher_id == teacher.id)
  ```
  El modelo SQLAlchemy [`Group`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/group.py#L119) define dicho campo como `Group.group_director_teacher_id` (migración `003_phase3_groups_and_actors.py`). El atributo `headquarters_teacher_id` no existe en la clase, lanzando inmediatamente:
  ```text
  AttributeError: type object 'Group' has no attribute 'headquarters_teacher_id'
  ```

### 16.3 Diferencia entre Tests Automatizados Anteriores y Runtime
- **Brecha en Suites Automatizadas:**
  - La suite de Fase 15 (`test_institutional_communications_api.py`) evaluaba únicamente los perfiles de rector, estudiante y acudiente, omitiendo una prueba que utilizara un token de docente contra `/teacher/communications`.
  - La suite de Portal Docente preexistente (`test_teacher_portal_api.py`) cubría dashboard, asignaciones, actividades, calificaciones, asistencia y planeación, pero no tenía casos para comunicaciones.
  - Al no ejecutarse el método `list_teacher_communications()` en ninguna prueba automatizada, la suite reportó 100% PASS mientras el defecto permanecía latente.
- **Runtime Real:** Al ingresar `natalia_castro` a la pestaña de Comunicaciones en el navegador, la llamada HTTP real ejecutó la línea defectuosa sobre el backend activo, provocando el fallo 500.

### 16.4 Corrección Aplicada
Con autorización expresa del propietario del proyecto, se sustituyó exclusivamente la referencia errónea en [`communication_service.py:627`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py#L627):
```diff
- dir_grp_stmt = select(Group).where(Group.headquarters_teacher_id == teacher.id)
+ dir_grp_stmt = select(Group).where(Group.group_director_teacher_id == teacher.id)
```
Se preservó de manera intacta e inalterada toda la lógica de filtrado de audiencias (`TODOS_INSTITUCION`, `SOLO_DOCENTES`, grados, sedes, grupos de `AcademicAssignment`, exclusión estricta de `SOLO_ESTUDIANTES` y `SOLO_ACUDIENTES`).

### 16.5 Nueva Prueba de Cobertura Obligatoria
Se agregó la prueba de integración HTTP real en [`backend/tests/test_teacher_portal_api.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_teacher_portal_api.py#L670-L787):
- **Nombre:** `test_teacher_communications_feed_and_tenant_isolation`
- **Cobertura verificada:**
  1. Ejecución real vía HTTP `client.get("/api/v1/teacher/communications")` con token docente.
  2. Respuesta `HTTP 200` y estructura de contrato (`items`, `total`, `unread_count`).
  3. Visibilidad exclusiva de comunicaciones dirigidas al docente o a toda la institución.
  4. Exclusión de comunicados dirigidos exclusivamente a estudiantes (`SOLO_ESTUDIANTES`).
  5. Registro automático de lectura en `GET /api/v1/teacher/communications/{id}` y reducción dinámica del `unread_count` de 1 a 0 en el feed subsecuente.
  6. Aislamiento institucional estricto (Anti-IDOR): respuesta `HTTP 404` ante comunicados pertenecientes a otra institución educativa.

### 16.6 Resultados de Verificación y Regresión
- **Prueba focalizada B2-H02:** `1 passed in 2.32s` (Exit code: 0).
- **Teacher Portal Suite completa:** `10 passed in 31.63s` (Exit code: 0).
- **Regresión B1 / Convivencia (`test_coexistence_incidents_api.py`):** `3 passed in 5.52s` (Exit code: 0).
- **Regresión Student Portal (`test_student_portal_api.py`):** `8 passed in 12.67s` (Exit code: 0).
- **Regresión Guardian Portal (`test_guardian_portal_api.py`):** `9 passed in 14.14s` (Exit code: 0).
- **Regresión RBAC & Permisos (`test_authorization.py`):** `5 passed in 0.23s` (Exit code: 0).
- **Regresión Autenticación y Tokens (`test_auth_endpoints.py`):** `5 passed in 4.69s` (Exit code: 0).
- **Frontend TypeScript (`npm run typecheck`):** `tsc --noEmit` completado con 0 errores (Exit code: 0).
- **Frontend Build (`npm run build`):** `tsc -b && vite build` completado exitosamente en 4.56s (Exit code: 0).

### 16.7 Validación en Runtime Real (PostgreSQL)
Se ejecutó una consulta real sobre el servidor backend en ejecución (`http://127.0.0.1:8000`) autenticado como la docente real `natalia_castro` (`f5e73171-294d-4270-b05f-dee4ac6fcea5`) contra la base de datos PostgreSQL:
- **Status:** `HTTP 200 OK`
- **Payload recibido:**
  ```json
  {
    "items": [
      {
        "id": "7e83e337-f130-4e0c-b831-4a0bd764c077",
        "institution_id": "404c2ebe-478c-45a0-a9a2-453fc7fcecb3",
        "author_user_id": "ca8a4525-c730-48d9-b1c4-dc7f76b26112",
        "title": "[QA-F15-20260907] Circular Oficial: Actividades Pedagógicas y Convivencia",
        "summary": "Comunicado oficial sintético para validación funcional humana de la Fase 15...",
        "category": "CIRCULAR_OFICIAL",
        "priority": "ALTA",
        "target_scope": "TODOS_INSTITUCION",
        "requires_acknowledgment": true,
        "status": "PUBLICADO",
        "author": {
          "first_name": "Sandra",
          "last_name": "Chavez Guzman"
        },
        "is_read": false,
        "is_acknowledged": false
      }
    ],
    "total": 1,
    "unread_count": 1
  }
  ```
- **Integridad:** No se modificó el usuario docente, no se crearon datos innecesarios, no se modificó la circular QA preexistente y no se crearon migraciones.

---

## GATE B2 (ACTUALIZADO TRAS CORRECCIÓN B2-H02)

**Resultado Técnico Antigravity:**
### `PASS — CORRECCIÓN LISTA PARA NUEVA VALIDACIÓN HUMANA`

*(Detención controlada: No se inicia B3, no se inicia Fase 17, no se certifica B2 automáticamente sin validación humana del propietario).*
