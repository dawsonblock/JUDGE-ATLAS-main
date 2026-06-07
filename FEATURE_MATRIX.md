# FEATURE_MATRIX

> **Alpha only.** All entries reflect current alpha state. Nothing here is a production readiness claim.
> Authoritative runtime state: `artifacts/proof/current/release_gate.json`
> Authoritative source coverage: `artifacts/proof/current/source_registry_status.json`

## Runtime Feature Flags

| Feature | Alpha State | Notes |
|---|---|---|
| Evidence-cited AI answering | enabled (alpha, review-only) | AI outputs are derivative only; require human review and linked evidence snapshot |
| Public platform API | disabled | `JTA_ENABLE_PUBLIC_PLATFORM=false` |
| Live map | disabled | `JTA_ENABLE_EXPERIMENTAL_LIVE_MAP=false` |
| Workflow admin | disabled | `JTA_ENABLE_WORKFLOW_ADMIN=false` |
| Legacy admin token | disabled | `JTA_ENABLE_LEGACY_ADMIN_TOKEN=false` — removal plan documented |
| Rate limiting | memory backend (alpha) | Production requires Redis-backed rate limiting |
| Ingestion queue | in-process (alpha) | Production requires external queue backend |
| Evidence store | local filesystem (alpha) | Production requires verified storage backend |
| PostGIS runtime proof | not completed | Required before production_ready=true |
| Egress proxy proof | not completed | Required before production_ready=true |

## Source Coverage

Derived from `docs/source-governance/COVERAGE_MATRIX.md`.
Authoritative counts: `artifacts/proof/current/source_registry_status.json`.

| Metric | Count |
|---|---|
| Total registered sources | 26 |
| Machine-ingest sources | 8 |
| Runnable now | 7 |
| Enable-ready (stubbed, testable) | 0 |
| Deprecated | 3 |
| Portal reference only | 10 |
| Disabled stubs | 5 |

### Runnable Sources (7)

| Source Key | Jurisdiction | Parser |
|---|---|---|
| federal_court_canada | Canada | federal_court_html |
| justice_canada_laws_xml | Canada | laws_justice_xml |
| saskatoon_open_data_public_safety | Saskatoon, SK | ckan_api |
| scc_decisions | Canada | scc_lexum_api |
| sk_courts_ca_decisions | Saskatchewan | canlii_api |
| sk_courts_qb_decisions | Saskatchewan | canlii_api |
| sk_legislature_hansard | Saskatchewan | sk_legislature_html |

### Deprecated Sources (3)

| Source Key | Migration Target |
|---|---|
| canada_justice_laws | Use justice_canada_laws_xml |
| federal_court_canada_decisions | Migrate to federal_court_canada |
| scc_judgments | Migrate to scc_decisions |

## Release Posture

| Claim | Value |
|---|---|
| alpha_candidate | true (when canonical proof gates pass) |
| self_verifying_alpha | true (when canonical proof gates pass) |
| production_release_candidate | false |
| production_ready | false |
| public_release_safe | false |

## Notes

- All public-facing records require human review approval and must be linked to an evidence snapshot.
- AI and memory outputs are derivative only — not legal determinations.
- Authoritative release archive: `dist/JUDGE_ATLAS-main-final.zip` (pipeline-produced only).
- Do not ship manually zipped working trees as release candidates.
