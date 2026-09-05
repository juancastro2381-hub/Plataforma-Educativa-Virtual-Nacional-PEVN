"""
PEVN Backend — Domain Services Package

Authoritative domain services for Authentication, Academic Management,
and Virtual Classroom / Real-Time Collaboration.
"""

from __future__ import annotations

from app.services.academic_assignment_service import AcademicAssignmentService
from app.services.academic_year_service import AcademicYearService
from app.services.attendance_service import AttendanceService
from app.services.auth_service import AuthService
from app.services.enrollment_service import EnrollmentService
from app.services.group_service import GroupService
from app.services.guardian_service import GuardianService
from app.services.recording_service import RecordingService
from app.services.student_service import StudentService
from app.services.teacher_portal_service import TeacherPortalService
from app.services.teacher_service import TeacherService
from app.services.transfer_service import TransferService
from app.services.virtual_classroom_service import VirtualClassroomService

__all__ = [
    "AcademicAssignmentService",
    "AcademicYearService",
    "AttendanceService",
    "AuthService",
    "EnrollmentService",
    "GroupService",
    "GuardianService",
    "RecordingService",
    "StudentService",
    "TeacherPortalService",
    "TeacherService",
    "TransferService",
    "VirtualClassroomService",
]
