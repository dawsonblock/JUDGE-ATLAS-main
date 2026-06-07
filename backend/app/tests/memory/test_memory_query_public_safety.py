"""
Memory query public safety tests.
"""

import pytest
from datetime import datetime, timezone
from backend.app.memory.memory_query import (
    MemoryQuery,
    MemoryHit,
    DateRange,
    validate_public_memory_query,
    filter_memory_hits_for_public,
    enrich_memory_hit_with_warnings,
)


@pytest.fixture
def safe_memory_query():
    """Safe query for public use."""
    return MemoryQuery(
        query="missing person Saskatchewan",
        jurisdiction="SK",
        source_types=["police", "news"],
        require_reviewed=True,
        require_citations=True,
        max_hits=10,
    )


@pytest.fixture
def reviewed_hit():
    """A reviewed, cited hit."""
    return MemoryHit(
        id="hit_001",
        text="Missing person alert from official source",
        score=0.95,
        source_snapshot_id="snap_001",
        citation_url="https://example.gov.sk.ca/alert",
        jurisdiction="SK",
        valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
        reviewed=True,
    )


@pytest.fixture
def unreviewed_hit():
    """An unreviewed hit."""
    return MemoryHit(
        id="hit_002",
        text="Unverified police information",
        score=0.65,
        source_snapshot_id="snap_002",
        citation_url="https://example.com",
        jurisdiction="SK",
        reviewed=False,
    )


@pytest.fixture
def uncited_hit():
    """Hit without citation."""
    return MemoryHit(
        id="hit_003",
        text="Information from unknown source",
        score=0.50,
        source_snapshot_id="snap_003",
        citation_url=None,  # No citation!
        jurisdiction="SK",
        reviewed=True,
    )


def test_safe_query_passes_validation(safe_memory_query):
    """Safe query configuration passes validation."""
    is_safe, errors = validate_public_memory_query(safe_memory_query)
    assert is_safe is True
    assert len(errors) == 0


def test_unreviewed_query_fails_validation():
    """Query with require_reviewed=False fails."""
    query = MemoryQuery(
        query="test",
        require_reviewed=False,  # Unsafe!
        require_citations=True,
    )
    is_safe, errors = validate_public_memory_query(query)
    assert is_safe is False
    assert any("require_reviewed" in e for e in errors)


def test_uncited_query_fails_validation():
    """Query with require_citations=False fails."""
    query = MemoryQuery(
        query="test",
        require_reviewed=True,
        require_citations=False,  # Unsafe!
    )
    is_safe, errors = validate_public_memory_query(query)
    assert is_safe is False
    assert any("require_citations" in e for e in errors)


def test_filter_excludes_unreviewed(reviewed_hit, unreviewed_hit):
    """Filter excludes unreviewed hits."""
    hits = [reviewed_hit, unreviewed_hit]
    filtered = filter_memory_hits_for_public(hits)

    assert len(filtered) == 1
    assert filtered[0].id == "hit_001"


def test_filter_excludes_uncited(reviewed_hit, uncited_hit):
    """Filter excludes hits without citations."""
    hits = [reviewed_hit, uncited_hit]
    filtered = filter_memory_hits_for_public(hits)

    assert len(filtered) == 1
    assert filtered[0].id == "hit_001"


def test_filter_excludes_contradictions(reviewed_hit):
    """Filter excludes hits marked as contradicting other sources."""
    contradictory_hit = MemoryHit(
        id="hit_004",
        text="Contradicting information",
        score=0.80,
        source_snapshot_id="snap_004",
        citation_url="https://example.com",
        reviewed=True,
        warnings=["contradicts_other_source"],
    )

    hits = [reviewed_hit, contradictory_hit]
    filtered = filter_memory_hits_for_public(hits)

    assert len(filtered) == 1
    assert filtered[0].id == "hit_001"


def test_enrich_with_low_confidence_warning(reviewed_hit):
    """Low confidence triggers warning."""
    enriched = enrich_memory_hit_with_warnings(reviewed_hit, confidence=0.65)

    assert "low_confidence" in enriched.warnings


def test_enrich_with_contradiction_warning(reviewed_hit):
    """Contradictions trigger warning."""
    enriched = enrich_memory_hit_with_warnings(
        reviewed_hit,
        contradictions=["hit_005", "hit_006"]
    )

    assert "contradicts_other_source" in enriched.warnings


def test_default_query_settings_safe():
    """Default MemoryQuery settings are safe."""
    default_query = MemoryQuery(query="test")

    assert default_query.require_reviewed is True
    assert default_query.require_citations is True


def test_no_public_answer_without_citation(reviewed_hit):
    """Memory without citation cannot be served publicly."""
    hit_no_citation = MemoryHit(
        id="hit_005",
        text="Information",
        score=0.90,
        source_snapshot_id="snap_005",
        citation_url=None,
        reviewed=True,
    )

    # Even if reviewed, no citation = not public-safe
    filtered = filter_memory_hits_for_public([hit_no_citation])
    assert len(filtered) == 0


def test_all_warnings_tracked():
    """All warning types are tracked."""
    hit = MemoryHit(
        id="hit_006",
        text="Test",
        score=0.50,
        source_snapshot_id="snap_006",
        citation_url=None,
        reviewed=False,
    )

    enriched = enrich_memory_hit_with_warnings(hit)

    assert "unreviewed" in enriched.warnings
    assert "no_citation" in enriched.warnings
