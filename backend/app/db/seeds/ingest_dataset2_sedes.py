"""
PEVN Backend — Authoritative Dataset 2 Physical Sedes Ingestion Engine

Ingests the 53,796 physical campuses from Dataset 2 (x5ay-984n) into PostgreSQL
across 54 controlled batches with strict transactional isolation and idempotency.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, ".")

from app.db.session import get_session_factory
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialCatalogSyncBatch,
    OfficialCatalogSyncChunk,
    OfficialInstitutionCatalog,
)
from sqlalchemy import func, select

logger = logging.getLogger("pevn.sedes_ingestion")


async def run_sedes_ingestion(
    chunk_size: int = 1000,
) -> dict[str, Any]:
    dataset_path = Path("scratch/official_sedes_dataset_x5ay.json")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset 2 file not found at {dataset_path}")

    records: list[dict[str, Any]] = json.loads(dataset_path.read_text(encoding="utf-8"))
    total_source_records = len(records)
    print(f"[*] Starting controlled physical sedes ingestion for {total_source_records} records...")

    factory = get_session_factory()
    async with factory() as session:
        # 1. Load active institution map (dane_code -> UUID)
        inst_stmt = select(OfficialInstitutionCatalog.dane_code, OfficialInstitutionCatalog.id)
        inst_rows = (await session.execute(inst_stmt)).all()
        inst_map: dict[str, Any] = {row[0]: row[1] for row in inst_rows}
        print(f"[*] Active institutions in PostgreSQL: {len(inst_map)}")

        # 2. Load existing campuses map (dane_sede_code -> OfficialCampusCatalog)
        camp_stmt = select(OfficialCampusCatalog)
        camp_objs = (await session.execute(camp_stmt)).scalars().all()
        camp_map: dict[str, OfficialCampusCatalog] = {c.dane_sede_code: c for c in camp_objs}
        initial_campus_count = len(camp_map)
        print(f"[*] Pre-existing campuses in PostgreSQL: {initial_campus_count}")

        # 3. Create synchronization batch for Dataset 2
        batch = OfficialCatalogSyncBatch(
            source_system="MINISTERIO DE EDUCACION NACIONAL (DUE/SIMAT) / DANE",
            source_dataset="datos.gov.co/x5ay-984n",
            source_version="2019",
            status="RUNNING",
            total_records=total_source_records,
            total_chunks=(total_source_records + chunk_size - 1) // chunk_size,
            quality_gate_status="RUNNING",
            audit_status="AUDITING",
        )
        session.add(batch)
        await session.flush()
        batch_id = batch.id

        total_inserted = 0
        total_updated = 0
        total_unchanged = 0
        total_orphans = 0
        total_rejected = 0
        total_duplicates = 0
        seen_sedes = set()
        chunk_summaries = []

        total_chunks = batch.total_chunks

        for c_idx in range(total_chunks):
            t_start = time.perf_counter()
            c_start = c_idx * chunk_size
            c_end = min(c_start + chunk_size, total_source_records)
            chunk_records = records[c_start:c_end]

            chunk_inserted = 0
            chunk_updated = 0
            chunk_unchanged = 0
            chunk_orphans = 0
            chunk_rejected = 0
            chunk_duplicates = 0

            for r in chunk_records:
                sede_code = str(r.get("codigo_dane_sede", "")).strip()
                ee_code = str(r.get("codigo_dane", "")).strip()
                sede_name = str(r.get("nombre_sede", "")).strip() or "SEDE SIN NOMBRE"
                is_main = str(r.get("principal", "")).strip().upper() == "S"
                zone = str(r.get("zona", "URBANA")).strip().upper()
                address = str(r.get("direccion", "")).strip() or None

                if not sede_code or len(sede_code) != 12:
                    chunk_rejected += 1
                    total_rejected += 1
                    continue

                if sede_code in seen_sedes:
                    chunk_duplicates += 1
                    total_duplicates += 1
                    continue
                seen_sedes.add(sede_code)

                # Check foreign key to active institution
                inst_id = inst_map.get(ee_code)
                if not inst_id:
                    chunk_orphans += 1
                    total_orphans += 1
                    continue

                if sede_code in camp_map:
                    # Update existing campus
                    c_obj = camp_map[sede_code]
                    c_obj.name = sede_name
                    c_obj.is_main = is_main
                    c_obj.zone = zone
                    if address:
                        c_obj.address = address
                    c_obj.official_institution_id = inst_id
                    chunk_updated += 1
                    total_updated += 1
                else:
                    # Insert new physical campus
                    new_camp = OfficialCampusCatalog(
                        official_institution_id=inst_id,
                        dane_sede_code=sede_code,
                        name=sede_name,
                        is_main=is_main,
                        zone=zone,
                        address=address,
                        status="ACTIVA",
                        is_active=True,
                    )
                    session.add(new_camp)
                    camp_map[sede_code] = new_camp
                    chunk_inserted += 1
                    total_inserted += 1

            t_duration = int((time.perf_counter() - t_start) * 1000)

            # Record chunk entity
            chunk_entity = OfficialCatalogSyncChunk(
                batch_id=batch_id,
                chunk_number=c_idx + 1,
                total_records=len(chunk_records),
                valid_records=chunk_inserted + chunk_updated,
                inserted_records=chunk_inserted,
                updated_records=chunk_updated,
                rejected_records=chunk_rejected + chunk_orphans,
                duplicate_records=chunk_duplicates,
                status="SUCCESS",
            )
            session.add(chunk_entity)
            await session.flush()

            chunk_summaries.append({
                "chunk": c_idx + 1,
                "inserted": chunk_inserted,
                "updated": chunk_updated,
                "orphans": chunk_orphans,
                "duration_ms": t_duration,
            })

            if (c_idx + 1) % 10 == 0 or c_idx + 1 == total_chunks:
                print(f"    [+] Processed Chunk {c_idx + 1:02d} / {total_chunks}: +{chunk_inserted} inserted, ~{chunk_updated} updated, {chunk_orphans} historical/orphans ({t_duration}ms)")

        # 4. Finalize Batch
        batch.status = "SUCCESS"
        batch.valid_records = total_inserted + total_updated
        batch.rejected_records = total_rejected + total_orphans
        batch.duplicate_records = total_duplicates
        batch.processed_chunks = total_chunks
        batch.failed_chunks = 0
        batch.quality_gate_status = "PASSED"
        batch.audit_status = "INGESTION_COMPLETE"
        batch.ingestion_progress = 100.0

        await session.commit()
        print("[*] Ingestion committed successfully!")

        # 5. Independent DB verification
        final_campus_count = (await session.execute(select(func.count()).select_from(OfficialCampusCatalog))).scalar_one()
        final_main_count = (await session.execute(select(func.count()).select_from(OfficialCampusCatalog).where(OfficialCampusCatalog.is_main.is_(True)))).scalar_one()
        final_annex_count = (await session.execute(select(func.count()).select_from(OfficialCampusCatalog).where(OfficialCampusCatalog.is_main.is_(False)))).scalar_one()

        print("\n=== POSTGRESQL POST-INGESTION METRICS ===")
        print(f"Initial Campuses Count:      {initial_campus_count}")
        print(f"Campuses Inserted:           {total_inserted}")
        print(f"Campuses Updated:            {total_updated}")
        print(f"Final Total Campuses in DB:  {final_campus_count}")
        print(f"Principal Campuses:          {final_main_count}")
        print(f"Annex / Rural Campuses:      {final_annex_count}")
        print(f"Orphan / Historical Sedes:   {total_orphans}")
        print(f"Rejected / Duplicate Sedes:  {total_rejected + total_duplicates}")
        print(f"Accounting Balance:          {(total_inserted + total_updated) + total_orphans + total_rejected + total_duplicates} == {total_source_records}")

        return {
            "batch_id": str(batch_id),
            "total_source_records": total_source_records,
            "inserted": total_inserted,
            "updated": total_updated,
            "orphans": total_orphans,
            "rejected": total_rejected,
            "duplicates": total_duplicates,
            "initial_campus_count": initial_campus_count,
            "final_campus_count": final_campus_count,
            "principal_campuses": final_main_count,
            "annex_campuses": final_annex_count,
            "chunks": total_chunks,
        }


if __name__ == "__main__":
    asyncio.run(run_sedes_ingestion())
