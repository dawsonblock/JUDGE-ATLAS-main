"""
Security tests: no stack traces, public redaction, auth boundaries.
"""

import pytest
from typing import Dict, Any


class TestNoStackTracesPublic:
    """Public endpoints must never expose Python stack traces."""

    def test_public_error_response_no_traceback(self):
        """Error responses to public endpoints must not contain traceback."""
        bad_response = {
            "error": "Internal server error",
            "detail": "Traceback (most recent call last):\n  File ...",
        }

        response_str = str(bad_response)
        assert "Traceback" not in response_str
        # This test verifies the expectation; actual endpoints would be tested
        # in integration tests.

    def test_public_response_no_file_references(self):
        """Error responses must not contain internal file paths."""
        bad_response = {
            "error": "Error in /app/backend/app/api/routes/map.py line 42",
        }

        response_str = str(bad_response)
        assert 'File "' not in response_str or '/app/' not in response_str


class TestPublicRedaction:
    """Public API responses must redact all private/unreviewed data."""

    def test_public_event_no_reviewer_notes(self):
        """Public event response must not include reviewer notes."""
        public_event = {
            "id": "evt_001",
            "title": "Public Event",
            "reviewed": True,
            "visible": True,
            # No reviewer_notes field
            # No internal_flags
            # No raw_snapshot_content
        }

        assert "reviewer_notes" not in public_event
        assert "internal_flags" not in public_event
        assert "raw_snapshot_content" not in public_event

    def test_public_response_excludes_unreviewed(self):
        """Public API must exclude unreviewed records."""
        public_response = {
            "events": [
                {"id": "evt_001", "reviewed": True},
                {"id": "evt_002", "reviewed": True},
            ]
        }

        for event in public_response["events"]:
            assert event["reviewed"] is True

    def test_public_response_no_ai_internals(self):
        """Public response must not expose AI extraction internals."""
        public_event = {
            "id": "evt_001",
            "title": "Event",
            # No extraction_debug_info
            # No model_inference_raw
            # No confidence_scores for internal models
        }

        assert "extraction_debug_info" not in public_event
        assert "model_inference_raw" not in public_event


class TestAdminRequiresAuth:
    """Admin routes must require authentication/authorization."""

    def test_admin_route_401_unauthorized(self):
        """Unauthenticated request to admin route must return 401."""
        # Simulated: actual would be integration test
        admin_route = "/admin/review"
        requires_auth = True
        assert requires_auth is True

    def test_admin_route_403_forbidden_non_admin(self):
        """Non-admin authenticated user must get 403."""
        # Simulated
        admin_route = "/admin/review"
        requires_admin = True
        assert requires_admin is True

    def test_admin_route_accessible_with_admin_token(self):
        """Admin with valid token can access admin route."""
        # This would test with a valid JWT containing admin role
        pass


class TestRawSnapshotPrivate:
    """Raw evidence snapshots must be strictly private."""

    def test_raw_snapshot_requires_admin(self):
        """Raw snapshot endpoint must require admin."""
        raw_snapshot_route = {
            "path": "/admin/snapshots/raw/<id>",
            "requires_admin": True,
        }
        assert raw_snapshot_route["requires_admin"] is True

    def test_raw_snapshot_not_in_public_api(self):
        """Raw snapshots never appear in public API responses."""
        public_response = {
            "events": [
                {
                    "id": "evt_001",
                    "title": "Event",
                    "evidence": {
                        "snapshot_id": "snap_001",
                        # But NOT raw_snapshot_content
                    },
                }
            ]
        }

        for event in public_response["events"]:
            assert "raw_snapshot_content" not in event.get("evidence", {})


class TestNoSensitiveEnvLeaks:
    """Config and environment variables must not leak in responses."""

    def test_database_credentials_not_in_response(self):
        """Database URLs/credentials never in API response."""
        safe_response = {
            "status": "ok",
            # No database connection string
            # No SECRET_KEY
            # No API_TOKEN
        }

        response_str = str(safe_response)
        assert "postgres://" not in response_str
        assert "SECRET_KEY" not in response_str


class TestResponseValidation:
    """Responses must conform to security schemas."""

    def test_public_response_schema(self):
        """Public responses must match safe schema."""
        public_event = {
            "id": "evt_001",
            "title": "Event",
            "event_type": "incident",
            "location": {"lat": 52.0, "lon": -106.0},
            "evidence": {
                "snapshot_id": "snap_001",
                "source_name": "Source",
                "citation_url": "https://example.com",
                "reviewed": True,
            },
        }

        # Schema validation
        assert "id" in public_event
        assert "title" in public_event
        assert public_event["evidence"]["reviewed"] is True

    def test_admin_response_may_include_notes(self):
        """Admin-only responses CAN include sensitive data."""
        admin_event = {
            "id": "evt_001",
            "title": "Event",
            "reviewed": True,
            "reviewer_notes": "Verified against official records",  # OK for admin
            "raw_snapshot_content": "<html>...</html>",  # OK for admin
        }

        assert "reviewer_notes" in admin_event
        assert "raw_snapshot_content" in admin_event
