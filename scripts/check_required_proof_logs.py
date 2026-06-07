#!/usr/bin/env python3
"""
Check that all required proof logs exist and are non-empty.

Required logs:
- backend_pytest.log
- frontend_build.log
- docker_runtime_preflight.log
- docker_smoke.log
- source_registry_proof_pytest.log
- (and others referenced in proof_manifest)

HARD RULE: No proof step is allowed to pass unless the matching .log file
exists and is non-empty.
"""

import json
import os
import sys


REQUIRED_LOGS = [
    "release_gate.log",
    "backend_pytest.log",
    "frontend_build.log",
    "frontend_route_smoke.log",
    "docker_runtime_preflight.log",
    "docker_smoke.log",
    "runtime_smoke.log",
    "source_registry_proof_pytest.log",
    "postgis_proof.log",
    "egress_proxy_proof.log",
    "demo_proof.log",
    "public_api_boundary.log",
    "archive_validation.log",
]


def check_required_proof_logs() -> bool:
    """Verify all required proof logs exist and are non-empty."""
    proof_dir = "artifacts/proof/current"

    if not os.path.exists(proof_dir):
        print(f"FAIL: Proof directory not found: {proof_dir}")
        return False

    missing = []
    empty = []

    for log_name in REQUIRED_LOGS:
        log_path = os.path.join(proof_dir, log_name)

        if not os.path.exists(log_path):
            missing.append(log_name)
        elif os.path.getsize(log_path) == 0:
            empty.append(log_name)

    if missing:
        print(f"FAIL: Missing proof logs ({len(missing)}):")
        for log in sorted(missing):
            print(f"      {log}")

    if empty:
        print(f"FAIL: Empty proof logs ({len(empty)}):")
        for log in sorted(empty):
            print(f"      {log}")

    if missing or empty:
        return False

    print(f"PASS: All {len(REQUIRED_LOGS)} required proof logs exist and are non-empty")
    return True


def load_proof_manifest() -> dict:
    """Load proof_manifest.json."""
    manifest_path = "artifacts/proof/current/proof_manifest.json"

    if not os.path.exists(manifest_path):
        print(f"WARN: proof_manifest.json not found: {manifest_path}")
        return {}

    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"WARN: Error loading manifest: {e}")
        return {}


def check_proof_manifest() -> bool:
    """Verify proof_manifest.json references existing files."""
    manifest = load_proof_manifest()

    if not manifest:
        print("FAIL: proof_manifest.json missing or invalid")
        return False

    proof_dir = "artifacts/proof/current"
    required_logs = manifest.get("required_logs", [])
    required_summaries = manifest.get("required_summaries", [])

    missing = []

    for log_path in required_logs:
        log_name = os.path.basename(log_path)
        full_path = os.path.join(proof_dir, log_name)
        if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
            missing.append(log_path)

    for summary_path in required_summaries:
        summary_name = os.path.basename(summary_path)
        full_path = os.path.join(proof_dir, summary_name)
        if not os.path.exists(full_path):
            missing.append(summary_path)

    if missing:
        print(f"FAIL: Missing referenced artifacts ({len(missing)}):")
        for artifact in sorted(missing):
            print(f"      {artifact}")
        return False

    print(f"PASS: proof_manifest verified ({len(required_logs)} logs, {len(required_summaries)} summaries)")
    return True


def main():
    logs_ok = check_required_proof_logs()
    manifest_ok = check_proof_manifest()

    if logs_ok and manifest_ok:
        print("\nAll proof checks PASS")
        sys.exit(0)
    else:
        print("\nSome proof checks FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
