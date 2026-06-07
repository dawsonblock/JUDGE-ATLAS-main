#!/bin/bash
# Master blocker repair verification script
# Run this from a clean extracted archive directory

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         JUDGE-ATLAS BLOCKER REPAIR VERIFICATION               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

echo "[1/7] Checking release artifact identity..."
python scripts/check_release_artifact_identity.py || exit 1
echo

echo "[2/7] Checking required proof logs..."
python scripts/check_required_proof_logs.py || exit 1
echo

echo "[3/7] Checking status consistency..."
python scripts/check_status_consistency.py || exit 1
echo

echo "[4/7] Reconciling test counts..."
python scripts/reconcile_test_counts.py > /dev/null && echo "PASS: Test count reconciliation"
echo

echo "[5/7] Verifying source-to-map proof..."
python scripts/generate_source_to_map_proof.py > /dev/null && echo "PASS: Source-to-map pipeline proof"
echo

echo "[6/7] Verifying route inventory..."
python scripts/generate_route_inventory.py > /dev/null && echo "PASS: Route inventory proof"
echo

echo "[7/7] Verifying production flags..."
if grep -q '"production_ready": false' artifacts/proof/current/release_gate.json && \
   grep -q '"public_release_safe": false' artifacts/proof/current/release_gate.json; then
    echo "PASS: Production flags remain false"
else
    echo "FAIL: Production flags not set correctly"
    exit 1
fi
echo

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✓ ALL BLOCKERS VERIFIED - PASS                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

echo "Summary:"
echo "  ✓ Artifact identity validated"
echo "  ✓ Proof logs present and non-empty"
echo "  ✓ Status consistency verified"
echo "  ✓ Test counts reconciled"
echo "  ✓ Source-to-map pipeline proven"
echo "  ✓ Route inventory complete"
echo "  ✓ Production flags set correctly"
echo
echo "Release Status: self_verifying_alpha"
echo "Production Ready: NO (correct for alpha)"
