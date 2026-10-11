"""
PEVN Backend — Rector Onboarding Domain Service

Handles cryptographically secure tokenized invitations, zero-knowledge credential
onboarding, single-use state transitions, replay attack prevention, and automatic
activation of institutional Rector accounts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import generate_raw_token, hash_token
from app.exceptions.errors import (
    ConflictError,
    NotFoundError,
    PEVNException,
    UnprocessableEntityError,
)
from app.models.institution import Institution
from app.models.invitation import RectorInvitation
from app.models.role import Role, UserRole
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.services.email_service import EmailDeliveryStatus, EmailService

_logger = get_logger(__name__)


class RectorInviteResult(tuple):
    """Backwards-compatible tuple for (invitation, raw_token) with delivery attributes."""

    def __new__(
        cls,
        invitation: RectorInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
    ) -> RectorInviteResult:
        return super().__new__(cls, (invitation, raw_token))

    def __init__(
        self,
        invitation: RectorInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
    ) -> None:
        self.invitation = invitation
        self.raw_token = raw_token
        self.delivery_status = delivery_status
        self.activation_url = activation_url


def _mask_email(email: str) -> str:
    """Mask email for privacy in public verification endpoint."""
    if "@" not in email:
        return email
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "***"
    else:
        masked_local = local_part[0] + "***" + local_part[-1]
    return f"{masked_local}@{domain}"


class RectorOnboardingService:
    """
    Service managing the secure onboarding workflow for institutional Rectors.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_svc: audit_service.__class__ = audit_service,
        email_service: EmailService | None = None,
    ) -> None:
        self._session = session
        self._audit = audit_svc
        self._email = email_service or EmailService()

    async def invite_rector(
        self,
        *,
        institution_id: uuid.UUID,
        first_name: str,
        last_name: str,
        document_type: DocumentType,
        document_number: str,
        email: str,
        phone_number: str | None = None,
        invited_by_id: uuid.UUID | str,
        invited_by_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
        authority_level: str = "normal_municipal",
    ) -> tuple[RectorInvitation, str]:
        """
        Create a pre-registered inactive Rector account and issue a single-use invitation.

        Returns:
            Tuple of (RectorInvitation entity, raw_invitation_token).
            The raw token is returned ONLY for delivery and NEVER persisted.
        """
        cleaned_email = email.strip().lower()
        cleaned_doc = document_number.strip()

        # 1. Verify Institution exists and is active
        inst_stmt = select(Institution).where(Institution.id == institution_id)
        inst = (await self._session.execute(inst_stmt)).scalar_one_or_none()
        if not inst:
            raise NotFoundError(
                f"Institución educativa {institution_id} no encontrada.",
                code="INSTITUTION_NOT_FOUND",
            )
        if not inst.is_active:
            raise ConflictError(
                "No se pueden emitir invitaciones para una institución inactiva o suspendida.",
                code="INSTITUTION_INACTIVE",
            )

        # 2. Verify Rector Role exists in database (auto-bootstrapping if role catalog is unseeded)
        role_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
        rector_role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not rector_role:
            from app.services.rbac_bootstrap_service import RbacBootstrapService
            bootstrap_svc = RbacBootstrapService(session=self._session)
            await bootstrap_svc.seed_canonical_rbac_if_needed()
            rector_role = (await self._session.execute(role_stmt)).scalar_one_or_none()

        if not rector_role:
            raise NotFoundError(
                "Rol canónico 'rector' no encontrado en el catálogo de roles.",
                code="ROLE_NOT_FOUND",
            )

        # 3. Check if institution already has an active Rector
        active_rector_stmt = (
            select(UserRole)
            .where(
                UserRole.institution_id == institution_id,
                UserRole.role_id == rector_role.id,
                UserRole.is_active == True,  # noqa: E712
            )
        )
        existing_active = (await self._session.execute(active_rector_stmt)).scalar_one_or_none()
        if existing_active:
            raise ConflictError(
                "La institución educativa ya cuenta con un Rector titular activo. "
                "Debe revocar o reemplazar al titular antes de invitar a uno nuevo.",
                code="RECTOR_ALREADY_EXISTS",
            )

        # 4. Check user identity uniqueness
        user_by_doc = (
            await self._session.execute(
                select(User).where(
                    User.document_type == document_type,
                    User.document_number == cleaned_doc,
                )
            )
        ).scalar_one_or_none()

        user_by_email = (
            await self._session.execute(select(User).where(User.email == cleaned_email))
        ).scalar_one_or_none()

        if user_by_doc and user_by_email and user_by_doc.id != user_by_email.id:
            raise ConflictError(
                "El documento de identidad y el correo pertenecen a cuentas de usuario distintas.",
                code="IDENTITY_CONFLICT",
            )

        target_user = user_by_doc or user_by_email

        if target_user:
            if target_user.institution_id and target_user.institution_id != institution_id:
                raise ConflictError(
                    "El usuario ya se encuentra registrado con una afiliación institucional diferente.",
                    code="CROSS_TENANT_AFFILIATION_CONFLICT",
                )
            # Update user affiliation to this institution if pending
            target_user.institution_id = institution_id
            target_user.first_name = first_name.strip()
            target_user.last_name = last_name.strip()
        else:
            # Create pre-registered inactive user with unguessable random initial hash
            unusable_hash = password_hasher.hash(generate_raw_token(32))
            target_user = User(
                institution_id=institution_id,
                email=cleaned_email,
                username=cleaned_email,
                hashed_password=unusable_hash,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                document_type=document_type,
                document_number=cleaned_doc,
                is_active=False,
                is_verified=False,
                must_change_password=True,
            )
            self._session.add(target_user)
            await self._session.flush()

        # 5. Ensure UserRole association exists (inactive until redeemed)
        user_role_stmt = select(UserRole).where(
            UserRole.user_id == target_user.id,
            UserRole.role_id == rector_role.id,
            UserRole.institution_id == institution_id,
        )
        existing_ur = (await self._session.execute(user_role_stmt)).scalar_one_or_none()
        if not existing_ur:
            ur = UserRole(
                user_id=target_user.id,
                role_id=rector_role.id,
                institution_id=institution_id,
                is_active=False,
            )
            self._session.add(ur)
            await self._session.flush()

        # 6. Revoke any prior active invitations for this user in this institution
        await self._session.execute(
            update(RectorInvitation)
            .where(
                RectorInvitation.user_id == target_user.id,
                RectorInvitation.institution_id == institution_id,
                RectorInvitation.is_used == False,  # noqa: E712
                RectorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 7. Generate high-entropy 48-byte URL-safe raw token and compute SHA-256 hash
        raw_token = generate_raw_token(48)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = RectorInvitation(
            institution_id=institution_id,
            user_id=target_user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(invited_by_id)),
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        # 8. Attempt email delivery
        activation_url = get_settings().build_invitation_url(raw_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=cleaned_email,
            recipient_name=f"{first_name} {last_name}".strip(),
            role_label="Rector",
            jurisdiction_label=None,
            activation_url=activation_url,
        )

        # 9. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECTOR_INVITED,
                actor_id=str(invited_by_id),
                actor_ip=invited_by_ip,
                target_id=str(target_user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "rector_email": cleaned_email,
                    "document_type": document_type.value,
                    "document_number": cleaned_doc,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                    "authority_level": authority_level,
                },
            ),
            session=self._session,
        )

        if authority_level == "superadmin_emergency":
            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.SUPERADMIN_EMERGENCY_ROLE_PROVISIONING,
                    actor_id=str(invited_by_id),
                    actor_ip=invited_by_ip,
                    target_id=str(target_user.id),
                    target_type="User",
                    institution_id=str(institution_id),
                    correlation_id=correlation_id,
                    metadata={
                        "action": "invite_rector",
                        "target_role": "rector",
                        "target_institution_id": str(institution_id),
                        "invitation_id": str(invitation.id),
                        "rector_email": cleaned_email,
                        "authority_level": authority_level,
                    },
                ),
                session=self._session,
            )

        if delivery_status == EmailDeliveryStatus.EMAIL_SENT:
            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.RECTOR_INVITATION_SENT,
                    actor_id=str(invited_by_id),
                    actor_ip=invited_by_ip,
                    target_id=str(target_user.id),
                    target_type="User",
                    institution_id=str(institution_id),
                    correlation_id=correlation_id,
                    metadata={
                        "invitation_id": str(invitation.id),
                        "rector_email": cleaned_email,
                    },
                ),
                session=self._session,
            )

        return RectorInviteResult(
            invitation,
            raw_token,
            delivery_status=delivery_status,
            activation_url=activation_url,
        )

    async def verify_invitation(
        self,
        *,
        token: str,
    ) -> dict[str, Any]:
        """
        Validate an invitation token for the public onboarding screen.
        """
        if not token or not token.strip():
            raise NotFoundError("Token de invitación no suministrado.", code="INVITATION_NOT_FOUND")

        token_hash = hash_token(token.strip())
        stmt = (
            select(RectorInvitation)
            .where(RectorInvitation.token_hash == token_hash)
            .options(
                selectinload(RectorInvitation.user),
                selectinload(RectorInvitation.institution),
            )
        )
        invitation = (await self._session.execute(stmt)).scalar_one_or_none()

        if not invitation:
            raise NotFoundError(
                "El enlace de invitación no es válido o no existe.",
                code="INVITATION_NOT_FOUND",
            )

        if invitation.is_revoked:
            raise ConflictError(
                "El enlace de invitación ha sido revocado o reemplazado por uno más reciente.",
                code="INVITATION_REVOKED",
            )

        if invitation.is_used:
            raise ConflictError(
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta de Rector.",
                code="INVITATION_ALREADY_USED",
            )

        if invitation.is_expired:
            raise PEVNException(
                "El enlace de invitación ha expirado (tiempo límite de 48 horas superado).",
                code="INVITATION_EXPIRED",
                status_code=410,
            )

        return {
            "valid": True,
            "email": _mask_email(invitation.user.email),
            "first_name": invitation.user.first_name,
            "last_name": invitation.user.last_name,
            "institution_name": invitation.institution.name,
            "expires_at": invitation.expires_at,
        }

    async def accept_invitation(
        self,
        *,
        token: str,
        password: str,
        password_confirmation: str,
        client_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> User:
        """
        Redeem invitation, set Argon2id password, activate user and activate Rector role.
        """
        if not token or not token.strip():
            raise NotFoundError("Token de invitación no suministrado.", code="INVITATION_NOT_FOUND")

        if password != password_confirmation:
            raise UnprocessableEntityError(
                "Las contraseñas ingresadas no coinciden.",
                code="PASSWORD_MISMATCH",
            )

        if len(password) < 8:
            raise UnprocessableEntityError(
                "La contraseña debe contener un mínimo de 8 caracteres.",
                code="WEAK_PASSWORD",
            )

        token_hash = hash_token(token.strip())
        stmt = (
            select(RectorInvitation)
            .where(RectorInvitation.token_hash == token_hash)
            .options(
                selectinload(RectorInvitation.user),
                selectinload(RectorInvitation.institution),
            )
        )
        invitation = (await self._session.execute(stmt)).scalar_one_or_none()

        if not invitation:
            raise NotFoundError(
                "El enlace de invitación no es válido o no existe.",
                code="INVITATION_NOT_FOUND",
            )

        if invitation.is_revoked:
            raise ConflictError(
                "El enlace de invitación ha sido revocado o reemplazado por uno más reciente.",
                code="INVITATION_REVOKED",
            )

        if invitation.is_used:
            raise ConflictError(
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta.",
                code="INVITATION_ALREADY_USED",
            )

        if invitation.is_expired:
            raise PEVNException(
                "El enlace de invitación ha expirado.",
                code="INVITATION_EXPIRED",
                status_code=410,
            )

        # Atomic single-use claim: only one concurrent redemption can flip is_used.
        claimed = await self._session.execute(
            update(RectorInvitation)
            .where(
                RectorInvitation.id == invitation.id,
                RectorInvitation.is_used == False,  # noqa: E712
                RectorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_used=True, used_at=datetime.now(UTC))
            .returning(RectorInvitation.id)
            .execution_options(synchronize_session=False)
        )
        if claimed.scalar_one_or_none() is None:
            raise ConflictError(
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta.",
                code="INVITATION_ALREADY_USED",
            )

        user = invitation.user
        institution = invitation.institution

        # 1. Update user password with Argon2id and activate account
        user.hashed_password = password_hasher.hash(password)
        user.is_active = True
        user.is_verified = True
        user.must_change_password = False
        user.password_changed_at = datetime.now(UTC)
        user.failed_login_attempts = 0
        user.locked_until = None

        # 2. Activate UserRole for Rector
        role_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
        rector_role = (await self._session.execute(role_stmt)).scalar_one()

        await self._session.execute(
            update(UserRole)
            .where(
                UserRole.user_id == user.id,
                UserRole.role_id == rector_role.id,
                UserRole.institution_id == institution.id,
            )
            .values(is_active=True)
        )

        # 3. Mark invitation as used
        invitation.is_used = True
        invitation.used_at = datetime.now(UTC)

        # 4. Invalidate any other pending invitations for this user
        await self._session.execute(
            update(RectorInvitation)
            .where(
                RectorInvitation.user_id == user.id,
                RectorInvitation.id != invitation.id,
                RectorInvitation.is_used == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        await self._session.flush()

        # 5. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECTOR_ONBOARDING_COMPLETED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(user.id),
                target_type="User",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "email": user.email,
                    "institution_name": institution.name,
                },
            ),
            session=self._session,
        )

        return user

    async def revoke_rector(
        self,
        *,
        institution_id: uuid.UUID,
        reason: str,
        justification: str | None = None,
        revoked_by_id: uuid.UUID | str,
        revoked_by_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
        authority_level: str = "normal_municipal",
    ) -> tuple[User, str]:
        """
        Revokes/deactivates the active Rector of an institution, enabling immediate succession.

        Validates that the institution exists, locates the active Rector UserRole association,
        deactivates the association atomically, revokes all pending unredeemed invitations,
        records an auditable event, and returns the revoked user entity.
        """
        # 1. Verify Institution exists
        inst_stmt = select(Institution).where(Institution.id == institution_id)
        inst = (await self._session.execute(inst_stmt)).scalar_one_or_none()
        if not inst:
            raise NotFoundError(
                f"Institución educativa {institution_id} no encontrada.",
                code="INSTITUTION_NOT_FOUND",
            )

        # 2. Verify Rector Role exists in database
        role_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
        rector_role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not rector_role:
            raise NotFoundError(
                "Rol canónico 'rector' no encontrado en el catálogo de roles.",
                code="ROLE_NOT_FOUND",
            )

        # 3. Locate currently active Rector for this institution
        active_ur_stmt = (
            select(UserRole)
            .where(
                UserRole.institution_id == institution_id,
                UserRole.role_id == rector_role.id,
                UserRole.is_active == True,  # noqa: E712
            )
            .options(selectinload(UserRole.user))
        )
        active_user_role = (await self._session.execute(active_ur_stmt)).scalar_one_or_none()
        if not active_user_role:
            raise NotFoundError(
                "La institución educativa no cuenta con un Rector titular activo para revocar.",
                code="NO_ACTIVE_RECTOR_FOUND",
            )

        revoked_user = active_user_role.user

        # 4. Atomically deactivate active Rector UserRole
        active_user_role.is_active = False

        # 5. Revoke any pending invitations for this institution
        await self._session.execute(
            update(RectorInvitation)
            .where(
                RectorInvitation.institution_id == institution_id,
                RectorInvitation.is_used == False,  # noqa: E712
                RectorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 6. Invalidate active session refresh tokens for the revoked rector
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == revoked_user.id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
            .execution_options(synchronize_session=False)
        )

        await self._session.flush()

        # 6. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECTOR_REVOKED,
                actor_id=str(revoked_by_id),
                actor_ip=revoked_by_ip,
                target_id=str(revoked_user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "rector_email": revoked_user.email,
                    "rector_name": f"{revoked_user.first_name} {revoked_user.last_name}",
                    "reason": reason,
                    "justification": justification,
                    "revoked_at": datetime.now(UTC).isoformat(),
                    "authority_level": authority_level,
                },
            ),
            session=self._session,
        )

        if authority_level == "superadmin_emergency":
            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.SUPERADMIN_EMERGENCY_ROLE_PROVISIONING,
                    actor_id=str(revoked_by_id),
                    actor_ip=revoked_by_ip,
                    target_id=str(revoked_user.id),
                    target_type="User",
                    institution_id=str(institution_id),
                    correlation_id=correlation_id,
                    metadata={
                        "action": "revoke_rector",
                        "target_role": "rector",
                        "target_institution_id": str(institution_id),
                        "target_user_id": str(revoked_user.id),
                        "reason": reason,
                        "justification": justification,
                        "authority_level": authority_level,
                    },
                ),
                session=self._session,
            )

        return revoked_user, reason

    async def resend_invitation(
        self,
        institution_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
        authority_level: str = "normal_municipal",
    ) -> RectorInviteResult:
        """
        Invalidate previous pending invitations and issue a new single-use token for a pending Rector.
        """
        # 1. Verify Institution exists and is active
        inst_stmt = select(Institution).where(Institution.id == institution_id)
        inst = (await self._session.execute(inst_stmt)).scalar_one_or_none()
        if not inst:
            raise NotFoundError(
                f"Institución educativa {institution_id} no encontrada.",
                code="INSTITUTION_NOT_FOUND",
            )
        if not inst.is_active:
            raise ConflictError(
                "No se pueden reenviar invitaciones para una institución inactiva o suspendida.",
                code="INSTITUTION_INACTIVE",
            )

        # 2. Verify Rector Role exists in database
        role_stmt = select(Role).where(Role.name == SystemRole.RECTOR.value)
        rector_role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not rector_role:
            raise NotFoundError(
                "Rol canónico 'rector' no encontrado en el catálogo de roles.",
                code="ROLE_NOT_FOUND",
            )

        # 3. Check if institution already has an active Rector
        active_rector_stmt = (
            select(UserRole)
            .where(
                UserRole.institution_id == institution_id,
                UserRole.role_id == rector_role.id,
                UserRole.is_active == True,  # noqa: E712
            )
        )
        existing_active = (await self._session.execute(active_rector_stmt)).scalar_one_or_none()
        if existing_active:
            raise ConflictError(
                "La cuenta ya fue activada. Para restablecer la contraseña utilice el flujo de recuperación de contraseña.",
                code="ACCOUNT_ALREADY_ACTIVATED",
            )

        # 4. Locate pending inactive Rector association
        pending_ur_stmt = (
            select(UserRole)
            .where(
                UserRole.institution_id == institution_id,
                UserRole.role_id == rector_role.id,
                UserRole.is_active == False,  # noqa: E712
            )
            .options(selectinload(UserRole.user))
            .order_by(UserRole.assigned_at.desc())
        )
        pending_ur = (await self._session.execute(pending_ur_stmt)).scalar_one_or_none()
        if not pending_ur or not pending_ur.user:
            raise NotFoundError(
                "No existe una cuenta de Rector pendiente de activación para esta institución.",
                code="NO_PENDING_RECTOR_FOUND",
            )

        target_user = pending_ur.user
        if target_user.is_verified or target_user.is_active:
            raise ConflictError(
                "La cuenta ya fue activada. Para restablecer la contraseña utilice el flujo de recuperación de contraseña.",
                code="ACCOUNT_ALREADY_ACTIVATED",
            )

        # 5. Revoke previous pending invitations for this user and institution
        await self._session.execute(
            update(RectorInvitation)
            .where(
                RectorInvitation.institution_id == institution_id,
                RectorInvitation.user_id == target_user.id,
                RectorInvitation.is_used == False,  # noqa: E712
                RectorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 6. Generate high-entropy 48-byte URL-safe raw token and compute SHA-256 hash
        raw_token = generate_raw_token(48)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = RectorInvitation(
            institution_id=institution_id,
            user_id=target_user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        # 7. Attempt email delivery
        activation_url = get_settings().build_invitation_url(raw_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=target_user.email,
            recipient_name=f"{target_user.first_name} {target_user.last_name}".strip(),
            role_label="Rector",
            jurisdiction_label=inst.name,
            activation_url=activation_url,
        )

        # 8. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECTOR_INVITATION_RESENT,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(target_user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "rector_email": target_user.email,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                    "authority_level": authority_level,
                },
            ),
            session=self._session,
        )

        return RectorInviteResult(
            invitation,
            raw_token,
            delivery_status=delivery_status,
            activation_url=activation_url,
        )
