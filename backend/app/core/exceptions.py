"""
PEVN Backend — Domain Exceptions

Standard domain error classes representing business invariant violations
and academic integrity rules, preventing exposure of raw database errors.
All domain exceptions inherit from PEVNException for centralized HTTP mapping.
"""

from __future__ import annotations

from http import HTTPStatus

from app.exceptions.errors import PEVNException


class AcademicDomainError(PEVNException):
    """Base domain exception for academic management operations."""

    default_code = "ACADEMIC_DOMAIN_ERROR"
    default_status = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or self.default_code,
            status_code=status_code or self.default_status,
        )


class StudentAlreadyEnrolledActiveError(AcademicDomainError):
    """Raised when attempting to create a second ACTIVE enrollment in same year."""

    default_code = "STUDENT_ALREADY_ENROLLED_ACTIVE"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = (
            "El estudiante ya cuenta con una matrícula activa en este año lectivo."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class GroupCapacityExceededError(AcademicDomainError):
    """Raised when group enrollment exceeds the defined capacity limit."""

    default_code = "GROUP_CAPACITY_EXCEEDED"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = "El grupo ha alcanzado su límite de cupos disponibles.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class DuplicateActiveAssignmentError(AcademicDomainError):
    """Raised when assigning a second active teacher to same subject/group/year."""

    default_code = "DUPLICATE_ACTIVE_ASSIGNMENT"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = (
            "Ya existe un docente titular activo asignado a esta materia en el grupo."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class CrossTenantMismatchError(AcademicDomainError):
    """Raised when attempting cross-institution association."""

    default_code = "CROSS_TENANT_MISMATCH"
    default_status = HTTPStatus.FORBIDDEN

    def __init__(
        self,
        message: str = (
            "Conflicto de aislamiento: entidades de distintas instituciones."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class InvalidTransferError(AcademicDomainError):
    """Raised when a group transfer violates business rules."""

    default_code = "INVALID_TRANSFER"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = (
            "La transferencia no es válida para el estado de la matrícula."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class EnrollmentNotFoundError(AcademicDomainError):
    """Raised when an enrollment record is not found."""

    default_code = "ENROLLMENT_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Registro de matrícula no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class AcademicYearNotFoundError(AcademicDomainError):
    """Raised when an academic year record is not found."""

    default_code = "ACADEMIC_YEAR_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Año lectivo no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class AcademicYearLifecycleError(AcademicDomainError):
    """Raised when an invalid academic year transition is attempted."""

    default_code = "ACADEMIC_YEAR_LIFECYCLE_ERROR"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = "Transición de estado del año lectivo no permitida.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class GroupNotFoundError(AcademicDomainError):
    """Raised when a group record is not found."""

    default_code = "GROUP_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Grupo de clase no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class StudentNotFoundError(AcademicDomainError):
    """Raised when a student record is not found."""

    default_code = "STUDENT_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Perfil de estudiante no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class TeacherNotFoundError(AcademicDomainError):
    """Raised when a teacher record is not found."""

    default_code = "TEACHER_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Perfil docente no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class GuardianNotFoundError(AcademicDomainError):
    """Raised when a guardian record is not found."""

    default_code = "GUARDIAN_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Registro de acudiente no encontrado.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class AcademicAssignmentNotFoundError(AcademicDomainError):
    """Raised when an academic assignment record is not found."""

    default_code = "ACADEMIC_ASSIGNMENT_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Asignación académica no encontrada.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


# =============================================================================
# Virtual Classroom & Meeting Domain Exceptions (Phase 4)
# =============================================================================


class VirtualClassroomDomainError(PEVNException):
    """Base domain exception for Virtual Classroom operations."""

    default_code = "VIRTUAL_CLASSROOM_DOMAIN_ERROR"
    default_status = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or self.default_code,
            status_code=status_code or self.default_status,
        )


class VirtualClassroomNotFoundError(VirtualClassroomDomainError):
    """Raised when a virtual classroom is not found or belongs to another tenant."""

    default_code = "VIRTUAL_CLASSROOM_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Aula virtual no encontrada.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class VirtualClassroomLifecycleError(VirtualClassroomDomainError):
    """Raised when an invalid virtual classroom lifecycle transition is attempted."""

    default_code = "VIRTUAL_CLASSROOM_LIFECYCLE_ERROR"
    default_status = HTTPStatus.CONFLICT

    def __init__(
        self,
        message: str = "Transición de estado del aula virtual no permitida.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class UnauthorizedMeetingAccessError(VirtualClassroomDomainError):
    """Raised when an unauthorized user attempts to join or moderate a session."""

    default_code = "UNAUTHORIZED_MEETING_ACCESS"
    default_status = HTTPStatus.FORBIDDEN

    def __init__(
        self,
        message: str = (
            "No tiene autorización para ingresar o moderar esta aula virtual."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class RecordingNotFoundError(VirtualClassroomDomainError):
    """Raised when a session recording is not found or belongs to another tenant."""

    default_code = "RECORDING_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "Grabación de aula virtual no encontrada.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )
