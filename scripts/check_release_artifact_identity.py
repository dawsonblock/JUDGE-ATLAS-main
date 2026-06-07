#!/usr/bin/env python3
"""
Check that the release artifact has canonical identity metadata.

Rejects manually zipped working folders.
Enforces canonical artifact naming.
"""

import json
import os
import sys
from datetime import datetime, timezone


def check_release_artifact_identity() -> bool:
    """Verify release_artifact_identity.json exists and is valid."""
    identity_path = "artifacts/proof/current/release_artifact_identity.json"

    if not os.path.exists(identity_path):
        print(f"FAIL: {identity_path} missing")
        return False

    try:
        with open(identity_path, "r") as f:
            identity = json.load(f)

        # Verify required fields
        if identity.get("manual_zip", False):
            print("FAIL: manual_zip=true (manually zipped folder detected)")
            return False

        if not identity.get("canonical", False):
            print("FAIL: canonical=false")
            return False

        if identity.get("artifact_kind") != "pipeline_release_artifact":
            print("FAIL: artifact_kind is not pipeline_release_artifact")
            return False

        # Verify artifact name
        expected_names = [
            "JUDGE_ATLAS-main-final.zip",
            "JUDGE-ATLAS-main-final.zip",
        ]
        artifact_name = identity.get("artifact_name", "")
        if artifact_name not in expected_names:
            print(f"FAIL: artifact_name={artifact_name} not in allowed names")
            print(f"      Expected one of: {expected_names}")
            return False

        print(f"PASS: Release artifact identity valid")
        print(f"      name={artifact_name}")
        print(f"      created_by={identity.get('created_by', 'unknown')}")
        print(f"      build_id={identity.get('build_id', 'unknown')}")
        return True

    except Exception as e:
        print(f"FAIL: Error reading {identity_path}: {e}")
        return False


def main():
    if not check_release_artifact_identity():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
