"""
PEVN Backend — Municipality Administrator Domain Service

Implements authoritative, transactional lifecycle management for MUNICIPALITY_ADMIN users:
  - Canonical municipality assignment validation against `municipalities` table
  - Automatic, server-authoritative parent department derivation (never trusts client)
  - Transactional user & user_role provisioning
  - Idempotent creation, status transitions, and municipality reassignment
  - Refresh token session invalidation upon deactivation or reassignment
  - Full audit logging adhering to AI Software Factory Standard v1.2
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.config import Environment, Settings, get_settings
from app.core.logging import get_logger
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import generate_raw_token, hash_token
from app.exceptions.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    PEVNException,
    UnprocessableEntityError,
)
from app.models.invitation import MunicipalityAdminInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import DocumentType, User
from app.schemas.municipality_admin import (
    MunicipalityAdminCreateRequest,
    MunicipalityAdminInvitationResponse,
    MunicipalityAdminResponse,
    MunicipalityOptionResponse,
)
from app.services.email_service import EmailDeliveryStatus, EmailService

_logger = get_logger(__name__)


class MunicipalityAdminInviteResult(tuple):
    """Backwards-compatible tuple for (invitation, raw_token) with delivery attributes."""

    def __new__(
        cls,
        invitation: MunicipalityAdminInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
        user: User | None = None,
        municipality: Municipality | None = None,
    ) -> MunicipalityAdminInviteResult:
        return super().__new__(cls, (invitation, raw_token))

    def __init__(
        self,
        invitation: MunicipalityAdminInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
        user: User | None = None,
        municipality: Municipality | None = None,
    ) -> None:
        self.invitation = invitation
        self.raw_token = raw_token
        self.delivery_status = delivery_status
        self.activation_url = activation_url
        self.user = user
        self.municipality = municipality


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


class MunicipalityAdminService:
    """
    Authoritative domain service for MUNICIPALITY_ADMIN lifecycle and municipal territorial provisioning.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
        email_service: EmailService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._audit = audit
        self._email = email_service or EmailService()
        self._settings = settings or get_settings()

    async def list_municipalities(
        self,
        department_id: uuid.UUID | None = None,
        municipality_id: uuid.UUID | None = None,
    ) -> list[MunicipalityOptionResponse]:
        """
        List canonical municipalities, optionally filtered by parent department or specific municipality.
        """
        stmt = (
            select(Municipality)
            .options(selectinload(Municipality.department))
            .order_by(Municipality.code.asc())
        )
        if municipality_id is not None:
            stmt = stmt.where(Municipality.id == municipality_id)
        elif department_id is not None:
            stmt = stmt.where(Municipality.department_id == department_id)

        result = await self._session.execute(stmt)
        munis = result.scalars().all()
        return [
            MunicipalityOptionResponse(
                id=m.id,
                code=m.code,
                name=m.name,
                department_id=m.department_id,
                department_code=m.department.code if m.department else None,
                department_name=m.department.name if m.department else None,
                display_label=f"{m.code} — {m.name} ({m.department.name if m.department else 'N/A'})",
            )
            for m in munis
        ]

    def _build_admin_response(
        self,
        user: User,
        municipality: Municipality,
        *,
        raw_invitation_token: str | None = None,
        invitation_id: uuid.UUID | None = None,
        email_delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        invitation_url: str | None = None,
    ) -> MunicipalityAdminResponse:
        """Helper to construct MunicipalityAdminResponse from entities."""
        dept = municipality.department
        return MunicipalityAdminResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            document_type=user.document_type,
            document_number=user.document_number,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[ur.role.name for ur in user.user_roles if ur.role] or [SystemRole.MUNICIPALITY_ADMIN.value],
            municipality_id=municipality.id,
            municipality_code=municipality.code,
            municipality_name=municipality.name,
            department_id=municipality.department_id,
            department_code=dept.code if dept else "N/A",
            department_name=dept.name if dept else "N/A",
            created_at=user.created_at,
            raw_invitation_token=raw_invitation_token,
            invitation_id=invitation_id,
            email_delivery_status=email_delivery_status,
            invitation_url=invitation_url,
        )

    async def list_municipality_admins(
        self,
        *,
        department_id: uuid.UUID | None = None,
        municipality_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[MunicipalityAdminResponse], int]:
        """
        List and search MUNICIPALITY_ADMIN accounts with optional territorial and status filters.
        """
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == SystemRole.MUNICIPALITY_ADMIN.value,
                UserRole.municipality_id.isnot(None),
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.user_roles)
                .selectinload(UserRole.municipality)
                .selectinload(Municipality.department),
            )
        )
        count_stmt = (
            select(func.count(func.distinct(User.id)))
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == SystemRole.MUNICIPALITY_ADMIN.value,
                UserRole.municipality_id.isnot(None),
            )
        )

        if municipality_id is not None:
            stmt = stmt.where(UserRole.municipality_id == municipality_id)
            count_stmt = count_stmt.where(UserRole.municipality_id == municipality_id)

        if department_id is not None:
            stmt = stmt.where(UserRole.department_id == department_id)
            count_stmt = count_stmt.where(UserRole.department_id == department_id)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            cond = or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                func.concat(User.first_name, " ", User.last_name).ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.document_number.ilike(search_pattern),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = (await self._session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        users = (await self._session.execute(stmt)).scalars().all()

        items: list[MunicipalityAdminResponse] = []
        for u in users:
            muni_role = next(
                (
                    ur
                    for ur in u.user_roles
                    if ur.role and ur.role.name == SystemRole.MUNICIPALITY_ADMIN.value and ur.municipality_id
                ),
                None,
            )
            if muni_role and muni_role.municipality:
                items.append(self._build_admin_response(u, muni_role.municipality))

        return items, total

    async def get_municipality_admin(self, user_id: uuid.UUID) -> MunicipalityAdminResponse:
        """
        Retrieve a single MUNICIPALITY_ADMIN by user UUID.
        """
        user = await self._load_municipality_admin_user(user_id)
        muni_role = self._extract_municipality_role(user)
        return self._build_admin_response(user, muni_role.municipality)

    async def create_municipality_admin(
        self,
        payload: MunicipalityAdminCreateRequest,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
        caller_department_id: uuid.UUID | None = None,
    ) -> MunicipalityAdminResponse:
        """
        Transactionally create a MUNICIPALITY_ADMIN account and persist the territorial scope.
        Derives the parent department strictly from the canonical municipality record.
        """
        # 1. Validate canonical municipality existence
        stmt = (
            select(Municipality)
            .where(Municipality.id == payload.municipality_id)
            .options(selectinload(Municipality.department))
        )
        res = await self._session.execute(stmt)
        municipality = res.scalar_one_or_none()
        if not municipality:
            raise NotFoundError(
                f"El municipio con ID {payload.municipality_id} no existe en el catálogo territorial del sistema.",
                code="MUNICIPALITY_NOT_FOUND",
            )

        # Enforce departmental isolation if caller is a department admin
        if caller_department_id is not None and municipality.department_id != caller_department_id:
            raise AuthorizationError(
                "No está autorizado para crear administradores municipales fuera de su departamento asignado.",
                code="PERMISSION_DENIED",
            )

        clean_email = payload.email.strip().lower()
        clean_username = payload.username.strip()

        # 2. Uniqueness checks
        email_check = (
            await self._session.execute(select(User.id).where(User.email == clean_email))
        ).scalar_one_or_none()
        if email_check:
            raise ConflictError(
                "El correo electrónico ya se encuentra registrado.",
                code="EMAIL_CONFLICT",
            )

        user_check = (
            await self._session.execute(select(User.id).where(User.username == clean_username))
        ).scalar_one_or_none()
        if user_check:
            raise ConflictError(
                "El nombre de usuario ya se encuentra registrado.",
                code="USERNAME_CONFLICT",
            )

        # 3. Document number handling
        clean_doc = (
            payload.document_number.strip()
            if payload.document_number
            else f"MA{secrets.randbelow(90000000) + 10000000}"
        )
        doc_check = (
            await self._session.execute(
                select(User.id).where(
                    User.document_type == payload.document_type,
                    User.document_number == clean_doc,
                )
            )
        ).scalar_one_or_none()
        if doc_check:
            raise ConflictError(
                "El documento de identidad ya se encuentra registrado para otro usuario.",
                code="DOCUMENT_CONFLICT",
            )

        # 4. Inactive and unverified initial state; unusable password hash
        unusable_hash = password_hasher.hash(generate_raw_token(32))
        hashed_password = unusable_hash
        is_active = False
        is_verified = False
        must_change_password = True

        # 5. Create User entity
        user = User(
            email=clean_email,
            username=clean_username,
            hashed_password=hashed_password,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            document_type=payload.document_type,
            document_number=clean_doc,
            institution_id=None,
            is_active=is_active,
            is_verified=is_verified,
            must_change_password=must_change_password,
        )
        self._session.add(user)
        await self._session.flush()

        # 6. Resolve canonical MUNICIPALITY_ADMIN role
        role_stmt = select(Role).where(Role.name == SystemRole.MUNICIPALITY_ADMIN.value)
        role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role:
            raise NotFoundError("Rol canónico municipality_admin no configurado en la base de datos.")

        # 7. Create UserRole with strictly validated municipality_id and derived department_id
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            municipality_id=municipality.id,
            department_id=municipality.department_id,
            institution_id=None,
            campus_id=None,
            is_active=is_active,
        )
        self._session.add(user_role)
        await self._session.flush()

        # 8. Revoke any prior pending invitations for this user
        await self._session.execute(
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.user_id == user.id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
                MunicipalityAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 9. Generate high-entropy 48-byte URL-safe raw token and compute SHA-256 hash
        raw_invitation_token = generate_raw_token(48)
        token_hash = hash_token(raw_invitation_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = MunicipalityAdminInvitation(
            municipality_id=municipality.id,
            user_id=user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        # 10. Attempt email delivery
        activation_url = get_settings().build_invitation_url(raw_invitation_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Administrador Municipal",
            jurisdiction_label=f"{municipality.name} (DANE {municipality.code})",
            activation_url=activation_url,
        )

        # 11. Record audit trail
        dept = municipality.department
        creation_event = AuditEvent(
            event_type=AuditEventType.MUNICIPALITY_ADMIN_CREATED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="municipality_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "actor_user_id": str(actor_id) if actor_id else None,
                "target_user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "municipality_id": str(municipality.id),
                "municipality_code": municipality.code,
                "municipality_name": municipality.name,
                "department_id": str(municipality.department_id),
                "department_code": dept.code if dept else "N/A",
                "department_name": dept.name if dept else "N/A",
                "invitation_id": str(invitation.id),
                "email_delivery_status": delivery_status.value,
            },
        )
        await self._audit.record(creation_event, session=self._session)

        invitation_event = AuditEvent(
            event_type=AuditEventType.MUNICIPALITY_ADMIN_INVITED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="User",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "invitation_id": str(invitation.id),
                "admin_email": user.email,
                "municipality_id": str(municipality.id),
                "municipality_code": municipality.code,
                "municipality_name": municipality.name,
                "expires_at": expires_at.isoformat(),
                "email_delivery_status": delivery_status.value,
            },
        )
        await self._audit.record(invitation_event, session=self._session)

        if delivery_status == EmailDeliveryStatus.EMAIL_SENT:
            sent_event = AuditEvent(
                event_type=AuditEventType.MUNICIPALITY_ADMIN_INVITATION_SENT,
                actor_ip=actor_ip,
                actor_id=str(actor_id) if actor_id else None,
                target_type="User",
                target_id=str(user.id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "admin_email": user.email,
                    "municipality_id": str(municipality.id),
                    "municipality_code": municipality.code,
                },
            )
            await self._audit.record(sent_event, session=self._session)

        # In production, never return raw token or link in API responses
        # In development, return raw token and link for controlled one-time delivery
        is_dev = self._settings.is_development
        disclosed_raw_token = raw_invitation_token if is_dev else None
        disclosed_url = activation_url if is_dev else None

        # Reload with relationships
        reload_stmt = (
            select(User)
            .where(User.id == user.id)
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role),
                selectinload(User.user_roles)
                .selectinload(UserRole.municipality)
                .selectinload(Municipality.department),
            )
        )
        reloaded_user = (await self._session.execute(reload_stmt)).scalar_one()
        return self._build_admin_response(
            reloaded_user,
            municipality,
            raw_invitation_token=disclosed_raw_token,
            invitation_id=invitation.id,
            email_delivery_status=delivery_status,
            invitation_url=disclosed_url,
        )

    async def update_status(
        self,
        user_id: uuid.UUID,
        is_active: bool,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
        caller_department_id: uuid.UUID | None = None,
    ) -> MunicipalityAdminResponse:
        """
        Activate or deactivate a MUNICIPALITY_ADMIN account.
        """
        user = await self._load_municipality_admin_user(user_id)
        muni_role = self._extract_municipality_role(user)

        if caller_department_id is not None and muni_role.municipality.department_id != caller_department_id:
            raise AuthorizationError(
                "No está autorizado para modificar administradores municipales fuera de su departamento.",
                code="PERMISSION_DENIED",
            )

        if is_active and not user.is_verified:
            # Activation must only occur through redemption of an invitation token.
            raise ConflictError(
                "La cuenta está pendiente de activación. El administrador debe completar su invitación "
                "para establecer su contraseña; no es posible activarla manualmente.",
                code="ACCOUNT_PENDING_ACTIVATION",
            )

        user.is_active = is_active
        muni_role.is_active = is_active

        if not is_active:
            await self._revoke_user_sessions(user.id)
            await self._revoke_pending_invitations(user.id)

        await self._session.flush()

        event = AuditEvent(
            event_type=AuditEventType.USER_ROLE_REVOKED if not is_active else AuditEventType.USER_ROLE_ASSIGNED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="municipality_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "action": "update_status",
                "is_active": is_active,
                "municipality_code": muni_role.municipality.code,
                "department_code": muni_role.municipality.department.code if muni_role.municipality.department else None,
                "reason": reason,
            },
        )
        await self._audit.record(event, session=self._session)

        return self._build_admin_response(user, muni_role.municipality)

    async def reassign_municipality(
        self,
        user_id: uuid.UUID,
        new_municipality_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
        caller_department_id: uuid.UUID | None = None,
    ) -> MunicipalityAdminResponse:
        """
        Explicitly reassign a MUNICIPALITY_ADMIN to another canonical municipality.
        Invalidates active session refresh tokens to prevent stale authorization scopes.
        """
        user = await self._load_municipality_admin_user(user_id)
        muni_role = self._extract_municipality_role(user)

        if caller_department_id is not None and muni_role.municipality.department_id != caller_department_id:
            raise AuthorizationError(
                "No está autorizado para reasignar administradores municipales fuera de su departamento.",
                code="PERMISSION_DENIED",
            )

        stmt = (
            select(Municipality)
            .where(Municipality.id == new_municipality_id)
            .options(selectinload(Municipality.department))
        )
        new_muni = (await self._session.execute(stmt)).scalar_one_or_none()
        if not new_muni:
            raise NotFoundError(
                f"El municipio destino con ID {new_municipality_id} no existe en el sistema.",
                code="MUNICIPALITY_NOT_FOUND",
            )

        if caller_department_id is not None and new_muni.department_id != caller_department_id:
            raise AuthorizationError(
                "No puede reasignar a un municipio fuera de su departamento de jurisdicción.",
                code="PERMISSION_DENIED",
            )

        prev_muni_code = muni_role.municipality.code
        prev_muni_id = str(muni_role.municipality_id)

        muni_role.municipality_id = new_muni.id
        muni_role.department_id = new_muni.department_id

        await self._revoke_user_sessions(user.id)
        # Pending invitations are bound to the previous municipality: invalidate them.
        await self._revoke_pending_invitations(user.id)
        await self._session.flush()

        event = AuditEvent(
            event_type=AuditEventType.USER_ROLE_ASSIGNED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="municipality_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "action": "reassign_municipality",
                "previous_municipality_id": prev_muni_id,
                "previous_municipality_code": prev_muni_code,
                "new_municipality_id": str(new_muni.id),
                "new_municipality_code": new_muni.code,
                "reason": reason,
            },
        )
        await self._audit.record(event, session=self._session)

        return self._build_admin_response(user, new_muni)

    async def _load_municipality_admin_user(self, user_id: uuid.UUID) -> User:
        """Load user by ID and ensure they have the MUNICIPALITY_ADMIN role."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.user_roles)
                .selectinload(UserRole.municipality)
                .selectinload(Municipality.department),
            )
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(f"Usuario con ID {user_id} no encontrado.", code="USER_NOT_FOUND")

        has_role = any(
            ur.role.name == SystemRole.MUNICIPALITY_ADMIN.value for ur in user.user_roles if ur.role
        )
        if not has_role:
            raise NotFoundError(
                f"El usuario {user_id} no posee el rol de Administrador Municipal.",
                code="NOT_MUNICIPALITY_ADMIN",
            )
        return user

    def _extract_municipality_role(self, user: User) -> UserRole:
        """Extract the active MUNICIPALITY_ADMIN UserRole record."""
        muni_role = next(
            (
                ur
                for ur in user.user_roles
                if ur.role and ur.role.name == SystemRole.MUNICIPALITY_ADMIN.value and ur.municipality
            ),
            None,
        )
        if not muni_role or not muni_role.municipality:
            raise NotFoundError(
                "El usuario no tiene una asignación municipal válida.",
                code="NO_MUNICIPAL_ASSIGNMENT",
            )
        return muni_role

    async def _revoke_user_sessions(self, user_id: uuid.UUID) -> None:
        """Mark all active refresh tokens for the user as revoked."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
            .execution_options(synchronize_session=False)
        )

    async def _revoke_pending_invitations(self, user_id: uuid.UUID) -> None:
        """Revoke every unused, non-revoked invitation bound to the user."""
        await self._session.execute(
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.user_id == user_id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
                MunicipalityAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session=False)
        )

    async def resend_invitation(
        self,
        user_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
        caller_department_id: uuid.UUID | None = None,
    ) -> MunicipalityAdminInviteResult:
        """
        Invalidates existing active invitations and issues a new time-limited token.
        """
        user = await self._load_municipality_admin_user(user_id)
        muni_role = self._extract_municipality_role(user)
        municipality = muni_role.municipality

        if caller_department_id is not None and municipality.department_id != caller_department_id:
            raise AuthorizationError(
                "No está autorizado para reenviar invitaciones a administradores fuera de su departamento.",
                code="PERMISSION_DENIED",
            )

        if user.is_verified:
            raise ConflictError(
                "La cuenta ya fue activada. Para restablecer la contraseña utilice el flujo de recuperación de contraseña.",
                code="ACCOUNT_ALREADY_ACTIVATED",
            )

        # 1. Invalidate previous pending invitations
        await self._session.execute(
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.user_id == user.id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
                MunicipalityAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 2. Generate new token
        raw_token = generate_raw_token(48)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = MunicipalityAdminInvitation(
            municipality_id=municipality.id,
            user_id=user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        # 3. Attempt email dispatch
        activation_url = get_settings().build_invitation_url(raw_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Administrador Municipal",
            jurisdiction_label=f"{municipality.name} (DANE {municipality.code})",
            activation_url=activation_url,
        )

        # 4. Audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MUNICIPALITY_ADMIN_INVITATION_RESENT,
                actor_ip=actor_ip,
                actor_id=str(actor_id) if actor_id else None,
                target_type="User",
                target_id=str(user.id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "admin_email": user.email,
                    "municipality_id": str(municipality.id),
                    "municipality_code": municipality.code,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                },
            ),
            session=self._session,
        )

        is_dev = self._settings.is_development
        disclosed_raw_token = raw_token if is_dev else None
        disclosed_url = activation_url if is_dev else None

        return MunicipalityAdminInviteResult(
            invitation,
            disclosed_raw_token or "",
            delivery_status=delivery_status,
            activation_url=disclosed_url,
            user=user,
            municipality=municipality,
        )

    async def verify_invitation(
        self,
        *,
        token: str,
    ) -> dict[str, Any]:
        """
        Validate a municipality administrator invitation token for the public onboarding screen.
        """
        if not token or not token.strip():
            raise NotFoundError("Token de invitación no suministrado.", code="INVITATION_NOT_FOUND")

        token_hash = hash_token(token.strip())
        stmt = (
            select(MunicipalityAdminInvitation)
            .where(MunicipalityAdminInvitation.token_hash == token_hash)
            .options(
                selectinload(MunicipalityAdminInvitation.user),
                selectinload(MunicipalityAdminInvitation.municipality).selectinload(Municipality.department),
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
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta de Administrador Municipal.",
                code="INVITATION_ALREADY_USED",
            )

        if invitation.is_expired:
            raise PEVNException(
                "El enlace de invitación ha expirado (tiempo límite de 48 horas superado).",
                code="INVITATION_EXPIRED",
                status_code=410,
            )

        dept = invitation.municipality.department
        return {
            "valid": True,
            "email": _mask_email(invitation.user.email),
            "first_name": invitation.user.first_name,
            "last_name": invitation.user.last_name,
            "municipality_name": invitation.municipality.name,
            "municipality_code": invitation.municipality.code,
            "department_name": dept.name if dept else None,
            "department_code": dept.code if dept else None,
            "role_name": "municipality_admin",
            "expires_at": invitation.expires_at,
        }

    async def accept_invitation(
        self,
        *,
        token: str,
        password: str,
        password_confirmation: str,
        client_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> User:
        """
        Redeem municipality admin invitation, set Argon2id password, activate user and territorial UserRole.
        Guarantees that role and municipality scope cannot be manipulated by the client.
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
            select(MunicipalityAdminInvitation)
            .where(MunicipalityAdminInvitation.token_hash == token_hash)
            .options(
                selectinload(MunicipalityAdminInvitation.user),
                selectinload(MunicipalityAdminInvitation.municipality).selectinload(Municipality.department),
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
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.id == invitation.id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
                MunicipalityAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_used=True, used_at=datetime.now(UTC))
            .returning(MunicipalityAdminInvitation.id)
            .execution_options(synchronize_session=False)
        )
        if claimed.scalar_one_or_none() is None:
            raise ConflictError(
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta.",
                code="INVITATION_ALREADY_USED",
            )

        user = invitation.user
        municipality = invitation.municipality
        dept = municipality.department

        # 1. Update user password with Argon2id and activate account
        user.hashed_password = password_hasher.hash(password)
        user.is_active = True
        user.is_verified = True
        user.must_change_password = False
        user.password_changed_at = datetime.now(UTC)
        user.failed_login_attempts = 0
        user.locked_until = None

        # 2. Activate UserRole for MUNICIPALITY_ADMIN strictly for the bound municipality
        role_stmt = select(Role).where(Role.name == SystemRole.MUNICIPALITY_ADMIN.value)
        ma_role = (await self._session.execute(role_stmt)).scalar_one()

        await self._session.execute(
            update(UserRole)
            .where(
                UserRole.user_id == user.id,
                UserRole.role_id == ma_role.id,
                UserRole.municipality_id == municipality.id,
            )
            .values(is_active=True)
        )

        # 3. Mark invitation as used
        invitation.is_used = True
        invitation.used_at = datetime.now(UTC)

        # 4. Invalidate any other pending invitations for this user
        await self._session.execute(
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.user_id == user.id,
                MunicipalityAdminInvitation.id != invitation.id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        await self._session.flush()

        # 5. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.MUNICIPALITY_ADMIN_ONBOARDING_COMPLETED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(user.id),
                target_type="User",
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "email": user.email,
                    "municipality_id": str(municipality.id),
                    "municipality_code": municipality.code,
                    "municipality_name": municipality.name,
                    "department_id": str(municipality.department_id),
                    "department_code": dept.code if dept else "N/A",
                },
            ),
            session=self._session,
        )

        _logger.info(
            "MUNICIPALITY_ADMIN onboarding completed",
            user_id=str(user.id),
            municipality_code=municipality.code,
            municipality_name=municipality.name,
        )

        return user

    async def remediate_test_account(
        self,
        *,
        username: str,
        email: str,
        document_type: DocumentType | str,
        document_number: str,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> User:
        """
        Remediate an insecurely created test account per NTA-09-R2 specifications.
        Revokes active sessions, sets inactive/unverified/must_change_password=True,
        replaces password hash with unguessable entropy, invalidates pending invitations,
        preserves municipal link and audit history, and records an audit remediation event.
        """
        doc_type_val = document_type.value if hasattr(document_type, "value") else str(document_type)

        stmt = (
            select(User)
            .where(
                User.username == username,
                User.email == email.strip().lower(),
                User.document_type == doc_type_val,
                User.document_number == document_number.strip(),
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.user_roles).selectinload(UserRole.municipality),
            )
        )
        results = (await self._session.execute(stmt)).scalars().all()
        if len(results) != 1:
            raise ConflictError(
                f"Expected exactly 1 test account matching ({username}, {email}), found {len(results)}.",
                code="AMBIGUOUS_TEST_ACCOUNT",
            )

        user = results[0]
        muni_role = self._extract_municipality_role(user)

        # 1. Revoke active refresh tokens and sessions
        await self._revoke_user_sessions(user.id)

        # 2. Securely replace password hash with high-entropy unguessable value
        user.hashed_password = password_hasher.hash(secrets.token_urlsafe(64))

        # 3. Set inactive, unverified, must_change_password=True
        user.is_active = False
        user.is_verified = False
        user.must_change_password = True
        muni_role.is_active = False

        # 4. Invalidate any existing invitations or reset tokens
        await self._session.execute(
            update(MunicipalityAdminInvitation)
            .where(
                MunicipalityAdminInvitation.user_id == user.id,
                MunicipalityAdminInvitation.is_used == False,  # noqa: E712
                MunicipalityAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )
        await self._session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.is_used == False,  # noqa: E712
            )
            .values(is_used=True)
        )

        await self._session.flush()

        # 5. Record remediation audit event without logging secrets
        remediation_event = AuditEvent(
            event_type=AuditEventType.MUNICIPALITY_ADMIN_REMEDIATED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="User",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "action": "remediate_test_account",
                "standard": "AI Software Factory Standard v1.2",
                "milestone": "NTA-09-R2",
                "target_user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "municipality_id": str(muni_role.municipality_id),
                "municipality_code": muni_role.municipality.code if muni_role.municipality else "N/A",
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "must_change_password": user.must_change_password,
            },
        )
        await self._audit.record(remediation_event, session=self._session)

        return user
