"""
Memory query safety - enforce citations and review requirements.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Date range filter for memory queries."""
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class MemoryQuery(BaseModel):
    """
    Query for retrieving legal memory.
    
    Default safety: require_reviewed=True, require_citations=True
    Public queries MUST use these defaults.
    """
    query: str
    jurisdiction: Optional[str] = None
    source_types: List[str] = Field(default_factory=list)
    date_range: Optional[DateRange] = None
    require_reviewed: bool = True  # MUST be True for public
    require_citations: bool = True  # MUST be True for public
    max_hits: int = 10


class MemoryHit(BaseModel):
    """Single search result from legal memory."""
    id: str
    text: str
    score: float  # 0.0 to 1.0 relevance score
    source_snapshot_id: str
    citation_url: Optional[str] = None
    jurisdiction: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    reviewed: bool
    warnings: List[str] = Field(default_factory=list)


def validate_public_memory_query(query: MemoryQuery) -> tuple[bool, List[str]]:
    """
    Validate that memory query is safe for public use.
    
    Returns: (is_safe, error_messages)
    """
    errors = []

    # Public queries MUST require reviewed results
    if not query.require_reviewed:
        errors.append("Public memory queries must require_reviewed=True")

    # Public queries MUST require citations
    if not query.require_citations:
        errors.append("Public memory queries must require_citations=True")

    # No citation, no public answer
    if query.require_citations is False:
        errors.append("Cannot serve uncited memory to public users")

    return len(errors) == 0, errors


def filter_memory_hits_for_public(hits: List[MemoryHit]) -> List[MemoryHit]:
    """
    Filter memory hits to only safe-for-public results.
    
    - Must be reviewed
    - Must have citation
    - No warnings that indicate unreliability
    """
    safe_hits = []

    for hit in hits:
        # Filter: unreviewed
        if not hit.reviewed:
            continue

        # Filter: no citation
        if not hit.citation_url:
            continue

        # Filter: warnings indicate unreliability
        if "contradicts_other_source" in hit.warnings:
            continue
        if "low_confidence" in hit.warnings:
            continue
        if "requires_human_review" in hit.warnings:
            continue

        safe_hits.append(hit)

    return safe_hits


def enrich_memory_hit_with_warnings(
    hit: MemoryHit,
    contradictions: Optional[List[str]] = None,
    confidence: Optional[float] = None,
) -> MemoryHit:
    """
    Enrich a memory hit with warning flags.
    
    Warnings are essential for legal integrity.
    """
    if contradictions:
        hit.warnings.append("contradicts_other_source")

    if confidence is not None and confidence < 0.7:
        hit.warnings.append("low_confidence")

    if not hit.reviewed:
        hit.warnings.append("unreviewed")

    if not hit.citation_url:
        hit.warnings.append("no_citation")

    return hit
