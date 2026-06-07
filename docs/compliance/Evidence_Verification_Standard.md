# Evidence Verification Standard

## Scope

This document defines the canonical schema and validation rules for evidence
records within JUDGE_ATLASX. Every evidence artifact that may be published or
cited must carry a complete `EvidenceVerificationRecord` satisfying all fields
listed below.

## Purpose

- Prevent publication of unverified or improperly attributed evidence.
- Ensure every public record has a complete custody chain from ingestion to
  publication.
- Enforce that AI-generated output is explicitly marked as derivative.
- Require human review before any evidence is marked publication-ready.

## Canonical Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `evidence_id` | string | Yes | Unique identifier for the evidence record. |
| `source_snapshot_id` | integer | Yes | FK to `SourceSnapshot.id` — the original raw content. |
| `source_id` | string | Yes | Source registry key (e.g. `justice_canada_laws_xml`). |
| `source_url` | string | Yes | URL the content was fetched from. |
| `original_hash` | string (64 hex) | Yes | SHA-256 of the raw source content. Immutable. |
| `final_hash` | string (64 hex) | Yes | SHA-256 after all processing. Must match recoverable bytes. |
| `processing_steps` | list[ProcessingStep] | Yes | Ordered transformations applied to the evidence. |
| `ai_output_is_derivative` | boolean | Yes | **Must be `true`** for any AI-processed evidence. |
| `human_reviewer` | string | null | Identity of the human reviewer. Required when `review_decision` is `approved`. |
| `review_decision` | enum | Yes | `pending`, `approved`, `rejected`, or `escalated`. |
| `review_timestamp` | datetime | null | When the review decision was recorded. Required when `review_decision` is `approved`. |
| `previous_log_hash` | string (64 hex) | null | Hash of the previous custody chain entry (append-only integrity). |
| `custody_chain` | list[dict] | Yes | Ordered custody events from ingestion to current state. |
| `publication_readiness` | enum | Yes | `ready`, `blocked`, or `needs_review`. |

## Validation Rules

1. `evidence_id` must be a non-empty string.
2. `source_snapshot_id` must be a positive integer referencing an existing snapshot.
3. `original_hash` and `final_hash` must each be exactly 64 hex characters.
4. `ai_output_is_derivative` must be `true`. Failure blocks publication.
5. When `review_decision` is `approved`:
   - `human_reviewer` must not be null.
   - `review_timestamp` must be a valid datetime.
6. When `publication_readiness` is `ready`:
   - `review_decision` must be `approved`.
   - `custody_chain` must contain at least one event.
   - If `original_hash != final_hash`, `processing_steps` must document the
     transformation.

## ProcessingStep Schema

Each entry in `processing_steps` is an ordered transformation:

| Field | Type | Description |
|---|---|---|
| `name` | string | Step name, e.g. `extract_claims`, `normalize_entities`. |
| `timestamp` | datetime | When the step ran. |
| `input_hash` | string | Hash of the input to this step. |
| `output_hash` | string | Hash of the output from this step. |
| `metadata` | dict | Step-specific metadata. |

## Enforcement

- The `verify_evidence_record()` function returns a list of validation errors.
- An empty list means the record is structurally valid.
- `is_publication_ready()` returns `true` only when the record is valid **and**
  `publication_readiness == ready`.

## Implementation

- `backend/app/evidence/verification_standard.py` — schema and validation
- `backend/app/tests/test_evidence_verification_standard.py` — test coverage
- `scripts/check_evidence_verification_standard.py` — proof gate check
