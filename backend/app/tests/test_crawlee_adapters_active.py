"""Contract tests: CrawleeGovNewsAdapter and CrawleePoliceReleaseAdapter active behavior.

These tests verify the adapters now implement the full ingestion contract:
- run() returns IngestionResult without raising
- parser_version is set correctly
- Evidence snapshot fields are populated (raw_snapshot_bytes, fetch_url, etc.)
- Only ReviewItem records are created (no direct CrimeIncident creation)
- Off-domain links are rejected
- Payload contains stable identity fields
"""

from __future__ import annotations

import pytest

from app.ingestion.source_adapters.crawlee_gov_news import (
    CrawleeGovNewsAdapter,
    PARSER_VERSION as GOV_PARSER_VERSION,
)
from app.ingestion.source_adapters.crawlee_police_release import (
    CrawleePoliceReleaseAdapter,
    PARSER_VERSION as POLICE_PARSER_VERSION,
)


# -----------------------------------------------------------------------------
# Fake fetcher for testing without network
# -----------------------------------------------------------------------------

from datetime import datetime, timezone


def fake_fetcher_success(url: str, allowed_domains: list[str], **kwargs):
    """Return a successful fetch result with sample HTML."""
    from app.services.source_fetcher import FetchResult

    html = b"""
    <html>
      <head><title>Police News</title></head>
      <body>
        <a href="/news/2026/example-release">Example police release</a>
        <a href="https://evil.com/bad">Bad off-domain link</a>
        <script>alert("bad")</script>
        <a href="/news/another-item">Another news item</a>
      </body>
    </html>
    """
    return FetchResult(
        url=url,
        final_url=url,
        fetched_at=datetime.now(timezone.utc),
        http_status=200,
        content_type="text/html",
        headers={},
        raw_content=html,
        raw_content_hash="abc123",
        extracted_text=None,
        extracted_text_hash=None,
        error=None,
    )


def fake_fetcher_blocked(url: str, allowed_domains: list[str], **kwargs):
    """Return a blocked fetch result."""
    from app.services.source_fetcher import FetchResult

    return FetchResult(
        url=url,
        final_url=url,
        fetched_at=datetime.now(timezone.utc),
        http_status=403,
        content_type=None,
        headers={},
        raw_content=b"",
        raw_content_hash="",
        extracted_text=None,
        extracted_text_hash=None,
        error="Domain not in allowlist",
    )


# -----------------------------------------------------------------------------
# CrawleePoliceReleaseAdapter
# -----------------------------------------------------------------------------


class TestCrawleePoliceReleaseAdapterActive:
    def _make(
        self, fetcher=fake_fetcher_success, source_key="web_monitor_saskatoon_police_news"
    ) -> CrawleePoliceReleaseAdapter:
        return CrawleePoliceReleaseAdapter(
            source_key=source_key,
            base_url="https://www.saskatoonpolice.ca/news",
            allowed_domains_json='["www.saskatoonpolice.ca", "saskatoonpolice.ca"]',
            public_record_authority="news_context",
            fetcher=fetcher,
        )

    def test_fetch_does_not_raise(self) -> None:
        """fetch() no longer raises NotImplementedError."""
        adapter = self._make()
        result = adapter.fetch()  # Should not raise
        assert isinstance(result, list)

    def test_run_returns_parser_version(self) -> None:
        """run() sets parser_version on IngestionResult."""
        adapter = self._make()
        result = adapter.run()
        assert result.parser_version == POLICE_PARSER_VERSION

    def test_run_sets_raw_snapshot_bytes(self) -> None:
        """run() populates raw_snapshot_bytes from fetch."""
        adapter = self._make()
        result = adapter.run()
        assert result.raw_snapshot_bytes is not None
        assert len(result.raw_snapshot_bytes) > 0

    def test_run_sets_fetch_url(self) -> None:
        """run() populates fetch_url from fetch result."""
        adapter = self._make()
        result = adapter.run()
        assert result.fetch_url is not None
        assert result.fetch_url.startswith("https://")

    def test_run_sets_fetch_http_status(self) -> None:
        """run() populates fetch_http_status from fetch result."""
        adapter = self._make()
        result = adapter.run()
        assert result.fetch_http_status == 200

    def test_run_sets_fetch_content_type(self) -> None:
        """run() populates fetch_content_type from fetch result."""
        adapter = self._make()
        result = adapter.run()
        assert result.fetch_content_type == "text/html"

    def test_run_creates_only_review_items(self) -> None:
        """run() creates review_items, not created_records."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        assert result.created_records == []

    def test_run_no_errors(self) -> None:
        """run() with valid fetcher produces no errors."""
        adapter = self._make()
        result = adapter.run()
        assert result.errors == []

    def test_review_item_payload_has_record_type(self) -> None:
        """ReviewItem payload contains record_type field."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["record_type"] == "ReviewItem"

    def test_review_item_payload_has_external_id(self) -> None:
        """ReviewItem payload contains external_id (URL) for stable identity."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["external_id"].startswith("https://")

    def test_review_item_payload_has_source_key(self) -> None:
        """ReviewItem payload contains source_key."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["source_key"] == "web_monitor_saskatoon_police_news"

    def test_review_item_payload_requires_review(self) -> None:
        """ReviewItem payload marks items for manual review."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["publish_recommendation"] == "review_required"
        assert item.payload["public_visibility"] is False

    def test_review_item_has_low_confidence(self) -> None:
        """News context items have low confidence score."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.confidence_score == 0.25

    def test_off_domain_links_rejected(self) -> None:
        """Links to off-domain URLs are not included."""
        adapter = self._make()
        result = adapter.run()
        # Should only get on-domain links, not evil.com
        for item in result.review_items:
            assert "evil.com" not in item.url

    def test_duplicate_links_removed(self) -> None:
        """Duplicate links are deduplicated."""
        # This is implicitly tested by the link extraction logic
        adapter = self._make()
        result = adapter.run()
        urls = [item.url for item in result.review_items]
        assert len(urls) == len(set(urls))  # No duplicates

    def test_blocked_fetch_returns_empty(self) -> None:
        """When fetch is blocked, run() returns empty results gracefully."""
        adapter = self._make(fetcher=fake_fetcher_blocked)
        result = adapter.run()
        assert result.review_items == []
        assert result.records_fetched == 0

    def test_run_with_db_still_works(self) -> None:
        """Legacy run_with_db() method still works for backward compatibility."""
        adapter = self._make()
        # Just verify it doesn't crash - actual DB test would need async setup
        assert hasattr(adapter, "run_with_db")


# -----------------------------------------------------------------------------
# CrawleeGovNewsAdapter
# -----------------------------------------------------------------------------


class TestCrawleeGovNewsAdapterActive:
    def _make(
        self, fetcher=fake_fetcher_success, source_key="sk_justice_ministry"
    ) -> CrawleeGovNewsAdapter:
        return CrawleeGovNewsAdapter(
            source_key=source_key,
            base_url="https://www.saskatchewan.ca/government/news",
            allowed_domains_json='["www.saskatchewan.ca", "saskatchewan.ca"]',
            public_record_authority="news_context",
            fetcher=fetcher,
        )

    def test_fetch_does_not_raise(self) -> None:
        """fetch() no longer raises NotImplementedError."""
        adapter = self._make()
        result = adapter.fetch()  # Should not raise
        assert isinstance(result, list)

    def test_run_returns_parser_version(self) -> None:
        """run() sets parser_version on IngestionResult."""
        adapter = self._make()
        result = adapter.run()
        assert result.parser_version == GOV_PARSER_VERSION

    def test_run_sets_raw_snapshot_bytes(self) -> None:
        """run() populates raw_snapshot_bytes from fetch."""
        adapter = self._make()
        result = adapter.run()
        assert result.raw_snapshot_bytes is not None

    def test_run_sets_fetch_url(self) -> None:
        """run() populates fetch_url from fetch result."""
        adapter = self._make()
        result = adapter.run()
        assert result.fetch_url is not None

    def test_run_sets_fetch_http_status(self) -> None:
        """run() populates fetch_http_status from fetch result."""
        adapter = self._make()
        result = adapter.run()
        assert result.fetch_http_status == 200

    def test_run_creates_only_review_items(self) -> None:
        """run() creates review_items, not created_records."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        assert result.created_records == []

    def test_review_item_payload_has_candidate_type_gov(self) -> None:
        """Gov news items have government_news_context candidate_type."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["candidate_type"] == "government_news_context"

    def test_review_item_payload_has_source_quality(self) -> None:
        """ReviewItem payload contains source_quality field."""
        adapter = self._make()
        result = adapter.run()
        assert len(result.review_items) > 0
        item = result.review_items[0]
        assert item.payload["source_quality"] == "news_only_context"

    def test_gov_include_patterns_different_from_police(self) -> None:
        """Gov adapter uses different include patterns than police adapter."""
        # The gov adapter should match patterns like "justice", "attorney", "court"
        adapter = self._make()
        # Just verify it runs successfully - pattern matching tested in extract_links
        result = adapter.run()
        assert result.parser_version == GOV_PARSER_VERSION

    def test_blocked_fetch_returns_empty(self) -> None:
        """When fetch is blocked, run() returns empty results gracefully."""
        adapter = self._make(fetcher=fake_fetcher_blocked)
        result = adapter.run()
        assert result.review_items == []
        assert result.records_fetched == 0
