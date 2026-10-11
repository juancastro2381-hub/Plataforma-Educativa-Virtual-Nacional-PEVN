# PEVN — TERRITORIAL DATA INTEGRITY AUDIT
## POST-REMEDIATION FORENSIC CATALOG & TERRITORIAL ANALYSIS

**Document ID:** `PEVN_TERRITORIAL_DATA_INTEGRITY_AUDIT.md`  
**Execution Date:** 2026-10-05  
**Audit Mode:** Read-Only Forensic Data Integrity Analysis (Non-Destructive)  
**Target Scope:** Colombian Educational Territorial Hierarchy & Official MEN/DANE Catalog  
**Evaluated Jurisdictions:** National (33 DANE Departments), DANE 11 (Bogotá D.C.)  
**Audit Classification:** **DATA INTEGRITY: PASS WITH OBSERVATIONS**  

---

## 1. Executive Summary

Following the technical remediation and certification of `DEPARTMENT_ADMIN` territorial scoping ([PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_REMEDIATION_REPORT.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/reports/PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_REMEDIATION_REPORT.md)), this read-only forensic audit investigated two apparent catalog anomalies observed in the Territorial Analytics subsystem:

1. **Municipality DANE 11001 Dual Rendering:** The Territorial Analytics screen displayed two distinct breakdown rows for municipality code `11001` (`BOGOTA D.C.` with 2 establishments, and `BOGOTÁ, D.C.` with 1874 establishments), summing to 1876 establishments.
2. **Department Count Discrepancy (45 vs 33):** The pre-remediation audit noted 45 department records returned in national analytics, whereas the remediated service returned 33 departments.

### Key Forensic Findings
- **Relational Integrity is Uncompromised:** The relational operational database (`departments`, `municipalities`, `institutions`, `campuses`) is fully normalized with strict `UNIQUE` constraints and zero duplicate records. The `municipalities` table contains **exactly 1 record** for DANE 11001 (`id: 75495d0b-e2f0-4d1b-9114-02589135a863`).
- **Source of the Split Rows:** The duplication exists solely within the denormalized read-cache table `official_institution_catalog`, caused by the coexistence of an initial 41-record pilot ingestion batch (ASCII uppercase without accents) and a subsequent 18,076-record national open-data ingestion batch (accented standard text).
- **Explanation of 45 vs 33 Departments:** Official Colombian geography comprises 32 departments plus 1 Capital District (**33 territorial entities**). In `official_institution_catalog`, 12 department codes contain dual text representations (`ATLANTICO` vs `ATLÁNTICO`, `BOGOTA D.C.` vs `CAPITAL BOGOTÁ, D.C.`, etc.). Grouping SQL queries by raw string columns `(department_code, department_name)` produced $33 + 12 = 45$ rows. Grouping by canonical `department_code` correctly yields **33 departments**.
- **Establishment vs Site Arithmetic is 100% Exact:** The 1876 establishments (419 public, 1457 private) in Bogotá D.C. link to 2189 distinct educational sites (`official_campus_catalog`), each possessing a unique 12-digit DANE sede code across 1-to-N institutional campus hierarchies.
- **Security Invariance:** No security leakage, IDOR vulnerability, or cross-tenant boundary breach exists. All records displayed for code 11001 reside strictly within Department 11.

---

## 2. Audit 1 — Municipality 11001 Duplication Analysis

### 2.1 Relational Operational Schema (`municipalities`)
Direct forensic SQL inspection of the operational `municipalities` table:
```sql
SELECT m.id, m.code, m.name, m.department_id, d.code as dept_code, d.name as dept_name
FROM municipalities m
LEFT JOIN departments d ON m.department_id = d.id
WHERE m.code = '11001' OR d.code = '11';
```

**Result:**
| ID | Code | Name | Department ID | Dept Code | Dept Name |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `75495d0b-e2f0-4d1b-9114-02589135a863` | `11001` | `BOGOTÁ, D.C.` | `7b774116-56f1-4199-ac63-ff646e7e327b` | `11` | `CAPITAL BOGOTÁ, D.C.` |

- **Row Count:** Exactly **1 row**.
- **Constraint:** `municipalities.code` has a PostgreSQL unique constraint (`uq_municipalities_code` / `index=True, unique=True`).
- **Conclusion:** There is **no duplicate municipality record** in the operational database.

### 2.2 Analytical Catalog Schema (`official_institution_catalog`)
Direct inspection of `official_institution_catalog` where `department_code = '11'`:
```sql
SELECT department_code, department_name, municipality_code, municipality_name,
       count(*) as inst_count, count(distinct dane_code) as distinct_dane_codes
FROM official_institution_catalog
WHERE department_code = '11'
GROUP BY department_code, department_name, municipality_code, municipality_name;
```

**Result:**
| Department Code | Department Name | Municipality Code | Municipality Name | Count | Distinct DANE Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `11` | `BOGOTA D.C.` | `11001` | `BOGOTA D.C.` | 2 | 2 |
| `11` | `CAPITAL BOGOTÁ, D.C.` | `11001` | `BOGOTÁ, D.C.` | 1874 | 1874 |

### 2.3 Forensic Ingestion History & Provenance
Tracing the two records with `BOGOTA D.C.` back to `official_catalog_sync_batches`:
```sql
SELECT id, dane_code, name, department_name, municipality_name, sync_batch_id
FROM official_institution_catalog
WHERE department_code = '11' AND department_name = 'BOGOTA D.C.';
```

**Records:**
1. `f1651f9d-cfed-469a-8594-d5f872468ee3` | DANE: `111001012345` | `COLEGIO NACIONAL NICOLAS ESGUERRA (IED)` | Batch: `33b82da7-edd9-4a71-938a-7eafaffd50c2`
2. `51b8aff3-ef3a-4549-a251-9264121f8728` | DANE: `111001014567` | `COLEGIO MAYOR DE SAN BARTOLOME (IED)` | Batch: `33b82da7-edd9-4a71-938a-7eafaffd50c2`

**Batch Analysis:**
- Batch `33b82da7-edd9-4a71-938a-7eafaffd50c2` was executed on `2026-09-14 13:36:12 UTC` from dataset `datos.gov.co/c36d-tcj8` containing 41 pilot institutions. Notice the sequential test pattern in the synthetic DANE codes (`...12345` and `...14567`).
- Batch `a49910c2-fd62-45fa-9feb-32e82e9d063a` was executed from dataset `datos.gov.co/cfw5-qzt5` containing 18,076 national records from MinEducación (DUE/SIMAT). In this batch, `COLEGIO NACIONAL NICOLAS ESGUERRA` has official DANE code `111001010910`, and `FUNDACION COLEGIO MAYOR DE SAN BARTOLOME` has official DANE code `311001003084`.
- Because `official_institution_catalog.dane_code` is unique, the two pilot records did not collide on DANE code with the official dataset and remained coexisting in the table.

### 2.4 Aggregation Root Cause
In [backend/app/services/territorial_analytics_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/territorial_analytics_service.py#L472-L478), `get_municipality_distribution` groups by:
```python
stmt = select(...).group_by(
    OfficialInstitutionCatalog.municipality_code,
    OfficialInstitutionCatalog.municipality_name,
    OfficialInstitutionCatalog.department_code,
    OfficialInstitutionCatalog.department_name,
)
```
Because the group-by includes raw textual fields `municipality_name` and `department_name`, the slight variation between `'BOGOTA D.C.'` and `'BOGOTÁ, D.C.'` caused SQL to split the aggregate into two rows.

**Entity Classification:** **C) Legacy/import artifact in the analytical cache table.**

---

## 3. Audit 2 — Department Catalog Discrepancy (45 vs 33)

### 3.1 Relational Operational Schema (`departments`)
Query:
```sql
SELECT id, code, name FROM departments ORDER BY code;
```
**Result:** Exactly **3 provisioned pilot departments**:
- `caf3cc3f-a895-4fcd-b4b9-17405f3edf76` | `08` | `ATLÁNTICO`
- `7b774116-56f1-4199-ac63-ff646e7e327b` | `11` | `CAPITAL BOGOTÁ, D.C.`
- `9aea113f-54e2-4345-8cc6-46970a91c7c6` | `25` | `CUNDINAMARCA`

### 3.2 National Catalog Enumeration (`official_institution_catalog`)
In Colombian territorial law (Constitución Política de Colombia Art. 286, Codificación DANE DIVIPOLA), Colombia consists of **32 Departamentos + 1 Distrito Capital = 33 Entidades Territoriales de Nivel Departamental**.

When inspecting `official_institution_catalog` grouped by `(department_code, department_name)`:
```sql
SELECT department_code, department_name, count(*) as count
FROM official_institution_catalog
GROUP BY department_code, department_name
ORDER BY department_code, department_name;
```
**Total Groups Found:** Exactly **45 groups**.

### 3.3 The 12 Duplicate String Groups
Across the 33 DANE department codes, exactly 12 codes have dual entries resulting from the pilot batch vs national batch diacritic variations:

| DANE Code | Name Variation A (Pilot Batch `33b82da7`) | Institutions A | Name Variation B (National Batch `a49910c2`) | Institutions B | Total Institutions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **08** | `ATLANTICO` | 2 | `ATLÁNTICO` | 1,155 | 1,157 |
| **11** | `BOGOTA D.C.` | 2 | `CAPITAL BOGOTÁ, D.C.` | 1,874 | 1,876 |
| **13** | `BOLIVAR` | 2 | `BOLÍVAR` | 773 | 775 |
| **15** | `BOYACA` | 2 | `BOYACÁ` | 605 | 607 |
| **18** | `CAQUETA` | 1 | `CAQUETÁ` | 222 | 223 |
| **23** | `CORDOBA` | 1 | `CÓRDOBA` | 638 | 639 |
| **27** | `CHOCO` | 1 | `CHOCÓ` | 248 | 249 |
| **44** | `LA GUAJIRA` | 1 | `GUAJIRA` | 364 | 365 |
| **52** | `NARINO` | 1 | `NARIÑO` | 784 | 785 |
| **88** | `ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA` | 1 | `ARCHIPIÉLAGO DE SAN ANDRES,PROVIDENCIA Y SANTA CATALINA` | 20 | 21 |
| **94** | `GUAINIA` | 1 | `GUAINÍA` | 27 | 28 |
| **97** | `VAUPES` | 1 | `VAUPÉS` | 20 | 21 |

$$\text{Total Groups} = 33 \text{ canonical DANE codes} + 12 \text{ alternate name spellings} = 45 \text{ groups}$$

### 3.4 Reconciliation of the 45 vs 33 Discrepancy
- The prior audit (`PEVN_DEPARTMENT_ADMIN_TERRITORIAL_SCOPE_AUDIT.md`) observed `45 registros departamentales devueltos` because `get_department_distribution` grouped by `(department_code, department_name)`.
- The remediated query groups strictly by `OfficialInstitutionCatalog.department_code` using `func.max(department_name)`.
- Consequently, `NATIONAL_ADMIN` now receives exactly **33 departments**, matching the authoritative DANE geographic model of Colombia.

---

## 4. Audit 3 — Establishments vs Sites Aggregation Analysis

### 4.1 Department 11 Summary Breakdown
Forensic trace of all indicators returned for Bogotá D.C. (`department_code = '11'`):

```
Establecimientos Registrados: 1,876
├── Oficiales (Públicos):      419
└── No Oficiales (Privados): 1,457
    Total: 419 + 1457 = 1,876 (100% exact)
```

### 4.2 Sedes Educativas (2,189) Integrity Verification
Query executed against `official_campus_catalog`:
```sql
SELECT count(c.id) as total_campuses,
       count(distinct c.dane_sede_code) as distinct_dane_codes
FROM official_campus_catalog c
JOIN official_institution_catalog i ON c.official_institution_id = i.id
WHERE i.department_code = '11';
```

**Results:**
- **Total Sedes linked to Bogotá establishments:** **2,189**
- **Distinct DANE Sede Codes:** **2,189** (Zero duplicate sede codes).
- **Referential Integrity:** 100% of campuses link to a valid `official_institution_catalog.id` via foreign key `CASCADE`.

### 4.3 Campus Multiplicity Distribution
In Colombian educational architecture (MEN DUE), an educational establishment (institución) comprises a principal campus (sede principal) and optional secondary campuses (sedes anexas/adscritas).

| Campuses per Establishment | Establishment Count | Total Sites Generated |
| :---: | :---: | :---: |
| 1 campus | 1,681 | 1,681 |
| 2 campuses | 116 | 232 |
| 3 campuses | 58 | 174 |
| 4 campuses | 16 | 64 |
| 5 campuses | 3 | 15 |
| 9 campuses | 1 | 9 |
| 14 campuses | 1 | 14 |
| **Total** | **1,876 institutions** | **2,189 sedes** |

$$1681 + 232 + 174 + 64 + 15 + 9 + 14 = 2,189 \text{ sedes}$$

The arithmetic, joins, and relationship integrity are **100% exact and verified**.

### 4.4 Provisioned vs Catalog Entities
| Layer | Bogotá D.C. Count | Source Table | Nature |
| :--- | :--- | :--- | :--- |
| **Catalog Establishments** | 1,876 | `official_institution_catalog` | Cached reference registry (DANE/MEN) |
| **Catalog Sedes** | 2,189 | `official_campus_catalog` | Cached reference registry (DANE/MEN) |
| **Provisioned Tenants** | 32 (29 active) | `institutions` | Operational platform tenants |
| **Provisioned Campuses** | 16 | `campuses` | Operational platform campuses |
| **Provisioned Users** | 150 (149 active) | `users` | Operational platform accounts |

---

## 5. Audit 4 — PEVN Territorial Domain Model & DANE Semantics

| Level | Table Name | Primary Key | DANE Code | Parent FK Relationship | Uniqueness Rule | Active Status Field | Source of Truth |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Country** | *(Conceptual)* | ISO `"CO"` | `"CO"` | None | Unique Country Code | Always Active | ISO 3166-1 alpha-2 |
| **Department** | `departments` | UUID | `code` (2 digits) | None | `UNIQUE(code)` | Operational | DANE DIVIPOLA |
| **Municipality**| `municipalities`| UUID | `code` (5 digits) | `department_id -> departments.id` | `UNIQUE(code)` | Operational | DANE DIVIPOLA |
| **Institution** | `institutions` | UUID | `dane_code` (12 digits) | `municipality_id -> municipalities.id` | `UNIQUE(dane_code)` | `is_active: bool` | PEVN Tenant Provisioning |
| **Campus/Sede** | `campuses` | UUID | `dane_code` (12 digits) | `institution_id -> institutions.id` | Optional unique | `is_active: bool` | PEVN Tenant Provisioning |
| **Catalog Est.**| `official_institution_catalog`| UUID | `dane_code` (12 digits) | Denormalized `department_code`, `municipality_code` | `UNIQUE(dane_code)` | N/A | MEN DUE / SIMAT Open Data |
| **Catalog Sede**| `official_campus_catalog` | UUID | `dane_sede_code` (12 digits)| `official_institution_id -> official_institution_catalog.id` | `UNIQUE(dane_sede_code)` | `is_active: bool` | MEN DUE / SIMAT Open Data |

### Representation of DANE 11 / Bogotá D.C.
- **Department:** `id: 7b774116-56f1-4199-ac63-ff646e7e327b`, `code: "11"`, `name: "CAPITAL BOGOTÁ, D.C."`.
- **Municipality:** `id: 75495d0b-e2f0-4d1b-9114-02589135a863`, `department_id: 7b774116-...`, `code: "11001"`, `name: "BOGOTÁ, D.C."`.
- **Operational Assignment:** Persisted on `user_roles.department_id = '7b774116-56f1-4199-ac63-ff646e7e327b'`.

---

## 6. Audit 5 — Security & Regression Invariance Verification

Executed non-destructive verification against the runtime identity and authorization context:

```python
User: department_admin
  Roles: [SystemRole.DEPARTMENT_ADMIN]
  Perms count: 17 (Has *:* = False)
  Scope: is_national=False, is_dept=True, dept_id='7b774116-56f1-4199-ac63-ff646e7e327b'

User: national_admin
  Roles: [SystemRole.NATIONAL_ADMIN]
  Perms count: 30 (Has *:* = False)
  Scope: is_national=True, is_dept=False, dept_id=None

User: admin_nacional (SUPER_ADMIN)
  Roles: [SystemRole.SUPERADMIN]
  Perms count: 1 (Permission(resource='*', action='*') -> *:*)
  Scope: is_national=True, is_dept=False, dept_id=None
```

### Security Assessment
- **Zero Cross-Department Leakage:** Both rows displayed for code `11001` belong strictly to Department 11. No data from Cundinamarca, Antioquia, or any other department is accessible.
- **Anti-IDOR Unaltered:** Direct object requests to institutions or users outside Department 11 continue returning `403 Forbidden` (`PERMISSION_DENIED`).
- **RBAC Immutability:** 0 role definitions, 0 hierarchy levels, and 0 permissions were altered.

---

## 7. Forensic Conclusions & Summary of Observations

| Observation # | Domain | Root Cause | Impact | Severity |
| :---: | :--- | :--- | :--- | :---: |
| **OBS-01** | `get_municipality_distribution` SQL Query | Grouping includes raw string column `municipality_name` instead of grouping solely by `municipality_code`. | Splits 14 Colombian municipalities (including 11001) into dual rows in UI breakdown. | Low (Cosmetic / UI) |
| **OBS-02** | `official_institution_catalog` Data | 41 synthetic pilot records from batch `33b82da7` coexist with the 18,076 national records from batch `a49910c2`. | Introduces unaccented string variants for 12 departments and 14 municipalities in catalog cache. | Low (Data Hygiene) |
| **OBS-03** | `departments` & `municipalities` Relational Tables | Only 3 pilot departments and 3 municipalities are provisioned in the operational relational layer. | Operational tables are minimal seeds; full territorial tree exists in catalog cache. | Expected (Pilot State) |

---

## 8. Final Classification & Recommendation

```
================================================================================
FINAL CLASSIFICATION: DATA INTEGRITY: PASS WITH OBSERVATIONS
================================================================================
```

### Justification
1. **PASS:** All relational operational entities are strictly normalized, referentially intact, and mathematically consistent. The territorial authorization boundary for `DEPARTMENT_ADMIN` is fully verified and secure.
2. **WITH OBSERVATIONS:** The read-optimized catalog cache displays dual rows for municipality 11001 due to raw SQL string grouping across two historical ingestion batches.

### Recommended Next Actions (Future Maintenance Cycle — No Action in Current Phase)
1. **Normalize Analytical Grouping:** In `TerritorialAnalyticsService.get_municipality_distribution`, group by `OfficialInstitutionCatalog.municipality_code` and use `func.max(OfficialInstitutionCatalog.municipality_name)`, identical to the fix applied to `get_department_distribution`.
2. **Decommission Pilot Batch:** In a scheduled catalog re-sync, retire batch `33b82da7-edd9-4a71-938a-7eafaffd50c2` to purge the 41 legacy pilot records whose official counterparts already exist in national batch `a49910c2`.
3. **No Immediate Code or DB Changes:** In strict accordance with user constraints, no code, schema, migration, or database modifications were applied in this audit phase.
