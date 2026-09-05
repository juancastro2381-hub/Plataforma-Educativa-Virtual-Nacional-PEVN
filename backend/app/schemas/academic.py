"""
PEVN Backend — Academic Management Pydantic Schemas

Defines request and response schemas for all academic domain entities:
Academic Years, Groups, Students, Teachers, Guardians, Enrollments,
Transfers, and Academic Assignments.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.academic_year import (
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import EnrollmentStatus
from app.models.grade import EducationalLevel
from app.models.group import ShiftEnum
from app.models.guardian import GuardianRelationshipType
from app.models.student import StudentGender
from app.models.teacher import TeacherContractType
from app.models.user import DocumentType
from app.schemas.user import UserResponse

# ===========================================================================
# 0. Grade Schemas (National Curriculum Catalog)
# ===========================================================================


class GradeResponse(BaseModel):
    """Response representation of a standardized curriculum grade."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    level: EducationalLevel
    ordinal_order: int


class GradeListResponse(BaseModel):
    """List response for curriculum grades."""

    items: list[GradeResponse]
    total: int


# ===========================================================================
# 0.1. Subject Schemas (Curricular Subjects)
# ===========================================================================


class SubjectResponse(BaseModel):
    """Response representation of a curricular subject."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    knowledge_area_id: uuid.UUID
    grade_id: uuid.UUID
    name: str
    weekly_hours: int
    created_at: datetime
    updated_at: datetime


class SubjectListResponse(BaseModel):
    """List response for curricular subjects."""

    items: list[SubjectResponse]
    total: int


class SubjectCreateRequest(BaseModel):
    """Payload for creating a custom curricular subject."""

    model_config = ConfigDict(extra="forbid")

    knowledge_area_id: uuid.UUID = Field(..., description="Knowledge Area ID")
    grade_id: uuid.UUID = Field(..., description="Grade ID")
    name: str = Field(..., min_length=2, max_length=150, description="Subject Name")
    weekly_hours: int = Field(default=4, ge=1, le=40, description="Weekly hours")


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


class AcademicPeriodResponse(BaseModel):
    """Response representation of an academic term period within a school year."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    academic_year_id: uuid.UUID
    period_number: int
    name: str
    weight_percentage: float
    start_date: date
    end_date: date
    is_closed: bool
    created_at: datetime
    updated_at: datetime


class AcademicPeriodListResponse(BaseModel):
    """List response for academic periods."""

    items: list[AcademicPeriodResponse]
    total: int


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
    periods: list[AcademicPeriodResponse] = []
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


class StudentNewUserPayload(BaseModel):
    """Civil identity payload for on-the-fly student user provisioning."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres del estudiante")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos del estudiante")
    document_type: DocumentType = Field(default=DocumentType.TI, description="Tipo de documento")
    document_number: str = Field(..., min_length=3, max_length=50, description="Número de documento")
    email: EmailStr = Field(..., description="Correo electrónico institucional")
    phone: str | None = Field(default=None, max_length=50, description="Teléfono de contacto")


class StudentCreateRequest(BaseModel):
    """Payload for creating a student profile either via existing user_id or new_user."""

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID | None = Field(
        default=None, description="User account ID (if linking existing user)"
    )
    new_user: StudentNewUserPayload | None = Field(
        default=None, description="Civil identity to provision a new student on the fly"
    )
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

    @model_validator(mode="after")
    def validate_user_provisioning_mode(self) -> StudentCreateRequest:
        if bool(self.user_id) == bool(self.new_user):
            raise ValueError(
                "Debe proporcionar exactamente uno: 'user_id' (usuario existente) o 'new_user' (nuevo estudiante)."
            )
        return self


class StudentAccountStatusEnum(StrEnum):
    """Lifecycle state of a student's login account."""

    SIN_CUENTA = "SIN_CUENTA"
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


class StudentAccountProvisionRequest(BaseModel):
    """Payload for provisioning a login account for an existing student."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = Field(default=None, description="Optional updated student email")


class StudentAccountStatusUpdateRequest(BaseModel):
    """Payload for activating or deactivating a student's login account."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool = Field(..., description="Target active state for login account")


class StudentAccountActionResponse(BaseModel):
    """Response representation of a student account lifecycle mutation."""

    student_id: uuid.UUID
    user_id: uuid.UUID
    account_status: StudentAccountStatusEnum
    message: str
    reset_token: str | None = Field(default=None, description="Temporary setup/reset token returned only upon action execution")


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
    account_status: StudentAccountStatusEnum = StudentAccountStatusEnum.SIN_CUENTA
    account_email: str | None = None
    has_account: bool = False
    created_at: datetime
    updated_at: datetime


class StudentListResponse(BaseModel):
    """List response for students."""

    items: list[StudentResponse]
    total: int


# ===========================================================================
# 4. Teacher Schemas
# ===========================================================================


class TeacherNewUserPayload(BaseModel):
    """Civil identity payload for on-the-fly teacher user provisioning."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres del docente")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos del docente")
    document_type: DocumentType = Field(default=DocumentType.CC, description="Tipo de documento")
    document_number: str = Field(..., min_length=3, max_length=50, description="Número de documento")
    email: EmailStr = Field(..., description="Correo electrónico institucional")
    phone: str | None = Field(default=None, max_length=50, description="Teléfono de contacto")


class TeacherCreateRequest(BaseModel):
    """Payload for creating a teacher profile either via existing user_id or new_user."""

    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID | None = Field(
        default=None, description="User account ID (if linking existing user)"
    )
    new_user: TeacherNewUserPayload | None = Field(
        default=None, description="Civil identity to provision a new user on the fly"
    )
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
    provision_account: bool = Field(
        default=True,
        description="Whether to immediately provision login credentials and activate teacher user role",
    )

    @model_validator(mode="after")
    def validate_user_provisioning_mode(self) -> TeacherCreateRequest:
        if bool(self.user_id) == bool(self.new_user):
            raise ValueError(
                "Debe proporcionar exactamente uno: 'user_id' (usuario existente) o 'new_user' (nuevo docente)."
            )
        return self


class TeacherAccountStatusEnum(StrEnum):
    """Lifecycle state of an educator's login account."""

    SIN_CUENTA = "SIN_CUENTA"
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


class TeacherAccountProvisionRequest(BaseModel):
    """Payload for provisioning a login account for an existing teacher."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = Field(default=None, description="Optional updated institutional email")


class TeacherAccountStatusUpdateRequest(BaseModel):
    """Payload for activating or deactivating a teacher's login account."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool = Field(..., description="Target active state for login account")


class TeacherAccountActionResponse(BaseModel):
    """Response representation of an account lifecycle mutation."""

    teacher_id: uuid.UUID
    user_id: uuid.UUID
    account_status: TeacherAccountStatusEnum
    message: str
    reset_token: str | None = Field(default=None, description="Temporary setup token (dev environment only)")


class TeacherResponse(BaseModel):
    """Response representation of a teacher profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    institution_id: uuid.UUID
    specialty_area: str | None = None
    contract_type: TeacherContractType
    escalafon_grade: str | None = None
    user: UserResponse | None = None
    account_status: TeacherAccountStatusEnum = TeacherAccountStatusEnum.SIN_CUENTA
    account_email: str | None = None
    has_account: bool = False
    reset_token: str | None = None
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


class GuardianNewUserPayload(BaseModel):
    """Civil identity payload for on-the-fly guardian user provisioning."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=100, description="Nombres del acudiente")
    last_name: str = Field(..., min_length=2, max_length=100, description="Apellidos del acudiente")
    document_type: DocumentType = Field(default=DocumentType.CC, description="Tipo de documento")
    document_number: str = Field(..., min_length=4, max_length=50, description="Número de documento")
    email: EmailStr = Field(..., description="Correo electrónico del acudiente")
    phone: str | None = Field(default=None, max_length=50, description="Teléfono de contacto")


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
    user_id: uuid.UUID | None = Field(default=None, description="Optional User ID if linking existing user")
    new_user: GuardianNewUserPayload | None = Field(
        default=None, description="Civil identity to provision a new guardian user on the fly"
    )
    provision_account: bool = Field(
        default=False,
        description="Whether to immediately provision login credentials and activate guardian user role",
    )


class GuardianAccountStatusEnum(StrEnum):
    """Lifecycle state of a legal guardian's login account."""

    SIN_CUENTA = "SIN_CUENTA"
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"


class GuardianAccountProvisionRequest(BaseModel):
    """Payload for provisioning a login account for an existing guardian."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = Field(default=None, description="Optional updated guardian email")


class GuardianAccountStatusUpdateRequest(BaseModel):
    """Payload for activating or deactivating a guardian's login account."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool = Field(..., description="Target active state for login account")


class GuardianAccountActionResponse(BaseModel):
    """Response representation of a guardian account lifecycle mutation."""

    guardian_id: uuid.UUID
    user_id: uuid.UUID
    account_status: GuardianAccountStatusEnum
    message: str
    reset_token: str | None = Field(default=None, description="Temporary setup/reset token returned only upon action execution")


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
    institution_id: uuid.UUID
    first_name: str
    last_name: str
    document_type: DocumentType
    document_number: str
    phone: str
    email: str | None
    address: str | None
    relationship_type: GuardianRelationshipType
    user_id: uuid.UUID | None
    user: UserResponse | None = None
    account_status: GuardianAccountStatusEnum = GuardianAccountStatusEnum.SIN_CUENTA
    account_email: str | None = None
    has_account: bool = False
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
    student: StudentResponse | None = None
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
