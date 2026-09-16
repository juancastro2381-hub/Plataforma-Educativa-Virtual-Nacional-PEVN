# INFORME DE CORRECCIÓN CONTROLADA — BLOQUEO B2-H02
## PORTAL DOCENTE: RESOLUCIÓN DE ERROR HTTP 500 EN COMUNICACIONES INSTITUCIONALES

- **Fecha:** 9 de Septiembre de 2026
- **Módulo:** Portal Docente (`TeacherPortal`) / Submódulo Comunicaciones
- **Fase:** B2
- **ID de Incidencia:** B2-H02
- **Autor:** Antigravity (Advanced Agentic Coding)
- **Estado Técnico:** **PASS — LISTO PARA NUEVA VALIDACIÓN HUMANA**
- **Estado de Certificación:** **NO CERTIFICADO** (Requiere re-validación manual por el Propietario del Proyecto)

---

## 1. RESUMEN EJECUTIVO

Durante la validación manual funcional del Portal Docente con el usuario `DOCENTE` (`natalia_castro`) en el entorno de desarrollo con PostgreSQL activo, la navegación a la subpestaña de **Comunicaciones** (`/teacher?tab=communications`) devolvía un error fatal:
- **HTTP 500 Internal Server Error** en la petición `GET /api/v1/teacher/communications`.
- **Mensaje en UI:** *"An unexpected error occurred. Please try again later."*.
- **Impacto:** Bloqueo total de la validación B2-H02 (imposibilidad de listar, abrir detalle, registrar lectura y confirmar acuse de recibo de comunicados oficiales).

Tras autorización expresa del propietario del proyecto, se diagnosticó la causa raíz, se aplicó la corrección puntual y estrictamente contenida dentro de B2, se incorporó una prueba de integración HTTP real que selló la brecha de cobertura, se ejecutaron regresiones completas de todos los módulos certificados y se validó el correcto funcionamiento en el entorno PostgreSQL real con respuesta `HTTP 200 OK`.

---

## 2. DIAGNÓSTICO FORENSE Y CAUSA RAÍZ

### 2.1 Reproducción y Excepción Exacta
- **Punto de fallo:** [`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py#L627)
- **Función:** `CommunicationService.list_teacher_communications()`
- **Línea:** 627
- **Traceback capturado:**
  ```text
  File "backend/app/api/v1/endpoints/teacher_portal.py", line 760, in list_teacher_communications
      tuples = await comm_service.list_teacher_communications(teacher=teacher, user=current_user)
  File "backend/app/services/communication_service.py", line 627, in list_teacher_communications
      dir_grp_stmt = select(Group).where(Group.headquarters_teacher_id == teacher.id)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  AttributeError: type object 'Group' has no attribute 'headquarters_teacher_id'
  ```

### 2.2 Causa Raíz
Al resolver los salones dirigidos por el docente para incluir circulares segmentadas a nivel de grupo, grado o sede, la consulta construía un filtro sobre el atributo inexistente `Group.headquarters_teacher_id`. 
En el modelo canónico [`Group`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/group.py#L119) (creado en la migración `003_phase3_groups_and_actors.py` y referenciado en `academic_scope_helper.py:98`), la clave foránea para el docente director de grupo se denomina:
```python
Group.group_director_teacher_id
```
La invocación de un atributo inexistente provocaba un `AttributeError` no capturado en la capa de servicio que se traducía en `HTTP 500`.

### 2.3 Explicación de la Diferencia entre Tests Anteriores y Runtime Real
- **Brecha en Suites Automatizadas:**
  - La suite de Fase 15 ([`test_institutional_communications_api.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_institutional_communications_api.py)) probaba exhaustivamente las bandejas de rector (`/communications`), estudiante (`/student/communications`) y acudiente (`/guardian/communications`), pero no tenía casos con token de docente para `/teacher/communications`.
  - La suite de Teacher Portal ([`test_teacher_portal_api.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_teacher_portal_api.py)) cubría asignaciones, salones, actividades, calificaciones, asistencia y planeación, pero no tenía casos para comunicaciones.
  - Al no ejecutarse el método `list_teacher_communications()`, los tests automáticos reportaban PASS (100%) a pesar del error latente.
- **Runtime Real:** Al ingresar `natalia_castro` a la pestaña correspondiente en el navegador, la petición real ejecutó la línea defectuosa sobre el backend y PostgreSQL activo, produciendo el 500.

---

## 3. CORRECCIÓN APLICADA

En [`backend/app/services/communication_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/communication_service.py#L627):

```diff
- dir_grp_stmt = select(Group).where(Group.headquarters_teacher_id == teacher.id)
+ dir_grp_stmt = select(Group).where(Group.group_director_teacher_id == teacher.id)
```

### Garantía de Integridad de Reglas de Negocio B2
- Se preservó estrictamente la segmentación de audiencias autorizada:
  - `TODOS_INSTITUCION` (visible para docentes).
  - `SOLO_DOCENTES` (visible para docentes).
  - Sedes, grados y grupos activos derivados de `AcademicAssignment`.
  - Salones dirigidos vía `group_director_teacher_id`.
  - Exclusión estricta de `SOLO_ESTUDIANTES` y `SOLO_ACUDIENTES`.
- **Cero cambios de base de datos o migraciones:** El campo `group_director_teacher_id` ya existía en la base de datos desde la Fase 3.
- **Cero ampliación de permisos:** El rol `DOCENTE` mantiene únicamente `communications:read` y `news:read`.

---

## 4. NUEVA PRUEBA DE INTEGRACIÓN HTTP REAL

Para cerrar definitivamente la brecha de cobertura, se implementó en [`backend/tests/test_teacher_portal_api.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_teacher_portal_api.py#L670-L787) el test:

```python
test_teacher_communications_feed_and_tenant_isolation
```

### Aspectos Validados por la Prueba:
1. **Ejecución HTTP Real:** Petición `GET /api/v1/teacher/communications` con cliente HTTP asíncrono y token con rol `teacher`.
2. **Respuesta y Estructura:** Código `HTTP 200 OK`, con contrato válido conteniendo `items`, `total`, `unread_count`.
3. **Filtrado de Audiencia:** Visibilidad de la circular dirigida a docentes (`SOLO_DOCENTES`) y exclusión de la circular para estudiantes (`SOLO_ESTUDIANTES`).
4. **Ciclo de Lectura Dinámico:** Consulta del detalle en `GET /api/v1/teacher/communications/{id}` registrando lectura automática (`is_read = True`) y actualización inmediata del feed reduciendo `unread_count` de 1 a 0.
5. **Aislamiento Multi-Tenant Estricto (Anti-IDOR):** Retorno de `HTTP 404 Not Found` al intentar consultar un comunicado de otra institución educativa.

---

## 5. RESULTADOS EXACTOS DE VALIDACIÓN Y REGRESIÓN

| Suite / Verificación | Comando Ejecutado | Resultado | Tiempo / Código |
|---|---|---|---|
| **Prueba Focalizada B2-H02** | `pytest tests/test_teacher_portal_api.py -k test_teacher_communications_feed_and_tenant_isolation -p no:cov -s` | **1 PASSED** | 2.32s (Exit: 0) |
| **Teacher Portal Completo (Fase 13D/B2)** | `pytest tests/test_teacher_portal_api.py -p no:cov -s` | **10 PASSED** | 31.63s (Exit: 0) |
| **B1 / Convivencia** | `pytest tests/test_coexistence_incidents_api.py -p no:cov -s` | **3 PASSED** | 5.52s (Exit: 0) |
| **Student Portal** | `pytest tests/test_student_portal_api.py -p no:cov -s` | **8 PASSED** | 12.67s (Exit: 0) |
| **Guardian Portal** | `pytest tests/test_guardian_portal_api.py -p no:cov -s` | **9 PASSED** | 14.14s (Exit: 0) |
| **RBAC / Autorización** | `pytest tests/test_authorization.py -p no:cov -s` | **5 PASSED** | 0.23s (Exit: 0) |
| **Autenticación / Sesión** | `pytest tests/test_auth_endpoints.py -p no:cov -s` | **5 PASSED** | 4.69s (Exit: 0) |
| **Frontend TypeScript** | `npm run typecheck` (`tsc --noEmit`) | **0 ERRORES** | Exit: 0 |
| **Frontend Production Build** | `npm run build` (`tsc -b && vite build`) | **194 módulos transformados** | 4.56s (Exit: 0) |

*Nota sobre runtime Windows / Python 3.14.2:* Se utilizó el parámetro `-p no:cov -s` con terminación controlada para evitar el bloqueo del intérprete de Python 3.14 al descargar hilos en Windows.

---

## 6. VALIDACIÓN EN RUNTIME REAL CON POSTGRESQL

Se ejecutó la consulta en vivo contra el backend en ejecución (`http://127.0.0.1:8000`) autenticado con el usuario docente real de la prueba manual:
- **Usuario:** `natalia_castro`
- **ID de Usuario:** `f5e73171-294d-4270-b05f-dee4ac6fcea5`
- **Institución:** `404c2ebe-478c-45a0-a9a2-453fc7fcecb3` (Colegio Glenn Doman)
- **Petición:** `GET /api/v1/teacher/communications`

### Respuesta Obtenida del Servidor en Vivo:
- **Status Code:** `200 OK`
- **Payload:**
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

---

## 7. DOCUMENTOS ACTUALIZADOS Y GOBERNANZA

1. [`docs/reports/TEACHER_PORTAL_B2_IMPLEMENTATION_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/TEACHER_PORTAL_B2_IMPLEMENTATION_REPORT.md): Actualizado con la Sección 16 documentando la incidencia B2-H02 completa sin ocultar el defecto hallado.
2. [`docs/reports/B2_H02_CONTROLLED_FIX_REPORT.md`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/B2_H02_CONTROLLED_FIX_REPORT.md): Documento formal específico de la corrección y pruebas de la incidencia.

### Reglas de Gobernanza Respetadas:
- NO se aplicaron migraciones.
- NO se ejecutaron comandos de `git reset`, `restore`, `clean`, `stash`, `commit` o `push`.
- NO se modificaron módulos fuera de B2 (Student Portal, Guardian Portal, B1, SIEE intactos).
- NO se certificó B2 automáticamente.
- NO se inició Fase B3 ni Fase 17.

---

## 8. CONCLUSIÓN Y ESTADO FINAL DE B2

### `PASS — CORRECCIÓN LISTA PARA NUEVA VALIDACIÓN HUMANA`

El bloqueo funcional B2-H02 ha sido superado técnica y operativamente. El endpoint responde `HTTP 200` y la interfaz del Portal Docente en `http://localhost:3000/teacher?tab=communications` está habilitada para que el usuario proceda con la validación manual de listado, detalle, lectura y acuse de recibo.
