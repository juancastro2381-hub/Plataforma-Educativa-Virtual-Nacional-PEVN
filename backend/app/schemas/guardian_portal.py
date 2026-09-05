"""
PEVN Backend — Guardian Portal Pydantic Schemas

Authoritative response and request schemas for the self-service Guardian Portal:
- Guardian Profile Context
- Authorized Children / Tutorados (Child Context Switcher)
- Academic Child Overview & Metrics
- Homework / Task Follow-up (Non-submitting observer view)
- Child Grades, Evaluations & Educator Comments
- Child Attendance & Absence Records
- Scheduled Virtual Classroom Agendas
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.academic_activity import (
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
)
from app.models.guardian import GuardianRelationshipType
from app.models.user import DocumentType
from app.schemas.student_portal import (
    StudentActivityItemResponse,
    StudentAttendanceItemResponse,
    StudentAttendanceSummary,
    StudentGradeItemResponse,
    StudentVirtualClassroomItemResponse,
)


# ===========================================================================
# 1. Guardian Profile
# ===========================================================================

class GuardianProfileResponse(BaseModel):
    """Authenticated guardian profile context."""

    model_config = ConfigDict(from_attributes=True)

    guardian_id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    email: str | None = None
    document_type: DocumentType | str
    document_number: str
    phone: str
    address: str | None = None
    institution_id: uuid.UUID
    institution_name: str
    total_linked_students: int = 0


# ===========================================================================
# 2. Linked Children / Tutorados (Selector)
# ===========================================================================

class GuardianChildItemResponse(BaseModel):
    """Enriched child profile for the Guardian child-switcher navigation."""

    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    code_simat: str
    document_type: DocumentType | str
    document_number: str
    birth_date: date
    relationship_type: GuardianRelationshipType | str
    is_primary_contact: bool
    is_authorized_pickup: bool
    institution_id: uuid.UUID
    institution_name: str
    campus_name: str | None = None
    grade_name: str | None = None
    group_id: uuid.UUID | None = None
    group_name: str | None = None
    academic_year_name: str | None = None
    enrollment_status: str | None = None


class GuardianChildrenListResponse(BaseModel):
    """List of all authorized children linked to the authenticated guardian."""

    items: list[GuardianChildItemResponse]
    total: int


# ===========================================================================
# 3. Child Academic Overview (Single Child)
# ===========================================================================

class GuardianChildOverviewResponse(BaseModel):
    """Comprehensive academic follow-up summary for a single selected child."""

    model_config = ConfigDict(from_attributes=True)

    child: GuardianChildItemResponse
    total_subjects: int
    pending_tasks_count: int
    overdue_tasks_count: int
    graded_tasks_count: int
    average_score: Decimal | None = None
    attendance_summary: StudentAttendanceSummary
    upcoming_virtual_classrooms: list[StudentVirtualClassroomItemResponse]
    pending_activities: list[StudentActivityItemResponse]
    recent_grades: list[StudentGradeItemResponse]


# ===========================================================================
# 4. Child Activities / Homework Follow-up
# ===========================================================================

class GuardianChildActivitiesListResponse(BaseModel):
    """List of child homework activities for parental monitoring."""

    student_id: uuid.UUID
    student_name: str
    items: list[StudentActivityItemResponse]
    total: int


# ===========================================================================
# 5. Child Grades
# ===========================================================================

class GuardianChildGradesListResponse(BaseModel):
    """Child evaluation records and grades."""

    student_id: uuid.UUID
    student_name: str
    items: list[StudentGradeItemResponse]
    total: int
    average_score: Decimal | None = None


# ===========================================================================
# 6. Child Attendance
# ===========================================================================

class GuardianChildAttendanceListResponse(BaseModel):
    """Child attendance history and statistics."""

    student_id: uuid.UUID
    student_name: str
    items: list[StudentAttendanceItemResponse]
    total: int
    summary: StudentAttendanceSummary


# ===========================================================================
# 7. Child Virtual Classrooms (Agenda View)
# ===========================================================================

class GuardianChildVirtualClassroomsListResponse(BaseModel):
    """Scheduled virtual classroom sessions for the child's group."""

    student_id: uuid.UUID
    student_name: str
    items: list[StudentVirtualClassroomItemResponse]
    total: int
