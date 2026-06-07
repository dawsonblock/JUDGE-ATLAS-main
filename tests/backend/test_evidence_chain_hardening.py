"""Phase 16: Evidence chain hardening tests.

Verifies that:
- ai_output_is_derivative is required and must be True for any
  AI-processed evidence.
- publication_readiness=ready requires review_decision=approved
  and a custody chain.
- original_hash and final_hash must each be exactly 64 hex characters.
- Approved review requires human_reviewer and review_timestamp.
- Evidence verification standard script and test exist on disk.
"""

from __future__ import annotations

import re
from pathlib import Path


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _valid_hash(value: str) -> bool:
    return bool(_HASH_RE.match(str(value)))


def _make_evidence_record(**overrides) -> dict:
    base = {
        "evidence_id": "ev-001",
        "source_snapshot_id": 1,
        "source_id": "justice_canada_laws_xml",
        "source_url": "https://laws.justice.gc.ca/test",
        "original_hash": "a" * 64,
        "final_hash": "a" * 64,
        "processing_steps": [],
        "ai_output_is_derivative": True,
        "human_reviewer": "reviewer@example.com",
        "review_decision": "approved",
        "review_timestamp": "2026-01-01T00:00:00Z",
        "previous_log_hash": None,
        "custody_chain": [{"event": "ingested", "at": "2026-01-01T00:00:00Z"}],
        "publication_readiness": "ready",
    }
    base.update(overrides)
    return base


def _validate(record: dict) -> list[str]:
    errors: list[str] = []
    if not record.get("evidence_id"):
        errors.append("evidence_id_missing")
    snap_id = record.get("source_snapshot_id")
    if not isinstance(snap_id, int) or snap_id <= 0:
        errors.append("source_snapshot_id_invalid")
    if not _valid_hash(record.get("original_hash", "")):
        errors.append("original_hash_invalid")
    if not _valid_hash(record.get("final_hash", "")):
        errors.append("final_hash_invalid")
    if record.get("ai_output_is_derivative") is not True:
        errors.append("ai_output_is_derivative_must_be_true")
    if record.get("review_decision") == "approved":
        if not record.get("human_reviewer"):
            errors.append("approved_missing_human_reviewer")
        if not record.get("review_timestamp"):
            errors.append("approved_missing_review_timestamp")
    if record.get("publication_readiness") == "ready":
        if record.get("review_decision") != "approved":
            errors.append("ready_requires_approved_decision")
        if not record.get("custody_chain"):
            errors.append("ready_requires_custody_chain")
        if record.get("original_hash") != record.get("final_hash"):
            if not record.get("processing_steps"):
                errors.append("hash_mismatch_requires_processing_steps")
    return errors


class TestEvidenceChainHardening:

    def test_valid_record_passes(self) -> None:
        assert _validate(_make_evidence_record()) == []

    def test_ai_output_is_derivative_false_blocked(self) -> None:
        errors = _validate(_make_evidence_record(ai_output_is_derivative=False))
        assert "ai_output_is_derivative_must_be_true" in errors

    def test_ai_output_is_derivative_missing_blocked(self) -> None:
        rec = _make_evidence_record()
        del rec["ai_output_is_derivative"]
        errors = _validate(rec)
        assert "ai_output_is_derivative_must_be_true" in errors

    def test_original_hash_short_blocked(self) -> None:
        errors = _validate(_make_evidence_record(original_hash="abc123"))
        assert "original_hash_invalid" in errors

    def test_final_hash_non_hex_blocked(self) -> None:
        errors = _validate(_make_evidence_record(final_hash="z" * 64))
        assert "final_hash_invalid" in errors

    def test_approved_without_reviewer_blocked(self) -> None:
        errors = _validate(_make_evidence_record(human_reviewer=None))
        assert "approved_missing_human_reviewer" in errors

    def test_approved_without_timestamp_blocked(self) -> None:
        errors = _validate(_make_evidence_record(review_timestamp=None))
        assert "approved_missing_review_timestamp" in errors

    def test_ready_without_approved_decision_blocked(self) -> None:
        errors = _validate(
            _make_evidence_record(
                review_decision="pending",
                human_reviewer=None,
                review_timestamp=None,
            )
        )
        assert "ready_requires_approved_decision" in errors

    def test_ready_without_custody_chain_blocked(self) -> None:
        errors = _validate(_make_evidence_record(custody_chain=[]))
        assert "ready_requires_custody_chain" in errors

    def test_hash_mismatch_requires_processing_steps(self) -> None:
        errors = _validate(
            _make_evidence_record(
                original_hash="a" * 64,
                final_hash="b" * 64,
                processing_steps=[],
            )
        )
        assert "hash_mismatch_requires_processing_steps" in errors

    def test_hash_mismatch_with_steps_passes(self) -> None:
        step = {"name": "normalize", "timestamp": "2026-01-01T00:00:00Z"}
        errors = _validate(
            _make_evidence_record(
                original_hash="a" * 64,
                final_hash="b" * 64,
                processing_steps=[step],
            )
        )
        assert "hash_mismatch_requires_processing_steps" not in errors


def test_evidence_verification_scripts_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "scripts/check_evidence_verification_standard.py",
        root / "tests/proof/test_evidence_verification_standard.py",
        root / "docs/compliance/Evidence_Verification_Standard.md",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, f"missing required evidence chain artifacts: {missing}"
