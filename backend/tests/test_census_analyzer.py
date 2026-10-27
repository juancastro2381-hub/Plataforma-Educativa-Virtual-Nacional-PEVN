"""
PEVN Backend — Tests for Dynamic Test Census Analyzer & Parser (DOC-04-R8)

Validates:
  1. Parsing of tree-formatted collection output (<Module ...> / <Coroutine|Function ...>).
  2. Parsing of node-ID formatted collection output (tests/test_*.py::test_name).
  3. Detection of duplicate test entries within modules.
  4. Malformed output handling (test items before module declaration).
  5. Missing summary line detection.
  6. Category partition and reconciliation validation.
  7. Fail-closed rejection of missing PostgreSQL suites.
  8. Subprocess error and timeout handling in analyze().
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scratch.analyze_tests import (
    POSTGRESQL_INTEGRATION_SUITES,
    analyze,
    parse_collection_output,
    reconcile_census,
)


SAMPLE_VALID_TREE_OUTPUT = """
<Module test_nta02_national_divipola_foundation.py>
  <Coroutine test_01_divipola_structure>
  <Coroutine test_02_divipola_hierarchy>
<Module test_nta03_catalog_provisioning_architecture.py>
  <Coroutine test_01_catalog_schema>
<Module test_nta04_national_provisioning_workflow.py>
  <Coroutine test_01_workflow_steps>
<Module test_nta05_territorial_control_center.py>
  <Coroutine test_01_territorial_kpis>
<Module test_sa01_superadmin_governance.py>
  <Coroutine test_01_superadmin_policy>
<Module test_sa02_technical_operations_portal.py>
  <Coroutine test_01_portal_operations>
<Module test_auth_service.py>
  <Coroutine test_login_flow>
  <Function test_password_hash_verification>
<Module test_institution_provisioning.py>
  <Coroutine test_inst_prov>
<Module test_nta10_rector_provisioning.py>
  <Coroutine test_rector_prov>
<Module test_db_safety.py>
  <Coroutine test_safety_check>

======================== 12 tests collected in 0.10s =========================
"""

SAMPLE_VALID_NODEID_OUTPUT = """
tests/test_nta02_national_divipola_foundation.py::test_01_divipola_structure
tests/test_nta02_national_divipola_foundation.py::test_02_divipola_hierarchy
tests/test_nta03_catalog_provisioning_architecture.py::test_01_catalog_schema
tests/test_nta04_national_provisioning_workflow.py::test_01_workflow_steps
tests/test_nta05_territorial_control_center.py::test_01_territorial_kpis
tests/test_sa01_superadmin_governance.py::test_01_superadmin_policy
tests/test_sa02_technical_operations_portal.py::test_01_portal_operations
tests/test_auth_service.py::test_login_flow
tests/test_auth_service.py::test_password_hash_verification
tests/test_institution_provisioning.py::test_inst_prov
tests/test_nta10_rector_provisioning.py::test_rector_prov
tests/test_db_safety.py::test_safety_check

======================== 12 tests collected in 0.10s =========================
"""


def test_parse_valid_tree_format() -> None:
    """Verify tree-formatted collection output parses correctly."""
    res = parse_collection_output(SAMPLE_VALID_TREE_OUTPUT)
    assert res["summary_collected"] == 12
    assert res["parsed_total"] == 12
    assert len(res["counts"]) == 10
    assert res["duplicates"] == []
    assert res["errors"] == []
    assert res["counts"]["test_nta02_national_divipola_foundation.py"] == 2
    assert res["counts"]["test_auth_service.py"] == 2


def test_parse_valid_nodeid_format() -> None:
    """Verify node-ID formatted collection output parses correctly."""
    res = parse_collection_output(SAMPLE_VALID_NODEID_OUTPUT)
    assert res["summary_collected"] == 12
    assert res["parsed_total"] == 12
    assert len(res["counts"]) == 10
    assert res["duplicates"] == []
    assert res["errors"] == []


def test_parse_detects_duplicate_entries() -> None:
    """Verify duplicate test names within the same module are detected."""
    dup_output = """
    <Module test_auth_service.py>
      <Coroutine test_login_flow>
      <Coroutine test_login_flow>
    ======================== 2 tests collected in 0.05s =========================
    """
    res = parse_collection_output(dup_output)
    assert len(res["duplicates"]) == 1
    assert "test_auth_service.py::test_login_flow" in res["duplicates"][0]
    # Duplicates are not counted twice
    assert res["counts"]["test_auth_service.py"] == 1
    assert res["parsed_total"] == 1


def test_parse_detects_malformed_item_before_module() -> None:
    """Verify test items encountered before any module line generate errors."""
    malformed_output = """
    <Coroutine orphan_test>
    <Module test_sample.py>
      <Coroutine sample_test>
    ======================== 2 tests collected in 0.05s =========================
    """
    res = parse_collection_output(malformed_output)
    assert len(res["errors"]) == 1
    assert "Test item found before any module declaration" in res["errors"][0]


def test_parse_missing_summary() -> None:
    """Verify output without a summary line reports summary_collected as None."""
    no_summary = """
    <Module test_sample.py>
      <Coroutine sample_test>
    """
    res = parse_collection_output(no_summary)
    assert res["summary_collected"] is None
    assert res["parsed_total"] == 1


def test_reconcile_census_valid() -> None:
    """Verify reconciliation succeeds with valid counts and all PostgreSQL suites."""
    parsed = parse_collection_output(SAMPLE_VALID_TREE_OUTPUT)
    rec = reconcile_census(parsed["counts"], parsed["summary_collected"])
    assert rec["arithmetic_valid"] is True
    assert rec["grand_total"] == 12
    assert rec["total_files"] == 10
    assert rec["pg_total"] == 7
    assert rec["pg_files"] == 6
    assert rec["unit_total"] == 5
    assert rec["unit_files"] == 4
    assert rec["errors"] == []


def test_reconcile_census_mismatched_summary() -> None:
    """Verify reconciliation fails when parsed count does not equal pytest summary."""
    parsed = parse_collection_output(SAMPLE_VALID_TREE_OUTPUT)
    # Tamper with summary to simulate collection truncation
    rec = reconcile_census(parsed["counts"], summary_collected=999)
    assert rec["arithmetic_valid"] is False
    assert any("does not match pytest summary" in err for err in rec["errors"])


def test_reconcile_census_missing_postgresql_suite() -> None:
    """Verify reconciliation fails closed if any of the 6 canonical PG suites is missing."""
    parsed = parse_collection_output(SAMPLE_VALID_TREE_OUTPUT)
    tampered_counts = dict(parsed["counts"])
    del tampered_counts["test_sa02_technical_operations_portal.py"]

    rec = reconcile_census(tampered_counts, summary_collected=11)
    assert rec["arithmetic_valid"] is False
    assert any("Missing required PostgreSQL integration suites" in err for err in rec["errors"])


def test_reconcile_census_empty_counts() -> None:
    """Verify reconciliation fails closed on empty collection."""
    rec = reconcile_census({}, summary_collected=0)
    assert rec["arithmetic_valid"] is False
    assert any("No modules or tests parsed" in err for err in rec["errors"])


def test_analyze_handles_subprocess_nonzero_exit() -> None:
    """Verify analyze() exits with nonzero code when pytest fails."""
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "Collection error in test_broken.py"
    mock_proc.stdout = ""

    with patch("subprocess.run", return_value=mock_proc):
        exit_code = analyze(Path(__file__).parent.parent)
        assert exit_code == 1


def test_analyze_handles_subprocess_timeout() -> None:
    """Verify analyze() exits with code 6 when pytest collection times out."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["pytest"], timeout=45)):
        exit_code = analyze(Path(__file__).parent.parent)
        assert exit_code == 6


def test_analyze_handles_duplicate_tests() -> None:
    """Verify analyze() detects duplicates and exits with code 4."""
    dup_stdout = """
    <Module test_dup.py>
      <Coroutine test_sample>
      <Coroutine test_sample>
    ======================== 2 tests collected in 0.05s =========================
    """
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = dup_stdout
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        exit_code = analyze(Path(__file__).parent.parent)
        assert exit_code == 4
