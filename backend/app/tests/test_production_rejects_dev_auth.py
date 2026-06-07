"""Tests that production runtime profile rejects dev/placeholder auth settings."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.settings_validation import (
    InsecureProductionConfigError,
    validate_production_safety,
)


def _prod_safe_base() -> dict:
    """Minimal safe production settings overrides."""
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


class TestProductionRejectsDevAuth:
    def test_placeholder_jwt_secret_is_rejected(self):
        overrides = _prod_safe_base()
        overrides["jwt_secret_key"] = "CHANGE-ME-BEFORE-PRODUCTION"
        s = Settings(**overrides)
        with pytest.raises(InsecureProductionConfigError) as exc_info:
            validate_production_safety(s)
        assert any("jwt_secret_key" in v for v in exc_info.value.violations)

    def test_empty_jwt_secret_is_rejected(self):
        overrides = _prod_safe_base()
        overrides["jwt_secret_key"] = ""
        s = Settings(**overrides)
        with pytest.raises(InsecureProductionConfigError) as exc_info:
            validate_production_safety(s)
        assert any("jwt_secret_key" in v for v in exc_info.value.violations)

    def test_jwt_auth_disabled_is_rejected(self):
        overrides = _prod_safe_base()
        overrides["jwt_auth_enabled"] = False
        s = Settings(**overrides)
        with pytest.raises(InsecureProductionConfigError) as exc_info:
            validate_production_safety(s)
        assert any("jwt_auth_enabled" in v for v in exc_info.value.violations)

    def test_legacy_admin_token_enabled_is_rejected(self):
        overrides = _prod_safe_base()
        overrides["enable_legacy_admin_token"] = True
        s = Settings(**overrides)
        with pytest.raises(InsecureProductionConfigError) as exc_info:
            validate_production_safety(s)
        assert any("enable_legacy_admin_token" in v for v in exc_info.value.violations)

    def test_safe_production_config_passes(self):
        """A fully hardened production config must pass without error."""
        s = Settings(**_prod_safe_base())
        validate_production_safety(s)  # Must not raise

    def test_development_profile_is_not_checked(self):
        """Validation must be a no-op for development profile."""
        s = Settings(
            runtime_profile="development",
            jwt_auth_enabled=False,
            jwt_secret_key="CHANGE-ME-BEFORE-PRODUCTION",
        )
        validate_production_safety(s)  # Must not raise

    def test_test_profile_is_not_checked(self):
        """Validation must be a no-op for test profile."""
        s = Settings(
            runtime_profile="test",
            jwt_auth_enabled=False,
            jwt_secret_key="CHANGE-ME-BEFORE-PRODUCTION",
        )
        validate_production_safety(s)  # Must not raise

    def test_staging_profile_is_checked(self):
        """Staging must be treated as production for security purposes."""
        overrides = _prod_safe_base()
        overrides["runtime_profile"] = "staging"
        overrides["jwt_secret_key"] = "CHANGE-ME-BEFORE-PRODUCTION"
        s = Settings(**overrides)
        with pytest.raises(InsecureProductionConfigError):
            validate_production_safety(s)
