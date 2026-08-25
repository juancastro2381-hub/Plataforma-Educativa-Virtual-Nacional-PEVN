"""
PEVN Backend — Token Service Unit Tests

Tests JWT access token creation, verification, signature validation, expiration,
claim integrity, and refresh token hashing.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.core.security.tokens import (
    JWTTokenService,
    generate_raw_token,
    hash_token,
    token_service,
)
from app.exceptions.errors import AuthenticationError


@pytest.mark.asyncio
async def test_access_token_creation_and_verification() -> None:
    """Test generating a valid JWT access token and verifying its payload."""
    user_id = str(uuid.uuid4())
    token = await token_service.create_access_token(
        subject=user_id,
        additional_claims={
            "username": "docente_test",
            "roles": ["teacher"],
            "institution_id": "inst-123",
        },
    )

    assert isinstance(token, str)
    assert len(token) > 20

    payload = await token_service.verify_token(token, expected_type="access")
    assert payload["sub"] == user_id
    assert payload["username"] == "docente_test"
    assert payload["roles"] == ["teacher"]
    assert payload["institution_id"] == "inst-123"
    assert payload["token_type"] == "access"
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_expired_token_rejected() -> None:
    """Test that an expired JWT token is rejected with AuthenticationError."""
    user_id = str(uuid.uuid4())
    # Create token that expired 10 seconds ago
    expired_token = await token_service.create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(AuthenticationError, match="expirado"):
        await token_service.verify_token(expired_token)


@pytest.mark.asyncio
async def test_tampered_token_rejected() -> None:
    """Test that a tampered JWT token fails signature verification."""
    user_id = str(uuid.uuid4())
    token = await token_service.create_access_token(subject=user_id)

    # Tamper with the payload part
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJzdWIiOiAiaGFja2VkIn0.{parts[2]}"

    with pytest.raises(AuthenticationError, match="inválido"):
        await token_service.verify_token(tampered_token)


@pytest.mark.asyncio
async def test_wrong_secret_key_rejected() -> None:
    """Test that a token signed with a different secret key is rejected."""
    user_id = str(uuid.uuid4())
    foreign_service = JWTTokenService(secret_key="foreign-different-secret-key-123")
    foreign_token = await foreign_service.create_access_token(subject=user_id)

    with pytest.raises(AuthenticationError, match="inválido"):
        await token_service.verify_token(foreign_token)


def test_hash_token_sha256_deterministic() -> None:
    """Test that token hashing produces consistent 64-char SHA-256 digests."""
    raw = "sample_raw_refresh_token_string_12345"
    hash1 = hash_token(raw)
    hash2 = hash_token(raw)

    assert hash1 == hash2
    assert len(hash1) == 64
    assert hash1 != raw


def test_generate_raw_token_entropy() -> None:
    """Test that generated tokens are unique and meet length expectations."""
    tokens = {generate_raw_token(48) for _ in range(100)}
    assert len(tokens) == 100
    for tok in tokens:
        assert len(tok) >= 48
