# PEVN Phase 16B — Domain Services & Business Logic Report

## Executive Summary

Phase 16B of the **Plataforma Educativa Virtual Nacional (PEVN)** has successfully implemented and hardened the authoritative domain service layer for institutional evaluations, grading consolidations, report cards, and year-end academic promotions, fully aligned with Colombian regulatory frameworks (**Decree 1290 of 2009**, Law 115 of 1994) and the permanent **National Multi-Tenant Architecture** of PEVN.

All institutional evaluation rules, grading scales, performance thresholds, remediation grade caps, attendance requirements, and promotion criteria are fully data-driven, configurable per institution and academic school year, and never hardcoded in application logic.

---

## Phase 16B Core Domain Services Implemented

### 1. `SieePolicyService` (`backend/app/services/siee_policy_service.py`)
- **Purpose**: Authoritative manager of institutional *Sistema Institucional de Evaluación de los Estudiantes* (SIEE) policies.
- **Key Responsibilities**:
  - `get_active_policy(institution_id, academic_year_id)`: Fetches the single active SIEE policy governing an institution and school year.
  - `get_or_create_default_policy(institution_id, academic_year_id, user_id)`: Bootstraps or returns the default national standard baseline policy if unconfigured.
  - `create_policy_version(institution_id, academic_year_id, data, user_id)`: Transactionally publishes a new immutable policy version, archiving previous versions and updating the single-active-policy invariant (`uq_siee_policies_one_active_per_year`).
  - `list_policy_history(institution_id, academic_year_id)`: Auditable historical trace of institutional SIEE configurations.
  - `map_score_to_performance_level(score, policy)`: Pure, deterministic mapping of numeric grades to national performance levels:
    - `BAJO` ($0.00 \le \text{score} \le \text{low\_threshold\_max}$)
    - `BASICO` ($\text{low\_threshold\_max} < \text{score} \le \text{basic\_threshold\_max}$)
    - `ALTO` ($\text{basic\_threshold\_max} < \text{score} \le \text{high\_threshold\_max}$)
    - `SUPERIOR` ($\text{high\_threshold\_max} < \text{score} \le \text{max\_score}$)

### 2. `EvaluationService` (`backend/app/services/evaluation_service.py`)
- **Purpose**: Period evaluation consolidation, teacher grading sheets, remedial grading, and period closure/reopening lifecycles.
- **Key Invariants & Decisions Enforced**:
  - **DECISION-16-03 (Hybrid Evaluation Consolidation)**: Deterministically calculates `calculated_score` from evaluated activities weighted by `weight_percentage`. Allows teacher adjustments to `final_score`, but strictly requires a non-empty `adjustment_reason` whenever `round(final_score, 2) != round(calculated_score, 2)`.
  - **DECISION-16-01 (Recovery / Remediation Grade Cap)**: When recording a recovery grade via `record_recovery_grade()`, the initial failing score remains immutable. The official adjusted recovery grade is capped dynamically via `min(recovery_score, policy.recovery_grade_cap)` and persisted into `recovery_grades`.
  - **Period Lock & Immutability**:
    - `close_period(institution_id, period_id, user_id)`: Sets `AcademicPeriod.is_closed = True`, batch-locks all `PeriodSubjectGrade.is_locked = True`, and registers an immutable `PERIOD_CLOSED` audit log.
    - Block on mutations: Any attempt to save grades in a closed period raises `PeriodClosedLockedError`.
    - `unlock_period(institution_id, period_id, user_id, reason)`: Requires administrative justification, unlocks grades, and emits `PERIOD_UNLOCKED` audit event.
  - **Teacher Scope Enforcement**: Confirms that non-directive users possess an active `AcademicAssignment` for the target `(group_id, subject_id, academic_year_id)`.

### 3. `ReportCardService` (`backend/app/services/report_card_service.py`)
- **Purpose**: Authoritative generation of periodic report cards (*Boletines Periódicos*), final annual report cards (*Boletín Final Acumulativo*), and group consolidation matrices (*Sábanas de Notas*).
- **Key Features**:
  - `get_student_report_card(institution_id, student_id, period_id, actor_user_id)`: Assembles comprehensive period bulletin including area groupings, teacher names, absences, qualitative achievement descriptors, recovery notes, and group ranking (*Puesto en el Grupo*).
  - `get_student_final_report_card(institution_id, student_id, academic_year_id, actor_user_id)`: Computes period-weighted cumulative final grades per subject, cumulative overall GPA, and promotion record.
  - `get_group_consolidation_matrix(institution_id, group_id, period_id)`: Multi-subject matrix used during evaluation commissions.
  - **Security & Anti-IDOR**: Guarantees tenant isolation and enrollment boundary checks.

### 4. `AcademicPromotionService` (`backend/app/services/academic_promotion_service.py`)
- **Purpose**: Evaluation commission decision support and official year-end promotion acts (*Actas de Evaluación y Promoción*).
- **Key Invariants & Decisions Enforced**:
  - **DECISION-16-02 (Dynamic SIEE Promotion Criteria)**: Evaluates student promotion status based on active institutional policy:
    1. Inattendance threshold: $\text{attendance\_percentage} < \text{policy.min\_attendance\_percentage} \implies \text{NO\_PROMOVIDO}$ (if $\text{attendance\_affects\_promotion}$ is enabled).
    2. Fundamental core area failures: $\text{failed\_core\_subjects} > \text{policy.max\_failed\_core\_subjects} \implies \text{NO\_PROMOVIDO}$.
    3. Total subject failures: $\text{failed\_subjects} > \text{policy.max\_failed\_subjects\_for\_promotion} \implies \text{NO\_PROMOVIDO}$.
    4. Pending remedial: $\text{failed\_subjects} > 0 \implies \text{PENDIENTE\_NIVELACION}$.
    5. Normal passing: If Grade 11 / Media $\implies \text{GRADUADO}$; otherwise $\implies \text{PROMOVIDO}$.
  - `calculate_promotion_preview(institution_id, group_id, academic_year_id)`: Read-only simulation for Institutional Evaluation Commissions.
  - `commit_group_promotions(...)`: Transactionally writes `StudentPromotion` rows, assigns official `acta_number`, transitions student `Enrollment.status` to `EnrollmentStatus.GRADUATED` upon promotion, and emits `PROMOTION_COMMITTED` audit log.

---

## Test Verification Summary

### 1. Phase 16B Domain Services Test Suite
```bash
pytest tests/test_siee_and_evaluations_domain_services.py -v
```
**Results:** `6 passed in 4.95s (100%)`

| Test Name | Scenario Verified | Status |
|---|---|:---:|
| `test_siee_policy_service_lifecycle_and_mapping` | Policy bootstrap, version publication, partial unique active index, Decree 1290 performance mapping | **PASSED** |
| `test_evaluation_service_hybrid_grading_and_adjustment_reason` | SIEE scale bounds, calculated vs adjusted score, mandatory adjustment reason, teacher scope | **PASSED** |
| `test_recovery_grade_capping_and_history` | Remedial grade recording, policy recovery cap enforcement, immutable initial grade preservation | **PASSED** |
| `test_period_closure_and_unlock_lifecycle` | Official period closure, grade locking, mutation rejection on closed period, authorized unlocking | **PASSED** |
| `test_report_card_service_generation` | Periodic and final report card generation, group ranking, area grouping, achievement descriptors | **PASSED** |
| `test_academic_promotion_service_preview_and_commit` | SIEE evaluation commission simulation, promotion criteria evaluation, official act commitment | **PASSED** |

### 2. Multi-Portal Regression Test Suite (Phases 1–15)
```bash
pytest tests/test_teacher_portal_api.py tests/test_student_portal_api.py tests/test_guardian_portal_api.py tests/test_institutional_communications_api.py tests/test_coexistence_incidents_api.py tests/test_institutional_news_api.py -v
```
**Results:** `33 passed in 61.35s (100% — Zero Regressions)`

---

## Verification of Regulatory and Architectural Rules

1. **National Multi-Tenant Platform**: No hardcoded school, municipal, or departmental rules. SIEE policies are tenant-scoped and year-scoped data entities.
2. **Decree 1290 Performance Levels**: Seamless mapping to `BAJO`, `BASICO`, `ALTO`, and `SUPERIOR` using configured score thresholds.
3. **Audit Trails**: Every administrative and grading state transition produces structured `AuditEvent` logs stored append-only in `audit_logs`.
4. **Boundary Isolation**: Strict tenant verification prevents cross-tenant access across all services.
