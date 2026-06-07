"""Tests that all known placeholder secret values are rejected in production."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.settings_validation import (
    InsecureProductionConfigError,
    validate_production_safety,
)

PLACEHOLDER_SECRETS = [
    "CHANGE-ME-BEFORE-PRODUCTION",
    "change-me",
    "dev-only-change-me",
    "secret",
    "password",
    "changeme",
    "",
]


def _prod_safe_base() -> dict:
    return {
        "runtime_profile": "production",
        "jwt_auth_enabled": True,
        "jwt_secret_key": "a-very-long-random-cryptographic-secret-key-32chars",
        "enable_legacy_admin_token": False,
        "rate_limit_enabled": True,
        "rate_limit_backend": "redis",
        "redis_url": "redis://prod-redis:6379/0",
        "enable_experimental_live_map": False,
        "enable_workflow_admin": False,
        "ingestion_queue_backend": "postgres",
        "enforce_jwt_mutations": True,
    }


@pytest.mark.parametrize("secret", PLACEHOLDER_SECRETS)
def test_placeholder_jwt_secret_rejected(secret):
    overrides = _prod_safe_base()
    overrides["jwt_secret_key"] = secret
    s = Settings(**overrides)
    with pytest.raises(InsecureProductionConfigError) as exc_info:
        validate_production_safety(s)
    assert any("jwt_secret_key" in v for v in exc_info.value.violations), (
        f"Expected jwt_secret_key violation for placeholder {secret!r}, "
        f"got violations: {exc_info.value.violations}"
    )


def test_all_violations_reported_together():
    """All violations must be reported in a single raise, not one at a time."""
    overrides = _prod_safe_base()
    overrides["jwt_secret_key"] = "CHANGE-ME-BEFORE-PRODUCTION"
    overrides["jwt_auth_enabled"] = False
    overrides["enable_legacy_admin_token"] = True
    overrides["rate_limit_enabled"] = False
    s = Settings(**overrides)
    with pytest.raises(InsecureProductionConfigError) as exc_info:
        validate_production_safety(s)
    assert len(exc_info.value.violations) >= 3, (
        f"Expected at least 3 violations, got {len(exc_info.value.violations)}: "
        f"{exc_info.value.violations}"
    )


def test_violation_message_lists_all_violations():
    """The exception message must include all violation descriptions."""
    overrides = _prod_safe_base()
    overrides["jwt_secret_key"] = "CHANGE-ME-BEFORE-PRODUCTION"
    overrides["jwt_auth_enabled"] = False
    s = Settings(**overrides)
    with pytest.raises(InsecureProductionConfigError) as exc_info:
        validate_production_safety(s)
    msg = str(exc_info.value)
    for violation in exc_info.value.violations:
        assert violation in msg, (
            f"Violation {violation!r} not found in exception message"
        )
