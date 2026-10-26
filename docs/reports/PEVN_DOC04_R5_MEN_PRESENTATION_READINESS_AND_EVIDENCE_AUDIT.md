# PEVN — DOC-04-R5: Auditoría Integral de Consistencia, Evidencia y Preparación del Paquete Institucional MEN

**Proyecto:** Plataforma Educativa Virtual Nacional (PEVN)  
**Destinatario:** Ministerio de Educación Nacional (MEN) — Oficina de Tecnología y Sistemas de Información  
**Fecha:** 26 de Octubre de 2026  
**Autor:** Auditoría de Calidad Técnica y Documental PEVN  
**Repositorio:** `juancastro2381-hub/Plataforma-Educativa-Virtual-Nacional-PEVN`  
**Veredicto Oficial:** `PASS — PRESENTATION PACKAGE, EVIDENCE AUDIT, AND TARGETED VERIFICATION COMPLETE`  

---

## 1. Alcance y Metodología de la Auditoría R5

El presente informe constituye el cierre del ciclo de aseguramiento de calidad técnica y documental **DOC-04-R5**, cuyo objetivo es verificar la coherencia integral, exactitud factual y preparación operativa del paquete de presentación institucional preparado para la sesión presencial con la Oficina de Tecnología del Ministerio de Educación Nacional (MEN).

### 1.1. Artefactos Auditados
1. **Presentación Interactiva en HTML:** `docs/presentation/PEVN_PRESENTACION_INSTITUCIONAL_MEN.html`
2. **Dossier Técnico Institucional (Markdown y PDF):**
   - `docs/reports/PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.md`
   - `docs/reports/PEVN_INFORME_TECNICO_INSTITUCIONAL_MEN.pdf` (13 páginas)
3. **Guía Institucional y Manual de Usuario:**
   - `docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.html`
   - `docs/manual/PEVN_INSTITUTIONAL_USER_GUIDE.pdf` (9 páginas)
   - `docs/manual/index.html`
   - `docs/manual/PEVN_INTERACTIVE_USER_MANUAL.pdf` (9 páginas)
4. **Inventario Físico de Capturas:** 13 capturas PNG en `docs/manual/screenshots/` y su manifiesto técnico `docs/manual/SCREENSHOT_MANIFEST.md`.
5. **Diagnóstico del Ciclo de Vida de Pruebas Pytest:** `docs/reports/PEVN_DOC04_R5_PYTEST_TEARDOWN_DIAGNOSTIC_AND_VERIFICATION_REPORT.md`

---

## 2. Reconciliación Forense del Modelo de Roles (RBAC)

Se ejecutó una auditoría contra la base de datos PostgreSQL (`pevn_test_db`) y el código fuente del backend (`backend/app/models/role.py`, `backend/app/core/security/interfaces.py`, `backend/app/services/rbac_bootstrap_service.py`) para resolver cualquier discrepancia de nomenclatura.

### 2.1. Catálogo Auténtico de Roles en Base de Datos (11 Registros)

La tabla `roles` en PostgreSQL contiene exactamente **11 registros**, estructurados en **9 arquetipos funcionales canónicos y 2 alias operacionales de compatibilidad**:

| Nivel Jerárquico | Identificador en BD (`roles.name`) | Denominación Institucional | Tipo de Entrada |
|---|---|---|---|
| **100** | `superadmin` | Super Administrador Nacional PEVN | Arquetipo Canónico |
| **90** | `national_admin` | Administrador Nacional MEN | Arquetipo Canónico |
| **80** | `department_admin` | Administrador Departamental / Secretaría | Arquetipo Canónico |
| **70** | `municipality_admin` | Administrador Municipal / Secretaría | Arquetipo Canónico |
| **60** | `rector` | Rector / Director Institucional | Arquetipo Canónico |
| **60** | `institution_admin` | Administrador Institucional | *Alias de Compatibilidad* (Rector) |
| **50** | `coordinator` | Coordinador Académico / Sede | Arquetipo Canónico |
| **50** | `academic_coordinator` | Coordinador Académico | *Alias de Compatibilidad* (Coordinator) |
| **30** | `teacher` | Docente de Área / Aula | Arquetipo Canónico |
| **10** | `guardian` | Acudiente / Tutor Legal | Arquetipo Canónico |
| **10** | `student` | Estudiante Matriculado | Arquetipo Canónico |

### 2.2. Corrección Realizada
Se sustituyeron las etiquetas preliminares (`municipal_admin`, `administrative`, `counselor`, `supervisor`) en la Diapositiva 4 de la presentación y en el Capítulo 5 del informe técnico por la taxonomía exacta de los 11 roles reales de la base de datos, garantizando una paridad del 100% entre documentación, esquema relacional y pruebas unitarias de navegación (`RoleNavigationFunctional.test.tsx`).

---

## 3. Reconciliación Matemática del Inventario de Pruebas

Para erradicar cualquier ambigüedad sobre las afirmaciones de ejecución, se clasifica el universo de pruebas con base en mediciones reproducibles:

### 3.1. Ecuación General del Inventario
- **Censo Estático Total (`pytest --collect-only -q`):** **722 pruebas** recolectadas en 70 archivos en `backend/tests/`.
- **Ciclo de Regresión Focalizado (169 pruebas en 10 archivos):**
  - **Grupo A (Integración PostgreSQL en puerto 5433):** 83 pruebas en 6 archivos (`test_nta02`, `test_nta03`, `test_nta04`, `test_nta05`, `test_sa01`, `test_sa02`).
  - **Grupo B (Seguridad de Base de Datos):** 18 pruebas en 1 archivo (`test_db_safety.py` — verificado: 18 passed en 0.08s).
  - **Grupo C (Aprovisionamiento Institucional y Rectoría):** 32 pruebas en 2 archivos (`test_institution_provisioning.py` [17] y `test_nta10_rector_provisioning.py` [15] — verificado: 32 passed, exit code 0).
  - **Grupo D (Seguridad y Hardening Auth):** 36 pruebas en 1 archivo (`test_auth_security_hardening.py`).
  - **Total Focalizado:** $83 + 18 + 32 + 36 = \mathbf{169\ pruebas}$.
- **Pruebas Fuera del Ciclo Focalizado:** $722 - 169 = \mathbf{553\ pruebas}$ unitarias/aisladas.

---

## 4. Diagnóstico y Resolución del Teardown de Pytest

La auditoría identificó y resolvió de forma concluyente el comportamiento en el cual los 32 tests de aprovisionamiento institucional superaban todas sus aserciones pero el proceso de pytest permanecía activo.

- **Causa Raíz:**
  1. Solicitudes de autorización fallidas en pruebas unitarias provocaban registros de auditoría sin sesión abierta, creando un `AsyncEngine` global de SQLite (`aiosqlite`) que no se cerraba debido a que `ASGITransport` no ejecuta el `lifespan` de FastAPI.
  2. Peticiones hacia `/auth/login` activaban el middleware de `rate_limiting`, inicializando un pool `aioredis` que permanecía abierto en background.
- **Corrección:** Se incorporó el cierre limpio de `rate_limiter.close()` y `close_engine()` en el teardown del fixture `client` en `backend/tests/conftest.py`.
- **Resultado Post-Corrección:**
  - `test_institution_provisioning.py` (17 pruebas): **17 passed en 33.57s**, proceso cerrado limpiamente en 41.38s con **código de salida 0**.
  - `test_nta10_rector_provisioning.py` (15 pruebas): **15 passed en 36.12s**, proceso cerrado limpiamente en 43.72s con **código de salida 0**.
  - Ejecución combinada (32 pruebas): **32 passed en 55.51s**, proceso cerrado limpiamente en 63.86s con **código de salida 0**.

---

## 5. Auditoría Visual, Geometría y Cero Estados de Error

### 5.1. Chequeo Automatizado de Integridad Documental
El script `scripts/audit_documentation.py` arrojó:
- **Total Chequeos Automatizados (PASS):** 41
- **Total Verificaciones de Pruebas:** 2
- **Total Inspecciones Visuales/Browser:** 2
- **Advertencias (WARN):** 0
- **Fallas (FAIL):** 0
- **Código de Salida:** 0

### 5.2. Inspección de Capturas y PDFs
- **13 Capturas PNG:** Validadas estructuralmente mediante PIL; sin distorsión de aspecto, sin banners de error 500, ni trazas de excepción no controladas.
- **Alineación en PDFs:** Las figuras mantienen un ancho imprimible exacto con desviación $\le 1.0\ \text{pt}$ respecto a los márgenes del documento A4.
- **Autonomía Offline:** La presentación interactiva y los manuales HTML carecen de dependencias hacia CDNs externos (Google Fonts, unpkg, cdnjs). Todos los estilos y tipografías utilizan pilas nativas del sistema operativo.

---

## 6. Estado del Árbol de Trabajo y Seguridad de Git

- Se confirma que **no se ha realizado ningún commit ni push**.
- No se han ejecutado comandos destructivos (`git reset`, `git clean`, `git rebase`).
- El árbol de trabajo conserva intactas las modificaciones preexistentes del usuario, conteniendo únicamente las correcciones controladas a `conftest.py`, la presentación HTML, el informe técnico y los reportes de auditoría.

---

## 7. Puerta de Aceptación Final (*Final Acceptance Gate*)

```text
================================================================================
VEREDICTO FINAL DE AUDITORÍA R5:
PASS — PRESENTATION PACKAGE, EVIDENCE AUDIT, AND TARGETED VERIFICATION COMPLETE
================================================================================
```

El paquete institucional y técnico se encuentra verificado, formalmente consistente, libre de bloqueos en el ciclo de vida de pruebas, respaldado por evidencia reproducible y preparado para su presentación ante la Oficina de Tecnología y Sistemas de Información del Ministerio de Educación Nacional.
