"""
PEVN Backend — Token Management Service (JWT & Opaque Refresh Tokens)

Implements ITokenService for creating, validating, and revoking cryptographic tokens.

Token Architecture:
  1. Access Tokens (JWT):
     - Short-lived (default: 15 minutes)
     - Signed with HMAC-SHA256 (HS256)
     - Self-contained claims: sub, roles, institution_id, scope, jti, exp
  2. Refresh Tokens (Opaque + Hash Storage):
     - Long-lived (default: 7 days)
     - High-entropy random string (secrets.token_urlsafe)
     - Only SHA-256 hash is persisted in the database
     - Managed via RefreshToken rotation families
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security.interfaces import ITokenService
from app.exceptions.errors import AuthenticationError

_logger = get_logger(__name__)


def hash_token(raw_token: str) -> str:
    """
    Compute the SHA-256 hex digest of a raw token string.

    Args:
        raw_token: Plaintext token string.

    Returns:
        64-character lowercase hexadecimal SHA-256 string.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_raw_token(length_bytes: int = 48) -> str:
    """Generate a high-entropy URL-safe cryptographic token."""
    return secrets.token_urlsafe(length_bytes)


class JWTTokenService(ITokenService):
    """
    JWT implementation of ITokenService using PyJWT and HMAC-SHA256.
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        settings = get_settings()
        self._secret_key = secret_key or settings.SECRET_KEY
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days
        self._revoked_jtis: set[str] = set()

    async def create_access_token(
        self,
        subject: str,
        additional_claims: dict[str, Any] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a signed JWT access token.

        Args:
            subject: The token subject (user UUID string).
            additional_claims: Extra claims (roles, scope, institution_id, username).
            expires_delta: Optional custom lifetime duration.

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(UTC)
        expire = now + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=self._access_token_expire_minutes)
        )

        payload: dict[str, Any] = {
            "sub": str(subject),
            "jti": str(uuid.uuid4()),
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        if additional_claims:
            # Exclude forbidden or sensitive claims
            for k, v in additional_claims.items():
                if k not in {"password", "hashed_password", "token", "secret"}:
                    payload[k] = v

        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    async def verify_token(
        self,
        token: str,
        expected_type: str = "access",
    ) -> dict[str, Any]:
        """
        Verify and decode a JWT token string.

        Args:
            token: Encoded JWT string.
            expected_type: Expected 'token_type' claim (default: 'access').

        Returns:
            Decoded payload dictionary.

        Raises:
            AuthenticationError: If token is expired, tampered, or invalid.
        """
        if not token:
            raise AuthenticationError("Token de autenticación ausente.")

        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "sub", "token_type"]},
            )

            token_type = payload.get("token_type")
            if token_type != expected_type:
                _logger.warning(
                    "Invalid token type presented",
                    expected=expected_type,
                    received=token_type,
                )
                raise AuthenticationError("Tipo de token inválido.")

            # SEC-008: Check if jti is in revocation denylist
            jti = payload.get("jti")
            if jti:
                if jti in self._revoked_jtis:
                    raise AuthenticationError("Token de autenticación revocado.")
                try:
                    from app.core.security.rate_limiter import rate_limiter
                    redis_client = getattr(rate_limiter, "_redis", None)
                    if redis_client and await redis_client.get(f"pevn:jwt:revoked:{jti}"):
                        self._revoked_jtis.add(jti)
                        raise AuthenticationError("Token de autenticación revocado.")
                except AuthenticationError:
                    raise
                except Exception:
                    pass

            return payload

        except ExpiredSignatureError as exc:
            raise AuthenticationError("El token de sesión ha expirado.") from exc
        except InvalidTokenError as exc:
            _logger.warning("Invalid token presented", error=str(exc))
            raise AuthenticationError("Token de autenticación inválido.") from exc
        except AuthenticationError:
            raise
        except Exception as exc:
            _logger.error("Unexpected error during token verification", error=str(exc))
            raise AuthenticationError("Error validando credenciales.") from exc

    async def revoke_token(self, token: str) -> None:
        """
        Revocation marker for access tokens. Denylists jti in Redis and memory (SEC-008).
        """
        if not token:
            return
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False},
            )
            jti = payload.get("jti")
            if jti:
                self._revoked_jtis.add(jti)
                try:
                    from app.core.security.rate_limiter import rate_limiter
                    redis_client = getattr(rate_limiter, "_redis", None)
                    if redis_client:
                        exp = payload.get("exp", 0)
                        now_ts = int(datetime.now(UTC).timestamp())
                        ttl = max(exp - now_ts, 60) if exp > now_ts else 60
                        await redis_client.set(f"pevn:jwt:revoked:{jti}", "1", ex=ttl)
                except Exception:
                    pass
                _logger.info("Access token revoked via session termination", jti=jti)
        except Exception:
            _logger.debug("Attempted to revoke invalid or malformed token")


# Default token service singleton instance
token_service: JWTTokenService = JWTTokenService()
