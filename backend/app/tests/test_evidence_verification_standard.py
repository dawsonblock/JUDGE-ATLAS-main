"""Tests for backend/app/evidence/verification_standard.py.

Covers:
- EvidenceVerificationRecord field presence and defaults
- verify_evidence_record: pass, fail per field
- is_publication_ready: only when all checks pass and readiness=ready
- ai_output_is_derivative must be True
- approved review requires human_reviewer and review_timestamp
- publication readiness gated on approved review and custody_chain
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.evidence.verification_standard import (
    EvidenceVerificationRecord,
    ProcessingStep,
    PublicationReadiness,
    ReviewDecision,
    is_publication_ready,
    verify_evidence_record,
)


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_record(**overrides) -> EvidenceVerificationRecord:
    defaults = {
        "evidence_id": "ev-001",
        "source_snapshot_id": 1,
        "source_id": "justice_canada_laws_xml",
        "source_url": "https://laws-lois.justice.gc.ca/",
        "original_hash": "a" * 64,
        "final_hash": "a" * 64,
        "processing_steps": [ProcessingStep(name="ingest")],
        "ai_output_is_derivative": True,
        "human_reviewer": None,
        "review_decision": ReviewDecision.pending,
        "review_timestamp": None,
        "previous_log_hash": None,
        "custody_chain": [],
        "publication_readiness": PublicationReadiness.needs_review,
    }
    defaults.update(overrides)
    return EvidenceVerificationRecord(**defaults)


class TestVerifyEvidenceRecord:
    def test_minimal_valid_record_passes(self):
        record = _make_record()
        errors = verify_evidence_record(record)
        assert errors == []

    def test_missing_evidence_id(self):
        record = _make_record(evidence_id="")
        errors = verify_evidence_record(record)
        assert any("evidence_id" in e for e in errors)

    def test_invalid_source_snapshot_id(self):
        record = _make_record(source_snapshot_id=0)
        errors = verify_evidence_record(record)
        assert any("source_snapshot_id" in e for e in errors)

    def test_missing_source_id(self):
        record = _make_record(source_id="")
        errors = verify_evidence_record(record)
        assert any("source_id" in e for e in errors)

    def test_missing_source_url(self):
        record = _make_record(source_url="")
        errors = verify_evidence_record(record)
        assert any("source_url" in e for e in errors)

    def test_short_original_hash(self):
        record = _make_record(original_hash="abc")
        errors = verify_evidence_record(record)
        assert any("original_hash" in e for e in errors)

    def test_short_final_hash(self):
        record = _make_record(final_hash="abc")
        errors = verify_evidence_record(record)
        assert any("final_hash" in e for e in errors)

    def test_processing_steps_must_be_list(self):
        record = _make_record(processing_steps="not-a-list")
        errors = verify_evidence_record(record)
        assert any("processing_steps must be a list" in e for e in errors)

    def test_processing_step_must_have_name(self):
        record = _make_record(processing_steps=[ProcessingStep(name="")])
        errors = verify_evidence_record(record)
        assert any("name must not be empty" in e for e in errors)

    def test_ai_output_is_derivative_must_be_true(self):
        record = _make_record(ai_output_is_derivative=False)
        errors = verify_evidence_record(record)
        assert any("ai_output_is_derivative" in e for e in errors)

    def test_approved_review_requires_human_reviewer(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            review_timestamp=_NOW,
        )
        errors = verify_evidence_record(record)
        assert any("human_reviewer" in e for e in errors)

    def test_approved_review_requires_review_timestamp(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            human_reviewer="alice",
        )
        errors = verify_evidence_record(record)
        assert any("review_timestamp" in e for e in errors)

    def test_ready_without_approved_review_blocked(self):
        record = _make_record(
            publication_readiness=PublicationReadiness.ready,
            custody_chain=[{"stage": "reviewed"}],
        )
        errors = verify_evidence_record(record)
        assert any(
            "publication_readiness cannot be ready" in e for e in errors
        )

    def test_ready_without_custody_chain_blocked(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            human_reviewer="alice",
            review_timestamp=_NOW,
            publication_readiness=PublicationReadiness.ready,
            custody_chain=[],
        )
        errors = verify_evidence_record(record)
        assert any("custody_chain must not be empty" in e for e in errors)

    def test_ready_with_hash_change_needs_processing_steps(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            human_reviewer="alice",
            review_timestamp=_NOW,
            original_hash="a" * 64,
            final_hash="b" * 64,
            processing_steps=[],
            publication_readiness=PublicationReadiness.ready,
            custody_chain=[{"stage": "reviewed"}],
        )
        errors = verify_evidence_record(record)
        assert any(
            "processing_steps must document hash change" in e for e in errors
        )

    def test_full_ready_record_passes(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            human_reviewer="alice",
            review_timestamp=_NOW,
            publication_readiness=PublicationReadiness.ready,
            custody_chain=[{"stage": "reviewed", "actor": "alice"}],
        )
        errors = verify_evidence_record(record)
        assert errors == []


class TestIsPublicationReady:
    def test_not_ready_when_pending(self):
        record = _make_record()
        assert is_publication_ready(record) is False

    def test_not_ready_when_blocked(self):
        record = _make_record(
            publication_readiness=PublicationReadiness.blocked,
        )
        assert is_publication_ready(record) is False

    def test_ready_when_all_checks_pass(self):
        record = _make_record(
            review_decision=ReviewDecision.approved,
            human_reviewer="alice",
            review_timestamp=_NOW,
            publication_readiness=PublicationReadiness.ready,
            custody_chain=[{"stage": "reviewed"}],
        )
        assert is_publication_ready(record) is True

    def test_not_ready_when_validation_fails(self):
        record = _make_record(
            evidence_id="",
            publication_readiness=PublicationReadiness.ready,
        )
        assert is_publication_ready(record) is False


class TestRequiredFields:
    def test_all_required_fields_exist(self):
        from app.evidence.verification_standard import REQUIRED_FIELDS

        record = _make_record()
        for field in REQUIRED_FIELDS:
            assert hasattr(record, field), f"missing field: {field}"
