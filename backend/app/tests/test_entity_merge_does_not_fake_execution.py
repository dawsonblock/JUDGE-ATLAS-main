"""Tests that execute_approved_merge does NOT claim to have executed a merge.

The graph merge pathway is not yet implemented.  The function MUST return
a status that clearly communicates non-completion so that callers and
operators are never misled into believing a merge happened.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.task_status import TaskExecutionStatus
from app.graph.entity_resolution_safety import execute_approved_merge


class TestExecuteApprovedMergeHonesty:
    def _make_db(self):
        return MagicMock()

    def _make_entities(self, confidence: float = 0.97):
        entity_1 = MagicMock()
        entity_1.id = 1
        entity_1.name = "Entity A"
        entity_1.entity_type = "person"
        entity_1.source_ids = [10]
        entity_1.confidence_score = confidence
        entity_1.merge_count = 0
        entity_1.is_canonical = True
        entity_1.jurisdiction = None

        entity_2 = MagicMock()
        entity_2.id = 2
        entity_2.name = "Entity B"
        entity_2.entity_type = "person"
        entity_2.source_ids = [20]
        entity_2.confidence_score = confidence
        entity_2.merge_count = 0
        entity_2.is_canonical = True
        entity_2.jurisdiction = None

        return entity_1, entity_2

    def _run_merge(self, confidence: float = 0.97):
        db = self._make_db()
        entity_1, entity_2 = self._make_entities(confidence)
        db.query.return_value.filter.return_value.first.side_effect = [
            entity_1,
            entity_2,
        ]
        with patch(
            "app.graph.entity_resolution_safety.propose_entity_merge",
            return_value={
                "confidence": confidence,
                "shared_sources": [],
                "name_similarity": 0.99,
                "type_match": True,
            },
        ):
            return execute_approved_merge(
                entity_id_1=1,
                entity_id_2=2,
                approved_by="test_operator",
                db=db,
            )

    def test_status_is_not_executed(self):
        """Must NOT return status='executed'."""
        result = self._run_merge()
        assert result.get("status") != "executed", (
            "execute_approved_merge returned status='executed' but the graph "
            "merge is not implemented.  Use TaskExecutionStatus.NOT_IMPLEMENTED."
        )

    def test_status_is_not_completed(self):
        """Must NOT return status='completed'."""
        result = self._run_merge()
        status = result.get("status")
        assert status != TaskExecutionStatus.COMPLETED, (
            f"execute_approved_merge returned {status!r} — must not claim completion"
        )
        assert status != "completed"

    def test_executed_flag_is_false(self):
        """The 'executed' boolean flag must be False."""
        result = self._run_merge()
        assert result.get("executed") is False, (
            f"execute_approved_merge returned executed={result.get('executed')!r}, "
            "expected False because no graph merge was performed."
        )

    def test_safe_to_rely_on_is_false(self):
        """safe_to_rely_on must be False for an unimplemented operation."""
        result = self._run_merge()
        assert result.get("safe_to_rely_on") is False

    def test_status_is_not_implemented(self):
        """Status must be TaskExecutionStatus.NOT_IMPLEMENTED."""
        result = self._run_merge()
        assert result.get("status") == TaskExecutionStatus.NOT_IMPLEMENTED

    def test_message_indicates_not_implemented(self):
        """Message must communicate that the merge was not performed."""
        result = self._run_merge()
        message = result.get("message", "").lower()
        assert any(
            phrase in message
            for phrase in ("not yet implemented", "not implemented", "no merge was performed")
        ), f"Message does not indicate not-implemented: {result.get('message')!r}"
