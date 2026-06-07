#!/usr/bin/env bash
# run_full_validation.sh — end-to-end validation orchestrator
#
# Implements the 21-step validation plan for JUDGE_ATLASX-main, covering:
#   A  ZIP safety check (optional)
#   B  Runtime versions
#   C  Source snapshot validity
#   D  Prove archive is NOT a final release (expected-fail phase)
#   E  Clean proof directory
#   F  Evidence verification proof
#   G  Full proof gate  (make proof)
#   H  Mandatory artifact check
#   I  Strict validators
#   J  Archive build
#   K  Archive hygiene (forbidden-file check)
#   L  Archive validation
#   M  Handoff consistency
#   N  Final 24-item checklist
#
# Usage:
#   bash scripts/run_full_validation.sh [OPTIONS]
#
# Options:
#   --source-zip <path>       Run phase A ZIP safety check against this file
#   --skip-docker             Skip phases/steps that require Docker
#   --source-snapshot         Validate source snapshot only
#   --final-archive           Validate only dist/JUDGE_ATLAS-main-final.zip
#   --source-snapshot-only    Stop after phase D (validate source snapshot only)
#   --proof-only              Skip A-D; run G onwards assuming proof is fresh
#   -h, --help                Show this help
#
# Exit codes:
#   0  All required phases passed
#   1  One or more phases failed (summary printed)
#   2  Usage error

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve repo root
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
SOURCE_ZIP=""
SKIP_DOCKER=false
SOURCE_SNAPSHOT=false
FINAL_ARCHIVE=false
PROOF_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-zip)
      SOURCE_ZIP="$2"; shift 2 ;;
    --skip-docker)
      SKIP_DOCKER=true; shift ;;
    --source-snapshot)
      SOURCE_SNAPSHOT=true; shift ;;
    --final-archive)
      FINAL_ARCHIVE=true; shift ;;
    --source-snapshot-only)
      SOURCE_SNAPSHOT=true; shift ;;
    --proof-only)
      PROOF_ONLY=true; shift ;;
    -h|--help)
      sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if "${SOURCE_SNAPSHOT}" && "${FINAL_ARCHIVE}"; then
  echo "ERROR: choose either --source-snapshot or --final-archive, not both" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
BOLD="\033[1m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

PHASE_RESULTS=()   # "PHASE_NAME:PASS" or "PHASE_NAME:FAIL:reason"
OVERALL_EXIT=0
STARTED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
SOURCE_REQUIRED_EXIT=0

_pass() {
  local phase="$1"
  echo -e "${GREEN}[PASS]${RESET} ${phase}"
  PHASE_RESULTS+=("${phase}:PASS")
}

_fail() {
  local phase="$1"
  local reason="${2:-}"
  echo -e "${RED}[FAIL]${RESET} ${phase}${reason:+ — ${reason}}"
  PHASE_RESULTS+=("${phase}:FAIL:${reason}")
  OVERALL_EXIT=1
}

_source_fail() {
  local phase="$1"
  local reason="${2:-}"
  SOURCE_REQUIRED_EXIT=1
  _fail "${phase}" "${reason}"
}

_skip() {
  local phase="$1"
  local reason="${2:-}"
  echo -e "${YELLOW}[SKIP]${RESET} ${phase}${reason:+ — ${reason}}"
  PHASE_RESULTS+=("${phase}:SKIP:${reason}")
}

_header() {
  echo ""
  echo -e "${BOLD}=== $* ===${RESET}"
}

_run_check() {
  # _run_check <phase_name> <cmd...>
  # Runs command; records PASS/FAIL.
  local phase="$1"; shift
  if "$@" 2>&1; then
    _pass "${phase}"
  else
    _fail "${phase}" "exit code $?"
  fi
}

_run_source_check() {
  local phase="$1"; shift
  if "$@" 2>&1; then
    _pass "${phase}"
  else
    _source_fail "${phase}" "exit code $?"
  fi
}

_run_check_cd() {
  # Like _run_check but runs in ROOT_DIR
  local phase="$1"; shift
  pushd "${ROOT_DIR}" >/dev/null
  if "$@" 2>&1; then
    _pass "${phase}"
    popd >/dev/null
  else
    local ec=$?
    popd >/dev/null
    _fail "${phase}" "exit code ${ec}"
  fi
}

_expected_fail() {
  # _expected_fail <phase_name> <cmd...>
  # Records PASS when the command FAILS (expected failure), FAIL when it succeeds.
  local phase="$1"; shift
  if "$@" >/dev/null 2>&1; then
    _fail "${phase}" "expected failure but command succeeded — archive may already contain proof logs"
  else
    _pass "${phase} (expected-fail confirmed)"
  fi
}

# ---------------------------------------------------------------------------
# Summary printer — defined early so early-exit paths can call it
# ---------------------------------------------------------------------------
_print_summary() {
  echo ""
  echo -e "${BOLD}=== Validation Summary ===${RESET}"
  echo "  Started : ${STARTED_AT}"
  echo "  Finished: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo ""
  local fail_count=0
  for entry in "${PHASE_RESULTS[@]+${PHASE_RESULTS[@]}}"; do
    result="${entry#*:}"
    result="${result%%:*}"
    if [[ "${result}" == "FAIL" ]]; then
      fail_count=$((fail_count + 1))
      reason="${entry##*:FAIL:}"
      echo -e "  ${RED}FAIL${RESET}  ${entry%%:*}  ${reason}"
    fi
  done
  if [[ "${fail_count}" -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}All phases passed. dist/JUDGE_ATLAS-main-final.zip is a valid self-verifying alpha.${RESET}"
  else
    echo -e "  ${RED}${BOLD}${fail_count} phase(s) failed. Archive is not ready for release.${RESET}"
  fi
  echo ""
}

# ---------------------------------------------------------------------------
# Phase A — ZIP safety check (optional)
# ---------------------------------------------------------------------------
if [[ -n "${SOURCE_ZIP}" ]] && ! "${PROOF_ONLY}" && ! "${FINAL_ARCHIVE}"; then
  _header "Phase A — ZIP Safety Check"
  if [[ ! -f "${SOURCE_ZIP}" ]]; then
    _source_fail "A.zip-exists" "file not found: ${SOURCE_ZIP}"
  else
    _pass "A.zip-exists"
    unsafe="$(zipinfo "${SOURCE_ZIP}" 2>/dev/null | grep -E '(^|/)\.\./' || true)"
    if [[ -n "${unsafe}" ]]; then
      _source_fail "A.zip-traversal-safe" "unsafe entries found: ${unsafe}"
    else
      _pass "A.zip-traversal-safe"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Phase B — Runtime versions
# ---------------------------------------------------------------------------
if ! "${PROOF_ONLY}" && ! "${FINAL_ARCHIVE}"; then
  _header "Phase B — Runtime Versions"
  pushd "${ROOT_DIR}" >/dev/null

  _run_source_check "B.check-runtime-versions" \
    python3 scripts/check_runtime_versions.py --root .

  _run_source_check "B.check-toolchain-versions" \
    python3 scripts/check_toolchain_versions.py --root .

  popd >/dev/null
fi

# ---------------------------------------------------------------------------
# Phase C — Source snapshot validity
# ---------------------------------------------------------------------------
if ! "${PROOF_ONLY}" && ! "${FINAL_ARCHIVE}"; then
  _header "Phase C — Source Snapshot Validity"
  pushd "${ROOT_DIR}" >/dev/null

  _run_source_check "C.compileall-backend" \
    python3 -m compileall -q backend/app scripts tests

  _run_source_check "C.source-registry-docs" \
    python3 scripts/check_source_registry_docs.py

  _run_source_check "C.status-consistency" \
    python3 scripts/check_status_consistency.py

  _run_source_check "C.no-local-paths" \
    python3 scripts/check_no_local_paths_in_release_proof.py

  _run_source_check "C.evidence-verification-standard" \
    python3 scripts/check_evidence_verification_standard.py

  popd >/dev/null
fi

# ---------------------------------------------------------------------------
# Phase D — Prove NOT a final release (expected-fail)
# ---------------------------------------------------------------------------
if ! "${PROOF_ONLY}" && ! "${FINAL_ARCHIVE}"; then
  _header "Phase D — Confirm Not a Final Release (Expected Failures)"
  echo "  These checks are expected to FAIL if proof logs are absent."
  echo "  A pass here means build is already a complete release."
  pushd "${ROOT_DIR}" >/dev/null

  _expected_fail "D.proof-logs-absent" \
    python3 scripts/check_required_proof_logs.py --strict-required-files

  _expected_fail "D.proof-consistency-absent" \
    python3 scripts/check_proof_consistency.py

  if "${SOURCE_SNAPSHOT}"; then
    if [[ -f "dist/JUDGE_ATLAS-main-final.zip" ]]; then
      echo "  Note: final archive exists; source-snapshot mode will not validate it."
    else
      echo "  Expected: final archive not present yet."
    fi
  elif [[ -n "${SOURCE_ZIP}" ]]; then
    _expected_fail "D.final-zip-invalid" \
      python3 scripts/validate_final_zip.py "${SOURCE_ZIP}"
  else
    _skip "D.final-zip-invalid" "--source-zip not provided"
  fi

  popd >/dev/null

  if "${SOURCE_SNAPSHOT}"; then
    _header "Source Snapshot Validation Complete"
    echo ""
    if [[ "${SOURCE_REQUIRED_EXIT}" -eq 0 ]]; then
      echo "Result: build is a valid SOURCE SNAPSHOT."
      echo "It is NOT a self-verifying release archive."
      echo "Run --final-archive after generating the canonical archive."
    else
      echo "Result: source snapshot validation FAILED."
      echo "Do not call this a valid source snapshot until required checks pass."
    fi
    echo ""
    _print_summary
    exit "${SOURCE_REQUIRED_EXIT}"
  fi
fi

if ! "${FINAL_ARCHIVE}"; then

# ---------------------------------------------------------------------------
# Phase E — Clean proof directory
# ---------------------------------------------------------------------------
_header "Phase E — Clean Proof Directory"
pushd "${ROOT_DIR}" >/dev/null
rm -rf artifacts/proof/current
mkdir -p artifacts/proof/current
_pass "E.proof-dir-clean"
popd >/dev/null

# ---------------------------------------------------------------------------
# Phase F — Evidence verification proof
# ---------------------------------------------------------------------------
_header "Phase F — Evidence Verification Proof"
pushd "${ROOT_DIR}" >/dev/null

_run_check "F.evidence-verification-script" \
  python3 scripts/check_evidence_verification_standard.py

_run_check "F.evidence-verification-pytest" \
  python3 -m pytest tests/proof/test_evidence_verification_standard.py -q

_run_check "F.proof-evidence-verification-make" \
  make proof-evidence-verification

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase G — Full proof gate
# ---------------------------------------------------------------------------
_header "Phase G — Full Proof Gate (make proof)"
if "${SKIP_DOCKER}"; then
  _skip "G.full-proof" "--skip-docker set; running release-proof-local only"
  pushd "${ROOT_DIR}" >/dev/null
  _run_check "G.release-proof-local" make release-proof-local
  popd >/dev/null
else
  pushd "${ROOT_DIR}" >/dev/null
  _run_check "G.full-proof" make proof
  popd >/dev/null
fi

# ---------------------------------------------------------------------------
# Phase H — Mandatory artifact check
# ---------------------------------------------------------------------------
_header "Phase H — Mandatory Proof Artifacts"
pushd "${ROOT_DIR}" >/dev/null

MANDATORY_FILES=(
  "artifacts/proof/current/release_gate.json"
  "artifacts/proof/current/proof_manifest.json"
  "artifacts/proof/current/required_log_index.json"
  "artifacts/proof/current/release_readiness.md"
  "artifacts/proof/current/REPAIR_REPORT.md"
  "artifacts/proof/current/source_registry_status.json"
)

for f in "${MANDATORY_FILES[@]}"; do
  if [[ -f "${f}" ]]; then
    _pass "H.exists:${f}"
  else
    _fail "H.exists:${f}" "file missing"
  fi
done

log_count="$(find artifacts/proof/current -name "*.log" | wc -l | tr -d ' ')"
if [[ "${log_count}" -gt 0 ]]; then
  _pass "H.proof-logs-present (${log_count} logs)"
else
  _fail "H.proof-logs-present" "no .log files in artifacts/proof/current"
fi

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase I — Strict validators
# ---------------------------------------------------------------------------
_header "Phase I — Strict Validators"
pushd "${ROOT_DIR}" >/dev/null

_run_check "I.check-required-proof-logs" \
  python3 scripts/check_required_proof_logs.py --strict-required-files

_run_check "I.check-proof-consistency" \
  python3 scripts/check_proof_consistency.py

_run_check "I.check-proof-freshness" \
  python3 scripts/check_proof_freshness.py

_run_check "I.check-no-local-paths" \
  python3 scripts/check_no_local_paths_in_release_proof.py

_run_check "I.check-source-registry-docs" \
  python3 scripts/check_source_registry_docs.py

_run_check "I.check-status-consistency" \
  python3 scripts/check_status_consistency.py

_run_check "I.check-evidence-verification" \
  python3 scripts/check_evidence_verification_standard.py

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase J — Archive build
# ---------------------------------------------------------------------------
_header "Phase J — Build Canonical Release Archive"
pushd "${ROOT_DIR}" >/dev/null
mkdir -p dist

_run_check "J.package-and-validate" \
  bash scripts/package_and_validate_release_archive.sh \
    --archive-path dist/JUDGE_ATLAS-main-final.zip \
    --package-root-name JUDGE_ATLAS-main

popd >/dev/null

fi

# ---------------------------------------------------------------------------
# Phase K — Archive hygiene
# ---------------------------------------------------------------------------
_header "Phase K — Archive Hygiene (Forbidden Files)"
pushd "${ROOT_DIR}" >/dev/null

ARCHIVE="dist/JUDGE_ATLAS-main-final.zip"

if [[ ! -f "${ARCHIVE}" ]]; then
  _fail "K.archive-exists" "dist/JUDGE_ATLAS-main-final.zip not found"
else
  _pass "K.archive-exists"

  forbidden="$(zipinfo "${ARCHIVE}" 2>/dev/null \
    | grep -E '(^|/)(\.env|\.env\.|\.kilo|THE-JUDGE\.sln|node_modules/|\.venv/|\.next/|__pycache__/|\.pytest_cache/|\.DS_Store)' \
    || true)"

  if [[ -n "${forbidden}" ]]; then
    _fail "K.no-forbidden-files" "found: ${forbidden}"
  else
    _pass "K.no-forbidden-files"
  fi

  proof_logs="$(zipinfo "${ARCHIVE}" 2>/dev/null \
    | grep -c 'artifacts/proof/current/.*\.log' || true)"
  if [[ "${proof_logs}" -gt 0 ]]; then
    _pass "K.proof-logs-in-archive (${proof_logs} logs)"
  else
    _fail "K.proof-logs-in-archive" "no proof .log files inside ZIP"
  fi
fi

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase L — Archive validation
# ---------------------------------------------------------------------------
_header "Phase L — Archive Validation"
pushd "${ROOT_DIR}" >/dev/null

_run_check "L.validate-final-zip" \
  python3 scripts/validate_final_zip.py dist/JUDGE_ATLAS-main-final.zip

_run_check "L.check-release-surface" \
  python3 scripts/check_release_surface.py \
    --archive dist/JUDGE_ATLAS-main-final.zip

_run_check "L.verify-archive-proof-freshness" \
  python3 scripts/verify_archive_proof_freshness.py \
    --archive dist/JUDGE_ATLAS-main-final.zip

_run_check "L.validate-extracted-release" \
  python3 scripts/validate_extracted_release.py \
    --archive dist/JUDGE_ATLAS-main-final.zip \
    --expected-root JUDGE_ATLAS-main

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase M — Handoff consistency
# ---------------------------------------------------------------------------
_header "Phase M — Handoff Consistency"
pushd "${ROOT_DIR}" >/dev/null

_run_check "M.render-proof-status-docs" \
  python3 scripts/render_proof_status_docs.py

_run_check "M.check-release-handoff-consistency" \
  python3 scripts/check_release_handoff_consistency.py \
    --archive dist/JUDGE_ATLAS-main-final.zip

popd >/dev/null

# ---------------------------------------------------------------------------
# Phase N — Final 24-item checklist
# ---------------------------------------------------------------------------
_header "Phase N — Final 24-Item Checklist"
pushd "${ROOT_DIR}" >/dev/null

CHECKLIST_PASS=0
CHECKLIST_FAIL=0

_check_item() {
  local num="$1"
  local label="$2"
  local result="$3"   # "pass" or "fail"
  if [[ "${result}" == "pass" ]]; then
    echo -e "  ${GREEN}[✓]${RESET} ${num}. ${label}"
    CHECKLIST_PASS=$((CHECKLIST_PASS + 1))
  else
    echo -e "  ${RED}[✗]${RESET} ${num}. ${label}"
    CHECKLIST_FAIL=$((CHECKLIST_FAIL + 1))
    OVERALL_EXIT=1
  fi
}

_file_check() {
  [[ -f "$1" ]] && echo "pass" || echo "fail"
}

_cmd_check() {
  "$@" >/dev/null 2>&1 && echo "pass" || echo "fail"
}

_check_item  1 "Evidence verification proof passes" \
  "$(_cmd_check python3 scripts/check_evidence_verification_standard.py)"

_check_item  2 "Source registry proof passes" \
  "$(_cmd_check python3 scripts/check_source_registry_docs.py)"

_check_item  3 "release_gate.json exists" \
  "$(_file_check artifacts/proof/current/release_gate.json)"

_check_item  4 "proof_manifest.json exists" \
  "$(_file_check artifacts/proof/current/proof_manifest.json)"

_check_item  5 "required_log_index.json exists" \
  "$(_file_check artifacts/proof/current/required_log_index.json)"

_check_item  6 "release_readiness.md exists" \
  "$(_file_check artifacts/proof/current/release_readiness.md)"

_check_item  7 "REPAIR_REPORT.md exists" \
  "$(_file_check artifacts/proof/current/REPAIR_REPORT.md)"

_check_item  8 "artifacts/proof/current contains real .log files" \
  "$([ "$(find artifacts/proof/current -name '*.log' | wc -l)" -gt 0 ] && echo pass || echo fail)"

_check_item  9 "check_required_proof_logs.py passes" \
  "$(_cmd_check python3 scripts/check_required_proof_logs.py --strict-required-files)"

_check_item 10 "check_proof_consistency.py passes" \
  "$(_cmd_check python3 scripts/check_proof_consistency.py)"

_check_item 11 "check_proof_freshness.py passes" \
  "$(_cmd_check python3 scripts/check_proof_freshness.py)"

_check_item 12 "check_status_consistency.py passes" \
  "$(_cmd_check python3 scripts/check_status_consistency.py)"

_check_item 13 "check_release_handoff_consistency.py passes" \
  "$(_cmd_check python3 scripts/check_release_handoff_consistency.py \
      --archive dist/JUDGE_ATLAS-main-final.zip)"

_check_item 14 "dist/JUDGE_ATLAS-main-final.zip exists" \
  "$(_file_check dist/JUDGE_ATLAS-main-final.zip)"

_check_item 15 "ZIP root is JUDGE_ATLAS-main/" \
  "$( (zipinfo dist/JUDGE_ATLAS-main-final.zip 2>/dev/null || true) \
      | grep -qE 'JUDGE_ATLAS-main/' && echo pass || echo fail)"

_check_item 16 "Final ZIP contains proof .log files" \
  "$([ "$(zipinfo dist/JUDGE_ATLAS-main-final.zip 2>/dev/null \
        | grep -c 'artifacts/proof/current/.*\.log' || true)" -gt 0 ] \
      && echo pass || echo fail)"

_check_item 17 "Final ZIP contains no .env files" \
  "$([ -z "$(zipinfo dist/JUDGE_ATLAS-main-final.zip 2>/dev/null \
      | grep -E '(^|/)\.env($|\.)' || true)" ] && echo pass || echo fail)"

_check_item 18 "Final ZIP contains no .kilo directory" \
  "$([ -z "$(zipinfo dist/JUDGE_ATLAS-main-final.zip 2>/dev/null \
      | grep -E '(^|/)\.kilo/' || true)" ] && echo pass || echo fail)"

_check_item 19 "Final ZIP excludes THE-JUDGE.sln" \
  "$([ -z "$(zipinfo dist/JUDGE_ATLAS-main-final.zip 2>/dev/null \
      | grep -F 'THE-JUDGE.sln' || true)" ] && echo pass || echo fail)"

_check_item 20 "validate_final_zip.py passes" \
  "$(_cmd_check python3 scripts/validate_final_zip.py \
      dist/JUDGE_ATLAS-main-final.zip)"

_check_item 21 "check_release_surface.py passes" \
  "$(_cmd_check python3 scripts/check_release_surface.py \
      --archive dist/JUDGE_ATLAS-main-final.zip)"

_check_item 22 "verify_archive_proof_freshness.py passes" \
  "$(_cmd_check python3 scripts/verify_archive_proof_freshness.py \
      --archive dist/JUDGE_ATLAS-main-final.zip)"

_check_item 23 "validate_extracted_release.py passes" \
  "$(_cmd_check python3 scripts/validate_extracted_release.py \
      --archive dist/JUDGE_ATLAS-main-final.zip \
      --expected-root JUDGE_ATLAS-main)"

_check_item 24 "Upload artifact is dist/JUDGE_ATLAS-main-final.zip, not source snapshot" \
  "$(_file_check dist/JUDGE_ATLAS-main-final.zip)"

echo ""
echo "  Checklist: ${CHECKLIST_PASS}/24 passed, ${CHECKLIST_FAIL} failed"

popd >/dev/null

_print_summary
exit "${OVERALL_EXIT}"
