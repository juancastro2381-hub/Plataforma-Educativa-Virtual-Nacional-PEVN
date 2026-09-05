"""
PEVN Backend — Teacher Domain Service

Authoritative business logic for educator professional profiles,
institutional binding, and group/subject assignment eligibility.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    TeacherNotFoundError,
)
from app.core.logging import get_logger
from app.models.role import Role, UserRole
from app.models.teacher import Teacher, TeacherContractType
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.academic import TeacherAccountStatusEnum, TeacherResponse
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

_logger = get_logger(__name__)


class TeacherService:
    """
    Domain service for Teacher professional profiles.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    @staticmethod
    def compute_account_status(teacher: Teacher) -> tuple[TeacherAccountStatusEnum, str | None, bool]:
        """
        Compute the dynamic account lifecycle state from Teacher -> User relationship.
        """
        user = teacher.user
        if not user:
            return TeacherAccountStatusEnum.SIN_CUENTA, None, False

        # Verify active 'teacher' role in user_roles
        has_teacher_role = any(
            ur.is_active and ur.role and ur.role.name == "teacher"
            for ur in user.user_roles
        )

        if not has_teacher_role:
            return TeacherAccountStatusEnum.SIN_CUENTA, user.email, False

        if user.is_active:
            return TeacherAccountStatusEnum.ACTIVA, user.email, True
        return TeacherAccountStatusEnum.INACTIVA, user.email, True

    def build_teacher_response(
        self,
        teacher: Teacher,
        reset_token: str | None = None,
    ) -> TeacherResponse:
        """
        Build TeacherResponse enriched with computed account_status.
        """
        account_status, account_email, has_account = self.compute_account_status(teacher)
        user_resp = UserResponse.model_validate(teacher.user) if teacher.user else None

        return TeacherResponse(
            id=teacher.id,
            user_id=teacher.user_id,
            institution_id=teacher.institution_id,
            specialty_area=teacher.specialty_area,
            contract_type=teacher.contract_type,
            escalafon_grade=teacher.escalafon_grade,
            user=user_resp,
            account_status=account_status,
            account_email=account_email,
            has_account=has_account,
            reset_token=reset_token,
            created_at=teacher.created_at,
            updated_at=teacher.updated_at,
        )

    async def create_teacher(
        self,
        *,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        specialty_area: str | None = None,
        contract_type: TeacherContractType = TeacherContractType.PROPIEDAD,
        escalafon_grade: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Teacher:
        """
        Create an educator profile 1:1 linked to an existing User account.
        """
        # 1. Validate User Tenant Ownership
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

        # 2. Check 1:1 User to Teacher Uniqueness
        existing = (
            await self._session.execute(
                select(Teacher).where(Teacher.user_id == user_id)
            )
        ).scalar_one_or_none()
        if existing:
            raise AcademicDomainError("El usuario ya posee un perfil docente asignado.")

        teacher = Teacher(
            user_id=user_id,
            institution_id=institution_id,
            specialty_area=specialty_area,
            contract_type=contract_type,
            escalafon_grade=escalafon_grade,
        )
        self._session.add(teacher)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.TEACHER_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(teacher.id),
                target_type="Teacher",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "user_id": str(user_id),
                    "contract_type": contract_type.value,
                },
            ),
            session=self._session,
        )

        return teacher

    async def get_teacher_by_id(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> Teacher:
        """
        Retrieve an educator profile validating tenant isolation.
        """
        stmt = (
            select(Teacher)
            .options(
                selectinload(Teacher.user)
                .selectinload(User.user_roles)
                .selectinload(UserRole.role)
            )
            .where(
                Teacher.id == teacher_id,
                Teacher.institution_id == institution_id,
            )
        )
        teacher = (await self._session.execute(stmt)).scalar_one_or_none()
        if not teacher:
            raise TeacherNotFoundError(
                f"Docente {teacher_id} no encontrado en la institución."
            )
        return teacher

    async def validate_teacher_eligibility(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> bool:
        """
        Verify that the educator is eligible for academic workload allocations.
        """
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        if not teacher.user or not teacher.user.is_active:
            raise AcademicDomainError(
                "La cuenta del docente se encuentra inactiva o deshabilitada."
            )
        return True

    async def provision_teacher_account(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
        email: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Teacher, TeacherAccountStatusEnum, str, str | None]:
        """
        Provision or activate login account credentials and assign canonical 'teacher' role.
        Preserves all existing Teacher records and academic data idempotently.
        """
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        user = teacher.user
        if not user:
            raise AcademicDomainError("El perfil docente no posee una cuenta base asociada.")

        # Update email if explicitly provided
        if email:
            clean_email = email.strip().lower()
            if clean_email != user.email:
                existing_email = (
                    await self._session.execute(
                        select(User).where(User.email == clean_email, User.id != user.id)
                    )
                ).scalar_one_or_none()
                if existing_email:
                    raise AcademicDomainError("El correo electrónico ya se encuentra registrado por otro usuario.")
                user.email = clean_email

        # Resolve canonical 'teacher' role with permissions loaded
        role_stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == "teacher")
        )
        role_obj = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role_obj:
            from app.services.rbac_bootstrap_service import RbacBootstrapService
            bootstrap = RbacBootstrapService(session=self._session)
            await bootstrap.seed_canonical_rbac_if_needed()
            role_obj = (await self._session.execute(role_stmt)).scalar_one()

        # Check or add UserRole
        user_role_stmt = select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role_obj.id,
        )
        existing_ur = (await self._session.execute(user_role_stmt)).scalar_one_or_none()
        if existing_ur:
            existing_ur.is_active = True
            existing_ur.role = role_obj
        else:
            new_ur = UserRole(
                user_id=user.id,
                role_id=role_obj.id,
                institution_id=institution_id,
                is_active=True,
            )
            new_ur.role = role_obj
            new_ur.user = user
            self._session.add(new_ur)
            if hasattr(user, "user_roles") and user.user_roles is not None:
                if new_ur not in user.user_roles:
                    user.user_roles.append(new_ur)

        # Set user active and force change password on first setup
        user.is_active = True
        user.must_change_password = True

        await self._session.flush()

        # Request single-use password reset / setup token
        reset_token = await auth_service.request_password_reset(
            db=self._session,
            email=user.email,
            client_ip=actor_ip,
            correlation_id=correlation_id,
        )

        # Emit audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.TEACHER_ACCOUNT_PROVISIONED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(teacher.id),
                target_type="Teacher",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "teacher_id": str(teacher.id),
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": "teacher",
                },
            ),
            session=self._session,
        )

        # Reload relationships
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        return teacher, TeacherAccountStatusEnum.ACTIVA, "Cuenta de acceso docente aprovisionada exitosamente.", reset_token

    async def update_teacher_account_status(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Teacher, TeacherAccountStatusEnum, str]:
        """
        Activate or deactivate a teacher's login account without deleting academic history.
        """
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        user = teacher.user
        if not user:
            raise AcademicDomainError("El docente no posee un usuario vinculado.")

        user.is_active = is_active

        if not is_active:
            # Revoke active refresh tokens for security
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user.id)
                .values(is_revoked=True)
            )
            event_type = AuditEventType.USER_DEACTIVATED
            target_status = TeacherAccountStatusEnum.INACTIVA
            msg = "Cuenta de acceso docente desactivada correctamente. Las sesiones activas han sido revocadas."
        else:
            event_type = AuditEventType.USER_ACTIVATED
            target_status = TeacherAccountStatusEnum.ACTIVA
            msg = "Cuenta de acceso docente reactivada correctamente."

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=event_type,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "teacher_id": str(teacher.id),
                    "user_id": str(user.id),
                    "is_active": is_active,
                },
            ),
            session=self._session,
        )

        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        return teacher, target_status, msg

    async def reset_teacher_password(
        self,
        *,
        teacher_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Teacher, str, str | None]:
        """
        Trigger secure password recovery for the teacher's institutional account.
        """
        teacher = await self.get_teacher_by_id(
            teacher_id=teacher_id,
            institution_id=institution_id,
        )
        user = teacher.user
        if not user or not user.is_active:
            raise AcademicDomainError("La cuenta del docente no existe o se encuentra inactiva.")

        reset_token = await auth_service.request_password_reset(
            db=self._session,
            email=user.email,
            client_ip=actor_ip,
            correlation_id=correlation_id,
        )

        return teacher, "Solicitud de restablecimiento de contraseña procesada exitosamente.", reset_token
