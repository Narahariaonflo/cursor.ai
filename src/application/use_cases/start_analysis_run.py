"""Use case for starting a run."""

from __future__ import annotations

from application.dto.analysis import StartAnalysisRequest
from domain.entities.analysis_run import AnalysisRun
from domain.value_objects.scan import ScanPreferences, TargetUrl
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.repository import ScanRepositoryPort


class StartAnalysisRun:
    """Create and persist a new analysis run."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store dependencies for the use case."""
        self._repository = repository
        self._logger = logger

    def execute(self, request: StartAnalysisRequest) -> AnalysisRun:
        """Accept and persist a new run without performing network work."""
        preferences = ScanPreferences(
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            device_profile=request.device_profile,
            enabled_agents=request.enabled_agents,
            check_external_links=request.check_external_links,
        )
        target_url = TargetUrl(request.target_url)
        run = AnalysisRun(
            tenant_id=request.tenant_id,
            target_url=target_url,
            preferences=preferences,
        )
        self._logger.info(
            "analysis_run.accepted",
            {
                "tenant_id": run.tenant_id,
                "scan_run_id": run.run_id,
                "state": run.state.value,
            },
        )
        self._repository.save_run(run)
        return run
