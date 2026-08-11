"""Unit tests for the SEO agent."""

from application.agent_services.seo_agent import SeoAgentService
from application.agents.contracts import AgentTask, PageEvidenceRef
from domain.entities.analysis_run import PageTarget
from domain.value_objects.enums import AgentKind
from domain.value_objects.scan import ScanPreferences


def test_seo_agent_reports_missing_title_and_canonical() -> None:
    """Missing title/canonical signals should create evidence-backed findings."""
    task = AgentTask(
        run_id="run-a",
        tenant_id="tenant-a",
        agent_name=AgentKind.SEO,
        page_target=PageTarget(url="https://example.com/", depth=0),
        scan_preferences=ScanPreferences(max_pages=1, max_depth=0),
        page_evidence=PageEvidenceRef(
            page_url="https://example.com/",
            dom_summary="<html><body><h1>Hi</h1></body></html>",
        ),
    )

    result = SeoAgentService().execute(task)

    assert result.status.value == "SUCCEEDED"
    assert {finding.title for finding in result.findings} == {
        "Missing document title",
        "Missing canonical link",
    }
    assert all(finding.evidence for finding in result.findings)
