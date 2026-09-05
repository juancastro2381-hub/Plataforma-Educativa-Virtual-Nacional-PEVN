"""
PEVN Backend - SIEE Evaluation, Report Card & Promotion Schemas (Phase 16C)

Pydantic v2 request/response contracts for:
  - Institutional SIEE Policy CRUD and versioning
  - Period-grade consolidation sheets (Sabana de Calificaciones)
  - Individual grade adjustments with mandatory audit reason
  - Remediation / recovery grade recording
  - Academic period closure and reopening
  - Periodic and year-end student report cards (Boletines)
  - Group consolidation matrices and ranking
  - Academic promotion previews and committed acts

All response schemas use ConfigDict(from_attributes=True) for ORM compatibility.
All request schemas use extra="forbid" to reject unknown fields.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluation import PerformanceLevelEnum, PromotionStatusEnum


# ===========================================================================
# 1. SIEE Policy Schemas
# ===========================================================================


class SieePolicyResponse(BaseModel):
    """Serialised representation of an institutional SIEE policy version."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    academic_year_id: uuid.UUID
    version: int
    name: str
    description: str | None = None
    min_passing_score: float
    max_score: float
    low_threshold_max: float
    basic_threshold_max: float
    high_threshold_max: float
    recovery_grade_cap: float
    max_failed_subjects_for_promotion: int
    max_failed_core_subjects: int
    min_attendance_percentage: float
    attendance_affects_promotion: bool
    rounding_decimals: int
    is_active: bool
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class SieePolicyCreateRequest(BaseModel):
    """
    Payload for creating a new versioned SIEE policy.
    All thresholds are validated by SieePolicyService.create_policy_version.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        default="Sistema Institucional de Evaluacion de los Estudiantes",
        max_length=150,
        description="Titulo oficial de la politica SIEE",
    )
    description: str | None = None
    min_passing_score: float = Field(default=3.00, gt=0, le=5.0)
    max_score: float = Field(default=5.00, gt=0)
    low_threshold_max: float = Field(default=2.99, ge=0)
    basic_threshold_max: float = Field(default=3.99, ge=0)
    high_threshold_max: float = Field(default=4.59, ge=0)
    recovery_grade_cap: float = Field(default=3.00, ge=0)
    max_failed_subjects_for_promotion: int = Field(default=2, ge=0)
    max_failed_core_subjects: int = Field(default=1, ge=0)
    min_attendance_percentage: float = Field(default=75.00, ge=0.0, le=100.0)
    attendance_affects_promotion: bool = True
    rounding_decimals: int = Field(default=1, ge=0, le=4)
    is_active: bool = True


class SieePolicyHistoryResponse(BaseModel):
    """List of all versioned SIEE policies for audit inspection."""

    items: list[SieePolicyResponse]
    total: int


# ===========================================================================
# 2. Evaluation Consolidation Sheet Schemas (Sabana de Calificaciones)
# ===========================================================================


class ActivitySummary(BaseModel):
    """Brief descriptor of an academic activity included in the period sheet."""

    id: uuid.UUID
    title: str
    weight_percentage: float
    max_score: float
    due_date: date | None = None


class AchievementSummary(BaseModel):
    """Competency descriptor / learning indicator associated with a performance level."""

    id: uuid.UUID
    code: str | None = None
    description: str
    performance_level: PerformanceLevelEnum


class RecoverySummary(BaseModel):
    """Read-only summary of a recovery / remediation grade record within a sheet."""

    id: uuid.UUID
    initial_score: float
    recovery_score: float
    applied_cap: float
    final_adjusted_score: float
    recovery_date: date
    act_number: str | None = None


class StudentGradeRow(BaseModel):
    """
    Per-student grade row in the period consolidation sheet.
    activity_grades maps activity_id (str) -> raw score or None (not submitted).
    """

    student_id: uuid.UUID
    enrollment_id: uuid.UUID
    simat_code: str | None = None
    first_name: str
    last_name: str
    document_number: str | None = None
    activity_grades: dict[str, float | None] = {}
    calculated_score: float
    final_score: float
    adjustment_reason: str | None = None
    performance_level: PerformanceLevelEnum
    total_absences: int = 0
    unexcused_absences: int = 0
    observations: str | None = None
    is_locked: bool = False
    recoveries: list[RecoverySummary] = []


class PeriodSheetResponse(BaseModel):
    """
    Complete consolidation sheet for a group x subject x period.
    Returned by GET /evaluations/period-sheet.
    """

    period: dict[str, Any]
    group: dict[str, Any]
    subject: dict[str, Any]
    policy: dict[str, Any]
    activities: list[ActivitySummary]
    achievements: list[AchievementSummary]
    students: list[StudentGradeRow]


class GradeItemRequest(BaseModel):
    """Single student grade entry in a batch save request."""

    model_config = ConfigDict(extra="forbid")

    student_id: uuid.UUID
    enrollment_id: uuid.UUID
    calculated_score: float = Field(ge=0.0)
    final_score: float = Field(ge=0.0)
    adjustment_reason: str | None = Field(
        default=None,
        description=(
            "Mandatory when final_score differs from calculated_score "
            "(DECISION-16-03 hybrid invariant)"
        ),
    )
    observations: str | None = None
    total_absences: int = Field(default=0, ge=0)
    unexcused_absences: int = Field(default=0, ge=0)


class AchievementItemRequest(BaseModel):
    """Competency descriptor to upsert alongside a grade batch."""

    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, max_length=20)
    description: str = Field(..., min_length=3, max_length=500)
    performance_level: PerformanceLevelEnum = PerformanceLevelEnum.BASICO


class SavePeriodGradesRequest(BaseModel):
    """Payload to save / update the consolidated period grades for a group x subject."""

    model_config = ConfigDict(extra="forbid")

    period_id: uuid.UUID
    group_id: uuid.UUID
    subject_id: uuid.UUID
    items: list[GradeItemRequest] = Field(..., min_length=1)
    achievements: list[AchievementItemRequest] | None = None


class SavePeriodGradesResponse(BaseModel):
    """Confirmation of successfully persisted period grades."""

    saved_count: int
    period_id: uuid.UUID
    group_id: uuid.UUID
    subject_id: uuid.UUID
    message: str = "Calificaciones consolidadas exitosamente."


# ===========================================================================
# 3. Recovery / Remediation Grade Schemas
# ===========================================================================


class RecordRecoveryGradeRequest(BaseModel):
    """Payload to register a remediation grade (nivelacion / recuperacion)."""

    model_config = ConfigDict(extra="forbid")

    recovery_score: float = Field(..., ge=0.0, description="Nota obtenida en la prueba de recuperacion")
    recovery_date: date = Field(..., description="Fecha de la prueba de recuperacion")
    act_number: str | None = Field(default=None, max_length=50)
    observations: str | None = Field(default=None, max_length=1000)


class RecoveryGradeResponse(BaseModel):
    """Response representation of a saved recovery grade record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period_subject_grade_id: uuid.UUID
    initial_score: float
    recovery_score: float
    applied_cap: float
    final_adjusted_score: float
    recovery_date: date
    act_number: str | None = None
    observations: str | None = None
    teacher_id: uuid.UUID | None = None
    created_at: datetime


# ===========================================================================
# 4. Period Closure / Unlock Schemas
# ===========================================================================


class ClosePeriodResponse(BaseModel):
    """Confirmation of period closure and grade sealing."""

    period_id: uuid.UUID
    is_closed: bool
    message: str = "Periodo academico cerrado y calificaciones selladas."


class UnlockPeriodRequest(BaseModel):
    """Payload for administrative period reopening (requires mandatory justification)."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        ...,
        min_length=10,
        description="Justificacion formal obligatoria para reabrir un periodo cerrado",
    )


class UnlockPeriodResponse(BaseModel):
    """Confirmation of period reopening."""

    period_id: uuid.UUID
    is_closed: bool
    message: str = "Periodo academico reabierto exitosamente."


# ===========================================================================
# 5. Report Card Schemas (Boletines de Calificaciones)
# ===========================================================================


class StudentReportCardResponse(BaseModel):
    """
    Complete periodic report card for a single student (Boletin de Calificaciones).
    """

    institution: dict[str, Any]
    campus: dict[str, Any]
    student: dict[str, Any]
    academic_year: dict[str, Any]
    period: dict[str, Any]
    group: dict[str, Any]
    summary: dict[str, Any]
    subjects: list[dict[str, Any]]


class GroupConsolidationMatrixResponse(BaseModel):
    """
    Group-level consolidation matrix (Sabana de Notas) including area averages
    and group ranking for an academic period.
    """

    group: dict[str, Any]
    period: dict[str, Any]
    subjects: list[dict[str, Any]]
    students: list[dict[str, Any]]
    total_students: int


class YearEndReportCardResponse(BaseModel):
    """
    Year-end cumulative report card for a student including all periods
    and their weighted final average.
    """

    institution: dict[str, Any]
    campus: dict[str, Any]
    student: dict[str, Any]
    academic_year: dict[str, Any]
    group: dict[str, Any]
    summary: dict[str, Any]
    promotion: dict[str, Any]
    subjects: list[dict[str, Any]]


# ===========================================================================
# 6. Academic Promotion Schemas (Comision de Evaluacion y Promocion)
# ===========================================================================


class PromotionDecisionItem(BaseModel):
    """Per-student promotion decision in a commit request."""

    model_config = ConfigDict(extra="forbid")

    student_id: uuid.UUID
    promotion_status: PromotionStatusEnum = Field(
        ...,
        description=(
            "PROMOVIDO | NO_PROMOVIDO | GRADUADO | PENDIENTE_NIVELACION. "
            "GRADUADO must only be used for students in the final grade (Grade 11). "
            "PROMOVIDO is not GRADUADO - see DECISION-16-04."
        ),
    )
    observations: str | None = Field(default=None, max_length=1000)
    decided_by_committee: bool = Field(
        default=False,
        description="True if the decision was made by an evaluation commission",
    )


class CommitGroupPromotionsRequest(BaseModel):
    """Payload for committing the official Promotion Act (Acta de Evaluacion y Promocion)."""

    model_config = ConfigDict(extra="forbid")

    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    acta_number: str = Field(..., min_length=1, max_length=50)
    decision_date: date
    observations: str | None = Field(default=None, max_length=2000)
    decisions: list[PromotionDecisionItem] = Field(..., min_length=1)


class PromotionCandidateRow(BaseModel):
    """Single student promotion preview row from calculate_promotion_preview."""

    student_id: uuid.UUID
    simat_code: str | None = None
    first_name: str
    last_name: str
    cumulative_average: float
    failed_subjects_count: int
    failed_core_subjects_count: int
    attendance_percentage: float
    proposed_status: PromotionStatusEnum
    decision_reason: str
    is_committed: bool = False
    committed_status: PromotionStatusEnum | None = None
    acta_number: str | None = None


class PromotionPreviewResponse(BaseModel):
    """Result of the promotion preview calculation for an entire group."""

    group: dict[str, Any]
    academic_year: dict[str, Any]
    siee_policy: dict[str, Any]
    total_candidates: int
    candidates: list[PromotionCandidateRow]


class StudentPromotionResponse(BaseModel):
    """Serialised committed StudentPromotion record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    student_id: uuid.UUID
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    promotion_status: PromotionStatusEnum
    acta_number: str | None = None
    decision_date: date | None = None
    observations: str | None = None
    decided_by_committee: bool = False
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class CommitGroupPromotionsResponse(BaseModel):
    """Confirmation of committed promotion acts."""

    committed_count: int
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    acta_number: str
    message: str = "Acta de evaluacion y promocion asentada exitosamente."
    records: list[StudentPromotionResponse] = []
