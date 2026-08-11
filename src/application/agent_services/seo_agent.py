"""SEO analysis against shared page evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from application.agents.contracts import AgentResult, AgentTask, PageEvidenceRef
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import AgentTaskStatus, EvidenceKind, Severity


_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_CANONICAL_RE = re.compile(
    r"""<link[^>]+rel=["']canonical["'][^>]*>""",
    re.IGNORECASE,
)


class SeoAgentService:
    """Detect missing title and canonical signals from DOM evidence."""

    def execute(self, task: AgentTask) -> AgentResult:
        """Return evidence-backed SEO findings for one page."""
        started = datetime.now(timezone.utc)
        evidence = self._require_evidence(task)
        findings = []
        if not _TITLE_RE.search(evidence.dom_summary):
            findings.append(
                make_finding(
                    category="seo",
                    severity=Severity.HIGH,
                    title="Missing document title",
                    description="The page does not declare a title element.",
                    page_url=task.page_target.url,
                    summary="No <title> element was found in the DOM snapshot.",
                    kind=EvidenceKind.DOM,
                    signal="missing_title",
                ),
            )
        if not _CANONICAL_RE.search(evidence.dom_summary):
            findings.append(
                make_finding(
                    category="seo",
                    severity=Severity.MEDIUM,
                    title="Missing canonical link",
                    description="The page does not declare a canonical link.",
                    page_url=task.page_target.url,
                    summary="No rel=canonical link was found in the DOM snapshot.",
                    kind=EvidenceKind.DOM,
                    signal="missing_canonical",
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

    @staticmethod
    def _require_evidence(task: AgentTask) -> PageEvidenceRef:
        """Require shared page evidence for SEO analysis."""
        if task.page_evidence is None:
            raise ValueError("SEO agent requires page evidence")
        return task.page_evidence
