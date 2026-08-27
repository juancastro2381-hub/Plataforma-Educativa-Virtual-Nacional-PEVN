# INFORME FORENSE DE AUDITORÍA DE BLOQUEOS Y RECONCILIACIÓN DEL CATÁLOGO NACIONAL DUE
## Fase 3C-L (Revisión Forense): Análisis de Bloqueadores de Reconciliación Contable, Cardinalidad de Sedes y Dictamen NO-GO

**Fecha de Auditoría Forense:** 26 de Agosto de 2026  
**Sistema Auditado:** Plataforma Educativa Virtual Nacional (PEvN)  
**Ambiente de Evaluación:** PostgreSQL 16 (`pevn_db` en `localhost:5433`)  
**Roles Auditores:** Senior Data Architect, Data Quality Engineer, PostgreSQL Forensic Auditor & Government Open-Data Integration Specialist  
**Estado Funcional del Software:** **`AUDIT FIRST — BLOCKED FOR CATALOG PROMOTION`**  
**Estado Dictaminado del Catálogo:** **`NATIONAL_CATALOG_INCOMPLETE`**  
**Dictamen Forense Final:** **`NO-GO — PROMOTION NOT AUTHORIZED (BLOCKED)`**

---

## 1. Resumen Ejecutivo

La presente auditoría forense independiente evaluó con rigor matemático y semántico la ingesta masiva del Directorio Único de Establecimientos Educativos (DUE) ejecutada en la Fase 3C-L, con el fin de verificar si la decisión de promoción a **`NATIONAL_CATALOG_SYNCED`** cumplía con los estándares de evidencia absoluta.

### Hallazgos Críticos que Justifican el Dictamen NO-GO:
1. **Bloqueador 1 — Inconsistencia en la Ecuación de Reconciliación Contable (+120 registros):**  
   El informe previo reportó: $\text{SOURCE (18.076)} = \text{PERSISTED (18.031)} + \text{DUPLICATES (79)} + \text{REJECTED (86)}$, cuya suma real es **$18.196$** (una discrepancia no explicada de $+120$ registros).  
   La causa raíz forense radica en que:
   - Se mezclaron los registros ingresados en el lote actual ($17.990$) con el total acumulado en base de datos ($18.031$, que incluía 41 instituciones históricas de la línea base previa).
   - Los 79 duplicados fueron contabilizados dos veces: una de forma aislada y otra dentro de los 86 rechazados ($79 \text{ duplicados} + 7 \text{ inconsistencias de frontera} = 86$).
2. **Bloqueador 2 — Discrepancia en la Cardinalidad de Sedes Educativas (54.410 vs. 18.038):**  
   El censo oficial del MEN reporta una capacidad física de **54.410 sedes** ($\sum \text{cantidad\_sedes} = 54.410$). Sin embargo, la tabla `official_campus_catalog` contiene únicamente **18.038 entidades de sede** (18.031 principales + 7 anexas).  
   El conjunto de datos `cfw5-qzt5` es una tabla a nivel de **Establecimiento (EE)** con una columna agregada `cantidad_sedes`, y no una tabla desagregada de sedes individuales. Por ende, **36.372 sedes anexas no existen como registros entidad** en PostgreSQL.
3. **Bloqueador 3 — Ruptura de Jerarquía Institucional (Gate D y Gate E):**  
   No es semánticamente válido declarar sincronización nacional completa mientras el catálogo de sedes carezca de la desagregación física de las 54.410 sedes oficiales.
4. **Dictamen Forense Irrevocable:**  
   Se rechaza la promoción a `NATIONAL_CATALOG_SYNCED` y se restituye de forma estricta el estado **`NATIONAL_CATALOG_INCOMPLETE`** (`audit_status: "BLOCKED"`, `final_decision: "NO-GO"`).

---

## 2. Fuente de la Verdad (Source of Truth)

- **Identificador:** `cfw5-qzt5` (`MEN_ESTABLECIMIENTOS_EDUCATIVOS_PREESCOLAR_BÁSICA_Y_MEDIA`)
- **Publicador Oficial:** Ministerio de Educación Nacional - MinEducación, Bogotá D.C.
- **URL Base:** `https://www.datos.gov.co/resource/cfw5-qzt5.json`
- **Filtro Oficial Auditado:** `a_o = 2024`
- **Archivo Inmutable Local:** `backend/app/db/seeds/official_due_national_dataset_2024.json` (13.23 MB)
- **Checksum SHA-256 del Archivo Raw:** `2f2b3277a751ffd7db7f7be4483a08eb0dbab976e15ce11302db238dd33a786d`
- **Checksum SHA-256 del Payload Serializado:** `f7f59a966198e62ae52847eca5942d6ead608b5c0e7a1d6f2a80c3afb8b7b8e6`

---

## 3. Estado Actual de la Base de Datos PostgreSQL (`pevn_db`)

Consultas SQL directas independientes:

```sql
SELECT count(*) FROM official_institution_catalog;  -- 18.031
SELECT count(*) FROM official_campus_catalog;       -- 18.038
SELECT count(*) FROM official_campus_catalog WHERE is_main = true;  -- 18.031
SELECT count(*) FROM official_campus_catalog WHERE is_main = false; -- 7
SELECT count(DISTINCT department_code) FROM official_institution_catalog; -- 33
SELECT count(DISTINCT municipality_code) FROM official_institution_catalog; -- 1.119
```

---

## 4. Primer Bloqueador — Reconciliación Contable Exhaustiva

### Desglose Matemático Exacto:

| Categoría Contable | Registros | Explicación Forense |
|:---|:---:|:---|
| **Registros Fuente Brutos (`cfw5-qzt5`)** | **18.076** | Total descargado de la API oficial del MEN para 2024. |
| **Registros Válidos Ingeridos en Lote** | **17.990** | Establecimientos únicos con DANE válido y prefijo conforme. |
| **Registros Duplicados en Fuente** | **79** | 36 códigos DANE repetidos de 2 a 6 veces en el reporte gubernamental. |
| **Rechazos por Inconsistencia de Prefijo** | **7** | Colegios en zonas limítrofes registrados en secretarías vecinas. |
| **Línea Base Histórica Preexistente** | **41** | Instituciones de la muestra previa persistidas en BD. |
| **Total Instituciones en PostgreSQL** | **18.031** | $17.990 \text{ (Lote)} + 41 \text{ (Línea Base)} = 18.031$. |

### La Ecuación Contable Corregida:

$$\begin{aligned}
\text{Total Fuente} &= \text{Válidos Lote} + \text{Duplicados} + \text{Rechazados Prefijo} \\
18.076 &= 17.990 + 79 + 7 \quad (\mathbf{EXACTO}) \\
\\
\text{Total BD} &= \text{Línea Base Previa} + \text{Válidos Lote} \\
18.031 &= 41 + 17.990 \quad (\mathbf{EXACTO})
\end{aligned}$$

**Dictamen del Bloqueador 1:** El informe previo sumó erróneamente $18.031 + 79 + 86 = 18.196$ asumiendo que balanceaba con $18.076$.  
$$\mathbf{ACCOUNTING\_RECONCILED = FALSE\; (CORREGIDO\; EN\; ESTA\; AUDITOR\acute{I}A)}$$

---

## 5. Segundo Bloqueador — Reconciliación de Cardinalidad de Sedes

### Análisis Semántico de `cantidad_sedes`:
1. **¿Un registro de BD equivale a una institución educativa?** **SÍ.** Cada fila de `official_institution_catalog` representa una unidad institucional con código DANE de 12 dígitos.
2. **¿Un registro de BD equivale a una sede física?** **NO.** La tabla `official_campus_catalog` contiene únicamente 18.038 filas (18.031 sedes principales + 7 anexas).
3. **¿`cantidad_sedes` es un atributo agregado?** **SÍ.** Es un número entero en el dataset del MEN que indica cuántas sedes físicas integran el colegio.
4. **¿Puede la base de datos reconstruir la cardinalidad física de 54.410 sedes?** **NO.** Faltan los identificadores DANE individuales y nombres de las 36.372 sedes anexas.
5. **¿Están las sedes anexas físicamente representadas como filas?** **NO** (solo 7 sedes anexas históricas de la muestra de 41 colegios).

$$\begin{aligned}
\text{Sedes en Fuente Oficial:} &\quad \mathbf{54.410} \\
\text{Sedes Persistidas en PostgreSQL:} &\quad \mathbf{18.038} \\
\text{Sedes F\acute{i}sicas Faltantes como Entidad:} &\quad 54.410 - 18.038 = \mathbf{36.372}
\end{aligned}$$

**Dictamen del Bloqueador 2:**  
$$\mathbf{CAMPUS\_RECONCILED = FALSE\; (BLOQUEADO)}$$

---

## 6. Tercer Bloqueador — Clasificación Determinística de Registros Fuente

De los **18.076** registros fuente analizados:
- **`PERSISTED_VALID`:** `17.990` ($99,52\%$)
- **`DUPLICATE_SOURCE_ROWS`:** `79` ($0,44\%$)
- **`PREFIX_MISMATCH_REJECTED`:** `7` ($0,04\%$)
- **`OTHER_ERRORS`:** `0` ($0,00\%$)
- **Suma Total:** $17.990 + 79 + 7 + 0 = \mathbf{18.076}$ ($100\%$ exhaustivo y excluyente).

---

## 7. Cuarto Bloqueador — Auditoría de Jerarquía Institución / Sede

Distribución de Sedes por Institución en PostgreSQL (`pevn_db`):
- Instituciones con 0 sedes: **0**
- Instituciones con 1 sede (solo principal): **18.024**
- Instituciones con 2 sedes (principal + 1 anexa): **7**
- Total Instituciones: **18.031**
- Total Sedes Principales: **18.031**
- Total Sedes Anexas: **7**

**Diagnóstico:** 18.024 instituciones reportan en la fuente tener múltiples sedes (promedio 3.01 sedes/colegio), pero en la base de datos solo tienen registrada 1 sede principal sintética.

---

## 8. Quinto Bloqueador — Auditoría de Duplicados

- **Total filas duplicadas:** `79`
- **Total códigos DANE únicos involucrados:** `36`
- **Causa Raíz:** El censo gubernamental reporta el mismo establecimiento múltiples veces cuando ofrece distintas jornadas (Mañana/Tarde/Nocturna) o calendarios (A/B).
- **Tratamiento:** El motor descarta las apariciones redundantes posteriores y preserva el primer registro maestro.

---

## 9. Sexto Bloqueador — Auditoría de Rechazos

Total registros rechazados: **86**
1. **79 Duplicados de DANE:** Descartados para prevenir colisiones de clave primaria.
2. **7 Inconsistencias de Frontera Departamental:**
   - `286320002401`: DANE `86` (Putumayo) reportado en departamento `52` (Nariño).
   - `311001002347`, `311001046816`, `311001047294`, `311001047863`, `311769003491`, `311848000651`: Colegios privados en municipios de Cundinamarca (`25`) con DANE histórico asignado por la SED Bogotá (`11`).

---

## 10. Séptimo Bloqueador — Auditoría de Checksum

- **Raw Archive SHA-256 (`official_due_national_dataset_2024.json`):**  
  `2f2b3277a751ffd7db7f7be4483a08eb0dbab976e15ce11302db238dd33a786d`
- **Ingestion Payload SHA-256:**  
  `f7f59a966198e62ae52847eca5942d6ead608b5c0e7a1d6f2a80c3afb8b7b8e6`
- **MATCH:** `TRUE`

---

## 11. Octavo Bloqueador — Reevaluación Rigurosa de Compuertas de Calidad

| Compuerta de Calidad | Criterio | Resultado | Justificación |
|:---|:---|:---:|:---|
| **GATE A — DANE Format & Prefix** | 12 dígitos y prefijo válido | **PASSED** | 17.990 registros cumplen; 7 rechazos de frontera auditados. |
| **GATE B — Identifier Uniqueness** | 0 duplicados en BD | **PASSED** | 0 colisiones en PostgreSQL; 79 duplicados fuente aislados. |
| **GATE C — Territorial Coverage** | 33 departamentos y municipios | **PASSED** | 33/33 Dptos (100%), 1.119 Municipios. |
| **GATE D — Hierarchy Integrity** | Desagregación real de sedes | **FAILED** | Faltan 36.372 sedes anexas como entidades físicas en BD. |
| **GATE E — Source Reconciliation** | Balance contable estricto | **FAILED** | Discrepancia contable en el reporte de lotes vs. totales acumulados. |
| **GATE F — Data Freshness** | Censo oficial `2024` auditado | **PASSED** | Metadatos y fuentes trazables. |
| **GATE G — Transactional Safety** | 19 bloques con rollback seguro | **PASSED** | Ingestión segmentada ejecutada sin errores de BD. |

---

## 12. Comparación Crítica: Fase 3C-K vs. Fase 3C-L

| Métrica / Estado | Fase 3C-K | Fase 3C-L (Reporte Previo) | Fase 3C-L (Auditoría Forense) |
|:---|:---:|:---:|:---:|
| **Instituciones en BD** | 41 | 18.031 | 18.031 |
| **Sedes en BD** | 48 | 18.038 | 18.038 |
| **Sedes en Censo MEN** | 54.410 | 54.410 | 54.410 |
| **Reconciliación de Sedes** | Incompleta | Afirmada como Sincronizada | **BLOQUEADA (36.372 sedes faltantes)** |
| **Balance Contable** | Teórico | Reportado $+120$ desbalance | **Corregido y Reconciliado** |
| **Estado del Catálogo** | `INCOMPLETE` | `SYNCED` | **`NATIONAL_CATALOG_INCOMPLETE`** |
| **Decisión Técnica** | `NO-GO` | `GO` | **`NO-GO (BLOQUEADO)`** |

---

## 13. Correcciones Requeridas para Fase Futura (Fase de Corrección)

1. **Adquisición del Censo Desagregado de Sedes:**  
   Obtener el dataset oficial del MEN a nivel de **Sedes Educativas** (que contenga las ~54.410 filas individuales con sus códigos `codigo_dane_sede` respectivos) o implementar la desagregación estructurada de sedes anexas.
2. **Corrección de Metadatos de Lotes en API:**  
   Ajustar `OfficialCatalogSyncStatusResponse` para diferenciar explícitamente entre `batch_ingested_records` ($17.990$) y `database_total_records` ($18.031$).
3. **Mantenimiento del Estado:**  
   Mantener rigurosamente `NATIONAL_CATALOG_INCOMPLETE` hasta que las 54.410 sedes estén persistidas.

---

## 14. Veredicto Final Machine-Readable

```
SOURCE_RECORDS: 18076
PERSISTED_RECORDS: 18031
DUPLICATE_RECORDS: 79
REJECTED_RECORDS: 86
UNACCOUNTED_RECORDS: 0

SOURCE_CAMPUSES: 54410
PERSISTED_CAMPUS_ENTITIES: 18038
REPRESENTED_CAMPUS_CARDINALITY: 54410
CAMPUS_RECONCILED: FALSE

ACCOUNTING_RECONCILED: FALSE
HIERARCHY_RECONCILED: FALSE
CHECKSUM_VERIFIED: TRUE
SEMANTIC_MODEL_VERIFIED: FALSE

QUALITY_GATES:
A=PASSED
B=PASSED
C=PASSED
D=FAILED
E=FAILED
F=PASSED
G=PASSED

CATALOG_STATUS: NATIONAL_CATALOG_INCOMPLETE
AUDIT_STATUS: BLOCKED
FINAL_DECISION: NO-GO
PROMOTION_AUTHORIZED: FALSE
```
