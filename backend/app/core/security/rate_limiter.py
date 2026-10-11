"""
PEVN Backend — Multi-Tier Adaptive Rate Limiter & Security Engine
Framework: AI Software Factory Standard v1.2 — Phase NTA-05 Hardening

Implements:
  - Three-tier sliding-window rate limiting backed by Redis sorted sets:
      * Tier 1: Source IP Global Throughput (180 requests / 60s)
      * Tier 2: Source IP Global Failure Velocity (25 failures / 60s)
      * Tier 3: Pairwise Failure Quota (5 failures / 300s, 6th blocked)
  - Right-to-left trusted proxy client IP resolution (spoof-proof)
  - Velocity State Machine (NORMAL, THROTTLED, SUSPICIOUS, HIGH_RISK, LOCKED)
  - Progressive server-side tarpitting delays (2.0s / 4.0s)
  - Fail-secure production Redis circuit breaker with local emergency defense
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import time
import uuid
from dataclasses import dataclass
from typing import Any

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

_logger = get_logger(__name__)

_HIGH_RISK_MIN_DISTINCT_IPS = 3
_SUSPICIOUS_MIN_DISTINCT_IPS = 2


class RedisFailSecureError(Exception):
    """Raised when Redis is unavailable beyond fail-secure threshold."""

    pass


@dataclass
class RateLimitResult:
    """Outcome of rate-limit tier evaluation."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    tier: str | None = None


def hash_identifier(value: str) -> str:
    """Return SHA-256 digest of identifier for privacy and fixed key length."""
    return hashlib.sha256(value.lower().strip().encode("utf-8")).hexdigest()


def is_ip_in_network(ip_str: str, network_or_ip: str) -> bool:
    """
    Check if an IP address matches a trusted proxy IP or CIDR network.
    Safely handles both IPv4 and IPv6.
    """
    try:
        parsed_ip = ipaddress.ip_address(ip_str.strip())
        target_network = ipaddress.ip_network(network_or_ip.strip(), strict=False)
        return parsed_ip in target_network
    except ValueError:
        return ip_str.strip() == network_or_ip.strip()


def resolve_client_ip(
    direct_peer: str,
    x_forwarded_for: str | None,
    trusted_proxies: list[str],
) -> str:
    """
    Resolve canonical client IP using strict right-to-left traversal.

    Security rules:
      1. If direct_peer is NOT in trusted_proxies:
         Direct peer is authoritative. All forwarded headers are IGNORED.
      2. If direct_peer IS in trusted_proxies:
         Parse X-Forwarded-For right-to-left.
         Skip hops matching trusted_proxies.
         First non-trusted IP is the authoritative client IP.
    """
    peer_clean = direct_peer.strip()
    is_peer_trusted = any(is_ip_in_network(peer_clean, tp) for tp in trusted_proxies)

    if not is_peer_trusted or not x_forwarded_for:
        return peer_clean

    hops = [h.strip() for h in x_forwarded_for.split(",") if h.strip()]
    if not hops:
        return peer_clean

    for hop in reversed(hops):
        is_hop_trusted = any(is_ip_in_network(hop, tp) for tp in trusted_proxies)
        if not is_hop_trusted:
            return hop

    return peer_clean


class InMemorySlidingWindow:
    """In-memory sliding window cache for development and fallback."""

    def __init__(self) -> None:
        self._store: dict[str, list[tuple[float, str]]] = {}
        self._lock: asyncio.Lock | None = None
        self._lock_loop: Any = None

    def _get_lock(self) -> asyncio.Lock:
        current_loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop != current_loop:
            self._lock_loop = current_loop
            self._lock = asyncio.Lock()
        return self._lock

    async def add_entry(self, key: str, window_seconds: float, member_id: str) -> int:
        async with self._get_lock():
            now = time.time()
            cutoff = now - window_seconds
            entries = self._store.get(key, [])
            valid_entries = [e for e in entries if e[0] > cutoff]
            valid_entries.append((now, member_id))
            self._store[key] = valid_entries
            return len(valid_entries)

    async def get_count(self, key: str, window_seconds: float) -> int:
        async with self._get_lock():
            now = time.time()
            cutoff = now - window_seconds
            entries = self._store.get(key, [])
            valid_entries = [e for e in entries if e[0] > cutoff]
            self._store[key] = valid_entries
            return len(valid_entries)

    async def get_entries(
        self, key: str, window_seconds: float
    ) -> list[tuple[float, str]]:
        async with self._get_lock():
            now = time.time()
            cutoff = now - window_seconds
            entries = self._store.get(key, [])
            valid_entries = [e for e in entries if e[0] > cutoff]
            self._store[key] = valid_entries
            return list(valid_entries)

    async def delete_key(self, key: str) -> None:
        async with self._get_lock():
            self._store.pop(key, None)

    async def clear_all(self) -> None:
        async with self._get_lock():
            self._store.clear()


class RateLimiter:
    """
    High-Assurance Multi-Tier Rate Limiter & Velocity Engine.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._redis: aioredis.Redis | None = None
        self._loop: Any = None
        self._local_cache = InMemorySlidingWindow()

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open = False
        self._outage_start_time: float | None = None
        self._outage_alert_sent = False
        self._disabled_alert_sent = False

    async def _get_redis(self) -> aioredis.Redis | None:
        """Obtain or initialize Redis connection for current event loop."""
        backend_url = self._settings.RATE_LIMIT_BACKEND
        if not backend_url or not backend_url.startswith("redis"):
            return None

        current_loop = asyncio.get_running_loop()
        if self._redis is not None and self._loop != current_loop:
            # Event loop changed (e.g., between pytest async test functions)
            self._redis = None

        if self._redis is None:
            try:
                self._loop = current_loop
                self._redis = aioredis.from_url(
                    backend_url,
                    socket_timeout=self._settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=self._settings.REDIS_CONNECT_TIMEOUT,
                    decode_responses=True,
                )
            except Exception as exc:
                _logger.warning("Failed to initialize Redis client", error=str(exc))
                return None
        return self._redis

    async def close(self) -> None:
        """Close connections cleanly."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    def _handle_redis_failure(self, error: Exception) -> None:
        """Handle Redis connection errors and manage circuit breaker."""
        self._consecutive_failures += 1
        _logger.warning(
            "Redis rate-limit operation failed",
            consecutive_failures=self._consecutive_failures,
            error=str(error),
        )

        max_failures = self._settings.REDIS_CIRCUIT_BREAKER_MAX_FAILURES
        if self._consecutive_failures >= max_failures:
            self._circuit_open = True
            if self._outage_start_time is None:
                self._outage_start_time = time.time()

    def _handle_redis_success(self) -> None:
        """Reset circuit breaker counters on successful communication."""
        self._consecutive_failures = 0
        self._circuit_open = False
        self._outage_start_time = None
        self._outage_alert_sent = False

    async def _check_outage_policy(self) -> None:
        """Evaluate fail-secure policy during an active Redis outage."""
        if not self._circuit_open or self._outage_start_time is None:
            return

        outage_duration = time.time() - self._outage_start_time

        # Emit audit alert once per outage
        if not self._outage_alert_sent:
            self._outage_alert_sent = True
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.SECURITY_REDIS_CLUSTER_OFFLINE,
                    actor_ip="127.0.0.1",
                    success=False,
                    metadata={
                        "consecutive_failures": self._consecutive_failures,
                        "policy": self._settings.REDIS_FAILURE_POLICY,
                        "duration_seconds": round(outage_duration, 2),
                    },
                )
            )

        # In production fail-secure mode, fail completely if outage > max duration
        max_duration = self._settings.REDIS_OUTAGE_MAX_DURATION_SECONDS
        if (
            self._settings.REDIS_FAILURE_POLICY == "fail_secure"
            and not self._settings.is_development
            and outage_duration > max_duration
        ):
            raise RedisFailSecureError(
                f"Redis down {outage_duration:.1f}s, max {max_duration}s"
            )

    # -----------------------------------------------------------------------
    # Sliding-Window Engine (Redis with Local Fallback)
    # -----------------------------------------------------------------------

    async def _record_sliding_event(
        self, key: str, window_seconds: float, member_id: str | None = None
    ) -> int:
        """Record an event into the sliding window sorted set."""
        now = time.time()
        member = member_id or f"{now}:{uuid.uuid4().hex[:8]}"
        cutoff = now - window_seconds
        redis_client = await self._get_redis()

        if redis_client and not self._circuit_open:
            try:
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zadd(key, {member: now})
                pipe.zcard(key)
                pipe.expire(key, int(window_seconds) + 5)
                results = await pipe.execute()
                self._handle_redis_success()
                return int(results[2])
            except (RedisError, OSError, RuntimeError, AttributeError) as exc:
                self._handle_redis_failure(exc)

        # Fallback to in-memory sliding window
        await self._check_outage_policy()
        return await self._local_cache.add_entry(key, window_seconds, member)

    async def _get_sliding_count(self, key: str, window_seconds: float) -> int:
        """Query current event count in the active sliding window."""
        now = time.time()
        cutoff = now - window_seconds
        redis_client = await self._get_redis()

        if redis_client and not self._circuit_open:
            try:
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zcard(key)
                results = await pipe.execute()
                self._handle_redis_success()
                return int(results[1])
            except (RedisError, OSError, RuntimeError, AttributeError) as exc:
                self._handle_redis_failure(exc)

        await self._check_outage_policy()
        return await self._local_cache.get_count(key, window_seconds)

    async def _delete_key(self, key: str) -> None:
        """Remove a key completely from Redis and local cache."""
        redis_client = await self._get_redis()
        if redis_client and not self._circuit_open:
            try:
                await redis_client.delete(key)
                self._handle_redis_success()
            except (RedisError, OSError, RuntimeError, AttributeError) as exc:
                self._handle_redis_failure(exc)

        await self._local_cache.delete_key(key)

    # -----------------------------------------------------------------------
    # Rate Limiting Tiers
    # -----------------------------------------------------------------------

    async def check_tier1(self, client_ip: str) -> RateLimitResult:
        """
        Tier 1: Source IP Global Throughput (180 requests / 60 seconds).
        Increments request count for the IP and evaluates quota.
        """
        if not self._settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(
                allowed=True, limit=180, remaining=180, retry_after=0
            )

        ip_hash = hash_identifier(client_ip)
        key = f"pevn:rl:ip:req:{ip_hash}"
        limit = self._settings.RATE_LIMIT_TIER1_IP_CAPACITY
        window = 60.0

        count = await self._record_sliding_event(key, window)
        allowed = count <= limit
        remaining = max(0, limit - count)
        retry_after = int(window) if not allowed else 0

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
            tier="tier1_ip_capacity",
        )

    async def check_tier2(self, client_ip: str) -> RateLimitResult:
        """
        Tier 2: Source IP Global Failure Velocity (25 failures / 60 seconds).
        Checks failure count before request execution.
        """
        if not self._settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(allowed=True, limit=25, remaining=25, retry_after=0)

        ip_hash = hash_identifier(client_ip)
        key = f"pevn:rl:ip:fail:{ip_hash}"
        limit = self._settings.RATE_LIMIT_TIER2_IP_FAILURES
        window = 60.0

        count = await self._get_sliding_count(key, window)
        allowed = count < limit  # e.g., if 25 failures exist, 26th is blocked
        remaining = max(0, limit - count)
        retry_after = int(window) if not allowed else 0

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
            tier="tier2_ip_failure",
        )

    async def record_tier2_failure(self, client_ip: str) -> int:
        """Record a login failure against the resolved client IP."""
        ip_hash = hash_identifier(client_ip)
        key = f"pevn:rl:ip:fail:{ip_hash}"
        return await self._record_sliding_event(key, 60.0)

    async def check_tier3(
        self, client_ip: str, normalized_account: str
    ) -> RateLimitResult:
        """
        Tier 3: Pairwise (Source IP + Target Account) Failure Quota.
        Capacity: 5 failures allowed. Attempt #6 returns HTTP 429.
        """
        if not self._settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(
                allowed=True, limit=5, remaining=5, retry_after=0
            )

        ip_hash = hash_identifier(client_ip)
        account_hash = hash_identifier(normalized_account)
        key = f"pevn:rl:pair:fail:{ip_hash}:{account_hash}"
        limit = self._settings.RATE_LIMIT_TIER3_PAIRWISE_FAILURES  # 5
        window = 300.0

        count = await self._get_sliding_count(key, window)
        # If count >= limit (5 failures recorded), next attempt (#6) is blocked
        allowed = count < limit
        remaining = max(0, limit - count)
        retry_after = int(window) if not allowed else 0

        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
            tier="tier3_pairwise_failure",
        )

    async def record_tier3_failure(
        self, client_ip: str, normalized_account: str
    ) -> int:
        """Record a failure for the (client IP, account) pair."""
        ip_hash = hash_identifier(client_ip)
        account_hash = hash_identifier(normalized_account)
        key = f"pevn:rl:pair:fail:{ip_hash}:{account_hash}"
        return await self._record_sliding_event(key, 300.0)

    async def clear_tier3_pair(
        self, client_ip: str, normalized_account: str
    ) -> None:
        """Clear the pair failure counter upon successful authentication."""
        ip_hash = hash_identifier(client_ip)
        account_hash = hash_identifier(normalized_account)
        key = f"pevn:rl:pair:fail:{ip_hash}:{account_hash}"
        await self._delete_key(key)

    # -----------------------------------------------------------------------
    # Velocity State Machine & Server-Side Tarpitting
    # -----------------------------------------------------------------------

    async def record_account_failure(
        self, normalized_account: str, client_ip: str
    ) -> None:
        """Record an account-level failure tracking distinct source IPs."""
        account_hash = hash_identifier(normalized_account)
        ip_hash = hash_identifier(client_ip)
        key = f"pevn:rl:acc:fail:{account_hash}"
        member = f"{ip_hash}:{uuid.uuid4().hex[:6]}"
        win = float(self._settings.ACCOUNT_VELOCITY_WINDOW_SECONDS)
        await self._record_sliding_event(key, win, member)

    async def get_account_velocity_state(
        self, normalized_account: str
    ) -> tuple[str, float]:
        """
        Evaluate account velocity state.
        Returns:
            (state_name, tarpit_delay_seconds)
            States:
              - 'HIGH_RISK': >= 15 failures across >= 3 IPs (4.0s delay)
              - 'SUSPICIOUS_VELOCITY': >= 5 failures across >= 2 IPs (2.0s delay)
              - 'NORMAL': (0.0s delay)
        """
        if not self._settings.RATE_LIMIT_ENABLED:
            return "NORMAL", 0.0

        account_hash = hash_identifier(normalized_account)
        key = f"pevn:rl:acc:fail:{account_hash}"
        window = float(self._settings.ACCOUNT_VELOCITY_WINDOW_SECONDS)
        now = time.time()
        cutoff = now - window

        redis_client = await self._get_redis()
        raw_members: list[str] = []

        if redis_client and not self._circuit_open:
            try:
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zrange(key, 0, -1)
                results = await pipe.execute()
                self._handle_redis_success()
                raw_members = results[1] or []
            except (RedisError, OSError, RuntimeError, AttributeError) as exc:
                self._handle_redis_failure(exc)

        if not raw_members:
            entries = await self._local_cache.get_entries(key, window)
            raw_members = [e[1] for e in entries]

        total_failures = len(raw_members)
        distinct_ips: set[str] = set()
        for m in raw_members:
            parts = m.split(":")
            if parts:
                distinct_ips.add(parts[0])

        distinct_ip_count = len(distinct_ips)

        if (
            total_failures >= self._settings.ACCOUNT_VELOCITY_HIGH_RISK_THRESHOLD
            and distinct_ip_count >= _HIGH_RISK_MIN_DISTINCT_IPS
        ):
            return "HIGH_RISK", self._settings.TARPIT_DELAY_HIGH_RISK_SECONDS

        if (
            total_failures >= self._settings.ACCOUNT_VELOCITY_SUSPICIOUS_THRESHOLD
            and distinct_ip_count >= _SUSPICIOUS_MIN_DISTINCT_IPS
        ):
            return "SUSPICIOUS_VELOCITY", self._settings.TARPIT_DELAY_SUSPICIOUS_SECONDS

        return "NORMAL", 0.0

    async def clear_account_velocity_state(self, normalized_account: str) -> None:
        """Clear account velocity state upon successful authentication or CLI unlock."""
        account_hash = hash_identifier(normalized_account)
        key = f"pevn:rl:acc:fail:{account_hash}"
        await self._delete_key(key)

    async def reset_all_for_account(self, normalized_account: str) -> None:
        """Reset all rate-limit and velocity keys associated with an account."""
        await self.clear_account_velocity_state(normalized_account)
        # Scan and remove any tier 3 pair keys for this account if redis is available
        account_hash = hash_identifier(normalized_account)
        redis_client = await self._get_redis()
        if redis_client and not self._circuit_open:
            try:
                pattern = f"pevn:rl:pair:fail:*:{account_hash}"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
            except Exception as exc:
                _logger.warning("Failed to scan tier3 keys for account", error=str(exc))


# Default global instance
rate_limiter = RateLimiter()
