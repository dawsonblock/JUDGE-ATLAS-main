"""Evidence vault: hashing, provenance, chain-of-custody, and extraction.

This package-level __init__ exposes only lightweight, DB-independent
primitives so that ``app.evidence`` can be imported without pulling in
SQLAlchemy.  DB-backed helpers remain importable from their submodules:
``app.evidence.provenance``, ``app.evidence.snapshots``, etc.
"""

from app.evidence.hashing import (
    EvidenceIntegrityError,
    compute_hash,
    verify_hash,
)
from app.evidence.verification_standard import (
    EvidenceVerificationRecord,
    ProcessingStep,
    PublicationReadiness,
    ReviewDecision,
    is_publication_ready,
    verify_evidence_record,
)

__all__ = [
    "EvidenceIntegrityError",
    "compute_hash",
    "verify_hash",
    "EvidenceVerificationRecord",
    "ProcessingStep",
    "PublicationReadiness",
    "ReviewDecision",
    "is_publication_ready",
    "verify_evidence_record",
]
