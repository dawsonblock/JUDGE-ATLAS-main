#!/usr/bin/env python3
"""Aggregate status-consistency checks for release truth alignment."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


CHECKS = (
    (
        "verify_status_consistency",
        ["python3", "scripts/verify_status_consistency.py", "--root", "."],
    ),
    (
        "check_status_truth_consistency",
        [
            "python3",
            "scripts/check_status_truth_consistency.py",
            "--root",
            ".",
        ],
    ),
)


def _dynamic_checks(
    repo_root: Path,
    *,
    include_handoff_consistency: bool,
) -> tuple[tuple[str, list[str]], ...]:
    checks: list[tuple[str, list[str]]] = list(CHECKS)
    canonical_archive = repo_root / "dist" / "JUDGE_ATLAS-main-final.zip"
    if include_handoff_consistency and canonical_archive.is_file():
        checks.append(
            (
                "check_release_handoff_consistency",
                [
                    "python3",
                    "scripts/check_release_handoff_consistency.py",
                    "--root",
                    ".",
                    "--handoff",
                    "FINAL_RELEASE_HANDOFF.md",
                    "--archive",
                    str(canonical_archive),
                ],
            )
        )
    return tuple(checks)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    cp = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(
        part for part in (cp.stdout.strip(), cp.stderr.strip()) if part
    )
    return cp.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--check-handoff-consistency",
        action="store_true",
        help=(
            "Include FINAL_RELEASE_HANDOFF vs canonical archive consistency "
            "check when dist/JUDGE_ATLAS-main-final.zip exists"
        ),
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    failures: list[tuple[str, int, str]] = []

    for name, cmd in _dynamic_checks(
        repo_root,
        include_handoff_consistency=args.check_handoff_consistency,
    ):
        rc, output = _run(cmd, cwd=repo_root)
        if rc != 0:
            failures.append((name, rc, output))

    if failures:
        print(f"STATUS_CONSISTENCY: FAIL ({len(failures)} checks failed)")
        for name, rc, output in failures:
            print(f"- {name}: rc={rc}")
            if output:
                print(output)
        return 1

    print("STATUS_CONSISTENCY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
