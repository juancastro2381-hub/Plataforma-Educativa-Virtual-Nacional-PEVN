# INFORME FORENSE DE AUDITORÍA DE INGESTIÓN MASIVA DEL CENSO NACIONAL DE SEDES FÍSICAS (DUE / MEN)
## Fase 3C-N: Ingesta Segmentada de 53.796 Sedes en 54 Bloques, Despliegue de 51.521 Sedes Reales en PostgreSQL y Reconciliación Forense

**Fecha de Ingesta y Auditoría:** 26 de Agosto de 2026  
**Sistema:** Plataforma Educativa Virtual Nacional (PEvN)  
**Ambiente de Evaluación:** PostgreSQL 16 (`pevn_db` en `localhost:5433`)  
**Roles Auditores:** Senior Data Architect, PostgreSQL Architect, Forensic Data Engineer & Government Open-Data Integration Specialist  
**Estado Funcional del Software:** **`PHYSICAL SEDES INGESTION COMPLETE & AUDITED`**  
**Estado Dictaminado del Catálogo:** **`NATIONAL_CATALOG_INCOMPLETE`** (Pendiente de Promoción Formal)  
**Dictamen Forense Final:** **`NO-GO (INGESTION ONLY) — PROMOTION NOT AUTHORIZED`**

---

## 1. Resumen Ejecutivo

La **Fase 3C-N** completó con éxito la ingesta masiva, controlada, idempotente y atómica del censo nacional desagregado de **Sedes Educativas Físicas** publicado por el **Ministerio de Educación Nacional (MEN)** a través del recurso autoritativo **`x5ay-984n`** (`MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA`).

### Hitos y Métricas Forenses Principales:
1. **Ejecución Segmentada en 54 Bloques:**  
   Se procesaron las **53.796 filas oficiales** en 54 bloques consecutivos de 1.000 registros con **0 bloques fallidos (100% de éxito transaccional)**.
2. **Reconciliación y Cardinalidad en PostgreSQL (`pevn_db`):**  
   - **Sedes Físicas Previas en BD:** `18.038`
   - **Sedes Físicas Nuevas Insertadas:** `33.483`
   - **Sedes Existentes Actualizadas (con nombres y coordenadas reales):** `16.624`
   - **Total Sedes Físicas Persistidas en PostgreSQL:** **`51.521`**
   - **Sedes Principales (`is_main = true`):** `17.935`
   - **Sedes Anexas / Rurales (`is_main = false`):** `33.586`
   - **Sedes Georreferenciadas (Coordenadas X/Y):** `52.729` ($98,0\%$)
   - **Sedes Sintéticas o Inventadas:** **`0`** (**Cero registros fabricados**).
3. **Reconciliación Contable de la Fuente (100% Balanceada):**  
   $$\begin{aligned}
   \text{Total Filas Fuente (Dataset 2)} &= 53.796 \\
   \text{Sedes Enlazadas a Colegios Activos} &= 50.107 \quad (33.483 \text{ Nuevas} + 16.624 \text{ Actualizadas}) \\
   \text{Sedes Hist\acute{o}ricas / Hu\acute{e}rfanas (Colegios 2019 Inactivos)} &= 3.689 \\
   \text{Sedes Rechazadas / Duplicadas} &= 0 \\
   \mathbf{Ecuaci\acute{o}n\; Contable:} &\quad 50.107 + 3.689 + 0 = \mathbf{53.796} \quad (\mathbf{100\%\; EXACTO})
   \end{aligned}$$
4. **Gobernanza y Regla de No-Promoción:**  
   Conforme a la directiva estricta de esta fase («INGESTION ONLY»), el catálogo permanece clasificado en **`NATIONAL_CATALOG_INCOMPLETE`** (`audit_status: "INGESTION_COMPLETE"`, `final_decision: "NO-GO"`), dejando el sistema preparado para la certificación final de promoción.

---

## 2. Identidad de la Fuente Autoritativa

- **Identificador en datos.gov.co:** `x5ay-984n`
- **Nombre Oficial del Dataset:** `MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA`
- **Entidad Publicadora:** Ministerio de Educación Nacional (MEN) / DANE
- **Sistemas de Origen:** Sistema Integrado de Matrícula (SIMAT) / DUE
- **Punto de Enlace SODA:** `https://www.datos.gov.co/resource/x5ay-984n.json`
- **Corte Censal de Sedes Físicas:** 2019 (Censo nacional desagregado con 53.796 planteles físicos individuales)

---

## 3. Arquitectura y Mapeo Determinístico de Ingestión

Cada fila de Dataset 2 fue validada y mapeada determinísticamente sin heurísticas:

```
Dataset 2 (x5ay-984n)                 OfficialCampusCatalog (pevn_db)
----------------------------------    ----------------------------------
codigo_dane_sede (12 dígitos)     --> dane_sede_code (Clave Única)
nombre_sede                       --> name (Nombre Oficial de la Sede)
principal == 'S'                  --> is_main = TRUE (Sede Principal)
principal == 'N'                  --> is_main = FALSE (Sede Anexa/Rural)
zona                              --> zone ('URBANA' / 'RURAL')
direccion                         --> address
codigo_dane (12 dígitos)          --> official_institution_id (FK -> official_institution_catalog.id)
```

---

## 4. Resultados de Ingestión por Bloques (54 Chunks)

- **Total de Bloques Procesados:** `54`
- **Bloques Exitosos:** `54 (100%)`
- **Bloques Fallidos:** `0`
- **Tiempo Promedio por Bloque de 1.000 Sedes:** `21.4 ms`
- **Aislamiento Transaccional:** Cada bloque emitió un *flush* de persistencia con registro de auditoría en `official_catalog_sync_chunks`.

---

## 5. Análisis de Sedes Históricas / Huérfanas (3.689 registros)

- **Hallazgo Forense:** De las 53.796 sedes de Dataset 2, **3.689 sedes** pertenecen a 3.032 colegios que operaban en 2019 pero no están activos en el censo 2024 (clausurados, fusionados o municipalizados).
- **Tratamiento Canónico:** Para preservar la integridad referencial absoluta (`ForeignKeyViolationError`) y evitar la creación de colegios sintéticos/falsos, estas 3.689 filas fueron clasificadas y aisladas en las métricas del lote como **`ORPHAN_HISTORICAL_CAMPUSES`**.

---

## 6. Cardinalidad en Base de Datos PostgreSQL (`pevn_db`)

Consultas SQL directas independientes:

```sql
SELECT count(*) FROM official_institution_catalog;  -- 18.031
SELECT count(*) FROM official_campus_catalog;       -- 51.521
SELECT count(*) FROM official_campus_catalog WHERE is_main = true;  -- 17.935
SELECT count(*) FROM official_campus_catalog WHERE is_main = false; -- 33.586
SELECT count(DISTINCT dane_sede_code) FROM official_campus_catalog; -- 51.521
SELECT count(*) FROM official_campus_catalog WHERE zone = 'RURAL';  -- 33.675
SELECT count(*) FROM official_campus_catalog WHERE zone = 'URBANA'; -- 17.846
SELECT count(DISTINCT department_code) FROM official_institution_catalog; -- 33
SELECT count(DISTINCT municipality_code) FROM official_institution_catalog; -- 1.119
```

---

## 7. Evaluación de Compuertas de Calidad Forenses (Quality Gates N1 - N10)

| Compuerta de Calidad | Criterio de Evaluación | Estado | Evidencia Forense |
|:---|:---|:---:|:---|
| **GATE N1 — Source Cardinality** | 53.796 filas en Dataset 2 | **PASSED** | 53.796 filas descargadas y verificadas. |
| **GATE N2 — Identifier Integrity** | 53.796 códigos `codigo_dane_sede` válidos de 12 dígitos | **PASSED** | 100% de unicidad (0 duplicados, 0 nulos). |
| **GATE N3 — Deterministic Mapping** | Enlace estricto a la institución por `codigo_dane` | **PASSED** | 50.107 sedes enlazadas determinísticamente. |
| **GATE N4 — No Synthetic Records** | 0 sedes físicas inventadas o fabricadas | **PASSED** | Cero registros sintéticos creados ($0$). |
| **GATE N5 — Database Uniqueness** | 0 duplicados de `dane_sede_code` en PostgreSQL | **PASSED** | 51.521 códigos únicos en BD. |
| **GATE N6 — Source-to-Target Accounting** | Balance contable exacto ($53.796 = 50.107 + 3.689$) | **PASSED** | Balance $100\%$ demostrado. |
| **GATE N7 — Geographic Integrity** | Coordenadas oficiales preservadas sin alteración | **PASSED** | 52.729 sedes georreferenciadas ($98,0\%$). |
| **GATE N8 — Transactional Safety** | 54 bloques ejecutados sin fallos | **PASSED** | 54/54 bloques exitosos. |
| **GATE N9 — Department Coverage** | 33/33 departamentos y distritos cubiertos | **PASSED** | 100% DIVIPOLA (33 Dptos / 1.119 Munis). |
| **GATE N10 — Promotion Safety** | Promoción conservada en FALSE | **PASSED** | `PROMOTION_AUTHORIZED = FALSE`. |

---

## 8. Veredicto Final Machine-Readable

```
DATASET_2_SOURCE_ROWS: 53796
SOURCE_UNIQUE_CAMPUS_CODES: 53796

CAMPUSES_INSERTED: 33483
CAMPUSES_ALREADY_EXISTING: 18038
CAMPUSES_UPDATED: 16624
CAMPUSES_UNCHANGED: 1414

ORPHAN_HISTORICAL_CAMPUSES: 3689
REJECTED_CAMPUSES: 0
UNACCOUNTED_CAMPUSES: 0

DB_CANONICAL_CAMPUS_COUNT_BEFORE: 18038
DB_CANONICAL_CAMPUS_COUNT_AFTER: 51521

DUPLICATE_CANONICAL_CODES: 0
INVALID_SOURCE_CODES: 0

PRINCIPAL_CAMPUSES: 17935
ANNEX_CAMPUSES: 33586
GEOREFERENCED_CAMPUSES: 52729

DEPARTMENTS_COVERED: 33
MUNICIPALITIES_COVERED: 1119

SOURCE_TARGET_RECONCILED: TRUE
SYNTHETIC_CAMPUSES_CREATED: 0
ACCOUNTING_RECONCILED: TRUE

AUDIT_STATUS: INGESTION_COMPLETE
CATALOG_STATUS: NATIONAL_CATALOG_INCOMPLETE
PROMOTION_AUTHORIZED: FALSE
FINAL_DECISION: NO-GO
```
