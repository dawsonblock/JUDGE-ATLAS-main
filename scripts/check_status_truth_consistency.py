#!/usr/bin/env python3
"""Fail when human-authored status narratives contradict canonical release truth."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CANONICAL_RELEASE_GATE = Path("artifacts/proof/current/release_gate.json")
CANONICAL_RELEASE_READINESS = Path("artifacts/proof/current/release_readiness.md")

ROOT_STATUS_DOCS = (
    Path("STATUS.md"),
    Path("CURRENT_STATUS.md"),
    Path("REPAIR_STATUS.md"),
    Path("PROOF_STATUS.md"),
    Path("RELEASE_BLOCKERS.md"),
    Path("FINAL_RELEASE_HANDOFF.md"),
    Path("artifacts/proof/current/CURRENT_PROOF.md"),
    Path("artifacts/proof/current/CURRENT_ALPHA_STATUS.md"),
    Path("artifacts/proof/current/release_readiness.md"),
    Path("README.md"),
)

AUTHORITY_REQUIRED_DOCS = {
    Path("STATUS.md"),
    Path("CURRENT_STATUS.md"),
    Path("REPAIR_STATUS.md"),
    Path("PROOF_STATUS.md"),
    Path("RELEASE_BLOCKERS.md"),
    Path("FINAL_RELEASE_HANDOFF.md"),
    Path("README.md"),
}

REQUIRED_MATRIX_KEYS = (
    "alpha_ready",
    "production_ready",
    "public_release_safe",
    "ingestion_coverage",
    "AI_answering_enabled",
    "workflow_admin_enabled",
    "live_map_enabled",
)

PRODUCTION_WARNING = "Production-ready=false until all production gates pass."

PRODUCTION_TRUE_PATTERNS = (
    re.compile(r"\bproduction[_ -]?ready\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bproduction release is ready\b", re.IGNORECASE),
)

ALPHA_TRUE_PATTERNS = (
    re.compile(r"\balpha[_ -]?gate[_ -]?passed\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\balpha[_ -]?ready\s*[:=]\s*true\b", re.IGNORECASE),
)

RELEASE_CANDIDATE_TRUE_PATTERNS = (
    re.compile(r"\brelease[_ -]?candidate\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\balpha[_ -]?release[_ -]?candidate\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\brelease[- ]ready\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\bfinal release\s+ready\b", re.IGNORECASE),
)

ALPHA_FALSE_PATTERNS = (
    re.compile(r"\balpha[_ -]?gate[_ -]?passed\s*[:=]\s*false\b", re.IGNORECASE),
    re.compile(r"\balpha[_ -]?ready\s*[:=]\s*false\b", re.IGNORECASE),
    re.compile(r"\balpha\s+gate\s*[:=]\s*failed\b", re.IGNORECASE),
    re.compile(r"\balpha\s+proof\s+status\s*[:=]\s*fail(?:ed)?\b", re.IGNORECASE),
)

STALE_REPAIR_PATTERNS = (
    re.compile(r"\balpha[_ -]?gate[_ -]?passed\s*[:=]\s*false\b", re.IGNORECASE),
    re.compile(r"\balpha\s+gate\s*[:=]\s*failed\b", re.IGNORECASE),
)

# Known-wrong source count phrases that must never appear in status docs.
# Use regex boundaries so "6 runnable sources" does not match
# "7/26 runnable sources".
STALE_COUNT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?<![\d/])2/26\s+runnable\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])2\s+actively\s+runnable\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])5\s+enable-ready\s+sources\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])5\s+enable-ready\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])3\s+runnable\s+sources\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])4\s+runnable\s+sources\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])5\s+runnable\s+sources\b", re.IGNORECASE),
    re.compile(r"(?<![\d/])6\s+runnable\s+sources\b", re.IGNORECASE),
)

_STALE_COUNT_SKIP_DOCS = {
    "docs/history",
    "docs/proof",
    "artifacts/history",
    "artifacts/proof/current",
    ".git",
    "node_modules",
    ".venv",
    "external_reference",
    ".kilo",
    ".windsurf",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_release_gate(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"missing:{path.as_posix()}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid_json_object:{path.as_posix()}")
    return data


def _parse_readiness_bool(text: str, key: str) -> bool | None:
    match = re.search(rf"^\s*-\s*{re.escape(key)}\s*:\s*(true|false)\s*$", text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def _has_any_pattern(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _scan_stale_repair_status(root: Path) -> list[str]:
    errors: list[str] = []
    skip_parts = {
        ".git",
        "node_modules",
        ".venv",
        "docs/history",
        "docs/proof",
        "artifacts/history",
        "artifacts/proof/current",
        "external_reference",
        ".kilo/plans",
        ".kilo/worktrees",
        "FINAL_RELEASE_HANDOFF.md",
        "CURRENT_PROOF.md",
        "REPAIR_REPORT.md",
        "docs/CURRENT_ALPHA_STATUS.md",
    }

    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if any(rel == prefix or rel.startswith(prefix + "/") for prefix in skip_parts):
            continue
        text = _read_text(path)
        for idx, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in STALE_REPAIR_PATTERNS):
                errors.append(f"stale_repair_status_outside_history:{rel}:{idx}")
    return errors


def verify(root: Path) -> list[str]:
    errors: list[str] = []

    gate = _load_release_gate(root / CANONICAL_RELEASE_GATE)
    release_readiness_path = root / CANONICAL_RELEASE_READINESS
    if not release_readiness_path.exists():
        errors.append(f"missing:{CANONICAL_RELEASE_READINESS.as_posix()}")
        release_readiness_text = ""
    else:
        release_readiness_text = _read_text(release_readiness_path)

    alpha_gate_passed = gate.get("alpha_gate_passed")
    release_candidate = gate.get("release_candidate")
    production_ready = gate.get("production_ready")

    if not isinstance(alpha_gate_passed, bool):
        errors.append("release_gate_invalid:alpha_gate_passed_not_bool")
    if not isinstance(release_candidate, bool):
        errors.append("release_gate_invalid:release_candidate_not_bool")
    if not isinstance(production_ready, bool):
        errors.append("release_gate_invalid:production_ready_not_bool")

    readiness_production_ready = _parse_readiness_bool(release_readiness_text, "production_ready")
    if isinstance(production_ready, bool):
        if readiness_production_ready is None:
            errors.append("release_readiness_missing:production_ready")
        elif readiness_production_ready != production_ready:
            errors.append(
                "release_readiness_contradiction:production_ready_mismatch"
                f":gate={str(production_ready).lower()}"
                f":readiness={str(readiness_production_ready).lower()}"
            )

    if isinstance(alpha_gate_passed, bool):
        readiness_status_line = _parse_readiness_overall_status(release_readiness_text)
        if readiness_status_line is None:
            errors.append("release_readiness_missing:overall_status")
        elif alpha_gate_passed and not _is_alpha_pass_status(readiness_status_line):
            errors.append(
                "release_readiness_contradiction:overall_status_not_pass_while_alpha_passed"
            )
        elif (not alpha_gate_passed) and _is_alpha_pass_status(readiness_status_line):
            errors.append(
                "release_readiness_contradiction:overall_status_pass_while_alpha_failed"
            )

    for rel_path in ROOT_STATUS_DOCS:
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing:{rel_path.as_posix()}")
            continue
        text = _read_text(path)

        if (
            rel_path in AUTHORITY_REQUIRED_DOCS
            and "artifacts/proof/current/release_gate.json" not in text
        ):
            errors.append(f"missing_release_gate_authority:{rel_path.as_posix()}")

        if rel_path in {
            Path("STATUS.md"),
            Path("CURRENT_STATUS.md"),
            Path("REPAIR_STATUS.md"),
            Path("PROOF_STATUS.md"),
            Path("RELEASE_BLOCKERS.md"),
        }:
            if PRODUCTION_WARNING not in text:
                errors.append(f"missing_required_warning:{rel_path.as_posix()}")

        if rel_path in {Path("STATUS.md"), Path("CURRENT_STATUS.md")}:
            for key in REQUIRED_MATRIX_KEYS:
                if re.search(rf"^\s*-\s*{re.escape(key)}\s*:", text, re.MULTILINE) is None:
                    errors.append(f"missing_status_matrix_key:{rel_path.as_posix()}:{key}")

        if production_ready is False and _has_any_pattern(text, PRODUCTION_TRUE_PATTERNS):
            errors.append(f"production_truth_contradiction:{rel_path.as_posix()}:gate_false_doc_claims_true")

        if alpha_gate_passed is False and _has_any_pattern(text, ALPHA_TRUE_PATTERNS):
            errors.append(f"alpha_truth_contradiction:{rel_path.as_posix()}:gate_false_doc_claims_true")

        if alpha_gate_passed is True and _has_any_pattern(text, ALPHA_FALSE_PATTERNS):
            errors.append(f"alpha_truth_contradiction:{rel_path.as_posix()}:gate_true_doc_claims_false")

        if release_candidate is False and _has_any_pattern(text, RELEASE_CANDIDATE_TRUE_PATTERNS):
            errors.append(
                f"release_candidate_contradiction:{rel_path.as_posix()}:gate_false_doc_claims_true"
            )

    errors.extend(_scan_stale_repair_status(root))
    errors.extend(_scan_stale_count_phrases(root))

    return errors


def _scan_stale_count_phrases(root: Path) -> list[str]:
    """Detect known-wrong source count phrases in any doc outside history."""
    errors: list[str] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if any(
            rel.startswith(skip + "/") or rel == skip
            for skip in _STALE_COUNT_SKIP_DOCS
        ):
            continue
        try:
            text = _read_text(path)
        except OSError:
            continue
        for pattern in STALE_COUNT_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"stale_count_phrase:{rel}:{pattern.pattern!r}"
                )
    return errors


def _parse_readiness_overall_status(text: str) -> str | None:
    match = re.search(r"^\s*-\s*overall_status\s*:\s*([^\n]+)$", text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().lower()


def _is_alpha_pass_status(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {
        "pass",
        "passed",
        "alpha-pass",
        "alpha_pass",
        "self-verifying-alpha",
        "self_verifying_alpha",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    errors = verify(root)
    if errors:
        print("STATUS TRUTH CONSISTENCY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("STATUS TRUTH CONSISTENCY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())