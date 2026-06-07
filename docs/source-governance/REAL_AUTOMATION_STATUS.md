# Real Automation Status — Source Ingestion

**Document type**: Operational truth  
**Last updated**: 2026 (auto-derivable from `artifacts/proof/current/source_registry_status.json`)  
**Status**: Alpha — single source enabled

---

## Summary

JUDGE ATLAS currently has **27 total registered sources**, with **8 sources runnable now** and **16 sources not currently runnable**. This document records the ground truth.

| Status | Count | Description |
|---|---|---|
| `machine_ready_enabled` | 8 | Adapter exists, automation enabled, runs in production |
| `machine_ready_disabled` | 3 | Adapter exists and validated but intentionally disabled (alpha scope) |
| `adapter_missing` | 13 | Source defined in registry; no adapter implemented yet |
| `deprecated` | 3 | Source removed from active scope |
| `disabled_stub` | 0 | Placeholder only; not intended for near-term automation |

Additional generated summary fields from `source_registry_status.json`:

- `total_sources`: 27
- `machine_ingest_sources`: 12
- `runnable_now`: 8
- `enable_ready`: 3
- `deprecated`: 3

---

## Enabled Source (Production)

| Source Key | Notes |
|---|---|
| `justice_canada_laws_xml` | Justice Canada consolidated statutes XML feed. Adapter complete, snapshot + dedup active. |
| `saskatoon_open_data_public_safety` | City of Saskatoon CKAN public-safety feed. Adapter is fixture-validated and enabled for machine ingest. |
| `sk_courts_qb_decisions` | Saskatchewan Court of King's Bench decisions via CanLII API. Adapter and tests verified. |
| `sk_courts_ca_decisions` | Saskatchewan Court of Appeal decisions via CanLII API. Adapter and tests verified. |
| `federal_court_canada` | Federal Court of Canada decisions via HTML scrape. Adapter and tests verified. |
| `scc_decisions` | Supreme Court of Canada decisions via Lexum RSS. Adapter and tests verified. |
| `sk_legislature_hansard` | Saskatchewan Legislative Assembly Hansard via HTML scrape. Adapter and tests verified. |
| `sk_court_of_appeal` | Saskatchewan Court of Appeal decisions via RSS feed. Adapter and tests verified. |

---

## Ready But Disabled (Alpha Scope)

| Source Key | Notes |
|---|---|
| `web_monitor_saskatoon_police_news` | Saskatoon Police Service news releases. Crawler adapter implemented; disabled until operator enablement. |
| `sk_justice_ministry` | Saskatchewan Ministry of Justice news releases. Crawler adapter implemented; disabled until operator enablement. |
| `rcmp_sk_news` | RCMP Saskatchewan news releases. Crawler adapter implemented; disabled until operator enablement. |

---

## Adapter Not Yet Implemented

13 sources are defined in the source registry but have no adapter code. These exist to document intent and future roadmap, not to claim automation capability.

See `backend/app/ingestion/sources/` for the registry definitions and `backend/app/ingestion/source_adapters/` for existing adapters.

---

## What "Automated" Means Here

A source is `machine_ready_enabled` only when ALL of the following hold:

1. An adapter class exists in `backend/app/ingestion/source_adapters/`
2. The adapter passes its contract test (`tests/backend/test_machine_ingest_contract.py`)
3. The source's `ingestion_mode` is `machine_ingest` in the source registry
4. The `automation_status` field is `machine_ready_enabled`
5. The source has produced at least one committed snapshot in the evidence vault
6. The proof pipeline (`make proof`) passes with this source included

---

## Governance

This document must be updated whenever:
- A source moves from `machine_ready_disabled` → `machine_ready_enabled`
- A new adapter is completed and passes contract tests
- A source is deprecated or removed

Changes require a new `make proof` run and a proof artifact update before commit.
