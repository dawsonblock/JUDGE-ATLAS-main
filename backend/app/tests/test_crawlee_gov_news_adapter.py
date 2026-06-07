"""Tests: CrawleeGovNewsAdapter.run_with_db() Phase 2 implementation.

Verifies that run_with_db():
1. Constructs a WebMonitorTarget with the adapter's source_key and base_url.
2. Instantiates CrawleeRunner with the target and the supplied db session.
3. Awaits CrawleeRunner.run().
4. Returns the runner's snapshots list.
5. All returned items come from the runner (review gate is the runner's concern).
6. Existing fetch() / parse() / run() stub behaviour is unaffected.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ingestion.source_adapters.crawlee_gov_news import CrawleeGovNewsAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_adapter(
    source_key: str = "sk_justice_ministry",
    base_url: str = "https://www.saskatchewan.ca/government/news",
    allowed_domains_json: str = '["www.saskatchewan.ca"]',
) -> CrawleeGovNewsAdapter:
    return CrawleeGovNewsAdapter(
        source_key=source_key,
        base_url=base_url,
        allowed_domains_json=allowed_domains_json,
    )


def _run(coro):
    """Run a coroutine synchronously inside a test."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Phase 2 tests
# ---------------------------------------------------------------------------

class TestCrawleeGovNewsRunWithDb:
    def test_run_with_db_builds_web_monitor_target(self) -> None:
        """WebMonitorTarget receives correct name and base_url."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=[])

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget"
        ) as MockTarget:
            MockTarget.return_value = MagicMock()
            _run(adapter.run_with_db(db))

        call_kwargs = MockTarget.call_args.kwargs
        assert "sk_justice_ministry" in call_kwargs["name"]
        assert call_kwargs["base_url"] == "https://www.saskatchewan.ca/government/news"

    def test_run_with_db_passes_db_to_runner(self) -> None:
        """CrawleeRunner receives the db session in constructor."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ) as MockRunner, patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            _run(adapter.run_with_db(db))

        _args, _kwargs = MockRunner.call_args
        # CrawleeRunner(target=target, db=db) - db is second positional arg
        assert _args[1] is db if len(_args) > 1 else _kwargs.get("db") is db

    def test_run_with_db_awaits_runner_run(self) -> None:
        """CrawleeRunner.run() is awaited exactly once."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            _run(adapter.run_with_db(db))

        mock_runner.run.assert_awaited_once()

    def test_run_with_db_returns_snapshots(self) -> None:
        """run_with_db returns the runner's snapshots list."""
        adapter = _make_adapter()
        db = MagicMock()

        fake_snapshot = MagicMock()
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=[fake_snapshot])

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            result = _run(adapter.run_with_db(db))

        assert result == [fake_snapshot]

    def test_run_with_db_returns_empty_list_when_no_snapshots(self) -> None:
        """run_with_db returns [] when CrawleeRunner produced nothing."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=[])

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            result = _run(adapter.run_with_db(db))

        assert result == []

    def test_run_with_db_allowed_domains_from_json(self) -> None:
        """allowed_domains_json is parsed and passed to WebMonitorTarget."""
        adapter = _make_adapter(
            allowed_domains_json='["news.gov.sk.ca", "www.saskatchewan.ca"]'
        )
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_gov_news.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_gov_news.WebMonitorTarget"
        ) as MockTarget:
            MockTarget.return_value = MagicMock()
            _run(adapter.run_with_db(db))

        call_kwargs = MockTarget.call_args.kwargs
        assert "news.gov.sk.ca" in call_kwargs["allowed_domains"]
        assert "www.saskatchewan.ca" in call_kwargs["allowed_domains"]

    # ------------------------------------------------------------------
    # Phase 3: Active adapter tests (NotImplementedError removed)
    # ------------------------------------------------------------------

    def test_fetch_now_works_without_error(self) -> None:
        """fetch() is now implemented and returns a list (may be empty)."""
        adapter = _make_adapter()
        result = adapter.fetch()  # Should not raise
        assert isinstance(result, list)

    def test_run_returns_result_without_stub_errors(self) -> None:
        """run() now returns IngestionResult without NotImplementedError."""
        adapter = _make_adapter()
        result = adapter.run()
        # Result may have errors from actual fetch failure, but not NotImplementedError
        for err in result.errors:
            assert "NotImplementedError" not in err
            assert "stub" not in err.lower()
