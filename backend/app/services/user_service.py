"""
PEVN Backend — User Domain Service

Authoritative business logic for user search, institutional account listing,
and identity lookups constrained strictly by organizational tenant boundaries.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.password import password_hasher
from app.core.security.tokens import generate_raw_token
from app.exceptions.errors import ConflictError, NotFoundError
from app.models.role import Role, UserRole
from app.models.user import DocumentType, User

_logger = get_logger(__name__)


class UserService:
    """
    Domain service for tenant-scoped User queries and management.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def list_users(
        self,
        *,
        institution_id: uuid.UUID | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """
        Search and list users strictly constrained by organizational tenant boundary.

        If `institution_id` is provided, only users belonging to that institution
        are returned (cross-tenant isolation). If `institution_id` is None, this
        is only permissible for national administrators / superadmins.
        """
        stmt = select(User).options(
            selectinload(User.user_roles),
            selectinload(User.institution),
        )
        count_stmt = select(func.count(User.id))

        # Tenant isolation filter
        if institution_id is not None:
            stmt = stmt.where(User.institution_id == institution_id)
            count_stmt = count_stmt.where(User.institution_id == institution_id)

        # Active filter
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        # Search filter (name, full name, document_number e.g. '8788', email, username)
        if search:
            search_clean = search.strip()
            search_pattern = f"%{search_clean}%"
            filter_condition = or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                func.concat(User.first_name, " ", User.last_name).ilike(search_pattern),
                User.document_number.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.username.ilike(search_pattern),
            )
            stmt = stmt.where(filter_condition)
            count_stmt = count_stmt.where(filter_condition)

        # Execute total count
        total = (await self._session.execute(count_stmt)).scalar_one()

        # Ordering and pagination
        stmt = (
            stmt.order_by(User.last_name.asc(), User.first_name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    async def get_user_by_id(
        self,
        *,
        user_id: uuid.UUID,
        institution_id: uuid.UUID | None = None,
    ) -> User:
        """
        Retrieve user by ID ensuring institutional tenant containment.
        """
        stmt = select(User).where(User.id == user_id).options(
            selectinload(User.user_roles),
            selectinload(User.institution),
        )
        if institution_id is not None:
            stmt = stmt.where(User.institution_id == institution_id)

        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError(f"Usuario {user_id} no encontrado en el contexto institucional.")
        return user

    async def provision_institutional_user(
        self,
        *,
        institution_id: uuid.UUID,
        first_name: str,
        last_name: str,
        document_type: DocumentType,
        document_number: str,
        email: str,
        role_name: str = "teacher",
        is_active: bool = True,
        is_verified: bool = False,
        must_change_password: bool = True,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> User:
        """
        Authoritative domain method for provisioning a new institutional User account
        and assigning their canonical institutional role within an atomic transaction.
        """
        clean_first = first_name.strip()
        clean_last = last_name.strip()
        clean_doc = document_number.strip()
        clean_email = email.strip().lower()

        # 1. Uniqueness check for document (document_type + document_number)
        doc_stmt = select(User).where(
            User.document_type == document_type,
            User.document_number == clean_doc,
        )
        existing_doc_user = (await self._session.execute(doc_stmt)).scalar_one_or_none()
        if existing_doc_user:
            raise ConflictError(
                "El documento o correo electrónico ya se encuentra registrado en el sistema.",
                code="IDENTITY_CONFLICT",
            )

        # 2. Uniqueness check for email
        email_stmt = select(User).where(User.email == clean_email)
        existing_email_user = (await self._session.execute(email_stmt)).scalar_one_or_none()
        if existing_email_user:
            raise ConflictError(
                "El documento o correo electrónico ya se encuentra registrado en el sistema.",
                code="IDENTITY_CONFLICT",
            )

        # 3. Derive unique username handle
        base_username = clean_email.split("@")[0].replace(".", "_")
        username_candidate = base_username
        user_stmt = select(User).where(User.username == username_candidate)
        if (await self._session.execute(user_stmt)).scalar_one_or_none():
            username_candidate = f"{base_username}_{clean_doc[-4:]}"

        # 4. Generate secure initial credential (never plaintext)
        raw_initial_password = generate_raw_token(16)
        hashed_password = password_hasher.hash(raw_initial_password)

        # 5. Create User entity with proper security flags
        user = User(
            institution_id=institution_id,
            email=clean_email,
            username=username_candidate,
            hashed_password=hashed_password,
            first_name=clean_first,
            last_name=clean_last,
            document_type=document_type,
            document_number=clean_doc,
            is_active=is_active,
            is_verified=is_verified,
            must_change_password=must_change_password,
        )
        self._session.add(user)
        await self._session.flush()

        # 6. Resolve canonical role and link UserRole
        role_stmt = select(Role).where(Role.name == role_name)
        role_obj = (await self._session.execute(role_stmt)).scalar_one_or_none()
        if not role_obj:
            from app.services.rbac_bootstrap_service import RbacBootstrapService
            bootstrap = RbacBootstrapService(session=self._session)
            await bootstrap.seed_canonical_rbac_if_needed()
            role_obj = (await self._session.execute(role_stmt)).scalar_one()

        user_role = UserRole(
            user_id=user.id,
            role_id=role_obj.id,
            institution_id=institution_id,
            is_active=is_active,
        )
        self._session.add(user_role)
        await self._session.flush()

        # 7. Audit log user creation
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.USER_CREATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(user.id),
                target_type="User",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "document_type": document_type.value,
                    "document_number": clean_doc,
                    "email": clean_email,
                    "role": role_name,
                },
            ),
            session=self._session,
        )

        return user
