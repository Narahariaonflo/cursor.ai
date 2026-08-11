"""Performance analysis via Lighthouse and optional PSI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Optional

from application.agents.contracts import AgentFailure, AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import (
    AgentTaskStatus,
    EvidenceKind,
    FailureClassification,
    Severity,
)
from ports.outbound.errors import OutboundOperationError
from ports.outbound.lighthouse import LighthousePort
from ports.outbound.psi import PsiPort


class PerformanceAgentService:
    """Create metric-backed performance findings from configured thresholds."""

    def __init__(
        self,
        lighthouse: LighthousePort,
        thresholds: Mapping[str, float],
        psi: Optional[PsiPort] = None,
        psi_enabled: bool = False,
    ) -> None:
        """Store tool ports and threshold configuration."""
        self._lighthouse = lighthouse
        self._thresholds = dict(thresholds)
        self._psi = psi
        self._psi_enabled = psi_enabled

    def execute(self, task: AgentTask) -> AgentResult:
        """Return performance findings or a scoped tool failure."""
        started = datetime.now(timezone.utc)
        try:
            audit = self._lighthouse.run_audit(task.page_target.url)
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
                    message="performance audit failed",
                    retryable=exc.retryable,
                ),
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

        findings = []
        for metric, threshold in self._thresholds.items():
            value = audit.metrics.get(metric)
            if value is None or value <= threshold:
                continue
            findings.append(
                make_finding(
                    category="performance",
                    severity=Severity.HIGH,
                    title=f"Performance threshold exceeded: {metric}",
                    description=f"{metric} exceeded the configured threshold.",
                    page_url=task.page_target.url,
                    summary=f"{metric}={value} threshold={threshold}",
                    kind=EvidenceKind.METRIC,
                    signal=metric,
                    artifact_ref=audit.artifact_ref,
                ),
            )
        warnings = []
        artifacts = ((audit.artifact_ref,) if audit.artifact_ref else ())
        if self._psi_enabled and self._psi is not None:
            psi_result = self._psi.fetch(task.page_target.url)
            if psi_result.artifact_ref:
                artifacts = artifacts + (psi_result.artifact_ref,)
        elif not self._psi_enabled:
            warnings.append("PSI_DISABLED_BY_DEFAULT")
        return AgentResult(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_name=task.agent_name,
            page_url=task.page_target.url,
            status=AgentTaskStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=artifacts,
            warnings=tuple(warnings),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )
