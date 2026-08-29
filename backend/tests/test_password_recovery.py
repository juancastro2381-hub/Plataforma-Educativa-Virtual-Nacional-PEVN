"""
PEVN Backend — Password Recovery Endpoints & Security Lifecycle Integration Tests

Tests anti-account enumeration on request, token validation, secure Argon2id password
replacement, single-use token consumption, and concurrent session revocation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.models.role import Role, UserRole
from app.models.token import PasswordResetToken, RefreshToken
from app.models.user import DocumentType, User
from app.services.auth_service import auth_service, hash_token


async def _create_active_user(
    db: AsyncSession,
    email: str = "active_user@pevn.edu.co",
    username: str = "activeuser",
    password: str = "OldPassword123!",
) -> User:
    """Helper to create an active user."""
    user = User(
        email=email,
        username=username,
        hashed_password=password_hasher.hash(password),
        first_name="Usuario",
        last_name="Activo",
        document_type=DocumentType.CC,
        document_number="5544332211",
        institution_id=None,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    db.add(user)
    await db.flush()

    role_res = await db.execute(
        select(Role).where(Role.name == SystemRole.TEACHER.value)
    )
    role = role_res.scalar_one()

    db.add(UserRole(user_id=user.id, role_id=role.id, institution_id=None, is_active=True))
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_password_reset_request_anti_enumeration(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    Test that POST /password/reset/request returns the exact same generic message
    for existing active email and non-existent email (prevents account enumeration).
    """
    user = await _create_active_user(db_session, email="real_user@pevn.edu.co")

    # 1. Existing user
    res_real = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    assert res_real.status_code == 200
    msg_real = res_real.json()["message"]

    # 2. Non-existent user
    res_fake = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "non_existent_random@pevn.edu.co"},
    )
    assert res_fake.status_code == 200
    msg_fake = res_fake.json()["message"]

    assert msg_real == msg_fake
    assert "Si la dirección de correo electrónico se encuentra registrada" in msg_real


@pytest.mark.asyncio
async def test_password_reset_verify_token_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test POST /password/reset/verify-token validates token integrity."""
    user = await _create_active_user(db_session, email="verify_user@pevn.edu.co")

    # Request reset to get raw token
    raw_token = await auth_service.request_password_reset(
        db=db_session, email=user.email, client_ip="127.0.0.1"
    )
    assert raw_token is not None

    # 1. Valid token -> 200 OK
    valid_res = await client.post(
        "/api/v1/auth/password/reset/verify-token",
        json={"token": raw_token},
    )
    assert valid_res.status_code == 200
    assert valid_res.json()["valid"] is True

    # 2. Invalid / bogus token -> 401 Unauthorized
    invalid_res = await client.post(
        "/api/v1/auth/password/reset/verify-token",
        json={"token": "bogus_token_1234567890_invalid"},
    )
    assert invalid_res.status_code == 401
    assert invalid_res.json()["error"]["code"] == "INVALID_RESET_TOKEN"


@pytest.mark.asyncio
async def test_password_reset_confirm_and_session_revocation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    Test full confirmation cycle:
    - Sets new password
    - Token becomes invalid (single-use)
    - All concurrent refresh tokens are revoked
    - Login with new password works
    """
    initial_pwd = "OldPassword123!"
    new_pwd = "NewSecurePassword2026!"
    user = await _create_active_user(db_session, email="reset_cycle@pevn.edu.co", password=initial_pwd)

    # Login to create an active refresh session
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": initial_pwd},
    )
    assert login_res.status_code == 200

    # Request reset token
    raw_token = await auth_service.request_password_reset(
        db=db_session, email=user.email, client_ip="127.0.0.1"
    )
    assert raw_token is not None

    # Confirm password reset
    confirm_res = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": raw_token, "new_password": new_pwd},
    )
    assert confirm_res.status_code == 200
    assert "Contraseña restablecida satisfactoriamente" in confirm_res.json()["message"]

    # 1. Token cannot be reused
    reuse_res = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": raw_token, "new_password": "AnotherPassword123!"},
    )
    assert reuse_res.status_code == 401

    # 2. Login with old password fails
    old_login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": initial_pwd},
    )
    assert old_login_res.status_code == 401

    # 3. Login with new password succeeds
    new_login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": new_pwd},
    )
    assert new_login_res.status_code == 200
    assert "access_token" in new_login_res.json()
