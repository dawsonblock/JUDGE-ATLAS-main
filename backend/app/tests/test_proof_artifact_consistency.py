"""
Proof artifact consistency test.

Validates that release_gate.json, proof_manifest.json, and all required
proof artifacts are consistent and complete.
"""

import json
import os
import pytest
from pathlib import Path


@pytest.fixture
def proof_dir():
    """Get proof directory from environment or use default."""
    return os.getenv("PROOF_DIR", "artifacts/proof/current")


def test_proof_manifest_exists(proof_dir):
    """proof_manifest.json must exist."""
    manifest_path = os.path.join(proof_dir, "proof_manifest.json")
    assert os.path.exists(manifest_path), f"proof_manifest.json not found at {manifest_path}"


def test_release_gate_exists(proof_dir):
    """release_gate.json must exist."""
    gate_path = os.path.join(proof_dir, "release_gate.json")
    assert os.path.exists(gate_path), f"release_gate.json not found at {gate_path}"


def test_release_gate_not_overclaiming(proof_dir):
    """
    release_gate.json must not claim production_ready=true or
    public_release_safe=true for alpha.
    """
    gate_path = os.path.join(proof_dir, "release_gate.json")
    with open(gate_path, "r") as f:
        gate = json.load(f)

    assert gate.get("production_ready", False) is False, \
        "release_gate claims production_ready=true but this is alpha"
    assert gate.get("public_release_safe", False) is False, \
        "release_gate claims public_release_safe=true but this is alpha"


def test_proof_manifest_and_gate_agree_on_build_id(proof_dir):
    """build_id must match between manifest and gate."""
    manifest_path = os.path.join(proof_dir, "proof_manifest.json")
    gate_path = os.path.join(proof_dir, "release_gate.json")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    with open(gate_path, "r") as f:
        gate = json.load(f)

    manifest_id = manifest.get("build_id")
    gate_id = gate.get("build_id")

    assert manifest_id is not None, "manifest missing build_id"
    assert gate_id is not None, "gate missing build_id"
    assert manifest_id == gate_id, f"build_id mismatch: {manifest_id} vs {gate_id}"


def test_proof_manifest_and_gate_agree_on_timestamp(proof_dir):
    """timestamps must be close (within 5 minutes)."""
    manifest_path = os.path.join(proof_dir, "proof_manifest.json")
    gate_path = os.path.join(proof_dir, "release_gate.json")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    with open(gate_path, "r") as f:
        gate = json.load(f)

    manifest_ts = manifest.get("timestamp")
    gate_ts = gate.get("timestamp")

    if manifest_ts and gate_ts:
        from datetime import datetime
        m_dt = datetime.fromisoformat(manifest_ts.replace('Z', '+00:00'))
        g_dt = datetime.fromisoformat(gate_ts.replace('Z', '+00:00'))
        time_diff = abs((m_dt - g_dt).total_seconds())
        assert time_diff < 300, f"timestamp skew: {time_diff}s"


def test_required_logs_exist(proof_dir):
    """All required logs listed in proof_manifest must exist."""
    manifest_path = os.path.join(proof_dir, "proof_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    required_logs = manifest.get("required_logs", [])
    missing = []

    for log_path in required_logs:
        log_name = os.path.basename(log_path)
        full_path = os.path.join(proof_dir, log_name)
        if not os.path.exists(full_path):
            missing.append(log_path)

    assert not missing, f"Missing required logs: {missing}"


def test_required_summaries_exist(proof_dir):
    """All required summaries listed in proof_manifest must exist."""
    manifest_path = os.path.join(proof_dir, "proof_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    required_summaries = manifest.get("required_summaries", [])
    missing = []

    for summary_path in required_summaries:
        summary_name = os.path.basename(summary_path)
        full_path = os.path.join(proof_dir, summary_name)
        if not os.path.exists(full_path):
            missing.append(summary_path)

    assert not missing, f"Missing required summaries: {missing}"


def test_backend_proof_summary_exists(proof_dir):
    """backend_proof_summary.json must exist."""
    path = os.path.join(proof_dir, "backend_proof_summary.json")
    assert os.path.exists(path), f"backend_proof_summary.json not found"


def test_frontend_proof_summary_exists(proof_dir):
    """frontend_proof_summary.json must exist."""
    path = os.path.join(proof_dir, "frontend_proof_summary.json")
    assert os.path.exists(path), f"frontend_proof_summary.json not found"


def test_backend_pytest_xml_exists(proof_dir):
    """backend_pytest.xml must exist."""
    path = os.path.join(proof_dir, "backend_pytest.xml")
    assert os.path.exists(path), f"backend_pytest.xml not found"


def test_test_count_reconciliation_exists(proof_dir):
    """test_count_reconciliation.json must exist."""
    path = os.path.join(proof_dir, "test_count_reconciliation.json")
    assert os.path.exists(path), f"test_count_reconciliation.json not found"

    with open(path, "r") as f:
        reconciliation = json.load(f)

    assert reconciliation.get("consistent", False) is True, \
        "test counts are not reconcilable"


def test_no_stack_traces_in_summaries(proof_dir):
    """
    Proof summaries must not contain Python stack traces.
    If a proof artifact contains stack traces, the build failed silently.
    """
    for summary_file in ["backend_proof_summary.json", "frontend_proof_summary.json"]:
        path = os.path.join(proof_dir, summary_file)
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
                assert "Traceback" not in content, \
                    f"{summary_file} contains stack trace"
                assert "File \"" not in content or "line" not in content, \
                    f"{summary_file} may contain stack trace"
