"""Tests that placeholder / not-yet-implemented tasks do not report success.

Rule: any function that has not yet implemented real side-effects MUST
return a status that is NOT TaskExecutionStatus.COMPLETED.  Returning
'completed', 'executed', or 'success' when no actual work was done is a
documentation lie and a release integrity violation.
"""

from __future__ import annotations

from app.core.task_status import TaskExecutionStatus


class TestTaskExecutionStatusSemantics:
    def test_completed_is_the_only_success_status(self):
        """Only COMPLETED maps to is_success=True."""
        assert TaskExecutionStatus.COMPLETED.is_success is True
        for status in TaskExecutionStatus:
            if status is not TaskExecutionStatus.COMPLETED:
                assert status.is_success is False, (
                    f"{status} must not report is_success=True"
                )

    def test_not_implemented_is_not_safe_to_rely_on(self):
        assert TaskExecutionStatus.NOT_IMPLEMENTED.safe_to_rely_on is False

    def test_dry_run_is_not_safe_to_rely_on(self):
        assert TaskExecutionStatus.DRY_RUN.safe_to_rely_on is False

    def test_blocked_is_not_safe_to_rely_on(self):
        assert TaskExecutionStatus.BLOCKED.safe_to_rely_on is False

    def test_error_is_not_safe_to_rely_on(self):
        assert TaskExecutionStatus.ERROR.safe_to_rely_on is False

    def test_completed_is_safe_to_rely_on(self):
        assert TaskExecutionStatus.COMPLETED.safe_to_rely_on is True

    def test_status_values_are_strings(self):
        """TaskExecutionStatus must be usable as a plain string in JSON."""
        for status in TaskExecutionStatus:
            assert isinstance(status.value, str)

    def test_not_implemented_value(self):
        assert TaskExecutionStatus.NOT_IMPLEMENTED == "not_implemented"

    def test_completed_value(self):
        assert TaskExecutionStatus.COMPLETED == "completed"
