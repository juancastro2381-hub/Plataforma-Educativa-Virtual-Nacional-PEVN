"""
PEVN Backend — Academic Activities, Grades, Attendance & Planning Domain Models

Authoritative domain models supporting the dedicated Teacher Portal:
- AcademicActivity: Teacher tasks, workshops, quizzes, exams, and projects.
- ActivityGrade: Student submissions, scoring, and pedagogical feedback.
- DailyAttendance: Classroom attendance records (Present, Absent, Excused, Late).
- AcademicPlan: Curricular lesson units, competencies, objectives, and evaluation criteria.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
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
    from app.models.academic_year import AcademicYear
    from app.models.group import Group
    from app.models.institution import Institution
    from app.models.student import Student
    from app.models.subject import Subject
    from app.models.teacher import Teacher


# ===========================================================================
# Enumerations
# ===========================================================================

class ActivityType(enum.StrEnum):
    """Pedagogical activity classifications."""
    TASK = "TASK"
    WORKSHOP = "WORKSHOP"
    QUIZ = "QUIZ"
    EXAM = "EXAM"
    PROJECT = "PROJECT"
    CLASS_ACTIVITY = "CLASS_ACTIVITY"


class ActivityResourceType(enum.StrEnum):
    """Types of materials / resources attached to an academic activity."""
    URL = "URL"
    FILE = "FILE"


class ActivityDeliveryType(enum.StrEnum):
    """Activity submission modality constraints."""
    TEXT = "TEXT"
    FILE = "FILE"
    TEXT_AND_FILE = "TEXT_AND_FILE"


class ActivityStatus(enum.StrEnum):
    """Lifecycle statuses for academic activities."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class SubmissionStatus(enum.StrEnum):
    """Lifecycle statuses for student submissions."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"
    RETURNED = "RETURNED"
    GRADED = "GRADED"


class ActivitySubmissionStatus(enum.StrEnum):
    """Evaluation / submission statuses for student grades."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"


class AttendanceStatusEnum(enum.StrEnum):
    """Daily student attendance marks."""
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"
    LATE = "LATE"


class AcademicPlanStatus(enum.StrEnum):
    """Curricular lesson plan lifecycle."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


# ===========================================================================
# 1. Academic Activity Model
# ===========================================================================

class AcademicActivity(Base):
    """
    Academic Activity Entity (Actividad / Tarea / Evaluación).

    Created by an educator for an assigned subject, group section, and academic year.
    """

    __tablename__ = "academic_activities"
    __table_args__ = (
        Index(
            "ix_academic_activities_tenant_teacher",
            "institution_id",
            "teacher_id",
        ),
        Index(
            "ix_academic_activities_group_subject",
            "group_id",
            "subject_id",
            "academic_year_id",
        ),
        CheckConstraint(
            "max_score > 0",
            name="ck_academic_activities_max_score_positive",
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
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Author educator.",
    )
    academic_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated academic workload assignment (optional linkage).",
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Subject of the activity.",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Target group section.",
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Academic school year.",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Activity title.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed summary or pedagogical context.",
    )
    activity_type: Mapped[ActivityType] = mapped_column(
        SQLEnum(
            ActivityType,
            name="activity_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ActivityType.TASK,
        doc="Activity pedagogical classification.",
    )
    status: Mapped[ActivityStatus] = mapped_column(
        SQLEnum(
            ActivityStatus,
            name="activity_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ActivityStatus.DRAFT,
        doc="Publication lifecycle state.",
    )
    publication_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when activity was published.",
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Deadline for student submission.",
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        nullable=False,
        default=Decimal("5.00"),
        doc="Maximum attainable grade (Colombian scale default 5.0).",
    )
    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Step-by-step instructions for students.",
    )
    resource_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Reference link or educational material URL (legacy field, preserved for backward compatibility).",
    )
    delivery_type: Mapped[ActivityDeliveryType] = mapped_column(
        SQLEnum(
            ActivityDeliveryType,
            name="activity_delivery_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ActivityDeliveryType.FILE,
        server_default="FILE",
        doc="Required modality for student submissions (TEXT, FILE, TEXT_AND_FILE).",
    )
    # Relationships
    teacher: Mapped[Teacher] = relationship("Teacher")
    subject: Mapped[Subject] = relationship("Subject")
    group: Mapped[Group] = relationship("Group")
    academic_year: Mapped[AcademicYear] = relationship("AcademicYear")
    grades: Mapped[list[ActivityGrade]] = relationship(
        "ActivityGrade",
        back_populates="activity",
        cascade="all, delete-orphan",
    )
    resources: Mapped[list[ActivityResource]] = relationship(
        "ActivityResource",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="ActivityResource.created_at",
    )
    submissions: Mapped[list[StudentSubmission]] = relationship(
        "StudentSubmission",
        back_populates="activity",
        cascade="all, delete-orphan",
        order_by="StudentSubmission.attempt_number",
    )


# ===========================================================================
# 2. Activity Pedagogical Resource Model (Phase B3-H11)
# ===========================================================================

class ActivityResource(Base):
    """
    Activity Pedagogical Resource / Attachment Entity (Material Pedagógico de Actividad).

    Represents support materials provided by the teacher for an academic activity.
    Can be an external URL or an uploaded secure file.
    """

    __tablename__ = "activity_resources"
    __table_args__ = (
        CheckConstraint(
            "(resource_type = 'URL' AND url IS NOT NULL) OR "
            "(resource_type = 'FILE' AND file_path IS NOT NULL AND original_filename IS NOT NULL)",
            name="ck_activity_resources_type_fields",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Tenant boundary for isolation.",
    )
    resource_type: Mapped[ActivityResourceType] = mapped_column(
        SQLEnum(
            ActivityResourceType,
            name="activity_resource_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ActivityResourceType.URL,
        doc="Type of resource: external URL or uploaded FILE.",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Display title of the resource.",
    )
    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="External web link when resource_type is URL.",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Opaque relative storage path when resource_type is FILE.",
    )
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User-facing original name of the uploaded file.",
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        doc="File size in bytes.",
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="MIME type of the uploaded file.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    activity: Mapped[AcademicActivity] = relationship(
        "AcademicActivity",
        back_populates="resources",
    )
    institution: Mapped[Institution] = relationship("Institution")


# ===========================================================================
# 3. Activity Grade / Evaluation Model
# ===========================================================================

class ActivityGrade(Base):
    """
    Student Activity Grade & Feedback (Calificación de Actividad).

    Represents an evaluated submission or score recorded by the teacher for a student.
    """

    __tablename__ = "activity_grades"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "student_id",
            name="uq_activity_grades_activity_student",
        ),
        CheckConstraint(
            "score >= 0",
            name="ck_activity_grades_score_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        doc="Attained grade.",
    )
    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Qualitative pedagogical feedback from educator.",
    )
    status: Mapped[ActivitySubmissionStatus] = mapped_column(
        SQLEnum(
            ActivitySubmissionStatus,
            name="activity_submission_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ActivitySubmissionStatus.PENDING,
    )
    graded_by_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        doc="Teacher who assigned the score.",
    )
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Relationships
    activity: Mapped[AcademicActivity] = relationship(
        "AcademicActivity",
        back_populates="grades",
    )
    student: Mapped[Student] = relationship("Student")
    graded_by: Mapped[Teacher | None] = relationship("Teacher")


# ===========================================================================
# 4. Student Submission & Attachment Models (Phase B3-H13)
# ===========================================================================

class StudentSubmission(Base):
    """
    Student Activity Submission Attempt (Entrega de Actividad por Estudiante).

    Captures student answers (text and/or attached files) with multi-attempt support.
    Grades and evaluative feedback remain strictly in ActivityGrade.
    """

    __tablename__ = "student_submissions"
    __table_args__ = (
        UniqueConstraint(
            "activity_id",
            "student_id",
            "attempt_number",
            name="uq_student_submissions_activity_student_attempt",
        ),
        Index(
            "ix_student_submissions_tenant_activity_student",
            "institution_id",
            "activity_id",
            "student_id",
        ),
        Index(
            "ix_student_submissions_activity_status",
            "activity_id",
            "status",
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
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target activity.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Submitting student.",
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        doc="Monotonically increasing attempt number for resubmissions.",
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        SQLEnum(
            SubmissionStatus,
            name="submission_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=SubmissionStatus.DRAFT,
        server_default="DRAFT",
        doc="Submission lifecycle state.",
    )
    student_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Textual answer or commentary submitted by the student.",
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when student confirmed delivery.",
    )
    is_late: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        doc="True if submitted past activity due_date in UTC.",
    )
    return_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Pedagogical feedback provided by teacher upon returning the attempt for revision.",
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when teacher returned the attempt.",
    )
    returned_by_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        doc="Teacher who returned this submission attempt.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    activity: Mapped[AcademicActivity] = relationship(
        "AcademicActivity",
        back_populates="submissions",
    )
    student: Mapped[Student] = relationship("Student")
    institution: Mapped[Institution] = relationship("Institution")
    returned_by: Mapped[Teacher | None] = relationship("Teacher")
    attachments: Mapped[list[SubmissionAttachment]] = relationship(
        "SubmissionAttachment",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionAttachment.created_at",
    )


class SubmissionAttachment(Base):
    """
    Submission Attachment Entity (Archivo Adjunto a una Entrega de Estudiante).

    Represents a student-uploaded document associated with a specific submission attempt.
    """

    __tablename__ = "submission_attachments"
    __table_args__ = (
        Index(
            "ix_submission_attachments_tenant_submission",
            "institution_id",
            "submission_id",
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
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated submission attempt.",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Opaque relative storage path on disk.",
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User-facing original filename.",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="File size in bytes.",
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Detected MIME type.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # Submission attachments are immutable upload evidence; migration 023 intentionally does not include updated_at.
    updated_at = None

    # Relationships
    submission: Mapped[StudentSubmission] = relationship(
        "StudentSubmission",
        back_populates="attachments",
    )
    institution: Mapped[Institution] = relationship("Institution")


# ===========================================================================
# 3. Daily Attendance Model
# ===========================================================================

class DailyAttendance(Base):
    """
    Daily Student Attendance Record (Registro de Asistencia Diaria).

    Captures student attendance for a classroom group session.
    """

    __tablename__ = "daily_attendances"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "student_id",
            "attendance_date",
            "subject_id",
            name="uq_daily_attendances_session_student",
        ),
        Index(
            "ix_daily_attendances_query",
            "group_id",
            "attendance_date",
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
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Subject being taught during attendance session.",
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Recording educator.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Calendar date of attendance.",
    )
    status: Mapped[AttendanceStatusEnum] = mapped_column(
        SQLEnum(
            AttendanceStatusEnum,
            name="daily_attendance_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AttendanceStatusEnum.PRESENT,
    )
    remarks: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Observation or justification note.",
    )
    # Relationships
    group: Mapped[Group] = relationship("Group")
    student: Mapped[Student] = relationship("Student")
    teacher: Mapped[Teacher] = relationship("Teacher")
    subject: Mapped[Subject | None] = relationship("Subject")


# ===========================================================================
# 4. Academic Planning Model (Planeación Curricular)
# ===========================================================================

class AcademicPlan(Base):
    """
    Academic Curricular Lesson Plan (Planeación de Unidad / Asignatura).

    Enables teachers to document learning objectives, competencies, methodology,
    and evaluation criteria for their active assignments.
    """

    __tablename__ = "academic_plans"
    __table_args__ = (
        Index(
            "ix_academic_plans_tenant_teacher",
            "institution_id",
            "teacher_id",
        ),
        Index(
            "ix_academic_plans_group_subject",
            "group_id",
            "subject_id",
            "academic_year_id",
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
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    academic_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    unit_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Thematic unit title (e.g. 'Unidad 1: Funciones y Límites').",
    )
    competencies: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Standard competencies (MEN standards / DBA).",
    )
    learning_objectives: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Expected learning outcomes (Evidencias de aprendizaje).",
    )
    methodology: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Didactic strategy and pedagogical methodology.",
    )
    evaluation_criteria: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Formative and summative assessment criteria.",
    )
    resources: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Textbooks, digital resources, or laboratory equipment.",
    )
    status: Mapped[AcademicPlanStatus] = mapped_column(
        SQLEnum(
            AcademicPlanStatus,
            name="academic_plan_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AcademicPlanStatus.DRAFT,
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    # Relationships
    teacher: Mapped[Teacher] = relationship("Teacher")
    subject: Mapped[Subject] = relationship("Subject")
    group: Mapped[Group] = relationship("Group")
    academic_year: Mapped[AcademicYear] = relationship("AcademicYear")
