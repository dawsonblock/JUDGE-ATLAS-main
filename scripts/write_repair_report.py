#!/usr/bin/env python3
"""Generate artifacts/proof/current/REPAIR_REPORT.md from current proof state.

This script is a standalone backstop: if the release gate fails to write
REPAIR_REPORT.md, running this script ensures the mandatory artifact exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "artifacts" / "proof" / "current"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    return result.stdout.strip()


def _git_sha() -> str:
    return _run(["git", "rev-parse", "HEAD"]) or "unknown"


def _python_version() -> str:
    return (
        f"{sys.version_info.major}."
        f"{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )


def _node_version() -> str:
    return (
        _run(["node", "--version"]).lstrip("v") or "unknown"
    )


def _npm_version() -> str:
    return (
        _run(["npm", "--version"]) or "unknown"
    )


def _docker_available() -> bool:
    result = subprocess.run(
        ["docker", "version"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return result.returncode == 0


def _load_gate_result() -> dict:
    gate_path = OUT_DIR / "release_gate.json"
    if gate_path.exists():
        try:
            return json.loads(gate_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _main() -> None:
    # If release_gate.py already wrote a complete REPAIR_REPORT.md (identified
    # by its authoritative header), do not overwrite it with this shallow
    # backstop — doing so would invalidate the SHA-256 recorded in
    # proof_manifest.json and lose the full phase/blocker detail.
    out_path = OUT_DIR / "REPAIR_REPORT.md"
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        if existing.startswith("# REPAIR_REPORT"):
            print(
                f"Skipping {out_path.relative_to(REPO_ROOT)}: "
                "authoritative report already present"
            )
            return

    gate = _load_gate_result()
    timestamp = datetime.now(timezone.utc).isoformat()

    alpha_gate_passed = gate.get("alpha_gate_passed", False)
    alpha_candidate = gate.get("alpha_candidate", False)
    self_verifying_alpha = gate.get("self_verifying_alpha", False)
    production_ready = gate.get("production_ready", False)
    public_release_safe = gate.get("public_release_safe", False)

    checks = gate.get("checks", [])
    passed = sum(1 for c in checks if c.get("passed"))
    failed = len(checks) - passed

    lines = [
        "# JUDGE_ATLASX Repair Report",
        "",
        f"Generated: {timestamp}",
        "",
        "## Runtime",
        f"- Python: {_python_version()}",
        f"- Node: {_node_version()}",
        f"- npm: {_npm_version()}",
        f"- Docker: {'available' if _docker_available() else 'unavailable'}",
        "",
        "## Proof State",
        f"- alpha_gate_passed: {alpha_gate_passed}",
        f"- alpha_candidate: {alpha_candidate}",
        f"- self_verifying_alpha: {self_verifying_alpha}",
        f"- production_ready: {production_ready}",
        f"- public_release_safe: {public_release_safe}",
        f"- checks_passed: {passed}",
        f"- checks_failed: {failed}",
        "",
        "## Required Artifacts",
        "- release_gate.json",
        "- proof_manifest.json",
        "- required_log_index.json",
        "- release_readiness.md",
        "- REPAIR_REPORT.md",
        "",
        "## Known Limitations",
        "- Not for production use.",
        "- Not public-release-safe.",
        "- AI outputs are derivative only.",
        "- Public/high-stakes outputs require human review"
        " and evidence snapshots.",
        "",
    ]

    text = "\n".join(lines)
    out_path.write_text(text, encoding="utf-8")
    # Also write a copy at repo root for visibility
    (REPO_ROOT / "REPAIR_REPORT.md").write_text(
        text, encoding="utf-8"
    )
    print(
        f"Wrote {out_path.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    _main()
