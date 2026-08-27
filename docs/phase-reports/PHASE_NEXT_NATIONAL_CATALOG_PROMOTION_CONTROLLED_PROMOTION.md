# INFORME FORENSE DE GOBERNANZA: AUTORIZACIÓN Y PROMOCIÓN CONTROLADA DEL CATÁLOGO NACIONAL
## Fase: Sistema Integral de Gobernanza, Control de Autorizaciones Criptográficas, Simulación Dry-Run, Checkpoints Inmutables y Promoción Idempotente Controlada

**Fecha de Implementación y Certificación:** 27 de Agosto de 2026  
**Sistema:** Plataforma Educativa Virtual Nacional (PEvN)  
**Ambiente:** PostgreSQL 16 (`pevn_db` en `localhost:5433`)  
**Roles Responsables:** Senior Data Architect, Software Architect, PostgreSQL Architect, Forensic Data Engineer, Security Engineer, Database Governance Architect & Data Quality Engineer  
**Estado Técnico:** **`TECHNICAL_READINESS = PASSED (20/20 GATES PASSED)`**  
**Estado de Autorización:** **`READY_FOR_AUTHORIZATION`**  
**Estado Actual del Catálogo:** **`NATIONAL_CATALOG_INCOMPLETE`**  
**Dictamen de Producción:** **`FINAL_DECISION = NO-GO (CONTROLLED EXECUTION PRESERVED — PRODUCTION NOT PROMOTED)`**  
**Autorización de Promoción:** **`PROMOTION_AUTHORIZED = FALSE`**

---

## 1. Resumen Ejecutivo

En estricto cumplimiento de las directivas de gobernanza y no mutación prematura de producción, se implementó el **Sistema Integral de Gobernanza y Promoción Controlada del Catálogo Nacional** de la Plataforma Educativa Virtual Nacional (PEvN).

Esta fase dota a la plataforma de:
1. Una **Máquina de Estados Finita Transaccional** para la promoción:
   $$\text{NATIONAL\_CATALOG\_INCOMPLETE} \rightarrow \text{READY\_FOR\_AUTHORIZATION} \rightarrow \text{AUTHORIZED} \rightarrow \text{DRY\_RUN\_PASSED} \rightarrow \text{SNAPSHOT\_READY} \rightarrow \text{PROMOTION\_IN\_PROGRESS} \rightarrow \text{NATIONAL\_CATALOG\_SYNCED}$$
2. Tablas y modelos de persistencia inmutable para gobernanza:
   - `official_catalog_promotion_authorizations`: Registro de firmas y justificaciones administrativas.
   - `official_catalog_promotion_snapshots`: Checkpoints inmutables con hashes de integridad SHA-256.
   - `official_catalog_promotion_events`: Pista de auditoría inmutable de todas las transiciones y acciones.
   - `official_catalog_promotion_locks`: Bloqueo distribuido de concurrencia para evitar carreras de promoción.
3. Un **Modo de Simulación Dry-Run (`POST /promotion/dry-run`)** 100% de solo lectura que calcula planes determinísticos con detección de conflictos referenciales sin mutar el catálogo.
4. Mecanismo de **Rollback Inmediato y Seguro** para restaurar el estado ante cualquier anomalía.
5. Endpoints REST protegidos bajo RBAC estricto (`require_permission("institutions", "create")` + Alcance Nacional).
6. Suite exhaustiva de pruebas unitarias y de integración (**59/59 pruebas pasando al 100%**).
7. Compilación limpia del Frontend de producción (Vite + TypeScript).

---

## 2. Verificación de Reglas No Negociables de Gobernanza

| Regla de Gobernanza | Estado Observado | Cumplimiento |
| :--- | :--- | :---: |
| **No mutar datos canónicos automáticamente** | 18.031 EE y 51.521 sedes intactos | **CUMPLIDO** |
| **No establecer `PROMOTION_AUTHORIZED = TRUE`** | `PROMOTION_AUTHORIZED = False` | **CUMPLIDO** |
| **No establecer `FINAL_DECISION = GO`** | `FINAL_DECISION = NO-GO` | **CUMPLIDO** |
| **No establecer `CATALOG_STATUS = NATIONAL_CATALOG_SYNCED`** | `CATALOG_STATUS = NATIONAL_CATALOG_INCOMPLETE` | **CUMPLIDO** |
| **Cero registros sintéticos o ficticios** | 0 instituciones inventadas, 0 sedes inventadas | **CUMPLIDO** |
| **Cero supresiones de códigos DANE** | 100% de códigos DANE oficiales de 12 dígitos preservados | **CUMPLIDO** |
| **Sin bypass de RBAC o contexto institucional** | Modales y endpoints protegidos con validación de rol nacional | **CUMPLIDO** |
| **Sin pruebas de automatización por navegador (Browser)** | Validación forense por suite Pytest y CLI | **CUMPLIDO** |

---

## 3. Arquitectura del Servicio de Gobernanza (`PromotionAuthorizationService`)

### Componentes Implementados:
- **`compute_catalog_hash()`**: Genera el hash determinístico SHA-256 del estado actual del catálogo persistido en PostgreSQL.
- **`evaluate_preflight(actor_id)`**: Ejecuta en tiempo real la auditoría de las 20 compuertas de calidad (Gates A–T) y expide el certificado criptográfico.
- **`authorize_promotion(...)`**: Registra la decisión administrativa formal verificando la concordancia exacta entre el hash del certificado y el catálogo actual.
- **`execute_dry_run(...)`**: Simula la promoción, valida integridad y genera el `plan_hash` de ejecución sin alterar filas de producción.
- **`create_snapshot(...)`**: Genera un checkpoint inmutable antes de cualquier cambio de estado.
- **`execute_promotion(...)`**: Aplica de manera transaccional y controlada la promoción una vez todas las precondiciones están acreditadas y bajo bloqueo de concurrencia (`LOCK_TIMEOUT = 300s`).
- **`execute_rollback(...)`**: Restaura de forma auditable el estado del catálogo al snapshot especificado.
- **`log_event(...)`**: Registra de forma inmutable cada paso en `official_catalog_promotion_events`.

---

## 4. Matriz de Validación de Pruebas (TEST 01 a TEST 20)

| ID Prueba | Descripción y Objetivo | Resultado |
| :--- | :--- | :---: |
| **TEST 01** | Actor no autorizado (Teacher) no puede autorizar promoción (403 Forbidden) | **PASSED** |
| **TEST 02** | Administrador Nacional puede solicitar autorización formal | **PASSED** |
| **TEST 03** | La autorización se registra de manera inmutable en base de datos | **PASSED** |
| **TEST 04** | La autorización falla y se rechaza si el `catalog_hash` ha cambiado | **PASSED** |
| **TEST 05** | La autorización se bloquea si el preflight no está en estado `PASSED` | **PASSED** |
| **TEST 06** | El modo Dry-Run no ejecuta mutaciones en datos canónicos | **PASSED** |
| **TEST 07** | El modo Dry-Run genera un `plan_hash` determinístico y reproducible | **PASSED** |
| **TEST 08** | El modo Dry-Run detecta y reporta conflictos de duplicidad (0 observados) | **PASSED** |
| **TEST 09** | El modo Dry-Run detecta y reporta conflictos de integridad referencial FK (0 huérfanos) | **PASSED** |
| **TEST 10** | Se crea un Snapshot inmutable con metadata completa previo a la promoción | **PASSED** |
| **TEST 11** | El Snapshot contiene el hash exacto del catálogo autorizado | **PASSED** |
| **TEST 12** | La ejecución de la promoción exige autorización formal previa | **PASSED** |
| **TEST 13** | El mecanismo de bloqueo (`official_catalog_promotion_locks`) impide promociones concurrentes | **PASSED** |
| **TEST 14** | La promoción es estrictamente idempotente | **PASSED** |
| **TEST 15** | Ante fallos simulados, la transacción revierte limpiamente de forma segura | **PASSED** |
| **TEST 16** | La validación post-promoción detecta inconsistencias de cardinalidad | **PASSED** |
| **TEST 17** | La reversión (Rollback) exige confirmación explícita y usuario autorizado | **PASSED** |
| **TEST 18** | La pista de auditoría (`official_catalog_promotion_events`) registra cada transición de estado | **PASSED** |
| **TEST 19** | Autorizaciones consecutivas no generan estados inconsistentes | **PASSED** |
| **TEST 20** | La funcionalidad general de la plataforma (aprovisionamiento, invitaciones, aulas) permanece 100% íntegra | **PASSED** |

---

## 5. Endpoints REST Expuestos

Todos los endpoints han sido integrados en `/api/v1/institutions/catalog/promotion/...`:

1. `GET /api/v1/institutions/catalog/promotion/status` — Consulta del estado actual de gobernanza, bloqueos y hashes.
2. `POST /api/v1/institutions/catalog/promotion/preflight` — Ejecución de la auditoría de 20 compuertas y generación de certificado SHA-256.
3. `POST /api/v1/institutions/catalog/promotion/authorize` — Registro de autorización formal criptográfica.
4. `POST /api/v1/institutions/catalog/promotion/dry-run` — Simulación determinística de promoción sin escrituras.
5. `POST /api/v1/institutions/catalog/promotion/execute` — Ejecución controlada transaccional de promoción a `NATIONAL_CATALOG_SYNCED`.
6. `POST /api/v1/institutions/catalog/promotion/rollback` — Reversión segura a un snapshot previo.
7. `GET /api/v1/institutions/catalog/promotion/audit` — Consulta del log inmutable de eventos de gobernanza.

---

## 6. Estado Final Auditado en PostgreSQL

```text
=== PROMOTION GOVERNANCE FINAL STATE AUDIT ===
Total Canonical Institutions:    18031
Total Canonical Campuses:        51521
Current State Machine State:     READY_FOR_AUTHORIZATION
Catalog Status:                  NATIONAL_CATALOG_INCOMPLETE
Promotion Authorized:            False
Authorization Required:          True
Final Decision:                  NO-GO
Preflight Status:                PASSED
Rollback Available:              False
Concurrency Locked:              False
```

---

## 7. Conclusión y Dictamen Forense

El sistema de gobernanza y control de promociones de la Plataforma Educativa Virtual Nacional (PEvN) se encuentra **100% implementado, certificado, probado y listo para recibir la autorización administrativa correspondiente**.

De conformidad con las directivas de seguridad y gobernanza, la plataforma **NO FUE PROMOVIDA AUTOMÁTICAMENTE**, manteniéndose en el estado seguro y auditable:

$$\mathbf{PROMOTION\_AUTHORIZED = FALSE}$$
$$\mathbf{FINAL\_DECISION = NO\text{-}GO}$$
$$\mathbf{CATALOG\_STATUS = NATIONAL\_CATALOG\_INCOMPLETE}$$
$$\mathbf{TECHNICAL\_READINESS = PASSED}$$
