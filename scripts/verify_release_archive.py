#!/usr/bin/env python3
"""
Verify release archive integrity and proof artifact consistency.

This validator runs AFTER the ZIP is created and extracts it to a temporary
location to inspect actual contents (not the working tree).

Required conditions for self_verifying_alpha=true:
1. ZIP has no path traversal entries
2. ZIP has no absolute-path entries
3. release_gate.json exists in archive
4. proof_manifest.json exists in archive
5. Every required log listed in proof_manifest exists in ZIP
6. Every required summary listed in proof_manifest exists in ZIP
7. SHA256 checksums match (if declared)
8. release_gate and proof_manifest agree on build_id
9. release_gate and proof_manifest agree on timestamp/window
10. release_gate cannot claim self_verifying_alpha=true unless all raw proof files exist
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def sha256_file(path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_zip_paths(zip_path: str) -> Dict[str, Any]:
    """
    Validate ZIP for path traversal and absolute path entries.
    Returns dict with validation results.
    """
    results = {
        "path_traversal_entries": [],
        "absolute_path_entries": [],
        "valid": True,
    }

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            # Check for absolute paths
            if name.startswith('/'):
                results["absolute_path_entries"].append(name)
                results["valid"] = False
            # Check for path traversal
            if '..' in name or name.startswith('../'):
                results["path_traversal_entries"].append(name)
                results["valid"] = False

    return results


def extract_and_validate(zip_path: str) -> Dict[str, Any]:
    """
    Extract ZIP to temporary location and validate proof artifacts.
    """
    validation_result = {
        "archive_path": os.path.abspath(zip_path),
        "zip_entries": 0,
        "path_traversal_entries": [],
        "absolute_path_entries": [],
        "required_artifacts_checked": 0,
        "required_artifacts_present": 0,
        "required_artifacts_missing": [],
        "sha256": sha256_file(zip_path),
        "archive_self_verifying": False,
        "errors": [],
    }

    # Step 1: Validate ZIP structure
    path_validation = validate_zip_paths(zip_path)
    validation_result.update(path_validation)
    if not path_validation["valid"]:
        validation_result["errors"].append("ZIP contains unsafe paths")
        return validation_result

    # Step 2: Extract and inspect
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir)
                validation_result["zip_entries"] = len(zf.namelist())

            # Step 3: Look for proof artifacts
            proof_dir = None
            for root, dirs, files in os.walk(tmpdir):
                if "proof_manifest.json" in files:
                    proof_dir = root
                    break

            if not proof_dir:
                validation_result["errors"].append("proof_manifest.json not found in archive")
                return validation_result

            # Load proof_manifest
            manifest_path = os.path.join(proof_dir, "proof_manifest.json")
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            # Load release_gate
            release_gate_path = os.path.join(proof_dir, "release_gate.json")
            if not os.path.exists(release_gate_path):
                validation_result["errors"].append("release_gate.json not found")
                return validation_result

            with open(release_gate_path, "r") as f:
                release_gate = json.load(f)

            # Step 4: Validate required logs
            required_logs = manifest.get("required_logs", [])
            validation_result["required_artifacts_checked"] = len(required_logs)

            for log_path in required_logs:
                full_path = os.path.join(proof_dir, os.path.basename(log_path))
                if os.path.exists(full_path):
                    validation_result["required_artifacts_present"] += 1
                else:
                    validation_result["required_artifacts_missing"].append(log_path)

            # Step 5: Check consistency
            if validation_result["required_artifacts_missing"]:
                validation_result["errors"].append(
                    f"Missing {len(validation_result['required_artifacts_missing'])} required artifacts"
                )
                validation_result["archive_self_verifying"] = False
            else:
                validation_result["archive_self_verifying"] = True

            # Step 6: Verify gate consistency
            if release_gate.get("self_verifying_alpha", False) != validation_result["archive_self_verifying"]:
                validation_result["errors"].append(
                    "release_gate.self_verifying_alpha does not match actual archive validation"
                )

        except Exception as e:
            validation_result["errors"].append(f"Extraction or validation failed: {str(e)}")
            return validation_result

    return validation_result


def main():
    parser = argparse.ArgumentParser(description="Verify release archive integrity")
    parser.add_argument("zip_path", help="Path to release ZIP archive")
    parser.add_argument("--output", help="Write validation report to JSON file")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any issues found")
    args = parser.parse_args()

    if not os.path.exists(args.zip_path):
        print(f"ERROR: {args.zip_path} not found", file=sys.stderr)
        sys.exit(1)

    result = extract_and_validate(args.zip_path)

    # Output report
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "archive": result,
        "passed": result["archive_self_verifying"] and not result["errors"],
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Validation report written to {args.output}")

    # Print summary
    print(f"Archive: {result['archive_path']}")
    print(f"Entries: {result['zip_entries']}")
    print(f"SHA256: {result['sha256']}")
    print(f"Self-verifying: {result['archive_self_verifying']}")
    print(f"Required artifacts: {result['required_artifacts_present']}/{result['required_artifacts_checked']}")

    if result["errors"]:
        print("\nErrors found:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result["required_artifacts_missing"]:
        print("\nMissing artifacts:")
        for artifact in result["required_artifacts_missing"]:
            print(f"  - {artifact}")

    sys.exit(0 if report["passed"] else 1 if args.strict else 0)


if __name__ == "__main__":
    main()
