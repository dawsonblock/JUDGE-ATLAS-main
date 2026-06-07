"""Tests for SKCourtOfAppealRSSAdapter.

These tests verify that the Saskatchewan Court of Appeal RSS adapter:
- Correctly fetches and parses RSS feeds
- Extracts neutral citations from titles
- Produces valid IngestionResults with evidence snapshot fields
- Handles errors gracefully
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Any

from app.ingestion.adapters import IngestionResult
from app.ingestion.source_adapters.sk_court_of_appeal_rss import (
    SKCourtOfAppealRSSAdapter,
    _clean_title,
    _parse_date,
)


# -----------------------------------------------------------------------------
# Test fixtures
# -----------------------------------------------------------------------------

@dataclass
class FakeFetchResult:
    """Fake fetch result for testing."""
    raw_content: bytes
    http_status: int = 200
    content_type: str = "application/rss+xml"
    final_url: str | None = None
    error: str | None = None


def fake_fetcher_success(url: str, allowed_domains: list[str]) -> FakeFetchResult:
    """Return a successful fetch result with sample SKCA RSS."""
    sample_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Saskatchewan Court of Appeal Judgments</title>
    <link>https://sasklawcourts.ca/</link>
    <description>Recently published Court of Appeal decisions</description>
    <item>
      <title>Smith v. Jones - 2024 SKCA 123</title>
      <link>https://sasklawcourts.ca/decisions/2024-skca-123</link>
      <description>Decision regarding contract interpretation.</description>
      <pubDate>Mon, 15 Jan 2024 10:30:00 GMT</pubDate>
    </item>
    <item>
      <title>R. v. Doe 2023 SKCA 45</title>
      <link>https://sasklawcourts.ca/decisions/2023-skca-45</link>
      <description>Criminal law decision regarding evidence.</description>
      <pubDate>2023-06-20</pubDate>
    </item>
    <item>
      <title>ABC Corp. v. XYZ Ltd.</title>
      <link>https://sasklawcourts.ca/decisions/abc-v-xyz</link>
      <description>Civil procedure decision without neutral citation.</description>
      <pubDate>Tue, 10 Oct 2023 14:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""
    return FakeFetchResult(raw_content=sample_rss)


def fake_fetcher_blocked(url: str, allowed_domains: list[str]) -> FakeFetchResult:
    """Return a blocked fetch result."""
    return FakeFetchResult(raw_content=b"", error="Domain not in allowlist")


def fake_fetcher_error(url: str, allowed_domains: list[str]) -> FakeFetchResult:
    """Return a fetch result with HTTP error."""
    return FakeFetchResult(raw_content=b"", http_status=500)


# -----------------------------------------------------------------------------
# Unit tests for helper functions
# -----------------------------------------------------------------------------

class TestCleanTitle:
    """Tests for _clean_title function."""

    def test_extracts_citation_with_hyphen(self):
        title = "Smith v. Jones - 2024 SKCA 123"
        case_name, citation = _clean_title(title)
        assert case_name == "Smith v. Jones"
        assert citation == "2024 SKCA 123"

    def test_extracts_citation_without_hyphen(self):
        title = "R. v. Doe 2023 SKCA 45"
        case_name, citation = _clean_title(title)
        assert "R. v. Doe" in case_name
        assert citation == "2023 SKCA 45"

    def test_returns_none_citation_when_not_present(self):
        title = "ABC Corp. v. XYZ Ltd."
        case_name, citation = _clean_title(title)
        assert case_name == "ABC Corp. v. XYZ Ltd."
        assert citation is None

    def test_handles_whitespace(self):
        title = "  Case Name   -   2024 SKCA 99  "
        case_name, citation = _clean_title(title)
        assert case_name == "Case Name"
        assert citation == "2024 SKCA 99"


class TestParseDate:
    """Tests for _parse_date function."""

    def test_parses_iso_format(self):
        assert _parse_date("2024-01-15") == "2024-01-15"

    def test_parses_rfc_2822_format(self):
        assert _parse_date("Mon, 15 Jan 2024 10:30:00 GMT") == "2024-01-15"

    def test_parses_another_rfc_format(self):
        assert _parse_date("Tue, 10 Oct 2023 14:00:00 GMT") == "2023-10-10"

    def test_returns_none_for_empty_string(self):
        assert _parse_date("") is None

    def test_returns_none_for_none(self):
        assert _parse_date(None) is None

    def test_returns_original_for_unknown_month(self):
        """Unknown month names must not silently default to January."""
        original = "15 Foo 2024 10:30:00 GMT"
        assert _parse_date(original) == original


# -----------------------------------------------------------------------------
# Adapter unit tests
# -----------------------------------------------------------------------------

class TestSKCourtOfAppealRSSAdapter:
    """Tests for SKCourtOfAppealRSSAdapter."""

    def _make_adapter(self, fetcher: Any = None) -> SKCourtOfAppealRSSAdapter:
        return SKCourtOfAppealRSSAdapter(
            source_key="sk_court_of_appeal_test",
            base_url="https://sasklawcourts.ca",
            allowed_domains_json='["sasklawcourts.ca"]',
            fetcher=fetcher or fake_fetcher_success,
        )

    def test_fetch_returns_items(self):
        adapter = self._make_adapter()
        items = adapter.fetch()
        assert len(items) == 3
        assert items[0]["title"] == "Smith v. Jones - 2024 SKCA 123"
        assert items[0]["link"] == "https://sasklawcourts.ca/decisions/2024-skca-123"

    def test_fetch_populates_evidence_fields(self):
        adapter = self._make_adapter()
        adapter.fetch()
        assert adapter._raw_bytes is not None
        assert adapter._fetch_http_status == 200
        assert adapter._fetch_content_type == "application/rss+xml"
        assert adapter._fetch_url is not None

    def test_fetch_handles_blocked_domain(self):
        adapter = self._make_adapter(fetcher=fake_fetcher_blocked)
        items = adapter.fetch()
        assert items == []

    def test_parse_returns_records(self):
        adapter = self._make_adapter()
        raw = adapter.fetch()
        records = adapter.parse(raw)
        assert len(records) == 3

    def test_parse_extracts_citations(self):
        adapter = self._make_adapter()
        raw = adapter.fetch()
        records = adapter.parse(raw)
        # First item has citation
        assert records[0].payload["neutral_citation"] == "2024 SKCA 123"
        # Second item has citation
        assert records[1].payload["neutral_citation"] == "2023 SKCA 45"
        # Third item has no citation
        assert records[2].payload["neutral_citation"] is None

    def test_parse_extracts_dates(self):
        adapter = self._make_adapter()
        raw = adapter.fetch()
        records = adapter.parse(raw)
        assert records[0].payload["published_at"] == "2024-01-15"
        assert records[1].payload["published_at"] == "2023-06-20"
        assert records[2].payload["published_at"] == "2023-10-10"

    def test_run_returns_ingestion_result(self):
        adapter = self._make_adapter()
        result = adapter.run()
        assert result.source_key == "sk_court_of_appeal_test"
        assert result.records_fetched == 3
        assert len(result.review_items) == 3
        assert result.success  # No errors

    def test_run_populates_evidence_snapshot(self):
        adapter = self._make_adapter()
        result = adapter.run()
        assert result.raw_snapshot_bytes is not None
        assert result.fetch_http_status == 200
        assert result.fetch_content_type == "application/rss+xml"
        assert result.fetch_url is not None

    def test_run_sets_confidence_based_on_citation(self):
        adapter = self._make_adapter()
        result = adapter.run()
        # Items with citations get higher confidence
        assert result.review_items[0].confidence_score == 0.8  # Has citation
        assert result.review_items[2].confidence_score == 0.6  # No citation

    def test_run_handles_fetch_error(self):
        adapter = self._make_adapter(fetcher=fake_fetcher_error)
        result = adapter.run()
        # Should not crash, but may have empty records
        assert isinstance(result.records_fetched, int)

    def test_review_items_have_required_fields(self):
        adapter = self._make_adapter()
        result = adapter.run()
        for item in result.review_items:
            assert item.source_key is not None
            assert item.headline is not None
            assert item.url is not None
            assert item.payload is not None


# -----------------------------------------------------------------------------
# Integration tests (network optional)
# -----------------------------------------------------------------------------

@pytest.mark.network_optional
class TestSKCourtOfAppealRSSAdapterLive:
    """Optional live tests against real SKCA RSS feed.

    These tests require network access and may fail if:
    - The feed is down
    - The feed format changes
    - The site blocks automated requests
    """

    def test_live_fetch_returns_items(self):
        """Test actual fetch against live RSS feed."""
        adapter = SKCourtOfAppealRSSAdapter(
            source_key="sk_court_of_appeal",
            allowed_domains_json='["sasklawcourts.ca", "www.sasklawcourts.ca"]',
        )
        items = adapter.fetch()
        # Feed should return items (may be empty if feed is down or format
        # changed).  We only assert structure, not content.
        assert isinstance(items, list)
        if items:
            assert "title" in items[0] or "link" in items[0]

    def test_live_run_produces_valid_result(self):
        """Test full run against live RSS feed."""
        adapter = SKCourtOfAppealRSSAdapter(
            source_key="sk_court_of_appeal",
            allowed_domains_json='["sasklawcourts.ca", "www.sasklawcourts.ca"]',
        )
        result = adapter.run()
        assert result.source_key == "sk_court_of_appeal"
        # External feeds can be down or return non-XML; run() must still
        # return a valid IngestionResult (errors captured, not raised).
        assert isinstance(result, IngestionResult)
        assert isinstance(result.records_fetched, int)
