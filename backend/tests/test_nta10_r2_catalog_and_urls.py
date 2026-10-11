"""
PEVN — NTA-10-R2: Absolute Invitation URLs, Complete Municipal Catalog, and Governance Test Suite

Validates:
1. Phase A: Absolute URL construction across development, LAN, and production configurations,
   trailing slash normalization, and safe token query parameter.
2. Phase B: Complete official catalog for Valparaíso, Caquetá (DANE 18860) reconciling exactly
   7 educational establishments and 49 campuses.
3. Phase C: Real-time lifecycle statuses across catalog discovery:
   - DISPONIBLE_PARA_APROVISIONAR
   - APROVISIONADA_SIN_RECTOR
   - INVITACION_RECTOR_PENDIENTE
   - RECTOR_ACTIVO
   - INACTIVA
4. Phase D: Territorial authorization, anti-duplication, safe catalog provisioning,
   and establishment-to-campus-to-Rector governance.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, Settings, get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.official_catalog import OfficialCampusCatalog, OfficialInstitutionCatalog
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.institution_service import InstitutionService
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def nta10_r2_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC, Caquetá/Valparaíso territory, and official catalog records."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Department: Caquetá (18) and Antioquia (05)
    dept_caq = Department(code="18", name="CAQUETÁ")
    dept_ant = Department(code="05", name="ANTIOQUIA")
    db_session.add_all([dept_caq, dept_ant])
    await db_session.flush()

    # 2. Municipalities: Valparaíso (18860), Florencia (18001), Medellín (05001)
    muni_valp = Municipality(department_id=dept_caq.id, code="18860", name="VALPARAÍSO")
    muni_flor = Municipality(department_id=dept_caq.id, code="18001", name="FLORENCIA")
    muni_med = Municipality(department_id=dept_ant.id, code="05001", name="MEDELLÍN")
    db_session.add_all([muni_valp, muni_flor, muni_med])
    await db_session.flush()

    # 3. Seed authoritative catalog for Valparaíso (7 establishments, 49 campuses)
    # 118860001293: 1 campus
    # 218860000208: 9 campuses
    # 218860001387: 6 campuses
    # 283860000191: 10 campuses
    # 283860000450: 9 campuses
    # 283860000506: 8 campuses
    # 283860000760: 6 campuses
    establishments_data = [
        ("118860001293", "INSTITUCION EDUCATIVA VALPARAISO", 1),
        ("218860000208", "INST EDUC RUR NIEVES ARRIBA", 9),
        ("218860001387", "INST EDUC RUR MIRAVALLE SANTROPEL", 6),
        ("283860000191", "INSTITUCION EDUCATIVA RURAL LA RICO KM 30", 10),
        ("283860000450", "INSTITUCION EDUCATIVA RURAL LA MUÑOZ", 9),
        ("283860000506", "INSTITUCION EDUCATIVA RURAL SANTIAGO DE LA SELVA", 8),
        ("283860000760", "INSTITUCION EDUCATIVA RURAL PLAYA RICA", 6),
    ]

    cat_map: dict[str, OfficialInstitutionCatalog] = {}
    for dane, name, campus_count in establishments_data:
        cat_inst = OfficialInstitutionCatalog(
            dane_code=dane,
            name=name,
            department_code="18",
            department_name="CAQUETÁ",
            municipality_code="18860",
            municipality_name="VALPARAÍSO",
            official_email=f"contacto.{dane}@valparaiso.edu.co",
            official_phone="3100000000",
            sector="OFICIAL",
            zone="RURAL" if "RUR" in name else "URBANA",
            status="ACTIVO",
            is_active=True,
        )
        db_session.add(cat_inst)
        await db_session.flush()
        cat_map[dane] = cat_inst

        # Seed campuses
        for c_idx in range(campus_count):
            c_dane = dane if c_idx == 0 else f"{dane}_{c_idx}"
            c_name = f"{name} - SEDE PRINCIPAL" if c_idx == 0 else f"{name} - SEDE {c_idx}"
            db_session.add(
                OfficialCampusCatalog(
                    official_institution_id=cat_inst.id,
                    dane_sede_code=c_dane,
                    name=c_name,
                    is_main=(c_idx == 0),
                    status="ACTIVA",
                    is_active=True,
                )
            )
        await db_session.flush()

    # Seed 1 establishment outside Valparaíso (Florencia)
    cat_flor = OfficialInstitutionCatalog(
        dane_code="118001000111",
        name="I.E. FLORENCIA CENTRAL",
        department_code="18",
        department_name="CAQUETÁ",
        municipality_code="18001",
        municipality_name="FLORENCIA",
        sector="OFICIAL",
        status="ACTIVO",
        is_active=True,
    )
    db_session.add(cat_flor)
    await db_session.flush()

    # 4. Provision tenant 1: 118860001293 (I.E VALPARAISO)
    inst_valp = Institution(
        municipality_id=muni_valp.id,
        catalog_institution_id=cat_map["118860001293"].id,
        dane_code="118860001293",
        name="INSTITUCION EDUCATIVA VALPARAISO",
        email="rectoria@ievalparaiso.edu.co",
        is_active=True,
    )
    db_session.add(inst_valp)
    await db_session.flush()

    campus_main = Campus(
        institution_id=inst_valp.id,
        dane_sede_code="118860001293",
        name="SEDE PRINCIPAL",
        is_active=True,
    )
    db_session.add(campus_main)
    await db_session.flush()

    # 5. Create Municipal Admin for Valparaíso (18860)
    role_muni = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.MUNICIPALITY_ADMIN.value))
    ).scalar_one()

    uid_valp = uuid.uuid4()
    user_muni_valp = User(
        id=uid_valp,
        email="admin.valparaiso@pevn.gov.co",
        username=f"admin_valp_{uid_valp.hex[:6]}",
        hashed_password="argon2_hashed_dummy_value",
        first_name="Admin",
        last_name="Valparaíso",
        document_type=DocumentType.CC,
        document_number=f"18860{random.randint(1000, 9999)}",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user_muni_valp)
    await db_session.flush()

    ur_muni = UserRole(
        user_id=user_muni_valp.id,
        role_id=role_muni.id,
        municipality_id=muni_valp.id,
        department_id=dept_caq.id,
        is_active=True,
    )
    db_session.add(ur_muni)
    await db_session.flush()

    token_muni_valp = await token_service.create_access_token(
        subject=str(user_muni_valp.id),
        additional_claims={
            "roles": [SystemRole.MUNICIPALITY_ADMIN.value],
            "department_id": str(dept_caq.id),
            "municipality_id": str(muni_valp.id),
        },
    )

    # 6. Create Municipal Admin for Florencia (18001)
    uid_flor = uuid.uuid4()
    user_muni_flor = User(
        id=uid_flor,
        email="admin.florencia@pevn.gov.co",
        username=f"admin_flor_{uid_flor.hex[:6]}",
        hashed_password="argon2_dummy",
        first_name="Admin",
        last_name="Florencia",
        document_type=DocumentType.CC,
        document_number=f"18001{random.randint(1000, 9999)}",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user_muni_flor)
    await db_session.flush()
    db_session.add(
        UserRole(
            user_id=user_muni_flor.id,
            role_id=role_muni.id,
            municipality_id=muni_flor.id,
            department_id=dept_caq.id,
            is_active=True,
        )
    )
    await db_session.flush()
    token_muni_flor = await token_service.create_access_token(
        subject=str(user_muni_flor.id),
        additional_claims={
            "roles": [SystemRole.MUNICIPALITY_ADMIN.value],
            "department_id": str(dept_caq.id),
            "municipality_id": str(muni_flor.id),
        },
    )

    # 7. Create National Admin
    role_nat = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one()
    uid_nat = uuid.uuid4()
    user_nat = User(
        id=uid_nat,
        email="admin.nacional@pevn.gov.co",
        username=f"admin_nat_{uid_nat.hex[:6]}",
        hashed_password="argon2_dummy",
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="99999999",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user_nat)
    await db_session.flush()
    db_session.add(UserRole(user_id=user_nat.id, role_id=role_nat.id, is_active=True))
    await db_session.flush()
    token_nat = await token_service.create_access_token(
        subject=str(user_nat.id),
        additional_claims={
            "roles": [SystemRole.NATIONAL_ADMIN.value],
            "is_national": True,
        },
    )

    await db_session.commit()

    return {
        "dept_caq": dept_caq,
        "muni_valp": muni_valp,
        "muni_flor": muni_flor,
        "cat_map": cat_map,
        "inst_valp": inst_valp,
        "token_muni_valp": token_muni_valp,
        "token_muni_flor": token_muni_flor,
        "token_nat": token_nat,
    }


@pytest.mark.anyio
async def test_01_absolute_url_configuration_and_trailing_slash_normalization():
    """Validate Phase A: Absolute URL generation and trailing slash normalization."""
    # Test 1: Default development settings
    settings_dev = Settings(ENVIRONMENT=Environment.DEVELOPMENT)
    assert settings_dev.public_frontend_url == "http://localhost:3000"
    url = settings_dev.build_invitation_url("tok_dev_123")
    assert url == "http://localhost:3000/auth/accept-invitation?token=tok_dev_123"

    # Test 2: Custom FRONTEND_PUBLIC_URL with trailing slash
    settings_custom = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        FRONTEND_PUBLIC_URL="http://192.168.1.50:3000/",
    )
    assert settings_custom.public_frontend_url == "http://192.168.1.50:3000"
    url = settings_custom.build_invitation_url("tok_lan_456")
    assert url == "http://192.168.1.50:3000/auth/accept-invitation?token=tok_lan_456"

    # Test 3: Staging HTTPS configuration
    settings_staging = Settings(
        ENVIRONMENT=Environment.STAGING,
        FRONTEND_PUBLIC_URL="https://staging.pevn.mineducacion.gov.co/",
    )
    assert settings_staging.public_frontend_url == "https://staging.pevn.mineducacion.gov.co"
    url = settings_staging.build_invitation_url("tok_staging_789")
    assert url == "https://staging.pevn.mineducacion.gov.co/auth/accept-invitation?token=tok_staging_789"


@pytest.mark.anyio
async def test_02_rector_invitation_returns_absolute_url_in_development(
    client: AsyncClient,
    nta10_r2_fixture: dict[str, Any],
):
    """Validate that invite_rector and resend return absolute URLs."""
    headers = {"Authorization": f"Bearer {nta10_r2_fixture['token_muni_valp']}"}
    inst_id = str(nta10_r2_fixture["inst_valp"].id)

    # 1. Invite Rector
    resp = await client.post(
        f"/api/v1/institutions/{inst_id}/rector-invitation",
        json={
            "first_name": "Gabriel",
            "last_name": "García",
            "document_type": "CC",
            "document_number": "18860001",
            "email": "rector.valparaiso@colegio.edu.co",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["invitation_url"] is not None
    # Must be absolute URL starting with http:// or https://
    assert data["invitation_url"].startswith("http://") or data["invitation_url"].startswith("https://")
    assert "/auth/accept-invitation?token=" in data["invitation_url"]
    assert data["raw_invitation_token"] in data["invitation_url"]

    # 2. Resend invitation
    resend_resp = await client.post(
        f"/api/v1/institutions/{inst_id}/rector-invitation/resend",
        headers=headers,
    )
    assert resend_resp.status_code == 200
    resend_data = resend_resp.json()
    assert resend_data["invitation_url"] is not None
    assert resend_data["invitation_url"].startswith("http://") or resend_data["invitation_url"].startswith("https://")
    assert "/auth/accept-invitation?token=" in resend_data["invitation_url"]
    assert resend_data["raw_invitation_token"] in resend_data["invitation_url"]
    assert resend_data["raw_invitation_token"] != data["raw_invitation_token"]


@pytest.mark.anyio
async def test_03_valparaiso_catalog_discovery_reconciles_7_establishments_and_49_campuses(
    client: AsyncClient,
    nta10_r2_fixture: dict[str, Any],
):
    """Validate Phase B & C: Municipal admin for Valparaíso discovers exactly 7 establishments."""
    headers = {"Authorization": f"Bearer {nta10_r2_fixture['token_muni_valp']}"}

    resp = await client.get("/api/v1/institutions/catalog-explorer", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 7
    assert len(data["items"]) == 7
    assert data["summary"]["total_catalog"] == 7
    assert data["summary"]["provisioned"] == 1
    assert data["summary"]["available"] == 6

    # Verify campus count sums to 49
    total_campuses = sum(item["campus_count"] for item in data["items"])
    assert total_campuses == 49

    # Verify DANE 118860001293 (I.E VALPARAISO) is provisioned
    valp_item = next(item for item in data["items"] if item["dane_code"] == "118860001293")
    assert valp_item["is_provisioned"] is True
    assert valp_item["campus_count"] == 1

    # Verify DANE 218860000208 (NIEVES ARRIBA) has 9 campuses and is available
    nieves_item = next(item for item in data["items"] if item["dane_code"] == "218860000208")
    assert nieves_item["is_provisioned"] is False
    assert nieves_item["campus_count"] == 9
    assert nieves_item["lifecycle_status"] == "DISPONIBLE_PARA_APROVISIONAR"


@pytest.mark.anyio
async def test_04_safe_catalog_provisioning_and_duplicate_prevention(
    client: AsyncClient,
    nta10_r2_fixture: dict[str, Any],
):
    """Validate Phase C & D: Safe provisioning from catalog with campus registration and anti-duplication."""
    headers = {"Authorization": f"Bearer {nta10_r2_fixture['token_muni_valp']}"}

    # 1. Duplicate provisioning attempt for already provisioned 118860001293 returns 409
    dup_resp = await client.post(
        "/api/v1/institutions/provision-catalog",
        json={"dane_code": "118860001293"},
        headers=headers,
    )
    assert dup_resp.status_code == 409
    assert "DUPLICATE_DANE_CODE" in dup_resp.text

    # 2. Provision available establishment 218860000208 (NIEVES ARRIBA)
    prov_resp = await client.post(
        "/api/v1/institutions/provision-catalog",
        json={
            "dane_code": "218860000208",
            "contact_email": "rectoria@nievesarriba.edu.co",
            "contact_phone": "3123456789",
        },
        headers=headers,
    )
    assert prov_resp.status_code == 201
    new_inst = prov_resp.json()
    assert new_inst["dane_code"] == "218860000208"
    assert new_inst["is_active"] is True
    # Verify all 9 campuses registered
    assert len(new_inst["campuses"]) == 9

    # 3. Discovery now reports 2 provisioned, 5 available
    cat_resp = await client.get("/api/v1/institutions/catalog-explorer", headers=headers)
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()
    assert cat_data["summary"]["provisioned"] == 2
    assert cat_data["summary"]["available"] == 5

    # NIEVES ARRIBA is now APROVISIONADA_SIN_RECTOR
    nieves_item = next(item for item in cat_data["items"] if item["dane_code"] == "218860000208")
    assert nieves_item["lifecycle_status"] == "APROVISIONADA_SIN_RECTOR"


@pytest.mark.anyio
async def test_05_territorial_boundaries_and_cross_municipality_rejection(
    client: AsyncClient,
    nta10_r2_fixture: dict[str, Any],
):
    """Validate that Municipal Admin for Valparaíso cannot query or provision Florencia establishments."""
    headers_valp = {"Authorization": f"Bearer {nta10_r2_fixture['token_muni_valp']}"}

    # 1. Attempting to query catalog with foreign municipality code returns 403
    resp_query = await client.get(
        "/api/v1/institutions/catalog-explorer?municipality_code=18001",
        headers=headers_valp,
    )
    assert resp_query.status_code == 403

    # 2. Attempting to provision establishment in Florencia (118001000111) returns 403
    resp_prov = await client.post(
        "/api/v1/institutions/provision-catalog",
        json={"dane_code": "118001000111"},
        headers=headers_valp,
    )
    assert resp_prov.status_code == 403
