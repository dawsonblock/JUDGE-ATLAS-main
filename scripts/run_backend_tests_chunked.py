#!/usr/bin/env python3
"""Run backend pytest in deterministic chunks with merged status output."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s\"'`]+"),
    re.compile(r"/home/[^\s\"'`]+"),
    re.compile(r"/private/[^\s\"'`]+"),
    re.compile(r"[A-Za-z]:\\[^\s\"'`]+"),
)


def _redact_local_paths_in_text(text: str) -> str:
    redacted = text
    for pattern in LOCAL_PATH_PATTERNS:
        redacted = pattern.sub("[REDACTED_LOCAL_PATH]", redacted)
    return redacted


def _run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _list_tests(tests_root: Path, repo_root: Path) -> list[str]:
    files = sorted(tests_root.rglob("test_*.py"))
    return [
        str(path.relative_to(repo_root)).replace("\\", "/")
        for path in files
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--tests-root",
        default="backend/app/tests",
        help="Root directory containing backend tests",
    )
    parser.add_argument(
        "--collect-log",
        default="artifacts/proof/current/backend_pytest_collect.log",
        help="Collect-only pytest log path",
    )
    parser.add_argument(
        "--status-json",
        default="artifacts/proof/current/backend_pytest_chunked_status.json",
        help="Chunked runner status JSON output",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=40,
        help="Number of test files per pytest invocation",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Test file path to exclude (repeatable)",
    )
    parser.add_argument(
        "--junitxml-output",
        default="",
        help="Path to write merged JUnit XML (empty = skip)",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    tests_root = (repo_root / args.tests_root).resolve()
    collect_log = (repo_root / args.collect_log).resolve()
    status_json = (repo_root / args.status_json).resolve()

    if not tests_root.is_dir():
        print(f"ERROR: tests root not found: {tests_root}")
        return 2
    if args.batch_size <= 0:
        print("ERROR: --batch-size must be > 0")
        return 2

    ignored = {
        str((repo_root / item).resolve().relative_to(repo_root)).replace(
            "\\", "/"
        )
        for item in args.ignore
    }
    test_files = [
        p for p in _list_tests(tests_root, repo_root) if p not in ignored
    ]

    env = os.environ.copy()

    collect_cmd = [
        sys.executable,
        "-m",
        "pytest",
        args.tests_root,
        "--collect-only",
        "--import-mode=importlib",
        "-q",
    ]
    collect_started = _utc_now()
    collect_result = _run(collect_cmd, repo_root, env)
    collect_finished = _utc_now()
    collect_stdout = _redact_local_paths_in_text(collect_result.stdout)
    collect_stderr = _redact_local_paths_in_text(collect_result.stderr)
    collect_text = (
        f"[backend_pytest_collect] started_at={collect_started}\n"
        f"[backend_pytest_collect] command={' '.join(collect_cmd)}\n"
        f"{collect_stdout}"
        f"{collect_stderr}"
        f"\n[backend_pytest_collect] finished_at={collect_finished}\n"
        f"[backend_pytest_collect] exit_code={collect_result.returncode}\n"
    )
    _write(collect_log, collect_text)

    if collect_result.returncode != 0:
        print(collect_text, end="")
        _write(
            status_json,
            json.dumps(
                {
                    "started_at": collect_started,
                    "finished_at": collect_finished,
                    "collect_exit_code": collect_result.returncode,
                    "batch_exit_code": None,
                    "batches": [],
                    "status": "FAIL",
                },
                indent=2,
            )
            + "\n",
        )
        return collect_result.returncode

    if not test_files:
        _write(
            status_json,
            json.dumps(
                {
                    "started_at": collect_started,
                    "finished_at": collect_finished,
                    "collect_exit_code": 0,
                    "batch_exit_code": 0,
                    "batches": [],
                    "status": "PASS",
                    "note": "No test files discovered",
                },
                indent=2,
            )
            + "\n",
        )
        print("No backend test files discovered; treating as pass.")
        return 0

    total_batches = int(math.ceil(len(test_files) / args.batch_size))
    batches: list[dict[str, object]] = []
    merged_lines: list[str] = []
    batch_exit_code = 0
    batch_junit_paths: list[Path] = []

    for idx in range(total_batches):
        start = idx * args.batch_size
        end = start + args.batch_size
        batch_files = test_files[start:end]

        batch_junit: list[str] = []
        if args.junitxml_output:
            batch_xml_path = (
                repo_root
                / f"artifacts/proof/current/backend_pytest_batch_{idx + 1}.xml"
            )
            batch_junit = [f"--junitxml={batch_xml_path}"]
            batch_junit_paths.append(batch_xml_path)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--import-mode=importlib",
            "-x",
            "--tb=short",
            "-q",
            *batch_junit,
            *batch_files,
        ]
        started_at = _utc_now()
        result = _run(cmd, repo_root, env)
        finished_at = _utc_now()

        batches.append(
            {
                "index": idx + 1,
                "started_at": started_at,
                "finished_at": finished_at,
                "exit_code": result.returncode,
                "file_count": len(batch_files),
                "first_file": batch_files[0],
                "last_file": batch_files[-1],
            }
        )

        merged_lines.append(
            "===== BATCH "
            f"{idx + 1}/{total_batches} "
            f"files={len(batch_files)} "
            f"exit={result.returncode} ====="
        )
        merged_lines.append("COMMAND: " + " ".join(cmd))
        merged_lines.append(
            _redact_local_paths_in_text(result.stdout).rstrip()
        )
        merged_lines.append(
            _redact_local_paths_in_text(result.stderr).rstrip()
        )
        merged_lines.append("")

        if result.returncode != 0:
            batch_exit_code = result.returncode
            break

    status_payload = {
        "started_at": collect_started,
        "finished_at": _utc_now(),
        "collect_exit_code": 0,
        "batch_exit_code": batch_exit_code,
        "batch_size": args.batch_size,
        "discovered_files": len(test_files),
        "batches": batches,
        "status": "PASS" if batch_exit_code == 0 else "FAIL",
    }
    _write(status_json, json.dumps(status_payload, indent=2) + "\n")

    print(
        "[backend_pytest_chunked] collect_log="
        + str(collect_log.relative_to(repo_root))
    )
    print(
        "[backend_pytest_chunked] status_json="
        + str(status_json.relative_to(repo_root))
    )
    print("\n".join(merged_lines).rstrip())

    if args.junitxml_output and batch_junit_paths:
        _merge_junit_xml(batch_junit_paths, repo_root / args.junitxml_output)

    return batch_exit_code


def _merge_junit_xml(batch_paths: list[Path], output: Path) -> None:
    """Merge per-batch JUnit XML files into one combined testsuite."""
    merged = ET.Element("testsuites")
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    for path in batch_paths:
        if not path.exists():
            continue
        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError:
            continue
        suites = (
            list(root.iter("testsuite"))
            if root.tag != "testsuite"
            else [root]
        )
        for suite in suites:
            total_tests += int(suite.get("tests", 0))
            total_failures += int(suite.get("failures", 0))
            total_errors += int(suite.get("errors", 0))
            total_skipped += int(suite.get("skipped", 0))
            merged.append(suite)
        path.unlink(missing_ok=True)

    merged.set("tests", str(total_tests))
    merged.set("failures", str(total_failures))
    merged.set("errors", str(total_errors))
    merged.set("skipped", str(total_skipped))

    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(merged).write(
        str(output), encoding="unicode", xml_declaration=True
    )


if __name__ == "__main__":
    raise SystemExit(main())
