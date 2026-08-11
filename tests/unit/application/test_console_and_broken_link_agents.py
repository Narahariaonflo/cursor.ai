"""Unit tests for console and broken-link agents."""

from application.agent_services.broken_link_agent import BrokenLinkAgentService
from application.agent_services.console_agent import ConsoleAgentService
from application.agents.contracts import AgentTask, PageEvidenceRef
from domain.entities.analysis_run import PageTarget
from domain.value_objects.enums import AgentKind
from domain.value_objects.scan import ScanPreferences
from ports.outbound.results import LinkCheckResult


class FakeLinkCheck:
    """Return deterministic link statuses."""

    def check(self, source_url: str, target_url: str) -> LinkCheckResult:
        """Return a broken external link status."""
        return LinkCheckResult(
            source_url=source_url,
            target_url=target_url,
            status_code=404,
            redirect_chain=(target_url,),
        )


def test_console_agent_maps_error_events() -> None:
    """Console errors should become evidence-backed findings."""
    result = ConsoleAgentService().execute(
        AgentTask(
            run_id="run",
            tenant_id="tenant",
            agent_name=AgentKind.CONSOLE,
            page_target=PageTarget("https://example.com/", 0),
            scan_preferences=ScanPreferences(1, 0),
            page_evidence=PageEvidenceRef(
                page_url="https://example.com/",
                dom_summary="<html></html>",
                console_events=("error: boom", "log: ok"),
            ),
        ),
    )
    assert len(result.findings) == 1
    assert "boom" in result.findings[0].evidence[0].summary


def test_broken_link_agent_can_disable_external_checks() -> None:
    """Disabling external checks should record a coverage limitation warning."""
    preferences = ScanPreferences(
        max_pages=1,
        max_depth=0,
        check_external_links=False,
    )
    result = BrokenLinkAgentService(FakeLinkCheck()).execute(
        AgentTask(
            run_id="run",
            tenant_id="tenant",
            agent_name=AgentKind.BROKEN_LINK,
            page_target=PageTarget("https://example.com/", 0),
            scan_preferences=preferences,
            page_evidence=PageEvidenceRef(
                page_url="https://example.com/",
                dom_summary="<html></html>",
                discovered_links=("https://other.example/404",),
            ),
        ),
    )
    assert result.findings == ()
    assert "EXTERNAL_LINK_VALIDATION_DISABLED" in result.warnings
