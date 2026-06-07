"""Tests: CrawleePoliceReleaseAdapter.run_with_db() Phase 2 implementation.

Verifies that run_with_db():
1. Constructs a WebMonitorTarget with source_type="police_news"
   and extractor_type="police_news_index".
2. Instantiates CrawleeRunner with the target and supplied db.
3. Awaits CrawleeRunner.run().
4. Returns runner.snapshots as a list.
5. Existing fetch() / parse() / run() stub behaviour is unaffected.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ingestion.source_adapters.crawlee_police_release import (
    CrawleePoliceReleaseAdapter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_adapter(
    source_key: str = "web_monitor_saskatoon_police_news",
    base_url: str = "https://www.saskatoonpolice.ca/news",
    allowed_domains_json: str = '["www.saskatoonpolice.ca"]',
) -> CrawleePoliceReleaseAdapter:
    return CrawleePoliceReleaseAdapter(
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

class TestCrawleePoliceReleaseRunWithDb:
    def test_run_with_db_sets_police_news_source_type(self) -> None:
        """WebMonitorTarget gets source_type='police_news'."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget"
        ) as MockTarget:
            MockTarget.return_value = MagicMock()
            _run(adapter.run_with_db(db))

        call_kwargs = MockTarget.call_args.kwargs
        assert call_kwargs["source_type"] == "police_news"

    def test_run_with_db_builds_target_with_name(self) -> None:
        """WebMonitorTarget receives a name containing the source_key."""
        adapter = _make_adapter(source_key="rcmp_sk_news")
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget"
        ) as MockTarget:
            MockTarget.return_value = MagicMock()
            _run(adapter.run_with_db(db))

        call_kwargs = MockTarget.call_args.kwargs
        assert "rcmp_sk_news" in call_kwargs["name"]

    def test_run_with_db_passes_db_to_runner(self) -> None:
        """CrawleeRunner receives the db session in constructor."""
        adapter = _make_adapter()
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=None)
        mock_runner.snapshots = []

        with patch(
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ) as MockRunner, patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget",
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
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            _run(adapter.run_with_db(db))

        mock_runner.run.assert_awaited_once()

    def test_run_with_db_returns_snapshots(self) -> None:
        """run_with_db returns the list of snapshots from the runner."""
        adapter = _make_adapter()
        db = MagicMock()

        snap1, snap2 = MagicMock(), MagicMock()
        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=[snap1, snap2])

        with patch(
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            result = _run(adapter.run_with_db(db))

        assert result == [snap1, snap2]

    def test_run_with_db_works_for_rcmp_source_key(self) -> None:
        """run_with_db works for the rcmp_sk_news source key variant."""
        adapter = _make_adapter(
            source_key="rcmp_sk_news",
            base_url="https://www.rcmp-grc.gc.ca/en/news/sk",
            allowed_domains_json='["www.rcmp-grc.gc.ca"]',
        )
        db = MagicMock()

        mock_runner = MagicMock()
        mock_runner.run = AsyncMock(return_value=[])

        with patch(
            "app.ingestion.source_adapters.crawlee_police_release.CrawleeRunner",
            return_value=mock_runner,
        ), patch(
            "app.ingestion.source_adapters.crawlee_police_release.WebMonitorTarget",
            return_value=MagicMock(),
        ):
            result = _run(adapter.run_with_db(db))

        assert result == []

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
