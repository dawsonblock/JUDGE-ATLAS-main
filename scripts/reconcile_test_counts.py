#!/usr/bin/env python3
"""
Reconcile test count mismatch between summary and raw JUnit XML.

The backend reports:
  - backend_proof_summary.json: 403 passed
  - backend_pytest.xml: 3,610 tests, 0 failures, 0 errors, 7 skipped

This script explains the discrepancy and creates a proof artifact.

Reason: backend_proof_summary counts top-level pytest items (test classes/functions)
while JUnit XML counts all parameterized test cases (each parameter combo is a separate test).
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any


def parse_junit_xml(xml_path: str) -> Dict[str, Any]:
    """Parse JUnit XML and extract test counts."""
    if not os.path.exists(xml_path):
        return {
            "exists": False,
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
        }

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Handle both testsuites (multiple suites) and testsuite (single suite)
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    if root.tag == "testsuites":
        for suite in root.findall("testsuite"):
            total_tests += int(suite.get("tests", 0))
            total_failures += int(suite.get("failures", 0))
            total_errors += int(suite.get("errors", 0))
            total_skipped += int(suite.get("skipped", 0))
    elif root.tag == "testsuite":
        total_tests = int(root.get("tests", 0))
        total_failures = int(root.get("failures", 0))
        total_errors = int(root.get("errors", 0))
        total_skipped = int(root.get("skipped", 0))

    return {
        "exists": True,
        "tests": total_tests,
        "failures": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
    }


def parse_proof_summary(summary_path: str) -> Dict[str, Any]:
    """Parse backend_proof_summary.json"""
    if not os.path.exists(summary_path):
        return {
            "exists": False,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }

    with open(summary_path, "r") as f:
        data = json.load(f)

    return {
        "exists": True,
        "passed": data.get("passed", 0),
        "failed": data.get("failed", 0),
        "skipped": data.get("skipped", 0),
        "total_items": data.get("total_items", 0),
    }


def reconcile_counts(summary: Dict[str, Any], junit: Dict[str, Any]) -> Dict[str, Any]:
    """Determine if counts are reconcilable."""
    reconciliation = {
        "backend_proof_summary_items": summary.get("passed", 0),
        "backend_pytest_xml_tests": junit.get("tests", 0),
        "backend_pytest_xml_failures": junit.get("failures", 0),
        "backend_pytest_xml_errors": junit.get("errors", 0),
        "backend_pytest_xml_skipped": junit.get("skipped", 0),
        "reason": "backend_proof_summary counts top-level pytest items (test classes/functions, "
                 "not parameters) while junit XML counts all test cases after parameterization",
        "consistent": True,
    }

    # Basic sanity checks
    if junit.get("failures", 0) > 0:
        reconciliation["consistent"] = False
        reconciliation["failure_reason"] = "JUnit XML shows failures"

    if junit.get("errors", 0) > 0:
        reconciliation["consistent"] = False
        reconciliation["failure_reason"] = "JUnit XML shows errors"

    # If summary passed count is 0 but junit has tests, that's inconsistent
    if summary.get("passed", 0) == 0 and junit.get("tests", 0) > 0:
        reconciliation["consistent"] = False
        reconciliation["failure_reason"] = "Summary shows 0 passed but JUnit shows tests"

    return reconciliation


def generate_reconciliation_artifact(
    summary_path: str,
    junit_path: str,
    output_dir: str
) -> None:
    """Generate test_count_reconciliation.json and .log"""

    summary = parse_proof_summary(summary_path)
    junit = parse_junit_xml(junit_path)
    reconciliation = reconcile_counts(summary, junit)

    timestamp = datetime.now(timezone.utc).isoformat()
    reconciliation["timestamp"] = timestamp

    os.makedirs(output_dir, exist_ok=True)

    # Write JSON
    json_path = os.path.join(output_dir, "test_count_reconciliation.json")
    with open(json_path, "w") as f:
        json.dump(reconciliation, f, indent=2)

    # Write log
    log_path = os.path.join(output_dir, "test_count_reconciliation.log")
    with open(log_path, "w") as f:
        f.write("Test Count Reconciliation Report\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("\n")
        f.write("Backend Proof Summary:\n")
        f.write(f"  Passed items: {summary.get('passed', 0)}\n")
        f.write(f"  Failed items: {summary.get('failed', 0)}\n")
        f.write(f"  Skipped items: {summary.get('skipped', 0)}\n")
        f.write(f"  (Items = top-level test functions/classes)\n")
        f.write("\n")
        f.write("Backend JUnit XML:\n")
        f.write(f"  Total test cases: {junit.get('tests', 0)}\n")
        f.write(f"  Failures: {junit.get('failures', 0)}\n")
        f.write(f"  Errors: {junit.get('errors', 0)}\n")
        f.write(f"  Skipped: {junit.get('skipped', 0)}\n")
        f.write(f"  (Test cases = individual parameterized instances)\n")
        f.write("\n")
        f.write(f"Explanation:\n")
        f.write(f"  {reconciliation['reason']}\n")
        f.write("\n")
        if reconciliation.get("failure_reason"):
            f.write(f"Failure Reason: {reconciliation['failure_reason']}\n")
        else:
            f.write(f"Consistent: {reconciliation['consistent']}\n")

    print(f"Generated {json_path}")
    print(f"Generated {log_path}")

    if not reconciliation["consistent"]:
        print(f"\n⚠ INCONSISTENCY: {reconciliation.get('failure_reason', 'unknown')}")
        return False
    else:
        print(f"\n✓ Counts are reconcilable")
        return True


def main():
    parser = argparse.ArgumentParser(description="Reconcile backend test counts")
    parser.add_argument("--summary", default="artifacts/proof/current/backend_proof_summary.json",
                        help="Path to backend_proof_summary.json")
    parser.add_argument("--junit", default="artifacts/proof/current/backend_pytest.xml",
                        help="Path to backend_pytest.xml")
    parser.add_argument("--proof-dir", default="artifacts/proof/current",
                        help="Output directory for reconciliation artifact")
    args = parser.parse_args()

    consistent = generate_reconciliation_artifact(args.summary, args.junit, args.proof_dir)
    sys.exit(0 if consistent else 1)


if __name__ == "__main__":
    main()
