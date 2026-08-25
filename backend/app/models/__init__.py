"""
PEVN Backend — Domain Models Package

Exports all domain ORM models for the Plataforma Educativa Virtual Nacional.
"""

from __future__ import annotations

from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.audit_log import AuditLog
from app.models.enrollment import (
    Enrollment,
    EnrollmentStatus,
    GroupTransferHistory,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import DocumentType, User
from app.models.virtual_classroom import (
    MeetingAttendance,
    MeetingParticipantRole,
    MeetingRecording,
    VirtualClassroom,
    VirtualClassroomStatus,
)

__all__ = [
    "AcademicAssignment",
    "AcademicPeriod",
    "AcademicYear",
    "AcademicYearCalendarType",
    "AcademicYearStatus",
    "AuditLog",
    "Campus",
    "Department",
    "DocumentType",
    "EducationalLevel",
    "Enrollment",
    "EnrollmentStatus",
    "Grade",
    "Group",
    "GroupTransferHistory",
    "Guardian",
    "GuardianRelationshipType",
    "Institution",
    "KnowledgeArea",
    "MeetingAttendance",
    "MeetingParticipantRole",
    "MeetingRecording",
    "Municipality",
    "PasswordResetToken",
    "Permission",
    "RefreshToken",
    "Role",
    "RolePermission",
    "ShiftEnum",
    "Student",
    "StudentGender",
    "StudentGuardian",
    "Subject",
    "Teacher",
    "TeacherContractType",
    "User",
    "UserRole",
    "VirtualClassroom",
    "VirtualClassroomStatus",
]
