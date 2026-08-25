"""
PEVN Backend — Password Hasher Unit Tests

Tests Argon2id hashing, timing safety, parameter verification, and rehash detection.
"""

from __future__ import annotations

import pytest

from app.core.security.password import Argon2PasswordHasher, password_hasher


def test_argon2_hash_and_verify_success() -> None:
    """Test that a password hashed with Argon2id is verified successfully."""
    raw_password = "SecurePassword123!"
    hashed = password_hasher.hash(raw_password)

    assert hashed.startswith("$argon2id$")
    assert password_hasher.verify(raw_password, hashed) is True


def test_argon2_verify_wrong_password_fails() -> None:
    """Test that an incorrect password fails verification."""
    raw_password = "SecurePassword123!"
    hashed = password_hasher.hash(raw_password)

    assert password_hasher.verify("WrongPassword456!", hashed) is False


def test_argon2_verify_empty_or_malformed_hash() -> None:
    """Test that empty or corrupted hashes fail safely without crashing."""
    assert password_hasher.verify("password", "") is False
    assert password_hasher.verify("", "$argon2id$invalid") is False
    assert password_hasher.verify("password", "not-a-valid-argon-hash") is False


def test_argon2_hash_empty_password_raises() -> None:
    """Test that hashing an empty password raises ValueError."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        password_hasher.hash("")


def test_argon2_unique_salt_per_hash() -> None:
    """Test that two hashes of the same password produce different hashes (unique salts)."""
    raw_password = "IdenticalPassword123!"
    hash1 = password_hasher.hash(raw_password)
    hash2 = password_hasher.hash(raw_password)

    assert hash1 != hash2
    assert password_hasher.verify(raw_password, hash1) is True
    assert password_hasher.verify(raw_password, hash2) is True


def test_argon2_needs_rehash() -> None:
    """Test that needs_rehash identifies hashes generated with older/different parameters."""
    # Create hasher with small time_cost
    old_hasher = Argon2PasswordHasher(time_cost=1, memory_cost=8192)
    old_hash = old_hasher.hash("TestPassword123!")

    # Standard hasher requires 3 iterations, 64MB memory -> needs rehash
    assert password_hasher.needs_rehash(old_hash) is True

    # Standard hasher on its own hash -> does not need rehash
    current_hash = password_hasher.hash("TestPassword123!")
    assert password_hasher.needs_rehash(current_hash) is False
