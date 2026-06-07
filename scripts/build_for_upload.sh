#!/usr/bin/env bash
set -euo pipefail

# Build the canonical archive after forcing strict proof regeneration.
# This script prevents the stale-proof bug: it NEVER reuses an existing
# archive unless --use-existing-proof is explicitly passed.
#
# Usage:
#   bash scripts/build_for_upload.sh          # strict mode: regenerate proof first
#   bash scripts/build_for_upload.sh --use-existing-proof  # advanced: skip proof regen

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL_ARCHIVE="${ROOT_DIR}/dist/JUDGE_ATLAS-main-final.zip"
UPLOAD_BASENAME="UPLOAD_THIS_JUDGE_ATLAS-main-final.zip"

USE_EXISTING_PROOF=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --use-existing-proof)
      USE_EXISTING_PROOF=true
      shift
      ;;
    --help|-h)
      echo "Usage: bash scripts/build_for_upload.sh [--use-existing-proof]"
      echo ""
      echo "  Default (strict): regenerates all proof before building archive."
      echo "  --use-existing-proof: skips proof regeneration (expert only)."
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1"
      echo "Run: bash scripts/build_for_upload.sh --help"
      exit 2
      ;;
  esac
done

# Try Desktop, fall back to repo root
if [[ -d "${HOME}/Desktop" ]]; then
    UPLOAD_TARGET="${HOME}/Desktop/${UPLOAD_BASENAME}"
elif [[ -d "${HOME}/desktop" ]]; then
    UPLOAD_TARGET="${HOME}/desktop/${UPLOAD_BASENAME}"
else
    UPLOAD_TARGET="${ROOT_DIR}/${UPLOAD_BASENAME}"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_bold() { echo -e "${BOLD}$*${NC}"; }

cd "${ROOT_DIR}"

# Step 1: strict proof regeneration (unless explicitly skipped)
if [[ "${USE_EXISTING_PROOF}" != "true" ]]; then
    log_bold "=== Phase 1: Strict Proof Regeneration ==="
    echo ""

    log_bold "1.1 Toolchain check"
    python3 scripts/check_toolchain_versions.py --root . || { log_fail "Toolchain check failed"; exit 1; }
    log_pass "Toolchain check passed"

    log_bold "1.2 Regenerating release gate"
    if python3 scripts/release_gate.py --out-dir artifacts/proof/current; then
        log_pass "release_gate.py completed (alpha gate passed)"
    else
        log_warn "release_gate.py completed (alpha gate blocked — archive will be marked blocked)"
    fi

    log_bold "1.3 Synchronizing status docs"
    python3 scripts/sync_status_docs_from_gate.py || { log_fail "sync_status_docs failed"; exit 1; }
    log_pass "Status docs synchronized"

    log_bold "1.4 Rendering proof status docs"
    python3 scripts/render_proof_status_docs.py --root . --skip-handoff || { log_fail "render_proof_status_docs failed"; exit 1; }
    log_pass "Proof status docs rendered"

    log_bold "1.4b Refreshing proof hash after status doc sync"
    python3 scripts/refresh_proof_hash.py --root . || { log_fail "hash refresh failed"; exit 1; }
    log_pass "Proof hash refreshed"

    log_bold "1.5 Checking proof freshness"
    python3 scripts/check_proof_freshness.py || { log_fail "check_proof_freshness failed"; exit 1; }
    python3 scripts/check_proof_freshness.py --strict-extra-files || { log_fail "check_proof_freshness --strict-extra-files failed"; exit 1; }
    log_pass "Proof freshness passed"

    log_bold "1.6 Checking proof consistency"
    python3 scripts/check_proof_consistency.py || { log_fail "check_proof_consistency failed"; exit 1; }
    log_pass "Proof consistency passed"

    log_bold "1.7 Checking required proof logs"
    python3 scripts/check_required_proof_logs.py --root . --strict-required-files || { log_fail "check_required_proof_logs failed"; exit 1; }
    log_pass "Required proof logs passed"

    log_bold "1.8 Checking single proof authority"
    python3 scripts/check_single_proof_authority.py --root . || { log_fail "check_single_proof_authority failed"; exit 1; }
    log_pass "Single proof authority passed"

    log_bold "1.9 Checking release gate"
    python3 scripts/check_release_gate.py --root . || { log_fail "check_release_gate failed"; exit 1; }
    log_pass "Release gate check passed"

    log_bold "1.10 Checking no local paths in release proof"
    python3 scripts/check_no_local_paths_in_release_proof.py --root . || { log_fail "check_no_local_paths failed"; exit 1; }
    log_pass "No local paths check passed"

    echo ""
    log_pass "=== Phase 1 Complete: All proof validators passed ==="
    echo ""
else
    log_warn "--use-existing-proof: SKIPPING strict proof regeneration"
    log_warn "This is dangerous. Only use if you are certain proof is fresh."
    echo ""
fi

# Step 2: build canonical archive
log_bold "=== Phase 2: Building Canonical Archive ==="
echo ""

# Always remove stale archive before building fresh
if [[ -f "${CANONICAL_ARCHIVE}" ]]; then
    rm -f "${CANONICAL_ARCHIVE}" "${CANONICAL_ARCHIVE}.sha256"
    log_warn "Removed stale archive: ${CANONICAL_ARCHIVE}"
fi

bash scripts/package_and_validate_release_archive.sh \
    --archive-path "${CANONICAL_ARCHIVE}" \
    --package-root-name JUDGE_ATLAS-main \
    --skip-release-gate \
    --skip-handoff-check \
    --skip-extracted-validation || { log_fail "package_and_validate_release_archive.sh failed"; exit 1; }

if [[ ! -f "${CANONICAL_ARCHIVE}" ]]; then
    log_fail "Failed to build canonical archive: ${CANONICAL_ARCHIVE}"
    exit 1
fi
log_pass "Canonical archive built: ${CANONICAL_ARCHIVE}"

# Step 3: copy to obvious location
cp -f "${CANONICAL_ARCHIVE}" "${UPLOAD_TARGET}"
log_pass "Copied canonical archive to: ${UPLOAD_TARGET}"

# Step 4: compute SHA-256
ARCHIVE_SHA256=""
if command -v sha256sum >/dev/null 2>&1; then
    ARCHIVE_SHA256=$(sha256sum "${CANONICAL_ARCHIVE}" | awk '{print $1}')
else
    ARCHIVE_SHA256=$(shasum -a 256 "${CANONICAL_ARCHIVE}" | awk '{print $1}')
fi

# Step 5: create symlink in repo root
SYMLINK_PATH="${ROOT_DIR}/UPLOAD_THIS.zip"
rm -f "${SYMLINK_PATH}"
ln -s "${CANONICAL_ARCHIVE}" "${SYMLINK_PATH}"
log_pass "Created symlink: ${SYMLINK_PATH} → ${CANONICAL_ARCHIVE}"

# Step 6: run upload verification
log_bold "=== Phase 3: Upload Verification ==="
echo ""
bash scripts/verify_upload_ready.sh || { log_fail "Upload verification failed"; exit 1; }

echo ""
echo "========================================"
echo "  UPLOAD FILE READY"
echo "========================================"
echo ""
log_bold "UPLOAD ONLY THIS EXACT FILE:"
echo ""
echo "  ${UPLOAD_TARGET}"
echo ""
log_bold "OR use the symlink in the repo root:"
echo ""
echo "  ${SYMLINK_PATH}"
echo ""
log_bold "Archive SHA-256:"
echo ""
echo "  ${ARCHIVE_SHA256}"
echo ""
echo "========================================"
log_bold "DO NOT UPLOAD:"
echo "  - Any file named JUDGE_ATLASX-main-master*.zip"
echo "  - Any source snapshot or git-export ZIP"
echo "  - Any ZIP containing .env.example files"
echo "  - Any ZIP with root folder other than JUDGE_ATLAS-main/"
echo "========================================"
