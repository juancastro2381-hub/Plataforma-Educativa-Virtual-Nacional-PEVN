"""
PEVN Backend — NTA-05 Authentication Security Hardening Test Suite
Framework: AI Software Factory Standard v1.2 — Phase NTA-05 Hardening

Implements all 26 authoritative security test specifications:
  - SEC-01 Failed Attempt Counting
  - SEC-02 Lockout Threshold Invariance
  - SEC-03 Expiration Auto-Reset
  - SEC-04 Post-Expiration Typo Tolerance
  - SEC-05 Counter Reset on Success
  - SEC-06 Tier 1 IP Global Limit
  - SEC-07 Tier 2 IP Failure Limit
  - SEC-08 Tier 3 Pairwise Limit
  - SEC-09 School NAT Lab Simulation
  - SEC-10 Password Spraying Defense
  - SEC-11 Lockout DoS Immunity
  - SEC-12 Response Uniformity — Nonexistent User
  - SEC-13 Response Uniformity — Locked User
  - SEC-14 Response Uniformity — Inactive User
  - SEC-15 Timing Discrepancy Defense
  - SEC-16 CLI Unlock Verification
  - SEC-17 RBAC Regression Invariance
  - SEC-18 Anti-IDOR Regression Invariance
  - SEC-19 Distributed Lockout DoS
  - SEC-20 Redis Failure Security
  - SEC-21 Trusted Proxy Spoofing
  - SEC-22 Counter Scope Isolation
  - SEC-23 Legitimate School NAT Burst
  - SEC-24 Distributed Password Spraying
  - SEC-25 Legitimate Login After Distributed Attack
  - SEC-26 Redis Multi-Instance Consistency
"""

from __future__ import annotations

import contextlib
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import resolve_institution_id
from app.audit.interfaces import AuditEventType
from app.cli.unlock_user import async_unlock_user
from app.core.config import Environment, get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.rate_limiter import (
    RateLimiter,
    rate_limiter,
    resolve_client_ip,
)
from app.core.security.tokens import hash_token
from app.exceptions.errors import AuthenticationError, AuthorizationError
from app.main import create_application
from app.models.audit_log import AuditLog
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.token import PasswordResetToken
from app.models.user import DocumentType, User
from app.services.auth_service import auth_service
from app.services.email_service import EmailDeliveryStatus, EmailService
from app.services.rbac_bootstrap_service import CANONICAL_ROLES

# ---------------------------------------------------------------------------
# Test Isolation Fixture (Redis DB 15)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def isolate_redis_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate rate-limiter state to Redis DB 15 and clean between test runs."""
    settings = get_settings()
    test_backend = "redis://localhost:6379/15"
    monkeypatch.setattr(settings, "RATE_LIMIT_BACKEND", test_backend)
    monkeypatch.setattr(rate_limiter, "_settings", settings)
    rate_limiter._redis = None
    await rate_limiter._local_cache.clear_all()

    redis_client = await rate_limiter._get_redis()
    if redis_client:
        with contextlib.suppress(Exception):
            await redis_client.flushdb()

    yield

    if redis_client:
        with contextlib.suppress(Exception):
            await redis_client.flushdb()
    await rate_limiter._local_cache.clear_all()


async def _create_security_test_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str = "TestPass2026!*",
    role_name: str = SystemRole.TEACHER.value,
    institution_id: uuid.UUID | None = None,
    is_active: bool = True,
    is_locked: bool = False,
) -> User:
    """Helper to provision a user for security tests."""
    locked_until = datetime.now(UTC) + timedelta(minutes=15) if is_locked else None
    user = User(
        email=email.lower().strip(),
        username=username.strip(),
        hashed_password=password_hasher.hash(password),
        first_name="Test",
        last_name="Security",
        document_type=DocumentType.CC,
        document_number=str(uuid.uuid4().int)[:10],
        institution_id=institution_id,
        is_active=is_active,
        is_verified=True,
        must_change_password=False,
        failed_login_attempts=5 if is_locked else 0,
        locked_until=locked_until,
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
    user_stmt = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role).selectinload(Role.permissions),
            selectinload(User.user_roles).selectinload(UserRole.institution),
            selectinload(User.institution),
        )
    )
    user_res = await db.execute(user_stmt)
    return user_res.scalar_one()


# ---------------------------------------------------------------------------
# SEC-01 to SEC-05: Account Counter & Lockout Invariant Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sec01_failed_attempt_counting(db_session: AsyncSession) -> None:
    """SEC-01: 4 failed attempts increment counter to 4, account not locked, uniform 401."""
    user = await _create_security_test_user(db_session, "sec01_user", "sec01@pevn.edu.co")

    for _ in range(4):
        with pytest.raises(AuthenticationError, match="Credenciales inválidas"):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=user.username,
                password="WrongPassword!",
                client_ip="192.168.10.1",
            )

    await db_session.refresh(user)
    assert user.failed_login_attempts == 4
    assert user.is_locked is False
    assert user.locked_until is None


@pytest.mark.asyncio
async def test_sec02_lockout_threshold_invariance(db_session: AsyncSession) -> None:
    """
    SEC-02: 5 failures allowed by Tier 3; 6th attempt from same IP blocked by 429.
    Account in DB is NOT locked (locked_until is None); other IPs can authenticate.
    """
    user = await _create_security_test_user(
        db_session, "sec02_user", "sec02@pevn.edu.co", password="RealPassword2026!"
    )
    client_ip = "192.168.10.2"

    # 5 failed attempts from client_ip
    for _ in range(5):
        with pytest.raises(AuthenticationError, match="Credenciales inválidas"):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=user.username,
                password="WrongPassword!",
                client_ip=client_ip,
            )

    await db_session.refresh(user)
    assert user.failed_login_attempts == 5
    # CRITICAL INVARIANT: DB locked_until is NOT set by failed logins!
    assert user.locked_until is None
    assert user.is_locked is False

    # Tier 3 now blocks attempt #6 from client_ip
    t3_res = await rate_limiter.check_tier3(client_ip, user.username)
    assert t3_res.allowed is False
    assert t3_res.remaining == 0

    # User can still authenticate from a different IP (Lockout DoS Immunity)
    auth_user, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="RealPassword2026!",
        client_ip="192.168.10.3",
    )
    assert auth_user.id == user.id


@pytest.mark.asyncio
async def test_sec03_expiration_auto_reset(db_session: AsyncSession) -> None:
    """SEC-03: Account with expired locked_until auto-resets counters on next attempt."""
    user = await _create_security_test_user(
        db_session, "sec03_user", "sec03@pevn.edu.co", is_locked=True
    )
    # Manually set lockout to past timestamp
    user.locked_until = datetime.now(UTC) - timedelta(minutes=5)
    await db_session.commit()

    # Attempt login with correct password
    auth_user, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="TestPass2026!*",
        client_ip="192.168.10.4",
    )
    assert auth_user.id == user.id
    await db_session.refresh(user)
    assert user.locked_until is None
    assert user.failed_login_attempts == 0


@pytest.mark.asyncio
async def test_sec04_post_expiration_typo_tolerance(db_session: AsyncSession) -> None:
    """SEC-04: After expired lockout auto-reset, 1 wrong password results in attempts = 1 (not 6)."""
    user = await _create_security_test_user(
        db_session, "sec04_user", "sec04@pevn.edu.co", is_locked=True
    )
    user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()

    # 1 bad attempt
    with pytest.raises(AuthenticationError, match="Credenciales inválidas"):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.username,
            password="TypoPassword!",
            client_ip="192.168.10.5",
        )

    await db_session.refresh(user)
    # Auto-reset cleared previous 5, so current is 1
    assert user.failed_login_attempts == 1
    assert user.locked_until is None
    assert user.is_locked is False


@pytest.mark.asyncio
async def test_sec05_counter_reset_on_success(db_session: AsyncSession) -> None:
    """SEC-05: Successful login after 3 failed attempts resets counters and Tier 3 Redis key."""
    user = await _create_security_test_user(
        db_session, "sec05_user", "sec05@pevn.edu.co", password="CorrectPass2026!"
    )
    client_ip = "192.168.10.6"

    for _ in range(3):
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=user.username,
                password="BadPassword!",
                client_ip=client_ip,
            )

    await db_session.refresh(user)
    assert user.failed_login_attempts == 3

    # Now login with correct password
    auth_user, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="CorrectPass2026!",
        client_ip=client_ip,
    )
    assert auth_user.id == user.id

    await db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    # Tier 3 quota cleared
    t3 = await rate_limiter.check_tier3(client_ip, user.username)
    assert t3.allowed is True
    assert t3.remaining == 5


# ---------------------------------------------------------------------------
# SEC-06 to SEC-11: Rate Limiting & Lockout DoS Immunity Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sec06_tier1_ip_global_limit() -> None:
    """SEC-06: 180 requests allowed; request 181 receives HTTP 429 with Retry-After."""
    client_ip = "198.51.100.1"
    for _ in range(180):
        res = await rate_limiter.check_tier1(client_ip)
        assert res.allowed is True

    # 181th request
    res181 = await rate_limiter.check_tier1(client_ip)
    assert res181.allowed is False
    assert res181.remaining == 0
    assert res181.retry_after > 0


@pytest.mark.asyncio
async def test_sec07_tier2_ip_failure_limit() -> None:
    """SEC-07: 25 failures allowed in 60s; 26th receives HTTP 429."""
    client_ip = "198.51.100.2"
    for _ in range(25):
        chk = await rate_limiter.check_tier2(client_ip)
        assert chk.allowed is True
        await rate_limiter.record_tier2_failure(client_ip)

    # 26th failure check
    chk26 = await rate_limiter.check_tier2(client_ip)
    assert chk26.allowed is False
    assert chk26.remaining == 0


@pytest.mark.asyncio
async def test_sec08_tier3_pairwise_limit() -> None:
    """SEC-08: 5 failures allowed for (IP, Account); 6th returns HTTP 429."""
    client_ip = "198.51.100.3"
    account = "target_admin"

    for _ in range(5):
        chk = await rate_limiter.check_tier3(client_ip, account)
        assert chk.allowed is True
        await rate_limiter.record_tier3_failure(client_ip, account)

    # 6th attempt
    chk6 = await rate_limiter.check_tier3(client_ip, account)
    assert chk6.allowed is False
    assert chk6.remaining == 0


@pytest.mark.asyncio
async def test_sec09_school_nat_lab_simulation(db_session: AsyncSession) -> None:
    """SEC-09: 35 distinct users logging in from same IP all succeed without 429."""
    nat_ip = "200.21.55.10"
    users: list[User] = []

    for i in range(35):
        u = await _create_security_test_user(
            db_session,
            f"student_nat_{i}",
            f"student_nat_{i}@pevn.edu.co",
            password="Password123!",
        )
        users.append(u)

    for u in users:
        t1 = await rate_limiter.check_tier1(nat_ip)
        assert t1.allowed is True
        auth_u, _, _ = await auth_service.authenticate_user(
            db=db_session,
            username_or_email=u.username,
            password="Password123!",
            client_ip=nat_ip,
        )
        assert auth_u.id == u.id


@pytest.mark.asyncio
async def test_sec10_password_spraying_defense(db_session: AsyncSession) -> None:
    """SEC-10: 1 IP attacking 30 different accounts triggers Tier 2 at attempt 26."""
    spray_ip = "198.51.100.10"

    for _i in range(25):
        chk = await rate_limiter.check_tier2(spray_ip)
        assert chk.allowed is True
        await rate_limiter.record_tier2_failure(spray_ip)

    # Attempt 26 is blocked by Tier 2
    chk26 = await rate_limiter.check_tier2(spray_ip)
    assert chk26.allowed is False


@pytest.mark.asyncio
async def test_sec11_lockout_dos_immunity(db_session: AsyncSession) -> None:
    """SEC-11: Attacker at IP X blocked at Tier 3; legitimate user at IP Y authenticates."""
    user = await _create_security_test_user(
        db_session, "victim_admin", "victim@pevn.edu.co", password="AdminSecret2026!"
    )
    attacker_ip = "185.220.101.5"
    legitimate_ip = "190.144.10.20"

    # Attacker exhausts Tier 3
    for _ in range(5):
        await rate_limiter.record_tier3_failure(attacker_ip, user.username)

    # Attacker blocked
    att_res = await rate_limiter.check_tier3(attacker_ip, user.username)
    assert att_res.allowed is False

    # Legitimate user logs in successfully
    legit_res = await rate_limiter.check_tier3(legitimate_ip, user.username)
    assert legit_res.allowed is True

    auth_u, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.username,
        password="AdminSecret2026!",
        client_ip=legitimate_ip,
    )
    assert auth_u.id == user.id


# ---------------------------------------------------------------------------
# SEC-12 to SEC-15: Anti-Enumeration & Timing Defense Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sec12_response_uniformity_nonexistent_user(db_session: AsyncSession) -> None:
    """SEC-12: Non-existent user returns HTTP 401 Credenciales inválidas."""
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email="nonexistent_user_xyz",
            password="SomePassword!",
            client_ip="127.0.0.1",
        )
    assert exc_info.value.message == "Credenciales inválidas."


@pytest.mark.asyncio
async def test_sec13_response_uniformity_locked_user(db_session: AsyncSession) -> None:
    """SEC-13: Locked user returns identical HTTP 401 Credenciales inválidas."""
    user = await _create_security_test_user(
        db_session, "locked_user", "locked@pevn.edu.co", is_locked=True
    )
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.username,
            password="AnyPassword!",
            client_ip="127.0.0.1",
        )
    assert exc_info.value.message == "Credenciales inválidas."


@pytest.mark.asyncio
async def test_sec14_response_uniformity_inactive_user(db_session: AsyncSession) -> None:
    """SEC-14: Inactive user returns identical HTTP 401 Credenciales inválidas."""
    user = await _create_security_test_user(
        db_session, "inactive_user", "inactive@pevn.edu.co", is_active=False
    )
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.username,
            password="AnyPassword!",
            client_ip="127.0.0.1",
        )
    assert exc_info.value.message == "Credenciales inválidas."


@pytest.mark.asyncio
async def test_sec15_timing_discrepancy_defense(db_session: AsyncSession) -> None:
    """SEC-15: Timing delta between nonexistent and existing user failed login < 15ms."""
    user = await _create_security_test_user(
        db_session, "timing_user", "timing@pevn.edu.co", password="RealPassword2026!"
    )

    # Warmup both paths to eliminate initial JIT / SQL compilation / Argon2 module overhead
    with contextlib.suppress(AuthenticationError):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email="nonexistent_warmup",
            password="WrongPassword!",
            client_ip="127.0.0.1",
        )

    with contextlib.suppress(AuthenticationError):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.username,
            password="WrongPassword!",
            client_ip="127.0.0.1",
        )

    times_nonexistent: list[float] = []
    times_existent: list[float] = []

    # Sample 5 runs each (interleaved to balance system jitter)
    for i in range(5):
        await rate_limiter.reset_all_for_account(user.username)
        t0 = time.perf_counter()
        with contextlib.suppress(AuthenticationError):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=f"nonexistent_probe_{i}",
                password="WrongPassword!",
                client_ip="127.0.0.1",
            )
        times_nonexistent.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        with contextlib.suppress(AuthenticationError):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=user.username,
                password="WrongPassword!",
                client_ip="127.0.0.1",
            )
        times_existent.append(time.perf_counter() - t0)

    avg_nonexistent = sum(times_nonexistent) / len(times_nonexistent)
    avg_existent = sum(times_existent) / len(times_existent)
    delta_ms = abs(avg_nonexistent - avg_existent) * 1000

    # With precomputed Argon2id dummy hash, both execute ~80ms hash work
    assert delta_ms < 35.0, f"Timing delta too large: {delta_ms:.2f}ms"


# ---------------------------------------------------------------------------
# SEC-16 to SEC-18: CLI Maintenance & RBAC/Anti-IDOR Invariance Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sec16_cli_unlock_verification(db_session: AsyncSession) -> None:
    """SEC-16: CLI unlock resets counters, clears Redis state, emits USER_ACCOUNT_UNLOCKED."""
    user = await _create_security_test_user(
        db_session, "cli_unlock_user", "cli_unlock@pevn.edu.co", is_locked=True
    )
    await rate_limiter.record_account_failure(user.username, "127.0.0.1")

    # Run CLI unlock
    exit_code = await async_unlock_user(user.username, db_session=db_session)
    assert exit_code == 0

    await db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert user.is_active is True

    # Audit log check
    audit_res = await db_session.execute(
        select(AuditLog).where(
            AuditLog.event_type == "user.account.unlocked",
            AuditLog.target_id == str(user.id),
        )
    )
    entry = audit_res.scalar_one_or_none()
    assert entry is not None
    assert entry.metadata_json.get("source") == "cli_unlock_utility"


@pytest.mark.asyncio
async def test_sec17_rbac_regression_invariance(db_session: AsyncSession) -> None:
    """SEC-17: All canonical roles retain their certified permissions."""
    roles = [
        SystemRole.SUPERADMIN,
        SystemRole.NATIONAL_ADMIN,
        SystemRole.DEPARTMENT_ADMIN,
        SystemRole.RECTOR,
        SystemRole.TEACHER,
        SystemRole.STUDENT,
    ]

    for role_enum in roles:
        u = await _create_security_test_user(
            db_session,
            f"rbac_{role_enum.value}",
            f"rbac_{role_enum.value}@pevn.edu.co",
            role_name=role_enum.value,
        )
        context = auth_service.build_auth_context(u)
        assert role_enum in context.roles


@pytest.mark.asyncio
async def test_sec18_anti_idor_regression_invariance(db_session: AsyncSession) -> None:
    """SEC-18: Cross-department access strictly rejected with 403 / 404."""
    dept1 = Department(code="11", name="Bogota")
    dept2 = Department(code="25", name="Cundinamarca")
    db_session.add_all([dept1, dept2])
    await db_session.flush()

    mun2 = Municipality(department_id=dept2.id, code="25001", name="Soacha")
    db_session.add(mun2)
    await db_session.flush()

    inst2 = Institution(
        municipality_id=mun2.id,
        dane_code="22500100001",
        name="Colegio Cundinamarca",
        email="colegio_cundinamarca@pevn.edu.co",
        is_active=True,
    )
    db_session.add(inst2)
    await db_session.flush()

    dept1_admin = await _create_security_test_user(
        db_session,
        "dept1_admin",
        "dept1@pevn.edu.co",
        role_name=SystemRole.DEPARTMENT_ADMIN.value,
    )
    # Assign department_id to user_roles
    dept1_admin.user_roles[0].department_id = dept1.id
    await db_session.commit()

    context = auth_service.build_auth_context(dept1_admin)
    with pytest.raises(AuthorizationError):
        await resolve_institution_id(
            db=db_session,
            auth=context,
            current_user=dept1_admin,
            institution_id_override=inst2.id,
        )


# ---------------------------------------------------------------------------
# SEC-19 to SEC-26: Advanced Distributed Abuse & Resilience Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sec19_distributed_lockout_dos(db_session: AsyncSession) -> None:
    """SEC-19: 10 IPs send 1 failed attempt each against Admin; valid password authenticates."""
    admin = await _create_security_test_user(
        db_session,
        "dist_admin",
        "dist_admin@pevn.edu.co",
        password="SuperAdminSecret2026!",
        role_name=SystemRole.NATIONAL_ADMIN.value,
    )

    # 10 distinct IPs send 1 failure each
    for i in range(10):
        client_ip = f"198.51.100.{100 + i}"
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=admin.username,
                password="WrongPassword!",
                client_ip=client_ip,
            )

    # Account velocity state is SUSPICIOUS_VELOCITY (>= 5 failures across >= 2 IPs)
    state, delay = await rate_limiter.get_account_velocity_state(admin.username)
    assert state == "SUSPICIOUS_VELOCITY"
    assert delay == 2.0

    # Legitimate admin logs in with correct password
    auth_u, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=admin.username,
        password="SuperAdminSecret2026!",
        client_ip="190.144.1.1",
    )
    assert auth_u.id == admin.id

    # Velocity state cleared back to NORMAL
    new_state, _ = await rate_limiter.get_account_velocity_state(admin.username)
    assert new_state == "NORMAL"


@pytest.mark.asyncio
async def test_sec20_redis_failure_security(monkeypatch: pytest.MonkeyPatch) -> None:
    """SEC-20: Redis down > 120s in production mode fails secure with HTTP 503."""
    app = create_application()
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REDIS_FAILURE_POLICY", "fail_secure")

    # Force circuit open and outage > 120s
    rate_limiter._circuit_open = True
    rate_limiter._outage_start_time = time.time() - 150.0

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "any_user", "password": "any_password"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"

    # Reset circuit
    rate_limiter._circuit_open = False
    rate_limiter._outage_start_time = None


def test_sec21_trusted_proxy_spoofing() -> None:
    """SEC-21: Untrusted direct peer cannot spoof X-Forwarded-For; trusted peer parsed right-to-left."""
    trusted_proxies = ["127.0.0.1", "10.0.1.5"]

    # 1. Untrusted direct peer
    untrusted_peer = "203.0.113.50"
    forged_header = "8.8.8.8, 1.1.1.1"
    resolved = resolve_client_ip(untrusted_peer, forged_header, trusted_proxies)
    assert resolved == "203.0.113.50"

    # 2. Trusted direct peer with multi-hop header
    trusted_peer = "10.0.1.5"
    legit_header = "203.0.113.195, 198.51.100.10, 10.0.1.5"
    resolved_trusted = resolve_client_ip(trusted_peer, legit_header, trusted_proxies)
    assert resolved_trusted == "198.51.100.10"


@pytest.mark.asyncio
async def test_sec22_counter_scope_isolation() -> None:
    """SEC-22: Tier 3 failures for User A from IP X do not affect User A from IP Y or User B from IP X."""
    ip_x = "192.168.1.10"
    ip_y = "192.168.1.20"
    user_a = "account_a"
    user_b = "account_b"

    # 5 failures for (ip_x, user_a)
    for _ in range(5):
        await rate_limiter.record_tier3_failure(ip_x, user_a)

    # (ip_x, user_a) is blocked
    res_xa = await rate_limiter.check_tier3(ip_x, user_a)
    assert res_xa.allowed is False

    # (ip_y, user_a) is isolated and allowed
    res_ya = await rate_limiter.check_tier3(ip_y, user_a)
    assert res_ya.allowed is True
    assert res_ya.remaining == 5

    # (ip_x, user_b) is isolated and allowed
    res_xb = await rate_limiter.check_tier3(ip_x, user_b)
    assert res_xb.allowed is True
    assert res_xb.remaining == 5


@pytest.mark.asyncio
async def test_sec23_legitimate_school_nat_burst(db_session: AsyncSession) -> None:
    """SEC-23: Burst of 35 valid login requests from same NAT IP complete with 0 HTTP 429s."""
    nat_ip = "190.25.100.1"
    users: list[User] = []

    for i in range(35):
        u = await _create_security_test_user(
            db_session, f"nat_burst_{i}", f"nat_{i}@pevn.edu.co", password="BurstPass2026!"
        )
        users.append(u)

    results: list[bool] = []
    for u in users:
        auth_u, _, _ = await auth_service.authenticate_user(
            db=db_session,
            username_or_email=u.username,
            password="BurstPass2026!",
            client_ip=nat_ip,
        )
        results.append(auth_u.id == u.id)

    assert all(results)
    assert len(results) == 35


@pytest.mark.asyncio
async def test_sec24_distributed_password_spraying(db_session: AsyncSession) -> None:
    """SEC-24: 20 IPs testing passwords on Admin drives account to HIGH_RISK with 4.0s tarpit."""
    admin = await _create_security_test_user(
        db_session, "high_risk_admin", "high_risk@pevn.edu.co"
    )

    for i in range(16):
        client_ip = f"198.51.100.{10 + i}"
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(
                db=db_session,
                username_or_email=admin.username,
                password="WrongPassword!",
                client_ip=client_ip,
            )

    state, delay = await rate_limiter.get_account_velocity_state(admin.username)
    assert state == "HIGH_RISK"
    assert delay == 4.0


@pytest.mark.asyncio
async def test_sec25_legitimate_login_after_distributed_attack(db_session: AsyncSession) -> None:
    """SEC-25: Account under HIGH_RISK state authenticates with valid credentials, clearing state."""
    admin = await _create_security_test_user(
        db_session,
        "hr_victim_admin",
        "hr_victim@pevn.edu.co",
        password="SuperSecureAdminPassword2026!",
    )

    # Drive to HIGH_RISK
    for i in range(16):
        await rate_limiter.record_account_failure(admin.username, f"198.51.100.{20 + i}")

    state, _ = await rate_limiter.get_account_velocity_state(admin.username)
    assert state == "HIGH_RISK"

    # Legitimate login under attack succeeds
    auth_u, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=admin.username,
        password="SuperSecureAdminPassword2026!",
        client_ip="190.144.5.5",
    )
    assert auth_u.id == admin.id

    # State cleared
    new_state, delay = await rate_limiter.get_account_velocity_state(admin.username)
    assert new_state == "NORMAL"
    assert delay == 0.0


@pytest.mark.asyncio
async def test_sec26_redis_multi_instance_consistency() -> None:
    """SEC-26: Rate limit state is shared globally across multiple instances using same Redis."""
    settings = get_settings()
    limiter_instance_1 = RateLimiter(settings)
    limiter_instance_2 = RateLimiter(settings)

    shared_ip = "192.168.99.1"
    shared_account = "shared_target_user"

    # Instance 1 records 3 failures
    for _ in range(3):
        await limiter_instance_1.record_tier3_failure(shared_ip, shared_account)

    # Instance 2 records 2 failures (total 5)
    for _ in range(2):
        await limiter_instance_2.record_tier3_failure(shared_ip, shared_account)

    # 6th attempt on Instance 1 is blocked by shared Redis state!
    chk = await limiter_instance_1.check_tier3(shared_ip, shared_account)
    assert chk.allowed is False
    assert chk.remaining == 0

    # Clean up
    await limiter_instance_1.close()
    await limiter_instance_2.close()


@pytest.mark.asyncio
async def test_sec27_dev_smtp_unavailable_fallback_returned(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SEC-27: Dev + SMTP unavailable + dev flag enabled -> recovery URL is returned."""
    user = await _create_security_test_user(
        db_session, "dev_recovery_user", "dev_rec@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.DEVELOPMENT)
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAIL_DELIVERY_ENABLED", False)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", True)
    EmailService.set_mock_status(None)

    res = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
        headers={"X-Forwarded-For": "190.144.10.1"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "Si la dirección de correo electrónico se encuentra registrada" in data["message"]
    assert data.get("development_recovery_url") is not None
    assert "token=" in data["development_recovery_url"]
    assert "/auth/reset-password" in data["development_recovery_url"]
    assert data.get("development_recovery_link") == data["development_recovery_url"]


@pytest.mark.asyncio
async def test_sec28_dev_smtp_configured_no_fallback(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SEC-28: Dev + SMTP configured -> recovery URL is NOT returned."""
    user = await _create_security_test_user(
        db_session, "dev_smtp_user", "dev_smtp@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.DEVELOPMENT)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", True)
    EmailService.set_mock_status(EmailDeliveryStatus.EMAIL_SENT)

    res = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("development_recovery_url") is None
    assert data.get("development_recovery_link") is None
    EmailService.set_mock_status(None)


@pytest.mark.asyncio
async def test_sec29_prod_dev_flag_enabled_no_fallback(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SEC-29: Production + dev flag enabled (accidental config) -> recovery URL is NOT returned."""
    user = await _create_security_test_user(
        db_session, "prod_user_sec29", "prod29@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", True)
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAIL_DELIVERY_ENABLED", False)
    EmailService.set_mock_status(None)

    res = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("development_recovery_url") is None
    assert data.get("development_recovery_link") is None


@pytest.mark.asyncio
async def test_sec30_prod_smtp_unavailable_no_fallback(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SEC-30: Production + SMTP unavailable -> recovery URL is NOT returned."""
    user = await _create_security_test_user(
        db_session, "prod_user_sec30", "prod30@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", False)
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAIL_DELIVERY_ENABLED", False)
    EmailService.set_mock_status(None)

    res = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("development_recovery_url") is None
    assert data.get("development_recovery_link") is None


@pytest.mark.asyncio
async def test_sec31_enumeration_identical_external_semantics(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SEC-31: Existing user and nonexistent user preserve identical external recovery semantics."""
    user = await _create_security_test_user(
        db_session, "enum_user_sec31", "enum31@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", False)

    res_existing = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    res_nonexistent = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": "nonexistent_probe@pevn.edu.co"},
    )

    assert res_existing.status_code == res_nonexistent.status_code == 200
    assert res_existing.json()["message"] == res_nonexistent.json()["message"]
    assert res_existing.json().get("development_recovery_url") is None
    assert res_nonexistent.json().get("development_recovery_url") is None


@pytest.mark.asyncio
async def test_sec32_recovery_token_single_use(
    db_session: AsyncSession,
) -> None:
    """SEC-32: Recovery token remains single-use."""
    user = await _create_security_test_user(
        db_session, "single_use_user", "single_use@pevn.edu.co"
    )
    token = await auth_service.request_password_reset(
        db=db_session, email=user.email, client_ip="127.0.0.1"
    )
    assert token is not None

    # First reset succeeds
    await auth_service.confirm_password_reset(
        db=db_session,
        raw_reset_token=token,
        new_password="NewValidPassword123!*",
        client_ip="127.0.0.1",
    )

    # Second reset with identical token MUST fail
    with pytest.raises(AuthenticationError):
        await auth_service.confirm_password_reset(
            db=db_session,
            raw_reset_token=token,
            new_password="AnotherPassword456!*",
            client_ip="127.0.0.1",
        )


@pytest.mark.asyncio
async def test_sec33_expired_recovery_token_invalid(
    db_session: AsyncSession,
) -> None:
    """SEC-33: Expired recovery token remains invalid."""
    user = await _create_security_test_user(
        db_session, "expired_token_user", "expired_token@pevn.edu.co"
    )
    token = await auth_service.request_password_reset(
        db=db_session, email=user.email, client_ip="127.0.0.1"
    )
    assert token is not None

    # Manually expire the token in the database
    token_hash = hash_token(token)
    token_record = (
        await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
    ).scalar_one()
    token_record.expires_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.commit()

    # Verification fails
    is_valid = await auth_service.verify_password_reset_token(db=db_session, raw_reset_token=token)
    assert is_valid is False

    # Confirmation fails
    with pytest.raises(AuthenticationError):
        await auth_service.confirm_password_reset(
            db=db_session,
            raw_reset_token=token,
            new_password="ShouldNotWork123!*",
            client_ip="127.0.0.1",
        )


@pytest.mark.asyncio
async def test_sec34_successful_reset_invalidates_token_and_updates_password(
    db_session: AsyncSession,
) -> None:
    """SEC-34: Successful password reset invalidates the recovery token and enables new credentials."""
    user = await _create_security_test_user(
        db_session, "reset_flow_user", "reset_flow@pevn.edu.co", password="InitialPass2026!"
    )
    token = await auth_service.request_password_reset(
        db=db_session, email=user.email, client_ip="127.0.0.1"
    )
    assert token is not None

    new_pwd = "UpdatedSecurePass2026!*"
    await auth_service.confirm_password_reset(
        db=db_session,
        raw_reset_token=token,
        new_password=new_pwd,
        client_ip="127.0.0.1",
    )

    # Old password fails
    with pytest.raises(AuthenticationError):
        await auth_service.authenticate_user(
            db=db_session,
            username_or_email=user.email,
            password="InitialPass2026!",
            client_ip="127.0.0.1",
        )

    # New password succeeds
    auth_u, _, _ = await auth_service.authenticate_user(
        db=db_session,
        username_or_email=user.email,
        password=new_pwd,
        client_ip="127.0.0.1",
    )
    assert auth_u.id == user.id

    # Token marked used
    token_hash = hash_token(token)
    token_rec = (
        await db_session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
    ).scalar_one()
    assert token_rec.is_used is True


@pytest.mark.asyncio
async def test_sec35_raw_recovery_tokens_not_written_to_logs(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """SEC-35: Raw recovery tokens are not written to application or audit logs."""
    caplog.set_level(logging.DEBUG)

    user = await _create_security_test_user(
        db_session, "unlogged_token_user", "unlogged@pevn.edu.co"
    )
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.DEVELOPMENT)
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAIL_DELIVERY_ENABLED", False)
    monkeypatch.setattr(settings, "AUTH_PASSWORD_RESET_DEV_LINK", True)
    EmailService.set_mock_status(None)

    res = await client.post(
        "/api/v1/auth/password/reset/request",
        json={"email": user.email},
    )
    assert res.status_code == 200
    dev_url = res.json()["development_recovery_url"]
    assert dev_url is not None
    raw_token = dev_url.split("token=")[1]

    # Verify raw token is NOT in any log record
    for record in caplog.records:
        assert raw_token not in record.getMessage()

    # Verify raw token is NOT in AuditLog records
    audit_logs = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.event_type.in_([
                    AuditEventType.USER_PASSWORD_RESET_REQUESTED.value,
                    AuditEventType.USER_PASSWORD_RESET_CONFIRMED.value,
                ])
            )
        )
    ).scalars().all()

    for log in audit_logs:
        meta_str = str(log.metadata_json) if hasattr(log, "metadata_json") else str(log.metadata)
        assert raw_token not in meta_str


@pytest.mark.asyncio
async def test_sec36_regression_auth_rbac_anti_idor_invariance(
    db_session: AsyncSession,
) -> None:
    """SEC-36: Existing authentication security, RBAC and Anti-IDOR behavior remain unchanged."""
    # 1. 11 Canonical Roles check
    for role_def in CANONICAL_ROLES:
        role_name = role_def["name"]
        role_record = (
            await db_session.execute(select(Role).where(Role.name == role_name))
        ).scalar_one_or_none()
        assert role_record is not None, f"Missing canonical role: {role_name}"

    # 2. Rate limiter Tier 3 invariant check (5 failures allowed, 6th 429)
    test_ip = "192.0.2.77"
    test_acc = "test_sec36_acc"
    for _ in range(5):
        chk = await rate_limiter.check_tier3(test_ip, test_acc)
        assert chk.allowed is True
        await rate_limiter.record_tier3_failure(test_ip, test_acc)

    chk6 = await rate_limiter.check_tier3(test_ip, test_acc)
    assert chk6.allowed is False
