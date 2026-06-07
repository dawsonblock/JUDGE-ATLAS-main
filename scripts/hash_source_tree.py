#!/usr/bin/env python3
"""Compute deterministic source-tree hash for release freshness checks."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path

DEFAULT_INCLUDE = (
    "backend/**/*",
    "frontend/**/*",
    "scripts/**/*",
    "docs/**/*",
    "tests/**/*",
    "Makefile",
    "docker-compose.yml",
    "Dockerfile",
    "pyproject.toml",
    "package.json",
    "frontend/package.json",
    "backend/pyproject.toml",
    "backend/app/ingestion/sources/**/*",
    "artifacts/proof/current/source_registry_status.json",
)

DEFAULT_IGNORE_PREFIXES = (
    ".git/",
    "node_modules/",
    ".venv/",
    "dist/",
    "artifacts/proof/current/",
    "artifacts/tmp/",
)

DEFAULT_IGNORE_GLOBS = (
    "**/.env",
    "**/.env.*",
    "**/.next/**",
    "**/node_modules/**",
    "**/.venv/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/.git/**",
    "**/dist/**",
    "**/.DS_Store",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.db",
    "**/*.sqlite",
    "**/*.sqlite3",
    "**/*.log",
)


def _normalize(rel_path: str) -> str:
    return rel_path.replace("\\", "/")


def _is_ignored(rel_path: str) -> bool:
    norm = _normalize(rel_path)
    if any(norm.startswith(prefix) for prefix in DEFAULT_IGNORE_PREFIXES):
        return True
    segments = set(Path(norm).parts)
    if {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        ".next",
        "dist",
    } & segments:
        return True
    if any(fnmatch.fnmatch(norm, pattern) for pattern in DEFAULT_IGNORE_GLOBS):
        return True
    return False


def discover_files(repo_root: Path) -> list[str]:
    files: set[str] = set()
    for pattern in DEFAULT_INCLUDE:
        for candidate in repo_root.glob(pattern):
            if not candidate.is_file():
                continue
            rel = _normalize(str(candidate.relative_to(repo_root)))
            if _is_ignored(rel):
                continue
            files.add(rel)
    return sorted(files)


def compute_tree_hash(repo_root: Path, rel_files: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in rel_files:
        file_path = repo_root / rel
        if not file_path.is_file():
            continue
        size = file_path.stat().st_size
        digest.update(rel.encode("utf-8"))
        digest.update(b"\n")
        digest.update(str(size).encode("utf-8"))
        digest.update(b"\n")
        with file_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rel_files = discover_files(root)
    tree_hash = compute_tree_hash(root, rel_files)

    payload = {
        "source_tree_hash": tree_hash,
        "file_count": len(rel_files),
        "files": rel_files,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(tree_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
