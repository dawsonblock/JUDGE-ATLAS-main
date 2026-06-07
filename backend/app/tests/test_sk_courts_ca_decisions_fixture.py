"""Fixture tests for sk_courts_ca_decisions using CanLII API payloads.

The SourceRegistry maps this source to parser ``canlii_api``. These tests keep
its local replay fixture aligned with the active adapter contract.
"""

import pytest
from app.ingestion.source_adapters.canlii_api import CanLIIApiAdapter


@pytest.fixture
def sk_courts_ca_decisions_adapter():
    """Create a CanLIIApiAdapter instance for testing."""
    return CanLIIApiAdapter(
        source_key="sk_courts_ca_decisions",
        base_url="https://api.canlii.org/v1",
        api_key="fake-api-key",
        databases=["skca"],
        result_count=10,
        allowed_domains_json=(
            '["api.canlii.org", "canlii.org", "www.canlii.org"]'
        ),
        public_record_authority="official_court_record",
    )


@pytest.fixture
def sk_courts_ca_decisions_mock_cases():
    """Mock CanLII case list payload for Saskatchewan Court of Appeal."""
    return [
        {
            "title": "R v Example CA 1",
            "url": (
                "https://www.canlii.org/en/sk/skca/"
                "doc/2026/2026skca1/2026skca1.html"
            ),
            "decisionDate": "2026-02-01",
            "citation": "2026 SKCA 1",
            "caseId": {"en": "2026skca1"},
            "_db_id": "skca",
        },
        {
            "title": "R v Example CA 2",
            "url": (
                "https://www.canlii.org/en/sk/skca/"
                "doc/2026/2026skca2/2026skca2.html"
            ),
            "decisionDate": "2026-02-02",
            "citation": "2026 SKCA 2",
            "caseId": {"en": "2026skca2"},
            "_db_id": "skca",
        },
    ]


@pytest.fixture
def sk_courts_ca_decisions_expected_records():
    """Expected parsed payload snippets from CanLII case input."""
    return [
        {
            "url": (
                "https://www.canlii.org/en/sk/skca/"
                "doc/2026/2026skca1/2026skca1.html"
            ),
            "headline": "R v Example CA 1",
        },
        {
            "url": (
                "https://www.canlii.org/en/sk/skca/"
                "doc/2026/2026skca2/2026skca2.html"
            ),
            "headline": "R v Example CA 2",
        },
    ]


def test_sk_courts_ca_decisions_adapter_config(sk_courts_ca_decisions_adapter):
    """Test that the adapter is properly configured."""
    assert (
        sk_courts_ca_decisions_adapter._source_key
        == "sk_courts_ca_decisions"
    )
    assert (
        sk_courts_ca_decisions_adapter._base_url
        == "https://api.canlii.org/v1"
    )
    assert sk_courts_ca_decisions_adapter._databases == ["skca"]
    assert (
        sk_courts_ca_decisions_adapter._public_record_authority
        == "official_court_record"
    )


def test_sk_courts_ca_decisions_adapter_parse_cases(
    sk_courts_ca_decisions_adapter,
    sk_courts_ca_decisions_mock_cases,
    sk_courts_ca_decisions_expected_records,
):
    """Test that the adapter correctly parses CanLII case payloads."""
    parsed_records = sk_courts_ca_decisions_adapter.parse(
        sk_courts_ca_decisions_mock_cases
    )

    assert len(parsed_records) == 2
    assert (
        parsed_records[0].payload["headline"]
        == sk_courts_ca_decisions_expected_records[0]["headline"]
    )
    assert (
        parsed_records[0].source_url
        == sk_courts_ca_decisions_expected_records[0]["url"]
    )
    assert (
        parsed_records[1].payload["headline"]
        == sk_courts_ca_decisions_expected_records[1]["headline"]
    )
    assert (
        parsed_records[1].source_url
        == sk_courts_ca_decisions_expected_records[1]["url"]
    )


def test_sk_courts_ca_decisions_adapter_parse_empty_cases(
    sk_courts_ca_decisions_adapter,
):
    """Test that empty case payload parses to an empty result list."""
    parsed_records = sk_courts_ca_decisions_adapter.parse([])
    assert parsed_records == []
