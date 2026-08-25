"""
PEVN Backend — Authentication Service

Implements credential authentication, Argon2id verification,
progressive account lockout, refresh token family rotation with
breach detection, and secure password recovery.

SECURITY POLICIES:
  - Zero plaintext password storage or logging
  - Account lockout after 5 consecutive failed attempts (15-minute freeze)
  - Refresh tokens stored strictly as SHA-256 digests
  - Replay of revoked refresh tokens immediately revokes the entire token family
  - Multi-tenant institutional context preserved on all auth records
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.interfaces import (
    AuthorizationContext,
    OrganizationalScope,
    SystemRole,
)
from app.core.security.interfaces import (
    Permission as SecurityPermission,
)
from app.core.security.password import password_hasher
from app.core.security.tokens import generate_raw_token, hash_token, token_service
from app.exceptions.errors import AuthenticationError
from app.models.role import Role, UserRole
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import User
from app.schemas.auth import ScopeResponse, UserMeResponse

_logger = get_logger(__name__)

# Account lockout thresholds
_MAX_FAILED_LOGIN_ATTEMPTS = 5
_LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    """
    Core authentication and session lifecycle service.
    """

    @staticmethod
    def build_auth_context(user: User) -> AuthorizationContext:
        """
        Build an AuthorizationContext from a User entity.
        """
        active_roles: list[SystemRole] = []
        permissions_list: list[SecurityPermission] = []
        institution_id_str = str(user.institution_id) if user.institution_id else None

        for ur in user.user_roles:
            if not ur.is_active:
                continue
            try:
                role_enum = SystemRole(ur.role.name)
                if role_enum not in active_roles:
                    active_roles.append(role_enum)
            except ValueError:
                pass

            for perm in ur.role.permissions:
                p = SecurityPermission(resource=perm.resource, action=perm.action)
                if p not in permissions_list:
                    permissions_list.append(p)

        # Build organizational scope
        is_national = any(
            r in {SystemRole.SUPERADMIN, SystemRole.NATIONAL_ADMIN}
            for r in active_roles
        )

        scope = OrganizationalScope(
            country_code="CO",
            department_id=None,
            municipality_id=None,
            institution_id=None if is_national else institution_id_str,
            campus_id=None,
        )

        return AuthorizationContext(
            user_id=str(user.id),
            roles=active_roles,
            permissions=permissions_list,
            scope=scope,
        )

    @staticmethod
    def build_user_me_response(user: User) -> UserMeResponse:
        """
        Serialize a User entity into the UserMeResponse schema.
        """
        context = AuthService.build_auth_context(user)
        return UserMeResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            document_type=user.document_type,
            document_number=user.document_number,
            institution_id=user.institution_id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            must_change_password=user.must_change_password,
            roles=[r.value for r in context.roles],
            permissions=[str(p) for p in context.permissions],
            scope=ScopeResponse(
                country_code=context.scope.country_code,
                department_id=context.scope.department_id,
                municipality_id=context.scope.municipality_id,
                institution_id=context.scope.institution_id,
                campus_id=context.scope.campus_id,
                is_national=context.scope.is_national(),
                is_institution=context.scope.is_institution(),
            ),
        )

    async def authenticate_user(
        self,
        db: AsyncSession,
        username_or_email: str,
        password: str,
        client_ip: str,
        user_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[User, str, str]:
        """
        Authenticate a user by credentials.

        Returns:
            Tuple of (User, access_token_jwt, raw_refresh_token).
        """
        query = (
            select(User)
            .where(
                (User.email == username_or_email.lower().strip())
                | (User.username == username_or_email.strip())
            )
            .options(
                selectinload(User.user_roles)
                .selectinload(UserRole.role)
                .selectinload(Role.permissions),
                selectinload(User.institution),
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        # 1. Unknown user
        if not user:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_LOGIN_FAILURE,
                    actor_ip=client_ip,
                    correlation_id=correlation_id,
                    success=False,
                    metadata={
                        "identifier": username_or_email,
                        "reason": "user_not_found",
                        "user_agent": user_agent,
                    },
                )
            )
            raise AuthenticationError("Credenciales inválidas.")

        # 2. Account lockout check
        if user.is_locked:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_LOGIN_FAILURE,
                    actor_id=str(user.id),
                    actor_ip=client_ip,
                    institution_id=(
                        str(user.institution_id) if user.institution_id else None
                    ),
                    correlation_id=correlation_id,
                    success=False,
                    metadata={
                        "reason": "account_locked",
                        "locked_until": (
                            user.locked_until.isoformat() if user.locked_until else None
                        ),
                        "user_agent": user_agent,
                    },
                )
            )
            raise AuthenticationError(
                "La cuenta se encuentra temporalmente bloqueada por "
                "múltiples intentos fallidos. Intente más tarde."
            )

        # 3. Inactive account check
        if not user.is_active:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_LOGIN_FAILURE,
                    actor_id=str(user.id),
                    actor_ip=client_ip,
                    institution_id=(
                        str(user.institution_id) if user.institution_id else None
                    ),
                    correlation_id=correlation_id,
                    success=False,
                    metadata={"reason": "account_inactive", "user_agent": user_agent},
                )
            )
            raise AuthenticationError("Cuenta inactiva. Contacte al administrador.")

        # 4. Verify password with Argon2id
        is_password_valid = password_hasher.verify(password, user.hashed_password)
        if not is_password_valid:
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= _MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=_LOCKOUT_DURATION_MINUTES
                )
                await audit_service.record(
                    AuditEvent(
                        event_type=AuditEventType.USER_ACCOUNT_LOCKED,
                        actor_id=str(user.id),
                        actor_ip=client_ip,
                        institution_id=(
                            str(user.institution_id) if user.institution_id else None
                        ),
                        correlation_id=correlation_id,
                        success=False,
                        metadata={
                            "failed_attempts": user.failed_login_attempts,
                            "locked_until": user.locked_until.isoformat(),
                            "user_agent": user_agent,
                        },
                    ),
                    session=db,
                )

            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_LOGIN_FAILURE,
                    actor_id=str(user.id),
                    actor_ip=client_ip,
                    institution_id=(
                        str(user.institution_id) if user.institution_id else None
                    ),
                    correlation_id=correlation_id,
                    success=False,
                    metadata={
                        "reason": "invalid_password",
                        "failed_attempts": user.failed_login_attempts,
                        "user_agent": user_agent,
                    },
                ),
                session=db,
            )
            await db.commit()
            raise AuthenticationError("Credenciales inválidas.")

        # 5. Successful password verification: reset lockout counters
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)

        # Transparent password hash upgrade if parameters changed
        if password_hasher.needs_rehash(user.hashed_password):
            user.hashed_password = password_hasher.hash(password)

        # 6. Generate Tokens
        context = self.build_auth_context(user)
        access_token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username,
                "roles": [r.value for r in context.roles],
                "institution_id": (
                    str(user.institution_id) if user.institution_id else None
                ),
            },
        )

        # 7. Generate Rotating Refresh Token
        raw_refresh_token = generate_raw_token(48)
        refresh_token_hash = hash_token(raw_refresh_token)
        family_id = uuid.uuid4()

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            family_id=family_id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_ip=client_ip,
            user_agent=user_agent,
        )
        db.add(db_refresh_token)

        # 8. Record Login Audit Event
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_LOGIN_SUCCESS,
                actor_id=str(user.id),
                actor_ip=client_ip,
                institution_id=(
                    str(user.institution_id) if user.institution_id else None
                ),
                correlation_id=correlation_id,
                success=True,
                metadata={
                    "roles": [r.value for r in context.roles],
                    "user_agent": user_agent,
                },
            ),
            session=db,
        )

        await db.commit()

        return user, access_token, raw_refresh_token

    async def rotate_refresh_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        client_ip: str,
        user_agent: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[User, str, str]:
        """
        Rotate a refresh token with automatic breach / reuse detection.

        Returns:
            Tuple of (User, new_access_token_jwt, new_raw_refresh_token).
        """
        token_hash = hash_token(raw_refresh_token)

        query = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .options(
                selectinload(RefreshToken.user)
                .selectinload(User.user_roles)
                .selectinload(UserRole.role)
                .selectinload(Role.permissions),
                selectinload(RefreshToken.user).selectinload(User.institution),
            )
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        # Unknown token
        if not token_record:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                    actor_ip=client_ip,
                    correlation_id=correlation_id,
                    success=False,
                    metadata={
                        "reason": "unknown_refresh_token",
                        "user_agent": user_agent,
                    },
                ),
                session=db,
            )
            raise AuthenticationError("Sesión inválida o expirada.")

        # REUSE / REPLAY BREACH DETECTION
        # If the token was already revoked or already replaced by a newer token:
        if token_record.is_revoked or token_record.replaced_by_token_id is not None:
            # Breach detected! Invalidate the entire token family immediately
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == token_record.family_id)
                .values(is_revoked=True)
            )
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.TOKEN_REUSE_DETECTED,
                    actor_id=str(token_record.user_id),
                    actor_ip=client_ip,
                    institution_id=(
                        str(token_record.user.institution_id)
                        if token_record.user.institution_id
                        else None
                    ),
                    correlation_id=correlation_id,
                    success=False,
                    metadata={
                        "family_id": str(token_record.family_id),
                        "token_id": str(token_record.id),
                        "user_agent": user_agent,
                        "action": "revoked_entire_token_family",
                    },
                ),
                session=db,
            )
            await db.commit()
            raise AuthenticationError(
                "Se ha detectado una reutilización de credenciales. "
                "La sesión ha sido revocada por seguridad."
            )

        # Expiration check
        if token_record.is_expired:
            raise AuthenticationError(
                "La sesión ha expirado. Inicie sesión nuevamente."
            )

        user = token_record.user
        if not user.is_active or user.is_locked:
            raise AuthenticationError("Cuenta inactiva o bloqueada.")

        # Generate new access token
        context = self.build_auth_context(user)
        access_token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "username": user.username,
                "roles": [r.value for r in context.roles],
                "institution_id": (
                    str(user.institution_id) if user.institution_id else None
                ),
            },
        )

        # Generate new refresh token in the same family
        new_raw_token = generate_raw_token(48)
        new_token_hash = hash_token(new_raw_token)

        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
            created_ip=client_ip,
            user_agent=user_agent,
        )
        db.add(new_refresh_record)
        await db.flush()

        # Link old token to new token
        token_record.replaced_by_token_id = new_refresh_record.id

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.TOKEN_REFRESH_SUCCESS,
                actor_id=str(user.id),
                actor_ip=client_ip,
                institution_id=(
                    str(user.institution_id) if user.institution_id else None
                ),
                correlation_id=correlation_id,
                success=True,
                metadata={"family_id": str(token_record.family_id)},
            ),
            session=db,
        )

        await db.commit()
        return user, access_token, new_raw_token

    async def revoke_refresh_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        actor_id: str | None = None,
        client_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> None:
        """
        Revoke an active refresh token family upon logout.
        """
        token_hash = hash_token(raw_refresh_token)
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()

        if token_record:
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == token_record.family_id)
                .values(is_revoked=True)
            )
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_LOGOUT,
                    actor_id=str(token_record.user_id),
                    actor_ip=client_ip,
                    correlation_id=correlation_id,
                    success=True,
                    metadata={"family_id": str(token_record.family_id)},
                ),
                session=db,
            )
            await db.commit()

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
        client_ip: str,
        correlation_id: str | None = None,
    ) -> None:
        """
        Update user password verifying previous password.
        """
        if not password_hasher.verify(current_password, user.hashed_password):
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_PASSWORD_CHANGED,
                    actor_id=str(user.id),
                    actor_ip=client_ip,
                    institution_id=(
                        str(user.institution_id) if user.institution_id else None
                    ),
                    correlation_id=correlation_id,
                    success=False,
                    metadata={"reason": "invalid_current_password"},
                ),
                session=db,
            )
            raise AuthenticationError("La contraseña actual es incorrecta.")

        user.hashed_password = password_hasher.hash(new_password)
        user.must_change_password = False

        # Invalidate all active refresh tokens for this user
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_PASSWORD_CHANGED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                institution_id=(
                    str(user.institution_id) if user.institution_id else None
                ),
                correlation_id=correlation_id,
                success=True,
            ),
            session=db,
        )
        await db.commit()

    async def request_password_reset(
        self,
        db: AsyncSession,
        email: str,
        client_ip: str,
        correlation_id: str | None = None,
    ) -> str | None:
        """
        Initiate password recovery flow. Returns raw token for email dispatch.
        """
        query = select(User).where(User.email == email.lower().strip())
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            # Record audit but return gracefully to avoid enumeration
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_PASSWORD_RESET_REQUESTED,
                    actor_ip=client_ip,
                    correlation_id=correlation_id,
                    success=False,
                    metadata={"email": email, "reason": "user_not_found_or_inactive"},
                ),
                session=db,
            )
            return None

        raw_reset_token = generate_raw_token(32)
        reset_token_hash = hash_token(raw_reset_token)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=reset_token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            is_used=False,
        )
        db.add(reset_record)

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_PASSWORD_RESET_REQUESTED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                institution_id=(
                    str(user.institution_id) if user.institution_id else None
                ),
                correlation_id=correlation_id,
                success=True,
            ),
            session=db,
        )
        await db.commit()
        return raw_reset_token

    async def confirm_password_reset(
        self,
        db: AsyncSession,
        raw_reset_token: str,
        new_password: str,
        client_ip: str,
        correlation_id: str | None = None,
    ) -> None:
        """
        Complete password recovery using single-use token.
        """
        reset_token_hash = hash_token(raw_reset_token)
        query = (
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == reset_token_hash)
            .options(selectinload(PasswordResetToken.user))
        )
        result = await db.execute(query)
        reset_record = result.scalar_one_or_none()

        if not reset_record or not reset_record.is_valid:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.USER_PASSWORD_RESET_CONFIRMED,
                    actor_ip=client_ip,
                    correlation_id=correlation_id,
                    success=False,
                    metadata={"reason": "invalid_or_expired_reset_token"},
                ),
                session=db,
            )
            raise AuthenticationError(
                "El token de restablecimiento es inválido o ha expirado."
            )

        user = reset_record.user
        user.hashed_password = password_hasher.hash(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        reset_record.is_used = True

        # Invalidate all active sessions for security
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(is_revoked=True)
        )

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.USER_PASSWORD_RESET_CONFIRMED,
                actor_id=str(user.id),
                actor_ip=client_ip,
                institution_id=(
                    str(user.institution_id) if user.institution_id else None
                ),
                correlation_id=correlation_id,
                success=True,
            ),
            session=db,
        )
        await db.commit()


# Default auth service instance
auth_service: AuthService = AuthService()
