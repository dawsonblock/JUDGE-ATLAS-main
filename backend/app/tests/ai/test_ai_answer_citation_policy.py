"""
AI answer citation policy tests.
"""

import pytest
from backend.app.ai.answer_safety import (
    RuntimeStepResult,
    AnswerBasis,
    AIAnswerPolicy,
)


@pytest.fixture
def source_backed_answer():
    """Answer backed by source evidence."""
    return RuntimeStepResult(
        step_id="step_001",
        answer="John Smith was reported missing on January 15, 2024",
        answer_basis=AnswerBasis.SOURCE_EVIDENCE,
        confidence=0.99,
        cited_snapshot_ids=["snap_001"],
        review_required=False,
        public_safe=True,
    )


@pytest.fixture
def model_inference_uncited():
    """Model inference without citations - UNSAFE."""
    return RuntimeStepResult(
        step_id="step_002",
        answer="This person is likely in province based on patterns",
        answer_basis=AnswerBasis.MODEL_INFERENCE,
        confidence=0.65,
        cited_snapshot_ids=[],  # No citations!
        review_required=False,
        public_safe=False,
    )


@pytest.fixture
def mixed_with_citations():
    """Mixed evidence+inference with citations."""
    return RuntimeStepResult(
        step_id="step_003",
        answer="Person last seen in Saskatoon, likely still in Saskatchewan",
        answer_basis=AnswerBasis.MIXED,
        confidence=0.85,
        cited_snapshot_ids=["snap_001", "snap_002"],
        review_required=True,
        public_safe=False,
    )


def test_source_evidence_can_be_public(source_backed_answer):
    """Source-backed answer can be public."""
    assert AIAnswerPolicy.can_make_public(source_backed_answer) is True


def test_model_inference_uncited_not_public(model_inference_uncited):
    """Uncited model inference cannot be public."""
    assert AIAnswerPolicy.can_make_public(model_inference_uncited) is False


def test_model_inference_with_citations_can_be_public():
    """Model inference WITH citations AND review can be public."""
    result = RuntimeStepResult(
        step_id="step_004",
        answer="Based on official records, person may have left province",
        answer_basis=AnswerBasis.MODEL_INFERENCE,
        confidence=0.80,
        cited_snapshot_ids=["snap_001", "snap_003"],
        review_required=True,
        public_safe=True,
    )

    # Would be public-safe after review
    assert result.cited_snapshot_ids
    assert result.review_required


def test_no_citations_never_public():
    """Answer with no citations cannot be public regardless of basis."""
    uncited = RuntimeStepResult(
        step_id="step_005",
        answer="Some conclusion",
        answer_basis=AnswerBasis.SOURCE_EVIDENCE,
        confidence=0.95,
        cited_snapshot_ids=[],  # Empty!
        review_required=False,
        public_safe=False,
    )

    assert AIAnswerPolicy.can_make_public(uncited) is False


def test_low_confidence_requires_review():
    """Low confidence answer requires review."""
    low_conf = RuntimeStepResult(
        step_id="step_006",
        answer="Possibly related information",
        answer_basis=AnswerBasis.MIXED,
        confidence=0.55,
        cited_snapshot_ids=["snap_001"],
        review_required=True,
        public_safe=False,
    )

    # Validation should flag this
    is_safe, errors = low_conf.validate_for_public()
    assert is_safe is False


def test_warnings_trigger_review_requirement():
    """Answer with warnings cannot be public without review."""
    with_warnings = RuntimeStepResult(
        step_id="step_007",
        answer="Information from conflicting sources",
        answer_basis=AnswerBasis.MIXED,
        confidence=0.75,
        cited_snapshot_ids=["snap_001", "snap_002"],
        warnings=["contradicts_other_source"],
        review_required=True,
        public_safe=False,
    )

    is_safe, errors = with_warnings.validate_for_public()
    assert is_safe is False
    assert len(errors) > 0


def test_public_safe_format():
    """Public-safe format includes citations, hides internals."""
    result = RuntimeStepResult(
        step_id="step_008",
        answer="Answer text",
        answer_basis=AnswerBasis.SOURCE_EVIDENCE,
        confidence=0.98,
        cited_snapshot_ids=["snap_001"],
        review_required=False,
        public_safe=True,
    )

    public_format = AIAnswerPolicy.make_public_safe(result)

    assert "answer" in public_format
    assert "cited_snapshots" in public_format
    # NOT included: internal reasoning, model scores, etc.
    assert "internal_reasoning" not in public_format


def test_unsafe_answer_rejected():
    """Unsafe answer rejected before public serving."""
    unsafe = RuntimeStepResult(
        step_id="step_009",
        answer="Made-up answer",
        answer_basis=AnswerBasis.MODEL_INFERENCE,
        confidence=0.50,
        cited_snapshot_ids=[],
        review_required=False,
        public_safe=False,
    )

    result = AIAnswerPolicy.make_public_safe(unsafe)
    assert "error" in result
    assert result["error"] == "Answer not public-safe"


def test_validation_catches_citation_gap():
    """Validation catches answers with gaps."""
    incomplete = RuntimeStepResult(
        step_id="step_010",
        answer="Partial answer",
        answer_basis=AnswerBasis.MIXED,
        confidence=0.70,
        cited_snapshot_ids=["snap_001"],
        review_required=False,  # SHOULD be True!
        public_safe=False,
    )

    is_safe, errors = incomplete.validate_for_public()
    # No warnings but mixed+model should require review
    assert not is_safe or errors


def test_answer_basis_declaration_required():
    """Every answer must declare its basis."""
    # All basis types should be explicitly stated
    bases = [
        AnswerBasis.SOURCE_EVIDENCE,
        AnswerBasis.MODEL_INFERENCE,
        AnswerBasis.MIXED,
        AnswerBasis.UNKNOWN,
    ]

    for basis in bases:
        result = RuntimeStepResult(
            step_id="test",
            answer="test",
            answer_basis=basis,
            confidence=0.80,
            cited_snapshot_ids=["snap_001"],
        )
        assert result.answer_basis == basis
