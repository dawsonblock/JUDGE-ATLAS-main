#!/usr/bin/env python3
"""Render derived status docs from canonical proof artifacts.

This script is the single entry point for status doc refresh in packaging and
consistency flows.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


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
        "--archive",
        default="dist/JUDGE_ATLAS-main-final.zip",
        help="Canonical release archive path used for handoff generation",
    )
    parser.add_argument(
        "--skip-handoff",
        action="store_true",
        help="Skip FINAL_RELEASE_HANDOFF generation",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    archive_path = (repo_root / args.archive).resolve()

    steps: list[tuple[str, list[str]]] = [
        (
            "sync_status_docs_from_gate",
            ["python3", "scripts/sync_status_docs_from_gate.py", "--root", "."],
        ),
    ]

    if not args.skip_handoff and archive_path.is_file():
        steps.append(
            (
                "generate_release_handoff",
                [
                    "python3",
                    "scripts/generate_release_handoff.py",
                    "--root",
                    ".",
                    "--archive",
                    str(archive_path),
                    "--output",
                    "FINAL_RELEASE_HANDOFF.md",
                ],
            )
        )

    failures: list[tuple[str, int, str]] = []
    for name, cmd in steps:
        rc, output = _run(cmd, cwd=repo_root)
        if rc != 0:
            failures.append((name, rc, output))

    if failures:
        print(f"RENDER_PROOF_STATUS_DOCS: FAIL ({len(failures)} steps failed)")
        for name, rc, output in failures:
            print(f"- {name}: rc={rc}")
            if output:
                print(output)
        return 1

    print("RENDER_PROOF_STATUS_DOCS: PASS")
    if archive_path.is_file() and not args.skip_handoff:
        print("handoff_rendered=true")
    else:
        print("handoff_rendered=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
