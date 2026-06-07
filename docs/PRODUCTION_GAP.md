# Production Gaps

This document lists known gaps between alpha and production readiness.

**This is NOT production-ready software. Do not use in production.**

## Critical Gaps

### 1. Limited Source Coverage

Current state: 12 runnable sources out of 27 total.

Required for production: 20+ verified sources with proven ingestion, or explicit deprecation/disabled status.

### 2. Alpha Ingestion Adapters

Some adapters are scaffolding with `NotImplementedError` hits:

- `backend/app/ingestion/adapters.py` — may have placeholder implementations
- Test files with `@pytest.mark.skip` or `raise NotImplementedError`

Production requirement: All runnable adapters must be fully implemented. Incomplete adapters must be marked `disabled` or `deprecated`.

### 3. No Production Monitoring

Current: Basic health checks.

Production requirement:
- Application Performance Monitoring (APM)
- Error tracking (Sentry, etc.)
- Log aggregation and analysis
- Metrics collection (Prometheus, Datadog, etc.)
- Alerting for SLA violations
- On-call team and incident response procedures

### 4. No Legal Professional Review

Current: Internal proof checks only.

Production requirement:
- Review by legal professionals or paralegals
- Audit of data accuracy and sourcing
- Verification of redaction/privacy policies
- Sign-off on legal liability disclaimers

### 5. No Red-Team Privacy Audit

Current: Automated tests for data leakage.

Production requirement:
- Engaged red-team or security firm
- Formal privacy audit with written report
- Penetration testing
- GDPR/privacy law compliance verification

### 6. Limited Live-Source Proof

Current: Fixture-based end-to-end tests.

Production requirement:
- Live-source ingestion tests (subset of real sources)
- Deterministic fallback fixtures for CI/CD
- Rate-limit compliance verification
- Robots.txt compliance proof

### 7. No Deployment Rollback Proof

Current: Not tested.

Production requirement:
- Tested rollback procedure
- Point-in-time restore capabilities
- Migration reversal proof
- Zero-downtime deployment patterns

### 8. Limited Audit Trail

Current: Bi-temporal versioning in schema.

Production requirement:
- Complete immutable audit log
- Cryptographic signing of changes
- Retention policy (legal holds, etc.)
- Compliance with data protection regulations

### 9. No Load Testing

Current: No scalability testing.

Production requirement:
- Load test with realistic traffic patterns
- 99th percentile latency acceptable
- Database query optimization completed
- Caching strategy implemented and validated

### 10. No Failover Testing

Current: Single-instance deployment assumed.

Production requirement:
- Multi-instance setup tested
- Database failover tested
- Cache failover tested (Redis, etc.)
- DNS/load balancer failover tested

## Moderate Gaps

### API Versioning

Current: No API versioning strategy.

Requirement: `/v1/`, `/v2/` endpoints; deprecation timeline for old versions.

### Rate Limiting

Current: Basic rate limits.

Requirement: Per-user, per-API-key, per-IP rate limits with graceful degradation.

### CORS Policy

Current: Likely permissive for development.

Requirement: Strict CORS policy for production; verified against actual frontend hosts.

### Input Validation

Current: Pydantic models for most routes.

Requirement: Exhaustive input validation testing; security review of validation rules.

## Documentation Gaps

### User Guides

Missing: How to use the map, filters, search features.

### Admin Runbooks

Missing: How to ingest new sources, debug issues, respond to incidents.

### Legal Disclaimers

Missing: Liability waivers, accuracy disclaimers, privacy policy.

### Developer Guides

Current: Basic README.

Requirement: Setup guide, architecture guide, deployment guide, testing guide.

## Quality Gaps

### Test Coverage

Current: ~70% backend, ~60% frontend (estimate).

Requirement: 85%+ backend, 75%+ frontend for critical paths.

### Static Analysis

Current: Basic linting.

Requirement: SonarQube, CodeQL, or equivalent with baseline.

### Dependency Scanning

Current: Manual review.

Requirement: Automated dependency scanning with CI/CD gate for critical/high vulnerabilities.

## Timeline to Production

**Estimate: 3-6 months of focused work**

### Phase 1 (Month 1-2): Source Completion

- [ ] Fix all NotImplementedError hits
- [ ] Verify 20+ sources runnable
- [ ] Red-team test source redaction

### Phase 2 (Month 2-3): Monitoring & Ops

- [ ] Deploy APM
- [ ] Set up logging and metrics
- [ ] Create incident response runbook
- [ ] On-call team training

### Phase 3 (Month 3-4): Legal & Privacy

- [ ] Engage legal professionals
- [ ] Formal privacy audit
- [ ] Red-team security audit
- [ ] Write legal disclaimers

### Phase 4 (Month 4-5): Performance & Reliability

- [ ] Load testing
- [ ] Failover testing
- [ ] Optimize database queries
- [ ] Implement caching

### Phase 5 (Month 5-6): Documentation & Testing

- [ ] Write user guides
- [ ] Write admin runbooks
- [ ] Increase test coverage to 85%+
- [ ] Security review all routes

## Current Status

**State**: `self_verifying_alpha`
**Production Ready**: NO
**Public Release Safe**: NO

This is alpha software suitable for:
- Internal testing
- Legal research prototyping
- Early user feedback
- Architecture validation

This is NOT suitable for:
- Public deployment
- Production use by third parties
- Handling real sensitive data
- Legal proceedings or official decisions
