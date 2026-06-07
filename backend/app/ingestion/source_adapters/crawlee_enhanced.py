"""Enhanced crawler utilities for deeper article extraction.

Provides helper functions for multi-level crawling:
1. Fetch listing page
2. Extract article URLs
3. Fetch each article
4. Extract and hash content

This module supports both police and government news crawlers.
"""

from __future__ import annotations

import hashlib
import html
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ArticleSnapshot:
    """Represents a fetched article with evidence preservation."""

    url: str
    title: str
    published_at: str | None
    body_text: str
    content_hash: str
    snapshot_hash: str
    http_status: int
    content_type: str
    is_valid: bool


def extract_title_from_html(html_content: str) -> str:
    """Extract article title from HTML.
    
    Tries in order:
    1. <h1> tag
    2. <title> tag content
    3. og:title meta tag
    4. Empty string if not found
    """
    # Try <h1>
    match = re.search(r"<h1[^>]*>([^<]+)</h1>", html_content, re.IGNORECASE)
    if match:
        return html.unescape(match.group(1).strip())
    
    # Try <title>
    match = re.search(r"<title>([^<]+)</title>", html_content, re.IGNORECASE)
    if match:
        return html.unescape(match.group(1).strip())
    
    # Try og:title
    match = re.search(
        r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"',
        html_content,
        re.IGNORECASE
    )
    if match:
        return html.unescape(match.group(1).strip())
    
    return ""


def extract_date_from_html(html_content: str) -> str | None:
    """Extract publication date from HTML.
    
    Tries in order:
    1. article:published_time meta tag
    2. og:publish_date meta tag
    3. data-publish-date attribute
    4. None if not found
    """
    # Try article:published_time
    match = re.search(
        r'<meta[^>]*property="article:published_time"[^>]*content="([^"]*)"',
        html_content,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    
    # Try og:publish_date
    match = re.search(
        r'<meta[^>]*property="og:publish_date"[^>]*content="([^"]*)"',
        html_content,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    
    # Try data-publish-date
    match = re.search(
        r'data-publish-date="([^"]*)"',
        html_content,
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    
    return None


def extract_body_text(html_content: str, max_length: int = 8000) -> str:
    """Extract main body text from HTML.
    
    Removes scripts, styles, and HTML tags. Normalizes whitespace.
    Truncates to max_length.
    """
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Unescape HTML entities
    html_content = html.unescape(html_content)
    
    # Normalize whitespace
    html_content = re.sub(r'\s+', ' ', html_content).strip()
    
    # Truncate to max length
    return html_content[:max_length]


def compute_hashes(content: str, raw_bytes: bytes) -> tuple[str, str]:
    """Compute SHA256 hashes for content and snapshot.
    
    Returns:
        (content_hash, snapshot_hash)
    """
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    snapshot_hash = hashlib.sha256(raw_bytes).hexdigest()
    return content_hash, snapshot_hash


async def fetch_article(
    url: str,
    fetcher: Any,
    allowed_domains: list[str],
    title_fallback: str = "",
) -> ArticleSnapshot | None:
    """Fetch an individual article and extract content.
    
    Args:
        url: Article URL to fetch
        fetcher: Async fetcher function
        allowed_domains: Allowed domains for URL validation
        title_fallback: Fallback title if extraction fails
    
    Returns:
        ArticleSnapshot if successful, None if fetch fails or content too short
    """
    result = fetcher(
        url,
        allowed_domains,
        timeout_seconds=30,
        max_bytes=512_000,
    )
    
    if result.error or not result.raw_content:
        logger.warning("Failed to fetch article %s: %s", url, result.error)
        return None
    
    try:
        html_content = result.raw_content.decode("utf-8", errors="replace")
        
        # Extract metadata
        title = extract_title_from_html(html_content) or title_fallback or url
        published_at = extract_date_from_html(html_content)
        body_text = extract_body_text(html_content)
        
        # Reject if body is too short (likely not a real article)
        if len(body_text) < 100:
            logger.debug("Article %s too short (%d chars), rejecting", url, len(body_text))
            return None
        
        # Compute hashes
        content_hash, snapshot_hash = compute_hashes(body_text, result.raw_content)
        
        return ArticleSnapshot(
            url=result.final_url or url,
            title=title,
            published_at=published_at,
            body_text=body_text,
            content_hash=content_hash,
            snapshot_hash=snapshot_hash,
            http_status=result.http_status or 200,
            content_type=result.content_type or "text/html",
            is_valid=True,
        )
    
    except Exception as exc:
        logger.exception("Error processing article %s: %s", url, exc)
        return None


class EnhancedCrawlerMixin:
    """Mixin for crawlers that perform depth-2 article extraction.
    
    Expects subclass to have:
    - self._fetcher
    - self._allowed_domains
    - self._source_key
    """

    async def fetch_article_with_depth(
        self,
        url: str,
        title_fallback: str = "",
    ) -> ArticleSnapshot | None:
        """Fetch article using the mixin's fetcher."""
        return await fetch_article(
            url=url,
            fetcher=self._fetcher,
            allowed_domains=self._allowed_domains,
            title_fallback=title_fallback,
        )

    def build_item_from_snapshot(self, snapshot: ArticleSnapshot) -> dict[str, Any]:
        """Convert ArticleSnapshot to standardized item dict."""
        return {
            "url": snapshot.url,
            "headline": snapshot.title,
            "published_at": snapshot.published_at,
            "text": snapshot.body_text,
            "content_hash": snapshot.content_hash,
            "snapshot_hash": snapshot.snapshot_hash,
            "http_status": snapshot.http_status,
            "content_type": snapshot.content_type,
        }
