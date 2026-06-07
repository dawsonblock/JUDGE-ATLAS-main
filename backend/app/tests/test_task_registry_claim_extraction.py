from app.orchestration.task_registry import TaskRegistry


def test_extract_claims_task_returns_conservative_claims():
    registry = TaskRegistry()

    result = registry.execute_task(
        "extract_claims",
        None,
        "/tmp/workspace",
        {"text": "A short factual statement. Another sentence."},
    )

    assert result.output["claims_extracted"] == 2
    assert result.output["claims"][0]["authority"] == "derivative_only"
    assert result.output["claims"][0]["claim_type"] == "explicit_text_span"


def test_extract_claims_task_fails_closed_when_extractor_raises(monkeypatch):
    def boom(_text: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.ai.claim_extractor.extract_claims_from_text",
        boom,
    )

    registry = TaskRegistry()

    result = registry.execute_task(
        "extract_claims",
        None,
        "/tmp/workspace",
        {"text": "This should fail."},
    )
    assert result.status.value == "error"
    assert "claim extraction failed" in result.error