#!/usr/bin/env python3
"""Inspect a release archive surface for forbidden files and directories."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

FORBIDDEN_SEGMENTS = {
    "external",
    "__MACOSX",
    "node_modules",
    ".kilo",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".validation_logs",
    ".git",
}
FORBIDDEN_PREFIXES = (
    "artifacts/proof/archive/",
    "artifacts/proof/backend/",
    "artifacts/proof/frontend/",
    "artifacts/proof/history/",
    "artifacts/history/",
    ".validation_logs/",
    "logs/",
    "tmp/",
    "temp/",
    "evidence_store/",
    "data/evidence_store/",
)
FORBIDDEN_FILE_NAMES = {
    ".env",
    ".env.example",
    ".env.local",
    ".env.production",
    ".env.development",
    ".coverage",
    ".ds_store",
    "thumbs.db",
    "id_rsa",
    "id_ed25519",
}
FORBIDDEN_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".crt",
    ".log",
)


def inspect_surface(archive: Path) -> dict:
    errors: list[str] = []
    forbidden_paths: list[str] = []

    report: dict[str, Any] = {
        "archive": str(archive),
        "valid": False,
        "errors": errors,
        "forbidden_paths": forbidden_paths,
    }

    if not archive.exists() or not archive.is_file():
        errors.append("archive_not_found")
        return report

    try:
        with zipfile.ZipFile(archive, "r") as zf:
            infos = [
                info
                for info in zf.infolist()
                if info.filename and not info.filename.endswith("/")
            ]
            for info in infos:
                parts = Path(info.filename).parts
                rel_path = (
                    "/".join(parts[1:]) if len(parts) > 1 else info.filename
                )
                rel_name = Path(rel_path).name.lower()

                if any(Path(part).name.startswith("._") for part in parts):
                    forbidden_paths.append(info.filename)
                    continue

                if any(part in FORBIDDEN_SEGMENTS for part in parts):
                    forbidden_paths.append(info.filename)
                    continue
                if any(
                    rel_path.startswith(prefix)
                    for prefix in FORBIDDEN_PREFIXES
                ):
                    forbidden_paths.append(info.filename)
                    continue
                if rel_name in FORBIDDEN_FILE_NAMES:
                    forbidden_paths.append(info.filename)
                    continue
                if rel_name.startswith(".env."):
                    forbidden_paths.append(info.filename)
                    continue
                if (
                    rel_name.endswith(".log")
                    and rel_path.startswith("artifacts/proof/current/")
                ):
                    continue
                if rel_name.endswith(FORBIDDEN_SUFFIXES):
                    forbidden_paths.append(info.filename)
                    continue
    except zipfile.BadZipFile:
        errors.append("bad_zip_file")
        return report

    report["forbidden_paths"] = sorted(set(forbidden_paths))
    if report["forbidden_paths"]:
        errors.append("forbidden_release_surface_paths")
    report["valid"] = not errors
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        required=True,
        help="Release archive path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output",
    )
    args = parser.parse_args()

    report = inspect_surface(Path(args.archive).resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("PASS" if report["valid"] else "FAIL")
        if report["forbidden_paths"]:
            print("forbidden_paths=" + ",".join(report["forbidden_paths"]))

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
