# JUDGE_ATLASX Compliance Mapping

## Overview

This document maps JUDGE_ATLASX system controls to compliance domains and
evidence verification requirements.

## Evidence Verification Standard

| Requirement | Field | Enforcement |
|---|---|---|
| Unique evidence identifier | `evidence_id` | Non-empty string, validated by `verify_evidence_record()` |
| Source provenance | `source_snapshot_id`, `source_id`, `source_url` | Must reference valid snapshot and source registry entry |
| Content integrity (original) | `original_hash` | 64-char SHA-256; immutable after ingest |
| Content integrity (final) | `final_hash` | 64-char SHA-256; must match recoverable bytes |
| Transformation lineage | `processing_steps` | Ordered list with input/output hashes per step |
| AI derivative flag | `ai_output_is_derivative` | Hard-coded default `true`; any `false` blocks publication |
| Human review gate | `human_reviewer`, `review_decision`, `review_timestamp` | Required before `publication_readiness = ready` |
| Custody chain | `custody_chain`, `previous_log_hash` | Append-only chain-of-custody events |
| Publication readiness | `publication_readiness` | Gated on approved review + non-empty custody chain |

## Compliance Domains

### Data Integrity
- **Control**: Every evidence record carries `original_hash` and `final_hash`.
- **Proof**: `verify_evidence_record()` enforces 64-char SHA-256 hashes.
- **Test**: `test_short_original_hash`, `test_short_final_hash`

### Provenance & Audit
- **Control**: `source_snapshot_id`, `source_id`, and `source_url` trace evidence
  back to the original ingest.
- **Proof**: Validation fails if any field is missing.
- **Test**: `test_missing_source_id`, `test_missing_source_url`

### AI Transparency
- **Control**: `ai_output_is_derivative` must be `true`.
- **Proof**: Any record with `ai_output_is_derivative=false` is rejected.
- **Test**: `test_ai_output_is_derivative_must_be_true`

### Human Review Gate
- **Control**: `review_decision` must be `approved` before publication.
- **Proof**: `publication_readiness=ready` without `approved` review fails.
- **Test**: `test_ready_without_approved_review_blocked`

### Chain of Custody
- **Control**: `custody_chain` must not be empty for publication-ready evidence.
- **Proof**: `previous_log_hash` links entries in append-only fashion.
- **Test**: `test_ready_without_custody_chain_blocked`

### Processing Documentation
- **Control**: If `original_hash != final_hash`, `processing_steps` must document
  the transformation.
- **Proof**: Validation checks for processing steps when hashes differ.
- **Test**: `test_ready_with_hash_change_needs_processing_steps`

## Verification Script

Run the evidence verification standard check:

```bash
python3 scripts/check_evidence_verification_standard.py
```

Run the test suite:

```bash
cd backend && python -m pytest app/tests/test_evidence_verification_standard.py -q
```
