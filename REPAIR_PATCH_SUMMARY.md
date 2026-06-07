# Release Repair Patch Summary

## Patch Applied

This patch fixes the release workflow to prevent stale proof from being packaged and uploaded by mistake.

## Changes

### 1. scripts/build_for_upload.sh

- **Before**: Checked if `dist/JUDGE_ATLAS-main-final.zip` existed; if so, copied it directly without validating proof freshness.
- **After**: Forces strict proof regeneration by default. Runs all validators before building the archive. Only skips proof regen if `--use-existing-proof` is explicitly passed.

### 2. Makefile

- Updated `build-for-upload` target description to reflect strict behavior.

### 3. docs/RELEASE_REPAIR_PLAN.md (new)

- Documents the strict validation sequence.
- Lists environment requirements and step-by-step release process.

### 4. UPLOAD_THIS.md (existing)

- Still present in repo root with unmistakable upload instructions.

## What This Prevents

- Uploading source snapshots (`JUDGE_ATLASX-main-master*.zip`)
- Packaging stale proof after source changes
- Uploading archives with missing proof logs
- Silent reuse of old archives without validation

## What Still Requires a Docker Host

The following checks need Docker Desktop + PostGIS:

- `release_gate.py` (for Docker/PostGIS proof)
- `verify_archive_proof_freshness.py`
- `validate_extracted_release.py`

These will remain as blockers until the full proof pipeline runs on a Docker-capable machine.

## Honest Status

- Source registry blocker: **fixed**
- Task fake-success: **fixed**
- Static validators: **passing**
- Proof freshness discipline: **fixed**
- Docker-dependent proof: **still requires Docker host**

## Next Step

Run `make build-for-upload` on a host with:
- Python 3.11.9
- Node 22.x, npm 10.x
- Docker Desktop + Compose
- PostGIS

This will produce `dist/JUDGE_ATLAS-main-final.zip` with fully regenerated proof.
Upload only that file.
