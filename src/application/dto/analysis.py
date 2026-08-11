"""Application DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Tuple

from domain.value_objects.enums import AgentKind, DeviceProfile


@dataclass(frozen=True)
class StartAnalysisRequest:
    """Request DTO for creating a scan run."""

    tenant_id: str
    target_url: str
    max_pages: int
    max_depth: int
    device_profile: DeviceProfile = DeviceProfile.DESKTOP
    enabled_agents: FrozenSet[AgentKind] = field(
        default_factory=lambda: frozenset(AgentKind),
    )
    check_external_links: bool = True


@dataclass(frozen=True)
class RunProgress:
    """Stable run progress counters."""

    pages_planned: int
    pages_completed: int
    agent_tasks_planned: int
    agent_tasks_completed: int
    findings_count: int


@dataclass(frozen=True)
class RunCoverage:
    """Stable run coverage counters."""

    pages_discovered: int
    pages_eligible: int
    pages_scanned: int


@dataclass(frozen=True)
class SafeFailure:
    """Safe terminal failure representation."""

    code: str
    message: str


@dataclass(frozen=True)
class RunStatusResponse:
    """Response DTO for run status lookups."""

    run_id: str
    state: str
    target_url: str
    progress: RunProgress
    coverage: RunCoverage
    limitations: Tuple[str, ...]
    agent_failures: Tuple[str, ...]
    failure: Optional[SafeFailure]
    created_at: str
    updated_at: str
    report_ready: bool = False
