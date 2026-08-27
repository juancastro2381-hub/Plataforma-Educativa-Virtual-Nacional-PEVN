import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.official_catalog import OfficialInstitutionCatalog, OfficialCampusCatalog
from app.services.promotion_authorization_gate import PromotionAuthorizationGateService


@pytest.mark.asyncio
async def test_promotion_authorization_gate_evaluation(
    db_session: AsyncSession,
) -> None:
    """
    Test that the PromotionAuthorizationGateService executes in strict read-only mode,
    evaluates all 20 gates (A to T), and strictly returns PROMOTION_AUTHORIZED = FALSE.
    """
    # Seed representative records in isolated test session
    inst = OfficialInstitutionCatalog(
        dane_code="111001000078",
        name="COLEGIO NACIONAL NICOLAS ESGUERRA",
        department_code="11",
        department_name="BOGOTA D.C.",
        municipality_code="11001",
        municipality_name="BOGOTA D.C.",
        sector="OFICIAL",
    )
    db_session.add(inst)
    await db_session.flush()

    campus = OfficialCampusCatalog(
        official_institution_id=inst.id,
        dane_sede_code="111001000078",
        name="SEDE PRINCIPAL",
        is_main=True,
        zone="URBANA",
        status="ACTIVA",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.commit()

    gate_service = PromotionAuthorizationGateService(db_session)
    cert = await gate_service.evaluate_authorization_preflight(actor_id="TEST_AUDITOR")

    assert cert["governance_status"]["promotion_authorized"] is False
    assert cert["governance_status"]["authorization_required"] is True
    assert cert["governance_status"]["catalog_status"] == "NATIONAL_CATALOG_INCOMPLETE"
    assert cert["governance_status"]["final_decision"] == "NO-GO"
    assert len(cert["certificate_hash"]) == 64
    assert len(cert["gates"]) == 20
