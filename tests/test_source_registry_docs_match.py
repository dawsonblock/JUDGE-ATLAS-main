"""Verify that status docs report source counts consistent with source_registry_status.json.

Detects the common drift where docs are edited by hand and diverge from
the machine-readable registry.  The canonical source of truth is always
artifacts/proof/current/source_registry_status.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "proof"
    / "current"
    / "source_registry_status.json"
)

REPO_ROOT = Path(__file__).resolve().parents[1]

STATUS_DOCS = [
    REPO_ROOT / "STATUS.md",
    REPO_ROOT / "CURRENT_STATUS.md",
    REPO_ROOT / "REPAIR_STATUS.md",
    REPO_ROOT / "PROOF_STATUS.md",
    REPO_ROOT / "RELEASE_BLOCKERS.md",
    REPO_ROOT / "STUBS_AND_PLACEHOLDERS.md",
]

# Phrases that encode the wrong runnable count and must never appear.
# The format is (phrase_text, reason).
FORBIDDEN_STALE_PHRASES = [
    ("2/26 runnable", "stale runnable count (registry now shows 7)"),
    ("2 actively runnable", "stale runnable count (registry now shows 7)"),
    ("5 enable-ready", "stale enable-ready count (registry now shows 0)"),
    ("5 enable-ready sources", "stale enable-ready count (registry now shows 0)"),
]


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.exists(), (
        f"source_registry_status.json not found at {REGISTRY_PATH}. "
        "Run `make proof` to regenerate."
    )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class TestStatusDocsMatchRegistry:
    def test_no_stale_runnable_count_phrases(self):
        """Status docs must not contain known-stale count phrases."""
        errors = []
        for doc_path in STATUS_DOCS:
            if not doc_path.exists():
                continue
            text = doc_path.read_text(encoding="utf-8").lower()
            for phrase, reason in FORBIDDEN_STALE_PHRASES:
                if phrase.lower() in text:
                    errors.append(
                        f"{doc_path.name}: contains stale phrase {phrase!r} — {reason}"
                    )
        assert not errors, (
            "Status docs contain stale source count phrases:\n"
            + "\n".join(errors)
        )

    def test_ingestion_coverage_line_uses_correct_count(self, registry):
        """ingestion_coverage lines in status docs must use the current runnable count."""
        actual_runnable = registry["summary"]["runnable_now"]
        pattern = re.compile(
            r"ingestion_coverage\s*:\s*(\d+)/\d+\s+runnable", re.IGNORECASE
        )
        errors = []
        for doc_path in STATUS_DOCS:
            if not doc_path.exists():
                continue
            text = doc_path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                doc_count = int(match.group(1))
                if doc_count != actual_runnable:
                    errors.append(
                        f"{doc_path.name}: ingestion_coverage shows {doc_count}/N "
                        f"but registry.runnable_now={actual_runnable}"
                    )
        assert not errors, (
            "Status docs have wrong runnable count in ingestion_coverage:\n"
            + "\n".join(errors)
        )

    def test_status_docs_reference_registry_as_authority(self):
        """Key status docs must reference source_registry_status.json or release_gate.json."""
        authority_markers = [
            "release_gate.json",
            "source_registry_status.json",
            "artifacts/proof/current",
        ]
        errors = []
        for doc_path in STATUS_DOCS[:5]:  # First 5 are the primary status docs
            if not doc_path.exists():
                errors.append(f"{doc_path.name}: file not found")
                continue
            text = doc_path.read_text(encoding="utf-8")
            if not any(m in text for m in authority_markers):
                errors.append(
                    f"{doc_path.name}: does not reference canonical authority "
                    "(release_gate.json, source_registry_status.json, or "
                    "artifacts/proof/current)"
                )
        assert not errors, "\n".join(errors)
