# Environment Variables

This document describes all runtime environment variables used by JUDGE_ATLAS.

## Core Application

| Variable | Default | Description |
|---|---|---|
| `JTA_APP_ENV` | `development` | Runtime environment: `development`, `staging`, or `production`. |
| `JTA_RUNTIME_PROFILE` | `alpha_local` | Deployment profile identifier. |
| `JTA_DATABASE_URL` | `sqlite:///./judgetracker.db` | Database connection string. PostgreSQL recommended for production. |
| `JTA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection (optional for local dev). |
| `JTA_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed CORS origins. |

## Evidence & Storage

| Variable | Default | Description |
|---|---|---|
| `JTA_EVIDENCE_STORE_ROOT` | `./artifacts/evidence-store` | Root path for evidence artifact storage. |
| `JTA_EVIDENCE_STORE_REQUIRED` | `false` | Whether evidence store is mandatory. |
| `JTA_STORAGE_BACKEND` | `local` | Storage backend type. |

## Queue & Rate Limiting

| Variable | Default | Description |
|---|---|---|
| `JTA_INGESTION_QUEUE_BACKEND` | `inprocess` | Queue backend: `inprocess` or `redis`. |
| `JTA_RATE_LIMIT_BACKEND` | `memory` | Rate limiter backend: `memory` or `redis`. |

## Security

| Variable | Default | Description |
|---|---|---|
| `JTA_JWT_SECRET_KEY` | *(required)* | Long random secret for JWT signing. |
| `JTA_JWT_ALGORITHM` | `HS256` | JWT algorithm. |
| `JTA_ADMIN_TOKEN` | *(required)* | Shared admin token (deprecated; migrate to JWT). |
| `JTA_ADMIN_REVIEW_TOKEN` | *(required)* | Shared review token (deprecated; migrate to JWT). |
| `JTA_FETCH_EGRESS_PROXY` | *(empty)* | Outbound fetch proxy URL (required in production). |
| `JTA_ALLOW_DIRECT_PROD_FETCH_WITH_NETWORK_POLICY` | *(unset)* | Acknowledge direct fetch risk if network policy handles egress. |

## Feature Gates

| Variable | Default | Description |
|---|---|---|
| `JTA_ENABLE_PUBLIC_PLATFORM` | `false` | Enable public-facing platform endpoints. |
| `JTA_ENABLE_EXPERIMENTAL_LIVE_MAP` | `false` | Enable live map features. |
| `JTA_ENABLE_WORKFLOW_ADMIN` | `false` | Enable workflow admin UI. |
| `JTA_ENABLE_LEGACY_ADMIN_TOKEN` | `false` | Allow legacy shared-token admin auth. |
| `JTA_ENABLE_ADMIN_IMPORTS` | `false` | Enable admin import endpoints. |
| `JTA_ENABLE_ADMIN_REVIEW` | `false` | Enable admin review endpoints. |
| `JTA_ENABLE_PUBLIC_EVENT_POST` | `false` | Allow public event posting. |
| `JTA_AUTO_SEED` | `true` | Auto-seed sample data in development. |

## External APIs

| Variable | Default | Description |
|---|---|---|
| `JTA_CANLII_API_KEY` | *(optional)* | CanLII API key for Saskatchewan court decisions. |
| `JTA_LEXUM_API_KEY` | *(optional)* | Lexum SCC bulk API key. |
| `JTA_COURTLISTENER_API_TOKEN` | *(optional)* | CourtListener API token. |
| `JTA_COURTLISTENER_BASE_URL` | `https://www.courtlistener.com/api/rest/v4` | CourtListener base URL. |
| `JTA_COURTLISTENER_MAX_PAGES` | `10` | Max pages to fetch per run. |
| `JTA_COURTLISTENER_TIMEOUT_SECONDS` | `60` | Request timeout. |
| `JTA_GEONAMES_USERNAME` | *(optional)* | GeoNames username for geocoding. |

## Frontend

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend API base URL. |
| `NEXT_PUBLIC_ENABLE_LIVE_MAP` | `false` | Enable live map in frontend. |
| `NEXT_PUBLIC_ENABLE_ADMIN_UI` | `true` | Enable admin UI in frontend. |

## Data Feeds

| Variable | Default | Description |
|---|---|---|
| `JTA_STATSCAN_ENABLED` | `false` | Enable Statistics Canada data feeds. |
| `JTA_FBI_CRIME_ENABLED` | `false` | Enable FBI crime data feeds. |
| `JTA_LOCAL_FEEDS_ENABLED` | `false` | Enable local jurisdiction feeds. |
| `JTA_GDELT_ENABLED` | `false` | Enable GDELT event feeds. |

## Ollama / LLM (optional)

| Variable | Default | Description |
|---|---|---|
| `JTA_OLLAMA_ENABLED` | `false` | Enable Ollama integration. |
| `JTA_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama base URL. |
| `JTA_OLLAMA_MODEL` | `mistral` | Default model name. |
| `JTA_OLLAMA_TIMEOUT_SECONDS` | `30` | Request timeout. |
