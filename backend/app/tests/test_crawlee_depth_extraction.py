"""Tests for enhanced crawler depth-2 extraction."""

import pytest

from app.ingestion.source_adapters.crawlee_enhanced import (
    extract_title_from_html,
    extract_date_from_html,
    extract_body_text,
    compute_hashes,
)


class TestTitleExtraction:
    """Test article title extraction from HTML."""

    def test_extracts_h1_title(self):
        """Should prefer <h1> tag for title."""
        html = "<h1>Police Release New Guidelines</h1>"
        assert extract_title_from_html(html) == "Police Release New Guidelines"

    def test_extracts_title_tag(self):
        """Should fallback to <title> tag."""
        html = "<title>News - Saskatchewan Justice</title>"
        assert extract_title_from_html(html) == "News - Saskatchewan Justice"

    def test_extracts_og_title(self):
        """Should extract og:title meta tag."""
        html = '<meta property="og:title" content="Court Decision Alert">'
        assert extract_title_from_html(html) == "Court Decision Alert"

    def test_returns_empty_string_when_no_title(self):
        """Should return empty string when no title found."""
        html = "<p>Some content</p>"
        assert extract_title_from_html(html) == ""


class TestDateExtraction:
    """Test publication date extraction from HTML."""

    def test_extracts_article_published_time(self):
        """Should extract article:published_time meta tag."""
        html = '<meta property="article:published_time" content="2026-01-15T10:30:00Z">'
        assert extract_date_from_html(html) == "2026-01-15T10:30:00Z"

    def test_extracts_publish_date_meta(self):
        """Should extract og:publish_date meta tag."""
        html = '<meta property="og:publish_date" content="2026-01-15">'
        assert extract_date_from_html(html) == "2026-01-15"

    def test_extracts_data_publish_date(self):
        """Should extract data-publish-date attribute."""
        html = '<div data-publish-date="2026-01-15">Article</div>'
        assert extract_date_from_html(html) == "2026-01-15"

    def test_returns_none_when_no_date(self):
        """Should return None when no date found."""
        html = "<p>Some content</p>"
        assert extract_date_from_html(html) is None


class TestBodyTextExtraction:
    """Test article body text extraction from HTML."""

    def test_removes_script_tags(self):
        """Should remove JavaScript content."""
        html = "<p>Real content</p><script>var x = 1;</script>"
        text = extract_body_text(html)
        assert "Real content" in text
        assert "var x" not in text

    def test_removes_style_tags(self):
        """Should remove CSS content."""
        html = "<p>Real content</p><style>.class { color: red; }</style>"
        text = extract_body_text(html)
        assert "Real content" in text
        assert ".class" not in text

    def test_removes_html_tags(self):
        """Should remove HTML markup."""
        html = "<div><p>Real <strong>content</strong></p></div>"
        text = extract_body_text(html)
        assert "Real" in text
        assert "content" in text
        assert "<" not in text

    def test_normalizes_whitespace(self):
        """Should normalize multiple spaces."""
        html = "<p>Text    with    extra    spaces</p>"
        text = extract_body_text(html)
        assert "Text with extra spaces" in text

    def test_truncates_to_max_length(self):
        """Should truncate text to max_length."""
        html = "<p>" + "x" * 10000 + "</p>"
        text = extract_body_text(html, max_length=100)
        assert len(text) <= 100

    def test_rejects_very_short_content(self):
        """Should be suitable for rejection of short content."""
        html = "<p>Hi</p>"
        text = extract_body_text(html)
        assert len(text) < 100


class TestHashComputation:
    """Test SHA256 hash computation."""

    def test_computes_content_hash(self):
        """Should compute SHA256 of text content."""
        content = "Example article text"
        raw_bytes = b"<html>Example article text</html>"
        content_hash, snapshot_hash = compute_hashes(content, raw_bytes)
        
        # Check that hashes are 64 characters (SHA256 in hex)
        assert len(content_hash) == 64
        assert len(snapshot_hash) == 64

    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        raw1 = b"Content A"
        raw2 = b"Content B"
        
        _, hash1 = compute_hashes("Content A", raw1)
        _, hash2 = compute_hashes("Content B", raw2)
        
        assert hash1 != hash2

    def test_same_content_same_hash(self):
        """Same content should produce same hash."""
        raw = b"Content"
        _, hash1 = compute_hashes("Content", raw)
        _, hash2 = compute_hashes("Content", raw)
        
        assert hash1 == hash2


class TestCrawlerDepth:
    """Test crawler depth-2 article extraction."""

    def test_fetch_article_depth_enhances_item(self):
        """fetch_article_depth should enhance item with full content."""
        from app.ingestion.source_adapters.crawlee_police_release import (
            CrawleePoliceReleaseAdapter,
        )

        # Mock fetcher
        class MockResult:
            error = None
            raw_content = b"""
            <html>
            <head><title>Police Press Release</title></head>
            <body>
            <h1>Department Announces New Safety Initiative</h1>
            <p>This is a comprehensive article about public safety...</p>
            </body>
            </html>
            """
            http_status = 200
            content_type = "text/html"
            final_url = "https://example.com/article"

        def mock_fetcher(url, allowed_domains, timeout_seconds=30, max_bytes=512000):
            return MockResult()

        adapter = CrawleePoliceReleaseAdapter(
            source_key="test_police",
            base_url="https://example.com",
            fetcher=mock_fetcher,
        )

        item = {"url": "https://example.com/article", "headline": "News"}
        result = adapter.fetch_article_depth(item)

        # Should have enhanced fields
        assert result["fetch_status"] == "success"
        assert result["content_hash"]  # Should be non-empty
        assert result["snapshot_hash"]  # Should be non-empty
        assert "Safety Initiative" in result["headline"]  # Title extracted

    def test_rejects_articles_too_short(self):
        """fetch_article_depth should reject articles with too little text."""
        from app.ingestion.source_adapters.crawlee_police_release import (
            CrawleePoliceReleaseAdapter,
        )

        class MockResult:
            error = None
            raw_content = b"<html><body><h1>Title</h1></body></html>"
            http_status = 200
            content_type = "text/html"
            final_url = "https://example.com/article"

        def mock_fetcher(url, allowed_domains, timeout_seconds=30, max_bytes=512000):
            return MockResult()

        adapter = CrawleePoliceReleaseAdapter(
            source_key="test_police",
            base_url="https://example.com",
            fetcher=mock_fetcher,
        )

        item = {"url": "https://example.com/article", "headline": "News"}
        result = adapter.fetch_article_depth(item)

        # Should reject as too short
        assert result["fetch_status"] == "too_short"
