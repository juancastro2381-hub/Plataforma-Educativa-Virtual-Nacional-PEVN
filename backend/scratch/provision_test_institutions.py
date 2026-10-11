import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import asyncio
import uuid
from sqlalchemy import select
from app.db.session import get_session_factory
from app.models.institution import Institution
from app.models.territory import Municipality
from app.models.official_catalog import OfficialInstitutionCatalog
from app.services.institution_service import InstitutionService

async def main():
    factory = get_session_factory()
    async with factory() as session:
        service = InstitutionService(session=session)
        
        # 1. Valparaiso: DANE 118860001293
        val_dane = "118860001293"
        existing_val = (await session.execute(select(Institution).where(Institution.dane_code == val_dane))).scalar_one_or_none()
        if not existing_val:
            muni_val = (await session.execute(select(Municipality).where(Municipality.code == "18860"))).scalar_one()
            cat_val = (await session.execute(select(OfficialInstitutionCatalog).where(OfficialInstitutionCatalog.dane_code == val_dane))).scalar_one()
            inst_val = await service.provision_institution(
                dane_code=val_dane,
                name=cat_val.name,
                email="rectoria@ievalparaiso.edu.co",
                phone="3101234567",
                address=cat_val.official_address or "Valparaíso Centro",
                municipality_id=muni_val.id,
                main_campus_name="Sede Principal",
                actor_id=None,
                actor_ip="127.0.0.1",
                correlation_id="SEED-TEST-VALPARAISO",
            )
            print("Provisioned Valparaiso institution:", inst_val.name, inst_val.dane_code)
        else:
            print("Valparaiso institution already exists:", existing_val.name, existing_val.dane_code)

        # 2. Barranquilla: DANE 108001000018 (Las Americas - without rector)
        baq_dane = "108001000018"
        existing_baq = (await session.execute(select(Institution).where(Institution.dane_code == baq_dane))).scalar_one_or_none()
        if not existing_baq:
            muni_baq = (await session.execute(select(Municipality).where(Municipality.code == "08001"))).scalar_one()
            cat_baq = (await session.execute(select(OfficialInstitutionCatalog).where(OfficialInstitutionCatalog.dane_code == baq_dane))).scalar_one()
            inst_baq = await service.provision_institution(
                dane_code=baq_dane,
                name=cat_baq.name,
                email="contacto@lasamericas.edu.co",
                phone="3001234567",
                address=cat_baq.official_address or "Barranquilla",
                municipality_id=muni_baq.id,
                main_campus_name="Sede Principal",
                actor_id=None,
                actor_ip="127.0.0.1",
                correlation_id="SEED-TEST-BARRANQUILLA",
            )
            print("Provisioned Barranquilla institution:", inst_baq.name, inst_baq.dane_code)
        else:
            print("Barranquilla institution already exists:", existing_baq.name, existing_baq.dane_code)

        await session.commit()
        print("Test institutions successfully committed to pevn_db!")

if __name__ == "__main__":
    asyncio.run(main())
