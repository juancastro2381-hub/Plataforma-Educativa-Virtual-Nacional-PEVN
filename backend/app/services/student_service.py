"""
PEVN Backend — Student Domain Service

Authoritative business logic for student profiles, SIMAT uniqueness,
socio-demographic inclusion metadata, and guardian associations.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.core.security.interfaces import AuthorizationContext
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.guardian import Guardian, StudentGuardian
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.academic import (
    StudentAccountStatusEnum,
    StudentResponse,
)
from app.schemas.user import UserResponse
from app.services.academic_scope_helper import (
    get_teacher_authorized_group_ids,
    is_directive_actor,
)
from app.services.auth_service import auth_service

if TYPE_CHECKING:
    from app.schemas.academic import StudentNewUserPayload

_logger = get_logger(__name__)

_MIN_STRATUM = 1
_MAX_STRATUM = 6


class StudentService:
    """
    Domain service for Student profile management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    @staticmethod
    def compute_account_status(student: Student) -> tuple[StudentAccountStatusEnum, str | None, bool]:
        """
        Compute the dynamic account lifecycle state from Student -> User relationship.
        """
        user = student.user
        if not user:
            return StudentAccountStatusEnum.SIN_CUENTA, None, False

        # Verify active 'student' role in user_roles
        has_student_role = any(
            ur.is_active and ur.role and ur.role.name == "student"
            for ur in (user.user_roles or [])
        )

        if not has_student_role:
            return StudentAccountStatusEnum.SIN_CUENTA, user.email, False

        if user.is_active:
            return StudentAccountStatusEnum.ACTIVA, user.email, True
        return StudentAccountStatusEnum.INACTIVA, user.email, True

    def build_student_response(
        self,
        student: Student,
    ) -> StudentResponse:
        """
        Build StudentResponse enriched with computed account_status.
        (Note: reset_token is strictly omitted from general responses for security).
        """
        account_status, account_email, has_account = self.compute_account_status(student)
        user_resp = UserResponse.model_validate(student.user) if student.user else None

        return StudentResponse(
            id=student.id,
            user_id=student.user_id,
            institution_id=student.institution_id,
            code_simat=student.code_simat,
            birth_date=student.birth_date,
            gender=student.gender,
            blood_type=student.blood_type,
            stratum=student.stratum,
            eps_health_provider=student.eps_health_provider,
            has_disability=student.has_disability,
            disability_type=student.disability_type,
            user=user_resp,
            account_status=account_status,
            account_email=account_email,
            has_account=has_account,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )

    async def create_student(
        self,
        *,
        institution_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        new_user: StudentNewUserPayload | None = None,
        code_simat: str,
        birth_date: date,
        gender: StudentGender = StudentGender.M,
        blood_type: str | None = None,
        stratum: int | None = None,
        eps_health_provider: str | None = None,
        has_disability: bool = False,
        disability_type: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Student:
        """
        Create a student profile linked 1:1 to an existing User account or by provisioning a new User on the fly.
        """
        # 1. Validate Mutually Exclusive Provisioning Mode
        if bool(user_id) == bool(new_user):
            raise AcademicDomainError(
                "Debe proporcionar exactamente uno: 'user_id' (usuario existente) o 'new_user' (nuevo estudiante)."
            )

        # 2. Validate Stratum Range
        if stratum is not None and not (_MIN_STRATUM <= stratum <= _MAX_STRATUM):
            raise AcademicDomainError(
                "El estrato socioeconómico debe estar entre 1 y 6."
            )

        # 3. Check SIMAT Uniqueness Pre-emptively before User Provisioning
        dup_simat = (
            await self._session.execute(
                select(Student).where(Student.code_simat == code_simat)
            )
        ).scalar_one_or_none()
        if dup_simat:
            raise AcademicDomainError(
                f"El código SIMAT '{code_simat}' ya se encuentra registrado."
            )

        # 4. Resolve / Provision User ID
        resolved_user_id: uuid.UUID
        if new_user:
            from app.services.user_service import UserService

            user_service = UserService(session=self._session, audit=self._audit)
            created_user = await user_service.provision_institutional_user(
                institution_id=institution_id,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                document_type=new_user.document_type,
                document_number=new_user.document_number,
                email=new_user.email,
                role_name="student",
                actor_id=actor_id,
                actor_ip=actor_ip,
                correlation_id=correlation_id,
            )
            resolved_user_id = created_user.id
        else:
            assert user_id is not None
            # Validate User Tenant Ownership
            user = (
                await self._session.execute(
                    select(User).where(
                        User.id == user_id,
                        User.institution_id == institution_id,
                    )
                )
            ).scalar_one_or_none()
            if not user:
                raise CrossTenantMismatchError(
                    "La cuenta de usuario no pertenece a la institución especificada."
                )
            resolved_user_id = user_id

        # 5. Check 1:1 User to Student Uniqueness
        existing_profile = (
            await self._session.execute(
                select(Student).where(Student.user_id == resolved_user_id)
            )
        ).scalar_one_or_none()
        if existing_profile:
            raise AcademicDomainError(
                "El usuario ya posee un perfil de estudiante asignado."
            )

        student = Student(
            user_id=resolved_user_id,
            institution_id=institution_id,
            code_simat=code_simat,
            birth_date=birth_date,
            gender=gender,
            blood_type=blood_type,
            stratum=stratum,
            eps_health_provider=eps_health_provider,
            has_disability=has_disability,
            disability_type=disability_type,
        )
        self._session.add(student)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.STUDENT_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student.id),
                target_type="Student",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "user_id": str(resolved_user_id),
                    "code_simat": code_simat,
                    "is_new_user": bool(new_user),
                },
            ),
            session=self._session,
        )

        # Reload student with eager-loaded user and user_roles
        return await self.get_student_by_id(
            student_id=student.id,
            institution_id=institution_id,
        )

    async def list_students(
        self,
        *,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
        code_simat: str | None = None,
    ) -> list[Student]:
        """
        List students within the institution.
        If caller is a Teacher without directive roles, strictly restricts results
        to students actively enrolled in groups within the teacher's authorized academic scope.
        """
        is_directive = is_directive_actor(auth, user=user)

        user_load = selectinload(Student.user).selectinload(User.user_roles).selectinload(UserRole.role)

        if is_directive:
            query = (
                select(Student)
                .options(user_load)
                .where(Student.institution_id == institution_id)
            )
            if code_simat:
                query = query.where(Student.code_simat.ilike(f"%{code_simat}%"))
            query = query.order_by(Student.code_simat.asc())
            result = await self._session.execute(query)
            return list(result.scalars().all())

        # Teacher (or non-directive) role: scope by authorized groups
        if not user:
            return []

        authorized_group_ids = await get_teacher_authorized_group_ids(
            self._session,
            user_id=user.id,
            institution_id=institution_id,
        )
        if not authorized_group_ids:
            return []

        query = (
            select(Student)
            .distinct()
            .join(Enrollment, Enrollment.student_id == Student.id)
            .options(user_load)
            .where(
                Student.institution_id == institution_id,
                Enrollment.group_id.in_(authorized_group_ids),
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if code_simat:
            query = query.where(Student.code_simat.ilike(f"%{code_simat}%"))
        query = query.order_by(Student.code_simat.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_student_by_id(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
    ) -> Student:
        """
        Retrieve a student validating tenant isolation and teacher academic scope.
        """
        is_directive = is_directive_actor(auth, user=user)
        user_load = selectinload(Student.user).selectinload(User.user_roles).selectinload(UserRole.role)

        if is_directive:
            stmt = (
                select(Student)
                .options(user_load)
                .where(
                    Student.id == student_id,
                    Student.institution_id == institution_id,
                )
            )
            student = (await self._session.execute(stmt)).scalar_one_or_none()
            if not student:
                raise StudentNotFoundError(
                    f"Estudiante {student_id} no encontrado en la institución."
                )
            return student

        # Teacher (or non-directive) role: must belong to teacher's authorized groups
        if not user:
            raise StudentNotFoundError(f"Estudiante {student_id} no encontrado.")

        authorized_group_ids = await get_teacher_authorized_group_ids(
            self._session,
            user_id=user.id,
            institution_id=institution_id,
        )
        if not authorized_group_ids:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en su ámbito académico."
            )

        stmt = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .options(user_load)
            .where(
                Student.id == student_id,
                Student.institution_id == institution_id,
                Enrollment.group_id.in_(authorized_group_ids),
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        student = (await self._session.execute(stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en su ámbito académico."
            )
        return student

    async def get_student_by_simat(
        self,
        *,
        code_simat: str,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
    ) -> Student:
        """
        Retrieve a student by national SIMAT code validating tenant isolation and scope.
        """
        is_directive = is_directive_actor(auth, user=user)
        user_load = selectinload(Student.user).selectinload(User.user_roles).selectinload(UserRole.role)

        if is_directive:
            stmt = (
                select(Student)
                .options(user_load)
                .where(
                    Student.code_simat == code_simat,
                    Student.institution_id == institution_id,
                )
            )
            student = (await self._session.execute(stmt)).scalar_one_or_none()
            if not student:
                raise StudentNotFoundError(
                    f"Estudiante con SIMAT '{code_simat}' no encontrado."
                )
            return student

        # Teacher (or non-directive) role
        if not user:
            raise StudentNotFoundError(f"Estudiante con SIMAT '{code_simat}' no encontrado.")

        authorized_group_ids = await get_teacher_authorized_group_ids(
            self._session,
            user_id=user.id,
            institution_id=institution_id,
        )
        if not authorized_group_ids:
            raise StudentNotFoundError(
                f"Estudiante con SIMAT '{code_simat}' no encontrado en su ámbito académico."
            )

        stmt = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .options(user_load)
            .where(
                Student.code_simat == code_simat,
                Student.institution_id == institution_id,
                Enrollment.group_id.in_(authorized_group_ids),
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        student = (await self._session.execute(stmt)).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante con SIMAT '{code_simat}' no encontrado en su ámbito académico."
            )
        return student

    async def provision_student_account(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        email: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Student, StudentAccountStatusEnum, str, str | None]:
        """
        Provision or activate login account credentials and assign canonical 'student' role.
        """
        student = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )

        user = student.user
        if not user:
            raise AcademicDomainError("El estudiante no posee un usuario vinculado.")

        # Update email if explicitly provided
        if email and email.strip().lower() != user.email:
            clean_email = email.strip().lower()
            existing_email = (
                await self._session.execute(
                    select(User).where(User.email == clean_email, User.id != user.id)
                )
            ).scalar_one_or_none()
            if existing_email:
                raise AcademicDomainError("El correo electrónico ya se encuentra registrado por otro usuario.")
            user.email = clean_email

        # Resolve canonical student role
        role_stmt = select(Role).where(Role.name == "student")
        role_obj = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role_obj:
            from app.services.rbac_bootstrap_service import RbacBootstrapService
            bootstrap = RbacBootstrapService(session=self._session)
            await bootstrap.seed_canonical_rbac_if_needed()
            role_obj = (await self._session.execute(role_stmt)).scalar_one()

        ur_stmt = select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role_obj.id,
        )
        existing_ur = (await self._session.execute(ur_stmt)).scalar_one_or_none()
        if existing_ur:
            existing_ur.is_active = True
        else:
            self._session.add(
                UserRole(
                    user_id=user.id,
                    role_id=role_obj.id,
                    institution_id=institution_id,
                    is_active=True,
                )
            )

        user.is_active = True
        user.must_change_password = True

        await self._session.flush()

        # Request password setup / reset token
        reset_token = await auth_service.request_password_reset(
            db=self._session,
            email=user.email,
            client_ip=actor_ip,
            correlation_id=correlation_id,
        )

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.STUDENT_ACCOUNT_PROVISIONED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student.id),
                target_type="Student",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(student.id),
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": "student",
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )
        return reloaded, StudentAccountStatusEnum.ACTIVA, "Cuenta de acceso para estudiante aprovisionada exitosamente.", reset_token

    async def update_student_account_status(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Student, StudentAccountStatusEnum, str]:
        """
        Activate or deactivate a student's login account without deleting academic history.
        """
        student = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )
        user = student.user
        if not user:
            raise AcademicDomainError("El estudiante no posee un usuario vinculado.")

        user.is_active = is_active

        if not is_active:
            # Revoke active refresh tokens for security
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user.id)
                .values(is_revoked=True)
            )

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.USER_ACTIVATED if is_active else AuditEventType.USER_DEACTIVATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(student.id),
                    "user_id": str(user.id),
                    "is_active": is_active,
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )
        status_enum = StudentAccountStatusEnum.ACTIVA if is_active else StudentAccountStatusEnum.INACTIVA
        message = "Cuenta de acceso del estudiante habilitada exitosamente." if is_active else "Cuenta de acceso del estudiante deshabilitada exitosamente."
        return reloaded, status_enum, message

    async def reset_student_password(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Student, StudentAccountStatusEnum, str, str | None]:
        """
        Request an administrative password reset token for a student.
        """
        student = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )
        user = student.user
        if not user:
            raise AcademicDomainError("El estudiante no posee una cuenta de usuario vinculada.")
        if not user.is_active:
            raise AcademicDomainError("No se puede restablecer la contraseña de una cuenta inactiva.")

        reset_token = await auth_service.request_password_reset(
            db=self._session,
            email=user.email,
            client_ip=actor_ip,
            correlation_id=correlation_id,
        )

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.USER_PASSWORD_RESET_REQUESTED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "student_id": str(student.id),
                    "user_id": str(user.id),
                    "email": user.email,
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
        )
        return reloaded, StudentAccountStatusEnum.ACTIVA, "Token de restablecimiento de contraseña generado exitosamente.", reset_token

    async def get_student_guardians(
        self,
        *,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        user: User | None = None,
        auth: AuthorizationContext | None = None,
    ) -> list[StudentGuardian]:
        """
        Retrieve all guardian associations for a student.
        """
        # Ensure student belongs to institution and scope
        await self.get_student_by_id(
            student_id=student_id,
            institution_id=institution_id,
            user=user,
            auth=auth,
        )

        stmt = (
            select(StudentGuardian)
            .options(
                selectinload(StudentGuardian.guardian).selectinload(Guardian.user).selectinload(User.user_roles).selectinload(UserRole.role)
            )
            .where(StudentGuardian.student_id == student_id)
        )
        return list((await self._session.execute(stmt)).scalars().all())
