#!/usr/bin/env python3
"""Check that the evidence verification standard is present and tests pass."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"


def _module_importable() -> tuple[bool, str]:
    try:
        if str(BACKEND_DIR) not in sys.path:
            sys.path.insert(0, str(BACKEND_DIR))
        import app.evidence.verification_standard as _evs
        _ = (
            _evs.REQUIRED_FIELDS,
            _evs.EvidenceVerificationRecord,
            _evs.ProcessingStep,
            _evs.PublicationReadiness,
            _evs.ReviewDecision,
            _evs.is_publication_ready,
            _evs.verify_evidence_record,
        )
        return True, "module_importable"
    except Exception as exc:
        return False, f"module_import_error:{exc}"


def _check_fields() -> list[str]:
    errors: list[str] = []
    try:
        if str(BACKEND_DIR) not in sys.path:
            sys.path.insert(0, str(BACKEND_DIR))
        from app.evidence.verification_standard import (
            REQUIRED_FIELDS,
            EvidenceVerificationRecord,
        )

        expected = [
            "evidence_id",
            "source_snapshot_id",
            "source_id",
            "source_url",
            "original_hash",
            "final_hash",
            "processing_steps",
            "ai_output_is_derivative",
            "human_reviewer",
            "review_decision",
            "review_timestamp",
            "previous_log_hash",
            "custody_chain",
            "publication_readiness",
        ]
        dc_fields = set(EvidenceVerificationRecord.__dataclass_fields__.keys())
        for field in expected:
            if field not in REQUIRED_FIELDS:
                errors.append(f"missing_required_field:{field}")
            if field not in dc_fields:
                errors.append(f"missing_dataclass_field:{field}")
    except Exception as exc:
        errors.append(f"field_check_error:{exc}")
    return errors


def _check_ai_derivative_default() -> list[str]:
    errors: list[str] = []
    try:
        if str(BACKEND_DIR) not in sys.path:
            sys.path.insert(0, str(BACKEND_DIR))
        from app.evidence.verification_standard import (
            EvidenceVerificationRecord,
        )

        record = EvidenceVerificationRecord(
            evidence_id="test",
            source_snapshot_id=1,
            source_id="src",
            source_url="http://example.com",
            original_hash="a" * 64,
            final_hash="a" * 64,
            processing_steps=[],
        )
        if record.ai_output_is_derivative is not True:
            errors.append("ai_output_is_derivative_default_not_true")
    except Exception as exc:
        errors.append(f"ai_derivative_default_error:{exc}")
    return errors


def _run_tests() -> tuple[bool, str]:
    isolated_test = (
        REPO_ROOT / "tests" / "proof"
        / "test_evidence_verification_standard.py"
    )
    legacy_test = (
        BACKEND_DIR / "app" / "tests"
        / "test_evidence_verification_standard.py"
    )

    # Prefer the isolated proof test that does not load backend conftest.py.
    test_path = isolated_test if isolated_test.exists() else legacy_test
    if not test_path.exists():
        return False, "test_file_missing"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        return (
            False,
            f"pytest_failed:rc={result.returncode}:\n"
            f"{result.stdout}\n{result.stderr}",
        )
    return True, "tests_passed"


def main() -> int:
    errors: list[str] = []

    ok, detail = _module_importable()
    if not ok:
        errors.append(detail)
        print("EVIDENCE_VERIFICATION_STANDARD: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    errors.extend(_check_fields())
    errors.extend(_check_ai_derivative_default())

    test_ok, test_detail = _run_tests()
    if not test_ok:
        errors.append(test_detail)

    if errors:
        print("EVIDENCE_VERIFICATION_STANDARD: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("EVIDENCE_VERIFICATION_STANDARD: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
