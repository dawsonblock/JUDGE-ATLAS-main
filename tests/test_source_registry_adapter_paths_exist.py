"""Verify that adapter files referenced in source_registry_status.json exist on disk.

For every source with adapter_exists=true and a non-empty adapter_key,
the corresponding adapter module must exist in the source_adapters directory.

This test does NOT require a live database or running backend.
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

ADAPTERS_DIR = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "app"
    / "ingestion"
    / "source_adapters"
)


@pytest.fixture(scope="module")
def registry() -> dict:
    assert REGISTRY_PATH.exists(), (
        f"source_registry_status.json not found at {REGISTRY_PATH}. "
        "Run `make proof` to regenerate."
    )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class TestAdapterPathsExist:
    def test_adapters_directory_exists(self):
        assert ADAPTERS_DIR.is_dir(), (
            f"Source adapters directory not found: {ADAPTERS_DIR}"
        )

    def test_claimed_present_adapters_exist_on_disk(self, registry):
        """Every source with adapter_exists=true must have a real file."""
        errors = []
        for src in registry["sources"]:
            adapter_key = src.get("adapter_key", "")
            claimed_exists = src.get("adapter_exists", False)
            if not claimed_exists or not adapter_key:
                continue

            adapter_file = ADAPTERS_DIR / f"{adapter_key}.py"
            if not adapter_file.exists():
                errors.append(
                    f"source '{src['source_key']}': adapter_exists=true but "
                    f"{adapter_file.relative_to(ADAPTERS_DIR.parent.parent.parent.parent)} "
                    f"not found on disk"
                )
        assert not errors, (
            "The following sources claim adapter_exists=true but the file is missing:\n"
            + "\n".join(errors)
        )

    def test_claimed_missing_adapters_do_not_exist_on_disk(self, registry):
        """Every source with adapter_exists=false must NOT have a stale file
        that contradicts the registry claim."""
        errors = []
        for src in registry["sources"]:
            adapter_key = src.get("adapter_key", "")
            claimed_exists = src.get("adapter_exists", False)
            if claimed_exists or not adapter_key:
                continue

            adapter_file = ADAPTERS_DIR / f"{adapter_key}.py"
            if adapter_file.exists():
                errors.append(
                    f"source '{src['source_key']}': adapter_exists=false but "
                    f"{adapter_key}.py exists on disk — registry is stale"
                )
        assert not errors, (
            "The following sources claim adapter_exists=false but the file exists:\n"
            + "\n".join(errors)
        )

    def test_runnable_sources_have_adapter(self, registry):
        """Every runnable_now=true source must have an adapter on disk."""
        errors = []
        for src in registry["sources"]:
            if not src.get("runnable_now"):
                continue
            adapter_key = src.get("adapter_key", "")
            if not adapter_key:
                errors.append(
                    f"source '{src['source_key']}' is runnable_now=true "
                    "but has no adapter_key"
                )
                continue
            adapter_file = ADAPTERS_DIR / f"{adapter_key}.py"
            if not adapter_file.exists():
                errors.append(
                    f"source '{src['source_key']}' is runnable_now=true but "
                    f"adapter file {adapter_key}.py not found"
                )
        assert not errors, (
            "Runnable sources with missing adapters:\n" + "\n".join(errors)
        )
