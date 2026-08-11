"""Shared agent task and result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

from domain.entities.analysis_run import Evidence, Finding, PageTarget
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import (
    AgentKind,
    AgentTaskStatus,
    FailureClassification,
)
from domain.value_objects.scan import ScanPreferences


@dataclass(frozen=True)
class PageEvidenceRef:
    """Immutable shared page evidence available to agents."""

    page_url: str
    dom_summary: str
    console_events: Tuple[str, ...] = ()
    network_events: Tuple[str, ...] = ()
    discovered_links: Tuple[str, ...] = ()
    screenshot_ref: Optional[str] = None


@dataclass(frozen=True)
class AgentFailure:
    """Safe structured agent failure."""

    classification: FailureClassification
    code: str
    message: str
    retryable: bool

    def __post_init__(self) -> None:
        """Require a stable code and safe message."""
        if not self.code.strip() or not self.message.strip():
            raise ValidationError("agent failure code and message are required")


@dataclass(frozen=True)
class AgentTask:
    """One page/agent unit of work."""

    run_id: str
    tenant_id: str
    agent_name: AgentKind
    page_target: PageTarget
    scan_preferences: ScanPreferences
    page_evidence: Optional[PageEvidenceRef] = None
    task_id: str = field(default_factory=lambda: str(uuid4()))
    attempt: int = 1


@dataclass(frozen=True)
class AgentResult:
    """Terminal structured result for one agent task."""

    task_id: str
    run_id: str
    agent_name: AgentKind
    page_url: str
    status: AgentTaskStatus
    findings: Tuple[Finding, ...] = ()
    evidence: Tuple[Evidence, ...] = ()
    artifacts: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    failure: Optional[AgentFailure] = None
    retry_count: int = 0
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    finished_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def __post_init__(self) -> None:
        """Enforce failure presence and evidence-first findings."""
        if self.status is AgentTaskStatus.FAILED and self.failure is None:
            raise ValidationError("failed agent results require failure details")
        if any(not finding.evidence for finding in self.findings):
            raise ValidationError("agent findings must include evidence")
