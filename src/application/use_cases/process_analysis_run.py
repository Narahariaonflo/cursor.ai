"""Drive a run from acceptance through aggregation and report publication."""

from __future__ import annotations

import asyncio
from typing import Dict

from application.agents.contracts import PageEvidenceRef
from application.evidence.browser_evidence_collector import BrowserEvidenceCollector
from application.orchestration.agent_execution_coordinator import (
    AgentExecutionCoordinator,
)
from application.orchestration.finding_aggregation import FindingAggregationService
from application.services.assistive_narrative import AssistiveNarrativeService
from application.use_cases.plan_analysis_run import PlanAnalysisRun
from application.use_cases.publish_run_report import PublishRunReport
from application.use_cases.validate_analysis_run import ValidateAnalysisRun
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import RunState
from domain.value_objects.operational import CoverageStats
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.repository import ScanRepositoryPort


class ProcessAnalysisRun:
    """Execute the approved post-accept lifecycle for one analysis run."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        validate_analysis_run: ValidateAnalysisRun,
        plan_analysis_run: PlanAnalysisRun,
        browser_evidence_collector: BrowserEvidenceCollector,
        agent_execution_coordinator: AgentExecutionCoordinator,
        finding_aggregation: FindingAggregationService,
        assistive_narrative: AssistiveNarrativeService,
        publish_run_report: PublishRunReport,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store orchestration dependencies."""
        self._repository = repository
        self._validate = validate_analysis_run
        self._plan = plan_analysis_run
        self._browser_evidence_collector = browser_evidence_collector
        self._coordinator = agent_execution_coordinator
        self._aggregation = finding_aggregation
        self._narrative = assistive_narrative
        self._publish = publish_run_report
        self._logger = logger

    def execute(self, tenant_id: str, run_id: str) -> None:
        """Synchronously process one run through report publication."""
        asyncio.run(self._execute_async(tenant_id, run_id))

    async def _execute_async(self, tenant_id: str, run_id: str) -> None:
        """Validate, plan, analyze, aggregate, and publish one run."""
        self._validate.execute(tenant_id, run_id)
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            raise ValidationError("run_id not found")
        if run.state is RunState.FAILED:
            return

        self._plan.execute(tenant_id, run_id)
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            raise ValidationError("run_id not found")
        run.transition_to(RunState.RUNNING)
        self._repository.save_run(run)

        evidence_by_url: Dict[str, PageEvidenceRef] = {}
        limitations = list(run.summary.get("limitations", []))
        for page in run.pages:
            try:
                captured = await self._browser_evidence_collector.collect(
                    tenant_id=tenant_id,
                    run_id=run_id,
                    page_url=page.url,
                    device_profile=run.preferences.device_profile,
                    capture_screenshot=True,
                )
                evidence_by_url[page.url] = PageEvidenceRef(
                    page_url=page.url,
                    dom_summary=captured.dom_summary,
                    console_events=captured.console_events,
                    network_events=captured.network_events,
                    discovered_links=captured.discovered_links,
                    screenshot_ref=captured.screenshot_ref,
                )
                if captured.screenshot_ref is None:
                    limitations.append("SCREENSHOT_GAP")
            except ValidationError:
                limitations.append(f"BROWSER_EVIDENCE_GAP:{page.url}")
                evidence_by_url[page.url] = PageEvidenceRef(
                    page_url=page.url,
                    dom_summary="",
                )

        results = await self._coordinator.execute(
            tenant_id=tenant_id,
            run_id=run_id,
            pages=run.pages,
            preferences=run.preferences,
            evidence_by_url=evidence_by_url,
        )
        aggregated = self._aggregation.aggregate(results)
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            raise ValidationError("run_id not found")
        run.add_findings(list(aggregated.findings))
        run.coverage = CoverageStats(
            pages_discovered=run.coverage.pages_discovered,
            pages_eligible=run.coverage.pages_eligible,
            pages_planned=run.coverage.pages_planned,
            pages_scanned=len(evidence_by_url),
        )
        all_limitations = sorted(
            set(limitations)
            | set(aggregated.limitations)
            | set(run.summary.get("limitations", [])),
        )
        run.summary = {
            **run.summary,
            "limitations": all_limitations,
            "agent_failures": list(aggregated.agent_failures),
            "narrative": self._narrative.compose(
                aggregated.findings,
                all_limitations,
            ),
        }
        if aggregated.agent_failures or all_limitations:
            run.failure_reason = "partial analysis due to agent or coverage limitations"
        run.transition_to(RunState.AGGREGATING)
        self._repository.save_run(run)
        self._publish.execute(tenant_id, run_id)
        self._logger.info(
            "analysis_run.processed",
            {"tenant_id": tenant_id, "scan_run_id": run_id},
        )
