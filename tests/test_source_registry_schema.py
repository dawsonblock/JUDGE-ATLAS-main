"""Verify that source_registry_status.json conforms to required schema.

This test runs against the proof artifact on disk and does NOT require a
live database or running backend.
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

REQUIRED_TOP_LEVEL_KEYS = {
    "generated_at_utc",
    "total_sources",
    "summary",
    "sources",
}

REQUIRED_SUMMARY_KEYS = {
    "total_sources",
    "machine_ingest_sources",
    "runnable_now",
    "enable_ready",
    "deprecated",
}

REQUIRED_SOURCE_KEYS = {
    "source_key",
    "source_name",
    "jurisdiction",
    "source_class",
    "source_type",
    "lifecycle_state",
    "runnable_now",
}


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.exists(), (
        f"source_registry_status.json not found at {REGISTRY_PATH}. "
        "Run `make proof` to regenerate."
    )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class TestSourceRegistryTopLevel:
    def test_required_top_level_keys_present(self, registry):
        missing = REQUIRED_TOP_LEVEL_KEYS - registry.keys()
        assert not missing, f"Missing top-level keys: {missing}"

    def test_sources_is_a_list(self, registry):
        assert isinstance(registry["sources"], list)

    def test_sources_list_not_empty(self, registry):
        assert len(registry["sources"]) > 0

    def test_total_sources_matches_list_length(self, registry):
        assert registry["total_sources"] == len(registry["sources"]), (
            f"total_sources={registry['total_sources']} but "
            f"len(sources)={len(registry['sources'])}"
        )

    def test_summary_total_matches_list_length(self, registry):
        assert registry["summary"]["total_sources"] == len(registry["sources"])


class TestSourceRegistrySummary:
    def test_required_summary_keys_present(self, registry):
        missing = REQUIRED_SUMMARY_KEYS - registry["summary"].keys()
        assert not missing, f"Missing summary keys: {missing}"

    def test_runnable_now_is_non_negative_int(self, registry):
        val = registry["summary"]["runnable_now"]
        assert isinstance(val, int) and val >= 0

    def test_enable_ready_is_non_negative_int(self, registry):
        val = registry["summary"]["enable_ready"]
        assert isinstance(val, int) and val >= 0

    def test_deprecated_is_non_negative_int(self, registry):
        val = registry["summary"]["deprecated"]
        assert isinstance(val, int) and val >= 0

    def test_summary_counts_are_consistent(self, registry):
        sources = registry["sources"]
        actual_runnable = sum(1 for s in sources if s.get("runnable_now") is True)
        assert registry["summary"]["runnable_now"] == actual_runnable, (
            f"summary.runnable_now={registry['summary']['runnable_now']} "
            f"but {actual_runnable} sources have runnable_now=true"
        )


class TestSourceRegistryPerSource:
    def test_each_source_has_required_keys(self, registry):
        errors = []
        for src in registry["sources"]:
            missing = REQUIRED_SOURCE_KEYS - src.keys()
            if missing:
                errors.append(
                    f"source '{src.get('source_key', '?')}' missing: {missing}"
                )
        assert not errors, "\n".join(errors)

    def test_source_keys_are_unique(self, registry):
        keys = [s["source_key"] for s in registry["sources"]]
        duplicates = {k for k in keys if keys.count(k) > 1}
        assert not duplicates, f"Duplicate source_key entries: {duplicates}"

    def test_lifecycle_state_values_are_known(self, registry):
        known_states = {
            "runnable",
            "runnable_disabled",
            "disabled_stub",
            "portal_reference",
            "manual_reference",
            "manual_upload",
            "deprecated",
            "enable_ready",
        }
        errors = []
        for src in registry["sources"]:
            state = src.get("lifecycle_state", "")
            if state not in known_states:
                errors.append(
                    f"source '{src['source_key']}' has unknown lifecycle_state: {state!r}"
                )
        assert not errors, "\n".join(errors)

    def test_runnable_now_is_boolean(self, registry):
        errors = []
        for src in registry["sources"]:
            val = src.get("runnable_now")
            if not isinstance(val, bool):
                errors.append(
                    f"source '{src['source_key']}': runnable_now={val!r} (expected bool)"
                )
        assert not errors, "\n".join(errors)
