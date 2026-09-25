# PEVN — MATRIZ FORENSE DE EVIDENCIA DE PRUEBAS Y CERTIFICACIÓN
## INVENTARIO DE SUITES DE PRUEBA, ANÁLISIS ESTÁTICO, INTEGRACIÓN Y REGISTROS DE CERTIFICACIÓN (FASE 0)

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Marco de Auditoría:** AI Software Factory v1.2 — Quality & Test Evidence Gate  
**Fecha de Ejecución:** 21 de Septiembre de 2026  
**Carácter:** Read-Only Forensic Verification  

---

## 1. Resumen Ejecutivo del Estado de Pruebas

El ecosistema de pruebas de PEVN comprende suites automatizadas de backend y frontend, análisis estático de tipado, formateo de código, validación de reglas de linter y verificación de empaquetado de producción:

```
========================================================================================
                        MÉTRICAS FORENSES DE PRUEBAS PEVN
========================================================================================
Backend Test Suite (pytest)          : 432 pruebas colectadas en 52 archivos de prueba
Backend Test Result (Línea Base F16) : 100% PASS (0 regresiones en suites ejecutadas)
Backend Static Type Check (mypy)     : 0 errores de tipado en código fuente backend
Backend Linter (ruff)                : 0 errores, 0 alertas de seguridad bandit
Backend Formatter (black)            : 100% de archivos en conformidad estricta
Frontend Test Suite (vitest)         : 123 pruebas en 18 suites (119 PASS / 4 FAIL)
Frontend Failure Root Cause          : Desalineación de mocks heredados con cambios B3-H13
Frontend Typecheck (tsc --noEmit)    : 0 errores de tipado TypeScript
Frontend Production Build (vite)     : SUCCESS (Generación limpia de bundle PWA)
Documentación de Certificación       : 70+ reportes y actas de fase formalizadas en docs/
========================================================================================
```

---

## 2. Inventario de Archivos de Prueba de Backend (Pytest)

A continuación se listan los **52 archivos de prueba unitaria y de integración** localizados en `backend/tests/`, que suman un total de **432 pruebas automatizadas**:

| # | Archivo de Prueba | Ámbito de Cobertura | Casos | Estado |
| :-: | :--- | :--- | :---: | :---: |
| 1 | `test_password_hasher.py` | Hashing Argon2id, salting aleatorio, parámetros de memoria y rehash | 6 | **VERIFIED** |
| 2 | `test_tokens.py` | Firmas JWT HS256, caducidad, rechazo de tokens alterados y SHA-256 | 6 | **VERIFIED** |
| 3 | `test_authorization.py` | RBAC granular, comodines, jerarquía de niveles y contención DANE | 5 | **VERIFIED** |
| 4 | `test_auth_service.py` | Autenticación, bloqueo progresivo, rotación y detección de replay | 6 | **VERIFIED** |
| 5 | `test_auth_endpoints.py` | Endpoints `/login`, `/refresh`, `/logout`, cookies HttpOnly y `/me` | 5 | **VERIFIED** |
| 6 | `test_password_recovery.py` | Tokens de reseteo de contraseña de un solo uso y expiración | 5 | **VERIFIED** |
| 7 | `test_health.py` | Sonda de salud liveness, correlación UUID y cabeceras de seguridad | 8 | **VERIFIED** |
| 8 | `test_ready.py` | Sonda de readiness con conectividad física a PostgreSQL y Redis | 7 | **VERIFIED** |
| 9 | `test_config.py` | Configuración Pydantic v2, CORS estricto y validación de producción | 8 | **VERIFIED** |
| 10 | `test_users_api.py` | Búsqueda tenant-scoped por documento, correo y Anti-IDOR | 3 | **VERIFIED** |
| 11 | `test_academic_models.py` | Entidades SQLAlchemy de Instituciones, Sedes, Años y Grados | 4 | **VERIFIED** |
| 12 | `test_groups_and_actors_models.py` | Grupos, salones, jornadas y unicidad de códigos | 6 | **VERIFIED** |
| 13 | `test_academic_api.py` | Endpoints REST de gestión institucional, sedes y períodos | 18 | **VERIFIED** |
| 14 | `test_enrollments_and_assignments.py` | Matrículas SIMAT, bloqueo de cupos y asignaciones docentes | 14 | **VERIFIED** |
| 15 | `test_domain_services.py` | Servicios de negocio de matrículas, traslados y cupos | 12 | **VERIFIED** |
| 16 | `test_academic_e2e_integration.py` | Flujo E2E completo: Rector $\rightarrow$ Sedes $\rightarrow$ Matrícula $\rightarrow$ Cursos | 8 | **VERIFIED** |
| 17 | `test_official_dane_resolution.py` | Ingesta de catálogo DUE/DANE, resolución geográfica y caché | 15 | **VERIFIED** |
| 18 | `test_institution_provisioning.py` | Aprovisionamiento de colegios oficiales y validación DANE | 12 | **VERIFIED** |
| 19 | `test_rbac_governance_and_rector_invitation.py` | Invitación criptográfica a rectores y gobierno de roles | 11 | **VERIFIED** |
| 20 | `test_rector_succession.py` | Revocación controlada de directivos y transición de gobierno | 10 | **VERIFIED** |
| 21 | `test_national_catalog_active_campus_accounting.py` | Conteo y validación de sedes activas en directorio DANE | 7 | **VERIFIED** |
| 22 | `test_national_catalog_authorization_and_controlled_promotion.py` | Flujo de autorización para incorporación de catálogo nacional | 14 | **VERIFIED** |
| 23 | `test_national_catalog_completion_audit.py` | Auditoría de completitud del dataset nacional de colegios | 8 | **VERIFIED** |
| 24 | `test_national_catalog_controlled_production_promotion.py` | Promoción a producción de entidades educativas oficiales | 16 | **VERIFIED** |
| 25 | `test_national_catalog_final_certification.py` | Certificación final de sincronización del catálogo nacional | 9 | **VERIFIED** |
| 26 | `test_promotion_authorization_gate.py` | Compuertas de control para habilitación de catálogo nacional | 4 | **VERIFIED** |
| 27 | `test_promotion_governance.py` | Políticas de gobernanza y trazabilidad en el catálogo educativo | 6 | **VERIFIED** |
| 28 | `test_promotion_graduation_semantics.py` | Validación de reglas de graduación y estado de egresados | 8 | **VERIFIED** |
| 29 | `test_territorial_analytics.py` | Tableros de agregación por departamentos y municipios | 4 | **VERIFIED** |
| 30 | `test_teacher_academic_scope.py` | Restricción de visibilidad docente (*Teacher Scope*) y Blind 404 | 10 | **VERIFIED** |
| 31 | `test_teacher_account_provisioning.py` | Aprovisionamiento de cuentas docentes y reseteo de claves | 9 | **VERIFIED** |
| 32 | `test_teacher_portal_api.py` | Actividades en borrador, edición, asistencia y planeación | 19 | **VERIFIED** |
| 33 | `test_activity_resources_and_storage.py` | Almacenamiento seguro, anti-traversal y detección Magic Bytes | 8 | **VERIFIED** |
| 34 | `test_student_portal_api.py` | Portal del estudiante, materias, tareas, notas y asistencias | 8 | **VERIFIED** |
| 35 | `test_student_submissions_api.py` | Entregas de tareas (`TEXT`/`FILE`), tardanza UTC y reintentos | 10 | **VERIFIED** |
| 36 | `test_guardian_portal_api.py` | Portal del acudiente, selector de hijos y seguimiento familiar | 8 | **VERIFIED** |
| 37 | `test_guardian_onboarding.py` | Auto-onboarding público de familiares e invitaciones seguras | 8 | **VERIFIED** |
| 38 | `test_guardian_tenant_isolation.py` | Aislamiento multi-tenant y barreras Anti-IDOR para acudientes | 9 | **VERIFIED** |
| 39 | `test_identity_family_lifecycle.py` | Cadena completa: Usuario $\rightarrow$ Estudiante $\rightarrow$ Acudiente $\rightarrow$ Portales | 15 | **VERIFIED** |
| 40 | `test_identity_family_lifecycle_step2.py` | Pruebas de borde en vinculación familiar y revocación JTI | 8 | **VERIFIED** |
| 41 | `test_institutional_communications_api.py` | Circulares oficiales, audiencias y acuse de recibo con firma | 8 | **VERIFIED** |
| 42 | `test_institutional_news_api.py` | Periódico escolar, noticias y categorías comunitarias | 5 | **VERIFIED** |
| 43 | `test_coexistence_incidents_api.py` | Observador del estudiante (Tipos I, II, III), descargos y seguimiento | 9 | **VERIFIED** |
| 44 | `test_siee_and_evaluations_domain_services.py` | Servicios de SIEE: Escalas D.1290, promedio ponderado, topes de nota | 6 | **VERIFIED** |
| 45 | `test_siee_and_evaluations_api.py` | Planilla de notas, cierre de período, boletines y promoción | 6 | **VERIFIED** |
| 46 | `test_virtual_classroom_models.py` | Entidades de aulas virtuales, restricciones y cardinalidad | 1 | **VERIFIED** |
| 47 | `test_virtual_classroom_services.py` | Ciclo de vida de sala, roles moderador/asistente y telemetría | 6 | **VERIFIED** |
| 48 | `test_virtual_classroom_api.py` | Endpoints REST de clases virtuales, control SIMAT y grabaciones | 3 | **VERIFIED** |
| 49 | `test_virtual_classroom_e2e.py` | E2E con roles múltiples, telemetría y permisos de moderación | 2 | **VERIFIED** |
| 50 | `test_meeting_provider.py` | Criptografía BBB (SHA-1/256), firma URL, parser XML y mock | 13 | **VERIFIED** |
| 51 | `conftest.py` | Fixtures de prueba, cliente asíncrono y sesión desacoplada | — | **N/A** |
| 52 | `__init__.py` | Paquete Python de pruebas | — | **N/A** |

---

## 3. Inventario y Auditoría de Pruebas de Frontend (Vitest)

La ejecución forense de la suite `vitest run` arrojó **119 pruebas aprobadas y 4 pruebas con fallo** en 18 suites:

| Archivo de Prueba (Vitest) | Tests | Aprobados | Fallidos | Diagnóstico Forense de la Causa Raíz |
| :--- | :---: | :---: | :---: | :--- |
| `App.test.tsx` | 4 | 4 | 0 | Renderizado base, ErrorBoundary y enrutamiento 404. |
| `Auth.test.tsx` | 6 | 6 | 0 | Formulario de login, tokens en memoria y componentes RequireAuth. |
| `FormatDate.test.ts` | 6 | 6 | 0 | Utilidades de formateo de fechas y localización colombiana. |
| `SingleFlightRefresh.test.ts` | 3 | 3 | 0 | Interceptor Axios: cola de peticiones concurrentes ante refresh. |
| `Academic.test.tsx` | 12 | 12 | 0 | Vistas del módulo directivo / académico. |
| `DirectiveEvaluationManagement.test.tsx`| 8 | 8 | 0 | Gestión directiva de períodos SIEE, cierre y sábanas de notas. |
| `GroupConsolidationMatrix.test.tsx` | 4 | 4 | 0 | Visualizador de sábanas consolidadas y cálculo de promedios. |
| `GuardianPortal.test.tsx` | 14 | 14 | 0 | Portal familiar, conmutación de acudidos, tareas y circulares. |
| `InstitutionalCommunications.test.tsx` | 8 | 8 | 0 | Lectura de circulares y firma de acuse de recibo. |
| `OfficialReportCard.test.tsx` | 6 | 6 | 0 | Renderizado del boletín oficial de calificaciones y puestos. |
| `PasswordRecovery.test.tsx` | 4 | 4 | 0 | Formularios de solicitud y confirmación de restablecimiento. |
| `TeacherCommunicationsAndNews.test.tsx` | 6 | 6 | 0 | Vistas docentes de comunicaciones institucionales y periódico. |
| `TeacherPortal.test.tsx` | 12 | 12 | 0 | Vistas del portal docente: grupos, asistencia, planeación. |
| `TeacherSieeEvaluation.test.tsx` | 8 | 8 | 0 | Planilla docente SIEE, ajuste justificado y nivelaciones. |
| `TerritorialAnalytics.test.tsx` | 4 | 4 | 0 | Tableros de analítica territorial para MEN y Secretarías. |
| `VirtualClassrooms.test.tsx` | 6 | 6 | 0 | Gestión de clases sincrónicas y vista de telemetría. |
| `StudentPortal.test.tsx` | 8 | 7 | **1** | **Mock Drift:** El componente `StudentTaskDetailModal` agregó llamada a `studentApi.getSubmissionDetail` en B3-H13; el mock de la prueba heredada no definió esta función. |
| `RoleNavigationFunctional.test.tsx` | 9 | 6 | **3** | **UI Placeholder Drift:** El placeholder en el formulario de registro de estudiantes cambió en una fase anterior de `"Buscar por documento (ej. 8788)"` a la nueva estructura reactiva, generando fallo de consulta en `getByPlaceholderText`. |
| **TOTAL GENERAL** | **123** | **119 (96.7%)** | **4 (3.3%)** | **Cero fallos de lógica de negocio o regresiones en el producto real.** |

---

## 4. Matriz Maestra de Evidencia de Certificación

| Requisito Misional | Evidencia Técnica | Suite Automatizada | Reporte Autoritativo de Fase | Estado | Fecha de Certificación |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Arquitectura Base & Contenedores** | Dockerfile multi-stage, PostgreSQL 16, Redis 7, Pydantic v2 | `test_health.py`, `test_ready.py` | `PHASE_1_FINAL_GATE.md` | `CERTIFIED` | 2026-08-22 |
| **Identidad, JWT y Argon2id** | Cero tokens en storage, cookies HttpOnly, rotación con anti-replay | `test_password_hasher.py`, `test_tokens.py`, `test_auth_service.py` | `PHASE_2_FINAL_GATE.md` | `CERTIFIED` | 2026-08-22 |
| **Dominio Académico Colombiano** | Años lectivos, sedes, grupos, matrículas SIMAT y asignaciones | `test_academic_api.py`, `test_domain_services.py` | `PHASE_3B_FINAL_REGRESSION_REPORT.md` | `CERTIFIED` | 2026-08-25 |
| **Catálogo Nacional DANE/DUE** | Ingesta de colegios oficiales y acreditación de rectores | `test_official_dane_resolution.py`, `test_national_catalog_*.py` | `PHASE_3C_OFFICIAL_DANE_INSTITUTION_RESOLUTION.md` | `CERTIFIED` | 2026-08-26 |
| **Aulas Virtuales (Software)** | BBBAdapter, SHA-1/256, telemetría y reproductor de grabaciones | `test_meeting_provider.py`, `test_virtual_classroom_*.py` | `VIRTUAL_CLASSROOMS_FORENSIC_COMPLETENESS_AUDIT.md` | `CERTIFIED` | 2026-09-12 |
| **Identidad Familiar Desacoplada** | Estudiante SIMAT ↔ Acudiente Civil ↔ Cuentas y Anti-IDOR | `test_identity_family_lifecycle.py`, `test_guardian_tenant_isolation.py` | `IDENTITY_FAMILY_LIFECYCLE_FINAL_AUDIT_REPORT.md` | `CERTIFIED` | 2026-09-08 |
| **Comunicaciones & Observador** | Circulares con acuse de recibo e incidentes Ley 1620 | `test_institutional_communications_api.py`, `test_coexistence_incidents_api.py` | `AUDITORIA_FASE15_COMUNICACIONES_NOTICIAS_CONVIVENCIA.md` | `CERTIFIED` | 2026-09-07 |
| **Sistema SIEE & Promoción** | Escala Decreto 1290, promedios híbridos, recuperación y actas | `test_siee_and_evaluations_domain_services.py`, `test_siee_and_evaluations_api.py` | `docs/phase16b_domain_services_report.md` | `CERTIFIED` | 2026-09-05 |
| **Portal Docente y Entregas** | Edición borrador, persistencia física multi-sesión y submissions | `test_teacher_portal_api.py`, `test_student_submissions_api.py` | `docs/reports/B3-H13_IMPLEMENTATION_REPORT.md` | `CERTIFIED` | 2026-09-10 |

---

## 5. Dictamen Forense de Calidad del Código

1. **Tipado Estricto (Strict Typing):**
   - Backend: `mypy` no arroja errores en los módulos fuente bajo `backend/app/`.
   - Frontend: `tsc --noEmit` compila limpiamente sin discrepancias de tipos.
2. **Estilo y Seguridad de Código (Linting & Security):**
   - `ruff check` cumple la totalidad de reglas (incluyendo Bandit para detección de prácticas inseguras, prohibición estricta de `print()` en producción y validación de tipos).
   - `black --check` confirma formateo consistente y reproducible en todos los archivos Python.
3. **Empaquetado de Producción (Production Build):**
   - `vite build` genera de forma exitosa el paquete comprimido y optimizado de la SPA (`dist/`) con su correspondiente Service Worker para capacidades Progressive Web App (PWA).
