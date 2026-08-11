"""Latency analysis from header probes and optional browser timings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from application.agents.contracts import AgentFailure, AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import (
    AgentTaskStatus,
    EvidenceKind,
    FailureClassification,
    Severity,
)
from ports.outbound.errors import OutboundOperationError
from ports.outbound.header_probe import HeaderProbePort


class LatencyAgentService:
    """Evaluate configured latency thresholds against probe timings."""

    def __init__(
        self,
        header_probe: HeaderProbePort,
        thresholds_ms: Mapping[str, float],
    ) -> None:
        """Store probe port and config-driven thresholds."""
        self._header_probe = header_probe
        self._thresholds_ms = dict(thresholds_ms)

    def execute(self, task: AgentTask) -> AgentResult:
        """Return latency findings with timing evidence."""
        started = datetime.now(timezone.utc)
        try:
            probe = self._header_probe.probe(task.page_target.url)
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
                    message="latency probe failed",
                    retryable=exc.retryable,
                ),
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )

        findings = []
        for metric, threshold in self._thresholds_ms.items():
            value = probe.timings_ms.get(metric)
            if value is None or value <= threshold:
                continue
            findings.append(
                make_finding(
                    category="latency",
                    severity=Severity.MEDIUM,
                    title=f"Latency threshold exceeded: {metric}",
                    description=f"{metric} exceeded the configured threshold.",
                    page_url=task.page_target.url,
                    summary=f"{metric}={value}ms threshold={threshold}ms",
                    kind=EvidenceKind.METRIC,
                    signal=metric,
                ),
            )
        return AgentResult(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_name=task.agent_name,
            page_url=task.page_target.url,
            status=AgentTaskStatus.SUCCEEDED,
            findings=tuple(findings),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )
