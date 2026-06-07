# Environment Template

Copy the relevant block into a `.env` file at the repository root and fill in secrets.
Do NOT commit `.env` to version control.

## Root `.env` (minimal local development)

```bash
# JudgeTracker Atlas — Environment Configuration
# Copy to .env and adjust for your environment

# Database (SQLite default for local dev, PostgreSQL for production)
JTA_DATABASE_URL=sqlite:///./judgetracker.db

# Environment
JTA_APP_ENV=development
JTA_RUNTIME_PROFILE=alpha_local

# Redis (optional for local dev)
JTA_REDIS_URL=redis://localhost:6379/0

# CORS Origins (comma-separated)
JTA_CORS_ORIGINS=http://localhost:3000

# Evidence store / storage backend
JTA_EVIDENCE_STORE_ROOT=./artifacts/evidence-store
JTA_EVIDENCE_STORE_REQUIRED=false
JTA_STORAGE_BACKEND=local

# Queue / rate limit backends
JTA_INGESTION_QUEUE_BACKEND=inprocess
JTA_RATE_LIMIT_BACKEND=memory

# Production outbound fetch safety (required in production)
JTA_FETCH_EGRESS_PROXY=

# Runtime feature gates
JTA_ENABLE_PUBLIC_PLATFORM=false
JTA_ENABLE_EXPERIMENTAL_LIVE_MAP=false
JTA_ENABLE_WORKFLOW_ADMIN=false
JTA_ENABLE_LEGACY_ADMIN_TOKEN=false

# JWT defaults (replace in non-local environments)
JTA_JWT_SECRET_KEY=replace_with_long_random_secret
JTA_JWT_ALGORITHM=HS256

# Frontend API base
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_LIVE_MAP=false
NEXT_PUBLIC_ENABLE_ADMIN_UI=true
```

## Backend `.env` (extended backend-only variables)

```bash
# JudgeTracker Atlas — Backend Environment Configuration
# All variables use JTA_ prefix to match Settings in app/core/config.py

# Database
# SQLite (default for local dev):
JTA_DATABASE_URL=sqlite:///./judgetracker.db
# PostgreSQL (production/Docker):
# JTA_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/judgetracker

# Production outbound fetch safety
# JTA_FETCH_EGRESS_PROXY=http://egress-proxy:8080
# JTA_ALLOW_DIRECT_PROD_FETCH_WITH_NETWORK_POLICY=1

# Environment
JTA_APP_ENV=development
JTA_RUNTIME_PROFILE=alpha_local

# Auto-seed sample data (only in development)
JTA_AUTO_SEED=true

# CORS Origins (comma-separated)
JTA_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Evidence store / storage backend
JTA_EVIDENCE_STORE_ROOT=./artifacts/evidence-store
JTA_EVIDENCE_STORE_REQUIRED=false
JTA_STORAGE_BACKEND=local

# Queue / rate limit backends
JTA_INGESTION_QUEUE_BACKEND=inprocess
JTA_RATE_LIMIT_BACKEND=memory

# Runtime feature gates
JTA_ENABLE_PUBLIC_PLATFORM=false
JTA_ENABLE_EXPERIMENTAL_LIVE_MAP=false
JTA_ENABLE_WORKFLOW_ADMIN=false
JTA_ENABLE_LEGACY_ADMIN_TOKEN=false

# JWT defaults (replace in non-local environments)
JTA_JWT_SECRET_KEY=replace_with_long_random_secret
JTA_JWT_ALGORITHM=HS256

# Admin Authentication (required for admin routes)
JTA_ADMIN_TOKEN=your-secure-admin-token-here
JTA_ADMIN_REVIEW_TOKEN=your-secure-review-token-here

# Admin Feature Flags
JTA_ENABLE_ADMIN_IMPORTS=false
JTA_ENABLE_ADMIN_REVIEW=false
JTA_ENABLE_PUBLIC_EVENT_POST=false

# CourtListener API
JTA_COURTLISTENER_API_TOKEN=your-courtlistener-token-here
JTA_COURTLISTENER_BASE_URL=https://www.courtlistener.com/api/rest/v4
JTA_COURTLISTENER_MAX_PAGES=10
JTA_COURTLISTENER_MAX_DOCKETS_PER_RUN=100
JTA_COURTLISTENER_TIMEOUT_SECONDS=60

# Ollama / Source Verification (optional, disabled by default)
JTA_OLLAMA_ENABLED=false
JTA_OLLAMA_BASE_URL=http://localhost:11434
JTA_OLLAMA_MODEL=mistral
JTA_OLLAMA_TIMEOUT_SECONDS=30

# Crime Data Feed Flags
JTA_STATSCAN_ENABLED=false
JTA_FBI_CRIME_ENABLED=false
JTA_LOCAL_FEEDS_ENABLED=false
JTA_GDELT_ENABLED=false

# Geocoding
JTA_GEONAMES_USERNAME=your-geonames-username

# Canadian Legal Sources
# CanLII API key — required for sk_courts_qb_decisions and sk_courts_ca_decisions
# JTA_CANLII_API_KEY=your-canlii-api-key

# Lexum SCC bulk API key — optional, for historical SCC decision back-fill
# JTA_LEXUM_API_KEY=your-lexum-api-key
```

## Frontend `.env` (frontend-only variables)

```bash
# Frontend alpha local defaults
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_LIVE_MAP=false
NEXT_PUBLIC_ENABLE_ADMIN_UI=true
```
