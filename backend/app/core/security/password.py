"""
PEVN Backend — Argon2id Password Hasher

Implements IPasswordHasher using the industry standard Argon2id algorithm (RFC 9106)
via argon2-cffi.

Parameters configured:
  - time_cost = 3 iterations
  - memory_cost = 65536 KiB (64 MiB)
  - parallelism = 4 lanes
  - hash_len = 32 bytes
  - salt_len = 16 bytes

SECURITY:
  - Passwords are never stored in plaintext
  - Passwords are never logged
  - Comparison is timing-safe
  - Supports needs_rehash() for transparent parameter upgrades
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.logging import get_logger
from app.core.security.interfaces import IPasswordHasher

_logger = get_logger(__name__)


class Argon2PasswordHasher(IPasswordHasher):
    """
    Argon2id implementation of IPasswordHasher.
    """

    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16,
    ) -> None:
        self._hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len,
        )

    def hash(self, password: str) -> str:
        """
        Hash a plaintext password with a unique cryptographic salt.

        Args:
            password: Raw plaintext password string.

        Returns:
            Argon2id encoded hash string ($argon2id$v=19$m=65536,t=3,p=4$...).
        """
        if not password:
            raise ValueError("Password cannot be empty")
        return self._hasher.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Timing-safe verification of plain_password against stored hashed_password.

        Args:
            plain_password: Raw password input from user.
            hashed_password: Argon2id hash from the database.

        Returns:
            True if matching, False if incorrect or hash is malformed.
        """
        if not plain_password or not hashed_password:
            return False
        try:
            return self._hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if stored hash was created with older hashing parameters.

        Args:
            hashed_password: Hash from the database.

        Returns:
            True if password should be rehashed upon successful login.
        """
        if not hashed_password:
            return False
        try:
            return self._hasher.check_needs_rehash(hashed_password)
        except (InvalidHashError, VerificationError):
            return True


# Default singleton instance
password_hasher: IPasswordHasher = Argon2PasswordHasher()
