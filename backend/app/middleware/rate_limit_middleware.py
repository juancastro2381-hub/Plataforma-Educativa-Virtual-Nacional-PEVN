"""
PEVN Backend — Rate Limiting ASGI Middleware
Framework: AI Software Factory Standard v1.2 — Phase NTA-05 Hardening

Enforces:
  - Three-tier adaptive rate limiting on POST /api/v1/auth/login:
      * Tier 1: IP Global Capacity (180 req / 60s)
      * Tier 2: IP Global Failure Velocity (25 fail / 60s)
      * Tier 3: Pairwise IP + Account Failure Quota (5 fail / 300s, 6th returns 429)
  - Right-to-left spoof-proof client IP resolution via TRUSTED_PROXIES
  - Immediate short-circuit before any database or Argon2id execution on 429
  - Standard RFC 6585 and IETF RateLimit response headers
  - Fail-secure HTTP 503 handling during extended Redis outages
  - Emergency security override auditing (RATE_LIMIT_ENABLED kill switch)
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.security.rate_limiter import (
    RateLimiter,
    RedisFailSecureError,
    rate_limiter,
    resolve_client_ip,
)

_logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette ASGI middleware for multi-tier authentication rate limiting.
    """

    def __init__(
        self,
        app: Any,
        settings: Settings | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self._settings = settings or get_settings()
        self._limiter = limiter or rate_limiter
        self._disabled_audit_emitted = False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = self._settings

        # 1. Resolve canonical client IP using trusted proxy rules
        direct_peer = request.client.host if request.client else "127.0.0.1"
        x_forwarded_for = request.headers.get("x-forwarded-for")
        trusted_proxies = (
            settings.TRUSTED_PROXIES
            if isinstance(settings.TRUSTED_PROXIES, list)
            else [settings.TRUSTED_PROXIES]
        )

        canonical_ip = resolve_client_ip(direct_peer, x_forwarded_for, trusted_proxies)
        request.state.client_ip = canonical_ip

        # 2. Check if rate limiting is enabled (emergency kill switch)
        if not settings.RATE_LIMIT_ENABLED:
            if not self._disabled_audit_emitted:
                self._disabled_audit_emitted = True
                _logger.warning("ALERT: Rate limiting DISABLED via override.")
                await audit_service.record(
                    AuditEvent(
                        event_type=AuditEventType.SECURITY_RATE_LIMIT_DISABLED,
                        actor_ip=canonical_ip,
                        success=True,
                        metadata={
                            "reason": "emergency_override",
                            "environment": settings.ENVIRONMENT,
                        },
                    )
                )
            return await call_next(request)

        # Rate limiting specifically targets the login endpoint
        login_path = f"{settings.API_V1_PREFIX}/auth/login"
        if request.url.path != login_path or request.method.upper() != "POST":
            return await call_next(request)

        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

        # 3. Buffer and clone request body so downstream handlers can parse credentials
        body_bytes = await request.body()
        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        request = Request(request.scope, receive=receive)

        # 4. Extract target username/email from JSON payload
        target_account: str | None = None
        if body_bytes:
            try:
                payload = json.loads(body_bytes.decode("utf-8"))
                raw_user = payload.get("username") or payload.get("email")
                if raw_user and isinstance(raw_user, str):
                    target_account = raw_user.lower().strip()
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # 5. Evaluate rate limit tiers or handle Redis outage
        early_resp = await self._evaluate_rate_limits(
            canonical_ip, target_account, correlation_id
        )
        if early_resp is not None:
            return early_resp

        # All tiers passed -> dispatch to downstream handler
        return await call_next(request)

    async def _evaluate_rate_limits(
        self,
        canonical_ip: str,
        target_account: str | None,
        correlation_id: str,
    ) -> Response | None:
        """Evaluate Tiers 1, 2, 3 and return 429/503 response if limit hit."""
        try:
            # Tier 1: Source IP Global Throughput (180 req/60s)
            t1_res = await self._limiter.check_tier1(canonical_ip)
            if not t1_res.allowed:
                return await self._build_429_response(
                    result=t1_res,
                    client_ip=canonical_ip,
                    correlation_id=correlation_id,
                )

            # Tier 2: Source IP Global Failure Velocity (25 fail/60s)
            t2_res = await self._limiter.check_tier2(canonical_ip)
            if not t2_res.allowed:
                return await self._build_429_response(
                    result=t2_res,
                    client_ip=canonical_ip,
                    correlation_id=correlation_id,
                )

            # Tier 3: Pairwise IP + Account Failure Quota (5 fail/300s)
            if target_account:
                t3_res = await self._limiter.check_tier3(
                    canonical_ip, target_account
                )
                if not t3_res.allowed:
                    return await self._build_429_response(
                        result=t3_res,
                        client_ip=canonical_ip,
                        correlation_id=correlation_id,
                        target_account=target_account,
                    )

        except RedisFailSecureError as rf_err:
            _logger.critical("Auth denied: fail-secure Redis", error=str(rf_err))
            msg = (
                "Servicio de autenticación no disponible temporalmente "
                "por mantenimiento de seguridad."
            )
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": msg,
                        "correlation_id": correlation_id,
                        "retry_after": 60,
                    }
                },
                headers={"Retry-After": "60"},
            )

        return None

    async def _build_429_response(
        self,
        result: Any,
        client_ip: str,
        correlation_id: str,
        target_account: str | None = None,
    ) -> JSONResponse:
        """Construct standard RFC 429 response and record audit log."""
        reset_epoch = int(time.time() + result.retry_after)
        headers = {
            "Retry-After": str(result.retry_after),
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_epoch),
        }

        # Log audit event
        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                actor_ip=client_ip,
                correlation_id=correlation_id,
                success=False,
                metadata={
                    "tier": result.tier,
                    "limit": result.limit,
                    "retry_after": result.retry_after,
                    "target_account_specified": bool(target_account),
                },
            )
        )

        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        "Demasiadas solicitudes de autenticación. "
                        "Por favor intente más tarde."
                    ),
                    "correlation_id": correlation_id,
                }
            },
            headers=headers,
        )
