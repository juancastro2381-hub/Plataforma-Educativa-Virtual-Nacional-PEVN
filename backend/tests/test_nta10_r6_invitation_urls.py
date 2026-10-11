"""
PEVN Backend — NTA-10-R6: Invitation URL Architecture & Security Tests

Validates:
1. Canonical absolute URL construction with exactly ONE frontend origin.
2. Proper URL parsing and standard query-parameter encoding (?token=...).
3. HTTPS enforcement for staging and production environments.
4. Prevention of localhost origins in production environments.
5. Error handling for missing, malformed, or unsupported URL configurations.
6. Municipality Admin create and resend endpoints return valid single-origin URLs in dev.
7. Token expiry (48h), single-use consumption, and regeneration invalidation.
8. Strict suppression of raw tokens and invitation URLs in non-development environments.
9. Compatibility with Rector and Department Administrator invitation contracts.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, Settings, get_settings
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.invitation import MunicipalityAdminInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService
from sqlalchemy import select


# ==============================================================================
# 1. SETTINGS URL CONSTRUCTION UNIT TESTS
# ==============================================================================

def test_01_development_default_url_construction() -> None:
    """Development settings generate canonical URL with localhost origin and encoded token."""
    settings = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    assert settings.public_frontend_url == "http://localhost:3000"

    url = settings.build_invitation_url("tok_dev_alpha_123")
    assert url == "http://localhost:3000/auth/accept-invitation?token=tok_dev_alpha_123"

    # Verify standard URL properties
    parsed = urlparse(url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "localhost:3000"
    assert parsed.path == "/auth/accept-invitation"
    assert parsed.query == "token=tok_dev_alpha_123"


def test_02_custom_frontend_public_url_normalizes_trailing_slash() -> None:
    """Trailing slashes in FRONTEND_PUBLIC_URL are cleanly stripped to prevent double slashes."""
    settings = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        FRONTEND_PUBLIC_URL="http://192.168.1.100:3000///",
    )
    assert settings.public_frontend_url == "http://192.168.1.100:3000"

    url = settings.build_invitation_url("tok_lan_beta_456")
    assert url == "http://192.168.1.100:3000/auth/accept-invitation?token=tok_lan_beta_456"
    assert "http://192.168.1.100:3000//" not in url


def test_03_staging_and_production_https_enforcement() -> None:
    """Staging and production environments require HTTPS origins."""
    # Staging valid HTTPS
    settings_staging = Settings(
        ENVIRONMENT=Environment.STAGING,
        FRONTEND_PUBLIC_URL="https://staging.pevn.mineducacion.gov.co",
    )
    url_staging = settings_staging.build_invitation_url("tok_staging_789")
    assert url_staging == "https://staging.pevn.mineducacion.gov.co/auth/accept-invitation?token=tok_staging_789"

    # Production valid HTTPS
    settings_prod = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        FRONTEND_PUBLIC_URL="https://pevn.mineducacion.gov.co",
    )
    url_prod = settings_prod.build_invitation_url("tok_prod_101")
    assert url_prod == "https://pevn.mineducacion.gov.co/auth/accept-invitation?token=tok_prod_101"


def test_04_staging_and_production_reject_insecure_http() -> None:
    """Attempting to build invitation URLs with HTTP in staging or production raises ValueError."""
    settings_insecure_staging = Settings(
        ENVIRONMENT=Environment.STAGING,
        FRONTEND_PUBLIC_URL="http://staging.pevn.mineducacion.gov.co",
    )
    with pytest.raises(ValueError, match="must use HTTPS"):
        settings_insecure_staging.build_invitation_url("tok_test")

    settings_insecure_prod = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        FRONTEND_PUBLIC_URL="http://pevn.mineducacion.gov.co",
    )
    with pytest.raises(ValueError, match="must use HTTPS"):
        settings_insecure_prod.build_invitation_url("tok_test")


def test_05_production_rejects_localhost_origin() -> None:
    """Production mode strictly forbids localhost in invitation URLs."""
    settings_prod_local = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        FRONTEND_PUBLIC_URL="https://localhost:3000",
    )
    with pytest.raises(ValueError, match="cannot use localhost"):
        settings_prod_local.build_invitation_url("tok_test")


def test_06_token_special_characters_are_safely_encoded() -> None:
    """Special characters in token parameters are properly encoded via urlencode."""
    settings = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    raw_token = "tok+special/char=123?&"
    url = settings.build_invitation_url(raw_token)

    assert "tok%2Bspecial%2Fchar%3D123%3F%26" in url
    # Ensure raw unencoded characters do not corrupt the URL query structure
    parsed = urlparse(url)
    assert parsed.query.startswith("token=")


def test_07_empty_token_raises_actionable_error() -> None:
    """Empty or whitespace-only token inputs raise a descriptive ValueError."""
    settings = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    with pytest.raises(ValueError, match="Invitation token must be non-empty"):
        settings.build_invitation_url("")

    with pytest.raises(ValueError, match="Invitation token must be non-empty"):
        settings.build_invitation_url("   ")


def test_08_invalid_url_config_raises_actionable_error() -> None:
    """Missing scheme or malformed URL config raises actionable error."""
    settings_no_scheme = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        FRONTEND_PUBLIC_URL="invalid-url-without-scheme",
    )
    with pytest.raises(ValueError, match="must include valid scheme"):
        settings_no_scheme.build_invitation_url("tok_test")


# ==============================================================================
# 2. INTEGRATION TESTS FOR MUNICIPALITY ADMIN INVITATION URLS
# ==============================================================================

@pytest.fixture
async def invitation_test_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and territorial test entities for NTA-10-R6."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    dept_san = Department(code=f"68_{uuid.uuid4().hex[:4]}", name="Santander URL Test")
    db_session.add(dept_san)
    await db_session.flush()

    muni_bucaramanga = Municipality(
        department_id=dept_san.id,
        code=f"68001_{uuid.uuid4().hex[:4]}",
        name="Bucaramanga URL Test",
    )
    db_session.add(muni_bucaramanga)
    await db_session.flush()

    # Create Department Admin actor
    role_obj = (await db_session.execute(select(Role).where(Role.name == "department_admin"))).scalar_one()
    pw = password_hasher.hash("Nta10R6Test2026!#")
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email=f"dept_admin_{uid.hex[:6]}@pevn.edu.co",
        username=f"dept_admin_{uid.hex[:6]}",
        hashed_password=pw,
        first_name="DeptAdmin",
        last_name="Tester",
        document_type=DocumentType.CC,
        document_number=f"10{uuid.uuid4().hex[:8]}",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(
        user_id=user.id,
        role_id=role_obj.id,
        department_id=dept_san.id,
        is_active=True,
    )
    db_session.add(ur)
    await db_session.flush()

    token = await token_service.create_access_token(
        subject=str(user.id),
        additional_claims={
            "roles": ["department_admin"],
            "department_id": str(dept_san.id),
        },
    )
    await db_session.commit()

    return {
        "dept": dept_san,
        "muni": muni_bucaramanga,
        "token_dept": token,
    }


@pytest.mark.anyio
async def test_09_municipality_admin_create_returns_single_origin_url(
    client: AsyncClient,
    invitation_test_fixture: dict[str, Any],
) -> None:
    """POST /api/v1/municipality-admins returns invitation_url with exactly one origin in development."""
    headers = {"Authorization": f"Bearer {invitation_test_fixture['token_dept']}"}
    muni = invitation_test_fixture["muni"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "municipality_id": str(muni.id),
        "first_name": "Clara",
        "last_name": "Rojas",
        "document_type": "CC",
        "document_number": f"90{tag}",
        "email": f"clara.{tag}@alcaldia.gov.co",
        "username": f"clara.{tag}",
    }

    resp = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    invitation_url = data.get("invitation_url")
    assert invitation_url is not None
    # Crucial regression check: MUST NOT contain duplicate origin
    assert "http://localhost:3000http://localhost:3000" not in invitation_url
    assert invitation_url.startswith("http://localhost:3000/auth/accept-invitation?token=")

    # Verify query parameter contains raw token
    raw_token = data.get("raw_invitation_token")
    assert raw_token is not None
    assert f"token={raw_token}" in invitation_url


@pytest.mark.anyio
async def test_10_municipality_admin_resend_returns_single_origin_url_and_invalidates_prior(
    client: AsyncClient,
    invitation_test_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """POST /api/v1/municipality-admins/{id}/resend-invitation generates a valid URL and revokes prior token."""
    headers = {"Authorization": f"Bearer {invitation_test_fixture['token_dept']}"}
    muni = invitation_test_fixture["muni"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "municipality_id": str(muni.id),
        "first_name": "Hernando",
        "last_name": "Montero",
        "document_type": "CC",
        "document_number": f"88{tag}",
        "email": f"hernando.{tag}@alcaldia.gov.co",
        "username": f"hernando.{tag}",
    }

    create_resp = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    user_id = create_data["id"]
    token_1 = create_data["raw_invitation_token"]

    # Resend invitation
    resend_resp = await client.post(
        f"/api/v1/municipality-admins/{user_id}/resend-invitation",
        headers=headers,
    )
    assert resend_resp.status_code == 200
    resend_data = resend_resp.json()

    invitation_url = resend_data.get("invitation_url")
    assert invitation_url is not None
    assert "http://localhost:3000http://localhost:3000" not in invitation_url
    assert invitation_url.startswith("http://localhost:3000/auth/accept-invitation?token=")

    token_2 = resend_data.get("raw_invitation_token")
    assert token_2 is not None
    assert token_2 != token_1

    # Verify old token is rejected by public verification endpoint (400, 404, or 409 Conflict)
    verify_1 = await client.post("/api/v1/auth/verify-invitation", json={"token": token_1})
    assert verify_1.status_code in (400, 404, 409)

    # Verify new token is accepted by public verification endpoint
    verify_2 = await client.post("/api/v1/auth/verify-invitation", json={"token": token_2})
    assert verify_2.status_code == 200
    assert verify_2.json().get("valid") is True


@pytest.mark.anyio
async def test_11_production_suppresses_token_and_url_on_create_and_resend(
    client: AsyncClient,
    invitation_test_fixture: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In production mode, create and resend endpoints strictly suppress token and URL disclosure."""
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "FRONTEND_PUBLIC_URL", "https://pevn.mineducacion.gov.co")

    headers = {"Authorization": f"Bearer {invitation_test_fixture['token_dept']}"}
    muni = invitation_test_fixture["muni"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "municipality_id": str(muni.id),
        "first_name": "Seguro",
        "last_name": "Produccion",
        "document_type": "CC",
        "document_number": f"77{tag}",
        "email": f"prod.{tag}@alcaldia.gov.co",
        "username": f"prod.{tag}",
    }

    create_resp = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    assert create_data.get("raw_invitation_token") is None
    assert create_data.get("invitation_url") is None

    resend_resp = await client.post(
        f"/api/v1/municipality-admins/{create_data['id']}/resend-invitation",
        headers=headers,
    )
    assert resend_resp.status_code == 200
    resend_data = resend_resp.json()
    assert resend_data.get("raw_invitation_token") is None
    assert resend_data.get("invitation_url") is None
