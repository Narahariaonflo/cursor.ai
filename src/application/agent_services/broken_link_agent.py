"""Broken-link analysis using the link-check port."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple
from urllib.parse import urlsplit

from application.agents.contracts import AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from domain.value_objects.enums import AgentTaskStatus, EvidenceKind, Severity
from ports.outbound.link_check import LinkCheckPort


class BrokenLinkAgentService:
    """Check discovered links under external-link preference controls."""

    def __init__(self, link_check: LinkCheckPort) -> None:
        """Store the link checker dependency."""
        self._link_check = link_check

    def execute(self, task: AgentTask) -> AgentResult:
        """Return broken/redirect findings for in-scope links."""
        started = datetime.now(timezone.utc)
        if task.page_evidence is None:
            raise ValueError("Broken-link agent requires page evidence")
        warnings = []
        findings = []
        origin = self._origin(task.page_target.url)
        for target in task.page_evidence.discovered_links:
            if self._origin(target) != origin:
                if not task.scan_preferences.check_external_links:
                    warnings.append("EXTERNAL_LINK_VALIDATION_DISABLED")
                    continue
            result = self._link_check.check(task.page_target.url, target)
            if result.status_code >= 400 or result.status_code == 0:
                findings.append(
                    make_finding(
                        category="broken_link",
                        severity=Severity.HIGH,
                        title="Broken link detected",
                        description="A linked URL returned an error status.",
                        page_url=task.page_target.url,
                        summary=(
                            f"source={result.source_url} target={result.target_url} "
                            f"status={result.status_code}"
                        ),
                        kind=EvidenceKind.RESPONSE,
                        signal=f"status_{result.status_code}",
                    ),
                )
            elif len(result.redirect_chain) > 1:
                findings.append(
                    make_finding(
                        category="broken_link",
                        severity=Severity.LOW,
                        title="Redirect chain detected",
                        description="A linked URL resolves through multiple redirects.",
                        page_url=task.page_target.url,
                        summary=(
                            f"target={result.target_url} "
                            f"redirects={len(result.redirect_chain)}"
                        ),
                        kind=EvidenceKind.RESPONSE,
                        signal="redirect_chain",
                    ),
                )
        return AgentResult(
            task_id=task.task_id,
            run_id=task.run_id,
            agent_name=task.agent_name,
            page_url=task.page_target.url,
            status=AgentTaskStatus.SUCCEEDED,
            findings=tuple(findings),
            warnings=tuple(sorted(set(warnings))),
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _origin(url: str) -> Tuple[str, str, int]:
        """Return normalized scheme/host/port identity."""
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        return (
            scheme,
            (parts.hostname or "").lower(),
            parts.port or (443 if scheme == "https" else 80),
        )
