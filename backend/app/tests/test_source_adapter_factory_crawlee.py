"""Factory tests: Verify build_adapter() constructs Crawlee adapters correctly.

Tests that the factory properly instantiates:
- CrawleePoliceReleaseAdapter for crawlee_police_release parser
- CrawleeGovNewsAdapter for crawlee_gov_news parser

All tests use fake settings and mock source registry rows.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ingestion.source_adapter_factory import build_adapter
from app.ingestion.source_adapters import (
    CrawleeGovNewsAdapter,
    CrawleePoliceReleaseAdapter,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _source(
    source_key: str = "test_source",
    parser: str = "crawlee_police_release",
    base_url: str = "https://example.com/news",
    allowed_domains: str = '["example.com"]',
    public_record_authority: str = "news_context",
    source_class: str = "machine_ingest",
    parser_version: str = "crawlee_police_v1",
) -> MagicMock:
    """Build a mock SourceRegistry row."""
    source = MagicMock()
    source.source_key = source_key
    source.parser = parser
    source.base_url = base_url
    source.allowed_domains = allowed_domains
    source.public_record_authority = public_record_authority
    source.source_class = source_class
    source.parser_version = parser_version
    source.config_json = None
    return source


def _settings() -> MagicMock:
    """Build a mock Settings object."""
    settings = MagicMock()
    settings.CANLII_API_KEY = None
    settings.SASKATOON_OPEN_DATA_API_KEY = None
    return settings


# -----------------------------------------------------------------------------
# CrawleePoliceReleaseAdapter factory tests
# -----------------------------------------------------------------------------


class TestFactoryBuildsPoliceCrawleeAdapter:
    def test_factory_builds_police_adapter(self) -> None:
        """build_adapter returns CrawleePoliceReleaseAdapter for crawlee_police_release parser."""
        source = _source(
            source_key="web_monitor_saskatoon_police_news",
            parser="crawlee_police_release",
            base_url="https://www.saskatoonpolice.ca/news",
            allowed_domains='["www.saskatoonpolice.ca", "saskatoonpolice.ca"]',
            public_record_authority="news_context",
            source_class="machine_ingest",
            parser_version="crawlee_police_v1",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert isinstance(adapter, CrawleePoliceReleaseAdapter)

    def test_police_adapter_has_source_key(self) -> None:
        """Built adapter has correct source_key attribute."""
        source = _source(
            source_key="rcmp_sk_news",
            parser="crawlee_police_release",
            base_url="https://www.rcmp-grc.gc.ca",
            allowed_domains='["www.rcmp-grc.gc.ca"]',
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._source_key == "rcmp_sk_news"

    def test_police_adapter_has_base_url(self) -> None:
        """Built adapter has correct base_url attribute."""
        source = _source(
            source_key="web_monitor_saskatoon_police_news",
            parser="crawlee_police_release",
            base_url="https://www.saskatoonpolice.ca/news",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._base_url == "https://www.saskatoonpolice.ca/news"

    def test_police_adapter_has_allowed_domains(self) -> None:
        """Built adapter has correct allowed_domains."""
        source = _source(
            source_key="web_monitor_saskatoon_police_news",
            parser="crawlee_police_release",
            allowed_domains='["www.saskatoonpolice.ca", "saskatoonpolice.ca"]',
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert "www.saskatoonpolice.ca" in adapter._allowed_domains
        assert "saskatoonpolice.ca" in adapter._allowed_domains

    def test_police_adapter_has_public_record_authority(self) -> None:
        """Built adapter has correct public_record_authority."""
        source = _source(
            source_key="web_monitor_saskatoon_police_news",
            parser="crawlee_police_release",
            public_record_authority="news_context",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._public_record_authority == "news_context"

    def test_police_adapter_fetcher_defaults_to_fetch_for_ingestion(self) -> None:
        """Built adapter has fetcher defaulting to fetch_for_ingestion."""
        from app.ingestion.fetcher import fetch_for_ingestion

        source = _source(parser="crawlee_police_release")
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._fetcher is fetch_for_ingestion


# -----------------------------------------------------------------------------
# CrawleeGovNewsAdapter factory tests
# -----------------------------------------------------------------------------


class TestFactoryBuildsGovNewsCrawleeAdapter:
    def test_factory_builds_gov_adapter(self) -> None:
        """build_adapter returns CrawleeGovNewsAdapter for crawlee_gov_news parser."""
        source = _source(
            source_key="sk_justice_ministry",
            parser="crawlee_gov_news",
            base_url="https://www.saskatchewan.ca/government/news",
            allowed_domains='["www.saskatchewan.ca", "saskatchewan.ca"]',
            public_record_authority="news_context",
            source_class="machine_ingest",
            parser_version="crawlee_gov_v1",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert isinstance(adapter, CrawleeGovNewsAdapter)

    def test_gov_adapter_has_source_key(self) -> None:
        """Built adapter has correct source_key attribute."""
        source = _source(
            source_key="sk_justice_ministry",
            parser="crawlee_gov_news",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._source_key == "sk_justice_ministry"

    def test_gov_adapter_has_base_url(self) -> None:
        """Built adapter has correct base_url attribute."""
        source = _source(
            source_key="sk_justice_ministry",
            parser="crawlee_gov_news",
            base_url="https://www.saskatchewan.ca/government/news",
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._base_url == "https://www.saskatchewan.ca/government/news"

    def test_gov_adapter_has_allowed_domains(self) -> None:
        """Built adapter has correct allowed_domains."""
        source = _source(
            source_key="sk_justice_ministry",
            parser="crawlee_gov_news",
            allowed_domains='["www.saskatchewan.ca"]',
        )
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert "www.saskatchewan.ca" in adapter._allowed_domains

    def test_gov_adapter_fetcher_defaults_to_fetch_for_ingestion(self) -> None:
        """Built adapter has fetcher defaulting to fetch_for_ingestion."""
        from app.ingestion.fetcher import fetch_for_ingestion

        source = _source(parser="crawlee_gov_news")
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is not None
        assert adapter._fetcher is fetch_for_ingestion


# -----------------------------------------------------------------------------
# Error handling tests
# -----------------------------------------------------------------------------


class TestFactoryErrorHandling:
    def test_returns_none_for_unknown_parser(self) -> None:
        """build_adapter returns None when parser is not in ADAPTER_REGISTRY."""
        source = _source(parser="unknown_parser_xyz")
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is None

    def test_returns_none_for_empty_parser(self) -> None:
        """build_adapter returns None when source.parser is empty/None."""
        source = _source()
        source.parser = None
        settings = _settings()

        adapter = build_adapter(source, settings)

        assert adapter is None
