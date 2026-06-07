"""
Strict source registry classification.

Uses exact automation_status + lifecycle_state rules to avoid contradictions
in proof artifacts.
"""

from typing import List, Dict, Any


def classify_source(source: Dict[str, Any]) -> str:
    """
    Classify a single source using strict rules.
    
    Rules:
      runnable_now: automation_status == "machine_ready_enabled" AND lifecycle_state == "runnable"
      enable_ready: automation_status == "machine_ready_disabled" AND lifecycle_state == "runnable_disabled"
      deprecated: lifecycle_state == "deprecated"
      adapter_missing: automation_status == "adapter_missing"
      disabled_stub: lifecycle_state == "disabled_stub"
      portal_reference: automation_status == "portal_reference" OR lifecycle_state == "portal_reference"
      other: anything else
    
    Returns: One of the above classification strings.
    """
    automation_status = source.get("automation_status", "")
    lifecycle_state = source.get("lifecycle_state", "")
    
    # Rule 1: Runnable NOW
    if (
        automation_status == "machine_ready_enabled"
        and lifecycle_state == "runnable"
    ):
        return "runnable_now"
    
    # Rule 2: Enable-ready (disabled but runnable when enabled)
    if (
        automation_status == "machine_ready_disabled"
        and lifecycle_state == "runnable_disabled"
    ):
        return "enable_ready"
    
    # Rule 3: Deprecated
    if lifecycle_state == "deprecated":
        return "deprecated"
    
    # Rule 4: Adapter missing
    if automation_status == "adapter_missing":
        return "adapter_missing"
    
    # Rule 5: Disabled stub
    if lifecycle_state == "disabled_stub":
        return "disabled_stub"
    
    # Rule 6: Portal reference (manual, not automated)
    if (
        automation_status == "portal_reference"
        or lifecycle_state == "portal_reference"
    ):
        return "portal_reference"
    
    # Default
    return "other"


def count_sources_by_status(sources: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count all sources by classification.
    
    Returns: dict with keys from classify_source() and counts as values.
    """
    counts = {
        "runnable_now": 0,
        "enable_ready": 0,
        "deprecated": 0,
        "adapter_missing": 0,
        "disabled_stub": 0,
        "portal_reference": 0,
        "other": 0,
    }
    
    for source in sources:
        classification = classify_source(source)
        counts[classification] += 1
    
    return counts


def expected_metrics() -> Dict[str, int]:
    """
    Return the expected correct metrics based on current YAML.
    
    From canada_saskatchewan_sources.yaml:
    - justice_canada_laws_xml: machine_ready_enabled + runnable → runnable_now
    - sk_courts_qb_decisions: machine_ready_enabled + runnable → runnable_now
    - sk_courts_ca_decisions: machine_ready_enabled + runnable → runnable_now
    - scc_decisions: machine_ready_enabled + runnable → runnable_now
    - federal_court_canada: machine_ready_enabled + runnable → runnable_now
    - sk_legislature_hansard: machine_ready_enabled + runnable → runnable_now
    - saskatoon_open_data_public_safety: machine_ready_enabled + runnable → runnable_now
    - sk_court_of_appeal: machine_ready_enabled + runnable → runnable_now
    Total runnable_now: 8
    
    - web_monitor_saskatoon_police_news: machine_ready_disabled + runnable_disabled → enable_ready
    - sk_justice_ministry: machine_ready_disabled + runnable_disabled → enable_ready
    - rcmp_sk_news: machine_ready_disabled + runnable_disabled → enable_ready
    Total enable_ready: 3
    
    - scc_judgments: deprecated
    - federal_court_canada_decisions: deprecated
    - canlii_sk: deprecated
    Total deprecated: 3
    
    - justice_canada_laws_pit_xml: adapter_missing
    - and 12 more with adapter_missing
    Total adapter_missing: 13
    
    - canada_justice_laws: deprecated (via deprecation policy)
    - and others: various
    
    Total sources: 27
    """
    return {
        "total_sources": 27,
        "machine_ingest_sources": 12,  # The ones with machine_ingest
        "runnable_now": 8,
        "enable_ready": 3,
        "deprecated": 3,
        "adapter_missing": 13,
        "disabled_stub": 0,  # None currently
        "portal_reference": 0,  # None currently
    }
