"""FastAPI application entrypoint."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import BackgroundTasks, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from adapters.inbound.ui.home_page import render_home_page
from application.dto.analysis import StartAnalysisRequest
from bootstrap.container import Container
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import AgentKind, DeviceProfile, ReportFormat


class ScanPreferencesPayload(BaseModel):
    """Optional bounded scan preferences."""

    model_config = ConfigDict(extra="forbid")

    max_pages: Optional[int] = Field(default=None, ge=1)
    max_depth: Optional[int] = Field(default=None, ge=0)
    device_profile: Optional[DeviceProfile] = None
    enabled_agents: Optional[List[AgentKind]] = Field(default=None, min_length=1)
    check_external_links: Optional[bool] = None


class CreateRunPayload(BaseModel):
    """Versioned analysis-run creation request."""

    model_config = ConfigDict(extra="forbid")

    target_url: str
    scan_preferences: Optional[ScanPreferencesPayload] = None


def create_app(container: Optional[Container] = None) -> FastAPI:
    """Build the FastAPI app with DI-backed handlers."""
    app = FastAPI(title="AI Website Health Orchestrator")
    dependencies = container or Container.build()

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Map request-shape failures to the approved safe error envelope."""
        del request, exc
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "request validation failed",
                },
            },
        )

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        """Return the minimal report-preview UI."""
        return render_home_page()

    @app.post("/api/v1/analysis-runs", status_code=202, response_model=None)
    def create_run(
        payload: CreateRunPayload,
        background_tasks: BackgroundTasks,
    ) -> Union[Dict[str, object], JSONResponse]:
        """Create a new analysis run and schedule processing."""
        preferences = payload.scan_preferences or ScanPreferencesPayload()
        try:
            run = dependencies.start_analysis_run.execute(
                StartAnalysisRequest(
                    tenant_id=dependencies.settings.development_tenant_id,
                    target_url=payload.target_url,
                    max_pages=preferences.max_pages or dependencies.settings.max_pages,
                    max_depth=(
                        preferences.max_depth
                        if preferences.max_depth is not None
                        else dependencies.settings.max_depth
                    ),
                    device_profile=preferences.device_profile or DeviceProfile.DESKTOP,
                    enabled_agents=(
                        frozenset(preferences.enabled_agents)
                        if preferences.enabled_agents is not None
                        else frozenset(AgentKind)
                    ),
                    check_external_links=(
                        preferences.check_external_links
                        if preferences.check_external_links is not None
                        else True
                    ),
                ),
            )
        except ValidationError as exc:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
            )
        background_tasks.add_task(
            dependencies.process_analysis_run.execute,
            dependencies.settings.development_tenant_id,
            run.run_id,
        )
        return {
            "run_id": run.run_id,
            "state": run.state.value,
            "target_url": run.target_url.value,
            "applied_preferences": {
                "max_pages": run.preferences.max_pages,
                "max_depth": run.preferences.max_depth,
                "device_profile": run.preferences.device_profile.value,
                "enabled_agents": sorted(
                    agent.value for agent in run.preferences.enabled_agents
                ),
                "check_external_links": run.preferences.check_external_links,
            },
            "created_at": run.created_at.isoformat(),
            "links": {"status": f"/api/v1/analysis-runs/{run.run_id}"},
        }

    @app.get("/api/v1/analysis-runs/{run_id}", response_model=None)
    def get_run(run_id: str) -> Union[Dict[str, object], JSONResponse]:
        """Return the current run status."""
        try:
            status = dependencies.get_run_status.execute(
                dependencies.settings.development_tenant_id,
                run_id,
            )
        except ValidationError as exc:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "RUN_NOT_FOUND", "message": str(exc)}},
            )
        response = asdict(status)
        links = {"self": f"/api/v1/analysis-runs/{run_id}"}
        if status.report_ready:
            links.update(
                {
                    "report": f"/api/v1/analysis-runs/{run_id}/report",
                    "html_download": (
                        f"/api/v1/analysis-runs/{run_id}/reports/html"
                    ),
                    "markdown_download": (
                        f"/api/v1/analysis-runs/{run_id}/reports/markdown"
                    ),
                },
            )
        response["links"] = links
        return response

    @app.get("/api/v1/analysis-runs/{run_id}/report", response_model=None)
    def preview_report(run_id: str) -> Union[Dict[str, object], JSONResponse]:
        """Return a JSON report preview for a terminal run."""
        run = dependencies.repository.get_run(
            dependencies.settings.development_tenant_id,
            run_id,
        )
        if run is None or not run.artifacts:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "REPORT_NOT_FOUND", "message": "report not ready"}},
            )
        findings_by_agent: Dict[str, List[Dict[str, object]]] = {}
        for finding in run.findings:
            findings_by_agent.setdefault(finding.category, []).append(
                {
                    "title": finding.title,
                    "severity": finding.severity.value,
                    "description": finding.description,
                    "fingerprint": finding.fingerprint,
                },
            )
        return {
            "run_id": run.run_id,
            "state": run.state.value,
            "target_url": run.target_url.value,
            "narrative": run.summary.get("narrative"),
            "findings_by_agent": findings_by_agent,
            "limitations": run.summary.get("limitations", []),
            "links": {
                "html_download": f"/api/v1/analysis-runs/{run_id}/reports/html",
                "markdown_download": (
                    f"/api/v1/analysis-runs/{run_id}/reports/markdown"
                ),
            },
        }

    @app.get("/api/v1/analysis-runs/{run_id}/reports/{report_format}", response_model=None)
    def download_report(
        run_id: str,
        report_format: ReportFormat,
    ) -> Union[FileResponse, JSONResponse]:
        """Download an immutable HTML or Markdown report artifact."""
        run = dependencies.repository.get_run(
            dependencies.settings.development_tenant_id,
            run_id,
        )
        if run is None:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "RUN_NOT_FOUND", "message": "run not found"}},
            )
        artifact = next(
            (item for item in run.artifacts if item.format is report_format),
            None,
        )
        if artifact is None:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "REPORT_NOT_FOUND", "message": "report missing"}},
            )
        path = Path(artifact.storage_ref)
        if not path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "REPORT_NOT_FOUND", "message": "report missing"}},
            )
        media = "text/html" if report_format is ReportFormat.HTML else "text/markdown"
        return FileResponse(path, media_type=media, filename=path.name)

    return app


app = create_app()
