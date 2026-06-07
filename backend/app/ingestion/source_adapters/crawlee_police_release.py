"""Adapter for police/RCMP news-release pages via Crawlee.

Handles source keys: ``web_monitor_saskatoon_police_news``, ``rcmp_sk_news``
Parser key: ``crawlee_police_release``
Creates: ``ReviewItem`` records only (news context — no direct public record authority)

Evidence contract: every run() call that fetches data must set
    result.raw_snapshot_bytes, result.fetch_http_status,
    result.fetch_content_type, result.fetch_url, and result.parser_version.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ingestion.adapters import (
    CanadianSourceAdapter,
    CreatedReviewItem,
    IngestionResult,
    ParsedRecord,
)
from app.ingestion.fetcher import FetchCallable, fetch_for_ingestion, parse_allowed_domains
from app.ingestion.source_rules import check_domain_allowed, check_record_type_allowed
from app.ingestion.source_adapters.web_monitor_base import stable_external_id

# Import web_monitor classes at module level for backward compatibility with tests
from app.ingestion.web_monitor.crawlee_runner import CrawleeRunner
from app.ingestion.web_monitor.source_targets import WebMonitorTarget

logger = logging.getLogger(__name__)

_RECORD_TYPE = "ReviewItem"
PARSER_VERSION = "crawlee_police_v1"


class CrawleePoliceReleaseAdapter(CanadianSourceAdapter):
    """Crawl police news-release pages and produce ReviewItem candidates.

    This adapter uses the project's approved fetcher to crawl news-release index
    pages from police services and converts each discovered article into a
    ``ReviewItem`` for human review. It does **not** auto-publish; all items
    require manual review before any judge/defendant associations are made.

    The adapter obeys the ingestion evidence contract:
    - Returns IngestionResult with all required fields
    - Sets raw_snapshot_bytes for evidence preservation
    - Uses fetch_for_ingestion for SSRF protection and domain allowlisting
    """

    def __init__(
        self,
        source_key: str,
        base_url: str,
        allowed_domains_json: str | None = None,
        public_record_authority: str | None = None,
        fetcher: FetchCallable | None = None,
        max_items: int = 25,
    ) -> None:
        self._source_key = source_key
        self._base_url = base_url.rstrip("/")
        self._allowed_domains_json = allowed_domains_json or "[]"
        self._allowed_domains = parse_allowed_domains(self._allowed_domains_json)
        self._public_record_authority = public_record_authority
        self._fetcher = fetcher or fetch_for_ingestion
        self._max_items = max_items
        # Evidence snapshot fields — populated during fetch().
        self._raw_bytes: bytes | None = None
        self._fetch_http_status: int | None = None
        self._fetch_content_type: str | None = None
        self._fetch_url: str | None = None

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch and extract news article links from the base URL.

        Uses the project-approved fetcher with SSRF protection and domain
        allowlisting. Extracts links matching police/news patterns.
        """
        from app.ingestion.source_adapters.web_monitor_base import extract_links

        fetch_url = self._base_url
        result = self._fetcher(
            fetch_url,
            self._allowed_domains,
            timeout_seconds=30,
            max_bytes=512_000,
        )

        if result.error:
            logger.warning(
                "Fetch blocked/failed for %s: %s", self._source_key, result.error
            )
            return []

        # Preserve evidence for snapshot contract.
        self._raw_bytes = result.raw_content
        self._fetch_http_status = result.http_status
        self._fetch_content_type = result.content_type or "text/html"
        self._fetch_url = result.final_url or fetch_url

        html = (result.raw_content or b"").decode("utf-8", errors="replace")

        items = extract_links(
            html=html,
            base_url=self._fetch_url,
            allowed_domains=self._allowed_domains,
            include_patterns=[
                "news",
                "release",
                "media",
                "rcmp",
                "police",
            ],
            exclude_patterns=[
                "facebook",
                "twitter",
                "x.com",
                "youtube",
                "privacy",
                "terms",
                "contact",
            ],
            max_links=self._max_items,
        )

        # Add extracted text for each item
        for item in items:
            item["text"] = item.get("headline", "")  # Minimal text extraction
            item["record_type"] = _RECORD_TYPE

        return items

    def parse(self, raw: list[dict[str, Any]]) -> list[ParsedRecord]:
        """Transform raw crawled items into ParsedRecord objects."""
        records: list[ParsedRecord] = []
        # Record type gate — constant per adapter run, checked once.
        record_type_violation = check_record_type_allowed(
            _RECORD_TYPE,
            self._public_record_authority,
            f'["{_RECORD_TYPE}"]',
        )
        if record_type_violation:
            logger.warning("Record type gate failed: %s", record_type_violation.detail)
            return records

        for item in raw:
            url = item.get("url", "")

            # Per-URL domain gate
            url_violation = check_domain_allowed(url, self._allowed_domains_json)
            if url_violation:
                logger.warning(
                    "URL domain rejected for %s: %s",
                    self._source_key,
                    url_violation.detail,
                )
                continue

            # Stable external_id — falls back to a hash when URL is missing.
            external_id = url or stable_external_id(
                self._source_key,
                item.get("headline", ""),
                item.get("published_at", ""),
            )

            # Build payload with stable identity fields
            payload = {
                "record_type": _RECORD_TYPE,
                "source_key": self._source_key,
                "external_id": external_id,
                "headline": item.get("headline"),
                "url": url,
                "extracted_text": item.get("text"),
                "published_at": item.get("published_at"),
                "source_quality": "news_only_context",
                "privacy_status": "needs_review",
                "publish_recommendation": "review_required",
                "public_visibility": False,
                "candidate_type": "crime_incident_context",
                "parser_version": PARSER_VERSION,
            }

            records.append(
                ParsedRecord(
                    source_name=self._source_key,
                    source_key=self._source_key,
                    record_type=_RECORD_TYPE,
                    external_id=external_id,
                    payload=payload,
                    source_url=url,
                    source_quality="news_only_context",
                )
            )
        return records

    def run(self) -> IngestionResult:
        """Execute a full fetch → parse cycle and return an IngestionResult.

        This is the primary production ingestion path. It does NOT require
        database access — the source_runner handles persistence.

        Returns:
            IngestionResult with evidence snapshot fields set per contract.
        """
        result = IngestionResult(
            source_key=self._source_key,
            parser_version=PARSER_VERSION,
        )
        try:
            raw = self.fetch()
            result.records_fetched = len(raw)

            # Propagate evidence snapshot fields per contract.
            result.raw_snapshot_bytes = self._raw_bytes
            result.fetch_http_status = self._fetch_http_status
            result.fetch_content_type = self._fetch_content_type
            result.fetch_url = self._fetch_url

            parsed = self.parse(raw)
            result.records_skipped = len(raw) - len(parsed)

            for p in parsed:
                result.review_items.append(
                    CreatedReviewItem(
                        source_key=p.source_key,
                        headline=p.payload.get("headline"),
                        url=p.source_url,
                        extracted_text=p.payload.get("extracted_text"),
                        confidence_score=0.25,  # Low confidence for news context
                        payload=p.payload,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled error in %s adapter", self._source_key)
            result.errors.append(str(exc))
        return result

    async def run_with_db(self, db: object) -> list[object]:
        """Legacy web-monitor runner bridge.

        Deprecated for normal ingestion. The production ingestion path is run(),
        which returns IngestionResult and lets source_runner persist snapshots
        and review items.

        This method is retained only for web-monitor compatibility tests.
        """
        try:
            allowed_domains: list[str] = json.loads(self._allowed_domains_json)
        except (ValueError, TypeError, json.JSONDecodeError):
            allowed_domains = []

        target = WebMonitorTarget(
            name=f"Police News — {self._source_key}",
            source_type="police_news",
            base_url=self._base_url,
            allowed_domains=allowed_domains,
            start_urls=[self._base_url],
            max_requests=25,
            max_depth=1,
        )
        runner = CrawleeRunner(target=target, db=db)
        review_items = await runner.run()
        return review_items
