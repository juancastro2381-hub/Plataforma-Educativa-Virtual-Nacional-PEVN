# PEVN — INFORME DE PREPARACIÓN DE DATOS QA PARA VALIDACIÓN FUNCIONAL HUMANA
## FASE 15: COMUNICADOS INSTITUCIONALES, NOTICIAS Y OBSERVADOR DE CONVIVENCIA ESCOLAR
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha de Preparación:** 2026-09-07  
**Marcador Único QA:** `QA-F15-20260907`  
**Estado de la Ejecución:** `PASS`  
**Estado Final del Gate:** `READY_FOR_MANUAL_FUNCTIONAL_VALIDATION`

---

## 1. ESTADO DE LA EJECUCIÓN
**PASS**

La preparación de datos sintéticos controlados y reversibles se completó con éxito. Los tres módulos de la Fase 15 disponen de registros sembrados, validados en PostgreSQL y verificados a través de la API REST en tiempo de ejecución.

---

## 2. MECANISMO UTILIZADO PARA CREAR LOS DATOS
Se implementó un script de desarrollo/QA local y controlado:
* **Ruta del Script:** `backend/scratch/qa_seed_phase15.py`
* **Características:**
  1. **Resolución dinámica:** No utiliza UUIDs fijos (*hardcoded*). Localiza mediante SQLAlchemy la institución, el estudiante, el acudiente y el autor directivo.
  2. **Idempotencia nativa:** Consulta previamente la existencia de registros con el marcador `QA-F15-20260907` antes de realizar inserciones.
  3. **Reversibilidad estricta:** Cuenta con un comando `--action cleanup` que elimina exclusivamente los registros vinculados al marcador `QA-F15-20260907`.
  4. **Alineación con el ORM:** Utiliza los modelos SQLAlchemy existentes sin alterar contratos ni dependencias de producción.

---

## 3. IDENTIFICADOR / MARCADOR QA UTILIZADO
* **Marcador Único:** `QA-F15-20260907`
* **Aplicación:** Incluido como prefijo formal en títulos de comunicados, noticias, descripciones de incidentes y notas de seguimiento pedagógico.

---

## 4. INSTITUCIÓN ENCONTRADA (RESOLUCIÓN DINÁMICA)
* **Nombre de la Institución:** `COLEGIO GLENN DOMAN`
* **UUID de la Institución:** `404c2ebe-478c-45a0-a9a2-453fc7fcecb3`

---

## 5. ESTUDIANTE UTILIZADO
* **Nombre:** `Ramiro Rey`
* **UUID Estudiante (`students.id`):** `09e7beab-090a-46b8-9f51-91cb402c103a`
* **UUID Usuario (`users.id`):** `91060389-9ed3-4fb1-b543-a67b84044040`
* **Email:** `ramiro.rey@colegio.edu.co`
* **Matrícula Activa:** Grupo ID `e131b6a3-3990-44e8-be23-a36b913e26c3`

---

## 6. ACUDIENTE UTILIZADO
* **Nombre:** `Alberto Mercado`
* **UUID Acudiente (`guardians.id`):** `f0a3f0dd-8750-4aea-8109-65fac72933fc`
* **UUID Usuario (`users.id`):** `4e10369e-0d3e-4e3d-bc80-b7b73a736a66`
* **Email:** `alberto@example.com`
* **Vínculo Legal con Ramiro Rey:** `StudentGuardian` activo con parentesco `PADRE`

---

## 7. COMUNICADO INSTITUCIONAL CREADO
* **ID:** `7e83e337-f130-4e0c-b831-4a0bd764c077`
* **Título:** `[QA-F15-20260907] Circular Oficial: Actividades Pedagógicas y Convivencia`
* **Resumen:** Comunicado oficial sintético para validación funcional humana de la Fase 15 (Portal Estudiante y Acudiente).
* **Categoría:** `CIRCULAR_OFICIAL`
* **Prioridad:** `ALTA`
* **Audiencia / Ámbito:** `TODOS_INSTITUCION` (alcanza simultáneamente a estudiantes y acudientes)
* **Requiere Acuse de Recibo:** `True`
* **Estado:** `PUBLICADO`
* **Fecha de Publicación:** `2026-09-07T17:29:26Z`
* **Autor:** `Sandra Chavez Guzman` (`rectoria@glenndoman.edu.co`)

---

## 8. NOTICIA INSTITUCIONAL CREADA
* **ID:** `d2d33449-fb86-4f20-bf2e-3f392beda905`
* **Título:** `[QA-F15-20260907] Logro Destacado en Feria de Ciencia e Innovación Escolar`
* **Resumen:** Nuestra institución obtuvo reconocimiento de excelencia en el encuentro regional de proyectos formativos.
* **Categoría:** `LOGRO_ACADEMICO` (reconocida plenamente por backend y frontend)
* **Estado:** `PUBLICADO`
* **Fecha de Publicación:** `2026-09-07T17:29:26Z`
* **Autor:** `Sandra Chavez Guzman` (`rectoria@glenndoman.edu.co`)

---

## 9. REGISTRO DE CONVIVENCIA CREADO (OBSERVADOR DEL ESTUDIANTE)
* **ID:** `8daf3c23-dae8-4eb7-8b7b-72845847b425`
* **Estudiante Asociado:** Ramiro Rey (`09e7beab-090a-46b8-9f51-91cb402c103a`)
* **Reportador:** `Sandra Chavez Guzman` (Directivo / Rectoría)
* **Tipo de Situación:** `TIPO_I` (Ley 1620 de 2013)
* **Estado:** `EN_SEGUIMIENTO`
* **Visibilidad Estudiante (`is_visible_to_student`):** `True`
* **Visibilidad Acudiente (`is_visible_to_guardian`):** `True`
* **Ubicación:** `Aula de Clases / Auditorio Principal`
* **Descripción:** `[QA-F15-20260907] Registro sintético formativo de convivencia escolar. Diálogo pedagógico preventivo sobre puntualidad y participación activa en actividades institucionales.`
* **Descargo del Estudiante:** `El estudiante manifiesta su compromiso con el cumplimiento de los acuerdos de convivencia y puntualidad escolar.`
* **Medidas Pedagógicas:** `Acompañamiento reflexivo pedagógico, orientación tutorial y acuerdo de seguimiento de convivencia.`
* **Compromisos:** `Mantener puntualidad y participación constructiva en la jornada escolar.`
* **Seguimiento Pedagógico Vinculado:**
  * **ID Seguimiento:** `e77469fa-03a4-456f-9f6c-11dbd526e93e`
  * **Fecha:** `2026-09-07T17:30:38Z`
  * **Notas:** `[QA-F15-20260907] Sesión de seguimiento formativo: El estudiante y su acudiente demostraron receptividad positiva frente a los acuerdos acordados.`

---

## 10. RESULTADO DE LAS VERIFICACIONES DIRECTAS EN POSTGRESQL
Se ejecutó la introspección relacional en PostgreSQL 16.4 (`pevn-db`, puerto 5433):
1. **Comunicaciones:** `institutional_communications` contiene 1 registro con `institution_id = 404c2ebe-478c-45a0-a9a2-453fc7fcecb3` y título con `QA-F15-20260907`.
2. **Noticias:** `institutional_news` contiene 1 registro con categoría `LOGRO_ACADEMICO`, estado `PUBLICADO` y título con `QA-F15-20260907`.
3. **Incidentes:** `student_incidents` contiene 1 registro con `student_id = 09e7beab-090a-46b8-9f51-91cb402c103a`, `is_visible_to_student = True`, `is_visible_to_guardian = True`.
4. **Seguimientos:** `incident_follow_ups` contiene 1 registro vinculado al incidente anterior.

---

## 11. RESULTADO DE LOS ENDPOINTS HTTP EN RUNTIME (`http://localhost:8000`)
Se emitieron peticiones HTTP autenticadas utilizando tokens JWT generados en vivo:

### Portal del Estudiante (Ramiro Rey)
* `GET /api/v1/student/communications`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "7e83e337-f130-4e0c-b831-4a0bd764c077", "title": "[QA-F15-20260907]...", "author_name": "Sandra Chavez Guzman", "requires_acknowledgment": true}], "total": 1, "unread_count": 1}`
* `GET /api/v1/student/news`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "d2d33449-fb86-4f20-bf2e-3f392beda905", "title": "[QA-F15-20260907]...", "category": "LOGRO_ACADEMICO", "author_name": "Sandra Chavez Guzman"}], "total": 1}`
* `GET /api/v1/student/incidents`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "8daf3c23-dae8-4eb7-8b7b-72845847b425", "situation_type": "TIPO_I", "status": "EN_SEGUIMIENTO", "reporter_name": "Sandra Chavez Guzman", "follow_ups": [{"id": "e77469fa-03a4-456f-9f6c-11dbd526e93e", ...}]}], "total": 1}`

### Portal del Acudiente (Alberto Mercado)
* `GET /api/v1/guardian/communications`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "7e83e337-f130-4e0c-b831-4a0bd764c077", "title": "[QA-F15-20260907]..."}], "total": 1, "unread_count": 1}`
* `GET /api/v1/guardian/news`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "d2d33449-fb86-4f20-bf2e-3f392beda905", "title": "[QA-F15-20260907]..."}], "total": 1}`
* `GET /api/v1/guardian/students/09e7beab-090a-46b8-9f51-91cb402c103a/incidents`  
  $\longrightarrow$ **HTTP 200 OK**  
  `{"items": [{"id": "8daf3c23-dae8-4eb7-8b7b-72845847b425", "situation_type": "TIPO_I", "status": "EN_SEGUIMIENTO", "reporter_name": "Sandra Chavez Guzman", "follow_ups": [{"id": "e77469fa-03a4-456f-9f6c-11dbd526e93e", ...}]}], "total": 1}`

---

## 12. CONFIRMACIÓN DE IDEMPOTENCIA
El script `qa_seed_phase15.py` fue ejecutado en múltiples ocasiones consecutivas:
```text
[QA SEED] Comunicado ya existente (Idempotente): ID 7e83e337-f130-4e0c-b831-4a0bd764c077
[QA SEED] Noticia ya existente (Idempotente): ID d2d33449-fb86-4f20-bf2e-3f392beda905
[QA SEED] Incidente ya existente (Idempotente): ID 8daf3c23-dae8-4eb7-8b7b-72845847b425
```
**Resultado:** Se confirma cero duplicación de registros en ejecuciones repetidas.

---

## 13. CONFIRMACIÓN DE NO ALTERACIÓN DE DATOS PREEXISTENTES
Se inspeccionaron los conteos globales de entidades previas y posteriores al seed:
* Total de Usuarios en la base de datos: `188` (sin alteraciones).
* Total de Estudiantes: `16` (sin alteraciones).
* Total de Acudientes: `11` (sin alteraciones).
* Los registros de Ramiro Rey, Alberto Mercado, Samuel Rua y demás usuarios permanecen estrictamente intactos.

---

## 14. CONFIRMACIÓN DE GOBERNANZA DE MIGRACIONES
* **Nuevas migraciones creadas:** **0**
* Se respetó la regla estricta de no agregar nuevas versiones de Alembic.
* La migración de la Fase 15 (`021_phase15_communications_news_incidents.py`) se mantiene como la versión `head` activa.

---

## 15. CONFIRMACIÓN DE NO MODIFICACIÓN DE CÓDIGO PRODUCTIVO
* Ningún archivo productivo (`backend/app/*`, `frontend/src/*`) fue modificado en esta tarea.
* Todo el mecanismo de preparación y control de datos reside en el entorno local de pruebas (`backend/scratch/qa_seed_phase15.py`).

---

## 16. LISTA EXACTA DE ARCHIVOS MODIFICADOS O CREADOS EN ESTA TAREA
1. `backend/scratch/qa_seed_phase15.py` **[NUEVO - Script de Seed/Cleanup QA local]**
2. `backend/migrations/versions/021_phase15_communications_news_incidents.py` **[AJUSTE AUDIT COLUMNS - creado en sesión previa]**
3. `docs/reports/PHASE_15_QA_DATA_PREPARATION_REPORT.md` **[NUEVO - Copia del presente informe]**

---

## 17. PROCEDIMIENTO EXACTO PARA ELIMINACIÓN POSTERIOR (REVERSIBILIDAD)
> [!IMPORTANT]
> **NO EJECUTAR TODAVÍA:** Los datos deben permanecer disponibles en la base de datos para la validación funcional humana por parte del propietario del producto en el navegador.

Cuando el usuario complete las pruebas manuales y ordene la limpieza, se debe ejecutar:
```bash
python backend/scratch/qa_seed_phase15.py --action cleanup
```
### Acciones ejecutadas por el comando de limpieza:
1. Elimina de `incident_follow_ups` los registros asociados al marcador `QA-F15-20260907`.
2. Elimina de `student_incidents` el registro que contiene `QA-F15-20260907`.
3. Elimina de `communication_receipts` y `communication_audiences` los registros asociados al comunicado QA.
4. Elimina de `institutional_communications` el comunicado con título `QA-F15-20260907`.
5. Elimina de `institutional_news` la noticia con título `QA-F15-20260907`.

---

## 18. RIESGOS U OBSERVACIONES
* **Aislamiento Asegurado:** Los datos creados corresponden a una sola institución (`COLEGIO GLENN DOMAN`) y están aislados por multi-tenant.
* **Seguridad Visual:** Los registros están claramente identificados con la etiqueta `[QA-F15-20260907]`, eliminando cualquier riesgo de confusión con datos pedagógicos reales.

---

## 19. ESTADO FINAL DEL GATE

$$\mathbf{READY\_FOR\_MANUAL\_FUNCTIONAL\_VALIDATION}$$

Los datos QA están listos, comprobados y disponibles en la base de datos en tiempo de ejecución. El propietario funcional del producto puede proceder a ingresar al navegador web y validar manualmente los tres módulos en el Portal del Estudiante y en el Portal del Acudiente.
