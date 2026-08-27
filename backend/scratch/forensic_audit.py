"""
PEVN Forensic Database Audit Script
Strict independent forensic audit of the official catalog tables in the database.
"""

import asyncio
import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialInstitutionCatalog,
)
from app.services.institution_service import InstitutionService
from app.services.official_catalog_sync_service import OfficialCatalogSyncService

DANE_REGEX = re.compile(r"^\d{12}$")

DIVIPOLA_33_DEPARTMENTS = {
    "05": "ANTIOQUIA",
    "08": "ATLANTICO",
    "11": "BOGOTA D.C.",
    "13": "BOLIVAR",
    "15": "BOYACA",
    "17": "CALDAS",
    "18": "CAQUETA",
    "19": "CAUCA",
    "20": "CESAR",
    "23": "CORDOBA",
    "25": "CUNDINAMARCA",
    "27": "CHOCO",
    "41": "HUILA",
    "44": "LA GUAJIRA",
    "47": "MAGDALENA",
    "50": "META",
    "52": "NARINO",
    "54": "NORTE DE SANTANDER",
    "63": "QUINDIO",
    "66": "RISARALDA",
    "68": "SANTANDER",
    "70": "SUCRE",
    "73": "TOLIMA",
    "76": "VALLE DEL CAUCA",
    "81": "ARAUCA",
    "85": "CASANARE",
    "86": "PUTUMAYO",
    "88": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
    "91": "AMAZONAS",
    "94": "GUAINIA",
    "95": "GUAVIARE",
    "97": "VAUPES",
    "99": "VICHADA",
}


async def run_forensic_audit() -> dict[str, Any]:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    audit_results: dict[str, Any] = {}

    async with session_factory() as session:
        # Seed if empty to get real state after startup
        inst_service = InstitutionService(session=session)
        await inst_service.seed_official_catalog_if_empty()
        await session.commit()

        # 1. Inspect latest batch
        batch_stmt = select(OfficialCatalogSyncBatch).order_by(OfficialCatalogSyncBatch.started_at.desc())
        all_batches = (await session.execute(batch_stmt)).scalars().all()
        latest_batch = all_batches[0] if all_batches else None

        audit_results["batches_count"] = len(all_batches)
        if latest_batch:
            audit_results["latest_batch"] = {
                "sync_batch_id": str(latest_batch.id),
                "source_system": latest_batch.source_system,
                "source_dataset": latest_batch.source_dataset,
                "source_version": latest_batch.source_version,
                "started_at": latest_batch.started_at.isoformat() if latest_batch.started_at else None,
                "completed_at": latest_batch.completed_at.isoformat() if latest_batch.completed_at else None,
                "status": latest_batch.status,
                "total_records": latest_batch.total_records,
                "valid_records": latest_batch.valid_records,
                "rejected_records": latest_batch.rejected_records,
                "duplicate_records": latest_batch.duplicate_records,
                "institutions_count": latest_batch.institutions_count,
                "campuses_count": latest_batch.campuses_count,
                "error_summary": latest_batch.error_summary,
            }
        else:
            audit_results["latest_batch"] = None

        # 2. Query all institutions
        inst_stmt = select(OfficialInstitutionCatalog)
        institutions = (await session.execute(inst_stmt)).scalars().all()
        audit_results["institutions_count"] = len(institutions)

        # 3. Query all campuses
        campus_stmt = select(OfficialCampusCatalog)
        campuses = (await session.execute(campus_stmt)).scalars().all()
        audit_results["campuses_count"] = len(campuses)

        # 4. Department coverage audit
        dept_codes_in_db = set(inst.department_code for inst in institutions)
        expected_depts = set(DIVIPOLA_33_DEPARTMENTS.keys())
        covered_depts = dept_codes_in_db.intersection(expected_depts)
        missing_depts = expected_depts - dept_codes_in_db
        unexpected_depts = dept_codes_in_db - expected_depts

        audit_results["territorial_coverage"] = {
            "expected_departments": len(expected_depts),
            "actual_departments": len(dept_codes_in_db),
            "covered_departments_count": len(covered_depts),
            "coverage_ratio": f"{len(covered_depts)}/{len(expected_depts)} COVERED",
            "missing_departments": sorted(list(missing_depts)),
            "unexpected_departments": sorted(list(unexpected_depts)),
            "covered_codes": sorted(list(covered_depts)),
        }

        # 5. DANE Code Integrity
        dane_audit = {
            "total_checked": 0,
            "valid": 0,
            "invalid": 0,
            "duplicates": 0,
            "null_dane": 0,
            "territorial_inconsistencies": 0,
            "details": [],
        }
        inst_danes_seen: set[str] = set()
        inst_id_set = set(inst.id for inst in institutions)

        for inst in institutions:
            dane_audit["total_checked"] += 1
            code = inst.dane_code
            if code is None:
                dane_audit["null_dane"] += 1
                dane_audit["invalid"] += 1
                continue
            if not DANE_REGEX.match(code):
                dane_audit["invalid"] += 1
                dane_audit["details"].append(f"Invalid format: {code}")
            else:
                dane_audit["valid"] += 1

            if code in inst_danes_seen:
                dane_audit["duplicates"] += 1
            inst_danes_seen.add(code)

            # Territorial prefix check: first 2 digits of DANE vs department_code
            if not code.startswith(inst.department_code):
                dane_audit["territorial_inconsistencies"] += 1
                dane_audit["details"].append(f"Prefix mismatch: DANE {code} vs Dept {inst.department_code}")

        audit_results["institution_dane_audit"] = dane_audit

        # Campus DANE audit
        campus_dane_audit = {
            "total_checked": 0,
            "valid": 0,
            "invalid": 0,
            "duplicates": 0,
            "null_dane": 0,
            "orphan_campuses": 0,
            "principal_campuses": 0,
            "attached_campuses": 0,
        }
        campus_danes_seen: set[str] = set()
        for campus in campuses:
            campus_dane_audit["total_checked"] += 1
            code = campus.dane_sede_code
            if code is None:
                campus_dane_audit["null_dane"] += 1
                campus_dane_audit["invalid"] += 1
            elif not DANE_REGEX.match(code):
                campus_dane_audit["invalid"] += 1
            else:
                campus_dane_audit["valid"] += 1

            if code in campus_danes_seen:
                campus_dane_audit["duplicates"] += 1
            campus_danes_seen.add(code)

            if campus.official_institution_id not in inst_id_set:
                campus_dane_audit["orphan_campuses"] += 1

            if campus.is_main:
                campus_dane_audit["principal_campuses"] += 1
            else:
                campus_dane_audit["attached_campuses"] += 1

        audit_results["campus_dane_audit"] = campus_dane_audit

        # 6. Check sync_service status response
        sync_svc = OfficialCatalogSyncService(session=session)
        sync_status_res = await sync_svc.get_catalog_sync_status()
        audit_results["api_catalog_status_response"] = sync_status_res.model_dump(mode="json")

    await engine.dispose()
    return audit_results


if __name__ == "__main__":
    result = asyncio.run(run_forensic_audit())
    print("=== FORENSIC AUDIT OUTPUT ===")
    print(json.dumps(result, indent=2))
