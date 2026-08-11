"""Unit tests for agent execution isolation and concurrency."""

from __future__ import annotations

import asyncio
from typing import Mapping, Optional

from application.agents.contracts import AgentResult, AgentTask, PageEvidenceRef
from application.orchestration.agent_execution_coordinator import (
    AgentExecutionCoordinator,
)
from domain.entities.analysis_run import PageTarget
from domain.value_objects.enums import AgentKind, AgentTaskStatus
from domain.value_objects.scan import ScanPreferences


class RecordingLogger:
    """Capture coordinator events."""

    def __init__(self) -> None:
        """Initialize storage."""
        self.events: list[str] = []

    def info(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Record info events."""
        self.events.append(event)

    def error(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Record error events."""
        self.events.append(event)

    def warning(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Record warning events."""
        self.events.append(event)

    def debug(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Ignore debug events."""


def _ok(task: AgentTask) -> AgentResult:
    """Return a successful empty result."""
    return AgentResult(
        task_id=task.task_id,
        run_id=task.run_id,
        agent_name=task.agent_name,
        page_url=task.page_target.url,
        status=AgentTaskStatus.SUCCEEDED,
    )


def _boom(task: AgentTask) -> AgentResult:
    """Raise to verify coordinator isolation."""
    raise RuntimeError("agent exploded")


def test_coordinator_isolates_agent_failures() -> None:
    """One agent exception should not prevent sibling agent success."""
    coordinator = AgentExecutionCoordinator(
        agents={
            AgentKind.SEO: _ok,
            AgentKind.CONSOLE: _boom,
        },
        logger=RecordingLogger(),
        max_in_flight=2,
    )
    preferences = ScanPreferences(
        max_pages=1,
        max_depth=0,
        enabled_agents=frozenset({AgentKind.SEO, AgentKind.CONSOLE}),
    )
    evidence = {
        "https://example.com/": PageEvidenceRef(
            page_url="https://example.com/",
            dom_summary="<html></html>",
            console_events=("error: boom",),
        ),
    }

    results = asyncio.run(
        coordinator.execute(
            tenant_id="tenant-a",
            run_id="run-a",
            pages=[PageTarget(url="https://example.com/", depth=0)],
            preferences=preferences,
            evidence_by_url=evidence,
        ),
    )

    by_agent = {result.agent_name: result for result in results}
    assert by_agent[AgentKind.SEO].status is AgentTaskStatus.SUCCEEDED
    assert by_agent[AgentKind.CONSOLE].status is AgentTaskStatus.FAILED
    assert by_agent[AgentKind.CONSOLE].failure is not None
