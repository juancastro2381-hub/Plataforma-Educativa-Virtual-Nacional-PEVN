"""
PEVN Backend — SIEE Evaluation, Periodic Consolidation, Recoveries & Promotion Domain Models (Phase 16A)

National multi-tenant evaluation architecture complying with Decreto 1290 de 2009 and SIEE regulations:
- SieePolicy: Institution-scoped, versioned grading, recovery cap, and promotion policies.
- PeriodSubjectGrade: Hybrid period final grades with calculated score, teacher override, and reason.
- AcademicAchievement: Periodic competency descriptors and learning indicators.
- RecoveryGrade: Remedial evaluation history preserving original failing scores with applied cap.
- StudentPromotion: Year-end academic promotion judgments, commission acts, and graduation status.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.academic_assignment import AcademicAssignment
    from app.models.academic_year import AcademicPeriod, AcademicYear
    from app.models.enrollment import Enrollment
    from app.models.group import Group
    from app.models.institution import Institution
    from app.models.student import Student
    from app.models.subject import Subject
    from app.models.teacher import Teacher
    from app.models.user import User


# ===========================================================================
# Enumerations
# ===========================================================================

class PerformanceLevelEnum(enum.StrEnum):
    """
    Colombian National Academic Performance Bands (Decreto 1290 de 2009).
    """

    BAJO = "BAJO"        # Reprobatorio (e.g. 1.00 - 2.99)
    BASICO = "BASICO"    # Aprobatorio mínimo (e.g. 3.00 - 3.99)
    ALTO = "ALTO"        # Aprobatorio satisfactorio (e.g. 4.00 - 4.59)
    SUPERIOR = "SUPERIOR"  # Aprobatorio excelente (e.g. 4.60 - 5.00)


class PromotionStatusEnum(enum.StrEnum):
    """
    Year-End School Promotion Statuses (Decreto 1290 de 2009).

    SEMANTIC INVARIANT (DECISION-16-04) — Promotion ≠ Graduation:
      PROMOVIDO         : Student passed the academic year and advances to the NEXT grade.
                          Enrollment stays ACTIVE. NOT the same as graduating.
      GRADUADO          : Student completed the institutionally defined FINAL GRADE (Grade 11)
                          and satisfies all graduation requirements. ONLY this status triggers
                          EnrollmentStatus.GRADUATED on the current-year enrollment.
      NO_PROMOVIDO      : Student failed and must repeat the current grade. Enrollment stays ACTIVE.
      PENDIENTE_NIVELACION: Student has failing subjects requiring remediation commission review.
                          Enrollment stays ACTIVE.
    """

    PROMOVIDO = "PROMOVIDO"                      # Promovido al grado siguiente (Enrollment: ACTIVE)
    NO_PROMOVIDO = "NO_PROMOVIDO"                # No promovido, repite grado (Enrollment: ACTIVE)
    GRADUADO = "GRADUADO"                        # Graduado — solo grado final (Enrollment: GRADUATED)
    PENDIENTE_NIVELACION = "PENDIENTE_NIVELACION"  # Requiere nivelación final (Enrollment: ACTIVE)


# ===========================================================================
# 1. Institutional SIEE Policy Model
# ===========================================================================

class SieePolicy(Base):
    """
    Institutional SIEE Evaluation Policy (Sistema Institucional de Evaluación).

    Data-driven, institution-scoped configuration defining grading thresholds,
    recovery caps, and promotion criteria for a specific academic year.
    Never hardcoded in code; fully versioned and audited.
    """

    __tablename__ = "siee_policies"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "academic_year_id",
            "version",
            name="uq_siee_policies_inst_year_version",
        ),
        Index(
            "uq_siee_policies_one_active_per_year",
            "institution_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
        CheckConstraint(
            "min_passing_score > 0 AND max_score > min_passing_score",
            name="ck_siee_policies_score_bounds",
        ),
        CheckConstraint(
            "recovery_grade_cap >= min_passing_score AND recovery_grade_cap <= max_score",
            name="ck_siee_policies_recovery_cap",
        ),
        CheckConstraint(
            "min_attendance_percentage >= 0 AND min_attendance_percentage <= 100",
            name="ck_siee_policies_attendance_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Owning educational institution (Tenant boundary).",
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Academic school year to which this policy applies.",
    )
    version: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        doc="Monotonically increasing version counter per institution and year.",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Sistema Institucional de Evaluación de los Estudiantes",
        doc="Institutional policy title or resolution designation.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Legal or administrative context (Acuerdo del Consejo Directivo).",
    )
    min_passing_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("3.00"),
        doc="Minimum passing grade on numeric scale (default 3.00).",
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("5.00"),
        doc="Maximum scale ceiling (default 5.00).",
    )
    low_threshold_max: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("2.99"),
        doc="Upper bound for Desempeño Bajo (default 2.99).",
    )
    basic_threshold_max: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("3.99"),
        doc="Upper bound for Desempeño Básico (default 3.99).",
    )
    high_threshold_max: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("4.59"),
        doc="Upper bound for Desempeño Alto (default 4.59). Above this is Superior.",
    )
    recovery_grade_cap: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("3.00"),
        doc="Maximum official grade assignable to recovery examinations (DECISION-16-01).",
    )
    max_failed_subjects_for_promotion: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=2,
        doc="Number of failed subjects triggering retention or remediation (DECISION-16-02).",
    )
    max_failed_core_subjects: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        doc="Failed core/fundamental subjects threshold (e.g. Math & Language).",
    )
    min_attendance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("75.00"),
        doc="Minimum required attendance percentage (default 75%).",
    )
    attendance_affects_promotion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether unexcused attendance deficit triggers non-promotion.",
    )
    rounding_decimals: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        doc="Decimals precision for period averages (1 or 2).",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this version is currently authoritative for the academic year.",
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Administrator/Rector who defined this policy version.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    institution: Mapped[Institution] = relationship("Institution")
    academic_year: Mapped[AcademicYear] = relationship("AcademicYear")
    created_by: Mapped[User | None] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<SieePolicy id={self.id} institution_id={self.institution_id} "
            f"year_id={self.academic_year_id} v={self.version} active={self.is_active}>"
        )


# ===========================================================================
# 2. Period Subject Grade Model (Consolidated Periodic Grade)
# ===========================================================================

class PeriodSubjectGrade(Base):
    """
    Consolidated Subject Period Grade (Definitiva de Período por Asignatura).

    Hybrid model storing both calculated score from tasks/activities and the final
    teacher score with mandatory adjustment reason when overridden (DECISION-16-03).
    Sealed immutably upon period closure.
    """

    __tablename__ = "period_subject_grades"
    __table_args__ = (
        UniqueConstraint(
            "academic_period_id",
            "student_id",
            "subject_id",
            name="uq_period_subject_grades_period_student_subject",
        ),
        Index(
            "ix_period_subject_grades_inst_period_subject",
            "institution_id",
            "academic_period_id",
            "subject_id",
        ),
        Index(
            "ix_period_subject_grades_student_period",
            "student_id",
            "academic_period_id",
        ),
        CheckConstraint(
            "calculated_score >= 0 AND calculated_score <= 5.0",
            name="ck_period_grades_calc_bounds",
        ),
        CheckConstraint(
            "final_score >= 0 AND final_score <= 5.0",
            name="ck_period_grades_final_bounds",
        ),
        CheckConstraint(
            "total_absences >= 0 AND unexcused_absences >= 0 AND unexcused_absences <= total_absences",
            name="ck_period_grades_absences",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Tenant boundary.",
    )
    academic_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Evaluation term period.",
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Student active enrollment linkage.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Evaluated student.",
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Evaluated subject.",
    )
    academic_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_assignments.id", ondelete="SET NULL"),
        nullable=True,
        doc="Teacher workload assignment.",
    )
    calculated_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Deterministic arithmetic average computed from activity evaluations.",
    )
    final_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Authoritative final score approved by teacher (subject to SIEE scale).",
    )
    adjustment_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Mandatory justification when final_score differs from calculated_score.",
    )
    performance_level: Mapped[PerformanceLevelEnum] = mapped_column(
        SQLEnum(
            PerformanceLevelEnum,
            name="performance_level_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PerformanceLevelEnum.BASICO,
        doc="National qualitative band (BAJO, BASICO, ALTO, SUPERIOR).",
    )
    total_absences: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        doc="Total class absences recorded in this period.",
    )
    unexcused_absences: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        doc="Unexcused class absences recorded in this period.",
    )
    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Pedagogical notes or recommendations for the report card.",
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this grade record is locked due to period closure.",
    )
    graded_by_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        doc="Teacher who validated and consolidated this grade.",
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    institution: Mapped[Institution] = relationship("Institution")
    academic_period: Mapped[AcademicPeriod] = relationship("AcademicPeriod")
    enrollment: Mapped[Enrollment] = relationship("Enrollment")
    student: Mapped[Student] = relationship("Student")
    subject: Mapped[Subject] = relationship("Subject")
    academic_assignment: Mapped[AcademicAssignment | None] = relationship("AcademicAssignment")
    graded_by: Mapped[Teacher | None] = relationship("Teacher")
    recovery_records: Mapped[list[RecoveryGrade]] = relationship(
        "RecoveryGrade",
        back_populates="period_grade",
        cascade="all, delete-orphan",
        order_by="RecoveryGrade.created_at.desc()",
    )

    def __repr__(self) -> str:
        return (
            f"<PeriodSubjectGrade id={self.id} student_id={self.student_id} "
            f"subject_id={self.subject_id} final={self.final_score} ({self.performance_level})>"
        )


# ===========================================================================
# 3. Academic Achievement Model (Logros y Descriptores)
# ===========================================================================

class AcademicAchievement(Base):
    """
    Academic Achievement Descriptor (Logro o Indicador de Desempeño).

    Pedagogical indicators linked to a subject, period, and teacher assignment,
    printed in official report cards according to attained performance level.
    """

    __tablename__ = "academic_achievements"
    __table_args__ = (
        Index(
            "ix_academic_achievements_assignment_period",
            "academic_assignment_id",
            "academic_period_id",
        ),
        Index(
            "ix_academic_achievements_tenant",
            "institution_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Tenant boundary.",
    )
    academic_assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Subject and group workload assignment.",
    )
    academic_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Academic period term.",
    )
    code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Optional curriculum code (e.g. 'DBA-MAT-01').",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Pedagogical descriptor text.",
    )
    performance_level: Mapped[PerformanceLevelEnum] = mapped_column(
        SQLEnum(
            PerformanceLevelEnum,
            name="performance_level_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PerformanceLevelEnum.BASICO,
        doc="Associated performance level target.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    institution: Mapped[Institution] = relationship("Institution")
    academic_assignment: Mapped[AcademicAssignment] = relationship("AcademicAssignment")
    academic_period: Mapped[AcademicPeriod] = relationship("AcademicPeriod")

    def __repr__(self) -> str:
        return (
            f"<AcademicAchievement id={self.id} level={self.performance_level} "
            f"desc={self.description[:30]!r}>"
        )


# ===========================================================================
# 4. Recovery Grade Model (Nivelaciones / Planes de Mejoramiento)
# ===========================================================================

class RecoveryGrade(Base):
    """
    Remedial / Recovery Grade Entry (Nivelación o Plan de Mejoramiento).

    Preserves full auditability of initial failed grade, recovery test score,
    and resulting capped official grade (DECISION-16-01).
    """

    __tablename__ = "recovery_grades"
    __table_args__ = (
        CheckConstraint(
            "initial_score >= 0 AND initial_score <= 5.0",
            name="ck_recovery_initial_bounds",
        ),
        CheckConstraint(
            "recovery_score >= 0 AND recovery_score <= 5.0",
            name="ck_recovery_score_bounds",
        ),
        CheckConstraint(
            "final_adjusted_score >= 0 AND final_adjusted_score <= 5.0",
            name="ck_recovery_adjusted_bounds",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    period_subject_grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("period_subject_grades.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent consolidated period grade.",
    )
    initial_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Original failing score before recovery (preserved inmutable).",
    )
    recovery_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Actual score attained on the recovery evaluation.",
    )
    applied_cap: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("3.00"),
        doc="Institutional recovery cap applied from SieePolicy (e.g. 3.00).",
    )
    final_adjusted_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Final official grade resulting from min(recovery_score, applied_cap).",
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Evaluating teacher who registered the recovery.",
    )
    act_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Official recovery act or resolution number.",
    )
    recovery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date when recovery assessment was administered.",
    )
    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Pedagogical comments regarding the recovery process.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    period_grade: Mapped[PeriodSubjectGrade] = relationship(
        "PeriodSubjectGrade",
        back_populates="recovery_records",
    )
    teacher: Mapped[Teacher] = relationship("Teacher")

    def __repr__(self) -> str:
        return (
            f"<RecoveryGrade id={self.id} initial={self.initial_score} "
            f"recovery={self.recovery_score} adjusted={self.final_adjusted_score}>"
        )


# ===========================================================================
# 5. Student Promotion Model (Promoción de Fin de Año y Actas)
# ===========================================================================

class StudentPromotion(Base):
    """
    Year-End Academic Promotion Record (Dictamen de Promoción Escolar y Actas).

    Official decision determining whether a student is promoted, retained, or graduated
    based on institutional SIEE policy criteria (DECISION-16-02).
    """

    __tablename__ = "student_promotions"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "student_id",
            name="uq_student_promotions_year_student",
        ),
        Index(
            "ix_student_promotions_inst_year_group",
            "institution_id",
            "academic_year_id",
            "group_id",
        ),
        CheckConstraint(
            "cumulative_average >= 0 AND cumulative_average <= 5.0",
            name="ck_promotions_avg_bounds",
        ),
        CheckConstraint(
            "failed_subjects_count >= 0 AND failed_core_subjects_count >= 0",
            name="ck_promotions_failed_bounds",
        ),
        CheckConstraint(
            "attendance_percentage >= 0 AND attendance_percentage <= 100",
            name="ck_promotions_att_bounds",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Tenant boundary.",
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Academic school year being closed.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Evaluated student.",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Student's enrolled class group.",
    )
    cumulative_average: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        doc="Annual cumulative grade average across all periods.",
    )
    failed_subjects_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        doc="Total number of failed subjects in the school year.",
    )
    failed_core_subjects_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        doc="Total number of failed core/fundamental subjects in the school year.",
    )
    attendance_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00"),
        doc="Cumulative annual attendance percentage.",
    )
    promotion_status: Mapped[PromotionStatusEnum] = mapped_column(
        SQLEnum(
            PromotionStatusEnum,
            name="promotion_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        doc="Final promotion judgment (PROMOVIDO, NO_PROMOVIDO, GRADUADO, PENDIENTE_NIVELACION).",
    )
    acta_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Official commission promotion act number (e.g. 'ACTA-2026-042').",
    )
    decision_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Official promotion commission decision date.",
    )
    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Academic commission notes or graduation remarks.",
    )
    closed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Rector/Coordinator who ratified the promotion act.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    institution: Mapped[Institution] = relationship("Institution")
    academic_year: Mapped[AcademicYear] = relationship("AcademicYear")
    student: Mapped[Student] = relationship("Student")
    group: Mapped[Group] = relationship("Group")
    closed_by: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        return (
            f"<StudentPromotion id={self.id} student_id={self.student_id} "
            f"year_id={self.academic_year_id} status={self.promotion_status} avg={self.cumulative_average}>"
        )
