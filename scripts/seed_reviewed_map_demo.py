#!/usr/bin/env python3
"""Deterministic seed script for reviewed map demo data.

Inserts:
- 1 reviewed court/legal event
- 1 reviewed crime incident
- 1 source snapshot
- 1 review item marked approved
- 1 audit log entry

Usage:
    source .venv/bin/activate
    python scripts/seed_reviewed_map_demo.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from hashlib import sha256

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Case,
    Court,
    CrimeIncident,
    CrimeIncidentSource,
    Defendant,
    Event,
    EventDefendant,
    EventSource,
    Judge,
    LegalSource,
    Location,
    ReviewActionLog,
    ReviewItem,
    SourceSnapshot,
)
from app.core.config import get_settings


def _db_url() -> str:
    settings = get_settings()
    return str(settings.database_url)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(text: str) -> str:
    return sha256(text.encode()).hexdigest()


def _get_or_create(session: Session, model, defaults: dict, **lookup):
    obj = session.scalar(select(model).filter_by(**lookup))
    if obj:
        return obj, False
    merged = {**defaults, **lookup}
    obj = model(**merged)
    session.add(obj)
    session.flush()
    return obj, True


def seed_demo_data() -> dict:
    engine = create_engine(_db_url(), future=True)
    results: dict = {}

    with Session(engine) as session:
        try:
            # ------------------------------------------------------------------
            # 1. Source snapshot
            # ------------------------------------------------------------------
            snapshot, created = _get_or_create(
                session,
                SourceSnapshot,
                defaults={
                    "source_key": "demo_seed",
                    "source_url": "https://demo.judgetracker.ai/seed",
                    "fetched_at": _now(),
                    "content_hash": _hash("https://demo.judgetracker.ai/seed"),
                    "raw_content": '{"seed": true, "description": "Demo seed snapshot"}',
                    "storage_backend": "db",
                },
                source_key="demo_seed",
                content_hash=_hash("https://demo.judgetracker.ai/seed"),
            )
            results["source_snapshot"] = {"id": snapshot.id, "created": created}

            # ------------------------------------------------------------------
            # 2. Location for court event
            # ------------------------------------------------------------------
            court_loc, created = _get_or_create(
                session,
                Location,
                defaults={
                    "name": "Saskatoon Court of King's Bench",
                    "city": "Saskatoon",
                    "state": "SK",
                    "region": "CA",
                    "latitude": 52.1332,
                    "longitude": -106.6702,
                    "location_type": "court",
                },
                name="Saskatoon Court of King's Bench",
            )
            results["court_location"] = {"id": court_loc.id, "created": created}

            # ------------------------------------------------------------------
            # 3. Court
            # ------------------------------------------------------------------
            court, created = _get_or_create(
                session,
                Court,
                defaults={
                    "name": "Court of King's Bench for Saskatchewan",
                    "jurisdiction": "SK",
                    "region": "CA",
                    "location_id": court_loc.id,
                },
                name="Court of King's Bench for Saskatchewan",
            )
            results["court"] = {"id": court.id, "created": created}

            # ------------------------------------------------------------------
            # 4. Judge
            # ------------------------------------------------------------------
            judge, created = _get_or_create(
                session,
                Judge,
                defaults={
                    "name": "Demo Judge",
                    "normalized_name": "demo judge",
                    "court_id": court.id,
                },
                name="Demo Judge",
            )
            results["judge"] = {"id": judge.id, "created": created}

            # ------------------------------------------------------------------
            # 5. Case
            # ------------------------------------------------------------------
            case, created = _get_or_create(
                session,
                Case,
                defaults={
                    "court_id": court.id,
                    "case_type": "criminal",
                    "filed_date": datetime(2024, 1, 15, tzinfo=timezone.utc).date(),
                },
                docket_number="SEED-2024-001",
            )
            results["case"] = {"id": case.id, "created": created}

            # ------------------------------------------------------------------
            # 6. Defendant
            # ------------------------------------------------------------------
            defendant, created = _get_or_create(
                session,
                Defendant,
                defaults={
                    "public_name": "Demo Defendant",
                    "normalized_public_name": "demo defendant",
                },
                anonymized_id="demo-defendant-001",
            )
            results["defendant"] = {"id": defendant.id, "created": created}

            # ------------------------------------------------------------------
            # 7. Legal source for event
            # ------------------------------------------------------------------
            legal_source, created = _get_or_create(
                session,
                LegalSource,
                defaults={
                    "source_type": "court_record",
                    "title": "Demo Legal Source",
                    "url": "https://demo.judgetracker.ai/source/1",
                    "url_hash": _hash("https://demo.judgetracker.ai/source/1"),
                    "source_quality": "court_record",
                    "verified_flag": True,
                    "retrieved_at": _now(),
                    "review_status": "verified_court_record",
                    "reviewed_at": _now(),
                    "reviewed_by": "seed_script",
                    "public_visibility": True,
                },
                source_id="SEED-SRC-001",
            )
            results["legal_source"] = {"id": legal_source.id, "created": created}

            # ------------------------------------------------------------------
            # 8. Reviewed court/legal event
            # ------------------------------------------------------------------
            event, created = _get_or_create(
                session,
                Event,
                defaults={
                    "court_id": court.id,
                    "judge_id": judge.id,
                    "case_id": case.id,
                    "primary_location_id": court_loc.id,
                    "event_type": "sentencing",
                    "event_subtype": "custodial",
                    "decision_date": datetime(2024, 3, 22, tzinfo=timezone.utc).date(),
                    "title": "Demo sentencing order",
                    "summary": "Demo seed sentencing order for map display.",
                    "repeat_offender_indicator": False,
                    "verified_flag": True,
                    "source_quality": "court_record",
                    "last_verified_at": _now(),
                    "review_status": "verified_court_record",
                    "reviewed_at": _now(),
                    "reviewed_by": "seed_script",
                    "review_notes": "Approved for public display via seed script.",
                    "public_visibility": True,
                    "classifier_metadata": {"confidence": 0.95, "seed": True},
                },
                event_id="EVT-SEED-001",
            )
            results["event"] = {"id": event.id, "created": created}

            # Link event to defendant
            _get_or_create(
                session,
                EventDefendant,
                defaults={},
                event_id=event.id,
                defendant_id=defendant.id,
            )

            # Link event to source
            _get_or_create(
                session,
                EventSource,
                defaults={},
                event_id=event.id,
                source_id=legal_source.id,
            )

            # ------------------------------------------------------------------
            # 9. Location for crime incident
            # ------------------------------------------------------------------
            crime_loc, created = _get_or_create(
                session,
                Location,
                defaults={
                    "name": "Downtown Saskatoon",
                    "city": "Saskatoon",
                    "state": "SK",
                    "region": "CA",
                    "latitude": 52.1332,
                    "longitude": -106.6702,
                    "location_type": "public_area",
                },
                name="Downtown Saskatoon",
            )
            results["crime_location"] = {"id": crime_loc.id, "created": created}

            # ------------------------------------------------------------------
            # 10. Reviewed crime incident
            # ------------------------------------------------------------------
            # Use ingestion_identity_hash for the lookup key because it has a
            # partial unique index (WHERE ingestion_identity_hash IS NOT NULL)
            # and is stable regardless of source_name or source_key changes.
            incident, created = _get_or_create(
                session,
                CrimeIncident,
                defaults={
                    "source_id": "SEED-CRIME-001",
                    "external_id": "SEED-EXT-001",
                    "incident_type": "Theft",
                    "incident_category": "property",
                    "reported_at": _now(),
                    "occurred_at": _now(),
                    "city": "Saskatoon",
                    "province_state": "SK",
                    "country": "Canada",
                    "public_area_label": "Downtown Saskatoon",
                    "latitude_public": 52.1332,
                    "longitude_public": -106.6702,
                    "precision_level": "general_area",
                    "source_url": "https://demo.judgetracker.ai/crime/1",
                    "source_name": "Saskatoon Police Service",
                    "source_key": "saskatoon_police",
                    "ingestion_identity_hash": _hash("SEED-CRIME-001"),
                    "verification_status": "reported",
                    "data_last_seen_at": _now(),
                    "is_public": True,
                    "review_status": "official_police_open_data_report",
                    "reviewed_at": _now(),
                    "reviewed_by": "seed_script",
                    "review_notes": "Approved for public display via seed script.",
                    "source_snapshot_id": snapshot.id,
                },
                ingestion_identity_hash=_hash("SEED-CRIME-001"),
            )
            results["crime_incident"] = {"id": incident.id, "created": created}

            # Link incident to source
            _get_or_create(
                session,
                CrimeIncidentSource,
                defaults={},
                crime_incident_id=incident.id,
                source_id=legal_source.id,
            )

            # ------------------------------------------------------------------
            # 11. Review item marked approved
            # ------------------------------------------------------------------
            review_item, created = _get_or_create(
                session,
                ReviewItem,
                defaults={
                    "record_type": "court_event",
                    "raw_source_id": event.id,
                    "source_snapshot_id": snapshot.id,
                    "suggested_payload_json": {
                        "event_id": event.event_id,
                        "title": event.title,
                        "review_status": event.review_status,
                    },
                    "source_url": "https://demo.judgetracker.ai/source/1",
                    "source_quality": "court_record",
                    "confidence": 0.95,
                    "privacy_status": "public_safe",
                    "publish_recommendation": "publish",
                    "public_visibility": True,
                    "ingestion_identity_hash": _hash("EVT-SEED-001"),
                    "status": "approved",
                    "reviewer_id": "seed_script",
                    "reviewer_notes": "Auto-approved deterministic seed data.",
                    "reviewed_at": _now(),
                },
                ingestion_identity_hash=_hash("EVT-SEED-001"),
            )
            results["review_item"] = {"id": review_item.id, "created": created}

            # ------------------------------------------------------------------
            # 12. Audit log entry
            # ------------------------------------------------------------------
            # Include actor in the lookup filter to avoid ambiguity when
            # multiple action logs exist for the same review item and action.
            action_log, created = _get_or_create(
                session,
                ReviewActionLog,
                defaults={
                    "actor": "seed_script",
                    "action": "approve",
                    "before_json": {"status": "pending"},
                    "after_json": {"status": "approved", "public_visibility": True},
                },
                review_item_id=review_item.id,
                action="approve",
                actor="seed_script",
            )
            results["audit_log"] = {"id": action_log.id, "created": created}

            session.commit()
        except Exception:
            session.rollback()
            raise

    print("Seed demo data completed successfully.")
    for key, val in results.items():
        print(f"  {key}: id={val['id']}, created={val['created']}")
    return results


if __name__ == "__main__":
    seed_demo_data()
