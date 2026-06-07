"""Adapter for Saskatchewan government news pages via Crawlee.

Handles source key: ``sk_justice_ministry``
Parser key: ``crawlee_gov_news``
Creates: ``ReviewItem`` records only (news context)
Authority: ``news_context``

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
PARSER_VERSION = "crawlee_gov_v1"


class CrawleeGovNewsAdapter(CanadianSourceAdapter):
    """Crawl Saskatchewan government news pages and produce ReviewItem candidates.

    Government ministry news pages (e.g. Justice and Attorney General) are
    scraped using the project-approved fetcher. Each news release or
    announcement creates a ``ReviewItem`` for human review. No auto-publish;
    all items require manual review.

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
        """Fetch listing page and extract article links (depth 1).

        Uses the project-approved fetcher with SSRF protection and domain
        allowlisting. Extracts links matching government/news patterns.
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
                "justice",
                "attorney",
                "court",
                "corrections",
                "policing",
                "crime",
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

        # Add placeholder fields that will be populated by fetch_article_depth()
        for item in items:
            item["record_type"] = _RECORD_TYPE

        return items

    def fetch_article_depth(self, item: dict[str, Any]) -> dict[str, Any]:
        """Fetch individual article and extract content (depth 2).

        Enhances the item with full article content, hashes, and metadata.
        """
        from app.ingestion.source_adapters.crawlee_enhanced import (
            extract_body_text,
            extract_date_from_html,
            extract_title_from_html,
            compute_hashes,
        )

        url = item.get("url", "")
        if not url:
            item["text"] = ""
            item["content_hash"] = ""
            item["snapshot_hash"] = ""
            return item

        # Fetch the individual article
        result = self._fetcher(
            url,
            self._allowed_domains,
            timeout_seconds=30,
            max_bytes=512_000,
        )

        if result.error or not result.raw_content:
            logger.debug("Failed to fetch article %s: %s", url, result.error)
            item["text"] = item.get("headline", "")
            item["content_hash"] = ""
            item["snapshot_hash"] = ""
            item["fetch_status"] = "failed"
            return item

        try:
            html_content = result.raw_content.decode("utf-8", errors="replace")

            # Extract enhanced metadata
            title = extract_title_from_html(html_content) or item.get("headline", "")
            published_at = extract_date_from_html(html_content)
            body_text = extract_body_text(html_content, max_length=8000)

            # Reject if body is too short
            if len(body_text) < 100:
                logger.debug("Article %s too short (%d chars)", url, len(body_text))
                item["text"] = item.get("headline", "")
                item["content_hash"] = ""
                item["snapshot_hash"] = ""
                item["fetch_status"] = "too_short"
                return item

            # Compute hashes
            content_hash, snapshot_hash = compute_hashes(body_text, result.raw_content)

            # Update item with full content
            item["headline"] = title
            item["text"] = body_text
            item["published_at"] = published_at
            item["content_hash"] = content_hash
            item["snapshot_hash"] = snapshot_hash
            item["http_status"] = result.http_status or 200
            item["content_type"] = result.content_type or "text/html"
            item["fetch_status"] = "success"

        except Exception as exc:
            logger.debug("Error processing article %s: %s", url, exc)
            item["text"] = item.get("headline", "")
            item["content_hash"] = ""
            item["snapshot_hash"] = ""
            item["fetch_status"] = "error"

        return item

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
                continue

            # Stable external_id — falls back to a hash when URL is missing.
            external_id = url or stable_external_id(
                self._source_key,
                item.get("headline", ""),
                item.get("published_at", ""),
            )

            payload = {
                "record_type": _RECORD_TYPE,
                "source_key": self._source_key,
                "external_id": external_id,
                "headline": item.get("headline"),
                "url": url,
                "extracted_text": item.get("text"),
                "published_at": item.get("published_at"),
                "content_hash": item.get("content_hash"),
                "snapshot_hash": item.get("snapshot_hash"),
                "http_status": item.get("http_status"),
                "content_type": item.get("content_type"),
                "source_quality": "government_news_with_full_text",
                "privacy_status": "needs_review",
                "publish_recommendation": "review_required",
                "public_visibility": False,
                "candidate_type": "government_news_context",
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
        """Execute a full fetch → parse cycle with depth-2 article fetching.

        Depth-2 flow:
        1. Fetch listing page (depth 1)
        2. Extract article URLs
        3. Fetch each article individually (depth 2)
        4. Extract and hash article content
        5. Parse to ReviewItem records

        Returns:
            IngestionResult with evidence snapshot fields set per contract.
        """
        result = IngestionResult(
            source_key=self._source_key,
            parser_version=PARSER_VERSION,
        )
        try:
            # Depth 1: Fetch listing page and extract URLs
            raw = self.fetch()
            result.records_fetched = len(raw)

            # Propagate evidence snapshot fields per contract.
            result.raw_snapshot_bytes = self._raw_bytes
            result.fetch_http_status = self._fetch_http_status
            result.fetch_content_type = self._fetch_content_type
            result.fetch_url = self._fetch_url

            # Depth 2: Fetch each article and extract full content
            for item in raw:
                self.fetch_article_depth(item)

            parsed = self.parse(raw)
            result.records_skipped = len(raw) - len(parsed)

            for p in parsed:
                result.review_items.append(
                    CreatedReviewItem(
                        source_key=p.source_key,
                        headline=p.payload.get("headline"),
                        url=p.source_url,
                        extracted_text=p.payload.get("extracted_text"),
                        confidence_score=0.35,  # Slightly higher for full article content
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
            name=f"SK Gov News — {self._source_key}",
            source_type="government_news",
            base_url=self._base_url,
            allowed_domains=allowed_domains,
            start_urls=[self._base_url],
            max_requests=25,
            max_depth=1,
        )
        runner = CrawleeRunner(target=target, db=db)
        review_items = await runner.run()
        return review_items
