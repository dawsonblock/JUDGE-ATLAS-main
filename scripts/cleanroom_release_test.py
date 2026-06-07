#!/usr/bin/env python3
"""Cleanroom release verification: validate the canonical release archive as if
opening it on a machine with no knowledge of the original workspace.

Checks:
1. Archive exists and is a valid ZIP.
2. Exactly one top-level root directory matching the expected root name.
3. All REQUIRED_PROOF_FILES are present inside the archive.
4. All REQUIRED_ROOT_FILES are present inside the archive.
5. No FORBIDDEN_FILE_NAMES or FORBIDDEN_FILE_SUFFIXES present.
6. No absolute local paths leak through any JSON or text file.
7. release_gate.json is parseable and has required boolean fields.
8. All log paths referenced in release_gate.json checks exist in archive.

This script is intentionally self-contained: it does not import from
validate_release_archive.py so it can serve as an independent second check.

Usage::

    python3 scripts/cleanroom_release_test.py
    python3 scripts/cleanroom_release_test.py --archive dist/JUDGE_ATLAS-main-final.zip
    python3 scripts/cleanroom_release_test.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = REPO_ROOT / "dist" / "JUDGE_ATLAS-main-final.zip"
EXPECTED_ROOT = "JUDGE_ATLAS-main"

REQUIRED_PROOF_FILES = (
    "artifacts/proof/current/CURRENT_PROOF.md",
    "artifacts/proof/current/release_gate.json",
    "artifacts/proof/current/proof_manifest.json",
    "artifacts/proof/current/required_log_index.json",
    "artifacts/proof/current/source_registry_status.json",
    "artifacts/proof/current/release_readiness.md",
)

REQUIRED_ROOT_FILES = (
    "README.md",
    "Makefile",
)

FORBIDDEN_FILE_NAMES = frozenset(
    {
        ".env",
        ".env.local",
        ".env.production",
        ".env.staging",
        "id_rsa",
        "id_ed25519",
        "secrets.json",
    }
)

FORBIDDEN_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks")

REQUIRED_GATE_BOOLEAN_FIELDS = (
    "alpha_gate_passed",
    "production_ready",
    "release_candidate",
)

_LOCAL_PATH_RE = re.compile(r"/(?:Users|home|root)/[^\s\"'<>{}\[\]]+")


def _top_level_roots(names: list[str]) -> list[str]:
    roots: set[str] = set()
    for name in names:
        parts = name.split("/")
        if parts:
            roots.add(parts[0])
    return sorted(roots)


def _read_text_member(zf: zipfile.ZipFile, name: str) -> str | None:
    try:
        raw = zf.read(name)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def run_cleanroom_test(archive: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not archive.exists() or not archive.is_file():
        return {
            "cleanroom_pass": False,
            "errors": ["archive_not_found"],
            "warnings": [],
            "archive": str(archive),
        }

    if not zipfile.is_zipfile(archive):
        return {
            "cleanroom_pass": False,
            "errors": ["not_a_valid_zip"],
            "warnings": [],
            "archive": str(archive),
        }

    with zipfile.ZipFile(archive, "r") as zf:
        infos = [i for i in zf.infolist() if not i.filename.endswith("/")]
        names = [i.filename for i in infos]
        name_set = set(names)

        # 1. Single top-level root
        roots = _top_level_roots(names)
        if len(roots) != 1:
            errors.append(
                f"archive_must_have_exactly_one_root:got={roots}"
            )
            return {
                "cleanroom_pass": False,
                "errors": errors,
                "warnings": warnings,
                "archive": str(archive),
            }
        root = roots[0]
        if root != EXPECTED_ROOT:
            errors.append(
                f"root_mismatch:expected={EXPECTED_ROOT}:got={root}"
            )

        # 2. Required proof files
        for rel in REQUIRED_PROOF_FILES:
            if f"{root}/{rel}" not in name_set:
                errors.append(f"missing_required_proof_file:{rel}")

        # 3. Required root files
        for rel in REQUIRED_ROOT_FILES:
            if f"{root}/{rel}" not in name_set:
                errors.append(f"missing_required_root_file:{rel}")

        # 4. Forbidden files
        for info in infos:
            fname = Path(info.filename).name.lower()
            if fname in FORBIDDEN_FILE_NAMES:
                errors.append(f"forbidden_file:{info.filename}")
            if fname.endswith(FORBIDDEN_FILE_SUFFIXES):
                errors.append(f"forbidden_suffix_file:{info.filename}")

        # 5. No local path leaks in text/JSON files
        for info in infos:
            fname_lower = info.filename.lower()
            if not (
                fname_lower.endswith(".json")
                or fname_lower.endswith(".md")
                or fname_lower.endswith(".txt")
                or fname_lower.endswith(".log")
            ):
                continue
            if info.file_size > 512 * 1024:
                continue
            text = _read_text_member(zf, info.filename)
            if text and _LOCAL_PATH_RE.search(text):
                errors.append(
                    f"local_path_leak_in:{info.filename}"
                )

        # 6. release_gate.json boolean fields and log references
        gate_name = f"{root}/artifacts/proof/current/release_gate.json"
        if gate_name in name_set:
            gate_text = _read_text_member(zf, gate_name)
            if gate_text is None:
                errors.append("release_gate_json_unreadable")
            else:
                try:
                    gate = json.loads(gate_text)
                except json.JSONDecodeError:
                    errors.append("release_gate_json_invalid")
                    gate = None

                if gate is not None:
                    for field in REQUIRED_GATE_BOOLEAN_FIELDS:
                        if not isinstance(gate.get(field), bool):
                            errors.append(
                                f"release_gate_missing_bool_field:{field}"
                            )

                    checks = gate.get("checks", [])
                    if isinstance(checks, list):
                        for check in checks:
                            if not isinstance(check, dict):
                                continue
                            log_path = check.get("log_path")
                            if not isinstance(log_path, str):
                                continue
                            normalized = log_path.replace("\\", "/")
                            if not normalized.startswith(
                                "artifacts/proof/current/"
                            ):
                                continue
                            if f"{root}/{normalized}" not in name_set:
                                errors.append(
                                    "missing_claimed_log:"
                                    f"{check.get('name','?')}:"
                                    f"{normalized}"
                                )

    cleanroom_pass = not errors
    return {
        "cleanroom_pass": cleanroom_pass,
        "errors": errors,
        "warnings": warnings,
        "archive": str(archive),
        "root": locals().get("root"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        default=str(DEFAULT_ARCHIVE),
        help="Path to the release archive ZIP",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print JSON result",
    )
    args = parser.parse_args()

    result = run_cleanroom_test(Path(args.archive))

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if result["cleanroom_pass"] else "FAIL"
        print(f"cleanroom_release_test: {status}")
        for err in result["errors"]:
            print(f"  ERROR: {err}")
        for warn in result["warnings"]:
            print(f"  WARN:  {warn}")

    return 0 if result["cleanroom_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
