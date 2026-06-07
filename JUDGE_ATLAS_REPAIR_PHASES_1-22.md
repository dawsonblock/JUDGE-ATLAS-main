# JUDGE-ATLAS: 22-Phase Comprehensive Repair Plan
## Complete Implementation Guide for Self-Verifying Alpha Release

---

## 📋 Executive Summary

**Problem**: The current build claims `self_verifying_alpha=true` while the extracted archive fails its own proof-manifest checks. This creates an endless repair loop.

**Solution**: Fix the release chain first. Implement 22 phases in strict sequence to ensure the final artifact (`JUDGE_ATLAS-main-final.zip`) can validate itself after extraction from a clean folder.

**Target State**:
```json
{
  "alpha_candidate": true,
  "self_verifying_alpha": true,
  "production_ready": false,
  "public_release_safe": false,
  "release_blockers_remaining": []
}
```

**Acceptance**: Running these commands from extracted archive must all pass:
```bash
python scripts/check_release_artifact_identity.py
python scripts/check_required_proof_logs.py
python scripts/check_proof_manifest.py
python scripts/check_status_consistency.py
python scripts/verify_release_archive.py dist/JUDGE_ATLAS-main-final.zip
bash scripts/final_acceptance_checklist.sh
```

---

## 🚨 FREEZE FEATURES IMMEDIATELY

**Do not add**:
- New map features
- New AI/legal reasoning
- New admin pages
- New workflow routes
- New source types
- New frontend redesigns
- New experimental routes

**Only repair** (22 phases below).

---

## 🔧 PHASES 1-7: RELEASE CHAIN (CRITICAL)

### Phase 1: Canonical Artifact Identity

**File**: `artifacts/proof/current/release_artifact_identity.json`

```json
{
  "artifact_name": "JUDGE_ATLAS-main-final.zip",
  "artifact_kind": "pipeline_release_artifact",
  "manual_zip": false,
  "canonical": true,
  "build_id": "2026-06-07-alpha-001",
  "git_commit": "<commit-sha>",
  "created_by": "alpha-release-proof pipeline",
  "created_at_utc": "<ISO-timestamp>",
  "source_root": "JUDGE-ATLAS-main"
}
```

**Script**: `scripts/check_release_artifact_identity.py` ✓ (DONE)

**Rules**:
- Reject manually zipped folders
- Enforce canonical naming
- Fail if manual_zip=true
- Fail if canonical=false
- Fail if build_id mismatch

---

### Phase 2: Proof Logging Wrapper

**Script**: `scripts/run_with_proof_log.py` ✓ (DONE)

**Usage**:
```bash
python scripts/run_with_proof_log.py \
  --name backend_pytest \
  --log artifacts/proof/current/backend_pytest.log \
  --summary artifacts/proof/current/backend_pytest_summary.json \
  -- pytest backend/app/tests
```

**Hard Rule**: No log = no pass. All logs must be non-empty.

**Required logs** (all must exist and be non-empty):
- `release_gate.log`
- `backend_compile.log`
- `backend_import.log`
- `backend_pytest.log`
- `backend_migrations.log`
- `runtime_smoke.log`
- `docker_runtime_preflight.log`
- `docker_smoke.log`
- `postgis_proof.log`
- `egress_proxy_proof.log`
- `demo_proof.log`
- `source_registry_proof_pytest.log`
- `public_api_boundary.log`
- `frontend_install.log`
- `frontend_node_gate.log`
- `frontend_lint.log`
- `frontend_typecheck.log`
- `frontend_contracts.log`
- `frontend_build.log`
- `frontend_route_smoke.log`
- `archive_validation.log`
- `proof_consistency_pytest.log`
- `status_consistency.log`

---

### Phase 3: Proof Manifest Enforcement

**Scripts**: 
- `scripts/check_required_proof_logs.py` ✓ (DONE)
- `scripts/check_proof_manifest.py` ✓ (DONE)

**Hard Rule**: If any required log is missing or empty, release fails.

---

### Phase 4: Archive File Index

**Script**: `scripts/generate_archive_file_index.py` ✓ (DONE)

**Output**: `artifacts/proof/current/archive_file_index.json`

Compares manifest against actual ZIP contents. Fails if promised files missing.

---

### Phase 5: Archive Validator

**Script**: `scripts/verify_release_archive.py` ✓ (DONE)

**Checks**:
- No path traversal
- No absolute paths
- No empty required logs
- All promised artifacts present
- Build ID consistency
- Checksums match (if declared)

**Output**: `artifacts/proof/current/archive_integrity.json`

---

### Phase 6: Release Gate Last

**Requirement**: Move `release_gate.json` generation to FINAL step in CI.

**Order** (simplified):
1. Run all tests (generate `.log` files)
2. Package candidate archive
3. Inspect candidate archive
4. Validate archive integrity
5. **ONLY THEN** generate `release_gate.json`

**File**: `.github/workflows/alpha-release-proof.yml`

---

### Phase 7: README Status Consistency

**File**: `README.md`

**Add section**:
```markdown
## Current release status
Canonical release status is defined by:
- `artifacts/proof/current/release_gate.json`
- `artifacts/proof/current/proof_manifest.json`

Current status:
- Alpha candidate: yes
- Self-verifying alpha: yes, only if archive validation passes
- Production ready: no
- Public release safe: no

To verify:
python scripts/check_required_proof_logs.py
python scripts/check_proof_manifest.py
python scripts/check_status_consistency.py
python scripts/verify_release_archive.py dist/JUDGE_ATLAS-main-final.zip
```

**Script**: `scripts/check_status_consistency.py` ✓ (DONE)

---

## 📊 PHASES 8-12: SOURCE & ADAPTER REPAIR (HIGH PRIORITY)

### Phase 8: Test Count Reconciliation

**Script**: `scripts/reconcile_test_counts.py` ✓ (DONE)

**Output**: `artifacts/proof/current/test_count_reconciliation.json`

Explains why backend_summary shows 403 passed but JUnit shows 3,610 tests (parameterization).

---

### Phase 9: Source Registry Repair

**Target**:
- 12 runnable sources
- 0 unexplained enable-ready
- 0 adapters with NotImplementedError
- 0 deprecated in active workflows

**Fields per source**:
```json
{
  "source_key": "sk_police",
  "lifecycle_state": "runnable",
  "adapter_exists": true,
  "adapter_state": "implemented",
  "runnable_now": true,
  "enable_ready": false,
  "blockers": [],
  "last_verified_at": "...",
  "proof_file": "artifacts/proof/current/sources/sk_police.json"
}
```

**Commands**:
```bash
python -m backend.app.ingestion.source_registry_ctl validate
python -m backend.app.ingestion.source_registry_ctl list --status runnable
python -m backend.app.ingestion.source_registry_ctl proof
```

---

### Phase 10: Runnable Adapter Interface

**Standard interface**:
```python
class SourceAdapter(Protocol):
    source_id: str
    async def fetch(self, limit: int = 10) -> list[RawSourceDocument]:
        ...
    async def normalize(self, raw: RawSourceDocument) -> NormalizedSourceDocument:
        ...
    async def snapshot(self, normalized: NormalizedSourceDocument) -> EvidenceSnapshot:
        ...
```

**Hard rule**: No runnable adapter may raise `NotImplementedError`.

**Fixture tests**: Each runnable source needs offline fixture test.

---

### Phase 11: Source-to-Map Pipeline Proof

**Files to create**:
- `backend/app/tests/e2e/test_source_to_map_pipeline.py`
- `frontend/tests/contracts/map-source-to-marker.contract.test.ts`
- `backend/app/tests/fixtures/sources/sk_public_safety_release_001.html`

**Proof artifact**: `artifacts/proof/current/source_to_map_proof.json`

```json
{
  "passed": true,
  "unreviewed_hidden": true,
  "approved_marker_public": true,
  "citation_trail_present": true,
  "frontend_contract_passed": true
}
```

---

### Phase 12: Route Boundaries & Inventory

**Script**: `scripts/generate_route_inventory.py` ✓ (DONE)

**Output**: `artifacts/proof/current/route_inventory.json`

Each route must be categorized (public/admin/experimental).

**Test**: `backend/app/tests/security/test_route_auth_boundaries.py`

---

## 🛡️ PHASES 13-19: SAFETY & HARDENING (MEDIUM PRIORITY)

### Phase 13: Admin Live Map Gate

```python
if settings.enable_admin_live_map:
    router.include_router(admin_live_map.router)
```

Default: `ENABLE_ADMIN_LIVE_MAP=false`

---

### Phase 14: Experimental & Legacy Routes

Defaults (all false):
- `ENABLE_EXPERIMENTAL_LIVE_MAP=false`
- `ENABLE_WORKFLOW_ADMIN=false`
- `ENABLE_LEGACY_US_INGEST_ROUTES=false`
- `ENABLE_ADMIN_LIVE_MAP=false`

Proof: `artifacts/proof/current/feature_flag_route_mounts.json`

---

### Phase 15: AI Answer Safety

**Schema**:
```python
class RuntimeStepResult(BaseModel):
    answer_basis: Literal["source_evidence", "model_inference", "mixed", "unknown"]
    confidence: float
    warnings: list[str]
    cited_snapshot_ids: list[str]
    review_required: bool
    public_safe: bool
```

**Rules**:
- Model inference requires citations
- No citation = no public answer
- Contradictions force review

---

### Phase 16: Memory Safety

**Schema**:
```python
class MemoryQuery(BaseModel):
    require_reviewed: bool = True
    require_citations: bool = True
```

Default: Safe for legal/public use.

---

### Phase 17: Bi-Temporal Versioning

**Fields**:
```python
valid_from
valid_to
recorded_at
superseded_at
version_id
is_current
```

Never overwrite history. Create new version, mark old as superseded.

---

### Phase 18: Frontend Contracts

Create contract tests:
- `frontend/tests/contracts/map-source-to-marker.contract.test.ts`
- `frontend/tests/contracts/source-registry.contract.test.ts`
- `frontend/tests/contracts/admin-review.contract.test.ts`
- `frontend/tests/contracts/map-public-safety.contract.test.ts`

---

### Phase 19: Docker/Runtime Proof

**Output**: `artifacts/proof/current/docker_compose_smoke.json`

```json
{
  "compose_up": true,
  "backend_health": true,
  "postgres_ready": true,
  "postgis_ready": true,
  "redis_ready": true,
  "alembic_current": true,
  "protected_route_unauthorized": true,
  "passed": true
}
```

---

## 📦 PHASES 20-22: CI & FINAL ACCEPTANCE

### Phase 20: Package Candidate Archive

```bash
./scripts/build_final_release.sh
```

Creates: `dist/JUDGE_ATLAS-main-final.zip`

---

### Phase 21: Archive Integrity Validation

Runs `scripts/verify_release_archive.py` on packaged archive.

Must pass before release gate generation.

---

### Phase 22: Final Acceptance Checklist

```bash
bash scripts/final_acceptance_checklist.sh
```

30+ checkpoints. All must pass.

---

## ✅ ACCEPTANCE CRITERIA

From clean extraction, these must all pass:

```
[PASS] Artifact identity validation
[PASS] Required proof logs present (23 logs)
[PASS] All logs non-empty
[PASS] Proof manifest matches ZIP contents
[PASS] Status consistency (README + proof)
[PASS] Test count reconciliation
[PASS] Source registry valid (12+ runnable)
[PASS] Runnable adapters (0 NotImplementedError)
[PASS] Source-to-map pipeline proof
[PASS] Route boundaries enforced
[PASS] Admin live map gated
[PASS] Feature flags default-off
[PASS] Archive integrity validation
[PASS] Release gate generation (AFTER validation)
[PASS] self_verifying_alpha=true
[PASS] production_ready=false
[PASS] public_release_safe=false
[PASS] release_blockers_remaining=[]
```

---

## 🎯 PRIORITY RANKING

**CRITICAL** (must fix before any release):
- Proof logs (all 23 required logs)
- Proof manifest consistency
- Archive validation
- Release gate ordering (LAST step)
- Status consistency
- Artifact identity

**HIGH** (required for useful alpha):
- Source registry (12 runnable)
- Runnable adapters (no NotImplementedError)
- Source-to-map proof (fixture works)
- Route boundaries (public/admin split)
- Admin live map gate

**MEDIUM** (safety/hardening):
- AI answer safety
- Memory safety
- Bi-temporal versioning
- Frontend contracts
- Docker proof

**LATER** (post-alpha):
- Production monitoring
- Live ingestion scale
- Legal review certification
- Red-team audit

---

## 🚀 IMPLEMENTATION ROADMAP

1. **This week**: Phases 1-7 (release chain)
2. **Next week**: Phases 8-12 (source/adapter)
3. **Week 3**: Phases 13-19 (safety)
4. **Week 4**: Phases 20-22 (CI + acceptance)

---

## 📄 REFERENCE: REQUIRED PROOF ARTIFACTS

**In final ZIP**:
- `release_artifact_identity.json`
- `release_gate.json`
- `proof_manifest.json`
- `archive_file_index.json`
- `archive_integrity.json`
- `test_count_reconciliation.json`
- `source_to_map_proof.json`
- `route_inventory.json`
- `feature_flag_route_mounts.json`
- `docker_compose_smoke.json`
- All `.log` files (23 required)
- All `.summary.json` files

**Canonical naming**: `JUDGE_ATLAS-main-final.zip` (no variations)

---

## ⚠️ CRITICAL RULES (NO EXCEPTIONS)

1. Release gate generated **LAST** (after archive validation)
2. No log = no pass (all 23 logs must be non-empty)
3. No citation = no public answer
4. No unreviewed = no public API
5. Archive must validate itself (clean extraction)
6. `production_ready=false` (alpha only)
7. `public_release_safe=false` (alpha only)
8. `self_verifying_alpha=true` only if ALL checks pass

---

**Status**: Implementation started. Phases 1-7 framework complete.  
**Next**: Phases 8-12 source/adapter repair.  
**Goal**: Honest, repeatable, verifiable alpha release.

