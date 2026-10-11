"""
PEVN Backend — Audit Service Interface and Foundation

Defines the audit trail architecture for recording security-sensitive events.

PHASE 1 STATUS:
  The IAuditService interface and event taxonomy are defined here.
  The NoOpAuditService is the Phase 1 implementation (records nothing).
  Phase 2 will replace it with a persistent implementation backed by
  a dedicated audit_log table (append-only, not modifiable by the app user).

Audit Design Principles:
  - Append-only: audit records are NEVER modified or deleted by the application.
  - Tamper-evident: future implementation should use cryptographic chaining
    or a write-once storage mechanism.
  - Completeness: all security-sensitive events must be recorded.
  - Privacy-preserving: personal data in audit logs must comply with
    Colombian data protection regulations (Ley 1581 de 2012).
  - Reliable: audit recording failures must NOT silently drop events.

Events that MUST be audited (to be implemented in Phase 2+):
  Authentication:
    - Login success
    - Login failure (including reason: bad password, account locked, etc.)
    - Logout
    - Password change
    - Password reset requested
    - Account locked / unlocked
    - MFA events (when implemented)

  Authorization / Access Control:
    - Permission grants
    - Permission revocations
    - Role assignments
    - Role removals
    - Institutional scope changes

  Data Access (high-sensitivity):
    - Grade modifications
    - Attendance modifications
    - Student record access
    - Recording access

  Administrative:
    - Institution creation / modification / deactivation
    - User creation / modification / deactivation
    - Configuration changes

  Security:
    - Brute force detection triggers
    - Rate limit violations
    - Suspicious access patterns
    - API key creation / revocation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.core.logging import get_logger

_logger = get_logger(__name__)


class AuditEventType(StrEnum):
    """
    Taxonomy of auditable events in the platform.

    Naming convention: NOUN_VERB (e.g., USER_LOGIN, GRADE_UPDATED)
    """

    # Authentication & Token events
    USER_LOGIN_SUCCESS = "user.login.success"
    USER_LOGIN_SUCCESS_UNDER_ATTACK = "user.login.success.under_attack"
    USER_LOGIN_FAILURE = "user.login.failure"
    USER_LOGOUT = "user.logout"
    TOKEN_REFRESH_SUCCESS = "token.refresh.success"  # noqa: S105
    TOKEN_REUSE_DETECTED = "token.reuse.detected"  # noqa: S105
    USER_PASSWORD_CHANGED = "user.password.changed"  # noqa: S105
    USER_PASSWORD_RESET_REQUESTED = "user.password_reset.requested"  # noqa: S105
    USER_PASSWORD_RESET_CONFIRMED = "user.password_reset.confirmed"  # noqa: S105
    USER_ACCOUNT_LOCKED = "user.account.locked"
    USER_ACCOUNT_UNLOCKED = "user.account.unlocked"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_ROLE_ASSIGNED = "user.role.assigned"
    USER_ROLE_REVOKED = "user.role.revoked"
    TEACHER_ACCOUNT_PROVISIONED = "teacher.account.provisioned"

    # Department Administrator Lifecycle
    DEPARTMENT_ADMIN_CREATED = "department_admin.created"
    DEPARTMENT_ADMIN_UPDATED = "department_admin.updated"
    DEPARTMENT_ADMIN_DEPARTMENT_CHANGED = "department_admin.department_changed"
    DEPARTMENT_ADMIN_ACTIVATED = "department_admin.activated"
    DEPARTMENT_ADMIN_DEACTIVATED = "department_admin.deactivated"
    DEPARTMENT_ADMIN_INVITED = "department_admin.invited"
    DEPARTMENT_ADMIN_INVITATION_SENT = "department_admin.invitation_sent"
    DEPARTMENT_ADMIN_ONBOARDING_COMPLETED = "department_admin.onboarding.completed"
    DEPARTMENT_ADMIN_INVITATION_RESENT = "department_admin.invitation_resent"

    # Municipality Administrator Lifecycle
    MUNICIPALITY_ADMIN_CREATED = "municipality_admin.created"
    MUNICIPALITY_ADMIN_UPDATED = "municipality_admin.updated"
    MUNICIPALITY_ADMIN_MUNICIPALITY_CHANGED = "municipality_admin.municipality_changed"
    MUNICIPALITY_ADMIN_ACTIVATED = "municipality_admin.activated"
    MUNICIPALITY_ADMIN_DEACTIVATED = "municipality_admin.deactivated"
    MUNICIPALITY_ADMIN_INVITED = "municipality_admin.invited"
    MUNICIPALITY_ADMIN_INVITATION_SENT = "municipality_admin.invitation_sent"
    MUNICIPALITY_ADMIN_ONBOARDING_COMPLETED = "municipality_admin.onboarding.completed"
    MUNICIPALITY_ADMIN_INVITATION_RESENT = "municipality_admin.invitation_resent"
    MUNICIPALITY_ADMIN_REMEDIATED = "municipality_admin.remediated"

    # Institution & Rector management
    INSTITUTION_CREATED = "institution.created"
    INSTITUTION_UPDATED = "institution.updated"
    INSTITUTION_DEACTIVATED = "institution.deactivated"
    OFFICIAL_DANE_RESOLVED = "official_dane.resolved"
    INSTITUTION_PROVISIONED_FROM_CATALOG = "institution.provisioned_from_catalog"
    RECTOR_INVITED = "rector.invited"
    RECTOR_INVITATION_SENT = "rector.invitation_sent"
    RECTOR_ONBOARDING_COMPLETED = "rector.onboarding.completed"
    RECTOR_INVITATION_RESENT = "rector.invitation_resent"
    RECTOR_REVOKED = "rector.revoked"
    COORDINATOR_INVITED = "coordinator.invited"
    COORDINATOR_INVITATION_SENT = "coordinator.invitation_sent"
    COORDINATOR_ONBOARDING_COMPLETED = "coordinator.onboarding.completed"
    COORDINATOR_INVITATION_RESENT = "coordinator.invitation_resent"
    COORDINATOR_DELEGATION_SETTING_UPDATED = "institution.coordinator_delegation.updated"
    SUPERADMIN_EMERGENCY_ROLE_PROVISIONING = "superadmin.emergency_role_provisioning"

    # National Provisioning & Onboarding Workflow (Phase NTA-04)
    ONBOARDING_REQUEST_CREATED = "onboarding.request.created"
    ONBOARDING_REQUEST_SUBMITTED = "onboarding.request.submitted"
    ONBOARDING_REQUEST_REVIEW_STARTED = "onboarding.request.review_started"
    ONBOARDING_REQUEST_APPROVED = "onboarding.request.approved"
    ONBOARDING_REQUEST_REJECTED = "onboarding.request.rejected"
    ONBOARDING_REQUEST_CANCELLED = "onboarding.request.cancelled"
    INSTITUTION_PROVISIONED_FROM_ONBOARDING = "institution.provisioned_from_onboarding"

    # Academic Management (Phase 3)
    ACADEMIC_YEAR_CREATED = "academic_year.created"
    ACADEMIC_YEAR_UPDATED = "academic_year.updated"
    ACADEMIC_YEAR_ACTIVATED = "academic_year.activated"
    ACADEMIC_YEAR_CLOSED = "academic_year.closed"
    ACADEMIC_PERIOD_CREATED = "academic_period.created"
    ACADEMIC_PERIODS_TEMPLATE_PROVISIONED = "academic_periods.template.provisioned"
    ACADEMIC_PERIODS_ACTIVATED = "academic_periods.activated"
    SIEE_COMPLIANCE_CONFIRMED = "siee.compliance.confirmed"
    SUBJECT_CREATED = "subject.created"
    GROUP_CREATED = "group.created"
    GROUP_UPDATED = "group.updated"
    GROUP_DIRECTOR_ASSIGNED = "group.director.assigned"
    STUDENT_CREATED = "student.created"
    STUDENT_UPDATED = "student.updated"
    STUDENT_ACCOUNT_PROVISIONED = "student.account.provisioned"
    TEACHER_CREATED = "teacher.created"
    TEACHER_UPDATED = "teacher.updated"
    GUARDIAN_CREATED = "guardian.created"
    GUARDIAN_UPDATED = "guardian.updated"
    GUARDIAN_ACCOUNT_PROVISIONED = "guardian.account.provisioned"
    GUARDIAN_ASSOCIATED = "guardian.associated"
    GUARDIAN_DISSOCIATED = "guardian.dissociated"
    GUARDIAN_ACTIVATION_REQUESTED = "guardian.activation.requested"
    GUARDIAN_ONBOARDING_COMPLETED = "guardian.onboarding.completed"
    ENROLLMENT_CREATED = "enrollment.created"
    ENROLLMENT_ACTIVATED = "enrollment.activated"
    ENROLLMENT_WITHDRAWN = "enrollment.withdrawn"
    ENROLLMENT_TRANSFERRED = "enrollment.transferred"
    ENROLLMENT_GRADUATED = "enrollment.graduated"
    ACADEMIC_ASSIGNMENT_CREATED = "academic_assignment.created"
    ACADEMIC_ASSIGNMENT_REPLACED = "academic_assignment.replaced"
    ACADEMIC_ASSIGNMENT_DEACTIVATED = "academic_assignment.deactivated"

    # Academic data (high sensitivity)
    GRADE_CREATED = "grade.created"
    GRADE_UPDATED = "grade.updated"
    GRADE_DELETED = "grade.deleted"
    ATTENDANCE_RECORDED = "attendance.recorded"
    ATTENDANCE_UPDATED = "attendance.updated"
    ACTIVITY_CREATED = "activity.created"
    ACTIVITY_UPDATED = "activity.updated"
    ACTIVITY_PUBLISHED = "activity.published"
    ACTIVITY_CLOSED = "activity.closed"
    ACTIVITY_DELETED = "activity.deleted"
    RESOURCE_CREATED = "resource.created"
    RESOURCE_DELETED = "resource.deleted"
    RESOURCE_DOWNLOADED = "resource.downloaded"
    SUBMISSION_CREATED = "submission.created"
    SUBMISSION_RETURNED = "submission.returned"
    SUBMISSION_RESUBMITTED = "submission.resubmitted"
    SUBMISSION_DOWNLOADED = "submission.downloaded"
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"
    PLAN_DELETED = "plan.deleted"

    # Virtual classroom & Real-Time Collaboration (Phase 4)
    MEETING_CREATED = "meeting.created"
    MEETING_LAUNCHED = "meeting.launched"
    MEETING_JOINED = "meeting.joined"
    MEETING_ENDED = "meeting.ended"
    RECORDING_SYNCED = "recording.synced"
    RECORDING_PUBLISHED = "recording.published"
    RECORDING_DELETED = "recording.deleted"
    RECORDING_ACCESSED = "recording.accessed"
    RECORDING_DOWNLOADED = "recording.downloaded"

    # Institutional Communications, News, and Coexistence (Phase 15)
    COMMUNICATION_CREATED = "communication.created"
    COMMUNICATION_UPDATED = "communication.updated"
    COMMUNICATION_PUBLISHED = "communication.published"
    COMMUNICATION_ARCHIVED = "communication.archived"
    COMMUNICATION_ACKNOWLEDGED = "communication.acknowledged"
    NEWS_CREATED = "news.created"
    NEWS_UPDATED = "news.updated"
    NEWS_PUBLISHED = "news.published"
    NEWS_ARCHIVED = "news.archived"
    INCIDENT_RECORDED = "incident.recorded"
    INCIDENT_UPDATED = "incident.updated"
    INCIDENT_CLOSED = "incident.closed"
    INCIDENT_VIEWED_BY_GUARDIAN = "incident.viewed_by_guardian"

    # SIEE Academic Evaluation, Period Closures & Promotions (Phase 16)
    SIEE_POLICY_CREATED = "siee_policy.created"
    SIEE_POLICY_UPDATED = "siee_policy.updated"
    PERIOD_GRADES_CONSOLIDATED = "period_grades.consolidated"
    PERIOD_GRADE_ADJUSTED = "period_grade.adjusted"
    RECOVERY_GRADE_RECORDED = "recovery_grade.recorded"
    PERIOD_CLOSED = "period.closed"
    PERIOD_UNLOCKED = "period.unlocked"
    REPORT_CARD_GENERATED = "report_card.generated"
    PROMOTION_COMMITTED = "promotion.committed"

    # Security events
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY_DETECTED = "security.suspicious_activity"
    PERMISSION_DENIED = "security.permission_denied"
    SECURITY_SUSPICIOUS_VELOCITY_DETECTED = "security.suspicious_velocity_detected"
    SECURITY_HIGH_RISK_ACCOUNT_ALERT = "security.high_risk_account_alert"
    SECURITY_REDIS_CLUSTER_OFFLINE = "security.redis_cluster_offline"
    SECURITY_RATE_LIMIT_DISABLED = "security.rate_limit_disabled"

    # Configuration / administrative
    CONFIG_CHANGED = "admin.config_changed"

    # Territorial Control Center (Phase NTA-05)
    TERRITORIAL_CONTROL_CENTER_ACCESSED = "territorial_control_center.accessed"


@dataclass
class AuditEvent:
    """
    Represents a single immutable audit event.

    Fields:
        event_type: The type of event that occurred.
        actor_id: The user ID who performed the action (None for system events).
        actor_ip: Client IP address at the time of the event.
        target_id: The ID of the affected resource (if applicable).
        target_type: The type name of the affected resource (e.g., "User", "Grade").
        institution_id: The institution context (for institutional isolation).
        metadata: Additional structured data about the event.
        occurred_at: When the event occurred (always UTC).
        correlation_id: Request correlation ID for log correlation.
        success: Whether the operation succeeded (False for failed attempts).
    """

    event_type: AuditEventType
    actor_ip: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_id: str | None = None
    target_id: str | None = None
    target_type: str | None = None
    institution_id: str | None = None
    correlation_id: str | None = None
    success: bool = True
    # Metadata must never contain passwords, tokens, or full PII
    metadata: dict[str, Any] = field(default_factory=dict)


class IAuditService(ABC):
    """
    Contract for the audit service.

    Phase 2 will implement this with a persistent database backend.
    Phase 1 uses NoOpAuditService.
    """

    @abstractmethod
    async def record(
        self,
        event: AuditEvent,
        session: Any | None = None,
    ) -> None:
        """
        Record an audit event.

        This method must be resilient — a failure to record an audit event
        should be logged as a critical error but must not crash the request.
        (The alternative — dropping the request — is worse than a lost audit record.)

        However: in Phase 2+, consider whether certain high-security events
        (e.g., grade changes) should fail the operation if audit recording fails.
        """
        raise NotImplementedError

    @abstractmethod
    async def record_many(
        self,
        events: list[AuditEvent],
        session: Any | None = None,
    ) -> None:
        """Record multiple audit events in a single batch."""
        raise NotImplementedError


class NoOpAuditService(IAuditService):
    """
    Phase 1 no-operation audit service.

    Does not persist any audit records.
    Logs at DEBUG level so audit events are visible in development.

    IMPORTANT: This must be replaced before any sensitive data is
    processed in staging or production environments.
    """

    async def record(
        self,
        event: AuditEvent,
        session: Any | None = None,
    ) -> None:
        """Log the audit event at DEBUG level (development only)."""
        _logger.debug(
            "AUDIT (no-op)",
            event_type=event.event_type,
            actor_id=event.actor_id,
            target_id=event.target_id,
            institution_id=event.institution_id,
            success=event.success,
        )

    async def record_many(
        self,
        events: list[AuditEvent],
        session: Any | None = None,
    ) -> None:
        """Log each audit event."""
        for event in events:
            await self.record(event)
