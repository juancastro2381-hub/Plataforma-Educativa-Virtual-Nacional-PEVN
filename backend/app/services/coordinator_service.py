"""
PEVN Backend — Coordinator Domain Service

Implements authoritative, transactional lifecycle management for COORDINATOR users:
  - Strict institutional tenant binding (institution_id validated server-side)
  - Optional campus-level scoping (campus_id validated against institution)
  - Hardcoded canonical 'coordinator' role assignment
  - Cryptographic single-use invitation lifecycle with SHA-256 token hashing
  - Secure credential generation and self-activation flow
  - Refresh token session invalidation upon deactivation
  - Full audit logging adhering to AI Software Factory Standard v1.2
"""

from __future__ import annotations

import asyncio
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.config import Settings, get_settings
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
from app.models.institution import Campus, Institution
from app.models.invitation import CoordinatorInvitation
from app.models.role import Role, UserRole
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.schemas.coordinator import (
    CoordinatorCampusOption,
    CoordinatorCreateRequest,
    CoordinatorResendInvitationResponse,
    CoordinatorResponse,
)
from app.services.email_service import EmailDeliveryStatus, EmailService

_logger = get_logger(__name__)

_institution_locks: dict[uuid.UUID, asyncio.Lock] = {}


def get_institution_lock(institution_id: uuid.UUID) -> asyncio.Lock:
    """Return an asyncio.Lock per institution to guarantee transactional isolation."""
    if institution_id not in _institution_locks:
        _institution_locks[institution_id] = asyncio.Lock()
    return _institution_locks[institution_id]


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


class CoordinatorService:
    """
    Authoritative domain service for COORDINATOR lifecycle within institutional scope.
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

    def _build_coordinator_response(
        self,
        user: User,
        *,
        campus: Campus | None = None,
        campus_id: uuid.UUID | None = None,
        campus_name: str | None = None,
        invitation: CoordinatorInvitation | None = None,
        raw_token: str | None = None,
        invitation_url: str | None = None,
        delivery_status: EmailDeliveryStatus | None = None,
    ) -> CoordinatorResponse:
        resolved_campus_id = campus.id if campus else campus_id
        resolved_campus_name = campus.name if campus else campus_name

        # If campus info not explicitly passed, inspect loaded user_roles safely without triggering lazyload
        if not resolved_campus_id and "user_roles" in user.__dict__ and user.user_roles:
            for ur in user.user_roles:
                if ur.campus_id:
                    resolved_campus_id = ur.campus_id
                    if "campus" in ur.__dict__ and ur.campus:
                        resolved_campus_name = ur.campus.name
                    break

        # Resolve invitation status
        resolved_status = "direct"
        resolved_invitation_id: uuid.UUID | None = None
        if invitation:
            resolved_invitation_id = invitation.id
            if user.is_verified:
                resolved_status = "accepted"
            elif invitation.is_revoked:
                resolved_status = "revoked"
            elif invitation.is_expired:
                resolved_status = "expired"
            elif invitation.is_used:
                resolved_status = "accepted"
            else:
                resolved_status = "pending"
        elif user.is_verified:
            resolved_status = "accepted"
        elif not user.is_active:
            resolved_status = "pending"

        return CoordinatorResponse(
            id=user.id,
            institution_id=user.institution_id or uuid.uuid4(),
            campus_id=resolved_campus_id,
            campus_name=resolved_campus_name,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            document_type=user.document_type,
            document_number=user.document_number,
            role="coordinator",
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            invitation_id=resolved_invitation_id,
            invitation_status=resolved_status,
            raw_invitation_token=raw_token,
            invitation_url=invitation_url,
            email_delivery_status=delivery_status,
        )

    async def list_campuses(self, institution_id: uuid.UUID) -> list[CoordinatorCampusOption]:
        """List active campuses for an institution to populate assignment selectors."""
        stmt = (
            select(Campus)
            .where(Campus.institution_id == institution_id)
            .order_by(Campus.name.asc())
        )
        res = await self._session.execute(stmt)
        campuses = res.scalars().all()
        return [
            CoordinatorCampusOption(
                id=c.id,
                institution_id=c.institution_id,
                dane_sede_code=c.dane_sede_code,
                name=c.name,
                is_main=getattr(c, "is_main", False),
                is_active=getattr(c, "is_active", True),
            )
            for c in campuses
        ]

    async def validate_coordinator_assignment_exclusivity(
        self,
        *,
        institution_id: uuid.UUID,
        campus_id: uuid.UUID | None,
        exclude_user_id: uuid.UUID | None = None,
    ) -> tuple[Institution, Campus | None]:
        """
        Enforce strict institution-scoped exclusivity policy for Academic Coordinator assignments (NTA-10-R10).
        Guarantees isolation and serializes concurrent checks via transaction row-lock on the Institution.

        Rules:
          - Rule A: At most one effective institution-wide coordinator.
                    Cannot coexist with any campus-specific coordinator.
          - Rule B: Each campus may have at most one effective coordinator.
          - Rule C: Effective assignments include active accounts and pending unexpired invitations.
                    Suspended accounts release their assignment slot until reactivation.
        """
        # 1. Concurrency control: Acquire exclusive row lock on the Institution
        inst_stmt = (
            select(Institution)
            .where(Institution.id == institution_id)
            .with_for_update()
        )
        inst = (await self._session.execute(inst_stmt)).scalar_one_or_none()
        if not inst:
            raise NotFoundError(
                f"Institución educativa {institution_id} no encontrada.",
                code="INSTITUTION_NOT_FOUND",
            )

        # 2. Validate campus relationship if specified
        target_campus: Campus | None = None
        if campus_id:
            target_campus = await self._session.get(Campus, campus_id)
            if not target_campus or target_campus.institution_id != institution_id:
                raise NotFoundError(
                    f"La sede educativa {campus_id} no existe o no pertenece a la institución educativa.",
                    code="CAMPUS_NOT_FOUND",
                )

        now = datetime.now(UTC)

        # 3. Query all effective coordinator assignments in the institution
        role_stmt = select(Role.id).where(
            Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value))
        )
        coord_role_ids = (await self._session.execute(role_stmt)).scalars().all()
        if not coord_role_ids:
            return inst, target_campus

        # Source A: Users with active coordinator roles where User is active
        active_roles_stmt = (
            select(UserRole, User, Campus)
            .join(User, UserRole.user_id == User.id)
            .outerjoin(Campus, UserRole.campus_id == Campus.id)
            .where(
                UserRole.institution_id == institution_id,
                UserRole.role_id.in_(coord_role_ids),
                UserRole.is_active == True,  # noqa: E712
                User.is_active == True,  # noqa: E712
            )
        )
        if exclude_user_id:
            active_roles_stmt = active_roles_stmt.where(User.id != exclude_user_id)

        active_res = (await self._session.execute(active_roles_stmt)).all()

        # Source B: Users with pending unexpired invitations who are not verified
        pending_inv_stmt = (
            select(CoordinatorInvitation, User, Campus)
            .join(User, CoordinatorInvitation.user_id == User.id)
            .outerjoin(Campus, CoordinatorInvitation.campus_id == Campus.id)
            .where(
                CoordinatorInvitation.institution_id == institution_id,
                CoordinatorInvitation.is_used == False,  # noqa: E712
                CoordinatorInvitation.is_revoked == False,  # noqa: E712
                CoordinatorInvitation.expires_at > now,
                User.is_verified == False,  # noqa: E712
            )
        )
        if exclude_user_id:
            pending_inv_stmt = pending_inv_stmt.where(CoordinatorInvitation.user_id != exclude_user_id)

        pending_res = (await self._session.execute(pending_inv_stmt)).all()

        # Build list of occupied assignments
        effective_assignments: list[dict[str, Any]] = []
        seen_user_ids = set()

        for ur, u, camp in active_res:
            effective_assignments.append({
                "user_id": u.id,
                "user_name": f"{u.first_name} {u.last_name}".strip(),
                "campus_id": ur.campus_id,
                "campus_name": camp.name if camp else None,
                "status_label": "activo",
            })
            seen_user_ids.add(u.id)

        for inv, u, camp in pending_res:
            if u.id not in seen_user_ids:
                effective_assignments.append({
                    "user_id": u.id,
                    "user_name": f"{u.first_name} {u.last_name}".strip(),
                    "campus_id": inv.campus_id,
                    "campus_name": camp.name if camp else None,
                    "status_label": "invitación pendiente",
                })
                seen_user_ids.add(u.id)

        # 4. Evaluate exclusivity rules
        global_coordinators = [a for a in effective_assignments if a["campus_id"] is None]
        campus_coordinators = [a for a in effective_assignments if a["campus_id"] is not None]

        # Case 1: Requested scope is Institution-Wide (campus_id is None)
        if campus_id is None:
            if global_coordinators:
                existing = global_coordinators[0]
                raise ConflictError(
                    f"La institución ya cuenta con un Coordinador Académico de alcance institucional ({existing['user_name']}, {existing['status_label']}). "
                    f"Solo se permite un coordinador institucional global por institución.",
                    code="COORDINATOR_GLOBAL_CONFLICT",
                )
            if campus_coordinators:
                campus_names = sorted({c["campus_name"] or str(c["campus_id"]) for c in campus_coordinators})
                raise ConflictError(
                    f"No es posible asignar un Coordinador Académico de alcance institucional porque existen coordinadores asignados a sedes específicas: {', '.join(campus_names)}. "
                    f"Para designar un coordinador global, no deben existir coordinaciones particulares por sede.",
                    code="COORDINATOR_SCOPE_CONFLICT",
                )

        # Case 2: Requested scope is Campus-Specific (campus_id is not None)
        else:
            if global_coordinators:
                existing = global_coordinators[0]
                target_name = target_campus.name if target_campus else str(campus_id)
                raise ConflictError(
                    f"No es posible asignar un coordinador a la sede '{target_name}' porque la institución cuenta con un Coordinador Académico de alcance global ({existing['user_name']}, {existing['status_label']}). "
                    f"No pueden coexistir coordinaciones por sede con una coordinación institucional global.",
                    code="COORDINATOR_SCOPE_CONFLICT",
                )
            same_campus_assigned = [c for c in campus_coordinators if c["campus_id"] == campus_id]
            if same_campus_assigned:
                existing = same_campus_assigned[0]
                target_name = target_campus.name if target_campus else str(campus_id)
                raise ConflictError(
                    f"La sede educativa '{target_name}' ya cuenta con un Coordinador Académico asignado ({existing['user_name']}, {existing['status_label']}). "
                    f"Cada sede educativa solo puede tener un coordinador asignado.",
                    code="COORDINATOR_CAMPUS_CONFLICT",
                )

        return inst, target_campus

    async def create_coordinator(
        self,
        *,
        institution_id: uuid.UUID,
        payload: CoordinatorCreateRequest,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> CoordinatorResponse:
        """
        Transactionally create an institutional Coordinator account.
        If no initial password is provided, executes the secure cryptographic invitation workflow.
        """
        async with get_institution_lock(institution_id):
            return await self._create_coordinator_locked(
                institution_id=institution_id,
                payload=payload,
                actor_id=actor_id,
                actor_ip=actor_ip,
                correlation_id=correlation_id,
            )

    async def _create_coordinator_locked(
        self,
        *,
        institution_id: uuid.UUID,
        payload: CoordinatorCreateRequest,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> CoordinatorResponse:
        # 1 & 2. Validate exclusivity, institution existence, and campus relationship
        inst, target_campus = await self.validate_coordinator_assignment_exclusivity(
            institution_id=institution_id,
            campus_id=payload.campus_id,
        )

        clean_email = payload.email.strip().lower()
        clean_doc = payload.document_number.strip()
        clean_first = payload.first_name.strip()
        clean_last = payload.last_name.strip()

        # 3. Uniqueness checks
        email_check = (
            await self._session.execute(select(User.id).where(User.email == clean_email))
        ).scalar_one_or_none()
        if email_check:
            raise ConflictError(
                "El correo electrónico ya se encuentra registrado.",
                code="EMAIL_CONFLICT",
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

        # 4. Derive username
        base_username = clean_email.split("@")[0].replace(".", "_")
        username_candidate = base_username
        if (await self._session.execute(select(User.id).where(User.username == username_candidate))).scalar_one_or_none():
            username_candidate = f"{base_username}_{clean_doc[-4:]}"

        # 5. Resolve canonical role 'coordinator'
        role_stmt = select(Role).where(Role.name == "coordinator")
        role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role:
            role_stmt2 = select(Role).where(Role.name == SystemRole.ACADEMIC_COORDINATOR.value)
            role = (await self._session.execute(role_stmt2)).scalar_one_or_none()
            if not role:
                raise NotFoundError("Rol canónico coordinator no encontrado en la base de datos.")

        # 6. Branch: Direct Password Provisioning vs. Secure Invitation
        if payload.password and payload.password.strip():
            raw_password = payload.password.strip()
            if len(raw_password) < 8:
                raise UnprocessableEntityError("La contraseña debe tener al menos 8 caracteres.")
            hashed_pwd = password_hasher.hash(raw_password)
            is_active = payload.is_active
            is_verified = True
            must_change = False

            user = User(
                institution_id=institution_id,
                email=clean_email,
                username=username_candidate,
                hashed_password=hashed_pwd,
                first_name=clean_first,
                last_name=clean_last,
                document_type=payload.document_type,
                document_number=clean_doc,
                is_active=is_active,
                is_verified=is_verified,
                must_change_password=must_change,
            )
            self._session.add(user)
            await self._session.flush()

            user_role = UserRole(
                user_id=user.id,
                role_id=role.id,
                institution_id=institution_id,
                campus_id=payload.campus_id,
                department_id=inst.department_id if hasattr(inst, "department_id") else None,
                municipality_id=inst.municipality_id,
                is_active=is_active,
            )
            self._session.add(user_role)
            await self._session.flush()

            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.USER_ROLE_ASSIGNED,
                    actor_id=str(actor_id) if actor_id else str(user.id),
                    actor_ip=actor_ip,
                    target_id=str(user.id),
                    target_type="User",
                    institution_id=str(institution_id),
                    metadata={
                        "action": "create_coordinator_direct",
                        "role": "coordinator",
                        "institution_id": str(institution_id),
                        "campus_id": str(payload.campus_id) if payload.campus_id else None,
                        "email": user.email,
                    },
                    correlation_id=correlation_id,
                    success=True,
                ),
                session=self._session,
            )

            await self._session.commit()
            return self._build_coordinator_response(user, campus=target_campus)

        # Standard Workflow: Secure Invitation (Account Inactive until Acceptance)
        unusable_hash = password_hasher.hash(generate_raw_token(32))
        is_active = False
        is_verified = False
        must_change = True

        user = User(
            institution_id=institution_id,
            email=clean_email,
            username=username_candidate,
            hashed_password=unusable_hash,
            first_name=clean_first,
            last_name=clean_last,
            document_type=payload.document_type,
            document_number=clean_doc,
            is_active=is_active,
            is_verified=is_verified,
            must_change_password=must_change,
        )
        self._session.add(user)
        await self._session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            institution_id=institution_id,
            campus_id=payload.campus_id,
            department_id=inst.department_id if hasattr(inst, "department_id") else None,
            municipality_id=inst.municipality_id,
            is_active=False,
        )
        self._session.add(user_role)
        await self._session.flush()

        # Invalidate any prior pending invitations for this user
        await self._session.execute(
            update(CoordinatorInvitation)
            .where(
                CoordinatorInvitation.user_id == user.id,
                CoordinatorInvitation.is_used == False,  # noqa: E712
                CoordinatorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # Generate 48-byte cryptographically secure random token and SHA-256 digest
        raw_invitation_token = generate_raw_token(48)
        token_hash = hash_token(raw_invitation_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = CoordinatorInvitation(
            institution_id=institution_id,
            campus_id=payload.campus_id,
            user_id=user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        activation_url = self._settings.build_invitation_url(raw_invitation_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Coordinador Académico",
            jurisdiction_label=f"{inst.name} ({target_campus.name if target_campus else 'Institución Completa'})",
            activation_url=activation_url,
        )

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COORDINATOR_INVITED,
                actor_id=str(actor_id) if actor_id else str(user.id),
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="Coordinator",
                institution_id=str(institution_id),
                metadata={
                    "invitation_id": str(invitation.id),
                    "action": "invite_coordinator",
                    "role": "coordinator",
                    "institution_id": str(institution_id),
                    "campus_id": str(payload.campus_id) if payload.campus_id else None,
                    "email": user.email,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                },
                correlation_id=correlation_id,
                success=True,
            ),
            session=self._session,
        )

        is_dev = self._settings.is_development
        disclosed_raw_token = raw_invitation_token if is_dev else None
        disclosed_url = activation_url if is_dev else None

        await self._session.commit()
        return self._build_coordinator_response(
            user,
            campus=target_campus,
            invitation=invitation,
            raw_token=disclosed_raw_token,
            invitation_url=disclosed_url,
            delivery_status=delivery_status,
        )

    async def resend_invitation(
        self,
        coordinator_id: uuid.UUID,
        institution_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> CoordinatorResendInvitationResponse:
        """
        Invalidates existing active invitations and issues a new time-limited token for a coordinator.
        """
        async with get_institution_lock(institution_id):
            return await self._resend_invitation_locked(
                coordinator_id=coordinator_id,
                institution_id=institution_id,
                actor_id=actor_id,
                actor_ip=actor_ip,
                correlation_id=correlation_id,
            )

    async def _resend_invitation_locked(
        self,
        coordinator_id: uuid.UUID,
        institution_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> CoordinatorResendInvitationResponse:
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                User.id == coordinator_id,
                User.institution_id == institution_id,
                Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)),
            )
            .options(selectinload(User.user_roles))
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(
                f"Coordinador {coordinator_id} no encontrado en la institución.",
                code="COORDINATOR_NOT_FOUND",
            )

        if user.is_verified:
            raise ConflictError(
                "La cuenta ya fue activada. Para restablecer la contraseña utilice el flujo de recuperación de contraseña.",
                code="ACCOUNT_ALREADY_ACTIVATED",
            )

        inst = await self._session.get(Institution, institution_id)
        coord_role = next((ur for ur in user.user_roles if ur.institution_id == institution_id), None)
        target_campus_id = coord_role.campus_id if coord_role else None
        target_campus = await self._session.get(Campus, target_campus_id) if target_campus_id else None

        # Validate that the slot is not conflicted by another coordinator
        await self.validate_coordinator_assignment_exclusivity(
            institution_id=institution_id,
            campus_id=target_campus_id,
            exclude_user_id=coordinator_id,
        )

        # 1. Invalidate previous pending invitations
        await self._session.execute(
            update(CoordinatorInvitation)
            .where(
                CoordinatorInvitation.user_id == user.id,
                CoordinatorInvitation.is_used == False,  # noqa: E712
                CoordinatorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 2. Generate new token
        raw_token = generate_raw_token(48)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = CoordinatorInvitation(
            institution_id=institution_id,
            campus_id=target_campus_id,
            user_id=user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        self._session.add(invitation)
        await self._session.flush()

        activation_url = self._settings.build_invitation_url(raw_token)
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Coordinador Académico",
            jurisdiction_label=f"{inst.name if inst else 'Institución'} ({target_campus.name if target_campus else 'Institución Completa'})",
            activation_url=activation_url,
        )

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COORDINATOR_INVITATION_RESENT,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="Coordinator",
                institution_id=str(institution_id),
                metadata={
                    "invitation_id": str(invitation.id),
                    "email": user.email,
                    "institution_id": str(institution_id),
                    "campus_id": str(target_campus_id) if target_campus_id else None,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                },
                correlation_id=correlation_id,
                success=True,
            ),
            session=self._session,
        )

        is_dev = self._settings.is_development
        disclosed_raw_token = raw_token if is_dev else None
        disclosed_url = activation_url if is_dev else None

        await self._session.commit()
        return CoordinatorResendInvitationResponse(
            invitation_id=invitation.id,
            raw_invitation_token=disclosed_raw_token,
            invitation_url=disclosed_url,
            email_delivery_status=delivery_status,
            expires_at=expires_at,
            message="Invitación reenviada exitosamente.",
        )

    async def verify_invitation(self, *, token: str) -> dict[str, Any]:
        """
        Validate a coordinator invitation token for the public onboarding screen.
        """
        if not token or not token.strip():
            raise NotFoundError("Token de invitación no suministrado.", code="INVITATION_NOT_FOUND")

        token_hash = hash_token(token.strip())
        stmt = (
            select(CoordinatorInvitation)
            .where(CoordinatorInvitation.token_hash == token_hash)
            .options(
                selectinload(CoordinatorInvitation.user),
                selectinload(CoordinatorInvitation.institution),
                selectinload(CoordinatorInvitation.campus),
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
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta de Coordinador.",
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
            "campus_name": invitation.campus.name if invitation.campus else None,
            "role_name": "coordinator",
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
        Redeem coordinator invitation, set Argon2id password, activate user and institutional UserRole.
        Guarantees that role, institution, and campus scope cannot be manipulated by the client.
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
            select(CoordinatorInvitation)
            .where(CoordinatorInvitation.token_hash == token_hash)
            .options(
                selectinload(CoordinatorInvitation.user),
                selectinload(CoordinatorInvitation.institution),
                selectinload(CoordinatorInvitation.campus),
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

        # Atomic single-use claim
        claimed = await self._session.execute(
            update(CoordinatorInvitation)
            .where(
                CoordinatorInvitation.id == invitation.id,
                CoordinatorInvitation.is_used == False,  # noqa: E712
                CoordinatorInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_used=True, used_at=datetime.now(UTC))
            .returning(CoordinatorInvitation.id)
            .execution_options(synchronize_session=False)
        )
        if claimed.scalar_one_or_none() is None:
            raise ConflictError(
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta.",
                code="INVITATION_ALREADY_USED",
            )

        user = invitation.user

        # 1. Update user password and activate account
        user.hashed_password = password_hasher.hash(password)
        user.is_active = True
        user.is_verified = True
        user.must_change_password = False
        user.password_changed_at = datetime.now(UTC)
        user.failed_login_attempts = 0
        user.locked_until = None

        # 2. Activate UserRole for coordinator
        role_stmt = select(Role).where(Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)))
        roles = (await self._session.execute(role_stmt)).scalars().all()
        role_ids = [r.id for r in roles]

        await self._session.execute(
            update(UserRole)
            .where(
                UserRole.user_id == user.id,
                UserRole.role_id.in_(role_ids),
                UserRole.institution_id == invitation.institution_id,
            )
            .values(is_active=True)
        )

        # 3. Invalidate any other pending invitations for this user
        await self._session.execute(
            update(CoordinatorInvitation)
            .where(
                CoordinatorInvitation.user_id == user.id,
                CoordinatorInvitation.id != invitation.id,
                CoordinatorInvitation.is_used == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COORDINATOR_ONBOARDING_COMPLETED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(user.id),
                target_type="Coordinator",
                institution_id=str(invitation.institution_id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "email": user.email,
                    "institution_id": str(invitation.institution_id),
                    "campus_id": str(invitation.campus_id) if invitation.campus_id else None,
                },
                success=True,
            ),
            session=self._session,
        )

        return user

    async def list_coordinators(
        self,
        institution_id: uuid.UUID,
        *,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CoordinatorResponse], int]:
        """
        List coordinators for a specific institution with campus and invitation metadata.
        """
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                User.institution_id == institution_id,
                Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)),
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.campus),
            )
            .distinct()
        )
        count_stmt = (
            select(func.count(func.distinct(User.id)))
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                User.institution_id == institution_id,
                Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)),
            )
        )

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        if search:
            search_pat = f"%{search.strip()}%"
            cond = or_(
                User.first_name.ilike(search_pat),
                User.last_name.ilike(search_pat),
                func.concat(User.first_name, " ", User.last_name).ilike(search_pat),
                User.email.ilike(search_pat),
                User.document_number.ilike(search_pat),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = (await self._session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        users = (await self._session.execute(stmt)).scalars().all()

        # Load latest invitations for users
        user_ids = [u.id for u in users]
        invitations_by_user: dict[uuid.UUID, CoordinatorInvitation] = {}
        if user_ids:
            inv_stmt = (
                select(CoordinatorInvitation)
                .where(CoordinatorInvitation.user_id.in_(user_ids))
                .order_by(CoordinatorInvitation.created_at.desc())
            )
            invs = (await self._session.execute(inv_stmt)).scalars().all()
            for inv in invs:
                if inv.user_id not in invitations_by_user:
                    invitations_by_user[inv.user_id] = inv

        responses: list[CoordinatorResponse] = []
        for u in users:
            inv = invitations_by_user.get(u.id)
            responses.append(self._build_coordinator_response(u, invitation=inv))

        return responses, total

    async def get_coordinator(
        self, institution_id: uuid.UUID, coordinator_id: uuid.UUID
    ) -> CoordinatorResponse:
        """Get single coordinator validating institutional tenant context."""
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                User.id == coordinator_id,
                User.institution_id == institution_id,
                Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)),
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.campus),
            )
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(
                f"Coordinador {coordinator_id} no encontrado en la institución.",
                code="COORDINATOR_NOT_FOUND",
            )

        inv_stmt = (
            select(CoordinatorInvitation)
            .where(CoordinatorInvitation.user_id == user.id)
            .order_by(CoordinatorInvitation.created_at.desc())
            .limit(1)
        )
        inv = (await self._session.execute(inv_stmt)).scalar_one_or_none()

        return self._build_coordinator_response(user, invitation=inv)

    async def update_status(
        self,
        *,
        institution_id: uuid.UUID,
        coordinator_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> CoordinatorResponse:
        """Update active status of a coordinator and invalidate sessions upon deactivation."""
        async with get_institution_lock(institution_id):
            return await self._update_status_locked(
                institution_id=institution_id,
                coordinator_id=coordinator_id,
                is_active=is_active,
                actor_id=actor_id,
                actor_ip=actor_ip,
                reason=reason,
                correlation_id=correlation_id,
            )

    async def _update_status_locked(
        self,
        *,
        institution_id: uuid.UUID,
        coordinator_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> CoordinatorResponse:
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                User.id == coordinator_id,
                User.institution_id == institution_id,
                Role.name.in_(("coordinator", SystemRole.ACADEMIC_COORDINATOR.value)),
            )
            .options(selectinload(User.user_roles).selectinload(UserRole.campus))
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(
                f"Coordinador {coordinator_id} no encontrado en la institución.",
                code="COORDINATOR_NOT_FOUND",
            )

        if is_active:
            coord_role = next((ur for ur in user.user_roles if ur.institution_id == institution_id), None)
            target_campus_id = coord_role.campus_id if coord_role else None
            await self.validate_coordinator_assignment_exclusivity(
                institution_id=institution_id,
                campus_id=target_campus_id,
                exclude_user_id=coordinator_id,
            )

        user.is_active = is_active
        for ur in user.user_roles:
            if ur.institution_id == institution_id:
                ur.is_active = is_active

        if not is_active:
            await self._session.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == coordinator_id, RefreshToken.is_revoked == False)
                .values(is_revoked=True)
                .execution_options(synchronize_session=False)
            )

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.USER_ROLE_REVOKED if not is_active else AuditEventType.USER_ROLE_ASSIGNED,
                actor_id=str(actor_id) if actor_id else str(user.id),
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="Coordinator",
                institution_id=str(institution_id),
                metadata={
                    "action": "update_coordinator_status",
                    "is_active": is_active,
                    "reason": reason,
                },
                correlation_id=correlation_id,
                success=True,
            ),
            session=self._session,
        )

        await self._session.commit()
        return self._build_coordinator_response(user)
