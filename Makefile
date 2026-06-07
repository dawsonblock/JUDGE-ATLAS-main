.PHONY: backend-install backend-test frontend-install frontend-check frontend-typecheck verify verify-runtime doctor-macos docker-smoke docker-proof-junit proof release-proof backend-proof frontend-build bootstrap-backend bootstrap-frontend bootstrap truth-check full-proof clean-clone-proof release-proof-local release-package-proof-local nox test check-generated dev stop setup release-zip build-clean-release validate-release-zip proof-static validate-archive-freshness validate-handoff-consistency saskatoon-staging-proof canlii-staging-contract statscan-boundary-proof validate-smoke-workspace validate-full-workspace validate-docker-workspace check-route-contract check-local-env check-config-docs sync-status-docs test-backend-unit test-backend-integration test-backend-db test-backend-auth test-backend-ingestion test-backend-proof test-frontend typecheck-frontend build-frontend lint-frontend frontend-route-smoke test-frontend-proof proof-evidence-verification validate-build validate-source-snapshot validate-build-no-docker

backend-install:
	cd backend && python -m pip install -e ".[test]"

backend-test:
	cd backend && python -m compileall -q app
	python -m pytest -q backend/app/tests

frontend-install:
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm ci --prefix frontend'

frontend-check:
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run lint --prefix frontend; \
		npm run typecheck --prefix frontend; \
		npm run build --prefix frontend'

frontend-build:
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run build --prefix frontend'

frontend-typecheck:
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run typecheck --prefix frontend'

test-backend-unit:
	@mkdir -p artifacts/proof/current
	@python3 -m pytest backend/app/tests -m unit -q 2>&1 | tee artifacts/proof/current/backend_unit_pytest.log

test-backend-integration:
	@mkdir -p artifacts/proof/current
	@python3 -m pytest backend/app/tests -m integration -q 2>&1 | tee artifacts/proof/current/backend_integration_pytest.log

test-backend-db:
	@mkdir -p artifacts/proof/current
	@python3 -m pytest backend/app/tests -m db -q 2>&1 | tee artifacts/proof/current/backend_db_pytest.log

test-backend-auth:
	@mkdir -p artifacts/proof/current
	@python3 -m pytest backend/app/tests -m auth -q 2>&1 | tee artifacts/proof/current/backend_auth_pytest.log

test-backend-ingestion:
	@mkdir -p artifacts/proof/current
	@python3 -m pytest backend/app/tests -m ingestion -q 2>&1 | tee artifacts/proof/current/backend_ingestion_pytest.log

test-backend-proof: test-backend-unit test-backend-integration test-backend-db test-backend-auth test-backend-ingestion

test-frontend:
	@mkdir -p artifacts/proof/current
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run test --prefix frontend 2>&1 | tee artifacts/proof/current/frontend_test.log; \
		npm run test:junit --prefix frontend 2>&1 | tee artifacts/proof/current/frontend_vitest_junit.log || true'

typecheck-frontend:
	@mkdir -p artifacts/proof/current
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run typecheck --prefix frontend 2>&1 | tee artifacts/proof/current/frontend_typecheck.log'

build-frontend:
	@mkdir -p artifacts/proof/current
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run build --prefix frontend 2>&1 | tee artifacts/proof/current/frontend_build.log'

lint-frontend:
	@mkdir -p artifacts/proof/current
	@bash -lc 'NVM_DIR="$${NVM_DIR:-$$HOME/.nvm}"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		nvm use 22.22.3 >/dev/null 2>&1 || { echo "BLOCKED_NODE_VERSION: nvm use 22.22.3 failed -- install Node 22.22.3 via: nvm install 22.22.3"; exit 1; }; \
		npm run lint --prefix frontend 2>&1 | tee artifacts/proof/current/frontend_lint.log'

frontend-route-smoke:
	@mkdir -p artifacts/proof/current
	@python3 scripts/frontend_route_smoke.py 2>&1 | tee artifacts/proof/current/frontend_route_smoke.log

test-frontend-proof: test-frontend typecheck-frontend build-frontend lint-frontend frontend-route-smoke

bootstrap-backend:
	bash scripts/bootstrap_backend.sh

bootstrap-frontend:
	bash scripts/bootstrap_frontend.sh

bootstrap:
	bash scripts/bootstrap_all.sh

# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------

# setup: copy .env.example → .env (if not present) then install all deps
setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example — review tokens before production use"; fi
	bash scripts/bootstrap_all.sh

# dev: start the full stack via Docker Compose (creates .env automatically)
dev:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example — review tokens before production use"; fi
	docker compose up --build

# stop: tear down Docker Compose services
stop:
	docker compose down

truth-check:
	python3 scripts/check_truth_claims.py --root .
	python3 scripts/check_status_truth_consistency.py --root .
	python3 scripts/check_config_docs_consistency.py --root .
	python3 scripts/validate_workflows.py
	python3 scripts/check_source_keys.py
	python3 scripts/check_statuses.py
	python3 scripts/check_azure_prod_config.py --root .

check-local-env:
	python3 scripts/check_local_dev_environment.py

verify-runtime:
	python3 scripts/check_runtime_versions.py --root .

doctor-macos:
	bash scripts/dev_doctor_macos.sh

check-config-docs:
	python3 scripts/check_config_docs_consistency.py --root .

check-generated:
	python3 scripts/check_no_generated_files.py --root .

nox:
	nox

full-proof:
	bash scripts/proof_full_stack.sh

release-proof-local:
	@if [ -x backend/.venv/bin/python ]; then \
		backend/.venv/bin/python scripts/release_gate.py; \
	else \
		python3 scripts/release_gate.py; \
	fi

release-package-proof-local:
	bash scripts/package_and_validate_release_archive.sh

clean-clone-proof:
	bash scripts/proof_clean_clone.sh

backend-proof:
	cd backend && python scripts/proof_backend_import.py

# test is an alias for backend-test
test: backend-test

# verify runs the full quality gate (no Docker)
verify: verify-runtime check-generated truth-check backend-install backend-test frontend-install frontend-check

docker-smoke:
	docker compose up -d --build
	curl -f http://localhost:8000/docs >/dev/null
	curl -f http://localhost:3000 >/dev/null
	docker compose down -v

docker-proof-junit:
	@mkdir -p artifacts/proof/current
	@python3 scripts/wrap_as_junit.py \
		--suite docker_runtime_preflight \
		--xml artifacts/proof/current/docker_runtime_preflight.xml \
		-- bash scripts/check_docker_runtime.sh \
		2>&1 | tee artifacts/proof/current/docker_runtime_preflight_junit.log || true

proof-evidence-verification:
	@mkdir -p artifacts/proof/current
	@if [ ! -f artifacts/proof/current/evidence_verification_standard.log ]; then \
		python3 scripts/check_evidence_verification_standard.py | tee artifacts/proof/current/evidence_verification_standard.log; \
	else \
		echo "Skipping evidence_verification_standard.log: already produced by release gate"; \
	fi
	@if [ ! -f artifacts/proof/current/evidence_verification_standard_pytest.log ]; then \
		python3 -m pytest tests/proof/test_evidence_verification_standard.py -q | tee artifacts/proof/current/evidence_verification_standard_pytest.log; \
	else \
		echo "Skipping evidence_verification_standard_pytest.log: already produced by release gate"; \
	fi

proof:
	@echo "=== Running canonical proof generation ==="
	@python3 scripts/check_runtime_versions.py --root .
	@python3 scripts/check_toolchain_versions.py --root .
	@$(MAKE) test-backend-proof test-frontend-proof
	@$(MAKE) release-proof-local
	@$(MAKE) docker-proof-junit
	@python3 scripts/write_repair_report.py
	@python3 scripts/check_single_proof_authority.py
	@python3 scripts/check_status_truth_consistency.py --root .
	@python3 scripts/check_proof_consistency.py
	@python3 scripts/check_proof_freshness.py
	@python3 scripts/check_no_post_proof_mutation.py
	@python3 scripts/check_release_claims.py --root .
	@python3 scripts/verify_proof_hash_sync.py --root .
	@python3 scripts/check_required_proof_logs.py --strict-required-files
	@$(MAKE) proof-evidence-verification
	@echo "Canonical proof: artifacts/proof/current/release_gate.json"
	@echo "Run 'bash scripts/package_and_validate_release_archive.sh' to build archive and validate handoff"

release-proof:
	@python3 scripts/check_runtime_versions.py --root .
	@python3 scripts/check_toolchain_versions.py --root .
	@python3 scripts/check_node_policy.py
	@python3 scripts/check_frontend_node_gate.py --expected-major 22
	@python3 scripts/check_false_claims.py
	@python3 scripts/check_status_truth_consistency.py --root .
	@python3 scripts/check_api_contracts.py
	@python3 scripts/check_frontend_backend_route_contract.py
	@python3 scripts/check_map_route.py
	@python3 scripts/check_proof_freshness.py
	@python3 scripts/check_no_post_proof_mutation.py
	@python3 scripts/check_release_claims.py --root .
	@python3 scripts/verify_proof_hash_sync.py --root .
	@python3 scripts/check_proof_consistency.py
	@python3 scripts/check_release_gate.py --root .
	@python3 scripts/check_required_proof_logs.py --root . --strict-required-files
	@python3 scripts/check_single_proof_authority.py --root .
	@bash scripts/check_no_pyc.sh
	@python3 scripts/check_azure_prod_config.py --root .
	@python3 scripts/check_no_generated_files.py --root .
	@bash scripts/package_and_validate_release_archive.sh --archive-path dist/JUDGE_ATLAS-main-final.zip --package-root-name JUDGE_ATLAS-main
	@python3 scripts/validate_final_zip.py dist/JUDGE_ATLAS-main-final.zip
	@python3 scripts/check_release_surface.py --archive dist/JUDGE_ATLAS-main-final.zip
	@python3 scripts/validate_extracted_release.py --archive dist/JUDGE_ATLAS-main-final.zip --expected-root JUDGE_ATLAS-main
	@python3 scripts/cleanroom_release_test.py --archive dist/JUDGE_ATLAS-main-final.zip

check-route-contract:
	@python3 scripts/check_frontend_backend_route_contract.py

sync-status-docs:
	@python3 scripts/sync_status_docs_from_gate.py --root .

validate-handoff-consistency:
	@python3 scripts/sync_status_docs_from_gate.py --root .
	@python3 scripts/check_release_handoff_consistency.py --archive dist/JUDGE_ATLAS-main-final.zip

validate-archive-freshness:
	@python3 scripts/verify_archive_proof_freshness.py --archive $(ARCHIVE)

saskatoon-staging-proof:
	@backend/.venv/bin/python -m pytest backend/app/tests/test_saskatoon_open_data_staging.py -q

canlii-staging-contract:
	@backend/.venv/bin/python -m pytest backend/app/tests/test_saskatchewan_court_sources.py backend/app/tests/test_canlii_sk_ingest.py -q

statscan-boundary-proof:
	@backend/.venv/bin/python -m pytest backend/app/tests/test_statscan_table_adapter_boundary.py backend/app/tests/test_source_registry_consistency.py -q

build-clean-release:
	@echo "DEPRECATED: use make release-package-proof-local (authoritative pipeline)"
	@bash scripts/package_and_validate_release_archive.sh --archive-path dist/JUDGE_ATLAS-main-final.zip --package-root-name JUDGE_ATLAS-main

validate-release-zip:
	@echo "DEPRECATED: use validate_final_zip/check_release_surface/verify_archive_proof_freshness on dist/JUDGE_ATLAS-main-final.zip"
	@python3 scripts/validate_final_zip.py dist/JUDGE_ATLAS-main-final.zip
	@python3 scripts/check_release_surface.py --archive dist/JUDGE_ATLAS-main-final.zip
	@python3 scripts/verify_archive_proof_freshness.py --archive dist/JUDGE_ATLAS-main-final.zip

validate-smoke-workspace:
	@TOOLATHLON_PROFILE=smoke bash scripts/validate_smoke_workspace.sh

validate-full-workspace:
	@TOOLATHLON_PROFILE=full bash scripts/validate_full_workspace.sh

validate-docker-workspace:
	@TOOLATHLON_PROFILE=smoke RUN_DOCKER=1 bash scripts/validate_smoke_workspace.sh

# proof-static: dependency-free boundary checks (no backend install required)
proof-static:
	@python3 scripts/validate_runtime_boundaries.py --static-only
	@python3 scripts/check_truth_claims.py --root .
	@echo "Static boundary checks complete (no backend install required)"

# validate-build: full 21-step validation — source snapshot → proof → canonical archive
validate-build:
	@bash scripts/run_full_validation.sh

# validate-source-snapshot: validate source snapshot only
# Usage: make validate-source-snapshot SOURCE_ZIP=/path/to/archive.zip
validate-source-snapshot:
	@bash scripts/run_full_validation.sh \
		--source-snapshot \
		$(if $(SOURCE_ZIP),--source-zip "$(SOURCE_ZIP)",)

# validate-build-no-docker: full validation without Docker-dependent phases
validate-build-no-docker:
	@bash scripts/run_full_validation.sh --source-snapshot --skip-docker

# release-zip: create a distributable archive excluding development artifacts
release-zip:
	@VERSION=$$(date +%Y%m%d-%H%M%S); \
	OUTFILE="judge_atlas_source_snapshot_$${VERSION}.zip"; \
	bash scripts/create_release_zip.sh --allow-non-authoritative --output "$${OUTFILE}"; \
	echo "Non-authoritative source snapshot archive: $${OUTFILE}"; \
	echo "For distributable releases use: make release-package-proof-local"

# verify-upload: validate canonical archive before uploading
# Ensures only dist/JUDGE_ATLAS-main-final.zip is uploaded
verify-upload:
	@bash scripts/verify_upload_ready.sh

# build-for-upload: produce the canonical archive after strict proof regeneration
# Usage: make build-for-upload
# This forces full proof regeneration, runs all validators, then builds the archive.
# The archive is copied to Desktop as UPLOAD_THIS_JUDGE_ATLAS-main-final.zip.
# Expert override: make build-for-upload EXISTING_PROOF=1 (not recommended)
build-for-upload:
	@bash scripts/build_for_upload.sh
