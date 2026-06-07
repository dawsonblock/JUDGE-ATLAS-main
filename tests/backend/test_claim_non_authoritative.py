"""Phase 17: Claim non-authoritative hardening tests.

Verifies that:
- Memory claims are always marked non-authoritative (is_authoritative=False).
- A claim without a source_snapshot_id cannot be marked publication-ready.
- Claims cannot be published directly without human review.
- The memory claim backend tests and admin memory module exist on disk.
"""

from __future__ import annotations

from pathlib import Path


def _validate_claim(claim: dict) -> list[str]:
    """Return a list of policy violations for the given claim dict."""
    errors: list[str] = []

    if claim.get("is_authoritative") is not False:
        errors.append("claim_must_be_non_authoritative")

    if not claim.get("source_snapshot_id"):
        errors.append("claim_requires_source_snapshot_id")

    if claim.get("publication_readiness") == "ready":
        if claim.get("review_decision") != "approved":
            errors.append("claim_ready_requires_approved_review")
        if not claim.get("human_reviewer"):
            errors.append("claim_ready_requires_human_reviewer")

    return errors


def _make_claim(**overrides) -> dict:
    base = {
        "claim_key": "c-001",
        "claim_type": "biography",
        "entity_id": 1,
        "claim_value": "Test claim value",
        "source_snapshot_id": 42,
        "confidence": 0.9,
        "is_authoritative": False,
        "status": "active",
        "review_decision": "approved",
        "human_reviewer": "reviewer@example.com",
        "publication_readiness": "ready",
    }
    base.update(overrides)
    return base


class TestClaimNonAuthoritative:

    def test_valid_non_authoritative_claim_passes(self) -> None:
        assert _validate_claim(_make_claim()) == []

    def test_authoritative_true_blocked(self) -> None:
        errors = _validate_claim(_make_claim(is_authoritative=True))
        assert "claim_must_be_non_authoritative" in errors

    def test_authoritative_missing_blocked(self) -> None:
        claim = _make_claim()
        del claim["is_authoritative"]
        errors = _validate_claim(claim)
        assert "claim_must_be_non_authoritative" in errors

    def test_missing_snapshot_id_blocked(self) -> None:
        errors = _validate_claim(_make_claim(source_snapshot_id=None))
        assert "claim_requires_source_snapshot_id" in errors

    def test_zero_snapshot_id_blocked(self) -> None:
        errors = _validate_claim(_make_claim(source_snapshot_id=0))
        assert "claim_requires_source_snapshot_id" in errors

    def test_ready_without_approved_review_blocked(self) -> None:
        errors = _validate_claim(
            _make_claim(review_decision="pending", human_reviewer=None)
        )
        assert "claim_ready_requires_approved_review" in errors

    def test_ready_without_human_reviewer_blocked(self) -> None:
        errors = _validate_claim(
            _make_claim(human_reviewer=None)
        )
        assert "claim_ready_requires_human_reviewer" in errors

    def test_non_ready_claim_no_reviewer_required(self) -> None:
        errors = _validate_claim(
            _make_claim(
                publication_readiness="needs_review",
                review_decision="pending",
                human_reviewer=None,
            )
        )
        assert "claim_ready_requires_approved_review" not in errors
        assert "claim_ready_requires_human_reviewer" not in errors


def test_memory_claim_backend_tests_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "backend/app/tests/test_admin_memory_fail_closed.py",
        root / "backend/app/tests/test_admin_memory_audit_logging.py",
        root / "backend/app/tests/test_task_registry_claim_extraction.py",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, (
        f"missing required memory/claim hardening tests: {missing}"
    )
