# JUDGE_ATLASX

## Truth Statement

JUDGE_ATLASX is an evidence-governed Canadian legal intelligence alpha. Evidence is authoritative. AI and memory outputs are derivative only. All public-facing data requires human review approval and must be linked to an evidence snapshot. This is an alpha release, not a production legal authority.

## What It Is

A proof-gated alpha runtime for evidence-linked legal-intelligence workflows with source governance, review gates, and auditability.

## What It Is Not

It is not an autonomous accusation engine, predictive policing system, or production legal authority.

## Alpha Warning

This repository is alpha only. Do not treat outputs as legal determinations.

## Maturity Definitions

- alpha_candidate: build/tests/gates pass for alpha scope only.
- self_verifying_alpha: archive contains the proof artifacts needed to verify its own claims.
- production_release_candidate: full production deployment/security/rollback proof complete.
- production_ready: approved for operational production use.
- public_release_safe: safe to publish without misleading claims or incomplete proof.

Current expected release posture:

- self_verifying_alpha: true only when canonical proof/archive validators pass.
- production_release_candidate: false
- production_ready: false
- public_release_safe: false

## Quickstart

**Prerequisites:** Python 3.11.x, Node 22.x / npm 10.x, Docker Desktop or Colima.
See [docs/setup/MACOS_VSCODE.md](docs/setup/MACOS_VSCODE.md) for a full setup guide.

```bash
# 1. Copy environment template and review placeholder values
cp .env.example .env

# 2. Bootstrap all dependencies
make setup

# 3. Verify local environment
python3 scripts/check_local_dev_environment.py

# 4. Start the stack
make dev
```

## Test Command

```bash
make test
```

## Proof Command

```bash
make proof
```

## Source Coverage Link

See `docs/source-governance/COVERAGE_MATRIX.md`.

## Security Warning

Evidence is authoritative. AI and memory outputs are derivative only. Public visibility requires review approval and linked evidence snapshot.

## Canonical Status And Proof References

- STATUS.md
- artifacts/proof/current/release_gate.json
- artifacts/proof/current/CURRENT_PROOF.md
- artifacts/proof/current/release_readiness.md

## Release Artifact Policy

> [!WARNING]
> Manual source ZIPs (e.g., `JUDGE_ATLASX-main N.zip`, `workspace_snapshot.zip`) are **NOT authoritative release artifacts**. Only `dist/JUDGE_ATLAS-main-final.zip` produced by the canonical build pipeline may be distributed.

- Authoritative release archives are produced only by scripts/package_and_validate_release_archive.sh.
- Raw source snapshot ZIP files are not distributable release artifacts.
- Publish only dist/JUDGE_ATLAS-main-final.zip and include its SHA-256 in release communication.
- Do not upload workspace/source snapshots (for example JUDGE_ATLASX-main N.zip) as release candidates.
- See docs/RELEASE_READINESS.md and docs/reports/HARDENING_RELEASE_ARTIFACT_CHAIN.md.

## Canonical Release Commands

```bash
make proof
bash scripts/package_and_validate_release_archive.sh \
  --archive-path dist/JUDGE_ATLAS-main-final.zip \
  --package-root-name JUDGE_ATLAS-main
```
