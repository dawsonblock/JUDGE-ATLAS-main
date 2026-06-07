# Final Release Handoff

This document is generated from the built archive and
canonical proof artifacts.
Manual edits are not authoritative.

## Authoritative Archive
- Path: dist/JUDGE_ATLAS-main-final.zip
- SHA-256: 5510522bbb3f675c189307ffc461aa6f5d4d6750f466feef0b0858bd54c870cc

## Proof Anchors
- release_gate_path: artifacts/proof/current/release_gate.json
- release_gate_sha256: 2918fc023ae0432a3da82261261c5a7a570755c3a6c6555ed7aea96bdeb3ab30
- proof_manifest_path: artifacts/proof/current/proof_manifest.json
- proof_manifest_sha256: 51aeec1b7269392d6563d7af819868b6df6ec4fd3c5fcc8ace458e4903642017
- required_log_index_path: artifacts/proof/current/required_log_index.json
- required_log_index_sha256: b94a46a50e309bc42af51c5c0f1f3d9e8332d5f596c0caa6e95b4295b2f71900

## Release Status
- release_classification: self-verifying alpha
- alpha_candidate: true
- self_verifying_alpha: true
- production_release_candidate: false
- production_ready: false
- public_release_safe: false
- proof_complete: true
- blocked_release_checks: []

## Build Metadata
- created_at_utc: 2026-06-07T09:25:04.623304+00:00
- generated_at_utc: 2026-06-07T09:25:04.623304+00:00
- git_commit: 131117bce06d46b2c73d436427a9f6477bfc7598
- platform: macOS-26.2-arm64-arm-64bit
- python: 3.11.9
- node: v22.22.3
- npm: 10.9.8

## Notes
- This is a self-verifying alpha.
- It is not ready for production deployment.
- Ship only the archive listed above.
- Validation must run against a fresh extraction
  of that archive.
- `release_gate.json` is only valid as a proof artifact when
  every log path it references exists inside
  `artifacts/proof/current/`
  at packaging time. Do not ship manually zipped working trees.
