"""
PEVN Backend — Student Portal Pydantic Schemas

Authoritative response and request schemas for the self-service Student Portal:
- Profile and Enrollment Context
- Consolidated Dashboard & Metrics
- Enrolled Subjects & Assigned Educators
- Tasks, Workshops, Quizzes & Submissions
- Grades, Scores & Qualitative Feedback
- Daily Attendance History
- Virtual Classrooms & Access Information
- Class Recordings
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.academic_activity import (
    ActivityDeliveryType,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    SubmissionStatus,
)
from app.models.user import DocumentType


# ===========================================================================
# 1. Student Profile & Academic Context
# ===========================================================================

class StudentProfileResponse(BaseModel):
    """Enriched student identity, institution, and active group enrollment."""

    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    email: str
    document_type: DocumentType | str
    document_number: str
    code_simat: str
    birth_date: date
    institution_id: uuid.UUID
    institution_name: str
    campus_name: str | None = None
    grade_name: str | None = None
    group_id: uuid.UUID | None = None
    group_name: str | None = None
    academic_year_id: uuid.UUID | None = None
    academic_year_name: str | None = None
    enrollment_status: str | None = None


# ===========================================================================
# 2. Subjects (Plan de Estudios)
# ===========================================================================

class StudentSubjectItemResponse(BaseModel):
    """Enrolled academic subject for the student's current active group."""

    model_config = ConfigDict(from_attributes=True)

    subject_id: uuid.UUID
    name: str
    weekly_hours: int
    knowledge_area_name: str | None = None
    teacher_id: uuid.UUID | None = None
    teacher_name: str | None = None
    teacher_email: str | None = None


class StudentSubjectsListResponse(BaseModel):
    """List of enrolled subjects for the active school year."""

    items: list[StudentSubjectItemResponse]
    total: int


# ===========================================================================
# 3. Activities / Tasks / Homework
# ===========================================================================

class StudentActivityResourceItem(BaseModel):
    """Resource item visible to an enrolled student."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_type: str  # URL | FILE
    title: str
    url: str | None = None
    original_filename: str | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    created_at: datetime


class StudentActivityResourceListResponse(BaseModel):
    """List of materials attached to an activity."""

    items: list[StudentActivityResourceItem]
    total: int


class StudentActivityItemResponse(BaseModel):
    """Activity representation tailored for student workflow and deadlines."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None = None
    activity_type: ActivityType
    status: ActivityStatus
    delivery_type: ActivityDeliveryType = Field(default=ActivityDeliveryType.FILE)
    submission_status: str  # PENDING, OVERDUE, SUBMITTED, GRADED
    publication_date: datetime | None = None
    due_date: datetime | None = None
    max_score: Decimal
    score: Decimal | None = None
    feedback: str | None = None
    graded_at: datetime | None = None
    subject_id: uuid.UUID
    subject_name: str
    teacher_name: str | None = None
    instructions: str | None = None
    resource_url: str | None = None
    resources: list[StudentActivityResourceItem] = []


class StudentActivitiesListResponse(BaseModel):
    """List of academic activities applicable to the student."""

    items: list[StudentActivityItemResponse]
    total: int


# ===========================================================================
# 3.1 Student Submissions & Deliveries (Phase B3-H13)
# ===========================================================================

class SubmissionAttachmentItemResponse(BaseModel):
    """Attachment file metadata for a student submission attempt."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    mime_type: str
    created_at: datetime


class StudentSubmissionAttemptResponse(BaseModel):
    """Historical or current attempt record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activity_id: uuid.UUID
    student_id: uuid.UUID
    attempt_number: int
    status: SubmissionStatus
    student_response: str | None = None
    submitted_at: datetime | None = None
    is_late: bool
    return_feedback: str | None = None
    returned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    attachments: list[SubmissionAttachmentItemResponse] = []


class StudentSubmissionDraftUpdateRequest(BaseModel):
    """Payload to update an in-progress submission draft."""

    student_response: str | None = Field(default=None, max_length=10000)


class StudentSubmissionDetailResponse(BaseModel):
    """Enriched submission view for the student portal, with current state and attempt history."""

    activity_id: uuid.UUID
    activity_title: str
    activity_status: ActivityStatus
    delivery_type: ActivityDeliveryType
    due_date: datetime | None = None
    can_submit: bool
    can_edit_draft: bool
    current_attempt: StudentSubmissionAttemptResponse | None = None
    history: list[StudentSubmissionAttemptResponse] = []
    grade_score: Decimal | None = None
    grade_feedback: str | None = None
    graded_at: datetime | None = None


# ===========================================================================
# 4. Grades & Academic Evaluations
# ===========================================================================

class StudentGradeItemResponse(BaseModel):
    """Evaluated activity grade with educator qualitative notes."""

    model_config = ConfigDict(from_attributes=True)

    grade_id: uuid.UUID | None = None
    activity_id: uuid.UUID
    activity_title: str
    activity_type: ActivityType
    subject_id: uuid.UUID
    subject_name: str
    score: Decimal | None = None
    max_score: Decimal
    feedback: str | None = None
    status: ActivitySubmissionStatus
    graded_at: datetime | None = None
    teacher_name: str | None = None


class StudentGradesListResponse(BaseModel):
    """Consolidated list of graded activities."""

    items: list[StudentGradeItemResponse]
    total: int
    average_score: Decimal | None = None


# ===========================================================================
# 5. Daily Attendance
# ===========================================================================

class StudentAttendanceItemResponse(BaseModel):
    """Individual daily attendance record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attendance_date: date
    status: AttendanceStatusEnum
    remarks: str | None = None
    subject_name: str | None = None
    teacher_name: str | None = None


class StudentAttendanceSummary(BaseModel):
    """Attendance statistics."""

    total_sessions: int = 0
    present_count: int = 0
    absent_count: int = 0
    excused_count: int = 0
    late_count: int = 0
    attendance_rate: float = 100.0


class StudentAttendanceListResponse(BaseModel):
    """List of attendance marks with summary breakdown."""

    items: list[StudentAttendanceItemResponse]
    total: int
    summary: StudentAttendanceSummary


# ===========================================================================
# 6. Virtual Classrooms & Recordings
# ===========================================================================

class StudentVirtualClassroomItemResponse(BaseModel):
    """Virtual class session representation for student attendee."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    scheduled_start_time: datetime | None = None
    scheduled_end_time: datetime | None = None
    subject_name: str | None = None
    teacher_name: str | None = None
    can_join: bool = False
    room_name: str | None = None
    has_recordings: bool = False


class StudentVirtualClassroomsListResponse(BaseModel):
    """List of virtual classrooms for the student's active group."""

    items: list[StudentVirtualClassroomItemResponse]
    total: int


class StudentRecordingItemResponse(BaseModel):
    """Lecture recording archive."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    virtual_classroom_id: uuid.UUID
    title: str
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
    playback_url: str | None = None
    created_at: datetime


class StudentRecordingsListResponse(BaseModel):
    """List of recorded lectures."""

    items: list[StudentRecordingItemResponse]
    total: int


# ===========================================================================
# 7. Student Dashboard (Consolidated)
# ===========================================================================

class StudentDashboardResponse(BaseModel):
    """Comprehensive single-trip student home dashboard."""

    model_config = ConfigDict(from_attributes=True)

    profile: StudentProfileResponse
    total_subjects: int
    pending_activities_count: int
    overdue_activities_count: int
    graded_activities_count: int
    attendance_summary: StudentAttendanceSummary
    upcoming_virtual_classrooms: list[StudentVirtualClassroomItemResponse]
    upcoming_activities: list[StudentActivityItemResponse]
    recent_grades: list[StudentGradeItemResponse]
