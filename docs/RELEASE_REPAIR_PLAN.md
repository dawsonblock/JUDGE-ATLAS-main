# Release Repair Plan

## Goal

Produce a self-verifying canonical release archive that passes all 24 validation checks and is safe to upload as the authoritative release artifact.

## What Was Broken

The release workflow allowed stale proof to be silently reused:

1. Source files changed
2. Proof hash became stale
3. Missing proof logs remained missing
4. `build_for_upload.sh` copied the existing stale archive without validation
5. Source snapshots were uploaded instead of canonical archives

## What Was Fixed

- `scripts/build_for_upload.sh` now **forces strict proof regeneration by default**
- It runs all validators before building the archive
- It only accepts `--use-existing-proof` as an explicit opt-in (not recommended)
- `make build-for-upload` now guarantees a freshly validated archive

## Strict Validation Sequence

Run automatically by `make build-for-upload`:

1. **Toolchain check** — `check_toolchain_versions.py`
2. **Release gate regeneration** — `release_gate.py`
3. **Status doc sync** — `sync_status_docs_from_gate.py`
4. **Proof status docs** — `render_proof_status_docs.py`
5. **Proof freshness** — `check_proof_freshness.py` + `--strict-extra-files`
6. **Proof consistency** — `check_proof_consistency.py`
7. **Required proof logs** — `check_required_proof_logs.py --strict-required-files`
8. **Single proof authority** — `check_single_proof_authority.py`
9. **Release gate check** — `check_release_gate.py`
10. **No local paths** — `check_no_local_paths_in_release_proof.py`
11. **Archive build** — `package_and_validate_release_archive.sh`
12. **Upload verification** — `verify_upload_ready.sh`

## Environment Requirements

- Python 3.11.9
- Node 22.x, npm 10.x
- Docker Desktop + Docker Compose
- PostGIS (for database proof)

## Steps to Produce a Valid Release

```bash
# 1. Ensure correct Python version
pyenv install 3.11.9
pyenv local 3.11.9

# 2. Ensure correct Node version
nvm install 22
nvm use 22

# 3. Verify Docker is running
docker version
docker compose version

# 4. Install backend dependencies
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -U pip
python -m pip install -e "backend[test]"
deactivate

# 5. Install frontend dependencies
npm ci --prefix frontend

# 6. Build the canonical archive (forces proof regeneration)
make build-for-upload

# 7. Verify before uploading
make verify-upload

# 8. Upload only this file
dist/JUDGE_ATLAS-main-final.zip
# or the Desktop copy:
UPLOAD_THIS_JUDGE_ATLAS-main-final.zip
```

## Exit Criteria

All of the following must pass:

- [ ] `check_proof_freshness.py`
- [ ] `check_proof_freshness.py --strict-extra-files`
- [ ] `check_proof_consistency.py`
- [ ] `check_required_proof_logs.py --strict-required-files`
- [ ] `check_release_gate.py`
- [ ] `validate_final_zip.py`
- [ ] `check_release_surface.py`
- [ ] `cleanroom_release_test.py`
- [ ] `check_release_handoff_consistency.py`
- [ ] `make verify-upload`

Until then, the status remains: **proof-blocked alpha source snapshot, not ready for release**.
