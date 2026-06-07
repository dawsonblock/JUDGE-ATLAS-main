#!/bin/bash
# JUDGE-ATLAS: Phase 22 Final Clean-Alpha Acceptance Checklist
# Run this from EXTRACTED archive root: cd /tmp/verify/JUDGE-ATLAS-main-main

set -e

PASS_COUNT=0
FAIL_COUNT=0

check() {
    local test_name="$1"
    local command="$2"
    
    if eval "$command" > /dev/null 2>&1; then
        echo "[PASS] $test_name"
        ((PASS_COUNT++))
    else
        echo "[FAIL] $test_name"
        ((FAIL_COUNT++))
    fi
}

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║   JUDGE-ATLAS FINAL CLEAN-ALPHA ACCEPTANCE CHECKLIST             ║"
echo "║   Running from extracted archive (clean verification)            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo

echo "RELEASE INTEGRITY CHECKS"
echo "───────────────────────────────────────────────────────────────────"

check "Artifact identity file exists" \
    "test -f artifacts/proof/current/release_artifact_identity.json"

check "Artifact identity is canonical" \
    "grep -q '\"canonical\": true' artifacts/proof/current/release_artifact_identity.json"

check "Artifact identity not manual zip" \
    "grep -q '\"manual_zip\": false' artifacts/proof/current/release_artifact_identity.json"

check "Release gate JSON exists" \
    "test -f artifacts/proof/current/release_gate.json"

check "Proof manifest exists" \
    "test -f artifacts/proof/current/proof_manifest.json"

check "No unsafe ZIP paths (checking root)" \
    "! find . -name '..' -o -name '../*' 2>/dev/null"

echo
echo "PROOF ARTIFACTS CHECKS"
echo "───────────────────────────────────────────────────────────────────"

# Check required logs exist and are non-empty
for log in \
    release_gate.log \
    backend_pytest.log \
    docker_smoke.log \
    source_registry_proof_pytest.log \
    public_api_boundary.log; do
    
    check "Required log present: $log" \
        "test -s artifacts/proof/current/$log"
done

echo
echo "PROOF MANIFEST CONSISTENCY"
echo "───────────────────────────────────────────────────────────────────"

check "Proof manifest has required_logs" \
    "grep -q 'required_logs' artifacts/proof/current/proof_manifest.json"

check "Manifest build_id matches release_gate" \
    "test \"\$(jq -r '.build_id' artifacts/proof/current/proof_manifest.json)\" = \"\$(jq -r '.build_id' artifacts/proof/current/release_gate.json)\""

check "Test count reconciliation exists" \
    "test -f artifacts/proof/current/test_count_reconciliation.json"

echo
echo "SOURCE-TO-MAP PIPELINE PROOF"
echo "───────────────────────────────────────────────────────────────────"

check "Source-to-map proof exists" \
    "test -f artifacts/proof/current/source_to_map_proof.json"

check "Source-to-map proof passed" \
    "grep -q '\"passed\": true' artifacts/proof/current/source_to_map_proof.json"

check "Citation trail present in proof" \
    "grep -q '\"citation_trail_present\": true' artifacts/proof/current/source_to_map_proof.json"

echo
echo "ROUTE BOUNDARY & SECURITY PROOF"
echo "───────────────────────────────────────────────────────────────────"

check "Route inventory exists" \
    "test -f artifacts/proof/current/route_inventory.json"

check "Public API boundary proof exists" \
    "test -f artifacts/proof/current/public_api_boundary.json"

check "Admin live map gated (proof)" \
    "grep -q '\"experimental\"' artifacts/proof/current/route_inventory.json"

echo
echo "DATA SAFETY & VERSIONING PROOF"
echo "───────────────────────────────────────────────────────────────────"

check "Archive integrity proof exists" \
    "test -f artifacts/proof/current/archive_integrity.json"

check "Feature flag route mounts proof exists" \
    "test -f artifacts/proof/current/feature_flag_route_mounts.json"

echo
echo "RELEASE GATE CONSTRAINTS"
echo "───────────────────────────────────────────────────────────────────"

check "Release gate: alpha_candidate=true" \
    "grep -q '\"alpha_candidate\": true' artifacts/proof/current/release_gate.json"

check "Release gate: self_verifying_alpha=true" \
    "grep -q '\"self_verifying_alpha\": true' artifacts/proof/current/release_gate.json"

check "Release gate: production_ready=false" \
    "grep -q '\"production_ready\": false' artifacts/proof/current/release_gate.json"

check "Release gate: public_release_safe=false" \
    "grep -q '\"public_release_safe\": false' artifacts/proof/current/release_gate.json"

check "Release gate: no blockers remaining" \
    "grep -q '\"release_blockers_remaining\": \\[\\]' artifacts/proof/current/release_gate.json || grep -q '\"release_blockers\": \\[\\]' artifacts/proof/current/release_gate.json"

echo
echo "README CONSISTENCY"
echo "───────────────────────────────────────────────────────────────────"

check "README has status section" \
    "grep -q 'Current release status' README.md || grep -q 'release status' README.md"

check "README references canonical proof" \
    "grep -q 'artifacts/proof/current/release_gate.json' README.md"

check "README does not claim production ready" \
    "! grep -q 'production.ready' README.md || grep -q 'production_ready: false' README.md"

echo
echo "═══════════════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════════════"
echo "Checks passed: $PASS_COUNT"
echo "Checks failed: $FAIL_COUNT"
echo

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ ALL CHECKS PASS - CLEAN ALPHA ACCEPTANCE COMPLETE"
    echo
    echo "Release Status:"
    echo "  Artifact: JUDGE_ATLAS-main-final.zip"
    echo "  State: self_verifying_alpha"
    echo "  Production ready: false (correct)"
    echo "  Public release safe: false (correct)"
    echo "  Release blockers: none"
    echo
    exit 0
else
    echo "❌ $FAIL_COUNT CHECKS FAILED - RELEASE INVALID"
    exit 1
fi
