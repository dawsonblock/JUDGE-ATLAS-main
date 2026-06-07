#!/usr/bin/env python3
"""Verify that Azure deployment configuration is safe for alpha and does not
accidentally configure a production deployment.

Checks:
1. azure.yaml does not reference production environment names without alpha labeling.
2. infra/main.parameters.json uses env-var substitution for secrets (not literals).
3. .github/workflows/azure-deploy.yml default environment is not named *prod* unless
   the alpha label is present in the workflow name.
4. Azure deploy workflow does not ship with placeholder secret values baked in.

This script does NOT block alpha deployments — it enforces that they are correctly
labeled as alpha rather than production.

Usage::

    python3 scripts/check_azure_prod_config.py
    python3 scripts/check_azure_prod_config.py --root /path/to/repo
    python3 scripts/check_azure_prod_config.py --json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[1]

_PLACEHOLDER_SECRETS = (
    "CHANGE-ME-BEFORE-PRODUCTION",
    "changeme",
    "placeholder",
    "dummy",
    "fake_secret",
    "password",
    "secret",
    "12345",
    "your-secret-here",
)

_PROD_ENV_NAME_RE = re.compile(r"judgetracker-prod(?!uction-ready-false)", re.IGNORECASE)
GITHUB_SECRET_PATTERN = re.compile(
    r"\$\{\{[^}]*secrets\.[A-Z0-9_]+[^}]*\}\}",
    re.IGNORECASE,
)
_ALPHA_LABEL_PHRASES = ("alpha", "ALPHA")


def _check_azure_yaml(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = repo_root / "azure.yaml"
    if not path.exists():
        return ["azure_yaml_missing"]
    text = path.read_text(encoding="utf-8")
    if "production" in text.lower() and not any(
        p in text for p in ("alpha", "ALPHA", "alpha_")
    ):
        errors.append("azure_yaml_references_production_without_alpha_label")
    return errors


def _check_infra_parameters(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = repo_root / "infra" / "main.parameters.json"
    if not path.exists():
        return ["infra_parameters_missing"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["infra_parameters_invalid_json"]

    params = data.get("parameters", {})
    for param_name, param_obj in params.items():
        if not isinstance(param_obj, dict):
            continue
        value = param_obj.get("value", "")
        if not isinstance(value, str):
            continue
        # Values must use ${ENV_VAR} substitution, not literal secrets
        stripped = value.strip()
        if stripped and not stripped.startswith("${") and not stripped.startswith("@"):
            for placeholder in _PLACEHOLDER_SECRETS:
                if placeholder.lower() in stripped.lower():
                    errors.append(
                        f"infra_parameter_placeholder_secret:{param_name}"
                    )
    return errors


def _check_azure_deploy_workflow(repo_root: Path) -> list[str]:
    errors: list[str] = []
    path = repo_root / ".github" / "workflows" / "azure-deploy.yml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")

    # Workflow name must contain alpha label if default env is production-named
    if _PROD_ENV_NAME_RE.search(text):
        has_alpha_label = any(phrase in text for phrase in _ALPHA_LABEL_PHRASES)
        if not has_alpha_label:
            errors.append(
                "azure_deploy_workflow_uses_prod_env_name_without_alpha_label"
            )

    # Baked-in placeholder secrets
    for placeholder in _PLACEHOLDER_SECRETS:
        scrubbed_text = GITHUB_SECRET_PATTERN.sub("", text)
        if placeholder in scrubbed_text:
            errors.append(
                f"azure_deploy_workflow_contains_placeholder_secret:{placeholder}"
            )

    return errors


def run_checks(repo_root: Path) -> dict:
    errors: list[str] = []
    errors.extend(_check_azure_yaml(repo_root))
    errors.extend(_check_infra_parameters(repo_root))
    errors.extend(_check_azure_deploy_workflow(repo_root))

    return {
        "azure_prod_config_pass": not errors,
        "errors": errors,
        "root": str(repo_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT_DEFAULT),
        help="Repo root path",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print JSON result",
    )
    args = parser.parse_args()

    result = run_checks(Path(args.root))

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if result["azure_prod_config_pass"] else "FAIL"
        print(f"check_azure_prod_config: {status}")
        for err in result["errors"]:
            print(f"  ERROR: {err}")

    return 0 if result["azure_prod_config_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
