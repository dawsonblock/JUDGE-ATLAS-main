#!/usr/bin/env python3
"""Fail if any proof-input file was modified after the release_gate.json was generated.

This is a companion to check_proof_freshness.py.  While freshness checks
verify hash correctness, this script verifies time-ordering: no tracked file
should have an mtime newer than the gate's generated_at_utc timestamp.

A violation means the proof was generated on stale inputs — the gate's
claims do not reflect the current state of the codebase.

Usage::

    python3 scripts/check_no_post_proof_mutation.py
    python3 scripts/check_no_post_proof_mutation.py --root /path/to/repo
    python3 scripts/check_no_post_proof_mutation.py --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import proof-input discovery from the freshness module.
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT_DEFAULT = _SCRIPTS_DIR.parent


def _load_freshness_module():
    import importlib.util
    mod_path = _SCRIPTS_DIR / "check_proof_freshness.py"
    spec = importlib.util.spec_from_file_location("check_proof_freshness", str(mod_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load check_proof_freshness from {mod_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_iso8601(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def check_no_post_proof_mutation(
    repo_root: Path,
    *,
    strict: bool = False,
    slack_seconds: float = 5.0,
) -> tuple[str, list[str]]:
    """Return (status, violations) where status is 'PASS' or 'FAIL'.

    Args:
        repo_root: Repository root directory.
        strict: If True, treat warnings as failures.
        slack_seconds: Clock-skew allowance in seconds (default 5).

    Returns:
        Tuple of (status_str, list_of_violation_messages).
    """
    gate_path = (
        repo_root / "artifacts" / "proof" / "current" / "release_gate.json"
    )
    if not gate_path.exists():
        return "FAIL", [f"missing: {gate_path.relative_to(repo_root).as_posix()}"]

    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    generated_at_str = gate.get("generated_at_utc") or gate.get("generated_at")
    if not generated_at_str:
        return "FAIL", ["release_gate.json missing generated_at_utc field"]

    try:
        gate_dt = _parse_iso8601(generated_at_str)
    except (ValueError, TypeError) as exc:
        return "FAIL", [f"release_gate.json has unparseable generated_at_utc: {exc}"]

    gate_epoch = gate_dt.timestamp()

    freshness_mod = _load_freshness_module()
    tracked_files = freshness_mod.discover_proof_input_files(repo_root)

    violations: list[str] = []
    warnings: list[str] = []

    for rel in tracked_files:
        abs_path = repo_root / rel
        if not abs_path.is_file():
            continue
        mtime = abs_path.stat().st_mtime
        if mtime > gate_epoch + slack_seconds:
            mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            delta = mtime - gate_epoch
            msg = (
                f"post-proof mutation: {rel} "
                f"(mtime={mtime_dt.isoformat()} "
                f"gate={gate_dt.isoformat()} "
                f"delta=+{delta:.1f}s)"
            )
            violations.append(msg)

    if violations:
        return "FAIL", violations

    if warnings and strict:
        return "FAIL", warnings

    return "PASS", []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--slack-seconds",
        type=float,
        default=5.0,
        help="Clock-skew allowance in seconds before a newer mtime is flagged (default 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable output",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    if not repo_root.is_dir():
        print(f"ERROR: root is not a directory: {repo_root}", file=sys.stderr)
        return 2

    status, violations = check_no_post_proof_mutation(
        repo_root,
        strict=args.strict,
        slack_seconds=args.slack_seconds,
    )

    if args.json_output:
        print(json.dumps({"status": status, "violations": violations}, indent=2))
        return 0 if status == "PASS" else 1

    if status == "PASS":
        print("NO_POST_PROOF_MUTATION: PASS")
        return 0

    print("NO_POST_PROOF_MUTATION: FAIL")
    for v in violations:
        print(f"- {v}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
