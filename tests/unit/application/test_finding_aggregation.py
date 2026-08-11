"""Unit tests for finding aggregation and ranking."""

from datetime import datetime, timezone

from application.agents.contracts import AgentFailure, AgentResult
from application.agents.finding_factory import make_finding
from application.orchestration.finding_aggregation import FindingAggregationService
from domain.entities.analysis_run import Finding
from domain.value_objects.enums import (
    AgentKind,
    AgentTaskStatus,
    EvidenceKind,
    FailureClassification,
    Severity,
)


def _result(*findings: Finding, failed: bool = False) -> AgentResult:
    """Build a minimal agent result fixture."""
    return AgentResult(
        task_id="task",
        run_id="run",
        agent_name=AgentKind.SEO,
        page_url="https://example.com/",
        status=AgentTaskStatus.FAILED if failed else AgentTaskStatus.SUCCEEDED,
        findings=findings,
        failure=(
            AgentFailure(
                classification=FailureClassification.PERMANENT,
                code="AGENT_EXCEPTION",
                message="failed",
                retryable=False,
            )
            if failed
            else None
        ),
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )


def test_aggregation_dedupes_and_ranks_by_severity() -> None:
    """Critical findings should rank above info and duplicates should merge."""
    critical = make_finding(
        category="security",
        severity=Severity.CRITICAL,
        title="Secret",
        description="secret",
        page_url="https://example.com/",
        summary="masked",
        kind=EvidenceKind.DOM,
        signal="secret",
    )
    info = make_finding(
        category="seo",
        severity=Severity.INFO,
        title="Info",
        description="info",
        page_url="https://example.com/",
        summary="info",
        kind=EvidenceKind.DOM,
        signal="info",
    )
    duplicate = Finding(
        finding_id="other",
        category=critical.category,
        severity=critical.severity,
        title=critical.title,
        description=critical.description,
        fingerprint=critical.fingerprint,
        evidence=list(critical.evidence),
    )

    aggregated = FindingAggregationService().aggregate(
        (_result(info), _result(critical, duplicate), _result(failed=True)),
    )

    assert [item.severity for item in aggregated.findings] == [
        Severity.CRITICAL,
        Severity.INFO,
    ]
    assert aggregated.agent_failures
    assert len(aggregated.findings) == 2

