"""
PEVN Backend — Academic Management Pydantic Schemas

Defines request and response schemas for all academic domain entities:
Academic Years, Groups, Students, Teachers, Guardians, Enrollments,
Transfers, and Academic Assignments.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.academic_year import (
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import EnrollmentStatus
from app.models.group import ShiftEnum
from app.models.guardian import GuardianRelationshipType
from app.models.student import StudentGender
from app.models.teacher import TeacherContractType
from app.models.user import DocumentType
from app.schemas.user import UserResponse

# ===========================================================================
# 1. Academic Year Schemas
# ===========================================================================


class AcademicYearCreateRequest(BaseModel):
    """Payload for creating a new academic school year."""

    model_config = ConfigDict(extra="forbid")

    year: int = Field(..., ge=2000, le=2100, description="Calendar year")
    name: str = Field(..., min_length=2, max_length=100, description="Name")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    calendar_type: AcademicYearCalendarType = Field(
        default=AcademicYearCalendarType.CALENDAR_A,
        description="Colombian calendar type",
    )
    status: AcademicYearStatus = Field(
        default=AcademicYearStatus.PLANNING,
        description="Initial lifecycle status",
    )


class AcademicYearResponse(BaseModel):
    """Response representation of an academic school year."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    year: int
    name: str
    start_date: date
    end_date: date
    calendar_type: AcademicYearCalendarType
    status: AcademicYearStatus
    created_at: datetime
    updated_at: datetime


class AcademicYearListResponse(BaseModel):
    """List response for academic school years."""

    items: list[AcademicYearResponse]
    total: int


# ===========================================================================
# 2. Group Schemas
# ===========================================================================


class GroupCreateRequest(BaseModel):
    """Payload for creating a classroom group section."""

    model_config = ConfigDict(extra="forbid")

    campus_id: uuid.UUID = Field(..., description="Campus ID")
    academic_year_id: uuid.UUID = Field(..., description="Academic year ID")
    grade_id: uuid.UUID = Field(..., description="National Grade catalog ID")
    name: str = Field(..., min_length=1, max_length=50, description="Name")
    shift: ShiftEnum = Field(default=ShiftEnum.MANANA, description="Shift")
    capacity_limit: int = Field(default=35, ge=1, le=100, description="Capacity")
    director_teacher_id: uuid.UUID | None = Field(
        default=None, description="Director teacher ID"
    )


class AssignGroupDirectorRequest(BaseModel):
    """Payload for assigning or changing a group director teacher."""

    model_config = ConfigDict(extra="forbid")

    teacher_id: uuid.UUID = Field(..., description="Teacher profile ID")


class GroupResponse(BaseModel):
    """Response representation of an educational group."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campus_id: uuid.UUID
    academic_year_id: uuid.UUID
    grade_id: uuid.UUID
    name: str
    shift: ShiftEnum
    capacity_limit: int
    group_director_teacher_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class GroupCapacityResponse(BaseModel):
    """Capacity and occupancy availability for a group."""

    group_id: uuid.UUID
    capacity_limit: int
    active_enrolled_count: int
    available_slots: int


class GroupListResponse(BaseModel):
    """List response for educational groups."""

    items: list[GroupResponse]
    total: int


# ===========================================================================
# 3. Student Schemas
# ===========================================================================


class StudentCreateRequest(BaseModel):
    """Payload for creating a student profile linked to a User account."""

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID = Field(..., description="User account ID")
    code_simat: str = Field(..., min_length=3, max_length=50, description="SIMAT")
    birth_date: date = Field(..., description="Date of birth")
    gender: StudentGender = Field(default=StudentGender.M, description="Gender")
    blood_type: str | None = Field(default=None, max_length=5, description="RH")
    stratum: int | None = Field(default=None, ge=1, le=6, description="Stratum")
    eps_health_provider: str | None = Field(
        default=None, max_length=100, description="EPS provider"
    )
    has_disability: bool = Field(default=False, description="Inclusion flag")
    disability_type: str | None = Field(
        default=None, max_length=100, description="Disability type"
    )


class StudentResponse(BaseModel):
    """Response representation of a student profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    institution_id: uuid.UUID
    code_simat: str
    birth_date: date
    gender: StudentGender
    blood_type: str | None
    stratum: int | None
    eps_health_provider: str | None
    has_disability: bool
    disability_type: str | None
    user: UserResponse | None = None
    created_at: datetime
    updated_at: datetime


class StudentListResponse(BaseModel):
    """List response for students."""

    items: list[StudentResponse]
    total: int


# ===========================================================================
# 4. Teacher Schemas
# ===========================================================================


class TeacherCreateRequest(BaseModel):
    """Payload for creating a teacher profile linked to a User account."""

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID = Field(..., description="User account ID")
    specialty_area: str | None = Field(
        default=None, max_length=150, description="Specialty"
    )
    contract_type: TeacherContractType = Field(
        default=TeacherContractType.PROPIEDAD,
        description="Appointment type",
    )
    escalafon_grade: str | None = Field(
        default=None, max_length=50, description="Escalafon"
    )


class TeacherResponse(BaseModel):
    """Response representation of a teacher profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    institution_id: uuid.UUID
    specialty_area: str | None
    contract_type: TeacherContractType
    escalafon_grade: str | None
    user: UserResponse | None = None
    created_at: datetime
    updated_at: datetime


class TeacherEligibilityResponse(BaseModel):
    """Eligibility status for teacher workload assignments."""

    teacher_id: uuid.UUID
    is_eligible: bool
    message: str


class TeacherListResponse(BaseModel):
    """List response for teachers."""

    items: list[TeacherResponse]
    total: int


# ===========================================================================
# 5. Guardian Schemas
# ===========================================================================


class GuardianCreateRequest(BaseModel):
    """Payload for creating a guardian profile (OPEN-DECISION-3A-01)."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    document_type: DocumentType = Field(default=DocumentType.CC)
    document_number: str = Field(..., min_length=4, max_length=50)
    phone: str = Field(..., min_length=7, max_length=50)
    email: EmailStr | None = Field(default=None, description="Optional email")
    address: str | None = Field(default=None, max_length=255)
    relationship_type: GuardianRelationshipType = Field(
        default=GuardianRelationshipType.MADRE
    )
    user_id: uuid.UUID | None = Field(default=None, description="Optional User")


class AssociateGuardianRequest(BaseModel):
    """Payload for associating a guardian to a student."""

    model_config = ConfigDict(extra="forbid")

    relationship_type: GuardianRelationshipType = Field(
        default=GuardianRelationshipType.PADRE
    )
    is_primary_contact: bool = Field(default=False)
    is_authorized_pickup: bool = Field(default=True)


class GuardianResponse(BaseModel):
    """Response representation of a guardian."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    document_type: DocumentType
    document_number: str
    phone: str
    email: str | None
    address: str | None
    relationship_type: GuardianRelationshipType
    user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class StudentGuardianResponse(BaseModel):
    """Response representation of student-guardian association."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    guardian_id: uuid.UUID
    relationship_type: GuardianRelationshipType
    is_primary_contact: bool
    is_authorized_pickup: bool
    guardian: GuardianResponse | None = None
    created_at: datetime
    updated_at: datetime


class GuardianListResponse(BaseModel):
    """List response for guardians."""

    items: list[GuardianResponse]
    total: int


# ===========================================================================
# 6. Enrollment Schemas
# ===========================================================================


class EnrollmentCreateRequest(BaseModel):
    """Payload for creating a new student enrollment."""

    model_config = ConfigDict(extra="forbid")

    student_id: uuid.UUID = Field(..., description="Student profile ID")
    group_id: uuid.UUID = Field(..., description="Group ID")
    academic_year_id: uuid.UUID = Field(..., description="Academic year ID")
    enrollment_date: date | None = Field(default=None, description="Enrollment date")
    status: EnrollmentStatus = Field(
        default=EnrollmentStatus.ACTIVE,
        description="Status",
    )
    status_reason: str | None = Field(default=None, max_length=255)


class EnrollmentWithdrawRequest(BaseModel):
    """Payload for withdrawing an enrollment."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(..., min_length=3, max_length=255, description="Reason")


class EnrollmentGraduateRequest(BaseModel):
    """Payload for graduating an active enrollment."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        default="Culminación exitosa del año lectivo",
        min_length=3,
        max_length=255,
    )


class EnrollmentResponse(BaseModel):
    """Response representation of a student enrollment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    enrollment_date: date
    status: EnrollmentStatus
    status_reason: str | None
    created_at: datetime
    updated_at: datetime


class EnrollmentListResponse(BaseModel):
    """List response for student enrollments."""

    items: list[EnrollmentResponse]
    total: int


# ===========================================================================
# 7. Transfer Schemas
# ===========================================================================


class GroupTransferRequest(BaseModel):
    """Payload for executing an atomic group transfer."""

    model_config = ConfigDict(extra="forbid")

    enrollment_id: uuid.UUID = Field(..., description="Enrollment ID")
    target_group_id: uuid.UUID = Field(..., description="Target group ID")
    reason: str = Field(..., min_length=3, max_length=255, description="Reason")


class GroupTransferHistoryResponse(BaseModel):
    """Response representation of a group transfer audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    enrollment_id: uuid.UUID
    previous_group_id: uuid.UUID
    new_group_id: uuid.UUID
    transferred_by_user_id: uuid.UUID
    transfer_date: datetime
    reason: str
    created_at: datetime


class TransferExecutionResponse(BaseModel):
    """Combined response returned upon successful group transfer."""

    enrollment: EnrollmentResponse
    transfer_history: GroupTransferHistoryResponse


class GroupTransferHistoryListResponse(BaseModel):
    """List response for transfer histories."""

    items: list[GroupTransferHistoryResponse]
    total: int


# ===========================================================================
# 8. Academic Assignment Schemas
# ===========================================================================


class AcademicAssignmentCreateRequest(BaseModel):
    """Payload for assigning a teacher to a subject and group."""

    model_config = ConfigDict(extra="forbid")

    teacher_id: uuid.UUID = Field(..., description="Teacher ID")
    subject_id: uuid.UUID = Field(..., description="Subject ID")
    group_id: uuid.UUID = Field(..., description="Group ID")
    academic_year_id: uuid.UUID = Field(..., description="Academic year ID")
    weekly_hours: int = Field(..., ge=1, le=40, description="Weekly hours")
    is_active: bool = Field(default=True, description="Active flag")


class TeacherReplacementRequest(BaseModel):
    """Payload for atomically substituting a teacher on an assignment."""

    model_config = ConfigDict(extra="forbid")

    new_teacher_id: uuid.UUID = Field(..., description="New teacher ID")


class AcademicAssignmentResponse(BaseModel):
    """Response representation of an academic workload assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    weekly_hours: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TeacherReplacementResponse(BaseModel):
    """Combined response returned upon teacher replacement."""

    previous_assignment: AcademicAssignmentResponse
    new_assignment: AcademicAssignmentResponse


class AcademicAssignmentListResponse(BaseModel):
    """List response for academic assignments."""

    items: list[AcademicAssignmentResponse]
    total: int
