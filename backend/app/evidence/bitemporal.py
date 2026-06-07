"""
Bi-temporal versioning for legal evidence.

Tracks both:
- valid_time: when the legal fact was true in the real world
- transaction_time: when the system learned/stored/updated it

Required for legal data integrity and auditability.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class BiTemporalRecord(BaseModel):
    """
    Base class for bi-temporal legal records.
    
    valid_from/valid_to: when the fact was true in reality
    recorded_at: when we first recorded it
    superseded_at: when a correction replaced it
    is_current: whether this is the active version
    version_id: immutable version identifier
    """
    # Identity
    id: str
    version_id: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Valid time (reality)
    valid_from: datetime
    valid_to: Optional[datetime] = None

    # Transaction time (system)
    recorded_at: datetime
    superseded_at: Optional[datetime] = None
    is_current: bool = True

    # Audit trail
    source_snapshot_id: str
    superseded_by_version_id: Optional[str] = None


class LegalInstrument(BiTemporalRecord):
    """Legal instrument with bi-temporal tracking."""
    instrument_type: str  # statute, case, regulation, etc.
    title: str
    jurisdiction: str
    body: str
    citations: list[str] = Field(default_factory=list)


class ExtractedEntity(BiTemporalRecord):
    """Extracted entity (person, organization, location) with versioning."""
    entity_type: str  # person, organization, location
    name: str
    attributes: dict = Field(default_factory=dict)


class PublicEventRecord(BiTemporalRecord):
    """Public event (map marker) with bi-temporal history."""
    title: str
    event_type: str
    description: str
    location: dict  # { lat, lon, label }
    occurred_at: datetime
    evidence_snapshot_ids: list[str] = Field(default_factory=list)


def create_new_version(
    original: BiTemporalRecord,
    **updates
) -> tuple[BiTemporalRecord, BiTemporalRecord]:
    """
    Create a new version of a bi-temporal record.
    
    Returns: (old_version_superseded, new_version)
    """
    now = datetime.now(timezone.utc)
    new_version_id = now.isoformat()

    # Mark original as superseded
    original_superseded = original.copy()
    original_superseded.is_current = False
    original_superseded.superseded_at = now
    original_superseded.superseded_by_version_id = new_version_id

    # Create new version with updates
    new_version = original.copy(update=updates)
    new_version.version_id = new_version_id
    new_version.recorded_at = now
    new_version.is_current = True
    new_version.superseded_at = None
    new_version.superseded_by_version_id = None

    return original_superseded, new_version


def get_record_history(records: list[BiTemporalRecord]) -> list[BiTemporalRecord]:
    """Get complete version history in chronological order."""
    return sorted(records, key=lambda r: r.recorded_at)


def get_current_record(records: list[BiTemporalRecord]) -> Optional[BiTemporalRecord]:
    """Get the current (non-superseded) version."""
    for record in records:
        if record.is_current:
            return record
    return None


def get_record_at_time(
    records: list[BiTemporalRecord],
    query_time: datetime
) -> Optional[BiTemporalRecord]:
    """
    Get what the record was at a specific point in time.
    
    Useful for legal/historical queries.
    """
    candidates = []
    for record in records:
        # Was this version active at query_time?
        if record.recorded_at <= query_time:
            if record.superseded_at is None or record.superseded_at > query_time:
                candidates.append(record)

    if candidates:
        return sorted(candidates, key=lambda r: r.recorded_at)[-1]
    return None
