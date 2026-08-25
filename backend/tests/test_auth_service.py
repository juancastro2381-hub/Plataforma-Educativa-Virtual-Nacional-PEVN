"""
PEVN Backend — Authentication Service Integration Tests

Tests credential validation, progressive account lockout, rotating refresh tokens,
breach / replay detection with family revocation, password change, and password reset.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.exceptions.errors import AuthenticationError
from app.models.audit_log import AuditLog
from app.models.role import Role, UserRole
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.services.auth_service import auth_service


async def _create_test_user(
    db: AsyncSession,
    email: str = "teacher@pevn.edu.co",
    username: str = "teacher1",
    password: str = "SecurePass123!",
    role_name: str = SystemRole.TEACHER.value,
    institution_id: uuid.UUID | None = None,
) -> User:
    """Helper to create an active test user with role and password hash."""
    user = User(
        email=email,
        username=username,
        hashed_password=password_hasher.hash(password),
        first_name="Profesor",
        last_name="Prueba",
        document_type=DocumentType.CC,
        document_number=str(uuid.uuid4().int)[:10],
        institution_id=institution_id,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    db.add(user)
    await db.flush()

    role_res = await db.execute(select(Role).where(Role.name == role_name))
    role = role_res.scalar_one()

    user_role = UserRole(
        user_id=user.id,
        role_id=role.id,
        institution_id=institution_id,
        is_active=True,
    )
    db.add(user_role)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_auth_service_successful_login(db_session: AsyncSession) -> None:
    """Test successful authentication returns User, JWT access token, and refresh token."""
    raw_password = "CorrectPassword123!"
    user = await _create_test_user(db_session, password=raw_password)

    auth_user, access_token, raw_refresh_token = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.email,
        password=raw_password,
        client_ip="192.168.1.100",
        user_agent="TestAgent/1.0",
    )

    assert auth_user.id == user.id
    assert isinstance(access_token, str)
    assert isinstance(raw_refresh_token, str)
    assert len(raw_refresh_token) >= 48

    # Verify audit log record was created
    audit_res = await db_session.execute(
        select(AuditLog).where(AuditLog.actor_id == user.id)
    )
    audit_entry = audit_res.scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.event_type == "user.login.success"


@pytest.mark.asyncio
async def test_auth_service_failed_login_and_lockout(
    db_session: AsyncSession,
) -> None:
    """Test that 5 consecutive failed attempts trigger account lockout."""
    user = await _create_test_user(db_session, password="RealPassword123!")

    # 4 failed attempts: increment failed counter
    for _ in range(4):
        with pytest.raises(AuthenticationError, match="Credenciales inválidas"):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=user.email,
                password="WrongPassword!",
                client_ip="192.168.1.100",
            )

    await db_session.refresh(user)
    assert user.failed_login_attempts == 4
    assert user.is_locked is False

    # 5th failed attempt: triggers lockout
    with pytest.raises(AuthenticationError, match="Credenciales inválidas"):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.email,
            password="WrongPassword!",
            client_ip="192.168.1.100",
        )

    await db_session.refresh(user)
    assert user.failed_login_attempts == 5
    assert user.is_locked is True
    assert user.locked_until is not None

    # Subsequent login attempt is blocked by lockout
    with pytest.raises(AuthenticationError, match="temporalmente bloqueada"):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.email,
            password="RealPassword123!",  # Even with correct password
            client_ip="192.168.1.100",
        )


@pytest.mark.asyncio
async def test_refresh_token_rotation_success(db_session: AsyncSession) -> None:
    """Test normal rotation: old token is linked to new token, new access token is returned."""
    user = await _create_test_user(db_session)

    _u, _acc, raw_refresh1 = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="SecurePass123!",
        client_ip="10.0.0.1",
    )

    # First rotation
    auth_user, new_access, raw_refresh2 = await auth_service.rotate_refresh_token(
        db=db_session,
        raw_refresh_token=raw_refresh1,
        client_ip="10.0.0.1",
    )

    assert auth_user.id == user.id
    assert isinstance(new_access, str)
    assert raw_refresh2 != raw_refresh1

    # Second rotation with the new token
    _u2, _new_access2, raw_refresh3 = await auth_service.rotate_refresh_token(
        db=db_session,
        raw_refresh_token=raw_refresh2,
        client_ip="10.0.0.1",
    )
    assert raw_refresh3 != raw_refresh2


@pytest.mark.asyncio
async def test_refresh_token_replay_breach_detection_revokes_family(
    db_session: AsyncSession,
) -> None:
    """
    CRITICAL SECURITY TEST:
    If an attacker replays raw_refresh1 (which was already rotated to raw_refresh2),
    breach detection MUST trigger, revoke the ENTIRE token family, and block all sessions.
    """
    user = await _create_test_user(db_session)

    _u, _acc, raw_refresh1 = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="SecurePass123!",
        client_ip="10.0.0.1",
    )

    # Legitimate client rotates raw_refresh1 -> raw_refresh2
    _u, _acc2, raw_refresh2 = await auth_service.rotate_refresh_token(
        db=db_session,
        raw_refresh_token=raw_refresh1,
        client_ip="10.0.0.1",
    )

    # Attacker tries to replay the old raw_refresh1!
    with pytest.raises(AuthenticationError, match="reutilización de credenciales"):
        await auth_service.rotate_refresh_token(
            db=db_session,
            raw_refresh_token=raw_refresh1,
            client_ip="198.51.100.2",
        )

    # Verify that the entire family (including raw_refresh2) is now revoked!
    tokens_res = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    tokens = tokens_res.scalars().all()
    assert len(tokens) == 2
    for t in tokens:
        assert t.is_revoked is True

    # Legitimate client attempting to use raw_refresh2 is now also rejected
    with pytest.raises(AuthenticationError, match="reutilización de credenciales"):
        await auth_service.rotate_refresh_token(
            db=db_session,
            raw_refresh_token=raw_refresh2,
            client_ip="10.0.0.1",
        )


@pytest.mark.asyncio
async def test_password_change_invalidates_active_tokens(
    db_session: AsyncSession,
) -> None:
    """Test changing password validates current password and invalidates existing sessions."""
    user = await _create_test_user(db_session, password="OldPassword123!")

    # Login to create an active session
    _u, _acc, raw_refresh = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.email,
        password="OldPassword123!",
        client_ip="127.0.0.1",
    )

    # Wrong current password fails
    with pytest.raises(AuthenticationError, match="incorrecta"):
        await auth_service.change_password(
            db=db_session,
            user=user,
            current_password="WrongOldPassword!",
            new_password="BrandNewPassword456!",
            client_ip="127.0.0.1",
        )

    # Correct current password succeeds
    await auth_service.change_password(
        db=db_session,
        user=user,
        current_password="OldPassword123!",
        new_password="BrandNewPassword456!",
        client_ip="127.0.0.1",
    )

    # Old refresh token is now revoked
    with pytest.raises(AuthenticationError):
        await auth_service.rotate_refresh_token(
            db=db_session,
            raw_refresh_token=raw_refresh,
            client_ip="127.0.0.1",
        )

    # Login with new password works
    auth_user, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.email,
        password="BrandNewPassword456!",
        client_ip="127.0.0.1",
    )
    assert auth_user.id == user.id


@pytest.mark.asyncio
async def test_password_reset_flow(db_session: AsyncSession) -> None:
    """Test full password reset request -> confirm cycle with single-use token."""
    user = await _create_test_user(db_session, password="InitialPassword123!")

    # 1. Request reset
    reset_token = await auth_service.request_password_reset(
        db=db_session,
        email=user.email,
        client_ip="127.0.0.1",
    )
    assert reset_token is not None

    # Request for non-existent email returns None safely
    non_existent = await auth_service.request_password_reset(
        db=db_session,
        email="doesnotexist@example.com",
        client_ip="127.0.0.1",
    )
    assert non_existent is None

    # 2. Confirm reset
    new_password = "ResetSuccessPassword789!"
    await auth_service.confirm_password_reset(
        db=db_session,
        raw_reset_token=reset_token,
        new_password=new_password,
        client_ip="127.0.0.1",
    )

    # 3. Token cannot be reused (single-use)
    with pytest.raises(AuthenticationError, match="inválido o ha expirado"):
        await auth_service.confirm_password_reset(
            db=db_session,
            raw_reset_token=reset_token,
            new_password="AnotherPassword!",
            client_ip="127.0.0.1",
        )

    # 4. Login with newly reset password
    auth_user, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.email,
        password=new_password,
        client_ip="127.0.0.1",
    )
    assert auth_user.id == user.id
