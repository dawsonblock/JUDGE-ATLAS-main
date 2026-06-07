#!/usr/bin/env python3
"""Wrap any shell command and emit a minimal JUnit XML representing its result.

Useful for commands that produce no native JUnit output (e.g. bash scripts,
docker checks) so their results can be consumed by CI JUnit processors.

Usage::

    python3 scripts/wrap_as_junit.py \\
        --suite docker_runtime_preflight \\
        --xml artifacts/proof/current/docker_runtime_preflight.xml \\
        -- bash scripts/check_docker_runtime.sh
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_junit(
    output: Path,
    suite_name: str,
    test_name: str,
    elapsed: float,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> None:
    testsuites = ET.Element("testsuites")
    testsuite = ET.SubElement(
        testsuites,
        "testsuite",
        name=suite_name,
        tests="1",
        failures="0" if exit_code == 0 else "1",
        errors="0",
        skipped="0",
        time=f"{elapsed:.3f}",
    )
    testcase = ET.SubElement(
        testsuite,
        "testcase",
        name=test_name,
        classname=suite_name,
        time=f"{elapsed:.3f}",
    )
    if stdout.strip():
        sys_out = ET.SubElement(testcase, "system-out")
        sys_out.text = stdout[-4096:]
    if stderr.strip():
        sys_err = ET.SubElement(testcase, "system-err")
        sys_err.text = stderr[-4096:]
    if exit_code != 0:
        failure = ET.SubElement(
            testcase,
            "failure",
            message=f"exit_code={exit_code}",
            type="NonZeroExitCode",
        )
        failure.text = (
            f"Command exited with code {exit_code}\n"
            f"stderr: {stderr[-2048:]}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(testsuites).write(
        str(output), encoding="unicode", xml_declaration=True
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        required=True,
        help="JUnit testsuite name",
    )
    parser.add_argument(
        "--test",
        default="",
        help="JUnit testcase name (default: same as --suite)",
    )
    parser.add_argument(
        "--xml",
        required=True,
        help="Output path for JUnit XML",
    )
    parser.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command to run (after --)",
    )
    args = parser.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if not cmd:
        print("ERROR: no command specified after --", file=sys.stderr)
        return 2

    test_name = args.test or args.suite
    started = _utc_now()
    t0 = time.monotonic()

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.monotonic() - t0

    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    _write_junit(
        Path(args.xml),
        suite_name=args.suite,
        test_name=test_name,
        elapsed=elapsed,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    print(
        f"[wrap_as_junit] suite={args.suite} "
        f"exit={result.returncode} "
        f"elapsed={elapsed:.1f}s "
        f"xml={args.xml} "
        f"started={started}",
        file=sys.stderr,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
