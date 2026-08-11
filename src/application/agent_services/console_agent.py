"""Browser console analysis against shared page evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from application.agents.contracts import AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import AgentTaskStatus, EvidenceKind, Severity


class ConsoleAgentService:
    """Map console errors and failed loads into findings."""

    def execute(self, task: AgentTask) -> AgentResult:
        """Return console findings without re-navigating."""
        started = datetime.now(timezone.utc)
        if task.page_evidence is None:
            raise ValueError("Console agent requires page evidence")
        findings = []
        for event in task.page_evidence.console_events:
            lowered = event.lower()
            if "error" not in lowered and "failed" not in lowered:
                continue
            findings.append(
                make_finding(
                    category="console",
                    severity=Severity.HIGH,
                    title="Browser console error",
                    description="The page emitted a console error or failed load.",
                    page_url=task.page_target.url,
                    summary=event,
                    kind=EvidenceKind.CONSOLE,
                    signal="console_error",
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
