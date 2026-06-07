"""Contract tests for TaskResult and placeholder task semantics.

These tests verify that the task registry enforces the truth discipline
required by the self-verifying alpha release.
"""

from __future__ import annotations

import pytest

from app.core.task_status import TaskExecutionStatus
from app.orchestration.task_registry import TaskRegistry, TaskResult


class TestTaskResultInvariant:
    """TaskResult must enforce truth invariants at construction time."""

    def test_completed_has_success_true(self) -> None:
        result = TaskResult(status=TaskExecutionStatus.COMPLETED, output={"ok": 1})
        assert result.success is True
        assert result.safe_to_rely_on is True
        assert result.executed is True

    def test_not_implemented_has_success_false(self) -> None:
        result = TaskResult(
            status=TaskExecutionStatus.NOT_IMPLEMENTED,
            message="not yet implemented",
        )
        assert result.success is False
        assert result.safe_to_rely_on is False
        assert result.executed is False

    def test_dry_run_has_success_false(self) -> None:
        result = TaskResult(
            status=TaskExecutionStatus.DRY_RUN,
            message="dry run only",
        )
        assert result.success is False
        assert result.safe_to_rely_on is False
        assert result.executed is False

    def test_blocked_has_success_false(self) -> None:
        result = TaskResult(
            status=TaskExecutionStatus.BLOCKED,
            message="blocked by prerequisite",
        )
        assert result.success is False
        assert result.safe_to_rely_on is False

    def test_error_has_success_false(self) -> None:
        result = TaskResult(
            status=TaskExecutionStatus.ERROR,
            error="something went wrong",
        )
        assert result.success is False
        assert result.safe_to_rely_on is False
        assert result.executed is False

    def test_executed_false_cannot_be_success_true(self) -> None:
        with pytest.raises(ValueError, match="executed=False cannot be success=True"):
            TaskResult(
                status=TaskExecutionStatus.COMPLETED,
                executed=False,
            )

    def test_to_dict_contains_status_fields(self) -> None:
        result = TaskResult(
            status=TaskExecutionStatus.NOT_IMPLEMENTED,
            message="test",
        )
        d = result.to_dict()
        assert d["status"] == "not_implemented"
        assert d["success"] is False
        assert d["safe_to_rely_on"] is False
        assert d["executed"] is False
        assert d["message"] == "test"


class TestPlaceholderTasksDoNotReportSuccess:
    """Placeholder task handlers must never claim success."""

    def _registry(self) -> TaskRegistry:
        return TaskRegistry()

    def test_evidence_snapshot_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "evidence_snapshot", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED
        assert result.safe_to_rely_on is False
        assert result.executed is False

    def test_parse_law_xml_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "parse_law_xml", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_parse_court_events_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "parse_court_events", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_parse_police_release_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "parse_police_release", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_resolve_entities_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "resolve_entities", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_geocode_locations_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "geocode_locations", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_dedupe_events_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "dedupe_events", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_contradiction_check_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "contradiction_check", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_confidence_score_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "confidence_score", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_legal_correlation_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "legal_correlation", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_enqueue_review_is_not_success(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "enqueue_review", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED

    def test_publish_map_layer_is_not_success(self) -> None:
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        fake_mod = SimpleNamespace(materialize_all_events=lambda _db: [])
        sys.modules["app.map.materialize_geo_legal_events"] = fake_mod
        try:
            reg = self._registry()
            mock_db = MagicMock()
            result = reg._task_publish_map_layer(
                db=mock_db, workspace_path="/tmp", params={}
            )
        finally:
            sys.modules.pop("app.map.materialize_geo_legal_events", None)
            sys.modules.pop("app.orchestration.task_registry", None)
        assert isinstance(result, TaskResult)
        assert result.success is False
        assert result.status is TaskExecutionStatus.DRY_RUN
        assert result.safe_to_rely_on is False
        assert result.executed is False

    def test_unknown_task_returns_not_implemented(self) -> None:
        reg = self._registry()
        result = reg.execute_task(
            "nonexistent_task", db=None, workspace_path="/tmp", params={}
        )
        assert result.success is False
        assert result.status is TaskExecutionStatus.NOT_IMPLEMENTED
