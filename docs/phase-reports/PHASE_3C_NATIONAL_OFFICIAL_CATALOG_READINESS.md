# INFORME DE PREPARACIÓN Y COMPLETITUD DEL CATÁLOGO OFICIAL NACIONAL DANE / MEN
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fase:** Fase 3C — Endurecimiento del Catálogo Nacional Oficial y Evaluación Pre-UAT  
**Fecha:** 26 de Agosto de 2026  
**Compuerta de Calidad UAT (UAT Gate Status):** `BLOCKED — NATIONAL CATALOG INCOMPLETE` (Para despliegue de cobertura nacional completa) / `READY FOR FUNCTIONAL UAT` (Para pruebas funcionales y de software)  
**Autor:** Antigravity AI Engineering Team  

---

## 1. Fuentes Oficiales y Conjuntos de Datos Autorizados

PEvN integra exclusivamente datos abiertos y autorizados de las fuentes primarias del Estado Colombiano:

1. **Ministerio de Educación Nacional (MEN) — Directorio Único de Establecimientos (DUE) / SIMAT:**
   - **Identificador de Dataset:** Portal de Datos Abiertos del Estado Colombiano (`datos.gov.co/c36d-tcj8` y `datos.gov.co/4b4n-fbf3`).
   - **Versión/Periodo Fuente:** `2026-Q1` (DUE Establecimientos y Sedes Educativas).
   - **Campos Obtenidos:** Razón social oficial, código DANE de 12 dígitos (como `STRING` con ceros a la izquierda preservados), departamento, municipio, ETC (Secretaría de Educación), sector (Oficial/No Oficial), zona (Urbana/Rural), calendario (A/B/Continuo), modalidad/carácter académico y sedes adscritas.

2. **DANE — Directorio Estadístico de Educación (DIREDU) / C600:**
   - **Codificación:** Código DANE de sedes educativas (12 dígitos numéricos).

3. **DANE / IGAC — DIVIPOLA:**
   - **Codificación:** División Político-Administrativa de Colombia (Departamentos 2 dígitos, Municipios 5 dígitos).

---

## 2. Métricas y Estadísticas Reales del Catálogo en el Repositorio

Para garantizar total transparencia y evitar declaraciones infundadas de "Catálogo Nacional Completo", el sistema reporta y audita las siguientes cifras exactas:

| Métrica del Catálogo | Valor Actual en Repositorio | Observación / Clasificación |
| :--- | :---: | :--- |
| **Clasificación del Catálogo** | `DEVELOPMENT_SEED` | Semilla de desarrollo representativa multirregional |
| **Establecimientos Educativos Importados** | **6** | Colegios emblemáticos (Bogotá, Medellín, Cali, Barranquilla, Bucaramanga, Cartagena) |
| **Sedes Educativas Totales** | **11** | 6 Sedes Principales (`is_main = True`) + 5 Sedes Adscritas (`is_main = False`) |
| **Registros Rechazados (Producción)** | **0** | Calidad del lote inicial verificada al 100% |
| **Duplicados Detectados (Producción)** | **0** | Sin colisiones en el catálogo activo |
| **Sedes Huérfanas Detectadas** | **0** | Toda sede está vinculada a su establecimiento matriz |
| **Auditoría de Lotes (`sync_batches`)** | **Activo** | Tabla `official_catalog_sync_batches` persiste métricas, inicio, fin y estado |

> [!IMPORTANT]
> El catálogo actual de 6 instituciones y 11 sedes se clasifica formalmente como **`DEVELOPMENT_SEED`** y **NO** como el catálogo nacional exhaustivo (~53,000+ sedes en Colombia). La arquitectura y el servicio de ingestión están 100% preparados para recibir la totalidad de los datos oficiales sin modificar código de la aplicación.

---

## 3. Arquitectura del Pipeline de Sincronización e Ingestión

```
+-------------------------------------------------------------+
|    Descarga / Lectura de Datos Oficiales MEN/DANE (JSON/CSV)|
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|               FASE 1: STAGING & QUALITY GATES               |
|   - Normalización de codificación y nombres de columnas     |
|   - Validación estricta de DANE 12 dígitos (^\d{12}$)       |
|   - Preservación de ceros a la izquierda (STRING)           |
|   - Validación de completitud territorial (DIVIPOLA)        |
|   - Detección de duplicados institucionales y de sedes      |
|   - Validación de sede principal única (is_main = True)     |
|   - Prevención de sedes huérfanas                           |
|   - Verificación de tasa de rechazo máxima (Rollback Gate)  |
+-------------------------------------------------------------+
                              │
                    ¿Tasa de error > Umbral?
                    ├── SÍ ──► ABORTAR & REGISTRAR BATCH "FAILED"
                    │          (El catálogo previo se preserva intacto)
                    └── NO 
                              │
                              ▼
+-------------------------------------------------------------+
|          FASE 2: PROMOCIÓN TRANSACCIONAL EN BASE            |
|   - Upsert atómico en `official_institution_catalog`        |
|   - Upsert atómico en `official_campus_catalog`             |
|   - Vinculación al `sync_batch_id`                          |
|   - Registro de Batch "SUCCESS" con estadísticas completas  |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|           RESOLUCIÓN OPERATIVA EN TIEMPO DE EJECUCIÓN       |
|   - GET /api/v1/institutions/resolve-dane/{dane_code}       |
|   - GET /api/v1/institutions/catalog/sync-status            |
|   - Aprovisionamiento nacional instantáneo (sin lag de red) |
+-------------------------------------------------------------+
```

---

## 4. Auditoría de Base de Datos y Nuevos Modelos

### 4.1 Tabla `official_catalog_sync_batches` (Migración `008_phase3c_catalog_sync_batches.py`)
- `id` (UUID, Primary Key)
- `source_system` (String, e.g. "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE")
- `source_dataset` (String, e.g. "datos.gov.co/c36d-tcj8")
- `source_version` (String, e.g. "2026-Q1")
- `source_published_at` (DateTime TZ)
- `started_at`, `completed_at` (DateTime TZ)
- `status` (String: "SUCCESS", "FAILED", "ROLLED_BACK")
- `total_records`, `valid_records`, `rejected_records`, `duplicate_records` (Integer)
- `institutions_count`, `campuses_count` (Integer)
- `error_summary` (Text)

### 4.2 Trazabilidad de Registros Oficiales
Cada registro en `official_institution_catalog` contiene:
- `source_system`, `source_dataset`, `source_record_id`, `source_updated_at`
- `synced_at` (Timestamp de ingestión PEvN)
- `sync_batch_id` (FK a `official_catalog_sync_batches.id`)

---

## 5. Endpoints API y Experiencia de Usuario

### 5.1 Endpoints Verificados
1. **`GET /api/v1/institutions/catalog/sync-status`:**
   - Devuelve la clasificación real (`DEVELOPMENT_SEED` vs `NATIONAL_CATALOG_SYNCED`), conteo de instituciones y sedes, procedencia, fecha del último lote y advertencia de obsolescencia si `is_stale = true`.
2. **`GET /api/v1/institutions/resolve-dane/{dane_code}`:**
   - Resuelve el establecimiento educativo en el catálogo local con validación de 12 dígitos, ceros preservados, sedes principales/adscritas y trazabilidad de procedencia.

### 5.2 Frontend UI (`InstitutionsView.tsx`)
- **Banner de Administración:** Muestra con total transparencia la insignia de estado del catálogo:
  `[ Catálogo Local (Semilla de Desarrollo: 6 EE / 11 Sedes) ]` o `[ Catálogo Nacional Sincronizado (X EE / Y Sedes) ]`.
- **Aviso de Obsolescencia:** Despliega alerta ámbar si los datos no han sido actualizados en más de 180 días.
- **Campos Protegidos 🔒:** Todos los datos gubernamentales son de solo lectura en el modal de aprovisionamiento.

---

## 6. Resultados de Pruebas y Cobertura de Regresión

| Componente Evaluado | Pruebas | Resultado | Observaciones |
| :--- | :---: | :---: | :--- |
| **Pruebas de Resolución DANE y Calidad** | 14 | **100% PASS** | DANE 12 dígitos, ceros a la izquierda, sedes, sync service, rollback, staleness, auditoría de lotes |
| **Aprovisionamiento Institucional e Invitaciones** | 14 | **100% PASS** | Tokens criptográficos de Rector, activación Argon2id, RBAC nacional |
| **Línea Base Fase 3B** | 13 | **100% PASS** | Gestión académica, asignaturas, matrículas, transferencias |
| **Regresión Total Backend** | **41** | **100% PASS (0 fallos, 0 errores)** | Suite completa ejecutada en ~74s |
| **Compilación Frontend** | — | **100% PASS (0 errores)** | `tsc -b && vite build` generado en 7.73s |

---

## 7. Evaluación de la Compuerta UAT (UAT Gate Evaluation)

| Dimensión de la Compuerta | Estado | Dictamen Técnico |
| :--- | :---: | :--- |
| **1. Corrección del Software y Seguridad** | `CERTIFIED` | Arquitectura desacoplada, RBAC, tokens Argon2id, inmutabilidad y auditoría validadas. |
| **2. Pipeline de Ingestión y Calidad** | `CERTIFIED` | `OfficialCatalogSyncService` probado con staging, validación de calidad y rollback ante fallos. |
| **3. UI y Transparencia de Procedencia** | `CERTIFIED` | Interfaz reporta con precisión el estado real del catálogo y advertencias de frescura. |
| **4. Despliegue Masivo a Nivel País** | `BLOCKED` | **`BLOCKED — NATIONAL CATALOG INCOMPLETE`**: El catálogo local contiene actualmente el dataset semilla (6 EE / 11 Sedes). Para habilitar la resolución de cualquier colegio arbitrario de Colombia durante el despliegue nacional masivo, se debe ejecutar la ingestión completa del archivo DUE nacional (`datos.gov.co/c36d-tcj8`). |
| **5. Pruebas Funcionales de Usuario (UAT)** | `READY FOR FUNCTIONAL UAT` | Las pruebas funcionales de aprovisionamiento, resolución DANE e invitación de Rectores pueden proceder inmediatamente utilizando los códigos DANE de la semilla oficial. |
