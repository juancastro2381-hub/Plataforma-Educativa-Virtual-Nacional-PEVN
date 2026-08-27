# INFORME FORENSE DE AUDITORÍA DEL MODELO CANÓNICO DE ENTIDADES DUE Y RECONCILIACIÓN DE CARDINALIDAD DE SEDES
## Fase 3C-M: Desarticulación Semántica de Establecimiento vs. Sede, Descubrimiento del Dataset Desagregado de Sedes (`x5ay-984n`) y Dictamen Forense

**Fecha de Auditoría Forense:** 26 de Agosto de 2026  
**Sistema:** Plataforma Educativa Virtual Nacional (PEvN)  
**Ambiente de Evaluación:** PostgreSQL 16 (`pevn_db` en `localhost:5433`)  
**Roles Auditores:** Senior Data Architect, Forensic Data Engineer, PostgreSQL Architect & Government Open-Data Integration Specialist  
**Estado Funcional del Software:** **`AUDIT COMPLETE — CANONICAL MODEL RESOLVED`**  
**Estado Dictaminado del Catálogo:** **`NATIONAL_CATALOG_INCOMPLETE`**  
**Dictamen Forense Final:** **`NO-GO — PROMOTION NOT AUTHORIZED (BLOCKED)`**

---

## 1. Resumen Ejecutivo

La **Fase 3C-M** tuvo como objetivo resolver con evidencia forense e irrefutable la discrepancia semántica y de cardinalidad entre los **18.076 Establecimientos Educativos** y las **54.410 Sedes Educativas Físicas** declaradas en el Directorio Único de Establecimientos (DUE) del Ministerio de Educación Nacional (MEN).

### Conclusiones Principales:
1. **Resolución Semántica del Modelo DUE (Biestratificado):**  
   El DUE no es una sola tabla plana, sino una arquitectura jerárquica oficial de **dos niveles**:
   - **Nivel 1 (Establecimiento Educativo / EE):** Entidad administrativa y rectoral identificada por `codigo_dane` (12 dígitos). Total nacional: **18.076 establecimientos**. Contiene el atributo numérico agregado `cantidad_sedes`.
   - **Nivel 2 (Sede Educativa / Campus Físico):** Inmueble y plantel físico identificado por su propio código DANE de 12 dígitos (`codigo_dane_sede`). Total nacional: **53.796 a 54.410 sedes físicas**, donde cada sede tiene un indicador `principal` (`"S"` = Sede Principal, `"N"` = Sede Anexa).
2. **Descubrimiento del Dataset Autoritativo Desagregado de Sedes:**  
   Se descubrió e inspeccionó en `datos.gov.co` el recurso oficial:  
   **`x5ay-984n`** (`MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA`), publicado directamente por MinEducación.  
   - Total de registros: **`53.796`**
   - Clave foránea: `codigo_dane` (enlace 1-a-Muchos hacia el Establecimiento).
   - Clave única de sede: `codigo_dane_sede` (12 dígitos numéricos por cada sede física).
   - Atributos físicos: `nombre_sede`, `principal` (`S`/`N`), coordenadas geográficas (`coordenada_x_sede`, `coordenada_y_sede`), `zona` (Urbana/Rural), y `total_matricula`.
3. **Causa Raíz de las 18.038 Sedes en PostgreSQL:**  
   La fase previa ingirió únicamente el **Dataset 1 (`cfw5-qzt5`)**, el cual genera una sede principal sintética por cada establecimiento. Por tanto, las 36.372 sedes anexas no han sido ingeridas aún porque residen en el **Dataset 2 (`x5ay-984n`)**.
4. **Dictamen de Gobernanza:**  
   El catálogo institucional permanece clasificado en **`NATIONAL_CATALOG_INCOMPLETE`** (`audit_status: "BLOCKED"`, `final_decision: "NO-GO"`), ya que la sincronización total (`NATIONAL_CATALOG_SYNCED`) exige la ingesta formal del dataset desagregado de sedes (`x5ay-984n`).

---

## 2. Semántica de la Fuente de la Verdad

| Dimensión | Dataset 1: Establecimientos (`cfw5-qzt5`) | Dataset 2: Sedes Físicas (`x5ay-984n`) |
|:---|:---|:---|
| **Nombre Oficial** | `MEN_ESTABLECIMIENTOS_EDUCATIVOS...` | `MEN_SEDES_EDUCATIVAS_PREESCOLAR_BÁSICA_Y_MEDIA` |
| **Nivel Jerárquico** | Nivel 1: Unidad Rectoral / Colegio | Nivel 2: Plantel Físico / Sede |
| **Cardinalidad** | 18.076 registros | 53.796 registros |
| **Clave Primaria** | `codigo_dane` (12 dígitos) | `codigo_dane_sede` (12 dígitos) |
| **Clave Foránea** | N/A (Entidad Raíz) | `codigo_dane` $\rightarrow$ Establecimiento |
| **Atributo de Sedes** | `cantidad_sedes` (Entero agregado) | `nombre_sede`, `principal` (`S`/`N`), coordenadas |

---

## 3. Identificadores Oficiales y Claves Primarias

- **Clave Primaria del Establecimiento:** `codigo_dane` (12 dígitos numéricos, e.g. `218150000578`).
- **Clave Primaria de la Sede Física:** `codigo_dane_sede` (12 dígitos numéricos, e.g. `218150001809`).
- **Tipo de Sede:** `principal` (`"S"` para la sede rectoral principal, `"N"` para sedes anexas/rurales).
- **Códigos Territoriales:** `cod_dane_departamento` (2 dígitos) y `cod_dane_municipio` (5 dígitos DIVIPOLA).

---

## 4. Especificación Técnica del Segundo Dataset Oficial (`x5ay-984n`)

- **Identificador del Recurso:** `x5ay-984n`
- **Punto de Enlace SODA:** `https://www.datos.gov.co/resource/x5ay-984n.json`
- **Entidad Publicadora:** Ministerio de Educación Nacional (MEN)
- **Fuentes Primarias:** SIMAT (Sistema Integrado de Matrícula) y DUE (Directorio Único de Establecimientos)
- **Campos Disponibles (23 columnas):**
  - `codigo_dane` (12 dígitos - Relación con Establecimiento)
  - `codigo_dane_sede` (12 dígitos - Clave única de la sede)
  - `nombre_establecimiento`
  - `nombre_sede`
  - `principal` (`S` / `N`)
  - `departamento`, `municipio`, `secretaria`
  - `cod_dane_municipio`
  - `zona` (`URBANA` / `RURAL`)
  - `direccion`, `telefono`, `email`
  - `coordenada_x_sede` (Longitud), `coordenada_y_sede` (Latitud)
  - `total_matricula`

---

## 5. Auditoría del Modelo de Datos Actual en PostgreSQL (`pevn_db`)

El esquema de base de datos de PEvN en `backend/app/models/official_catalog.py` **ya cuenta con la estructura relacional 1-a-Muchos correcta**:

```
OfficialInstitutionCatalog (1)
  id: UUID (PK)
  dane_code: VARCHAR(12) (UNIQUE)
  name: VARCHAR(255)
  department_code: VARCHAR(2)
  municipality_code: VARCHAR(5)
  ...
       |
       | 1-to-Many
       v
OfficialCampusCatalog (N)
  id: UUID (PK)
  official_institution_id: UUID (FK -> official_institution_catalog.id)
  dane_sede_code: VARCHAR(12) (UNIQUE)
  name: VARCHAR(255)
  is_main: BOOLEAN
  ...
```

**Evaluación del Esquema:**
- El modelo relacional en PostgreSQL está arquitectónicamente preparado para recibir tanto sedes principales (`is_main = true`) como anexas (`is_main = false`).
- La única razón por la que `official_campus_catalog` cuenta actualmente con 18.038 registros en lugar de ~54.000 es que solo se ha poblado con el dataset de nivel 1 (`cfw5-qzt5`).

---

## 6. Reconciliación de los 41 Registros Históricos de Línea Base

- **Origen:** 41 instituciones oficiales legítimas insertadas durante las Fases 3C-E y 3C-F como semilla de prueba nacional (`representative_national_baseline.json`), cubriendo 33 departamentos.
- **Clasificación:** **`VALID_HISTORICAL_BASELINE`**.
- **Impacto Contable:** Se integran limpiamente al universo total sin colisión de claves ($17.990 \text{ nuevas} + 41 \text{ preexistentes} = 18.031 \text{ instituciones en BD}$).

---

## 7. Reconciliación Forense de los 79 Duplicados en `cfw5-qzt5`

- **Hallazgo Forense:** Corresponden a 36 códigos DANE que aparecen duplicados en el volcado de datos abierto del MEN.
- **Causa Raíz Comprobada:** En establecimientos con múltiples sedes o jornadas (e.g. `205038000439` con `sedes=5` que aparece 5 veces en `cfw5-qzt5`), la vista SQL origen del MEN multiplicó las filas del establecimiento por cada sede sin incluir las columnas individuales de las sedes.
- **Tratamiento Canónico:** Al ingerir el dataset de nivel 1 (`cfw5-qzt5`), la deduplicación por `codigo_dane` es obligatoria para garantizar la unicidad de la entidad Establecimiento. La desagregación de sedes debe obtenerse del dataset de nivel 2 (`x5ay-984n`).

---

## 8. Fórmulas de Reconciliación Canónica

$$\begin{aligned}
\text{SOURCE\_ESTABLISHMENTS} &= 18.076 \\
\text{VALID\_SOURCE\_RECORDS} &= 17.990 \\
\text{DUPLICATE\_SOURCE\_RECORDS} &= 79 \\
\text{PREFIX\_REJECTED\_RECORDS} &= 7 \\
\mathbf{Balance\; Fuente:} &\quad 18.076 = 17.990 + 79 + 7 \\
\\
\text{HISTORICAL\_PREEXISTING\_RECORDS} &= 41 \\
\text{CURRENT\_PERSISTED\_ESTABLISHMENTS} &= 41 + 17.990 = \mathbf{18.031} \\
\\
\text{SOURCE\_DECLARED\_CAMPUSES} &= \mathbf{54.410} \\
\text{CURRENT\_PERSISTED\_CAMPUS\_ENTITIES} &= \mathbf{18.038} \\
\text{UNREPRESENTED\_CAMPUS\_CARDINALITY} &= 54.410 - 18.038 = \mathbf{36.372}
\end{aligned}$$

---

## 9. Evaluación de Compuertas de Calidad Forenses (Quality Gates H-M)

| Compuerta de Calidad | Criterio de Evaluación | Estado | Evidencia / Justificación Forense |
|:---|:---|:---:|:---|
| **GATE H — Entity Semantics** | Separación conceptual entre Establecimiento (EE) y Sede Física | **PASSED** | Modelo biestratificado validado en fuentes oficiales del MEN. |
| **GATE I — Campus Cardinality** | Reconciliación de las 54.410 sedes físicas | **BLOCKED** | 36.372 sedes anexas pendientes por ingesta de `x5ay-984n`. |
| **GATE J — Identifier Integrity** | Unicidad y formato de `codigo_dane` y `codigo_dane_sede` | **PASSED** | 12 dígitos auditados sin colisiones en PostgreSQL. |
| **GATE K — Historical Baseline** | Reconciliación de los 41 registros preexistentes | **PASSED** | 41 instituciones válidas clasificadas e integradas ($18.031$ total). |
| **GATE L — Source/Target Cardinality** | Ecuación contable balanceada ($18.076 = 17.990 + 79 + 7$) | **PASSED** | Balance $100\%$ exacto demostrado matemáticamente. |
| **GATE M — Canonical Model Integrity** | Identificación del dataset autoritativo de sedes | **PASSED** | Recurso `x5ay-984n` identificado y probado en `datos.gov.co`. |

---

## 10. Hoja de Ruta para la Próxima Fase (Fase 3C-N)

1. **Fase 3C-N (Ingesta Masiva Desagregada de Sedes):**
   - Diseñar el adaptador e ingesta por bloques (54 bloques de 1.000 registros) para el dataset oficial `x5ay-984n`.
   - Realizar el `JOIN` determinístico mediante `codigo_dane` contra `official_institution_catalog`.
   - Poblar `official_campus_catalog` con las ~53.796 sedes físicas (identificadas por `codigo_dane_sede`, con nombres reales, coordenadas y `is_main = (principal == 'S')`).
   - Elevar `PERSISTED_CAMPUS_ENTITIES` a ~53.796+.
   - Ejecutar la auditoría de promoción para alcanzar formalmente **`NATIONAL_CATALOG_SYNCED`**.

---

## 11. Veredicto Final Machine-Readable

```
SOURCE_RECORDS: 18076
VALID_SOURCE_RECORDS: 17990
DUPLICATE_SOURCE_RECORDS: 79
PREFIX_REJECTED_RECORDS: 7
HISTORICAL_PREEXISTING_RECORDS: 41
CURRENT_PERSISTED_ESTABLISHMENTS: 18031

SOURCE_DECLARED_CAMPUS_CARDINALITY: 54410
CURRENT_PERSISTED_CAMPUS_ENTITIES: 18038
UNREPRESENTED_CAMPUS_CARDINALITY: 36372

CURRENT_CATALOG_STATUS: NATIONAL_CATALOG_INCOMPLETE
CURRENT_AUDIT_STATUS: BLOCKED
CURRENT_FINAL_DECISION: NO-GO
CURRENT_PROMOTION_AUTHORIZED: FALSE

CANONICAL_ENTITY_MODEL: BIESTRATIFICADO (Establecimiento 1-a-Muchos Sedes)
CAMPUS_SEMANTICS: ENTIDAD_FISICA_CON_DANE_SEDE_12_DIGITOS
AUTHORITATIVE_CAMPUS_SOURCE: datos.gov.co/resource/x5ay-984n.json
NEXT_REQUIRED_PHASE: PHASE_3C_N_NATIONAL_PHYSICAL_SEDES_INGESTION_AND_PROMOTION

PROMOTION_BLOCKERS:
- INGESTA_PENDIENTE_DATASET_SEDES_X5AY_984N
- 36372_SEDES_ANEXAS_NO_PERSISTIDAS_COMO_FILAS

FINAL_DECISION: NO-GO
PROMOTION_AUTHORIZED: FALSE
```
