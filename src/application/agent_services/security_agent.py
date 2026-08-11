"""Security hygiene analysis with mandatory secret masking."""

from __future__ import annotations

from datetime import datetime, timezone

from application.agents.contracts import AgentResult, AgentTask
from application.agents.finding_factory import make_finding
from application.security.sensitive_data_masker import SensitiveDataMasker
from domain.value_objects.enums import AgentTaskStatus, EvidenceKind, Severity
from ports.outbound.header_probe import HeaderProbePort
from ports.outbound.secret_scan import SecretScanPort


_REQUIRED_HEADERS = (
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
)


class SecurityAgentService:
    """Detect mixed content, missing headers, and masked secret patterns."""

    def __init__(
        self,
        secret_scan: SecretScanPort,
        header_probe: HeaderProbePort,
        masker: SensitiveDataMasker,
    ) -> None:
        """Store security ports and masking dependency."""
        self._secret_scan = secret_scan
        self._header_probe = header_probe
        self._masker = masker

    def execute(self, task: AgentTask) -> AgentResult:
        """Return masked security findings for one page."""
        started = datetime.now(timezone.utc)
        findings = []
        html = task.page_evidence.dom_summary if task.page_evidence else ""
        if "http://" in html and task.page_target.url.startswith("https://"):
            findings.append(
                make_finding(
                    category="security",
                    severity=Severity.HIGH,
                    title="Mixed content detected",
                    description="An HTTPS page references insecure HTTP assets.",
                    page_url=task.page_target.url,
                    summary="DOM snapshot contains http:// asset references.",
                    kind=EvidenceKind.DOM,
                    signal="mixed_content",
                ),
            )
        if "<form" in html.lower() and 'action="http://' in html.lower():
            findings.append(
                make_finding(
                    category="security",
                    severity=Severity.CRITICAL,
                    title="Insecure form action",
                    description="A form posts to an insecure HTTP endpoint.",
                    page_url=task.page_target.url,
                    summary="Form action uses http://.",
                    kind=EvidenceKind.DOM,
                    signal="insecure_form",
                ),
            )

        secrets = self._secret_scan.scan(task.page_target.url, html)
        for match in secrets.masked_matches:
            findings.append(
                make_finding(
                    category="security",
                    severity=Severity.CRITICAL,
                    title="Client-side secret pattern detected",
                    description="A secret-like value was detected and masked.",
                    page_url=task.page_target.url,
                    summary=self._masker.mask_text(match),
                    kind=EvidenceKind.DOM,
                    signal="secret_pattern",
                ),
            )

        probe = self._header_probe.probe(task.page_target.url)
        headers = {name.lower(): value for name, value in probe.headers.items()}
        for header in _REQUIRED_HEADERS:
            if header not in headers:
                findings.append(
                    make_finding(
                        category="security",
                        severity=Severity.MEDIUM,
                        title=f"Missing security header: {header}",
                        description="A recommended security header is absent.",
                        page_url=task.page_target.url,
                        summary=f"header={header} missing",
                        kind=EvidenceKind.RESPONSE,
                        signal=header,
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
