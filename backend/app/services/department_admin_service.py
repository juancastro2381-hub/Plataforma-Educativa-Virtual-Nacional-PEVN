"""
PEVN Backend — Department Administrator Domain Service

Implements authoritative, transactional lifecycle management for DEPARTMENT_ADMIN users:
  - Canonical department assignment validation against `departments` table
  - Transactional user & user_role provisioning
  - Profile modification and status transitions
  - Explicit department reassignment with audit logging and session token revocation
  - Prevention of unauthorized privilege elevation or cross-department access
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
from app.models.invitation import DepartmentAdminInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.schemas.department_admin import (
    DepartmentAdminCreateRequest,
    DepartmentAdminInvitationResponse,
    DepartmentAdminKPIs,
    DepartmentAdminResponse,
    DepartmentAdminUpdateRequest,
    DepartmentOptionResponse,
)
from app.services.email_service import EmailDeliveryStatus, EmailService

_logger = get_logger(__name__)


class DepartmentAdminInviteResult(tuple):
    """Backwards-compatible tuple for (invitation, raw_token) with delivery attributes."""

    def __new__(
        cls,
        invitation: DepartmentAdminInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
        user: User | None = None,
        department: Department | None = None,
    ) -> DepartmentAdminInviteResult:
        return super().__new__(cls, (invitation, raw_token))

    def __init__(
        self,
        invitation: DepartmentAdminInvitation,
        raw_token: str,
        delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        activation_url: str | None = None,
        user: User | None = None,
        department: Department | None = None,
    ) -> None:
        self.invitation = invitation
        self.raw_token = raw_token
        self.delivery_status = delivery_status
        self.activation_url = activation_url
        self.user = user
        self.department = department


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


class DepartmentAdminService:
    """
    Authoritative business logic for DEPARTMENT_ADMIN lifecycle and territorial provisioning.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
        email_service: EmailService | None = None,
    ) -> None:
        self._session = session
        self._audit = audit
        self._email = email_service or EmailService()

    async def list_departments(self) -> list[DepartmentOptionResponse]:
        """
        List all canonical departments populated in the operational database.
        """
        stmt = select(Department).order_by(Department.code.asc())
        result = await self._session.execute(stmt)
        depts = result.scalars().all()
        return [
            DepartmentOptionResponse(
                id=d.id,
                code=d.code,
                name=d.name,
                display_label=f"{d.code} — {d.name}",
            )
            for d in depts
        ]

    async def get_kpis(self) -> DepartmentAdminKPIs:
        """
        Calculate authoritative server-side KPI counts for the DEPARTMENT_ADMIN population.
        Strictly enforces the mathematical invariant: total = active + inactive.
        Coverage: distinct departments provisioned with >= 1 administrator out of 33 canonical Colombian entities.
        """
        stmt = (
            select(User.id, User.is_active, UserRole.department_id)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == SystemRole.DEPARTMENT_ADMIN.value,
                UserRole.department_id.isnot(None),
            )
        )
        rows = (await self._session.execute(stmt)).fetchall()

        # Deduplicate per User.id
        user_states: dict[uuid.UUID, tuple[bool, uuid.UUID]] = {}
        for uid, is_act, dept_id in rows:
            user_states[uid] = (is_act, dept_id)

        total = len(user_states)
        active = sum(1 for is_act, _ in user_states.values() if is_act is True)
        inactive = sum(1 for is_act, _ in user_states.values() if is_act is False)
        distinct_depts = len(set(dept_id for _, dept_id in user_states.values() if dept_id is not None))

        return DepartmentAdminKPIs(
            total=total,
            active=active,
            inactive=inactive,
            departments_covered=distinct_depts,
            total_canonical_departments=33,
        )

    async def list_department_admins(
        self,
        *,
        department_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DepartmentAdminResponse], int, DepartmentAdminKPIs]:
        """
        List and search DEPARTMENT_ADMIN accounts with optional territorial and status filters.
        Enforces that only accounts with an assigned canonical department are included.
        """
        stmt = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == SystemRole.DEPARTMENT_ADMIN.value,
                UserRole.department_id.isnot(None),
            )
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.user_roles).selectinload(UserRole.department),
            )
        )
        count_stmt = (
            select(func.count(func.distinct(User.id)))
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                Role.name == SystemRole.DEPARTMENT_ADMIN.value,
                UserRole.department_id.isnot(None),
            )
        )

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

        items: list[DepartmentAdminResponse] = []
        for u in users:
            dept_role = next(
                (ur for ur in u.user_roles if ur.role.name == SystemRole.DEPARTMENT_ADMIN.value and ur.department_id),
                None,
            )
            if dept_role and dept_role.department:
                items.append(self._build_admin_response(u, dept_role.department))

        kpis = await self.get_kpis()
        return items, total, kpis


    async def get_department_admin(self, user_id: uuid.UUID) -> DepartmentAdminResponse:
        """
        Retrieve a single DEPARTMENT_ADMIN by user UUID.
        """
        user = await self._load_department_admin_user(user_id)
        dept_role = self._extract_department_role(user)
        return self._build_admin_response(user, dept_role.department)

    async def create_department_admin(
        self,
        payload: DepartmentAdminCreateRequest,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> DepartmentAdminResponse:
        """
        Transactionally create a DEPARTMENT_ADMIN account and persist the territorial scope.
        """
        # 1. Validate canonical department existence
        dept = await self._session.get(Department, payload.department_id)
        if not dept:
            raise NotFoundError(
                f"El departamento con ID {payload.department_id} no existe en el catálogo territorial del sistema.",
                code="DEPARTMENT_NOT_FOUND",
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
            else f"DA{secrets.randbelow(90000000) + 10000000}"
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

        # 4. Credential and activation state
        has_initial_password = bool(payload.password and payload.password.strip())
        if has_initial_password:
            raw_password = payload.password.strip()
            if len(raw_password) < 8:
                raise UnprocessableEntityError("La contraseña debe tener al menos 8 caracteres.")
            hashed_password = password_hasher.hash(raw_password)
            is_active = payload.is_active if payload.is_active is not None else True
            is_verified = True
            must_change_password = False
        else:
            # Pre-registered inactive account with unguessable random hash
            unusable_hash = password_hasher.hash(generate_raw_token(32))
            hashed_password = unusable_hash
            is_active = False
            is_verified = False
            must_change_password = False

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

        # 6. Resolve canonical DEPARTMENT_ADMIN role
        role_stmt = select(Role).where(Role.name == SystemRole.DEPARTMENT_ADMIN.value)
        role = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role:
            raise NotFoundError("Rol canónico department_admin no configurado en la base de datos.")

        # 7. Create UserRole with strictly validated department_id
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            department_id=dept.id,
            institution_id=None,
            campus_id=None,
            is_active=is_active,
        )
        self._session.add(user_role)
        await self._session.flush()

        # 8. Revoke any prior pending invitations for this user
        await self._session.execute(
            update(DepartmentAdminInvitation)
            .where(
                DepartmentAdminInvitation.user_id == user.id,
                DepartmentAdminInvitation.is_used == False,  # noqa: E712
                DepartmentAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        # 9. Generate high-entropy 48-byte URL-safe raw token and compute SHA-256 hash
        raw_invitation_token = generate_raw_token(48)
        token_hash = hash_token(raw_invitation_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = DepartmentAdminInvitation(
            department_id=dept.id,
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
        activation_url = f"/invitation/accept?token={raw_invitation_token}"
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Administrador Departamental",
            jurisdiction_label=f"{dept.name} (DANE {dept.code})",
            activation_url=activation_url,
        )

        # 11. Record audit trail
        creation_event = AuditEvent(
            event_type=AuditEventType.DEPARTMENT_ADMIN_CREATED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="department_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "actor_user_id": str(actor_id) if actor_id else None,
                "target_user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "department_id": str(dept.id),
                "department_code": dept.code,
                "department_name": dept.name,
                "invitation_id": str(invitation.id),
                "email_delivery_status": delivery_status.value,
            },
        )
        await self._audit.record(creation_event, session=self._session)

        invitation_event = AuditEvent(
            event_type=AuditEventType.DEPARTMENT_ADMIN_INVITED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="User",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "invitation_id": str(invitation.id),
                "admin_email": user.email,
                "department_id": str(dept.id),
                "department_code": dept.code,
                "department_name": dept.name,
                "expires_at": expires_at.isoformat(),
                "email_delivery_status": delivery_status.value,
            },
        )
        await self._audit.record(invitation_event, session=self._session)

        if delivery_status == EmailDeliveryStatus.EMAIL_SENT:
            sent_event = AuditEvent(
                event_type=AuditEventType.DEPARTMENT_ADMIN_INVITATION_SENT,
                actor_ip=actor_ip,
                actor_id=str(actor_id) if actor_id else None,
                target_type="User",
                target_id=str(user.id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "admin_email": user.email,
                    "department_id": str(dept.id),
                    "department_code": dept.code,
                },
            )
            await self._audit.record(sent_event, session=self._session)

        _logger.info(
            "DEPARTMENT_ADMIN user created and invitation issued",
            user_id=str(user.id),
            username=user.username,
            department_code=dept.code,
            department_name=dept.name,
            invitation_id=str(invitation.id),
            email_delivery_status=delivery_status.value,
        )

        return self._build_admin_response(
            user,
            dept,
            raw_invitation_token=raw_invitation_token,
            invitation_id=invitation.id,
            email_delivery_status=delivery_status,
            invitation_url=activation_url,
        )

    async def update_department_admin(
        self,
        user_id: uuid.UUID,
        payload: DepartmentAdminUpdateRequest,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> DepartmentAdminResponse:
        """
        Update basic profile information or status of an existing DEPARTMENT_ADMIN.
        """
        user = await self._load_department_admin_user(user_id)
        dept_role = self._extract_department_role(user)

        if payload.first_name is not None:
            user.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            user.last_name = payload.last_name.strip()
        if payload.document_number is not None:
            user.document_number = payload.document_number.strip()

        if payload.email is not None:
            clean_email = payload.email.strip().lower()
            if clean_email != user.email:
                email_check = (
                    await self._session.execute(
                        select(User.id).where(User.email == clean_email, User.id != user.id)
                    )
                ).scalar_one_or_none()
                if email_check:
                    raise ConflictError(
                        "El nuevo correo electrónico ya está en uso.",
                        code="EMAIL_CONFLICT",
                    )
                user.email = clean_email

        if payload.is_active is not None:
            user.is_active = payload.is_active
            dept_role.is_active = payload.is_active
            if not payload.is_active:
                await self._revoke_user_sessions(user.id)

        await self._session.flush()

        event = AuditEvent(
            event_type=AuditEventType.DEPARTMENT_ADMIN_UPDATED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="department_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "actor_user_id": str(actor_id) if actor_id else None,
                "target_user_id": str(user.id),
                "username": user.username,
                "is_active": user.is_active,
                "department_code": dept_role.department.code,
            },
        )
        await self._audit.record(event, session=self._session)

        return self._build_admin_response(user, dept_role.department)

    async def reassign_department(
        self,
        user_id: uuid.UUID,
        new_department_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> DepartmentAdminResponse:
        """
        Explicitly reassign a DEPARTMENT_ADMIN to another canonical department.
        Invalidates active session refresh tokens to prevent stale authorization scopes.
        """
        user = await self._load_department_admin_user(user_id)
        dept_role = self._extract_department_role(user)

        new_dept = await self._session.get(Department, new_department_id)
        if not new_dept:
            raise NotFoundError(
                f"El departamento destino con ID {new_department_id} no existe en el sistema.",
                code="DEPARTMENT_NOT_FOUND",
            )

        prev_dept_id = str(dept_role.department_id)
        prev_dept_code = dept_role.department.code if dept_role.department else None

        # Reassign foreign key
        dept_role.department_id = new_dept.id

        # Invalidate active session refresh tokens so next refresh rebuilds context
        await self._revoke_user_sessions(user.id)

        await self._session.flush()

        event = AuditEvent(
            event_type=AuditEventType.DEPARTMENT_ADMIN_DEPARTMENT_CHANGED,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="department_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "actor_user_id": str(actor_id) if actor_id else None,
                "target_user_id": str(user.id),
                "previous_department_id": prev_dept_id,
                "previous_department_code": prev_dept_code,
                "new_department_id": str(new_dept.id),
                "new_department_code": new_dept.code,
                "reason": reason,
            },
        )
        await self._audit.record(event, session=self._session)

        _logger.info(
            "DEPARTMENT_ADMIN reassigned to new department",
            user_id=str(user.id),
            previous_department=prev_dept_code,
            new_department=new_dept.code,
        )

        return self._build_admin_response(user, new_dept)

    async def update_status(
        self,
        user_id: uuid.UUID,
        is_active: bool,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        reason: str | None = None,
        correlation_id: str | None = None,
    ) -> DepartmentAdminResponse:
        """
        Activate or deactivate a DEPARTMENT_ADMIN account.
        """
        user = await self._load_department_admin_user(user_id)
        dept_role = self._extract_department_role(user)

        user.is_active = is_active
        dept_role.is_active = is_active

        if not is_active:
            await self._revoke_user_sessions(user.id)

        await self._session.flush()

        event_type = (
            AuditEventType.DEPARTMENT_ADMIN_ACTIVATED
            if is_active
            else AuditEventType.DEPARTMENT_ADMIN_DEACTIVATED
        )
        event = AuditEvent(
            event_type=event_type,
            actor_ip=actor_ip,
            actor_id=str(actor_id) if actor_id else None,
            target_type="department_admin",
            target_id=str(user.id),
            correlation_id=correlation_id,
            metadata={
                "actor_user_id": str(actor_id) if actor_id else None,
                "target_user_id": str(user.id),
                "is_active": is_active,
                "department_code": dept_role.department.code,
                "reason": reason,
            },
        )
        await self._audit.record(event, session=self._session)

        return self._build_admin_response(user, dept_role.department)

    async def _load_department_admin_user(self, user_id: uuid.UUID) -> User:
        """Load user by ID and ensure they have the DEPARTMENT_ADMIN role."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
                selectinload(User.user_roles).selectinload(UserRole.department),
            )
        )
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(f"Usuario con ID {user_id} no encontrado.")

        has_dept_role = any(
            ur.role.name == SystemRole.DEPARTMENT_ADMIN.value for ur in user.user_roles if ur.role
        )
        if not has_dept_role:
            raise NotFoundError(
                f"El usuario {user_id} no posee el rol de Administrador Departamental.",
                code="NOT_DEPARTMENT_ADMIN",
            )

        return user

    def _extract_department_role(self, user: User) -> UserRole:
        """Extract the active DEPARTMENT_ADMIN UserRole record."""
        dept_role = next(
            (
                ur
                for ur in user.user_roles
                if ur.role and ur.role.name == SystemRole.DEPARTMENT_ADMIN.value and ur.department
            ),
            None,
        )
        if not dept_role or not dept_role.department:
            raise NotFoundError("El usuario no tiene una asignación departamental válida.")
        return dept_role

    async def _revoke_user_sessions(self, user_id: uuid.UUID) -> None:
        """Mark all active refresh tokens for the user as revoked."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True)
            .execution_options(synchronize_session=False)
        )

    def _build_admin_response(
        self,
        user: User,
        dept: Department,
        *,
        raw_invitation_token: str | None = None,
        invitation_id: uuid.UUID | None = None,
        email_delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        invitation_url: str | None = None,
    ) -> DepartmentAdminResponse:
        """Build standard serialized response."""
        user_dict = user.__dict__
        return DepartmentAdminResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=f"{user.first_name} {user.last_name}".strip(),
            document_type=user.document_type,
            document_number=user.document_number,
            role=SystemRole.DEPARTMENT_ADMIN.value,
            role_code=SystemRole.DEPARTMENT_ADMIN.value,
            department_id=dept.id,
            department_code=dept.code,
            department_name=dept.name,
            is_active=bool(user_dict.get("is_active", user.is_active)),
            is_verified=bool(user_dict.get("is_verified", user.is_verified)),
            created_at=user_dict.get("created_at") or datetime.now(UTC),
            updated_at=user_dict.get("updated_at"),
            last_login_at=user_dict.get("last_login_at"),
            raw_invitation_token=raw_invitation_token,
            invitation_id=invitation_id,
            email_delivery_status=email_delivery_status,
            invitation_url=invitation_url,
        )

    async def resend_invitation(
        self,
        user_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> DepartmentAdminInviteResult:
        """
        Resend onboarding invitation to an existing DEPARTMENT_ADMIN.
        Invalidates any prior pending invitation tokens and generates a fresh one.
        """
        user = await self._load_department_admin_user(user_id)
        dept_role = self._extract_department_role(user)
        dept = dept_role.department

        # Invalidate prior pending invitations
        await self._session.execute(
            update(DepartmentAdminInvitation)
            .where(
                DepartmentAdminInvitation.user_id == user.id,
                DepartmentAdminInvitation.is_used == False,  # noqa: E712
                DepartmentAdminInvitation.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        raw_token = generate_raw_token(48)
        token_hash = hash_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=48)

        invitation = DepartmentAdminInvitation(
            department_id=dept.id,
            user_id=user.id,
            token_hash=token_hash,
            invited_by_id=uuid.UUID(str(actor_id)) if actor_id else None,
            expires_at=expires_at,
            is_used=False,
            is_revoked=False,
        )
        invitation.user = user
        invitation.department = dept
        self._session.add(invitation)
        await self._session.flush()

        # Attempt email delivery
        activation_url = f"/invitation/accept?token={raw_token}"
        delivery_status = await self._email.send_invitation_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}",
            role_label="Administrador Departamental",
            jurisdiction_label=f"{dept.name} (DANE {dept.code})",
            activation_url=activation_url,
        )

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.DEPARTMENT_ADMIN_INVITATION_RESENT,
                actor_ip=actor_ip,
                actor_id=str(actor_id) if actor_id else None,
                target_type="User",
                target_id=str(user.id),
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "admin_email": user.email,
                    "department_id": str(dept.id),
                    "department_code": dept.code,
                    "expires_at": expires_at.isoformat(),
                    "email_delivery_status": delivery_status.value,
                },
            ),
            session=self._session,
        )

        if delivery_status == EmailDeliveryStatus.EMAIL_SENT:
            await self._audit.record(
                AuditEvent(
                    event_type=AuditEventType.DEPARTMENT_ADMIN_INVITATION_SENT,
                    actor_ip=actor_ip,
                    actor_id=str(actor_id) if actor_id else None,
                    target_type="User",
                    target_id=str(user.id),
                    correlation_id=correlation_id,
                    metadata={
                        "invitation_id": str(invitation.id),
                        "admin_email": user.email,
                        "department_id": str(dept.id),
                        "department_code": dept.code,
                    },
                ),
                session=self._session,
            )

        _logger.info(
            "DEPARTMENT_ADMIN invitation resent",
            user_id=str(user.id),
            department_code=dept.code,
            invitation_id=str(invitation.id),
            email_delivery_status=delivery_status.value,
        )

        return DepartmentAdminInviteResult(
            invitation,
            raw_token,
            delivery_status=delivery_status,
            activation_url=activation_url,
            user=user,
            department=dept,
        )

    async def verify_invitation(
        self,
        *,
        token: str,
    ) -> dict[str, Any]:
        """
        Validate a department administrator invitation token for the public onboarding screen.
        """
        if not token or not token.strip():
            raise NotFoundError("Token de invitación no suministrado.", code="INVITATION_NOT_FOUND")

        token_hash = hash_token(token.strip())
        stmt = (
            select(DepartmentAdminInvitation)
            .where(DepartmentAdminInvitation.token_hash == token_hash)
            .options(
                selectinload(DepartmentAdminInvitation.user),
                selectinload(DepartmentAdminInvitation.department),
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
                "Esta invitación ya fue utilizada anteriormente para activar la cuenta de Administrador Departamental.",
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
            "department_name": invitation.department.name,
            "department_code": invitation.department.code,
            "role_name": "department_admin",
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
        Redeem department admin invitation, set Argon2id password, activate user and territorial UserRole.
        Guarantees that role and department scope cannot be manipulated by the client.
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
            select(DepartmentAdminInvitation)
            .where(DepartmentAdminInvitation.token_hash == token_hash)
            .options(
                selectinload(DepartmentAdminInvitation.user),
                selectinload(DepartmentAdminInvitation.department),
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

        user = invitation.user
        dept = invitation.department

        # 1. Update user password with Argon2id and activate account
        user.hashed_password = password_hasher.hash(password)
        user.is_active = True
        user.is_verified = True
        user.password_changed_at = datetime.now(UTC)
        user.failed_login_attempts = 0
        user.locked_until = None

        # 2. Activate UserRole for DEPARTMENT_ADMIN strictly for the bound department
        role_stmt = select(Role).where(Role.name == SystemRole.DEPARTMENT_ADMIN.value)
        da_role = (await self._session.execute(role_stmt)).scalar_one()

        await self._session.execute(
            update(UserRole)
            .where(
                UserRole.user_id == user.id,
                UserRole.role_id == da_role.id,
                UserRole.department_id == dept.id,
            )
            .values(is_active=True)
        )

        # 3. Mark invitation as used
        invitation.is_used = True
        invitation.used_at = datetime.now(UTC)

        # 4. Invalidate any other pending invitations for this user
        await self._session.execute(
            update(DepartmentAdminInvitation)
            .where(
                DepartmentAdminInvitation.user_id == user.id,
                DepartmentAdminInvitation.id != invitation.id,
                DepartmentAdminInvitation.is_used == False,  # noqa: E712
            )
            .values(is_revoked=True, revoked_at=datetime.now(UTC))
        )

        await self._session.flush()

        # 5. Record audit trail
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.DEPARTMENT_ADMIN_ONBOARDING_COMPLETED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                target_id=str(user.id),
                target_type="User",
                correlation_id=correlation_id,
                metadata={
                    "invitation_id": str(invitation.id),
                    "email": user.email,
                    "department_id": str(dept.id),
                    "department_code": dept.code,
                    "department_name": dept.name,
                },
            ),
            session=self._session,
        )

        _logger.info(
            "DEPARTMENT_ADMIN onboarding completed",
            user_id=str(user.id),
            email=user.email,
            department_code=dept.code,
            department_name=dept.name,
        )

        return user

