"""Coordinate per-page agent execution under concurrency and isolation rules."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Callable, Mapping, Sequence, Tuple

from application.agents.contracts import (
    AgentFailure,
    AgentResult,
    AgentTask,
    PageEvidenceRef,
)
from domain.entities.analysis_run import PageTarget
from domain.value_objects.enums import (
    AgentKind,
    AgentTaskStatus,
    FailureClassification,
)
from domain.value_objects.scan import ScanPreferences
from ports.outbound.logger import StructuredLoggerPort


AgentHandler = Callable[[AgentTask], AgentResult]


class AgentExecutionCoordinator:
    """Dispatch enabled agents and isolate task-level failures."""

    def __init__(
        self,
        agents: Mapping[AgentKind, AgentHandler],
        logger: StructuredLoggerPort,
        max_in_flight: int,
    ) -> None:
        """Store agent handlers and concurrency ceiling."""
        self._agents = dict(agents)
        self._logger = logger
        self._max_in_flight = max_in_flight

    async def execute(
        self,
        *,
        tenant_id: str,
        run_id: str,
        pages: Sequence[PageTarget],
        preferences: ScanPreferences,
        evidence_by_url: Mapping[str, PageEvidenceRef],
    ) -> Tuple[AgentResult, ...]:
        """Run the enabled agent matrix and return structured results."""
        tasks = [
            AgentTask(
                run_id=run_id,
                tenant_id=tenant_id,
                agent_name=agent_name,
                page_target=page,
                scan_preferences=preferences,
                page_evidence=evidence_by_url.get(page.url),
            )
            for page in pages
            for agent_name in sorted(preferences.enabled_agents, key=lambda item: item.value)
            if agent_name in self._agents
        ]
        semaphore = asyncio.Semaphore(self._max_in_flight)
        loop = asyncio.get_running_loop()

        async def _run(task: AgentTask) -> AgentResult:
            async with semaphore:
                return await loop.run_in_executor(
                    None,
                    self._execute_task,
                    task,
                )

        return tuple(await asyncio.gather(*(_run(task) for task in tasks)))

    def _execute_task(self, task: AgentTask) -> AgentResult:
        """Execute one agent task and convert unexpected errors into failures."""
        started = datetime.now(timezone.utc)
        handler = self._agents[task.agent_name]
        self._logger.info(
            "agent_task.started",
            {
                "tenant_id": task.tenant_id,
                "scan_run_id": task.run_id,
                "agent_name": task.agent_name.value,
                "page_url": task.page_target.url,
            },
        )
        try:
            result = handler(task)
        except Exception as exc:
            result = AgentResult(
                task_id=task.task_id,
                run_id=task.run_id,
                agent_name=task.agent_name,
                page_url=task.page_target.url,
                status=AgentTaskStatus.FAILED,
                failure=AgentFailure(
                    classification=FailureClassification.PERMANENT,
                    code="AGENT_EXCEPTION",
                    message="agent execution failed",
                    retryable=False,
                ),
                started_at=started,
                finished_at=datetime.now(timezone.utc),
            )
            del exc
        self._logger.info(
            "agent_task.finished",
            {
                "tenant_id": task.tenant_id,
                "scan_run_id": task.run_id,
                "agent_name": task.agent_name.value,
                "status": result.status.value,
            },
        )
        return result
