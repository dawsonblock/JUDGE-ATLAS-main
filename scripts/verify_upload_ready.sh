#!/usr/bin/env bash
set -euo pipefail

# Pre-upload verification script
# Ensures only the canonical archive dist/JUDGE_ATLAS-main-final.zip
# is considered for release upload.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_PATH="${ROOT_DIR}/dist/JUDGE_ATLAS-main-final.zip"
CANONICAL_NAME="JUDGE_ATLAS-main-final.zip"
CANONICAL_ROOT="JUDGE_ATLAS-main"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

ERRORS=0

# 1. Check canonical archive exists
if [[ ! -f "${ARCHIVE_PATH}" ]]; then
    log_fail "Canonical archive missing: ${ARCHIVE_PATH}"
    log_fail "Run: bash scripts/package_and_validate_release_archive.sh"
    exit 1
fi
log_pass "Canonical archive exists: ${ARCHIVE_PATH}"

# 2. Validate with validate_final_zip.py
if ! python3 "${ROOT_DIR}/scripts/validate_final_zip.py" "${ARCHIVE_PATH}" >/dev/null 2>&1; then
    log_fail "validate_final_zip.py failed for ${ARCHIVE_PATH}"
    ERRORS=$((ERRORS + 1))
else
    log_pass "validate_final_zip.py passed"
fi

# 3. Validate with check_release_surface.py
if ! python3 "${ROOT_DIR}/scripts/check_release_surface.py" --archive "${ARCHIVE_PATH}" >/dev/null 2>&1; then
    log_fail "check_release_surface.py failed"
    ERRORS=$((ERRORS + 1))
else
    log_pass "check_release_surface.py passed"
fi

# 4. Validate with cleanroom_release_test.py
if ! python3 "${ROOT_DIR}/scripts/cleanroom_release_test.py" --archive "${ARCHIVE_PATH}" >/dev/null 2>&1; then
    log_fail "cleanroom_release_test.py failed"
    ERRORS=$((ERRORS + 1))
else
    log_pass "cleanroom_release_test.py passed"
fi

# 5. Validate with check_release_handoff_consistency.py
if ! python3 "${ROOT_DIR}/scripts/check_release_handoff_consistency.py" --archive "${ARCHIVE_PATH}" >/dev/null 2>&1; then
    log_fail "check_release_handoff_consistency.py failed"
    ERRORS=$((ERRORS + 1))
else
    log_pass "check_release_handoff_consistency.py passed"
fi

# 6. Compute SHA-256
ARCHIVE_SHA256=""
if command -v sha256sum >/dev/null 2>&1; then
    ARCHIVE_SHA256=$(sha256sum "${ARCHIVE_PATH}" | awk '{print $1}')
else
    ARCHIVE_SHA256=$(shasum -a 256 "${ARCHIVE_PATH}" | awk '{print $1}')
fi

# 7. Check for forbidden source-snapshot ZIPs in the project root
for candidate in "${ROOT_DIR}"/*.zip; do
    [[ -f "${candidate}" ]] || continue
    # Skip symlinks (e.g., UPLOAD_THIS.zip pointing to canonical archive)
    [[ -L "${candidate}" ]] && continue
    basename_candidate=$(basename "${candidate}")
    if [[ "${basename_candidate}" != "${CANONICAL_NAME}" ]]; then
        log_warn "Found non-canonical ZIP that must NOT be uploaded: ${basename_candidate}"
        log_warn "  -> Only upload: ${CANONICAL_NAME}"
    fi
done

# 8. Print upload instructions
echo ""
echo "========================================"
echo "  UPLOAD VERIFICATION COMPLETE"
echo "========================================"
if [[ ${ERRORS} -eq 0 ]]; then
    log_pass "All checks passed. Ready for upload."
else
    log_fail "${ERRORS} check(s) failed. Fix before uploading."
fi
echo ""
echo "UPLOAD ONLY THIS EXACT FILE:"
echo "  ${ARCHIVE_PATH}"
echo ""
echo "Archive SHA-256:"
echo "  ${ARCHIVE_SHA256}"
echo ""
echo "DO NOT UPLOAD:"
echo "  - Any file named JUDGE_ATLASX-main-master*.zip"
echo "  - Any source snapshot or git-export ZIP"
echo "  - Any ZIP containing .env.example files"
echo ""
echo "To validate on a Docker-capable host before uploading:"
echo "  bash scripts/run_full_validation.sh --final-archive"
echo ""

if [[ ${ERRORS} -gt 0 ]]; then
    exit 1
fi
exit 0
