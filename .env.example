# Root development environment
# Copy to .env: cp .env.example .env
# Review all values before use in any non-development environment.

JTA_APP_ENV=development
JTA_API_HOST=127.0.0.1
JTA_API_PORT=8000
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=judge_atlas
POSTGRES_USER=judge_atlas
POSTGRES_PASSWORD=judge_atlas_dev_password
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=judge_atlas_dev
MINIO_SECRET_KEY=judge_atlas_dev_password
MINIO_BUCKET=evidence
JTA_EVIDENCE_STORE_ROOT=./data/evidence
JTA_JWT_AUTH_ENABLED=false
JTA_JWT_SECRET=dev-only-change-me
JTA_ADMIN_AUTH_MODE=dev
JTA_EGRESS_PROXY_REQUIRED=false
JTA_RUNTIME_PROFILE=alpha_local
JTA_DATABASE_URL=postgresql+psycopg://judge_atlas:judge_atlas_dev_password@localhost:5432/judge_atlas
JTA_REDIS_URL=redis://localhost:6379/0
JTA_JWT_SECRET_KEY=dev-only-change-me
JTA_JWT_ALGORITHM=HS256
JTA_CORS_ORIGINS=http://localhost:3000
JTA_EVIDENCE_STORE_REQUIRED=false
JTA_STORAGE_BACKEND=local
JTA_ENABLE_EXPERIMENTAL_LIVE_MAP=false
JTA_ENABLE_WORKFLOW_ADMIN=false
JTA_ENABLE_LEGACY_ADMIN_TOKEN=false
JTA_FETCH_EGRESS_PROXY=
JTA_RATE_LIMIT_BACKEND=memory
JTA_INGESTION_QUEUE_BACKEND=inprocess

# Frontend build-time variables (referenced by CI and documentation)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_LIVE_MAP=false
NEXT_PUBLIC_ENABLE_ADMIN_UI=true
