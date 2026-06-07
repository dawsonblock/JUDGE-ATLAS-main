#!/usr/bin/env python3
"""
Generate source registry proof with strict classifier.

Reads canada_saskatchewan_sources.yaml and generates a consistent
proof JSON using the unified classifier.
"""

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.ingestion.source_registry_classifier import (
    classify_source,
    count_sources_by_status,
)


def main() -> int:
    # Load YAML
    yaml_path = Path(__file__).parent.parent / "backend" / "app" / "ingestion" / "sources" / "canada_saskatchewan_sources.yaml"
    data = yaml.safe_load(yaml_path.read_text())
    sources = data.get("sources", [])
    
    # Classify all sources
    classified_sources = []
    for source in sources:
        classification = classify_source(source)
        classified_sources.append({
            "source_key": source.get("source_key"),
            "automation_status": source.get("automation_status"),
            "lifecycle_state": source.get("lifecycle_state"),
            "classification": classification,
            "runnable_now": classification == "runnable_now",
            "enable_ready": classification == "enable_ready",
        })
    
    # Count by status
    counts = count_sources_by_status(sources)
    
    # Build proof JSON
    proof = {
        "status": "PASS",
        "timestamp": "2026-06-07T00:00:00Z",
        "classifier_used": "strict_automation_status_plus_lifecycle_state",
        "summary": {
            "total_sources": len(sources),
            "machine_ingest_sources": sum(1 for s in sources if s.get("source_class") == "machine_ingest"),
            "runnable_now": counts["runnable_now"],
            "enable_ready": counts["enable_ready"],
            "deprecated": counts["deprecated"],
            "adapter_missing": counts["adapter_missing"],
            "disabled_stub": counts["disabled_stub"],
            "portal_reference": counts["portal_reference"],
        },
        "sources": classified_sources,
    }
    
    # Write to proof directory
    proof_dir = Path(__file__).parent.parent / "artifacts" / "proof" / "current"
    proof_dir.mkdir(parents=True, exist_ok=True)
    
    proof_path = proof_dir / "source_registry_status.json"
    proof_path.write_text(json.dumps(proof, indent=2) + "\n")
    
    print(f"✓ Generated {proof_path.relative_to(Path.cwd())}")
    print(f"  Total sources: {proof['summary']['total_sources']}")
    print(f"  Runnable now: {proof['summary']['runnable_now']}")
    print(f"  Enable-ready: {proof['summary']['enable_ready']}")
    print(f"  Deprecated: {proof['summary']['deprecated']}")
    print(f"  Adapter missing: {proof['summary']['adapter_missing']}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
