#!/usr/bin/env python3
"""
Check that README.md and documentation are consistent with canonical proof.

Verifies README has status block and doesn't overclaim readiness.
"""

import json
import os
import sys


def check_readme_status_block() -> bool:
    """Verify README has status block referencing canonical proof."""
    readme_path = "README.md"

    if not os.path.exists(readme_path):
        print(f"FAIL: README.md not found")
        return False

    with open(readme_path, "r") as f:
        content = f.read()

    required_patterns = [
        "artifacts/proof/current/release_gate.json",
        "artifacts/proof/current/proof_manifest.json",
        "production_ready",
        "public_release_safe",
        "self_verifying_alpha",
    ]

    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)

    if missing_patterns:
        print(f"FAIL: README missing required status references:")
        for pattern in missing_patterns:
            print(f"      {pattern}")
        return False

    # Check for overclaiming
    overclaim_patterns = [
        "production-ready unless",
        "production_ready=true",
        "This is production ready",
    ]

    for pattern in overclaim_patterns:
        if pattern in content:
            print(f"WARN: README may be overclaiming: {pattern}")

    print("PASS: README status block verified")
    return True


def check_proof_gate_consistency() -> bool:
    """Verify release_gate.json is consistent with canonical proof."""
    gate_path = "artifacts/proof/current/release_gate.json"

    if not os.path.exists(gate_path):
        print(f"FAIL: release_gate.json not found")
        return False

    try:
        with open(gate_path, "r") as f:
            gate = json.load(f)
    except Exception as e:
        print(f"FAIL: Error reading release_gate.json: {e}")
        return False

    # Alpha must not claim production readiness
    if gate.get("production_ready", False):
        print("FAIL: release_gate claims production_ready=true for alpha")
        return False

    if gate.get("public_release_safe", False):
        print("FAIL: release_gate claims public_release_safe=true for alpha")
        return False

    print("PASS: release_gate.json consistency verified")
    return True


def check_manifest_exists() -> bool:
    """Verify proof_manifest.json exists."""
    manifest_path = "artifacts/proof/current/proof_manifest.json"

    if not os.path.exists(manifest_path):
        print(f"FAIL: proof_manifest.json not found")
        return False

    try:
        with open(manifest_path, "r") as f:
            json.load(f)
        print("PASS: proof_manifest.json exists and is valid JSON")
        return True
    except Exception as e:
        print(f"FAIL: proof_manifest.json is invalid: {e}")
        return False


def main():
    checks = [
        ("README status block", check_readme_status_block),
        ("Proof gate consistency", check_proof_gate_consistency),
        ("Manifest exists", check_manifest_exists),
    ]

    all_pass = True
    for name, check_fn in checks:
        result = check_fn()
        all_pass = all_pass and result
        if not result:
            print()

    if all_pass:
        print("\nAll consistency checks PASS")
        sys.exit(0)
    else:
        print("\nSome consistency checks FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
