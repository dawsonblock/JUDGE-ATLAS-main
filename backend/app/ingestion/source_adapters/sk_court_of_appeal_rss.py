"""Adapter for Saskatchewan Court of Appeal decisions via RSS feed.

Handles source key: ``sk_court_of_appeal``
Parser key: ``sk_ca_rss``
Creates: ``ReviewItem`` records only
Authority: ``official_court_record``

Validated structure (2026-06-06):
- RSS feed: https://sasklawcourts.ca/rss/ca.xml
- Returns recent Court of Appeal decisions
- Item structure: <title>, <link>, <description>, <pubDate>
- Title format: typically includes case name and neutral citation

Evidence contract: every run() call that fetches data must set
    result.raw_snapshot_bytes, result.fetch_http_status,
    result.fetch_content_type, and result.fetch_url.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.ingestion.adapters import (
    CanadianSourceAdapter,
    CreatedReviewItem,
    IngestionResult,
    ParsedRecord,
)
from app.ingestion.fetcher import FetchCallable, fetch_for_ingestion, parse_allowed_domains
from app.ingestion.source_rules import check_record_type_allowed
from app.ingestion.source_adapters.web_monitor_base import stable_external_id

logger = logging.getLogger(__name__)

_RECORD_TYPE = "ReviewItem"
PARSER_VERSION = "sk_ca_rss_v1"

# Saskatchewan Court of Appeal RSS feed
_SK_CA_RSS_URL = "https://sasklawcourts.ca/rss/ca.xml"

# Regex patterns for extracting case metadata
_CITATION_PATTERN = re.compile(r"(\d{4}\s+SKCA\s+\d+)", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _clean_title(raw_title: str) -> tuple[str, str | None]:
    """Parse SKCA RSS title into (case_name, neutral_citation).

    Title format varies but often includes neutral citation like "2024 SKCA 123".
    """
    # Look for neutral citation pattern
    citation_match = _CITATION_PATTERN.search(raw_title)
    neutral_citation = citation_match.group(1).strip() if citation_match else None

    # Case name is the title without citation
    case_name = _CITATION_PATTERN.sub("", raw_title).strip()
    # Clean up common artifacts
    case_name = re.sub(r"\s+-\s*$", "", case_name).strip()
    case_name = re.sub(r"^\s+-\s+", "", case_name).strip()

    return case_name, neutral_citation


def _parse_date(date_str: str | None) -> str | None:
    """Parse RSS date string into ISO format.

    Handles various formats including RFC 2822 (pubDate).
    """
    if not date_str:
        return None

    # Try ISO format first
    if _DATE_PATTERN.match(date_str):
        return date_str

    # Try parsing RFC 2822 format (e.g., "Mon, 15 Jan 2024 10:30:00 GMT")
    try:
        # Simple heuristic: extract YYYY-MM-DD from common patterns
        rfc_match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_str)
        if rfc_match:
            day, month_str, year = rfc_match.groups()
            month_map = {
                "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                "may": "05", "jun": "06", "jul": "07", "aug": "08",
                "sep": "09", "oct": "10", "nov": "11", "dec": "12",
            }
            month = month_map.get(month_str.lower()[:3])
            if month is None:
                return date_str
            return f"{year}-{month}-{day.zfill(2)}"
    except Exception:
        pass

    return date_str


class SKCourtOfAppealRSSAdapter(CanadianSourceAdapter):
    """Fetch Saskatchewan Court of Appeal decisions and produce ReviewItem candidates.

    The Saskatchewan Court of Appeal publishes decisions through sasklawcourts.ca.
    This adapter uses the site's RSS feed for recent decisions.

    All records require manual review before publication.

    Validated structure (2026-06-06):
    - RSS URL: ``https://sasklawcourts.ca/rss/ca.xml``
    - Fields: ``<title>``, ``<link>``, ``<description>``, ``<pubDate>``
    - Title needs normalization for neutral citation extraction
    """

    def __init__(
        self,
        source_key: str,
        base_url: str | None = None,
        allowed_domains_json: str | None = None,
        public_record_authority: str | None = None,
        fetcher: FetchCallable | None = None,
    ) -> None:
        self._source_key = source_key
        self._base_url = base_url or _SK_CA_RSS_URL
        self._allowed_domains_json = (
            allowed_domains_json or '["sasklawcourts.ca", "www.sasklawcourts.ca"]'
        )
        self._public_record_authority = public_record_authority
        self._fetcher = fetcher or fetch_for_ingestion
        self._allowed_domains = parse_allowed_domains(self._allowed_domains_json)
        # Evidence snapshot fields — populated during _fetch_rss().
        self._raw_bytes: bytes | None = None
        self._fetch_http_status: int | None = None
        self._fetch_content_type: str | None = None
        self._fetch_url: str | None = None

    def _fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch and parse the SKCA RSS feed for recent decisions."""
        import xml.etree.ElementTree as ET  # stdlib — safe

        url = self._base_url
        fetch_result = self._fetcher(url, self._allowed_domains)
        if fetch_result.error:
            logger.warning(
                "RSS URL blocked for %s: %s", self._source_key, fetch_result.error
            )
            return []
        # Preserve raw evidence bytes for snapshot contract.
        self._raw_bytes = fetch_result.raw_content
        self._fetch_http_status = fetch_result.http_status
        self._fetch_content_type = fetch_result.content_type or "application/rss+xml"
        self._fetch_url = fetch_result.final_url or url
        raw_text = (fetch_result.raw_content or b"").decode("utf-8", errors="replace")
        # Defensive: reject responses that are clearly not XML/RSS.
        stripped = raw_text.lstrip()
        if not (
            stripped.startswith("<?xml")
            or stripped.startswith("<rss")
            or stripped.startswith("<feed")
        ):
            logger.error(
                "Expected RSS XML from %s but got non-XML response "
                "(status=%s, content_type=%s, first_chars=%r)",
                url,
                fetch_result.http_status,
                fetch_result.content_type,
                stripped[:200],
            )
            return []
        root = ET.fromstring(raw_text)
        items: list[dict[str, Any]] = []
        for item in root.iter("item"):
            entry: dict[str, Any] = {}
            for child in item:
                tag = child.tag.split("}")[-1]  # strip namespace
                entry[tag] = child.text
            items.append(entry)
        return items

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch raw records from the SKCA RSS feed."""
        return self._fetch_rss()

    def parse(self, raw: list[dict[str, Any]]) -> list[ParsedRecord]:
        """Transform raw RSS items into ParsedRecord objects."""
        records: list[ParsedRecord] = []
        # Record type gate — constant per adapter run, checked once.
        record_type_violation = check_record_type_allowed(
            _RECORD_TYPE,
            self._public_record_authority,
            f'["{_RECORD_TYPE}"]',
        )
        if record_type_violation:
            logger.warning(
                "Record type gate failed: %s", record_type_violation.detail
            )
            return records

        for item in raw:
            url = item.get("link") or ""
            raw_title = item.get("title") or ""
            description = item.get("description") or ""

            # Normalize the title and extract neutral citation.
            case_name, neutral_citation = _clean_title(raw_title)

            # Parse publication date.
            pub_date = _parse_date(item.get("pubDate") or item.get("date"))

            # Stable external_id — falls back to a hash when URL is missing.
            external_id = url or stable_external_id(
                self._source_key,
                case_name or raw_title,
                pub_date or "",
            )

            records.append(
                ParsedRecord(
                    source_name=self._source_key,
                    source_key=self._source_key,
                    record_type=_RECORD_TYPE,
                    external_id=external_id,
                    payload={
                        "headline": case_name or raw_title.strip(),
                        "url": url,
                        "neutral_citation": neutral_citation,
                        "published_at": pub_date,
                        "description": description,
                        "court": "Court of Appeal for Saskatchewan",
                    },
                    source_url=url,
                )
            )
        return records

    def run(self) -> IngestionResult:
        """Execute a full fetch → parse cycle and return an IngestionResult."""
        result = IngestionResult(
            source_key=self._source_key,
            parser_version=PARSER_VERSION,
        )
        try:
            raw = self.fetch()
            result.records_fetched = len(raw)
            # Propagate evidence snapshot fields.
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
                        extracted_text=p.payload.get("description"),
                        confidence_score=0.8 if p.payload.get("neutral_citation") else 0.6,
                        payload=p.payload,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled error in %s adapter", self._source_key)
            result.errors.append(str(exc))
        return result
