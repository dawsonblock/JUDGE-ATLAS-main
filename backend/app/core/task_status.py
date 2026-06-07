"""Canonical task execution status enum.

Any placeholder or deferred task MUST use this enum to communicate its
state.  Callers MUST NOT return status="completed" or status="executed"
for logic that has not actually run.

Allowed transitions::

    NOT_IMPLEMENTED → DRY_RUN → COMPLETED
    NOT_IMPLEMENTED → BLOCKED
    NOT_IMPLEMENTED → ERROR
    DRY_RUN → COMPLETED
    DRY_RUN → BLOCKED
"""

from __future__ import annotations

from enum import Enum


class TaskExecutionStatus(str, Enum):
    """Canonical execution status for tasks that may be stub/placeholder."""

    COMPLETED = "completed"
    """Task ran successfully and produced real side-effects."""

    DRY_RUN = "dry_run"
    """Task ran in simulation mode — no persistent side-effects were written."""

    NOT_IMPLEMENTED = "not_implemented"
    """Task logic is a stub.  Callers must not treat this as success."""

    BLOCKED = "blocked"
    """Task is gated on a prerequisite that has not been satisfied."""

    ERROR = "error"
    """Task encountered an unrecoverable error."""

    @property
    def is_success(self) -> bool:
        """True only when the task produced real, committed side-effects."""
        return self is TaskExecutionStatus.COMPLETED

    @property
    def safe_to_rely_on(self) -> bool:
        """True when callers may act on the result as authoritative."""
        return self is TaskExecutionStatus.COMPLETED
