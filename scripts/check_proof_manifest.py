#!/usr/bin/env python3
"""Validate proof_manifest.json against on-disk artifacts.

Supports validating from a repository root or from a built archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUIRED_LOGS: tuple[str, ...] = (
    "artifacts/proof/current/release_gate.log",
    "artifacts/proof/current/backend_pytest.log",
    "artifacts/proof/current/frontend_build.log",
    "artifacts/proof/current/docker_runtime_preflight.log",
    "artifacts/proof/current/proof_consistency_pytest.log",
    "artifacts/proof/current/archive_validation.log",
    ".validation_logs/docker_smoke.log",
    ".validation_logs/runtime_smoke.log",
)


def _load_manifest(repo_root: Path) -> dict:
    manifest_path = repo_root / "artifacts" / "proof" / "current" / "proof_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing proof manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_manifest_from_root(root: Path) -> dict:
    manifest_path = root / "artifacts" / "proof" / "current" / "proof_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing proof manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_logs_from_manifest(manifest: dict) -> list[str]:
    required_logs = manifest.get("required_logs")
    if isinstance(required_logs, list) and required_logs:
        filtered = [entry for entry in required_logs if isinstance(entry, str) and entry]
        if filtered:
            return filtered
    return list(DEFAULT_REQUIRED_LOGS)


def _entry_path(entry: dict) -> str | None:
    path = entry.get("path")
    if isinstance(path, str) and path:
        return path
    log_path = entry.get("log_path")
    if isinstance(log_path, str) and log_path:
        return log_path
    return None


def _resolve_archive_root(archive: Path, extract_dir: Path) -> Path:
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(extract_dir)
        candidates = [
            Path(name).parts[0]
            for name in zf.namelist()
            if name.endswith("artifacts/proof/current/proof_manifest.json")
        ]

    unique = sorted(set(candidates))
    if not unique:
        raise FileNotFoundError("archive_missing:artifacts/proof/current/proof_manifest.json")
    if len(unique) > 1:
        raise RuntimeError(f"archive_multiple_roots_with_manifest:{','.join(unique)}")
    return extract_dir / unique[0]


def _validate_manifest(root: Path, manifest: dict) -> tuple[list[str], list[str], list[str]]:
    required_logs = _required_logs_from_manifest(manifest)
    missing: list[str] = []
    empty: list[str] = []
    bad_entries: list[str] = []

    for rel_path in required_logs:
        path = root / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        if path.stat().st_size <= 0:
            empty.append(rel_path)

    proof_commands = manifest.get("proof_commands")
    if isinstance(proof_commands, list):
        for entry in proof_commands:
            if not isinstance(entry, dict):
                bad_entries.append("non_dict_entry")
                continue
            entry_path = _entry_path(entry)
            if not entry_path:
                bad_entries.append(f"missing_path:{entry.get('name', 'unknown')}")
                continue

            file_path = root / entry_path
            if not file_path.exists():
                bad_entries.append(f"missing_file:{entry_path}")
                continue
            if file_path.stat().st_size <= 0:
                bad_entries.append(f"empty_file:{entry_path}")
                continue

            if not isinstance(entry.get("required"), bool):
                bad_entries.append(f"missing_required_flag:{entry_path}")

            expected_size = entry.get("size_bytes")
            if not isinstance(expected_size, int):
                bad_entries.append(f"missing_size_bytes:{entry_path}")
            elif expected_size != file_path.stat().st_size:
                bad_entries.append(f"size_mismatch:{entry_path}")

            expected_hash = entry.get("sha256")
            if not isinstance(expected_hash, str) or not expected_hash:
                bad_entries.append(f"missing_sha256:{entry_path}")
            else:
                actual_hash = _sha256(file_path)
                if actual_hash != expected_hash:
                    bad_entries.append(f"sha256_mismatch:{entry_path}")

            if not (
                isinstance(entry.get("captured_at"), str)
                and entry.get("captured_at")
            ) and not (
                isinstance(entry.get("created_at"), str)
                and entry.get("created_at")
            ):
                bad_entries.append(f"missing_timestamp:{entry_path}")

            if not (
                isinstance(entry.get("command"), str)
                and entry.get("command")
            ) and not (
                isinstance(entry.get("proof_source"), str)
                and entry.get("proof_source")
            ):
                bad_entries.append(f"missing_command_or_source:{entry_path}")
    else:
        bad_entries.append("proof_commands_missing_or_invalid")

    return missing, empty, bad_entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root")
    parser.add_argument(
        "--archive",
        default=None,
        help="Validate proof manifest from an archive ZIP instead of the live repo tree",
    )
    args = parser.parse_args()

    archive = Path(args.archive).resolve() if args.archive else None

    try:
        if archive is None:
            root = Path(args.root).resolve()
            manifest = _load_manifest_from_root(root)
            mode = "repo"
            missing, empty, bad_entries = _validate_manifest(root, manifest)
        else:
            if not archive.exists() or not archive.is_file():
                raise FileNotFoundError(f"archive_not_found:{archive}")
            with tempfile.TemporaryDirectory() as tmp:
                extract_dir = Path(tmp)
                root = _resolve_archive_root(archive, extract_dir)
                manifest = _load_manifest_from_root(root)
                mode = "archive"
                missing, empty, bad_entries = _validate_manifest(root, manifest)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"CHECK_PROOF_MANIFEST: FAIL\n- {exc}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"CHECK_PROOF_MANIFEST: FAIL\n- invalid proof_manifest.json: {exc}")
        return 1

    if missing or empty or bad_entries:
        print("CHECK_PROOF_MANIFEST: FAIL")
        for rel_path in missing:
            print(f"- missing:{rel_path}")
        for rel_path in empty:
            print(f"- empty:{rel_path}")
        for rel_path in bad_entries:
            print(f"- bad:{rel_path}")
        return 1

    required_logs = _required_logs_from_manifest(manifest)
    print(f"CHECK_PROOF_MANIFEST: PASS ({mode})")
    for rel_path in required_logs:
        print(f"- ok:{rel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
