"""
PEVN Backend — Domain Models Package

Exports all domain ORM models for the Plataforma Educativa Virtual Nacional.
"""

from __future__ import annotations

from app.models.academic_activity import (
    AcademicActivity,
    AcademicPlan,
    AcademicPlanStatus,
    ActivityDeliveryType,
    ActivityGrade,
    ActivityResource,
    ActivityResourceType,
    ActivityStatus,
    ActivitySubmissionStatus,
    ActivityType,
    AttendanceStatusEnum,
    DailyAttendance,
    StudentSubmission,
    SubmissionAttachment,
    SubmissionStatus,
)
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.audit_log import AuditLog
from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentFollowUp,
    IncidentStatus,
    StudentIncident,
)
from app.models.communication import (
    CommunicationAudience,
    CommunicationCategory,
    CommunicationPriority,
    CommunicationReceipt,
    InstitutionalCommunication,
    PublishingStatus,
    TargetScopeType,
)
from app.models.enrollment import (
    Enrollment,
    EnrollmentStatus,
    GroupTransferHistory,
)
from app.models.evaluation import (
    AcademicAchievement,
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    PromotionStatusEnum,
    RecoveryGrade,
    SieePolicy,
    StudentPromotion,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.invitation import GuardianInvitation, RectorInvitation
from app.models.news import (
    InstitutionalNews,
    NewsCategory,
)
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialCatalogSyncChunk,
    OfficialInstitutionCatalog,
)
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
    "AcademicAchievement",
    "AcademicActivity",
    "AcademicAssignment",
    "AcademicPeriod",
    "AcademicPlan",
    "AcademicPlanStatus",
    "AcademicYear",
    "AcademicYearCalendarType",
    "AcademicYearStatus",
    "ActivityDeliveryType",
    "ActivityGrade",
    "ActivityResource",
    "ActivityResourceType",
    "ActivityStatus",
    "ActivitySubmissionStatus",
    "ActivityType",
    "AttendanceStatusEnum",
    "AuditLog",
    "Campus",
    "CoexistenceSituationType",
    "CommunicationAudience",
    "CommunicationCategory",
    "CommunicationPriority",
    "CommunicationReceipt",
    "DailyAttendance",
    "Department",
    "DocumentType",
    "EducationalLevel",
    "Enrollment",
    "EnrollmentStatus",
    "Grade",
    "Group",
    "GroupTransferHistory",
    "Guardian",
    "GuardianInvitation",
    "GuardianRelationshipType",
    "IncidentFollowUp",
    "IncidentStatus",
    "Institution",
    "InstitutionalCommunication",
    "InstitutionalNews",
    "KnowledgeArea",
    "MeetingAttendance",
    "MeetingParticipantRole",
    "MeetingRecording",
    "Municipality",
    "NewsCategory",
    "OfficialCampusCatalog",
    "OfficialCatalogSyncBatch",
    "OfficialCatalogSyncChunk",
    "OfficialInstitutionCatalog",
    "PasswordResetToken",
    "PerformanceLevelEnum",
    "PeriodSubjectGrade",
    "Permission",
    "PromotionStatusEnum",
    "PublishingStatus",
    "RecoveryGrade",
    "RectorInvitation",
    "RefreshToken",
    "Role",
    "RolePermission",
    "ShiftEnum",
    "SieePolicy",
    "Student",
    "StudentGender",
    "StudentGuardian",
    "StudentIncident",
    "StudentPromotion",
    "StudentSubmission",
    "SubmissionAttachment",
    "SubmissionStatus",
    "Subject",
    "TargetScopeType",
    "Teacher",
    "TeacherContractType",
    "User",
    "UserRole",
    "VirtualClassroom",
    "VirtualClassroomStatus",
]
