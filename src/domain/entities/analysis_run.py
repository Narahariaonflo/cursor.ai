"""Domain entities for scan runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from domain.exceptions.errors import ValidationError
from domain.services.state_machine import validate_transition
from domain.value_objects.enums import (
    AgentKind,
    DeviceProfile,
    EvidenceKind,
    PageEligibilityStatus,
    ReportFormat,
    RunState,
    Severity,
)
from domain.value_objects.operational import CoverageStats
from domain.value_objects.scan import ScanPreferences, TargetUrl


@dataclass(frozen=True)
class Evidence:
    """Evidence attached to a finding."""

    evidence_id: str
    kind: EvidenceKind
    page_url: str
    summary: str
    artifact_ref: Optional[str] = None

    def __post_init__(self) -> None:
        """Require evidence identity, location, and a non-empty safe summary."""
        if not self.evidence_id.strip():
            raise ValidationError("evidence_id must not be empty")
        TargetUrl(self.page_url)
        if not self.summary.strip():
            raise ValidationError("evidence summary must not be empty")


@dataclass(frozen=True)
class Finding:
    """Normalized website issue."""

    finding_id: str
    category: str
    severity: Severity
    title: str
    description: str
    fingerprint: str
    evidence: list[Evidence]
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Enforce evidence-first findings."""
        if not self.evidence:
            raise ValidationError("findings must contain evidence")
        if not self.fingerprint.strip():
            raise ValidationError("finding fingerprint must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValidationError("finding confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class PageTarget:
    """Page queued for analysis."""

    url: str
    depth: int
    source_url: Optional[str] = None
    eligibility_status: PageEligibilityStatus = PageEligibilityStatus.ELIGIBLE

    def __post_init__(self) -> None:
        """Validate page depth and URL."""
        TargetUrl(self.url)
        if self.depth < 0:
            raise ValidationError("page depth must be >= 0")


@dataclass(frozen=True)
class ReportArtifact:
    """Published HTML or Markdown report."""

    artifact_id: str
    run_id: str
    format: ReportFormat
    storage_ref: str
    checksum: str

    def __post_init__(self) -> None:
        """Require complete immutable artifact identity and integrity metadata."""
        if not self.artifact_id.strip() or not self.run_id.strip():
            raise ValidationError("report artifact IDs must not be empty")
        if not self.storage_ref.strip():
            raise ValidationError("report storage_ref must not be empty")
        if not self.checksum.strip():
            raise ValidationError("report checksum must not be empty")


@dataclass
class AnalysisRun:
    """Aggregate root for one analysis request."""

    target_url: TargetUrl
    preferences: ScanPreferences
    tenant_id: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    state: RunState = RunState.ACCEPTED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pages: list[PageTarget] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    artifacts: list[ReportArtifact] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    coverage: CoverageStats = field(default_factory=CoverageStats)
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        """Require an authenticated tenant scope for every run."""
        if not self.tenant_id.strip():
            raise ValidationError("tenant_id must not be empty")

    def transition_to(self, state: RunState) -> None:
        """Move the run through an approved lifecycle transition."""
        if state is RunState.FAILED:
            raise ValidationError("failed transitions require set_failure with a reason")
        validate_transition(self.state, state)
        self.state = state
        self.updated_at = datetime.now(timezone.utc)

    def set_failure(self, reason: str) -> None:
        """Mark the run as failed with a terminal reason."""
        if not reason.strip():
            raise ValidationError("failure reason must not be empty")
        validate_transition(self.state, RunState.FAILED)
        self.failure_reason = reason
        self.state = RunState.FAILED
        self.updated_at = datetime.now(timezone.utc)

    def add_pages(self, pages: list[PageTarget]) -> None:
        """Attach planned pages to the run."""
        self.pages.extend(pages)
        self.updated_at = datetime.now(timezone.utc)

    def add_findings(self, findings: list[Finding]) -> None:
        """Attach normalized findings to the run."""
        self.findings.extend(findings)
        self.updated_at = datetime.now(timezone.utc)

    def add_artifact(self, artifact: ReportArtifact) -> None:
        """Attach a published report artifact."""
        self.artifacts.append(artifact)
        self.updated_at = datetime.now(timezone.utc)

    def finalize(self) -> None:
        """Close the run as completed or partial."""
        formats = {artifact.format for artifact in self.artifacts}
        if formats != {ReportFormat.HTML, ReportFormat.MARKDOWN}:
            raise ValidationError("completed or partial runs need HTML and Markdown reports")
        if any(artifact.run_id != self.run_id for artifact in self.artifacts):
            raise ValidationError("report artifacts must belong to the analysis run")
        target = RunState.PARTIAL if self.failure_reason else RunState.COMPLETED
        self.transition_to(target)

    def to_record(self) -> dict[str, Any]:
        """Serialize the run for persistence."""
        return {
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "target_url": self.target_url.value,
            "preferences": {
                "max_pages": self.preferences.max_pages,
                "max_depth": self.preferences.max_depth,
                "device_profile": self.preferences.device_profile.value,
                "enabled_agents": sorted(
                    agent.value for agent in self.preferences.enabled_agents
                ),
                "check_external_links": self.preferences.check_external_links,
            },
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "pages": [
                {
                    **page.__dict__,
                    "eligibility_status": page.eligibility_status.value,
                }
                for page in self.pages
            ],
            "findings": [
                {
                    "finding_id": finding.finding_id,
                    "category": finding.category,
                    "severity": finding.severity.value,
                    "title": finding.title,
                    "description": finding.description,
                    "fingerprint": finding.fingerprint,
                    "confidence": finding.confidence,
                    "evidence": [
                        {
                            **evidence.__dict__,
                            "kind": evidence.kind.value,
                        }
                        for evidence in finding.evidence
                    ],
                }
                for finding in self.findings
            ],
            "artifacts": [
                {
                    **artifact.__dict__,
                    "format": artifact.format.value,
                }
                for artifact in self.artifacts
            ],
            "summary": self.summary,
            "coverage": self.coverage.__dict__,
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> "AnalysisRun":
        """Rebuild a run from persisted data."""
        run = cls(
            run_id=payload["run_id"],
            tenant_id=payload["tenant_id"],
            target_url=TargetUrl(payload["target_url"]),
            preferences=ScanPreferences(
                max_pages=payload["preferences"]["max_pages"],
                max_depth=payload["preferences"]["max_depth"],
                device_profile=DeviceProfile(
                    payload["preferences"].get("device_profile", "desktop"),
                ),
                enabled_agents=frozenset(
                    AgentKind(agent)
                    for agent in payload["preferences"].get(
                        "enabled_agents",
                        [agent.value for agent in AgentKind],
                    )
                ),
                check_external_links=payload["preferences"].get(
                    "check_external_links",
                    True,
                ),
            ),
            state=RunState(payload["state"]),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(
                payload.get("updated_at", payload["created_at"]),
            ),
        )
        run.pages = [
            PageTarget(
                **{
                    **page,
                    "eligibility_status": PageEligibilityStatus(
                        page.get("eligibility_status", PageEligibilityStatus.ELIGIBLE.value),
                    ),
                },
            )
            for page in payload.get("pages", [])
        ]
        run.findings = [
            Finding(
                finding_id=finding["finding_id"],
                category=finding["category"],
                severity=Severity(finding["severity"]),
                title=finding["title"],
                description=finding["description"],
                fingerprint=finding["fingerprint"],
                confidence=finding["confidence"],
                evidence=[
                    Evidence(
                        **{
                            **evidence,
                            "kind": EvidenceKind(evidence["kind"]),
                        },
                    )
                    for evidence in finding["evidence"]
                ],
            )
            for finding in payload.get("findings", [])
        ]
        run.artifacts = [
            ReportArtifact(
                **{
                    **artifact,
                    "format": ReportFormat(artifact["format"]),
                },
            )
            for artifact in payload.get("artifacts", [])
        ]
        run.summary = payload.get("summary", {})
        run.coverage = CoverageStats(**payload.get("coverage", {}))
        run.failure_reason = payload.get("failure_reason")
        return run
