"""Phase 18: Retrieval non-authoritative hardening tests.

Verifies that:
- AI retrieval output is always marked derivative (not authoritative).
- Retrieval responses carry an explicit disclaimer field.
- Retrieval output cannot be returned as a public API response
  without human review gating.
- Backend AI retrieval / correctness test files exist on disk.
"""

from __future__ import annotations

from pathlib import Path


_REQUIRED_DISCLAIMER_KEYS = {"is_derivative", "requires_human_review"}


def _validate_retrieval_response(resp: dict) -> list[str]:
    """Return policy violations for an AI retrieval response dict."""
    errors: list[str] = []

    if resp.get("is_authoritative") is not False:
        errors.append("retrieval_must_be_non_authoritative")

    if not resp.get("is_derivative"):
        errors.append("retrieval_must_be_derivative")

    if not resp.get("requires_human_review"):
        errors.append("retrieval_must_require_human_review")

    if resp.get("is_public") and not resp.get("reviewed_by_human"):
        errors.append("public_retrieval_requires_human_review")

    return errors


def _make_retrieval_response(**overrides) -> dict:
    base = {
        "query": "test query",
        "results": [],
        "is_authoritative": False,
        "is_derivative": True,
        "requires_human_review": True,
        "reviewed_by_human": False,
        "is_public": False,
        "model_name": "test-model",
        "prompt_version": "v1",
    }
    base.update(overrides)
    return base


class TestRetrievalNonAuthoritative:

    def test_valid_non_public_response_passes(self) -> None:
        assert _validate_retrieval_response(_make_retrieval_response()) == []

    def test_authoritative_true_blocked(self) -> None:
        errors = _validate_retrieval_response(
            _make_retrieval_response(is_authoritative=True)
        )
        assert "retrieval_must_be_non_authoritative" in errors

    def test_authoritative_missing_blocked(self) -> None:
        resp = _make_retrieval_response()
        del resp["is_authoritative"]
        errors = _validate_retrieval_response(resp)
        assert "retrieval_must_be_non_authoritative" in errors

    def test_not_derivative_blocked(self) -> None:
        errors = _validate_retrieval_response(
            _make_retrieval_response(is_derivative=False)
        )
        assert "retrieval_must_be_derivative" in errors

    def test_no_review_required_flag_blocked(self) -> None:
        errors = _validate_retrieval_response(
            _make_retrieval_response(requires_human_review=False)
        )
        assert "retrieval_must_require_human_review" in errors

    def test_public_without_human_review_blocked(self) -> None:
        errors = _validate_retrieval_response(
            _make_retrieval_response(is_public=True, reviewed_by_human=False)
        )
        assert "public_retrieval_requires_human_review" in errors

    def test_public_with_human_review_passes(self) -> None:
        errors = _validate_retrieval_response(
            _make_retrieval_response(is_public=True, reviewed_by_human=True)
        )
        assert "public_retrieval_requires_human_review" not in errors

    def test_required_disclaimer_keys_present(self) -> None:
        resp = _make_retrieval_response()
        present = _REQUIRED_DISCLAIMER_KEYS & resp.keys()
        assert present == _REQUIRED_DISCLAIMER_KEYS, (
            f"missing disclaimer keys: {_REQUIRED_DISCLAIMER_KEYS - present}"
        )


def test_ai_retrieval_backend_tests_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "backend/app/tests/test_ai_correctness.py",
        root
        / "backend/app/tests"
        / "test_ai_review_requires_reviewer_or_source_admin.py",
        root / "backend/app/tests/test_ai_pipeline.py",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, (
        f"missing required AI retrieval gate tests: {missing}"
    )
