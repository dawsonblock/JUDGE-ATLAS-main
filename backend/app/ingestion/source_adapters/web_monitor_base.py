"""Shared base module for web monitor adapters.

Provides common utilities for crawling web pages and extracting structured data
without duplicating logic across multiple adapters.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class WebMonitorFetchState:
    """Tracks fetch state for evidence contract compliance."""

    raw_snapshot_bytes: bytes | None = None
    fetch_http_status: int | None = None
    fetch_content_type: str | None = None
    fetch_url: str | None = None


def normalize_url(base_url: str, href: str) -> str:
    """Normalize a relative URL against a base URL."""
    return urljoin(base_url.rstrip("/") + "/", href)


def clean_text(html: str, *, limit: int = 4000) -> str:
    """Extract clean text from HTML, removing scripts and styles.

    Args:
        html: Raw HTML string
        limit: Maximum character length for result

    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def extract_title(html: str) -> str | None:
    """Extract title from HTML.

    Tries <title> first, then first <h1>, returns None if neither found.
    """
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(" ", strip=True)
    return None


def is_allowed_url(url: str, allowed_domains: list[str]) -> bool:
    """Check if URL's hostname is in allowed domains list.

    Args:
        url: URL to check
        allowed_domains: List of allowed domain strings

    Returns:
        True if URL's host matches or is subdomain of allowed domain
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    return any(host == d or host.endswith(f".{d}") for d in allowed_domains)


def extract_links(
    *,
    html: str,
    base_url: str,
    allowed_domains: list[str],
    include_patterns: list[str],
    exclude_patterns: list[str] | None = None,
    max_links: int = 25,
) -> list[dict[str, Any]]:
    """Extract links from HTML matching include patterns.

    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links
        allowed_domains: Domains allowed for extracted links
        include_patterns: Substrings that must appear in URL or link text
        exclude_patterns: Substrings that disqualify a link
        max_links: Maximum number of links to return

    Returns:
        List of dicts with 'url' and 'headline' keys
    """
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    exclude_patterns = exclude_patterns or []

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        url = normalize_url(base_url, href)

        if url in seen:
            continue
        if not is_allowed_url(url, allowed_domains):
            continue

        lowered = url.lower()
        text = a.get_text(" ", strip=True)

        # Must match at least one include pattern
        if not any(
            p.lower() in lowered or p.lower() in text.lower() for p in include_patterns
        ):
            continue

        # Must not match any exclude pattern
        if any(
            p.lower() in lowered or p.lower() in text.lower() for p in exclude_patterns
        ):
            continue

        seen.add(url)
        items.append(
            {
                "url": url,
                "headline": text or url,
            }
        )
        if len(items) >= max_links:
            break

    return items


def stable_external_id(source_key: str, *parts: str) -> str:
    """Generate a stable external_id from source key and content parts.

    Used as a fallback when a source does not provide a natural unique
    identifier (e.g. missing URL).  The returned id is a truncated
    SHA-256 hex digest so it is deterministic and collision-resistant.
    """
    payload = "|".join([source_key, *parts])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
