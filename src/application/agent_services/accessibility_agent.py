"""Accessibility analysis via the axe port."""

from __future__ import annotations

from datetime import datetime, timezone

from application.agents.contracts import AgentFailure, AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import (
    AgentTaskStatus,
    EvidenceKind,
    FailureClassification,
    Severity,
)
from ports.outbound.axe import AxePort
from ports.outbound.errors import OutboundOperationError


_IMPACT_SEVERITY = {
    "critical": Severity.CRITICAL,
    "serious": Severity.HIGH,
    "moderate": Severity.MEDIUM,
    "minor": Severity.LOW,
}


class AccessibilityAgentService:
    """Convert axe violations above the configured impact threshold."""

    def __init__(self, axe: AxePort, minimum_impact: str = "moderate") -> None:
        """Store axe adapter and impact floor."""
        self._axe = axe
        self._minimum_impact = minimum_impact
        self._allowed = self._impacts_at_or_above(minimum_impact)

    def execute(self, task: AgentTask) -> AgentResult:
        """Return accessibility findings or a scoped failure."""
        started = datetime.now(timezone.utc)
        try:
            html = task.page_evidence.dom_summary if task.page_evidence else None
            result = self._axe.run_accessibility_scan(task.page_target.url, html)
        except OutboundOperationError as exc:
            return AgentResult(
                task_id=task.task_id,
                run_id=task.run_id,
                agent_name=task.agent_name,
                page_url=task.page_target.url,
                status=AgentTaskStatus.FAILED,
                failure=AgentFailure(
                    classification=FailureClassification.TRANSIENT
                    if exc.retryable
                    else FailureClassification.PERMANENT,
                    code=exc.code,
                    message="accessibility scan failed",
                    retryable=exc.retryable,
                ),
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

        findings = []
        for violation in result.violations:
            if violation.impact.lower() not in self._allowed:
                continue
            findings.append(
                make_finding(
                    category="accessibility",
                    severity=_IMPACT_SEVERITY.get(
                        violation.impact.lower(),
                        Severity.MEDIUM,
                    ),
                    title=f"Accessibility violation: {violation.rule_id}",
                    description=violation.summary,
                    page_url=task.page_target.url,
                    summary=(
                        f"rule={violation.rule_id} impact={violation.impact} "
                        f"target={violation.target}"
                    ),
                    kind=EvidenceKind.TOOL_OUTPUT,
                    signal=violation.rule_id,
                    rule_id=violation.rule_id,
                    artifact_ref=result.artifact_ref,
                ),
            )
        return AgentResult(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_name=task.agent_name,
            page_url=task.page_target.url,
            status=AgentTaskStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=((result.artifact_ref,) if result.artifact_ref else ()),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _impacts_at_or_above(minimum: str) -> set[str]:
        """Return impact labels meeting the configured floor."""
        order = ("minor", "moderate", "serious", "critical")
        if minimum not in order:
            return set(order)
        return set(order[order.index(minimum) :])
