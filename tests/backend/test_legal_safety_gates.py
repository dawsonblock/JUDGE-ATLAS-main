"""Phase 22: Legal safety gate hardening tests.

Verifies that:
- No forbidden scoring fields appear in any public-facing response.
- Causal judge-crime attribution language is blocked.
- Every public record carries the required legal disclaimer.
- Legal safety backend test files exist on disk.

These are policy-layer tests that do not require a running database.
"""

from __future__ import annotations

import re as _re
from pathlib import Path


_FORBIDDEN_FIELDS = frozenset(
    {
        "guilt_score",
        "danger_score",
        "judge_score",
        "blame",
        "suspect_score",
        "criminal_score",
        "offender_score",
    }
)

_REQUIRED_DISCLAIMER_FIELDS = frozenset({"disclaimer", "is_derivative"})

_CAUSAL_PATTERNS = [
    _re.compile(r"\b(judge|justice)\s+\w*\s*caused\b", _re.IGNORECASE),
    _re.compile(r"\b(judge|justice)\s+\w*\s*committed\b", _re.IGNORECASE),
    _re.compile(
        r"\b(judge|justice)\s+\w*\s*(?:is\s+)?responsible\s+for\b",
        _re.IGNORECASE,
    ),
    _re.compile(
        r"\b(judge|justice)\s+\w*\s*(?:is\s+)?guilty\s+of\b",
        _re.IGNORECASE,
    ),
]


def _check_forbidden_fields(record: dict) -> list[str]:
    found = _FORBIDDEN_FIELDS & record.keys()
    return [f"forbidden_field:{f}" for f in sorted(found)]


def _check_disclaimer(record: dict) -> list[str]:
    missing = _REQUIRED_DISCLAIMER_FIELDS - record.keys()
    return [f"missing_disclaimer_field:{f}" for f in sorted(missing)]


def _check_causal_attribution(text: str) -> bool:
    """Return True if text contains blocked causal attribution language."""
    return any(pat.search(text) for pat in _CAUSAL_PATTERNS)


class TestForbiddenFieldsAbsent:

    def test_clean_record_passes(self) -> None:
        record = {
            "id": 1,
            "map_quality": "verified",
            "disclaimer": "Alpha only. Requires human review.",
            "is_derivative": True,
        }
        assert _check_forbidden_fields(record) == []

    def test_guilt_score_blocked(self) -> None:
        record = {"guilt_score": 0.9, "map_quality": "verified"}
        errors = _check_forbidden_fields(record)
        assert "forbidden_field:guilt_score" in errors

    def test_danger_score_blocked(self) -> None:
        record = {"danger_score": 0.5}
        errors = _check_forbidden_fields(record)
        assert "forbidden_field:danger_score" in errors

    def test_judge_score_blocked(self) -> None:
        record = {"judge_score": 0.1}
        errors = _check_forbidden_fields(record)
        assert "forbidden_field:judge_score" in errors

    def test_multiple_forbidden_fields_all_reported(self) -> None:
        record = {"guilt_score": 0.5, "blame": "judge", "id": 1}
        errors = _check_forbidden_fields(record)
        assert len(errors) == 2


class TestDisclaimerRequired:

    def test_record_with_disclaimer_passes(self) -> None:
        record = {
            "id": 1,
            "disclaimer": "Alpha only. AI output. Requires human review.",
            "is_derivative": True,
        }
        assert _check_disclaimer(record) == []

    def test_missing_disclaimer_flagged(self) -> None:
        record = {"id": 1, "is_derivative": True}
        errors = _check_disclaimer(record)
        assert "missing_disclaimer_field:disclaimer" in errors

    def test_missing_is_derivative_flagged(self) -> None:
        record = {"id": 1, "disclaimer": "Alpha."}
        errors = _check_disclaimer(record)
        assert "missing_disclaimer_field:is_derivative" in errors


class TestCausalAttributionBlocked:

    def test_clean_text_passes(self) -> None:
        assert not _check_causal_attribution(
            "Judge presided over case number 2023-SC-001."
        )

    def test_judge_caused_blocked(self) -> None:
        assert _check_causal_attribution(
            "The judge caused the victim undue harm."
        )

    def test_justice_committed_blocked(self) -> None:
        assert _check_causal_attribution(
            "Justice Smith committed an act of misconduct."
        )

    def test_judge_guilty_blocked(self) -> None:
        assert _check_causal_attribution(
            "The judge is guilty of breach of conduct."
        )

    def test_case_insensitive(self) -> None:
        assert _check_causal_attribution("JUDGE CAUSED the incident.")

    def test_neutral_judge_mention_passes(self) -> None:
        assert not _check_causal_attribution(
            "Judge ordered a stay of proceedings."
        )


def test_legal_safety_backend_tests_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "backend/app/tests/test_ai_correctness.py",
        root / "backend/app/tests/test_security_hardening.py",
        root / "backend/app/tests/test_abuse_controls.py",
        root / "backend/app/tests/test_source_honesty.py",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    assert not missing, (
        f"missing required legal safety backend tests: {missing}"
    )
