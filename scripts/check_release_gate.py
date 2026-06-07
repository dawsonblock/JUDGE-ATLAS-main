#!/usr/bin/env python3
"""Validate release_gate maturity vocabulary and safety semantics.

This check enforces explicit alpha maturity fields and blocks ambiguous
production wording in the release gate payload.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release_gate payload must be a JSON object")
    return payload


def validate_release_gate(path: Path) -> tuple[list[str], bool]:
    errors: list[str] = []
    if not path.exists() or not path.is_file():
        return [f"missing_release_gate:{path}"], False

    try:
        gate = _load_json(path)
    except Exception as exc:  # pragma: no cover - defensive parser guard
        return [f"invalid_release_gate_json:{exc}"], False

    required_bool_fields = (
        "alpha_candidate",
        "self_verifying_alpha",
        "production_release_candidate",
        "production_ready",
        "public_release_safe",
    )
    has_new_schema = all(field in gate for field in required_bool_fields)

    for field in required_bool_fields:
        if field not in gate:
            if not has_new_schema:
                continue
            errors.append(f"missing_field:{field}")
            continue
        if not isinstance(gate.get(field), bool):
            errors.append(f"non_boolean_field:{field}")

    production_release_candidate = bool(
        gate.get("production_release_candidate", False)
    )
    production_ready = bool(gate.get("production_ready", False))
    public_release_safe = bool(gate.get("public_release_safe", False))

    if production_release_candidate:
        errors.append("production_release_candidate_must_be_false_for_alpha")
    if production_ready:
        errors.append("production_ready_must_be_false_for_alpha")
    if public_release_safe:
        errors.append("public_release_safe_must_be_false_for_alpha")

    self_verifying_alpha = bool(
        gate.get("self_verifying_alpha", gate.get("alpha_gate_passed", False))
    )
    alpha_candidate = bool(
        gate.get("alpha_candidate", gate.get("alpha_gate_passed", False))
    )
    alpha_gate_passed = bool(gate.get("alpha_gate_passed", False))

    if self_verifying_alpha and not alpha_candidate:
        errors.append("self_verifying_alpha_requires_alpha_candidate")
    if self_verifying_alpha != alpha_gate_passed:
        errors.append("self_verifying_alpha_mismatch_alpha_gate_passed")

    # Legacy key is tolerated only for legacy payloads.
    if (
        has_new_schema
        and "release_candidate" in gate
        and bool(gate.get("release_candidate", False))
    ):
        errors.append("legacy_release_candidate_must_not_be_true")

    return errors, has_new_schema


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root containing artifacts/proof/current/release_gate.json",
    )
    parser.add_argument(
        "--release-gate",
        default="artifacts/proof/current/release_gate.json",
        help="Path to release gate JSON (absolute or repo-relative)",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    gate_path = Path(args.release_gate)
    if not gate_path.is_absolute():
        gate_path = (repo_root / gate_path).resolve()

    errors, has_new_schema = validate_release_gate(gate_path)
    if errors:
        print("RELEASE_GATE_VOCAB: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    if not has_new_schema:
        print("RELEASE_GATE_VOCAB: PASS (legacy schema tolerated)")
        return 0

    print("RELEASE_GATE_VOCAB: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
