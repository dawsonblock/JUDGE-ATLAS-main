"""
AI answer safety - require citations and review before public use.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AnswerBasis(str, Enum):
    """Source of answer content."""
    SOURCE_EVIDENCE = "source_evidence"
    MODEL_INFERENCE = "model_inference"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class RuntimeStepResult(BaseModel):
    """
    Result from a single AI reasoning step.
    
    Every answer must declare:
    - answer_basis: what this is based on
    - confidence: numerical confidence
    - warnings: any issues found
    - cited_snapshot_ids: which evidence this cites
    - review_required: whether human review is needed
    - public_safe: whether this can be shown to public users
    """
    step_id: str
    answer: Optional[str] = None
    answer_basis: AnswerBasis
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    cited_snapshot_ids: List[str] = Field(default_factory=list)
    review_required: bool = False
    public_safe: bool = False

    def validate_for_public(self) -> tuple[bool, List[str]]:
        """
        Check if this step result can be publicly shown.
        
        Returns: (is_public_safe, error_messages)
        """
        errors = []

        # Inference without sources cannot be public
        if self.answer_basis == AnswerBasis.MODEL_INFERENCE:
            if not self.cited_snapshot_ids:
                errors.append("Model inference without citations cannot be public")
                return False, errors

        # No citations = not public
        if not self.cited_snapshot_ids:
            errors.append("No cited sources - cannot be public")
            return False, errors

        # Low confidence requires review
        if self.confidence < 0.7:
            if not self.review_required:
                errors.append("Low confidence answer requires review before public")
            return False, errors

        # Any warnings require review
        if self.warnings:
            if not self.review_required:
                errors.append("Warnings present - requires review before public")
            return False, errors

        return True, []


class AIAnswerPolicy:
    """
    Policy: No AI answer can become public without:
    1. Explicit citations to evidence snapshots
    2. Human review
    3. Safe confidence level
    """

    @staticmethod
    def can_make_public(result: RuntimeStepResult) -> bool:
        """
        Determine if AI answer can be shown to public users.
        
        Hard rule: Answer must be reviewed and cited.
        """
        # Model inference MUST have sources
        if result.answer_basis == AnswerBasis.MODEL_INFERENCE:
            if not result.cited_snapshot_ids:
                return False
            if not result.review_required:
                return False

        # ANY inference must have citations
        if not result.cited_snapshot_ids:
            return False

        # Must pass validation
        is_safe, _ = result.validate_for_public()
        return is_safe

    @staticmethod
    def make_public_safe(result: RuntimeStepResult) -> dict:
        """
        Convert AI answer to public-safe format.
        
        Includes citations, filters raw model output.
        """
        if not AIAnswerPolicy.can_make_public(result):
            return {
                "error": "Answer not public-safe",
                "reason": "requires review or citations missing",
            }

        return {
            "answer": result.answer,
            "answer_basis": result.answer_basis.value,
            "confidence": result.confidence,
            "cited_snapshots": result.cited_snapshot_ids,
            "warnings": result.warnings,
            # NOT included:
            # - internal reasoning
            # - model scores
            # - debug info
        }
