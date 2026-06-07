#!/usr/bin/env python3
"""Verify that release_gate.json claims are internally consistent and that
status documents do not contradict the gate's authoritative boolean claims.

This script is distinct from check_truth_claims.py (which scans free-form text
for forbidden production phrases) and check_status_truth_consistency.py (which
checks alpha/production label consistency).  This script focuses on:

1. Internal consistency of release_gate.json boolean claim fields.
2. That CURRENT_PROOF.md and key status docs accurately reflect the gate's
   claimed pass/fail and production-readiness state.
3. That no doc claims production_ready=true while the gate says false.

Usage::

    python3 scripts/check_release_claims.py
    python3 scripts/check_release_claims.py --root /path/to/repo
    python3 scripts/check_release_claims.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[1]

STATUS_DOCS = [
    "CURRENT_PROOF.md",
    "CURRENT_STATUS.md",
    "PROOF_STATUS.md",
    "STATUS.md",
    "REPAIR_STATUS.md",
    "RELEASE_BLOCKERS.md",
]

_PRODUCTION_READY_PHRASES = [
    "production_ready: true",
    "production ready: true",
    "production_release_candidate: true",
    "release_candidate: true",
    "public_release_safe: true",
]

_ALPHA_BLOCKED_PHRASES = [
    "alpha_gate_passed: false",
    "alpha-proof-blocked",
]

_ALPHA_PASS_PHRASES = [
    "alpha_gate_passed: true",
    "alpha-proof-pass",
    "alpha_candidate: true",
]


def _load_gate(repo_root: Path) -> dict | None:
    gate_path = (
        repo_root / "artifacts" / "proof" / "current" / "release_gate.json"
    )
    if not gate_path.exists():
        return None
    return json.loads(gate_path.read_text(encoding="utf-8"))


def _check_gate_internal_consistency(gate: dict) -> list[str]:
    violations: list[str] = []

    alpha_passed = gate.get("alpha_gate_passed")
    production_ready = gate.get("production_ready")
    prod_release_candidate = gate.get("production_release_candidate")
    public_release_safe = gate.get("public_release_safe")
    release_candidate = gate.get("release_candidate")

    # production_ready implies alpha passed
    if production_ready and not alpha_passed:
        violations.append(
            "production_ready=true but alpha_gate_passed is not true — "
            "production requires alpha gate to pass first"
        )

    # production_release_candidate implies production_ready
    if prod_release_candidate and not production_ready:
        violations.append(
            "production_release_candidate=true but production_ready=false — "
            "inconsistent state"
        )

    # public_release_safe implies production_ready
    if public_release_safe and not production_ready:
        violations.append(
            "public_release_safe=true but production_ready=false — "
            "inconsistent state"
        )

    # release_candidate implies alpha passed
    if release_candidate and not alpha_passed:
        violations.append(
            "release_candidate=true but alpha_gate_passed is not true — "
            "inconsistent state"
        )

    # If explicitly alpha-blocked (alpha_gate_passed=false), none of the
    # production-positive flags should be set.
    if alpha_passed is False:
        for flag, key in [
            (production_ready, "production_ready"),
            (prod_release_candidate, "production_release_candidate"),
            (public_release_safe, "public_release_safe"),
            (release_candidate, "release_candidate"),
        ]:
            if flag:
                violations.append(
                    f"{key}=true while alpha_gate_passed=false — "
                    "gate is in an impossible state"
                )

    return violations


def _check_docs_match_gate(repo_root: Path, gate: dict) -> list[str]:
    violations: list[str] = []

    production_ready = gate.get("production_ready", False)
    alpha_passed = gate.get("alpha_gate_passed", False)

    for doc_name in STATUS_DOCS:
        doc_path = repo_root / doc_name
        if not doc_path.exists():
            continue
        text_lower = doc_path.read_text(encoding="utf-8", errors="replace").lower()

        # No doc should claim production_ready=true when gate says false
        if not production_ready:
            for phrase in _PRODUCTION_READY_PHRASES:
                if phrase.lower() in text_lower:
                    violations.append(
                        f"{doc_name}: claims '{phrase}' but "
                        "release_gate.json has production_ready=false"
                    )

        # No doc should claim alpha pass when gate says blocked
        if alpha_passed is False:
            for phrase in _ALPHA_PASS_PHRASES:
                if phrase.lower() in text_lower:
                    violations.append(
                        f"{doc_name}: claims '{phrase}' but "
                        "release_gate.json has alpha_gate_passed=false"
                    )

    return violations


def run_checks(repo_root: Path) -> tuple[str, list[str]]:
    gate = _load_gate(repo_root)
    if gate is None:
        return "FAIL", [
            "artifacts/proof/current/release_gate.json not found; "
            "run 'make proof' to generate"
        ]

    violations: list[str] = []
    violations.extend(_check_gate_internal_consistency(gate))
    violations.extend(_check_docs_match_gate(repo_root, gate))

    if violations:
        return "FAIL", violations
    return "PASS", []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON output",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    if not repo_root.is_dir():
        print(f"ERROR: root is not a directory: {repo_root}", file=sys.stderr)
        return 2

    status, violations = run_checks(repo_root)

    if args.json_output:
        print(json.dumps({"status": status, "violations": violations}, indent=2))
        return 0 if status == "PASS" else 1

    if status == "PASS":
        print("RELEASE_CLAIMS: PASS")
        return 0

    print("RELEASE_CLAIMS: FAIL")
    for v in violations:
        print(f"- {v}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
