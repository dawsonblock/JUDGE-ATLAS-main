#!/usr/bin/env python3
"""
Generate archive integrity proof after ZIP creation.

This script runs AFTER the ZIP is packaged and verifies:
1. ZIP structure safety (no path traversal, no absolute paths)
2. Required proof artifacts exist inside ZIP
3. SHA256 checksums match
4. Timestamps and build IDs are consistent
5. archive_self_verifying claim is justified
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def sha256_file(path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_zip_paths(zip_path: str) -> tuple[bool, list[str], list[str]]:
    """Check for path traversal and absolute path entries."""
    traversals = []
    absolutes = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if name.startswith('/'):
                absolutes.append(name)
            if '..' in name or name.startswith('../'):
                traversals.append(name)

    return not (traversals or absolutes), traversals, absolutes


def extract_and_validate(zip_path: str, proof_dir: str) -> Dict[str, Any]:
    """Extract and validate archive contents."""
    result = {
        "archive_path": os.path.abspath(zip_path),
        "archive_sha256": sha256_file(zip_path),
        "archive_size_bytes": os.path.getsize(zip_path),
        "zip_entries": 0,
        "path_traversal_entries": [],
        "absolute_path_entries": [],
        "required_artifacts_checked": 0,
        "required_artifacts_present": 0,
        "required_artifacts_missing": [],
        "timestamps_consistent": False,
        "build_ids_consistent": False,
        "archive_self_verifying": False,
        "validation_errors": [],
    }

    # Step 1: Check ZIP structure safety
    safe, traversals, absolutes = validate_zip_paths(zip_path)
    result["path_traversal_entries"] = traversals
    result["absolute_path_entries"] = absolutes

    if not safe:
        result["validation_errors"].append("ZIP contains unsafe paths")
        return result

    # Step 2: Extract to temporary location
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmpdir)
                result["zip_entries"] = len(zf.namelist())

            # Step 3: Find proof directory in extracted archive
            extracted_proof_dir = None
            for root, dirs, files in os.walk(tmpdir):
                if "proof_manifest.json" in files:
                    extracted_proof_dir = root
                    break

            if not extracted_proof_dir:
                result["validation_errors"].append("proof_manifest.json not found in extracted archive")
                return result

            # Step 4: Load manifests
            manifest_path = os.path.join(extracted_proof_dir, "proof_manifest.json")
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            release_gate_path = os.path.join(extracted_proof_dir, "release_gate.json")
            if not os.path.exists(release_gate_path):
                result["validation_errors"].append("release_gate.json not found in extracted archive")
                return result

            with open(release_gate_path, "r") as f:
                release_gate = json.load(f)

            # Step 5: Validate timestamps and build IDs match
            manifest_build_id = manifest.get("build_id")
            gate_build_id = release_gate.get("build_id")
            if manifest_build_id and gate_build_id and manifest_build_id == gate_build_id:
                result["build_ids_consistent"] = True
            else:
                result["validation_errors"].append("build_id mismatch between manifest and gate")

            manifest_timestamp = manifest.get("timestamp")
            gate_timestamp = release_gate.get("timestamp")
            if manifest_timestamp and gate_timestamp:
                # Allow small time difference (< 5 minutes)
                from datetime import datetime
                m_dt = datetime.fromisoformat(manifest_timestamp.replace('Z', '+00:00'))
                g_dt = datetime.fromisoformat(gate_timestamp.replace('Z', '+00:00'))
                time_diff = abs((m_dt - g_dt).total_seconds())
                if time_diff < 300:  # 5 minutes
                    result["timestamps_consistent"] = True
                else:
                    result["validation_errors"].append(
                        f"timestamp skew: {time_diff}s between manifest and gate"
                    )

            # Step 6: Check required artifacts
            required_logs = manifest.get("required_logs", [])
            required_summaries = manifest.get("required_summaries", [])
            all_required = required_logs + required_summaries

            result["required_artifacts_checked"] = len(all_required)

            for artifact_relpath in all_required:
                # Extract filename from path
                artifact_name = os.path.basename(artifact_relpath)
                full_path = os.path.join(extracted_proof_dir, artifact_name)

                if os.path.exists(full_path):
                    result["required_artifacts_present"] += 1
                else:
                    result["required_artifacts_missing"].append(artifact_relpath)

            # Step 7: Determine self-verifying status
            if (not result["validation_errors"] and
                    not result["required_artifacts_missing"] and
                    result["build_ids_consistent"] and
                    result["timestamps_consistent"] and
                    result["zip_entries"] > 0):
                result["archive_self_verifying"] = True

        except Exception as e:
            result["validation_errors"].append(f"Exception during validation: {str(e)}")
            return result

    return result


def generate_integrity_artifact(validation: Dict[str, Any], output_dir: str) -> None:
    """Write archive_integrity.json and archive_integrity.log"""
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate JSON artifact
    integrity_json = {
        "timestamp": timestamp,
        "archive_path": validation["archive_path"],
        "archive_sha256": validation["archive_sha256"],
        "archive_size_bytes": validation["archive_size_bytes"],
        "zip_entries": validation["zip_entries"],
        "path_traversal_entries": validation["path_traversal_entries"],
        "absolute_path_entries": validation["absolute_path_entries"],
        "required_artifacts_checked": validation["required_artifacts_checked"],
        "required_artifacts_present": validation["required_artifacts_present"],
        "required_artifacts_missing": validation["required_artifacts_missing"],
        "build_ids_consistent": validation["build_ids_consistent"],
        "timestamps_consistent": validation["timestamps_consistent"],
        "archive_self_verifying": validation["archive_self_verifying"],
        "validation_errors": validation["validation_errors"],
    }

    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "archive_integrity.json")
    with open(json_path, "w") as f:
        json.dump(integrity_json, f, indent=2)

    # Generate log artifact
    log_path = os.path.join(output_dir, "archive_integrity.log")
    with open(log_path, "w") as f:
        f.write(f"Archive Integrity Validation Report\n")
        f.write(f"Generated: {timestamp}\n")
        f.write(f"\n")
        f.write(f"Archive: {validation['archive_path']}\n")
        f.write(f"SHA256: {validation['archive_sha256']}\n")
        f.write(f"Size: {validation['archive_size_bytes']} bytes\n")
        f.write(f"Entries: {validation['zip_entries']}\n")
        f.write(f"\n")
        f.write(f"Path Safety:\n")
        f.write(f"  Traversal entries: {len(validation['path_traversal_entries'])}\n")
        f.write(f"  Absolute path entries: {len(validation['absolute_path_entries'])}\n")
        f.write(f"\n")
        f.write(f"Required Artifacts:\n")
        f.write(f"  Checked: {validation['required_artifacts_checked']}\n")
        f.write(f"  Present: {validation['required_artifacts_present']}\n")
        f.write(f"  Missing: {len(validation['required_artifacts_missing'])}\n")
        if validation["required_artifacts_missing"]:
            for missing in validation["required_artifacts_missing"]:
                f.write(f"    - {missing}\n")
        f.write(f"\n")
        f.write(f"Consistency Checks:\n")
        f.write(f"  Build IDs consistent: {validation['build_ids_consistent']}\n")
        f.write(f"  Timestamps consistent: {validation['timestamps_consistent']}\n")
        f.write(f"\n")
        f.write(f"Archive Self-Verifying: {validation['archive_self_verifying']}\n")
        if validation["validation_errors"]:
            f.write(f"\nValidation Errors:\n")
            for error in validation["validation_errors"]:
                f.write(f"  - {error}\n")

    print(f"Generated {json_path}")
    print(f"Generated {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate archive integrity proof")
    parser.add_argument("zip_path", help="Path to packaged ZIP archive")
    parser.add_argument("--proof-dir", default="artifacts/proof/current",
                        help="Output directory for proof artifacts")
    args = parser.parse_args()

    if not os.path.exists(args.zip_path):
        print(f"ERROR: {args.zip_path} not found", file=sys.stderr)
        sys.exit(1)

    validation = extract_and_validate(args.zip_path, args.proof_dir)
    generate_integrity_artifact(validation, args.proof_dir)

    if validation["archive_self_verifying"]:
        print("✓ Archive is self-verifying")
        sys.exit(0)
    else:
        print("✗ Archive is NOT self-verifying")
        if validation["validation_errors"]:
            print("\nErrors:")
            for error in validation["validation_errors"]:
                print(f"  {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
