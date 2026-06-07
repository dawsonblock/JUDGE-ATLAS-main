#!/usr/bin/env python3
"""
Run a proof command and capture both .json summary and .log output.

Usage:
  python scripts/run_with_proof_log.py \
    --name backend_pytest \
    --log artifacts/proof/current/backend_pytest.log \
    --json artifacts/proof/current/backend_pytest_summary.json \
    -- pytest backend/app/tests
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_with_proof_log(
    name: str,
    log_path: str,
    json_path: str,
    command: list[str],
) -> bool:
    """Run command, capture output to log, generate summary JSON."""

    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)

    print(f"Running: {' '.join(command)}")
    print(f"Logging to: {log_path}")
    print(f"Summary: {json_path}")

    # Run command, capture output
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Write raw log
        with open(log_path, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)

        # Generate summary
        summary = {
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": " ".join(command),
            "return_code": result.returncode,
            "passed": result.returncode == 0,
            "log_path": log_path,
            "log_size": os.path.getsize(log_path),
            "stdout_lines": len(result.stdout.splitlines()),
            "stderr_lines": len(result.stderr.splitlines()),
        }

        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)

        # Verify log is non-empty
        if os.path.getsize(log_path) == 0:
            print(f"FAIL: Log file is empty: {log_path}")
            return False

        if result.returncode == 0:
            print(f"PASS: {name} (exit code 0)")
        else:
            print(f"FAIL: {name} (exit code {result.returncode})")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"FAIL: Command timed out after 300 seconds")
        with open(log_path, "w") as f:
            f.write("TIMEOUT: Command execution exceeded 300 seconds\n")
        return False
    except Exception as e:
        print(f"FAIL: Exception: {e}")
        with open(log_path, "w") as f:
            f.write(f"ERROR: {e}\n")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run command with proof logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", required=True, help="Proof name")
    parser.add_argument("--log", required=True, help="Output log file path")
    parser.add_argument("--json", required=True, help="Output JSON summary path")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run (after --)",
    )

    args = parser.parse_args()

    if not args.command or args.command[0] != "--":
        print("ERROR: Use -- to separate options from command")
        print("Example: ... -- pytest backend/app/tests")
        sys.exit(1)

    # Remove the -- separator
    command = args.command[1:]

    if not command:
        print("ERROR: No command specified after --")
        sys.exit(1)

    success = run_with_proof_log(args.name, args.log, args.json, command)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
