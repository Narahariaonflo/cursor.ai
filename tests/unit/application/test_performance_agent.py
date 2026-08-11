"""Unit tests for performance agent defaults and thresholds."""

from application.agent_services.performance_agent import PerformanceAgentService
from application.agents.contracts import AgentTask
from domain.entities.analysis_run import PageTarget
from domain.value_objects.enums import AgentKind, AgentTaskStatus
from domain.value_objects.scan import ScanPreferences
from ports.outbound.results import LighthouseAuditResult


class FakeLighthouse:
    """Return fixture Lighthouse metrics."""

    def run_audit(self, url: str) -> LighthouseAuditResult:
        """Return a threshold-breaching LCP metric."""
        return LighthouseAuditResult(
            page_url=url,
            metrics={"largest_contentful_paint": 4000},
            artifact_ref="memory://lighthouse",
        )


def test_performance_agent_flags_threshold_and_keeps_psi_off() -> None:
    """PSI remains disabled by default while Lighthouse breaches are reported."""
    agent = PerformanceAgentService(
        lighthouse=FakeLighthouse(),
        thresholds={"largest_contentful_paint": 2500},
        psi_enabled=False,
    )
    result = agent.execute(
        AgentTask(
            run_id="run-a",
            tenant_id="tenant-a",
            agent_name=AgentKind.PERFORMANCE,
            page_target=PageTarget(url="https://example.com/", depth=0),
            scan_preferences=ScanPreferences(1, 0),
        ),
    )

    assert result.status is AgentTaskStatus.SUCCEEDED
    assert len(result.findings) == 1
    assert result.warnings == ("PSI_DISABLED_BY_DEFAULT",)
    assert result.artifacts == ("memory://lighthouse",)
