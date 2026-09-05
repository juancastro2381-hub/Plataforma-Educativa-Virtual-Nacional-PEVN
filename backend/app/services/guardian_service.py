"""
PEVN Backend — Guardian Domain Service

Authoritative business logic for legal guardians and parent actors (Acudientes),
supporting decoupled national document identification per [OPEN-DECISION-3A-01],
account provisioning, lifecycle management, and bidirectional family associations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    AcademicDomainError,
    CrossTenantMismatchError,
    GuardianNotFoundError,
    StudentNotFoundError,
)
from app.core.logging import get_logger
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.role import Role, UserRole
from app.models.student import Student
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.schemas.academic import (
    GuardianAccountStatusEnum,
    GuardianResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

if TYPE_CHECKING:
    from app.schemas.academic import GuardianNewUserPayload

_logger = get_logger(__name__)


class GuardianService:
    """
    Domain service for Guardian and Student-Guardian associations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    @staticmethod
    def compute_account_status(guardian: Guardian) -> tuple[GuardianAccountStatusEnum, str | None, bool]:
        """
        Compute the dynamic account lifecycle state from Guardian -> User relationship.
        """
        user = guardian.user
        if not user:
            return GuardianAccountStatusEnum.SIN_CUENTA, None, False

        # Verify active 'guardian' role in user_roles
        has_guardian_role = any(
            ur.is_active and ur.role and ur.role.name == "guardian"
            for ur in (user.user_roles or [])
        )

        if not has_guardian_role:
            return GuardianAccountStatusEnum.SIN_CUENTA, user.email, False

        if user.is_active:
            return GuardianAccountStatusEnum.ACTIVA, user.email, True
        return GuardianAccountStatusEnum.INACTIVA, user.email, True

    def build_guardian_response(
        self,
        guardian: Guardian,
    ) -> GuardianResponse:
        """
        Build GuardianResponse enriched with computed account_status.
        (Note: reset_token is strictly omitted from general responses for security).
        """
        account_status, account_email, has_account = self.compute_account_status(guardian)
        user_resp = UserResponse.model_validate(guardian.user) if guardian.user else None

        return GuardianResponse(
            id=guardian.id,
            institution_id=guardian.institution_id,
            first_name=guardian.first_name,
            last_name=guardian.last_name,
            document_type=guardian.document_type,
            document_number=guardian.document_number,
            phone=guardian.phone,
            email=guardian.email,
            address=guardian.address,
            relationship_type=guardian.relationship_type,
            user_id=guardian.user_id,
            user=user_resp,
            account_status=account_status,
            account_email=account_email,
            has_account=has_account,
            created_at=guardian.created_at,
            updated_at=guardian.updated_at,
        )

    async def create_guardian(
        self,
        *,
        institution_id: uuid.UUID,
        first_name: str,
        last_name: str,
        document_type: DocumentType,
        document_number: str,
        phone: str,
        email: str | None = None,
        address: str | None = None,
        relationship_type: GuardianRelationshipType = (GuardianRelationshipType.MADRE),
        user_id: uuid.UUID | None = None,
        new_user: GuardianNewUserPayload | None = None,
        provision_account: bool = False,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> tuple[Guardian, str | None]:
        """
        Create a guardian record anchored to the specified institution.
        Supports linking an existing User or provisioning a new User on the fly.
        Returns a tuple of (Guardian, reset_token | None).
        """
        # 1. Mutually exclusive validation if both user_id and new_user are provided
        if user_id is not None and new_user is not None:
            raise AcademicDomainError(
                "Debe proporcionar únicamente uno: 'user_id' (usuario existente) o 'new_user' (nuevo usuario)."
            )

        # 2. Check document uniqueness within the institution
        dup_stmt = select(Guardian).where(
            Guardian.institution_id == institution_id,
            Guardian.document_type == document_type,
            Guardian.document_number == document_number,
        )
        existing = (await self._session.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise AcademicDomainError(
                "Ya existe un acudiente registrado con documento "
                f"{document_type.value} {document_number} en esta institución."
            )

        resolved_user_id: uuid.UUID | None = None
        reset_token: str | None = None

        # 3. Resolve User ID based on mode
        if new_user is not None:
            from app.services.user_service import UserService

            user_service = UserService(session=self._session, audit=self._audit)
            created_user = await user_service.provision_institutional_user(
                institution_id=institution_id,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                document_type=new_user.document_type,
                document_number=new_user.document_number,
                email=new_user.email,
                role_name="guardian",
                actor_id=actor_id,
                actor_ip=actor_ip,
                correlation_id=correlation_id,
            )
            resolved_user_id = created_user.id
            if provision_account:
                reset_token = await auth_service.request_password_reset(
                    db=self._session,
                    email=created_user.email,
                    client_ip=actor_ip,
                    correlation_id=correlation_id,
                )
        elif user_id is not None:
            # Validate existing User Tenant Ownership
            user_stmt = select(User).where(
                User.id == user_id,
                User.institution_id == institution_id,
            )
            user = (await self._session.execute(user_stmt)).scalar_one_or_none()
            if not user:
                raise CrossTenantMismatchError(
                    "La cuenta de usuario no pertenece a la institución especificada."
                )

            # Check 1:1 uniqueness
            existing_user_guardian = (
                await self._session.execute(
                    select(Guardian).where(Guardian.user_id == user_id)
                )
            ).scalar_one_or_none()
            if existing_user_guardian:
                raise AcademicDomainError("El usuario ya posee un perfil de acudiente vinculado.")

            resolved_user_id = user_id

            # Ensure canonical 'guardian' role is assigned
            role_stmt = select(Role).where(Role.name == "guardian")
            role_obj = (await self._session.execute(role_stmt)).scalar_one_or_none()
            if not role_obj:
                from app.services.rbac_bootstrap_service import RbacBootstrapService
                bootstrap = RbacBootstrapService(session=self._session)
                await bootstrap.seed_canonical_rbac_if_needed()
                role_obj = (await self._session.execute(role_stmt)).scalar_one()

            ur_stmt = select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_obj.id,
            )
            existing_ur = (await self._session.execute(ur_stmt)).scalar_one_or_none()
            if existing_ur:
                existing_ur.is_active = True
            else:
                new_ur = UserRole(
                    user_id=user_id,
                    role_id=role_obj.id,
                    institution_id=institution_id,
                    is_active=True,
                )
                self._session.add(new_ur)

            if provision_account:
                reset_token = await auth_service.request_password_reset(
                    db=self._session,
                    email=user.email,
                    client_ip=actor_ip,
                    correlation_id=correlation_id,
                )

        guardian = Guardian(
            institution_id=institution_id,
            first_name=first_name,
            last_name=last_name,
            document_type=document_type,
            document_number=document_number,
            phone=phone,
            email=email or (new_user.email if new_user else None),
            address=address,
            relationship_type=relationship_type,
            user_id=resolved_user_id,
        )
        self._session.add(guardian)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(guardian.id),
                target_type="Guardian",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "document_type": document_type.value,
                    "document_number": document_number,
                    "institution_id": str(institution_id),
                    "user_id": str(resolved_user_id) if resolved_user_id else None,
                },
            ),
            session=self._session,
        )

        # If a user was linked, refresh their user_roles to avoid stale identity-map cache.
        if resolved_user_id is not None:
            # Build a fresh selectinload of User.user_roles for the linked user.
            fresh_user_stmt = (
                select(User)
                .options(
                    selectinload(User.user_roles).selectinload(UserRole.role)
                )
                .execution_options(populate_existing=True)
                .where(User.id == resolved_user_id)
            )
            await self._session.execute(fresh_user_stmt)

        # Reload relationships with populate_existing=True to pick up freshly-assigned roles.
        reloaded = await self.get_guardian_by_id(
            guardian_id=guardian.id,
            institution_id=institution_id,
        )
        return reloaded, reset_token

    async def list_guardians(
        self,
        *,
        institution_id: uuid.UUID,
        document_number: str | None = None,
    ) -> list[Guardian]:
        """
        List guardians belonging strictly to the institution with eager loaded user.
        """
        query = (
            select(Guardian)
            .options(
                selectinload(Guardian.user).selectinload(User.user_roles).selectinload(UserRole.role)
            )
            .where(Guardian.institution_id == institution_id)
        )
        if document_number:
            query = query.where(Guardian.document_number.ilike(f"%{document_number}%"))

        query = query.order_by(Guardian.last_name.asc(), Guardian.first_name.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_guardian_by_id(
        self,
        *,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID | None = None,
    ) -> Guardian:
        """
        Retrieve a guardian by primary key ID, enforcing tenant isolation boundary.
        """
        stmt = (
            select(Guardian)
            .options(
                selectinload(Guardian.user).selectinload(User.user_roles).selectinload(UserRole.role)
            )
            .execution_options(populate_existing=True)
            .where(Guardian.id == guardian_id)
        )
        if institution_id is not None:
            stmt = stmt.where(Guardian.institution_id == institution_id)
        guardian = (await self._session.execute(stmt)).scalar_one_or_none()
        if not guardian:
            raise GuardianNotFoundError(f"Acudiente {guardian_id} no encontrado.")
        return guardian

    async def provision_guardian_account(
        self,
        *,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        email: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Guardian, GuardianAccountStatusEnum, str, str | None]:
        """
        Provision or activate login account credentials and assign canonical 'guardian' role.
        """
        guardian = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )

        user = guardian.user
        target_email = email.strip().lower() if email else (guardian.email or f"{guardian.document_number.lower()}@acudiente.pevn.edu.co")

        if not user:
            from app.services.user_service import UserService

            user_service = UserService(session=self._session, audit=self._audit)
            user = await user_service.provision_institutional_user(
                institution_id=institution_id,
                first_name=guardian.first_name,
                last_name=guardian.last_name,
                document_type=guardian.document_type,
                document_number=guardian.document_number,
                email=target_email,
                role_name="guardian",
                actor_id=actor_id,
                actor_ip=actor_ip,
                correlation_id=correlation_id,
            )
            guardian.user_id = user.id
            guardian.email = target_email
        else:
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
                guardian.email = clean_email

            # Resolve canonical guardian role
            role_stmt = select(Role).where(Role.name == "guardian")
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
                event_type=AuditEventType.GUARDIAN_ACCOUNT_PROVISIONED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(guardian.id),
                target_type="Guardian",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_id": str(guardian.id),
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": "guardian",
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )
        return reloaded, GuardianAccountStatusEnum.ACTIVA, "Cuenta de acceso para acudiente aprovisionada exitosamente.", reset_token

    async def update_guardian_account_status(
        self,
        *,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Guardian, GuardianAccountStatusEnum, str]:
        """
        Activate or deactivate a guardian's login account without deleting civil or family history.
        """
        guardian = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )
        user = guardian.user
        if not user:
            raise AcademicDomainError("El acudiente no posee una cuenta de usuario vinculada.")

        user.is_active = is_active

        if not is_active:
            # Revoke refresh tokens on deactivation
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
                    "guardian_id": str(guardian.id),
                    "user_id": str(user.id),
                    "is_active": is_active,
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )
        status_enum = GuardianAccountStatusEnum.ACTIVA if is_active else GuardianAccountStatusEnum.INACTIVA
        message = "Cuenta de acudiente habilitada exitosamente." if is_active else "Cuenta de acudiente deshabilitada exitosamente."
        return reloaded, status_enum, message

    async def reset_guardian_password(
        self,
        *,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> tuple[Guardian, GuardianAccountStatusEnum, str, str | None]:
        """
        Request an administrative password reset token for a guardian.
        """
        guardian = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )
        user = guardian.user
        if not user:
            raise AcademicDomainError("El acudiente no posee una cuenta de usuario vinculada.")
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
                    "guardian_id": str(guardian.id),
                    "user_id": str(user.id),
                    "email": user.email,
                },
            ),
            session=self._session,
        )

        reloaded = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )
        return reloaded, GuardianAccountStatusEnum.ACTIVA, "Token de restablecimiento de contraseña generado exitosamente.", reset_token

    async def associate_guardian_to_student(
        self,
        *,
        student_id: uuid.UUID,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        relationship_type: GuardianRelationshipType = (GuardianRelationshipType.PADRE),
        is_primary_contact: bool = False,
        is_authorized_pickup: bool = True,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> StudentGuardian:
        """
        Associate a guardian to a student, validating student and guardian tenant boundary.
        """
        # 1. Validate Student Tenant Ownership
        student = (
            await self._session.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en la institución."
            )

        # 2. Validate Guardian exists in this institution (anti-IDOR 404 on mismatch)
        guardian = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )

        # 3. Check for existing association
        dup_stmt = select(StudentGuardian).where(
            StudentGuardian.student_id == student_id,
            StudentGuardian.guardian_id == guardian_id,
        )
        if (await self._session.execute(dup_stmt)).scalar_one_or_none():
            raise AcademicDomainError(
                "El acudiente ya se encuentra vinculado a este estudiante."
            )

        assoc = StudentGuardian(
            student_id=student_id,
            guardian_id=guardian_id,
            relationship_type=relationship_type,
            is_primary_contact=is_primary_contact,
            is_authorized_pickup=is_authorized_pickup,
        )
        self._session.add(assoc)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_ASSOCIATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student_id),
                target_type="StudentGuardian",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_id": str(guardian.id),
                    "student_id": str(student.id),
                    "relationship_type": relationship_type.value,
                },
            ),
            session=self._session,
        )

        return assoc

    async def dissociate_guardian_from_student(
        self,
        *,
        student_id: uuid.UUID,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """
        Safely unlink a guardian from a student, verifying tenant ownership and emitting audit event.
        Does not delete Student, Guardian, or User entities.
        """
        # Validate Student in institution
        student = (
            await self._session.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.institution_id == institution_id,
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise StudentNotFoundError(
                f"Estudiante {student_id} no encontrado en la institución."
            )

        # Validate Guardian in institution
        guardian = await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )

        stmt = select(StudentGuardian).where(
            StudentGuardian.student_id == student_id,
            StudentGuardian.guardian_id == guardian_id,
        )
        assoc = (await self._session.execute(stmt)).scalar_one_or_none()
        if not assoc:
            raise AcademicDomainError(
                "La vinculación entre el acudiente y el estudiante no existe."
            )

        await self._session.delete(assoc)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.GUARDIAN_DISSOCIATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(student_id),
                target_type="StudentGuardian",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "guardian_id": str(guardian.id),
                    "student_id": str(student.id),
                },
            ),
            session=self._session,
        )

        return {"message": "Vinculación entre acudiente y estudiante eliminada exitosamente."}

    async def get_guardian_students(
        self,
        *,
        guardian_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> list[StudentGuardian]:
        """
        Retrieve all student associations for a guardian adhering to tenant isolation.
        """
        # Validate Guardian in institution (anti-IDOR 404 on mismatch)
        await self.get_guardian_by_id(
            guardian_id=guardian_id,
            institution_id=institution_id,
        )

        stmt = (
            select(StudentGuardian)
            .join(Student, Student.id == StudentGuardian.student_id)
            .options(
                selectinload(StudentGuardian.student).selectinload(Student.user).selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(StudentGuardian.guardian).selectinload(Guardian.user).selectinload(User.user_roles).selectinload(UserRole.role),
            )
            .where(
                StudentGuardian.guardian_id == guardian_id,
                Student.institution_id == institution_id,
            )
        )
        return list((await self._session.execute(stmt)).scalars().all())


