"""Use case for reading run status."""

from __future__ import annotations

from application.dto.analysis import (
    RunCoverage,
    RunProgress,
    RunStatusResponse,
    SafeFailure,
)
from domain.exceptions.errors import ValidationError
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.repository import ScanRepositoryPort


class GetRunStatus:
    """Return a simplified view of a run."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store repository dependency."""
        self._repository = repository
        self._logger = logger

    def execute(self, tenant_id: str, run_id: str) -> RunStatusResponse:
        """Load and shape run status data."""
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            self._logger.error("analysis_run.not_found", {"scan_run_id": run_id})
            raise ValidationError("run_id not found")
        self._logger.info(
            "analysis_run.status_read",
            {
                "tenant_id": run.tenant_id,
                "scan_run_id": run.run_id,
                "state": run.state.value,
            },
        )
        return RunStatusResponse(
            run_id=run.run_id,
            state=run.state.value,
            target_url=run.target_url.value,
            progress=RunProgress(
                pages_planned=len(run.pages),
                pages_completed=run.coverage.pages_scanned,
                agent_tasks_planned=0,
                agent_tasks_completed=0,
                findings_count=len(run.findings),
            ),
            coverage=RunCoverage(
                pages_discovered=run.coverage.pages_discovered,
                pages_eligible=run.coverage.pages_eligible,
                pages_scanned=run.coverage.pages_scanned,
            ),
            limitations=tuple(run.summary.get("limitations", [])),
            agent_failures=tuple(run.summary.get("agent_failures", [])),
            failure=(
                SafeFailure(code="RUN_FAILED", message=run.failure_reason)
                if run.failure_reason
                else None
            ),
            created_at=run.created_at.isoformat(),
            updated_at=run.updated_at.isoformat(),
            report_ready=bool(run.artifacts),
        )
