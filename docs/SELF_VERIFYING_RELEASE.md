# Self-Verifying Release Architecture

## Overview

This document describes how JUDGE_ATLASX achieves a reproducible, self-verifying alpha release.

The core principle: **The release artifact must be able to prove its own integrity without external validation.**

## What Does "Self-Verifying" Mean?

A self-verifying release artifact:

1. **Contains all proof artifacts** — not just binary code, but the logs, test results, and validation reports that prove the build worked
2. **Validates itself** — includes a validator script that extracts and inspects the archive contents
3. **Is immutable** — every proof artifact has a SHA256 hash; content cannot be replaced without detection
4. **Is auditable** — the complete build chain is represented in proof files, allowing anyone to verify what was built and why

## Archive Structure

```
JUDGE_ATLASX-main-repair-self-verifying-alpha.zip
├── backend/
│   ├── app/
│   ├── tests/
│   └── ...
├── frontend/
│   ├── app/
│   ├── tests/
│   └── ...
├── artifacts/proof/current/
│   ├── release_gate.json                    # Release metadata
│   ├── proof_manifest.json                  # Index of all proofs
│   ├── archive_integrity.json               # Archive validation result
│   ├── archive_integrity.log                # Human-readable validation
│   ├── test_count_reconciliation.json       # Test count explanation
│   ├── test_count_reconciliation.log        # Human-readable reconciliation
│   ├── route_inventory.json                 # Route security inventory
│   ├── source_to_map_proof.json             # End-to-end pipeline proof
│   ├── source_to_map_proof.log              # Pipeline test log
│   ├── backend_pytest.xml                   # Raw JUnit XML
│   ├── backend_proof_summary.json           # Backend test summary
│   ├── frontend_proof_summary.json          # Frontend test summary
│   ├── backend_pytest.log                   # Backend test log
│   ├── frontend_build.log                   # Frontend build log
│   ├── docker_compose_smoke.json            # Docker smoke test result
│   ├── docker_compose_smoke.log             # Docker smoke test log
│   └── ...
└── scripts/
    ├── verify_release_archive.py            # Validator script
    ├── generate_archive_integrity.py        # Integrity generator
    ├── reconcile_test_counts.py             # Count reconciler
    └── generate_route_inventory.py          # Route inventory generator
```

## Proof Artifacts

### 1. release_gate.json

Release metadata and decision gates.

```json
{
  "build_id": "2024-01-20-alpha-001",
  "timestamp": "2024-01-20T14:32:00Z",
  "state": "self_verifying_alpha",
  "production_ready": false,
  "public_release_safe": false,
  "self_verifying_alpha": true,
  "archive_self_verifying": true,
  "blockers": []
}
```

**Rule**: `self_verifying_alpha` can only be `true` if `archive_self_verifying` is also `true`.

### 2. proof_manifest.json

Index of all required proof artifacts.

```json
{
  "build_id": "2024-01-20-alpha-001",
  "timestamp": "2024-01-20T14:32:00Z",
  "required_logs": [
    "backend_pytest.log",
    "frontend_build.log",
    "docker_compose_smoke.log"
  ],
  "required_summaries": [
    "backend_proof_summary.json",
    "frontend_proof_summary.json"
  ]
}
```

### 3. archive_integrity.json

Validation result for the extracted archive.

```json
{
  "archive_path": "dist/JUDGE_ATLASX-main-repair-self-verifying-alpha.zip",
  "archive_sha256": "abc123...",
  "zip_entries": 3174,
  "path_traversal_entries": [],
  "absolute_path_entries": [],
  "required_artifacts_checked": 12,
  "required_artifacts_present": 12,
  "required_artifacts_missing": [],
  "build_ids_consistent": true,
  "timestamps_consistent": true,
  "archive_self_verifying": true
}
```

## Validation Flow

### During Build (CI)

1. Run all tests and generate proof artifacts in `artifacts/proof/current/`
2. Create `proof_manifest.json` listing all required artifacts
3. Package the archive (ZIP)
4. Run `generate_archive_integrity.py` to validate the archive
5. Generate `archive_integrity.json` and `archive_integrity.log`
6. Only then generate `release_gate.json` as the final step

### After Packaging

```bash
# Verify the archive can prove itself
python scripts/verify_release_archive.py \
  dist/JUDGE_ATLASX-main-repair-self-verifying-alpha.zip \
  --strict \
  --output artifacts/proof/current/archive_validation.json
```

This script:
1. Extracts the ZIP to a temporary location
2. Finds `proof_manifest.json`
3. Verifies every listed artifact exists
4. Checks SHA256 hashes
5. Validates build_id and timestamp consistency
6. Either confirms or rejects `self_verifying_alpha` claim

If validation fails, the release gate must block.

## Hard Rules

1. **No overclaiming**: `production_ready=false` and `public_release_safe=false` for alpha
2. **No false self-verification**: `self_verifying_alpha=true` only if archive validation passes
3. **No missing logs**: Every log claimed in `proof_manifest.json` must exist in the archive
4. **No path traversal**: ZIP cannot contain entries like `../../../etc/passwd`
5. **No absolute paths**: ZIP cannot contain entries starting with `/`
6. **Consistent metadata**: build_id and timestamps must match between manifest and gate

## Security Properties

- **Immutability**: Hashes prevent silent corruption
- **Transparency**: All proof artifacts are readable JSON/logs, not opaque binary formats
- **Auditability**: Anyone with the ZIP can run `verify_release_archive.py` to validate
- **Completeness**: The archive is self-contained; no external dependencies for verification

## Current Alpha Status

This release is **NOT production-ready**.

Known limitations:
- Limited source coverage (12 runnable adapters)
- Alpha ingestion adapters (may have NotImplementedError)
- No production monitoring/SLA
- Limited live-source proof
- No legal professional review certification
- No red-team privacy audit

See [PRODUCTION_GAP.md](PRODUCTION_GAP.md) for full details.

## Next Steps

To move beyond self-verifying alpha:

1. Complete all source adapters (0 NotImplementedError)
2. Add production monitoring and SLAs
3. Engage legal professional review
4. Red-team the privacy/redaction system
5. Add deployment rollback proof
6. Define incident response procedures
