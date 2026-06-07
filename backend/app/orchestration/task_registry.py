"""Task registry for registering safe Python task implementations.

This module registers safe Python task implementations for each allowed workflow
step type. All tasks call existing Judge AtlasX systems (evidence snapshot, claim
extraction, contradiction engine, confidence engine). No arbitrary shell execution
is allowed - all tasks are registered Python functions.
"""
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.task_status import TaskExecutionStatus

logger = logging.getLogger(__name__)

# Security constraints
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
ALLOWED_URL_SCHEMES = {"https"}
ALLOWED_URL_DOMAINS = {
    "laws-lois.justice.gc.ca",
    "justice.gc.ca",
    "canada.ca",
}  # Add more as needed


def _validate_url(url: str) -> None:
    """Validate that a URL is safe to fetch.
    
    Args:
        url: URL to validate
        
    Raises:
        ValueError: If URL is invalid or not from allowed domain
    """
    parsed = urlparse(url)
    
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"URL scheme '{parsed.scheme}' not allowed. Allowed: {ALLOWED_URL_SCHEMES}")
    
    if parsed.netloc not in ALLOWED_URL_DOMAINS:
        raise ValueError(f"URL domain '{parsed.netloc}' not in allowlist. Allowed: {ALLOWED_URL_DOMAINS}")


def _validate_workspace_path(workspace_path: str, base_dir: Path) -> Path:
    """Validate and sanitize workspace path to prevent path traversal.
    
    Args:
        workspace_path: User-provided workspace path
        base_dir: Base directory that workspace must be within
        
    Returns:
        Resolved, validated Path object
        
    Raises:
        ValueError: If path attempts to traverse outside base directory
    """
    resolved = Path(workspace_path).resolve()
    base_resolved = base_dir.resolve()
    
    # Check that resolved path is within base directory
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Workspace path '{workspace_path}' resolves outside base directory '{base_dir}'")
    
    return resolved


def _resolve_workspace_relative_path(workspace_path: str, relative_path: str) -> Path:
    """Resolve a task-supplied path within the workspace root.

    The returned path is guaranteed to stay inside the resolved workspace root
    even if the user supplies a traversal segment or a symlink escape.
    """
    cleaned = (relative_path or "").strip()
    if not cleaned:
        raise ValueError("Path must not be empty")

    if Path(cleaned).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", cleaned):
        raise ValueError(f"Path '{relative_path}' must be relative to the workspace")

    workspace_root = Path(workspace_path).resolve()
    resolved = (workspace_root / cleaned).resolve()
    try:
        resolved.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(
            f"Path '{relative_path}' resolves outside workspace '{workspace_path}'"
        ) from exc
    return resolved


class TaskResult:
    """Result of a task execution."""

    def __init__(
        self,
        status: TaskExecutionStatus,
        output: Dict[str, Any] | None = None,
        error: str | None = None,
        message: str = "",
        executed: bool | None = None,
        metadata: Dict[str, Any] | None = None,
    ):
        self.status = status
        self.success = status is TaskExecutionStatus.COMPLETED
        self.safe_to_rely_on = status.safe_to_rely_on
        self.executed = self.success if executed is None else executed
        if self.executed is False and self.success:
            raise ValueError("executed=False cannot be success=True")
        self.output = output or {}
        self.error = error
        self.message = message
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "status": self.status.value,
            "safe_to_rely_on": self.safe_to_rely_on,
            "executed": self.executed,
            "output": self.output,
            "error": self.error,
            "message": self.message,
            "metadata": self.metadata,
        }


class TaskRegistry:
    """Registry for safe task implementations."""

    def __init__(self):
        self.tasks: Dict[str, Callable] = {}
        self._register_default_tasks()

    def register(self, task_type: str, task_func: Callable) -> None:
        """Register a task implementation for a task type."""
        self.tasks[task_type] = task_func
        logger.info(f"Registered task: {task_type}")

    def get_task(self, task_type: str) -> Callable | None:
        """Get a task implementation by type."""
        return self.tasks.get(task_type)

    def _completed(self, output: Dict[str, Any], message: str = "") -> TaskResult:
        return TaskResult(
            status=TaskExecutionStatus.COMPLETED,
            output=output,
            message=message,
            executed=True,
        )

    def _not_implemented(self, message: str) -> TaskResult:
        return TaskResult(
            status=TaskExecutionStatus.NOT_IMPLEMENTED,
            output={},
            message=message,
            executed=False,
        )

    def execute_task(
        self,
        task_type: str,
        db: Session,
        workspace_path: str,
        params: Dict[str, Any],
    ) -> TaskResult:
        """Execute a task by type with given parameters."""
        task_func = self.get_task(task_type)
        if not task_func:
            return TaskResult(
                status=TaskExecutionStatus.NOT_IMPLEMENTED,
                error=f"Unknown task type: {task_type}",
                message=f"Unknown task type: {task_type}",
                executed=False,
            )

        try:
            output = task_func(db, workspace_path, params)
            if isinstance(output, TaskResult):
                return output
            return self._completed(output=output)
        except Exception as e:
            logger.error(f"Task {task_type} failed: {e}", exc_info=True)
            return TaskResult(
                status=TaskExecutionStatus.ERROR,
                error=str(e),
                message=str(e),
                executed=False,
            )

    def _register_default_tasks(self) -> None:
        """Register default safe task implementations."""
        self.register("fetch_url", self._task_fetch_url)
        self.register("fetch_api", self._task_fetch_api)
        self.register("evidence_snapshot", self._task_evidence_snapshot)
        self.register("parse_law_xml", self._task_parse_law_xml)
        self.register("parse_court_events", self._task_parse_court_events)
        self.register("parse_police_release", self._task_parse_police_release)
        self.register("extract_claims", self._task_extract_claims)
        self.register("resolve_entities", self._task_resolve_entities)
        self.register("geocode_locations", self._task_geocode_locations)
        self.register("dedupe_events", self._task_dedupe_events)
        self.register("contradiction_check", self._task_contradiction_check)
        self.register("confidence_score", self._task_confidence_score)
        self.register("legal_correlation", self._task_legal_correlation)
        self.register("enqueue_review", self._task_enqueue_review)
        self.register("publish_map_layer", self._task_publish_map_layer)

    # Task implementations

    def _task_fetch_url(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Fetch data from a URL and save to workspace."""
        import httpx

        url = params.get("url")
        if not url:
            raise ValueError("fetch_url requires 'url' parameter")

        # Validate URL
        _validate_url(url)

        headers = params.get("headers", {})
        timeout = params.get("timeout_seconds", 300)
        output_relative_path = params.get("output_path", "raw/fetched_data.xml")

        output_path = _resolve_workspace_relative_path(
            workspace_path, output_relative_path
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            # Check file size
            content_length = len(response.content)
            if content_length > MAX_FILE_SIZE_BYTES:
                raise ValueError(f"File size {content_length} bytes exceeds maximum {MAX_FILE_SIZE_BYTES} bytes")
            
            output_path.write_bytes(response.content)

        return self._completed({
            "output_path": str(output_path),
            "content_length": content_length,
            "status_code": response.status_code,
        })

    def _task_fetch_api(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Fetch data from an API endpoint and save to workspace."""
        import httpx

        url = params.get("url")
        if not url:
            raise ValueError("fetch_api requires 'url' parameter")

        # Validate URL
        _validate_url(url)

        headers = params.get("headers", {})
        timeout = params.get("timeout_seconds", 300)
        output_relative_path = params.get("output_path", "raw/api_response.json")

        output_path = _resolve_workspace_relative_path(
            workspace_path, output_relative_path
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            
            # Check response size
            content_length = len(response.content)
            if content_length > MAX_FILE_SIZE_BYTES:
                raise ValueError(f"Response size {content_length} bytes exceeds maximum {MAX_FILE_SIZE_BYTES} bytes")
            
            output_path.write_bytes(response.content)

        return self._completed({
            "output_path": str(output_path),
            "status_code": response.status_code,
        })

    def _task_evidence_snapshot(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Create an evidence snapshot from fetched data."""
        return self._not_implemented(
            "Evidence snapshot creation is not implemented in this build."
        )

    def _task_parse_law_xml(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Parse law XML data into structured format."""
        return self._not_implemented(
            "Law XML parsing is not implemented in this build."
        )

    def _task_parse_court_events(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Parse court event data."""
        return self._not_implemented(
            "Court event parsing is not implemented in this build."
        )

    def _task_parse_police_release(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Parse police release data."""
        return self._not_implemented(
            "Police release parsing is not implemented in this build."
        )

    def _task_extract_claims(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Extract claims from parsed data using AI."""
        from app.ai.claim_extractor import extract_claims_from_text

        claim_types = params.get("claim_types", [])
        confidence_threshold = params.get("confidence_threshold", 0.7)
        text = (
            params.get("text")
            or params.get("source_text")
            or params.get("input_text")
            or ""
        )

        try:
            claims = extract_claims_from_text(text)
        except Exception as exc:
            raise ValueError(f"claim extraction failed: {exc}") from exc

        if not isinstance(claims, list):
            raise ValueError("claim extraction failed: extractor returned non-list output")

        return self._completed({
            "claim_types": claim_types,
            "confidence_threshold": confidence_threshold,
            "claims": claims,
            "claims_extracted": len(claims),
        })

    def _task_resolve_entities(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Resolve and deduplicate legal entities."""
        return self._not_implemented(
            "Entity resolution is not implemented in this build."
        )

    def _task_geocode_locations(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Geocode location references."""
        return self._not_implemented(
            "Location geocoding is not implemented in this build."
        )

    def _task_dedupe_events(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Deduplicate events based on configured fields."""
        return self._not_implemented(
            "Event deduplication is not implemented in this build."
        )

    def _task_contradiction_check(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Check for contradictions using the contradiction engine."""
        return self._not_implemented(
            "Contradiction checking is not implemented in this build."
        )

    def _task_confidence_score(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Score confidence of claims using the confidence engine."""
        return self._not_implemented(
            "Confidence scoring is not implemented in this build."
        )

    def _task_legal_correlation(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Run legal correlation analysis."""
        return self._not_implemented(
            "Legal correlation analysis is not implemented in this build."
        )

    def _task_enqueue_review(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> Any:
        """Enqueue items for review."""
        return self._not_implemented(
            "Review enqueueing is not implemented in this build."
        )

    def _task_publish_map_layer(
        self, db: Session, workspace_path: str, params: Dict[str, Any]
    ) -> TaskResult:
        """Read-only preview of map layer data; does not publish externally."""
        from app.map.materialize_geo_legal_events import materialize_all_events

        layer_type = params.get("layer_type", "default")
        publish_status = params.get("publish_status", "public_safe")
        require_approval = params.get("require_approval", True)

        events = materialize_all_events(db)
        return TaskResult(
            status=TaskExecutionStatus.DRY_RUN,
            output={
                "layer_type": layer_type,
                "publish_status": publish_status,
                "require_approval": require_approval,
                "events_previewed": len(events),
            },
            message=(
                "Map layer materialization is a dry-run preview only; "
                "no external publish occurred."
            ),
            executed=False,
        )


# Global task registry instance
task_registry = TaskRegistry()
