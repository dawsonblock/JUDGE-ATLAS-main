"""Evidence verification standard for JUDGE_ATLASX.

Enforces a canonical schema for evidence records before they are
approved for publication. Every published or publishable evidence
record must satisfy all fields defined here.

The standard enforces:
- evidence_id: unique identifier for the evidence record
- source_snapshot_id: FK to the original source snapshot
- source_id: source registry key
- source_url: URL the content was fetched from
- original_hash: SHA-256 of raw source content (immutable)
- final_hash: SHA-256 after all processing (must match recoverable bytes)
- processing_steps: ordered list of transformations applied
- ai_output_is_derivative: MUST be True for AI-processed evidence
- human_reviewer: identity of the human reviewer
- review_decision: pending | approved | rejected | escalated
- review_timestamp: when the review decision was recorded
- previous_log_hash: hash of the previous custody chain entry
- custody_chain: ordered list of custody events
- publication_readiness: ready | blocked | needs_review
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReviewDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"
    pending = "pending"
    escalated = "escalated"


class PublicationReadiness(str, Enum):
    ready = "ready"
    blocked = "blocked"
    needs_review = "needs_review"


@dataclass
class ProcessingStep:
    """One transformation step in the evidence pipeline."""

    name: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    input_hash: str | None = None
    output_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceVerificationRecord:
    """Canonical evidence verification record.

    Every evidence artifact that may be published must carry a complete
    verification record. Missing fields block publication.
    """

    evidence_id: str
    source_snapshot_id: int
    source_id: str
    source_url: str
    original_hash: str  # hash of raw source content
    final_hash: str  # hash after all processing
    processing_steps: list[ProcessingStep]
    ai_output_is_derivative: bool = True
    # MUST be True for AI-processed evidence
    human_reviewer: str | None = None
    review_decision: ReviewDecision = field(
        default_factory=lambda: ReviewDecision.pending
    )
    review_timestamp: datetime | None = None
    previous_log_hash: str | None = None  # hash of previous custody log entry
    custody_chain: list[dict[str, Any]] = field(default_factory=list)
    publication_readiness: PublicationReadiness = field(
        default_factory=lambda: (
            PublicationReadiness.needs_review
        )
    )


class EvidenceVerificationError(Exception):
    """Raised when an evidence record fails verification."""


REQUIRED_FIELDS = [
    "evidence_id",
    "source_snapshot_id",
    "source_id",
    "source_url",
    "original_hash",
    "final_hash",
    "processing_steps",
    "ai_output_is_derivative",
    "human_reviewer",
    "review_decision",
    "review_timestamp",
    "previous_log_hash",
    "custody_chain",
    "publication_readiness",
]


def verify_evidence_record(record: EvidenceVerificationRecord) -> list[str]:
    """Validate an evidence verification record.

    Returns a list of error strings. Empty list means the record passes.
    """
    errors: list[str] = []

    if not record.evidence_id or not isinstance(record.evidence_id, str):
        errors.append("evidence_id must be a non-empty string")

    if not isinstance(record.source_snapshot_id, int) or (
        record.source_snapshot_id <= 0
    ):
        errors.append("source_snapshot_id must be a positive integer")

    if not record.source_id or not isinstance(record.source_id, str):
        errors.append("source_id must be a non-empty string")

    if not record.source_url or not isinstance(record.source_url, str):
        errors.append("source_url must be a non-empty string")

    if not record.original_hash or not _SHA256_RE.match(record.original_hash):
        errors.append(
            "original_hash must be a 64-character SHA-256 hex string"
        )

    if not record.final_hash or not _SHA256_RE.match(record.final_hash):
        errors.append(
            "final_hash must be a 64-character SHA-256 hex string"
        )

    if not isinstance(record.processing_steps, list):
        errors.append("processing_steps must be a list")
    else:
        for idx, step in enumerate(record.processing_steps):
            if not isinstance(step, ProcessingStep):
                errors.append(
                    f"processing_steps[{idx}] must be a "
                    f"ProcessingStep instance"
                )
                continue
            if not step.name:
                errors.append(
                    f"processing_steps[{idx}].name must not be empty"
                )

    if record.ai_output_is_derivative is not True:
        errors.append(
            "ai_output_is_derivative must be True for "
            "all AI-processed evidence"
        )

    if record.review_decision == ReviewDecision.approved:
        if not record.human_reviewer:
            errors.append(
                "human_reviewer is required when review_decision is approved"
            )
        if not isinstance(record.review_timestamp, datetime):
            errors.append(
                "review_timestamp must be a datetime when "
                "review_decision is approved"
            )

    if record.publication_readiness == PublicationReadiness.ready:
        if record.review_decision != ReviewDecision.approved:
            errors.append(
                "publication_readiness cannot be ready without "
                "approved review_decision"
            )
        if not record.custody_chain:
            errors.append(
                "custody_chain must not be empty for "
                "publication-ready evidence"
            )
        if (
            record.original_hash != record.final_hash
            and not record.processing_steps
        ):
            errors.append(
                "processing_steps must document hash change "
                "from original to final"
            )

    return errors


def is_publication_ready(record: EvidenceVerificationRecord) -> bool:
    """Return True only if the record passes all checks and is marked ready."""
    return (
        not verify_evidence_record(record)
        and record.publication_readiness == PublicationReadiness.ready
    )
