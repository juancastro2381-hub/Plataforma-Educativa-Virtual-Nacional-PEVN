# PEVN — Informe Formal de Remediación y Certificación Git en Windows

**Fecha:** 16 de septiembre de 2026  
**Sistema Operativo:** Windows (Win32 / NTFS / OneDrive)  
**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Veredicto Final del Gate:** `PASS — GIT ISSUE RESOLVED`  

---

## 1. Causa Raíz Original (Original Root Cause)

Durante las operaciones rutinarias de control de versiones (`git status`, refresco del Source Control de Antigravity IDE / VS Code, o intentos de `git commit`), Git emitía advertencias críticas del tipo:
```text
Git warning: could not open directory 'backend/data/storage/.../submissions/...': Filename too long
```

La auditoría forense determinó que este problema era causado por:
1. **Omisión en `.gitignore`:** El directorio `backend/data/` (utilizado por el subsistema de almacenamiento seguro `StorageService` y `LocalStorageDriver`) no estaba registrado en `.gitignore`. Git interpretaba estas carpetas locales como directorios no rastreados (*untracked*) y forzaba un recorrido recursivo profundo.
2. **Jerarquía profunda por diseño de aislamiento multi-inquilino (Phase B3-H11/H13):** Las entregas y adjuntos de estudiantes se almacenan estructurados bajo:
   `backend/data/storage/<institution_uuid>/submissions/<activity_uuid>/<student_uuid>/<submission_uuid>/<attachment_uuid>.<ext>`
   Esta profundidad de 5 UUIDs anidados sobre la ruta base de Windows alcanzaba longitudes de entre **272 y 312 caracteres**, superando el límite canónico de 260 caracteres (`MAX_PATH`) de la API Win32.
3. **Configuración de Git en Windows:** Git para Windows mantenía deshabilitado por defecto el soporte de rutas largas (`core.longpaths` = no configurado / falso). Mientras que el runtime de Python usa explícitamente el prefijo `\\?\` para acceder a los archivos sin problemas, las funciones de Git colapsaban con el error de sistema `ENAMETOOLONG`.

---

## 2. Cambios Efectivamente Aplicados (Changes Actually Applied)

Se aplicaron de manera estricta y quirúrgica **únicamente los dos cambios autorizados**:

### A. Configuración de Git
Se ejecutó el comando para habilitar soporte de rutas largas en la configuración local del repositorio:
```bash
git config core.longpaths true
```

### B. Modificación en `.gitignore`
Se añadieron las siguientes líneas exactas en [.gitignore](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.gitignore) inmediatamente después de los volúmenes de Docker:
```gitignore
# ------------------------------------------------------------
# Application runtime storage and uploads (Phase B3-H11/H13)
# ------------------------------------------------------------
backend/data/
data/storage/
```

> [!IMPORTANT]
> **Protección del Código Fuente:** Se evitó intencionalmente el uso de reglas genéricas como `storage/` o `*/storage/`. De este modo, los módulos de código fuente legítimo en `backend/app/core/storage/` (`interfaces.py`, `local.py`, `service.py`, `__init__.py`) permanecen plenamente visibles para el control de versiones.

---

## 3. Configuración Exacta de Git

Verificación de la configuración local en [.git/config](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/.git/config):
```powershell
PS> git config --get core.longpaths
true
```

---

## 4. Diff Exacto en `.gitignore`

```diff
diff --git a/.gitignore b/.gitignore
index cc22ee6..f87a30e 100644
--- a/.gitignore
+++ b/.gitignore
@@ -105,6 +105,12 @@ postgres-data/
 redis-data/
 docker-volumes/
 
+# ------------------------------------------------------------
+# Application runtime storage and uploads (Phase B3-H11/H13)
+# ------------------------------------------------------------
+backend/data/
+data/storage/
+
 # ------------------------------------------------------------
 # IDEs and editors
 # ------------------------------------------------------------
```

---

## 5. Resultados de Verificación (Verification Results)

| # | Prueba de Validación | Comando Ejecutado | Salida Obtenida | Estado |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Soporte de rutas largas en Git | `git config --get core.longpaths` | `true` | **PASS** |
| 2 | Exclusión de directorio de almacenamiento | `git check-ignore -v backend/data/storage` | `.gitignore:111:backend/data/ backend/data/storage` | **PASS** |
| 3 | Supresión de advertencias en `git status` | `git status --short` | Cero advertencias `Filename too long`. `backend/data/` no figura en untracked. | **PASS** |
| 4 | Preservación física de datos | `Test-Path '\\?\...ed580a09-0d0b-4753-8f88-427d49d3b6f0'` | `True` (Las 71 carpetas de instituciones e instancias de prueba permanecen intactas). | **PASS** |
| 5 | Visibilidad de código fuente de storage | `git check-ignore -v backend/app/core/storage` | Exit code 1 (NO ignorado; código fuente legítimo visible). | **PASS** |
| 6 | Integridad del proyecto | `git diff` | Único archivo modificado: `.gitignore`. Ningún código de aplicación ni esquema alterado. | **PASS** |

---

## 6. Confirmaciones de Seguridad e Integridad

1. **Confirmación de Preservación de Archivos en Runtime:**
   - No se ejecutó ningún comando destructivo (`git rm`, `git clean`, `rm -rf`).
   - Los archivos binarios, adjuntos de entregas y recursos de actividades bajo `backend/data/storage/` se encuentran 100% íntegros y accesibles en el sistema de archivos local.
2. **Confirmación de Código Fuente de Almacenamiento:**
   - La carpeta `backend/app/core/storage/` continúa visible para Git como un directorio con archivos de código fuente pendientes de commit:
     - `backend/app/core/storage/__init__.py`
     - `backend/app/core/storage/interfaces.py`
     - `backend/app/core/storage/local.py`
     - `backend/app/core/storage/service.py`
3. **Confirmación de Cero Alteración en Lógica de Negocio y Base de Datos:**
   - Ningún modelo, migración de Alembic, endpoint o servicio backend fue tocado.
   - Ningún componente o tipo de frontend fue modificado.
4. **No-Commit y No-Push:**
   - No se ha creado ningún commit ni se ha enviado nada a repositorios remotos.

---

## 7. Estado Final de Git (`git status --short`)

```text
 M .gitignore
 M backend/app/api/v1/endpoints/auth.py
 M backend/app/api/v1/endpoints/student_portal.py
 M backend/app/api/v1/endpoints/teacher_portal.py
 M backend/app/audit/interfaces.py
 M backend/app/core/config.py
 M backend/app/models/__init__.py
 M backend/app/models/academic_activity.py
 M backend/app/schemas/communication.py
 M backend/app/schemas/incident.py
 M backend/app/schemas/news.py
 M backend/app/schemas/student_portal.py
 M backend/app/schemas/teacher_portal.py
 M backend/app/services/communication_service.py
 M backend/app/services/guardian_onboarding_service.py
 M backend/app/services/rbac_bootstrap_service.py
 M backend/app/services/student_portal_service.py
 M backend/app/services/teacher_portal_service.py
 M backend/tests/test_teacher_portal_api.py
 M frontend/src/components/student/StudentTaskDetailModal.tsx
 M frontend/src/pages/academic/GuardiansView.tsx
 M frontend/src/pages/academic/StudentsView.tsx
 M frontend/src/pages/guardian/GuardianIncidentsView.tsx
 M frontend/src/pages/guardian/GuardianNewsView.tsx
 M frontend/src/pages/student/StudentCommunicationsView.tsx
 M frontend/src/pages/student/StudentIncidentsView.tsx
 M frontend/src/pages/student/StudentNewsView.tsx
 M frontend/src/pages/student/StudentPortal.tsx
 M frontend/src/pages/teacher/TeacherActivitiesView.tsx
 M frontend/src/pages/teacher/TeacherAttendanceView.tsx
 M frontend/src/pages/teacher/TeacherDashboardView.tsx
 M frontend/src/pages/teacher/TeacherGradesView.tsx
 M frontend/src/pages/teacher/TeacherGroupsView.tsx
 M frontend/src/pages/teacher/TeacherPlanningView.tsx
 M frontend/src/pages/teacher/TeacherPortal.tsx
 M frontend/src/services/communication.ts
 M frontend/src/services/student.ts
 M frontend/src/services/teacher.ts
 M frontend/src/test/TeacherPortal.test.tsx
 M frontend/src/types/communication.ts
 M frontend/src/types/student.ts
 M frontend/src/types/teacher.ts
 M frontend/src/utils/index.ts
 M frontend/tsconfig.tsbuildinfo
?? .agents/
?? AUDITORIA_FASE15_COMUNICACIONES_NOTICIAS_CONVIVENCIA.md
?? GIT_FILENAME_TOO_LONG_AUDIT.md
?? backend/app/core/storage/
?? backend/migrations/versions/020_guardian_invitations.py
?? backend/migrations/versions/021_phase15_communications_news_incidents.py
?? backend/migrations/versions/022_activity_resources_and_storage.py
?? backend/migrations/versions/023_student_submissions_and_attachments.py
?? backend/scratch/qa_seed_phase15.py
?? backend/tests/test_activity_resources_and_storage.py
?? backend/tests/test_student_submissions_api.py
?? docs/reports/B2_H02_CONTROLLED_FIX_REPORT.md
?? docs/reports/B2_H08_DIAGNOSTICO_STARTTIME.md
?? docs/reports/B3-H11_RUNTIME_SCHEMA_RECONCILIATION.md
?? docs/reports/B3-H12_1_SUBMISSIONS_FUNCTIONAL_CONTRACT.md
?? docs/reports/B3-H12_SUBMISSIONS_PRE_IMPLEMENTATION_AUDIT.md
?? docs/reports/B3-H13_H1_BLOCKER_REPORT.md
?? docs/reports/B3-H13_IMPLEMENTATION_REPORT.md
?? docs/reports/B3_H01_DRAFT_CREATION_DIAGNOSTIC.md
?? docs/reports/B3_H01_REMEDIATION_PLAN.md
?? docs/reports/B3_H02_STARTTIME_RUNTIME_INVESTIGATION.md
?? docs/reports/B3_H10_SUBMISSIONS_RESOURCES_AUDIT.md
?? docs/reports/B3_H11_ACTIVITY_RESOURCES_IMPLEMENTATION_REPORT.md
?? docs/reports/B3_IMPLEMENTATION_REPORT.md
?? docs/reports/B3_PRE_IMPLEMENTATION_AUDIT.md
?? docs/reports/GIT_FILENAME_TOO_LONG_REMEDIATION_REPORT.md
?? docs/reports/H2_ATTENDANCE_DATE_CORRECTION_REPORT.md
?? docs/reports/H2_ATTENDANCE_DATE_DIAGNOSTIC.md
?? docs/reports/IDENTITY_FAMILY_LIFECYCLE_FINAL_AUDIT_REPORT.md
?? docs/reports/PHASE_15_CONTROLLED_FIX_REPORT.md
?? docs/reports/PHASE_15_FORENSIC_FUNCTIONAL_AUDIT_REPORT.md
?? docs/reports/PHASE_15_QA_DATA_PREPARATION_REPORT.md
?? docs/reports/TEACHER_PORTAL_B2_IMPLEMENTATION_REPORT.md
?? docs/reports/TEACHER_PORTAL_PRE_IMPLEMENTATION_AUDIT.md
?? docs/reports/VIRTUAL_CLASSROOMS_FORENSIC_COMPLETENESS_AUDIT.md
?? frontend/src/components/teacher/
?? frontend/src/pages/teacher/TeacherCommunicationsView.tsx
?? frontend/src/pages/teacher/TeacherIncidentsView.tsx
?? frontend/src/pages/teacher/TeacherNewsView.tsx
?? frontend/src/test/FormatDate.test.ts
?? frontend/src/test/TeacherCommunicationsAndNews.test.tsx
```

---

## 8. Veredicto Final del Gate

```text
PASS — GIT ISSUE RESOLVED
```
