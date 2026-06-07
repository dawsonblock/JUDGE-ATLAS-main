#!/usr/bin/env python3
"""Synchronize human-authored status docs from canonical proof artifacts.

This script updates selected status lines in root markdown files so they
cannot drift from artifacts/proof/current/release_gate.json and
artifacts/proof/current/release_readiness.md.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_object:{path}")
    return payload


def _replace_line(text: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, text, flags=re.MULTILINE)


def _sync_status_md(repo_root: Path, gate: dict) -> bool:
    path = repo_root / "STATUS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    alpha_ready = str(bool(gate.get("alpha_gate_passed", False))).lower()
    production_ready = str(bool(gate.get("production_ready", False))).lower()
    public_release_safe = str(bool(gate.get("public_release_safe", False))).lower()
    updated = text
    updated = _replace_line(updated, r"^\s*-\s*alpha_ready\s*:\s*.*$", f"- alpha_ready: {alpha_ready}")
    updated = _replace_line(updated, r"^\s*-\s*production_ready\s*:\s*.*$", f"- production_ready: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*public_release_safe\s*:\s*.*$", f"- public_release_safe: {public_release_safe}")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _sync_current_status_md(repo_root: Path, gate: dict) -> bool:
    path = repo_root / "CURRENT_STATUS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    alpha_ready = str(bool(gate.get("alpha_gate_passed", False))).lower()
    production_ready = str(bool(gate.get("production_ready", False))).lower()
    public_release_safe = str(bool(gate.get("public_release_safe", False))).lower()
    updated = text
    updated = _replace_line(updated, r"^\s*-\s*alpha_ready\s*:\s*.*$", f"- alpha_ready: {alpha_ready}")
    updated = _replace_line(updated, r"^\s*-\s*production_ready\s*:\s*.*$", f"- production_ready: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*public_release_safe\s*:\s*.*$", f"- public_release_safe: {public_release_safe}")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _sync_release_blockers_md(repo_root: Path, gate: dict) -> bool:
    path = repo_root / "RELEASE_BLOCKERS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    alpha_candidate = str(bool(gate.get("alpha_candidate", gate.get("alpha_gate_passed", False)))).lower()
    self_verifying_alpha = str(bool(gate.get("self_verifying_alpha", gate.get("alpha_gate_passed", False)))).lower()
    production_release_candidate = str(bool(gate.get("production_release_candidate", False))).lower()
    production_ready = str(bool(gate.get("production_ready", False))).lower()
    public_release_safe = str(bool(gate.get("public_release_safe", False))).lower()
    updated = text

    # Status Matrix block
    updated = _replace_line(updated, r"^\s*-\s*alpha_candidate\s*:\s*.*$", f"- alpha_candidate: {alpha_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*self_verifying_alpha\s*:\s*.*$", f"- self_verifying_alpha: {self_verifying_alpha}")
    updated = _replace_line(updated, r"^\s*-\s*production_release_candidate\s*:\s*.*$", f"- production_release_candidate: {production_release_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*production_ready\s*:\s*.*$", f"- production_ready: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*public_release_safe\s*:\s*.*$", f"- public_release_safe: {public_release_safe}")

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _sync_repair_status_md(repo_root: Path, gate: dict) -> bool:
    path = repo_root / "REPAIR_STATUS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    alpha_gate_passed = str(bool(gate.get("alpha_gate_passed", False))).lower()
    release_candidate = str(bool(gate.get("release_candidate", gate.get("alpha_gate_passed", False)))).lower()
    production_ready = str(bool(gate.get("production_ready", False))).lower()
    public_release_safe = str(bool(gate.get("public_release_safe", False))).lower()
    updated = text

    updated = _replace_line(
        updated,
        r'"alpha_gate_passed"\s*:\s*"?[^"]+"?,?',
        f'"alpha_gate_passed": {alpha_gate_passed},',
    )
    updated = _replace_line(
        updated,
        r'"release_candidate"\s*:\s*"?[^"]+"?,?',
        f'"release_candidate": {release_candidate},',
    )
    updated = _replace_line(
        updated,
        r'"production_ready"\s*:\s*"?[^"]+"?',
        f'"production_ready": {production_ready}',
    )
    updated = _replace_line(updated, r"^\s*-\s*alpha_ready\s*:\s*.*$", f"- alpha_ready: {alpha_gate_passed}")
    updated = _replace_line(updated, r"^\s*-\s*production_ready\s*:\s*.*$", f"- production_ready: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*public_release_safe\s*:\s*.*$", f"- public_release_safe: {public_release_safe}")

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _sync_proof_status_md(repo_root: Path, gate: dict) -> bool:
    path = repo_root / "PROOF_STATUS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    alpha_candidate = str(bool(gate.get("alpha_candidate", gate.get("alpha_gate_passed", False)))).lower()
    self_verifying_alpha = str(bool(gate.get("self_verifying_alpha", gate.get("alpha_gate_passed", False)))).lower()
    production_release_candidate = str(bool(gate.get("production_release_candidate", False))).lower()
    production_ready = str(bool(gate.get("production_ready", False))).lower()
    public_release_safe = str(bool(gate.get("public_release_safe", False))).lower()

    updated = text
    updated = _replace_line(updated, r"^\s*-\s*\*\*alpha_candidate\*\*\s*:\s*.*$", f"- **alpha_candidate**: {alpha_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*\*\*self_verifying_alpha\*\*\s*:\s*.*$", f"- **self_verifying_alpha**: {self_verifying_alpha}")
    updated = _replace_line(updated, r"^\s*-\s*\*\*production_release_candidate\*\*\s*:\s*.*$", f"- **production_release_candidate**: {production_release_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*\*\*production_ready\*\*\s*:\s*.*$", f"- **production_ready**: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*\*\*public_release_safe\*\*\s*:\s*.*$", f"- **public_release_safe**: {public_release_safe}")

    updated = _replace_line(updated, r"^\s*-\s*alpha_candidate\s*:\s*.*$", f"- alpha_candidate: {alpha_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*self_verifying_alpha\s*:\s*.*$", f"- self_verifying_alpha: {self_verifying_alpha}")
    updated = _replace_line(updated, r"^\s*-\s*production_release_candidate\s*:\s*.*$", f"- production_release_candidate: {production_release_candidate}")
    updated = _replace_line(updated, r"^\s*-\s*production_ready\s*:\s*.*$", f"- production_ready: {production_ready}")
    updated = _replace_line(updated, r"^\s*-\s*public_release_safe\s*:\s*.*$", f"- public_release_safe: {public_release_safe}")

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    gate_path = repo_root / "artifacts" / "proof" / "current" / "release_gate.json"
    if not gate_path.exists():
        raise SystemExit(f"release_gate_not_found:{gate_path}")

    gate = _load_json(gate_path)
    changed = False
    changed |= _sync_status_md(repo_root, gate)
    changed |= _sync_current_status_md(repo_root, gate)
    changed |= _sync_release_blockers_md(repo_root, gate)
    changed |= _sync_repair_status_md(repo_root, gate)
    changed |= _sync_proof_status_md(repo_root, gate)

    print("SYNC_STATUS_DOCS: PASS")
    print(f"changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())