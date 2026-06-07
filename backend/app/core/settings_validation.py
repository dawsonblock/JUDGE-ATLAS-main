"""Central validator that rejects dangerous configuration in production environments.

Call ``validate_production_safety(settings)`` at application startup when
``runtime_profile`` is ``production`` or ``staging``.  Raises
``InsecureProductionConfigError`` with a list of all violations found.

This module must have NO side-effects on import — it only exports the
validator function and the exception class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings


class InsecureProductionConfigError(RuntimeError):
    """Raised when a production-unsafe configuration is detected at startup."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        bullet_list = "\n".join(f"  - {v}" for v in violations)
        super().__init__(
            f"Production startup blocked — {len(violations)} insecure setting(s) "
            f"detected:\n{bullet_list}"
        )


_PLACEHOLDER_SECRETS = frozenset(
    {
        "change-me-before-production",
        "change-me",
        "dev-only-change-me",
        "secret",
        "password",
        "changeme",
        "",
    }
)

_PRODUCTION_PROFILES = frozenset({"production", "staging"})


def validate_production_safety(settings: "Settings") -> None:
    """Raise InsecureProductionConfigError if settings are unsafe for production.

    This function is a no-op for non-production runtime_profiles.
    """
    if settings.runtime_profile not in _PRODUCTION_PROFILES:
        return

    violations: list[str] = []

    # JWT secret must not be a placeholder
    if settings.jwt_secret_key.lower() in _PLACEHOLDER_SECRETS:
        violations.append(
            "jwt_secret_key is a placeholder value; set JTA_JWT_SECRET_KEY "
            "to a cryptographically random secret before deploying"
        )

    # JWT auth must be enabled in production
    if not settings.jwt_auth_enabled:
        violations.append(
            "jwt_auth_enabled=false in production; set JTA_JWT_AUTH_ENABLED=true "
            "and ensure at least one admin user has been created"
        )

    # Legacy admin token must not be enabled in production
    if settings.enable_legacy_admin_token:
        violations.append(
            "enable_legacy_admin_token=true in production; shared-token auth "
            "must be disabled (JTA_ENABLE_LEGACY_ADMIN_TOKEN=false)"
        )

    # admin_token placeholder check
    if settings.admin_token is not None:
        if settings.admin_token.lower() in _PLACEHOLDER_SECRETS:
            violations.append(
                "admin_token is a placeholder value; remove or replace with a "
                "strong random token, or disable legacy admin token auth entirely"
            )

    # Rate limiting must be enabled
    if not settings.rate_limit_enabled:
        violations.append(
            "rate_limit_enabled=false in production; "
            "set JTA_RATE_LIMIT_ENABLED=true"
        )

    # Rate limit backend must be redis (not memory) in production
    if settings.rate_limit_backend != "redis":
        violations.append(
            f"rate_limit_backend={settings.rate_limit_backend!r} in production; "
            "must be 'redis' (JTA_RATE_LIMIT_BACKEND=redis)"
        )

    # Redis URL must be set when rate_limit_backend is redis
    if settings.rate_limit_backend == "redis" and not settings.redis_url:
        violations.append(
            "redis_url is not set but rate_limit_backend=redis; "
            "set JTA_REDIS_URL to the production Redis URL"
        )

    # Experimental routes must be off in production
    if settings.enable_experimental_live_map:
        violations.append(
            "enable_experimental_live_map=true in production; "
            "experimental routes must be disabled (JTA_ENABLE_EXPERIMENTAL_LIVE_MAP=false)"
        )

    if settings.enable_workflow_admin:
        violations.append(
            "enable_workflow_admin=true in production; "
            "experimental routes must be disabled (JTA_ENABLE_WORKFLOW_ADMIN=false)"
        )

    # In-process queue is alpha-only
    if settings.ingestion_queue_backend == "inprocess":
        violations.append(
            "ingestion_queue_backend='inprocess' in production; "
            "inprocess queue is alpha-only and not production-capable. "
            "Set JTA_INGESTION_QUEUE_BACKEND=postgres"
        )

    # enforce_jwt_mutations must be True
    if not settings.enforce_jwt_mutations:
        violations.append(
            "enforce_jwt_mutations=false in production; "
            "set JTA_ENFORCE_JWT_MUTATIONS=true to prevent shared-token mutations"
        )

    if violations:
        raise InsecureProductionConfigError(violations)
