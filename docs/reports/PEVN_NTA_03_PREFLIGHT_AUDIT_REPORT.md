# PEVN — NTA-03: PREFLIGHT AUDIT & RECONCILIATION REPORT
## CATALOG ↔ PROVISIONING ARCHITECTURE
**AI Software Factory Standard v1.2 — Mandatory Read-Only Pre-Flight Inspection**

- **Document Identifier:** `docs/reports/PEVN_NTA_03_PREFLIGHT_AUDIT_REPORT.md`
- **Execution Date:** 2026-10-06
- **Database Engine:** PostgreSQL 16 (`pevn_db`)
- **Inspection Mode:** STRICT READ-ONLY FORENSIC AUDIT (0 mutations executed)
- **Status:** **STOP CONDITION TRIGGERED — AMBIGUITY / ZERO-MATCH REPORTED**

---

## 1. PREFLIGHT METRICS SUMMARY

| Item | Requirement / Metric | Measured Value | Baseline Compliance |
| :--- | :--- | :---: | :---: |
| **A** | Number of PEVN institutions | **34** | Matches certified baseline (34) |
| **B** | Number active institutions | **31** | Matches certified baseline (31) |
| **C** | Number inactive institutions | **3** | Matches certified baseline (3) |
| **D** | Number of catalog institutions | **18,031** | Complete official universe |
| **E** | Number of duplicate catalog `dane_code` | **0** | 100% unique in catalog |
| **F** | PEVN institutions matching exactly 1 catalog record | **7** | Real establishments (DANE verified) |
| **G** | PEVN institutions matching 0 catalog records | **27** | Synthetic test fixtures |
| **H** | PEVN institutions matching multiple catalog records | **0** | Zero ambiguous collisions |
| **I** | Institutions already having `catalog_institution_id` | **0** (Column does not exist yet) | Ready for schema addition |
| **—** | Operational campuses | **18** | Matches baseline (18) |
| **—** | Operational users | **200** | Matches baseline (200) |
| **—** | Scoped Department Administrators | **10** | Matches baseline (10) |

---

## 2. DETAILED INSTITUTION MAPPING RECONCILIATION (ITEMS J & K)

### 2.1 The 7 Verified Official Establishments (Exact Match: 7 / 7)
These 7 institutions correspond to genuine Colombian educational institutions with valid 12-digit DANE codes present in `official_institution_catalog`:

| # | PEVN Institution Name | PEVN DANE Code | Dept / Muni | Status | Official Catalog UUID | Official Catalog Name | Match Type |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| 1 | `CENTRO DE EDUCACION BASICA # 201` | `108001000085` | 08 / 08001 | Active | `9fb8fe97-6e9b-4584-845b-436f736d62a0` | `CENTRO DE EDUCACION BASICA # 201` | **EXACT (1:1)** |
| 2 | `COLEGIO AQUILEO PARRA (IED)` | `111001000132` | 11 / 11001 | Active | `a7521367-5580-4d56-955d-5ced8e58d7c3` | `COLEGIO AQUILEO PARRA (IED)` | **EXACT (1:1)** |
| 3 | `COLEGIO FRIEDRICH NAUMANN (IED)` | `111001044806` | 11 / 11001 | Active | `096337ea-f7b7-4e77-97da-1f4f25398169` | `COLEGIO FRIEDRICH NAUMANN (IED)` | **EXACT (1:1)** |
| 4 | `COLEGIO LA AURORA (IED)` | `111001045705` | 11 / 11001 | Active | `0fd17257-3f04-4a92-a246-79f4488ce924` | `COLEGIO LA AURORA (IED)` | **EXACT (1:1)** |
| 5 | `COLEGIO GLENN DOMAN` | `311001000310` | 11 / 11001 | Active | `4fb507a2-aed7-4f58-bf4b-99f34a4bcd67` | `COLEGIO GLENN DOMAN` | **EXACT (1:1)** |
| 6 | `JARDIN INFANTIL CHARLY BROWN SAS` | `311001088985` | 11 / 11001 | Active | `e7fb13d0-3b95-4a71-9fc7-f41cf4a45365` | `JARDIN INFANTIL CHARLY BROWN SAS` | **EXACT (1:1)** |
| 7 | `COL CRISTIANO INTEGRAL` | `325286000823` | 25 / 25286 | Active | `67a3aafa-1cb6-4110-b37e-2561dbde07ab` | `COL CRISTIANO INTEGRAL` | **EXACT (1:1)** |

---

### 2.2 The 27 Synthetic Test Fixtures (Catalog Matches: 0 / 27)
These 27 institutions were created during automated testing and developmental iterations in August 2026. Their DANE codes are synthetic (e.g., `111111111111`, `222222222222`, hex hash suffixes like `11138cf8928`, or non-numeric strings like `DANE2cd062ca`). None of them exist in the official national catalog (`official_institution_catalog`):

| # | PEVN Institution Name | PEVN DANE Code | Dept / Muni | Status | Catalog Matches | Origin / Nature |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `Colegio San Pedro A` | `111111111111` | 11 / 11001 | Active | 0 | Automated test fixture |
| 2 | `Colegio Distrital Santander A` | `111337470814` | 11 / 11001 | Inactive | 0 | Automated test fixture |
| 3 | `Colegio Mayor A (38cf8928)` | `11138cf8928` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 4 | `Colegio Distrital Santander A` | `111509063615` | 11 / 11001 | Active | 0 | Automated test fixture |
| 5 | `Colegio Distrital Santander A` | `111789843642` | 11 / 11001 | Inactive | 0 | Automated test fixture |
| 6 | `Colegio Mayor A (8afed208)` | `1118afed208` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 7 | `Colegio Distrital Santander A` | `111947731611` | 11 / 11001 | Active | 0 | Automated test fixture |
| 8 | `Colegio Mayor A (c3aed126)` | `111c3aed126` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 9 | `Colegio Mayor A (d99fffaf)` | `111d99fffaf` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 10 | `Colegio Mayor A (e378175f)` | `111e378175f` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 11 | `Colegio Departamental B` | `222158975795` | 11 / 11001 | Inactive | 0 | Automated test fixture |
| 12 | `Colegio Santa Clara B` | `222222222222` | 11 / 11001 | Active | 0 | Automated test fixture |
| 13 | `Colegio Departamental B` | `222345167375` | 11 / 11001 | Active | 0 | Automated test fixture |
| 14 | `Colegio Departamental B` | `222380951826` | 11 / 11001 | Active | 0 | Automated test fixture |
| 15 | `Colegio Mayor B (38cf8928)` | `22238cf8928` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 16 | `Colegio Departamental B` | `222792214136` | 11 / 11001 | Active | 0 | Automated test fixture |
| 17 | `Colegio Mayor B (8afed208)` | `2228afed208` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 18 | `Colegio Mayor B (c3aed126)` | `222c3aed126` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 19 | `Colegio Mayor B (d99fffaf)` | `222d99fffaf` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 20 | `Colegio Mayor B (e378175f)` | `222e378175f` | 11 / 11001 | Active | 0 | Automated test fixture (hex DANE) |
| 21 | `Colegio Santa Clara B` | `279309112073` | 11 / 11001 | Active | 0 | Automated test fixture |
| 22 | `Colegio Santa Clara B` | `580646656080` | 11 / 11001 | Active | 0 | Automated test fixture |
| 23 | `Colegio San Pedro A` | `683702135761` | 11 / 11001 | Active | 0 | Automated test fixture |
| 24 | `Colegio San Pedro A` | `701741950906` | 11 / 11001 | Active | 0 | Automated test fixture |
| 25 | `Colegio Santa Clara B` | `722768576039` | 11 / 11001 | Active | 0 | Automated test fixture |
| 26 | `Colegio San Pedro A` | `954152364944` | 11 / 11001 | Active | 0 | Automated test fixture |
| 27 | `Colegio Test ec6ea5` | `DANE2cd062ca` | 11 / 11001 | Active | 0 | Automated test fixture |

---

## 3. ARCHITECTURAL GAP & CONFLICT ANALYSIS

1. **User Request Expectation (Section 5):**
   > *"Expected result: 34 / 34 existing PEVN institutions have exactly one valid catalog_institution_id. If any existing tenant cannot be mapped unambiguously: DO NOT GUESS. Stop the migration and report the exact institution and ambiguity."*
2. **Authoritative Blueprint Definition (`docs/reports/PEVN_NATIONAL_TERRITORIAL_ARCHITECTURE_BLUEPRINT.md`, line 681–682):**
   > *"Migration NTA-M3 (Backfill Existing Tenants):*
   > *`UPDATE institutions i SET catalog_institution_id = c.id FROM official_institution_catalog c WHERE i.dane_code = c.dane_code;`*
   > *For pilot test institutions with synthetic DANE codes not in catalog (e.g. `111111111111`), `catalog_institution_id` remains `NULL` safely."*
3. **Database Integrity Constraints:**
   - `catalog_institution_id` is a Foreign Key referencing `official_institution_catalog.id`.
   - Since these 27 records do not exist in the official catalog, assigning them an arbitrary or fake UUID would violate referential integrity (`fk_institutions_catalog_institution_id`).
   - Creating dummy catalog entries in `official_institution_catalog` is strictly prohibited by Section 6 (*"Do not modify catalog records. Catalog data remains untouched"*).
   - Guessing or using fuzzy name matching is strictly prohibited by Section 4 (*"Do NOT use institution name as identity. Do NOT use fuzzy matching"*).

---

## 4. STOP CONDITION & RESOLUTION OPTIONS

In strict compliance with:
- **Section 3:** *"STOP before mutation if the preflight reveals unexpected corruption, orphan records, duplicate structural codes, or a mismatch with the certified baseline."*
- **Section 5:** *"If any existing tenant cannot be mapped unambiguously: DO NOT GUESS. Stop the migration and report the exact institution and ambiguity."*

All database mutations have been held.
