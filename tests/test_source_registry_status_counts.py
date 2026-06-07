"""Verify that source_registry_status.json summary counts are internally consistent
and match expected values for this alpha release.

These counts are the ground truth — status docs must derive from them,
not the other way around.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "proof"
    / "current"
    / "source_registry_status.json"
)

# Minimum acceptable runnable count for alpha gate.
# Update when new sources become runnable.
MIN_RUNNABLE_NOW = 8

# Maximum enable-ready for current state (3 crawlee sources ready but disabled).
MAX_ENABLE_READY = 3


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.exists(), (
        f"source_registry_status.json not found at {REGISTRY_PATH}. "
        "Run `make proof` to regenerate."
    )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class TestSourceRegistryCounts:
    def test_runnable_now_meets_minimum(self, registry):
        actual = registry["summary"]["runnable_now"]
        assert actual >= MIN_RUNNABLE_NOW, (
            f"runnable_now={actual} is below the required minimum {MIN_RUNNABLE_NOW}. "
            "Update the registry or raise MIN_RUNNABLE_NOW when new sources are promoted."
        )

    def test_enable_ready_matches_expectation(self, registry):
        actual = registry["summary"]["enable_ready"]
        assert actual <= MAX_ENABLE_READY, (
            f"enable_ready={actual} exceeds MAX_ENABLE_READY={MAX_ENABLE_READY}. "
            "If sources were promoted to enable_ready, update MAX_ENABLE_READY "
            "and the corresponding status docs."
        )

    def test_summary_runnable_matches_per_source_count(self, registry):
        """summary.runnable_now must equal the count of sources with runnable_now=true."""
        per_source = sum(
            1 for s in registry["sources"] if s.get("runnable_now") is True
        )
        summary = registry["summary"]["runnable_now"]
        assert per_source == summary, (
            f"summary.runnable_now={summary} but {per_source} sources have "
            "runnable_now=true in the per-source list."
        )

    def test_total_sources_is_27(self, registry):
        """Total registered sources must be 27 for current alpha."""
        assert registry["total_sources"] == 27, (
            f"Expected 27 registered sources, got {registry['total_sources']}. "
            "If sources were added/removed, update this test and all status docs."
        )

    def test_machine_ingest_sources_count(self, registry):
        """machine_ingest_sources must match per-source count."""
        per_source = sum(
            1 for s in registry["sources"]
            if s.get("source_class") == "machine_ingest"
        )
        summary = registry["summary"]["machine_ingest_sources"]
        assert per_source == summary, (
            f"summary.machine_ingest_sources={summary} but {per_source} sources "
            "have source_class='machine_ingest' in the per-source list."
        )

    def test_deprecated_count_matches_per_source(self, registry):
        per_source = sum(
            1 for s in registry["sources"]
            if s.get("lifecycle_state") == "deprecated"
        )
        summary = registry["summary"]["deprecated"]
        assert per_source == summary, (
            f"summary.deprecated={summary} but {per_source} sources "
            "have lifecycle_state='deprecated'."
        )
