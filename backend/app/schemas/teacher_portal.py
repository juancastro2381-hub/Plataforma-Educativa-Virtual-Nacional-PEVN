"""
PEVN Backend — Teacher Portal Pydantic Schemas

Strict Pydantic schemas for the dedicated Teacher Portal API:
- Dashboard KPI metrics and summary
- Teacher Academic Workload allocations
- Teacher Group sections and student rosters
- Academic Activities and submission/grade management
- Daily classroom attendance recording
- Curricular lesson planning
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.academic_activity import (
    AcademicPlanStatus,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
)
from app.models.group import ShiftEnum


# ===========================================================================
# 1. Dashboard Summary
# ===========================================================================

class TeacherDashboardSummaryResponse(BaseModel):
    """Aggregated operational metrics for teacher home dashboard."""

    model_config = ConfigDict(from_attributes=True)

    teacher_id: uuid.UUID
    teacher_name: str
    specialty_area: str | None = None
    institution_id: uuid.UUID
    institution_name: str
    active_academic_year: str | None = None
    total_active_assignments: int = 0
    total_assigned_groups: int = 0
    total_assigned_subjects: int = 0
    total_active_activities: int = 0
    total_pending_grades: int = 0
    total_enrolled_students: int = 0


# ===========================================================================
# 2. My Academic Load (Assignments)
# ===========================================================================

class TeacherAssignmentItemResponse(BaseModel):
    """Enriched active academic assignment item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    subject_name: str
    knowledge_area_name: str | None = None
    group_id: uuid.UUID
    group_name: str
    grade_name: str | None = None
    campus_name: str | None = None
    shift: ShiftEnum | str | None = None
    academic_year_id: uuid.UUID
    academic_year_name: str
    weekly_hours: int
    is_active: bool


class TeacherAssignmentsListResponse(BaseModel):
    """List of teacher academic assignments."""

    items: list[TeacherAssignmentItemResponse]
    total: int


# ===========================================================================
# 3. My Groups & Student Rosters
# ===========================================================================

class TeacherGroupItemResponse(BaseModel):
    """Group summary assigned to the teacher."""

    model_config = ConfigDict(from_attributes=True)

    group_id: uuid.UUID
    group_name: str
    grade_name: str | None = None
    campus_name: str | None = None
    shift: ShiftEnum | str | None = None
    academic_year_id: uuid.UUID
    academic_year_name: str
    capacity_limit: int
    active_enrolled_count: int
    subjects_taught: list[str] = Field(default_factory=list)


class TeacherGroupsListResponse(BaseModel):
    """List of groups where the teacher has active assignments."""

    items: list[TeacherGroupItemResponse]
    total: int


class TeacherStudentRosterItem(BaseModel):
    """Student identity and enrollment details for a group."""

    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    enrollment_id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    document_type: str
    document_number: str
    simat_code: str | None = None
    enrollment_status: str
    enrollment_date: date


class TeacherGroupRosterResponse(BaseModel):
    """Complete classroom roster for an authorized group."""

    group_id: uuid.UUID
    group_name: str
    academic_year_id: uuid.UUID
    academic_year_name: str
    campus_name: str | None = None
    shift: str | None = None
    total_students: int
    students: list[TeacherStudentRosterItem]


# ===========================================================================
# 4. Academic Activities
# ===========================================================================

class AcademicActivityCreateRequest(BaseModel):
    """Payload to create a new academic activity."""

    subject_id: uuid.UUID
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    title: Annotated[str, Field(min_length=3, max_length=200)]
    description: str | None = None
    activity_type: ActivityType = ActivityType.TASK
    due_date: datetime | None = None
    max_score: Annotated[Decimal, Field(gt=0, le=100)] = Decimal("5.00")
    instructions: str | None = None
    resource_url: str | None = None


class AcademicActivityUpdateRequest(BaseModel):
    """Payload to update an existing academic activity."""

    title: Annotated[str, Field(min_length=3, max_length=200)] | None = None
    description: str | None = None
    activity_type: ActivityType | None = None
    due_date: datetime | None = None
    max_score: Annotated[Decimal, Field(gt=0, le=100)] | None = None
    instructions: str | None = None
    resource_url: str | None = None


class AcademicActivityResponse(BaseModel):
    """Enriched academic activity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    teacher_id: uuid.UUID
    teacher_name: str | None = None
    subject_id: uuid.UUID
    subject_name: str | None = None
    group_id: uuid.UUID
    group_name: str | None = None
    academic_year_id: uuid.UUID
    academic_year_name: str | None = None
    title: str
    description: str | None = None
    activity_type: ActivityType
    status: ActivityStatus
    publication_date: datetime | None = None
    due_date: datetime | None = None
    max_score: Decimal
    instructions: str | None = None
    resource_url: str | None = None
    total_submissions: int = 0
    total_graded: int = 0
    created_at: datetime
    updated_at: datetime


class AcademicActivityListResponse(BaseModel):
    """List of academic activities."""

    items: list[AcademicActivityResponse]
    total: int


# ===========================================================================
# 5. Activity Grades & Evaluations
# ===========================================================================

class ActivityGradeItemResponse(BaseModel):
    """Grade record for a single student in an activity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_document: str
    score: Decimal | None = None
    feedback: str | None = None
    status: ActivitySubmissionStatus
    graded_at: datetime | None = None


class ActivityGradesListResponse(BaseModel):
    """Gradesheet list for an activity."""

    activity_id: uuid.UUID
    activity_title: str
    group_name: str
    subject_name: str
    max_score: Decimal
    items: list[ActivityGradeItemResponse]
    total: int


class ActivityGradeEntry(BaseModel):
    """Single student grade payload."""

    student_id: uuid.UUID
    score: Annotated[Decimal, Field(ge=0)] | None = None
    feedback: str | None = None


class ActivityGradeBatchUpdateRequest(BaseModel):
    """Batch grade update request for an activity."""

    grades: list[ActivityGradeEntry]


# ===========================================================================
# 6. Daily Classroom Attendance
# ===========================================================================

class DailyAttendanceStudentItem(BaseModel):
    """Attendance item per student for a date and group."""

    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    student_name: str
    document_number: str
    status: AttendanceStatusEnum
    remarks: str | None = None


class DailyAttendanceListResponse(BaseModel):
    """Attendance sheet for a group session."""

    group_id: uuid.UUID
    group_name: str
    subject_id: uuid.UUID | None = None
    subject_name: str | None = None
    attendance_date: date
    total_students: int
    items: list[DailyAttendanceStudentItem]


class DailyAttendanceEntry(BaseModel):
    """Single student attendance mark."""

    student_id: uuid.UUID
    status: AttendanceStatusEnum
    remarks: str | None = None


class DailyAttendanceBatchRequest(BaseModel):
    """Batch attendance record submission."""

    subject_id: uuid.UUID | None = None
    attendance_date: date
    records: list[DailyAttendanceEntry]


# ===========================================================================
# 7. Curricular Planning
# ===========================================================================

class AcademicPlanCreateRequest(BaseModel):
    """Payload to create a lesson / unit plan."""

    subject_id: uuid.UUID
    group_id: uuid.UUID
    academic_year_id: uuid.UUID
    unit_name: Annotated[str, Field(min_length=3, max_length=200)]
    competencies: str | None = None
    learning_objectives: str | None = None
    methodology: str | None = None
    evaluation_criteria: str | None = None
    resources: str | None = None
    status: AcademicPlanStatus = AcademicPlanStatus.DRAFT
    start_date: date | None = None
    end_date: date | None = None


class AcademicPlanUpdateRequest(BaseModel):
    """Payload to update an existing plan."""

    unit_name: Annotated[str, Field(min_length=3, max_length=200)] | None = None
    competencies: str | None = None
    learning_objectives: str | None = None
    methodology: str | None = None
    evaluation_criteria: str | None = None
    resources: str | None = None
    status: AcademicPlanStatus | None = None
    start_date: date | None = None
    end_date: date | None = None


class AcademicPlanResponse(BaseModel):
    """Lesson plan representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    teacher_id: uuid.UUID
    teacher_name: str | None = None
    subject_id: uuid.UUID
    subject_name: str | None = None
    group_id: uuid.UUID
    group_name: str | None = None
    academic_year_id: uuid.UUID
    academic_year_name: str | None = None
    unit_name: str
    competencies: str | None = None
    learning_objectives: str | None = None
    methodology: str | None = None
    evaluation_criteria: str | None = None
    resources: str | None = None
    status: AcademicPlanStatus
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime
    updated_at: datetime


class AcademicPlanListResponse(BaseModel):
    """List of lesson plans."""

    items: list[AcademicPlanResponse]
    total: int
