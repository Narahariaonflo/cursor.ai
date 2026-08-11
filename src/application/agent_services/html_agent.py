"""HTML document structure analysis against shared evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from application.agents.contracts import AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import AgentTaskStatus, EvidenceKind, Severity
from ports.outbound.html_analysis import HtmlAnalysisPort


_H1_RE = re.compile(r"<h1\b", re.IGNORECASE)


class HtmlDocumentAgentService:
    """Detect markup/document issues using injected HTML analysis."""

    def __init__(self, html_analysis: HtmlAnalysisPort) -> None:
        """Store the HTML analysis port."""
        self._html_analysis = html_analysis

    def execute(self, task: AgentTask) -> AgentResult:
        """Return structure findings for one page."""
        started = datetime.now(timezone.utc)
        if task.page_evidence is None:
            raise ValueError("HTML agent requires page evidence")
        result = self._html_analysis.analyze(
            task.page_target.url,
            task.page_evidence.dom_summary,
        )
        findings = []
        if result.signals.get("html_lang") == "missing":
            findings.append(
                make_finding(
                    category="html",
                    severity=Severity.MEDIUM,
                    title="Missing html lang attribute",
                    description="The root html element does not declare a language.",
                    page_url=task.page_target.url,
                    summary="html[lang] is missing from the document snapshot.",
                    kind=EvidenceKind.DOM,
                    signal="missing_lang",
                ),
            )
        if len(_H1_RE.findall(task.page_evidence.dom_summary)) != 1:
            findings.append(
                make_finding(
                    category="html",
                    severity=Severity.LOW,
                    title="Unexpected h1 count",
                    description="The page should expose exactly one h1 heading.",
                    page_url=task.page_target.url,
                    summary=f"h1_count={result.signals.get('h1_count', 'unknown')}",
                    kind=EvidenceKind.DOM,
                    signal="h1_count",
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
