#!/usr/bin/env python3
"""
PEVN Backend Test Collection and Arithmetic Reconciliation Analyzer (DOC-04-R8)

Derives authoritative collection counts from pytest directly in an isolated process.
Supports execution from both repository root and the backend working directory.
Guarantees fail-closed exit if collection fails, parsing is incomplete, duplicates exist,
or category partitioning is mathematically inconsistent.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Explicit canonical PostgreSQL integration test suites (exactly 6 suites)
POSTGRESQL_INTEGRATION_SUITES: frozenset[str] = frozenset({
    "test_nta02_national_divipola_foundation.py",
    "test_nta03_catalog_provisioning_architecture.py",
    "test_nta04_national_provisioning_workflow.py",
    "test_nta05_territorial_control_center.py",
    "test_sa01_superadmin_governance.py",
    "test_sa02_technical_operations_portal.py",
})

NAMED_PROVISIONING_SUITES: frozenset[str] = frozenset({
    "test_institution_provisioning.py",
    "test_nta10_rector_provisioning.py",
})

DB_SAFETY_SUITES: frozenset[str] = frozenset({
    "test_db_safety.py",
})


def parse_collection_output(stdout: str) -> dict[str, Any]:
    """
    Parse pytest collection output supporting both tree-formatted output
    (<Module ...> / <Coroutine|Function|Item ...>) and node-ID format
    (tests/test_*.py::test_name).

    Detects duplicate test entries, malformed records, and summary counts.
    """
    lines = stdout.splitlines()
    counts: dict[str, int] = {}
    seen_tests: set[tuple[str, str]] = set()
    duplicates: list[str] = []
    errors: list[str] = []

    current_module: str | None = None
    summary_collected: int | None = None

    module_pattern = re.compile(r"^<Module\s+([^>]+)>")
    item_pattern = re.compile(r"^\s*<(Coroutine|Function|Item)\s+([^>]+)>")
    nodeid_pattern = re.compile(r"^(?:tests[\\/])?([^:\\/\s]+\.py)::([^\s]+)")
    summary_pattern = re.compile(r"(\d+)\s+tests?\s+collected")
    summary_pattern_alt = re.compile(r"collected\s+(\d+)\s+items?")

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Check summary line
        sum_m = summary_pattern.search(line) or summary_pattern_alt.search(line)
        if sum_m:
            summary_collected = int(sum_m.group(1))
            continue

        # Check Tree Format: Module
        mod_m = module_pattern.match(line)
        if mod_m:
            mod_name = Path(mod_m.group(1).strip()).name
            current_module = mod_name
            if current_module not in counts:
                counts[current_module] = 0
            continue

        # Check Tree Format: Test Item
        item_m = item_pattern.match(line)
        if item_m:
            if not current_module:
                errors.append(f"Test item found before any module declaration: {line}")
                continue
            test_name = item_m.group(2).strip()
            test_id = (current_module, test_name)
            if test_id in seen_tests:
                duplicates.append(f"{current_module}::{test_name}")
            else:
                seen_tests.add(test_id)
                counts[current_module] += 1
            continue

        # Check NodeID Format: e.g. tests/test_foo.py::test_bar
        node_m = nodeid_pattern.match(line)
        if node_m:
            mod_name = Path(node_m.group(1).strip()).name
            test_name = node_m.group(2).strip()
            if mod_name not in counts:
                counts[mod_name] = 0
            test_id = (mod_name, test_name)
            if test_id in seen_tests:
                duplicates.append(f"{mod_name}::{test_name}")
            else:
                seen_tests.add(test_id)
                counts[mod_name] += 1
            continue

    parsed_total = sum(counts.values())

    return {
        "counts": counts,
        "parsed_total": parsed_total,
        "summary_collected": summary_collected,
        "duplicates": duplicates,
        "errors": errors,
    }


def reconcile_census(counts: dict[str, int], summary_collected: int | None) -> dict[str, Any]:
    """
    Reconcile parsed test counts with summary, enforce PostgreSQL suite
    completeness, and verify category partition arithmetic.
    """
    reconciliation_errors: list[str] = []
    parsed_total = sum(counts.values())

    if not counts or parsed_total == 0:
        reconciliation_errors.append("No modules or tests parsed from collection.")

    if summary_collected is None:
        reconciliation_errors.append("Pytest summary line was not found in collection output.")
    elif parsed_total != summary_collected:
        reconciliation_errors.append(
            f"Parsed total ({parsed_total}) does not match pytest summary ({summary_collected})."
        )

    # Validate that all 6 canonical PostgreSQL suites are present
    missing_pg = POSTGRESQL_INTEGRATION_SUITES - set(counts.keys())
    if missing_pg:
        reconciliation_errors.append(
            f"Missing required PostgreSQL integration suites: {sorted(missing_pg)}"
        )

    # Category partition: PostgreSQL vs Unit/In-Memory
    pg_modules = {m: counts[m] for m in counts if m in POSTGRESQL_INTEGRATION_SUITES}
    pg_total = sum(pg_modules.values())

    inst_count = counts.get("test_institution_provisioning.py", 0)
    rector_count = counts.get("test_nta10_rector_provisioning.py", 0)
    db_safety_count = counts.get("test_db_safety.py", 0)

    special_modules = (
        POSTGRESQL_INTEGRATION_SUITES
        | NAMED_PROVISIONING_SUITES
        | DB_SAFETY_SUITES
    )
    remaining_modules = {m: counts[m] for m in counts if m not in special_modules}
    remaining_total = sum(remaining_modules.values())

    unit_total = inst_count + rector_count + db_safety_count + remaining_total
    unit_modules_count = len(counts) - len(pg_modules)
    grand_total = pg_total + unit_total

    # Verify arithmetic
    arithmetic_valid = (
        (pg_total + unit_total == grand_total)
        and (len(pg_modules) + unit_modules_count == len(counts))
        and (grand_total == parsed_total)
        and (len(reconciliation_errors) == 0)
    )

    return {
        "grand_total": grand_total,
        "total_files": len(counts),
        "pg_total": pg_total,
        "pg_files": len(pg_modules),
        "pg_modules": pg_modules,
        "unit_total": unit_total,
        "unit_files": unit_modules_count,
        "inst_count": inst_count,
        "rector_count": rector_count,
        "db_safety_count": db_safety_count,
        "remaining_total": remaining_total,
        "remaining_files": len(remaining_modules),
        "arithmetic_valid": arithmetic_valid,
        "errors": reconciliation_errors,
    }


def analyze(backend_dir: Path | None = None) -> int:
    """Execute collection and print human-readable and structured census results."""
    if backend_dir is None:
        script_path = Path(__file__).resolve()
        backend_dir = script_path.parent.parent

    tests_dir = backend_dir / "tests"
    if not tests_dir.is_dir():
        print(f"FATAL: Tests directory not found at: {tests_dir}", file=sys.stderr)
        return 2

    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    cmd_str = " ".join(cmd)

    print("=" * 80)
    print("PEVN — Authoritative Backend Test Collection & Reconciliation Analyzer (R8)")
    print(f"Working Directory : {backend_dir}")
    print(f"Execution Command : {cmd_str}")
    print("=" * 80)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("FATAL: pytest collection timed out after 45 seconds.", file=sys.stderr)
        return 6
    except Exception as exc:
        print(f"FATAL: Failed to launch pytest subprocess: {exc}", file=sys.stderr)
        return 3

    if proc.returncode != 0:
        print(f"FATAL: pytest collection returned non-zero exit code: {proc.returncode}", file=sys.stderr)
        print("STDERR:\n" + proc.stderr.strip(), file=sys.stderr)
        print("STDOUT:\n" + proc.stdout.strip(), file=sys.stderr)
        return proc.returncode

    # Parse collection output
    parsed = parse_collection_output(proc.stdout)
    if parsed["errors"]:
        for err in parsed["errors"]:
            print(f"FATAL: Parsing error: {err}", file=sys.stderr)
        return 4

    if parsed["duplicates"]:
        for dup in parsed["duplicates"]:
            print(f"FATAL: Duplicate test detected: {dup}", file=sys.stderr)
        return 4

    # Reconcile census
    reconciled = reconcile_census(parsed["counts"], parsed["summary_collected"])
    if not reconciled["arithmetic_valid"]:
        for err in reconciled["errors"]:
            print(f"FATAL: Reconciliation failure: {err}", file=sys.stderr)
        return 5

    # 6. Formatted Output Report
    counts = parsed["counts"]
    print(f"\n[1] Inventario de Módulos Censados: {reconciled['total_files']} archivos de prueba")
    print(f"[2] Gran Total de Pruebas Recolectadas: {reconciled['grand_total']}")
    print("\n[3] Desglose por Categorías Mutuamente Excluyentes:")
    print(f"  • Grupo A — Integración PostgreSQL ({reconciled['pg_files']} archivos): {reconciled['pg_total']} pruebas")
    for mod in sorted(reconciled["pg_modules"]):
        print(f"      - {mod}: {reconciled['pg_modules'][mod]}")

    print(f"\n  • Grupo B — Suites Unitarias y En Memoria ({reconciled['unit_files']} archivos): {reconciled['unit_total']} pruebas")
    print(f"      - Provisión Institucional (test_institution_provisioning.py): {reconciled['inst_count']}")
    print(f"      - Provisión de Rector (test_nta10_rector_provisioning.py): {reconciled['rector_count']}")
    print(f"      - Seguridad de Base de Datos (test_db_safety.py): {reconciled['db_safety_count']}")
    print(f"      - Suites Unitarias / Modelos / Servicios Restantes ({reconciled['remaining_files']} archivos): {reconciled['remaining_total']}")

    print("\n[4] Reconciliación Aritmética Matemática:")
    print(f"    PostgreSQL ({reconciled['pg_total']}) + Unitarias ({reconciled['unit_total']}) = {reconciled['grand_total']}")
    print(f"    {reconciled['pg_total']} + {reconciled['inst_count']} + {reconciled['rector_count']} + {reconciled['db_safety_count']} + {reconciled['remaining_total']} = {reconciled['grand_total']}")
    print(f"    Verificación de Suma: {reconciled['arithmetic_valid']}")

    print("\n[5] Resumen Estructurado para Auditoría:")
    print(f"    CENSO_TOTAL_PRUEBAS: {reconciled['grand_total']}")
    print(f"    CENSO_TOTAL_ARCHIVOS: {reconciled['total_files']}")
    print(f"    CENSO_PG_PRUEBAS: {reconciled['pg_total']}")
    print(f"    CENSO_PG_ARCHIVOS: {reconciled['pg_files']}")
    print(f"    CENSO_UNIT_PRUEBAS: {reconciled['unit_total']}")
    print(f"    CENSO_UNIT_ARCHIVOS: {reconciled['unit_files']}")
    print(f"    CENSO_SUMA_VERIFICADA: {reconciled['arithmetic_valid']}")

    print("=" * 80)
    print("RESULTADO: Colección reconciliada satisfactoriamente sin ambigüedades.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(analyze())
