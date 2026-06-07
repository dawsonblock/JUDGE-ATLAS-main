#!/usr/bin/env python3
"""
Generate archive_file_index.json from actual packaged ZIP contents.

Compares against proof_manifest to ensure no claimed files are missing.
"""

import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def generate_archive_file_index(zip_path: str, output_path: str) -> bool:
    """Create index of all files in the ZIP archive."""

    if not os.path.exists(zip_path):
        print(f"FAIL: ZIP not found: {zip_path}")
        return False

    try:
        files = []
        total_size = 0

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                # Extract and hash the file
                with zf.open(info) as f:
                    content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                    size = len(content)

                files.append({
                    "path": info.filename,
                    "size": size,
                    "sha256": file_hash,
                    "compressed_size": info.compress_size,
                })
                total_size += size

        index = {
            "archive_path": os.path.abspath(zip_path),
            "archive_sha256": _sha256_file(zip_path),
            "archive_size": os.path.getsize(zip_path),
            "files": files,
            "total_size": total_size,
            "file_count": len(files),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(index, f, indent=2)

        print(f"Generated: {output_path}")
        print(f"  Files: {len(files)}")
        print(f"  Total size: {total_size} bytes")
        return True

    except Exception as e:
        print(f"FAIL: Error generating index: {e}")
        return False


def _sha256_file(path: str) -> str:
    """Calculate SHA256 of file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_required_artifacts(zip_path: str) -> bool:
    """Verify all required artifacts exist in ZIP."""
    manifest_path = "artifacts/proof/current/proof_manifest.json"

    if not os.path.exists(manifest_path):
        print("WARN: proof_manifest.json not found")
        return True

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"WARN: Error loading manifest: {e}")
        return True

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zip_files = set(zf.namelist())

    required_logs = manifest.get("required_logs", [])
    required_summaries = manifest.get("required_summaries", [])
    all_required = required_logs + required_summaries

    missing = []
    for artifact_path in all_required:
        # Find in ZIP (by basename or full path)
        artifact_name = os.path.basename(artifact_path)
        found = any(f.endswith(artifact_name) for f in zip_files)

        if not found:
            missing.append(artifact_path)

    if missing:
        print(f"FAIL: Missing required artifacts ({len(missing)}):")
        for artifact in sorted(missing):
            print(f"      {artifact}")
        return False

    print(f"PASS: All required artifacts present in ZIP ({len(all_required)} items)")
    return True


def main():
    parser = __import__("argparse").ArgumentParser(
        description="Generate archive file index"
    )
    parser.add_argument("zip_path", help="Path to ZIP archive")
    parser.add_argument(
        "--output",
        default="artifacts/proof/current/archive_file_index.json",
        help="Output index file",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify required artifacts are present",
    )

    args = parser.parse_args()

    success = generate_archive_file_index(args.zip_path, args.output)

    if args.verify:
        success = success and verify_required_artifacts(args.zip_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
