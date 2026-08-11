"""Use case for report publication."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Tuple
from urllib.parse import urlparse
from uuid import uuid4

from domain.entities.analysis_run import ReportArtifact
from domain.exceptions.errors import ValidationError
from domain.services.reporting import summarize_findings
from domain.value_objects.enums import ReportFormat, RunState
from ports.outbound.artifact_store import ArtifactStorePort
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.report_renderer import ReportRendererPort
from ports.outbound.repository import ScanRepositoryPort


class PublishRunReport:
    """Render and persist a report for a run."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        artifact_store: ArtifactStorePort,
        report_renderer: ReportRendererPort,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store dependencies for report publication."""
        self._repository = repository
        self._artifact_store = artifact_store
        self._report_renderer = report_renderer
        self._logger = logger

    def execute(self, tenant_id: str, run_id: str) -> Tuple[str, str]:
        """Create Markdown and HTML report artifacts for an aggregated run."""
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            self._logger.error("analysis_run.not_found", {"scan_run_id": run_id})
            raise ValidationError("run_id not found")
        if run.state is not RunState.AGGREGATING:
            raise ValidationError("run must be in AGGREGATING state")

        run.summary = {
            **run.summary,
            **summarize_findings(run.findings),
        }
        run.transition_to(RunState.RENDERING)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        domain_name = urlparse(run.target_url.value).netloc.replace(":", "_")
        base_name = f"website-health-report_{domain_name}_{timestamp}"

        markdown = self._report_renderer.render_markdown(run)
        html = self._report_renderer.render_html(run)
        markdown_ref = self._artifact_store.save_text(f"{base_name}.md", markdown)
        html_ref = self._artifact_store.save_text(f"{base_name}.html", html)
        run.add_artifact(
            ReportArtifact(
                artifact_id=str(uuid4()),
                run_id=run.run_id,
                format=ReportFormat.MARKDOWN,
                storage_ref=markdown_ref,
                checksum=sha256(markdown.encode("utf-8")).hexdigest(),
            ),
        )
        run.add_artifact(
            ReportArtifact(
                artifact_id=str(uuid4()),
                run_id=run.run_id,
                format=ReportFormat.HTML,
                storage_ref=html_ref,
                checksum=sha256(html.encode("utf-8")).hexdigest(),
            ),
        )
        run.finalize()
        self._repository.save_run(run)
        self._logger.info(
            "analysis_run.report_published",
            {
                "scan_run_id": run.run_id,
                "tenant_id": run.tenant_id,
                "state": run.state.value,
                "report_formats": ["html", "markdown"],
            },
        )
        return markdown_ref, html_ref
