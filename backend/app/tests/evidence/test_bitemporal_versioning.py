"""
Bi-temporal versioning tests.

Verifies that legal data versioning preserves history and audit trail.
"""

import pytest
from datetime import datetime, timezone, timedelta
from backend.app.evidence.bitemporal import (
    BiTemporalRecord,
    LegalInstrument,
    PublicEventRecord,
    create_new_version,
    get_record_history,
    get_current_record,
    get_record_at_time,
)


@pytest.fixture
def original_record():
    """Create an original record."""
    return PublicEventRecord(
        id="evt_001",
        title="Missing Person",
        event_type="missing_person",
        description="John Doe, missing since Jan 15",
        location={"lat": 52.0, "lon": -106.0, "label": "Saskatoon, SK"},
        occurred_at=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        valid_from=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        recorded_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        source_snapshot_id="snap_001",
    )


def test_original_record_is_current(original_record):
    """Newly created record should be marked current."""
    assert original_record.is_current is True
    assert original_record.superseded_at is None
    assert original_record.superseded_by_version_id is None


def test_create_new_version_marks_original_superseded(original_record):
    """Creating a new version supersedes the original."""
    old_v, new_v = create_new_version(
        original_record,
        description="John Doe, found safe"
    )

    assert old_v.is_current is False
    assert old_v.superseded_at is not None
    assert old_v.superseded_by_version_id == new_v.version_id
    assert old_v.version_id != new_v.version_id


def test_new_version_is_current(original_record):
    """New version should be marked current."""
    old_v, new_v = create_new_version(
        original_record,
        description="Updated description"
    )

    assert new_v.is_current is True
    assert new_v.superseded_at is None


def test_version_chain_preserved(original_record):
    """Version chain must be preserved in history."""
    versions = [original_record]

    # Create first update
    v1_old, v1_new = create_new_version(versions[-1], description="Update 1")
    versions.append(v1_old)
    versions.append(v1_new)

    # Create second update
    v2_old, v2_new = create_new_version(versions[-1], description="Update 2")
    versions.append(v2_old)
    versions.append(v2_new)

    # Verify chain
    assert versions[0].is_current is False
    assert versions[1].is_current is False
    assert versions[2].is_current is False
    assert versions[3].is_current is True
    assert versions[4].is_current is True  # Latest


def test_get_current_record(original_record):
    """get_current_record returns only the active version."""
    old_v, new_v = create_new_version(original_record, description="Updated")

    versions = [original_record, old_v, new_v]
    current = get_current_record(versions)

    assert current.version_id == new_v.version_id
    assert current.is_current is True


def test_get_record_history_chronological(original_record):
    """get_record_history returns versions in order."""
    old_v, v1 = create_new_version(original_record)
    old_v2, v2 = create_new_version(v1)

    versions = [original_record, old_v, v1, old_v2, v2]
    history = get_record_history(versions)

    # Should be ordered by recorded_at
    assert history[0].recorded_at <= history[1].recorded_at
    assert history[1].recorded_at <= history[2].recorded_at


def test_get_record_at_time_before_creation():
    """Record doesn't exist before it was recorded."""
    record = PublicEventRecord(
        id="evt_001",
        title="Event",
        event_type="incident",
        description="Desc",
        location={"lat": 52.0, "lon": -106.0},
        occurred_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
        recorded_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
        source_snapshot_id="snap_001",
    )

    # Query before it was recorded
    before_record = datetime(2024, 1, 16, 9, 0, 0, tzinfo=timezone.utc)
    result = get_record_at_time([record], before_record)
    assert result is None


def test_get_record_at_time_after_supersession():
    """Can retrieve what version was current at historical time."""
    record1 = PublicEventRecord(
        id="evt_001",
        title="Event v1",
        event_type="incident",
        description="Version 1",
        location={"lat": 52.0, "lon": -106.0},
        occurred_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
        recorded_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
        source_snapshot_id="snap_001",
    )

    old_r1, record2 = create_new_version(record1, title="Event v2", description="Version 2")
    record2.recorded_at = datetime(2024, 1, 17, 10, 0, 0, tzinfo=timezone.utc)

    # Query at time when record1 was current
    query_time = datetime(2024, 1, 16, 11, 0, 0, tzinfo=timezone.utc)
    result = get_record_at_time([old_r1, record2], query_time)

    assert result is not None
    assert result.title == "Event v1"


def test_legal_instrument_versioning():
    """Legal instruments must preserve all versions."""
    statute_v1 = LegalInstrument(
        id="statute_001",
        instrument_type="statute",
        title="Act Respecting Public Safety",
        jurisdiction="SK",
        body="Original text",
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        recorded_at=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        source_snapshot_id="snap_statute_001",
    )

    # Statute amended
    old_statute, statute_v2 = create_new_version(
        statute_v1,
        body="Amended text with new provisions",
        valid_from=datetime(2024, 3, 1, tzinfo=timezone.utc),
    )

    # Original version preserved
    assert old_statute.is_current is False
    assert old_statute.body == "Original text"

    # Amendment tracked
    assert statute_v2.is_current is True
    assert statute_v2.body == "Amended text with new provisions"
    assert statute_v2.superseded_by_version_id is None


def test_never_overwrite_silently():
    """Creating new version never overwrites old version in-place."""
    record1 = PublicEventRecord(
        id="evt_001",
        title="Original",
        event_type="incident",
        description="Original description",
        location={"lat": 52.0, "lon": -106.0},
        occurred_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
        recorded_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
        source_snapshot_id="snap_001",
    )

    original_id = record1.version_id
    old_r1, record2 = create_new_version(record1, title="Updated")

    # Original version_id never changes
    assert old_r1.version_id == original_id
    # But now marked as old
    assert old_r1.is_current is False
