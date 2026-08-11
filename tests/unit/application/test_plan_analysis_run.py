"""Unit tests for crawl planning use case persistence."""

from __future__ import annotations

from typing import Mapping, Optional, Tuple

from application.dto.analysis import StartAnalysisRequest
from application.orchestration.crawl_planner import CrawlPlannerService
from application.use_cases.plan_analysis_run import PlanAnalysisRun
from application.use_cases.start_analysis_run import StartAnalysisRun
from application.use_cases.validate_analysis_run import ValidateAnalysisRun
from domain.entities.analysis_run import AnalysisRun
from domain.value_objects.operational import BudgetDecision, LimitSnapshot, PolicyDecision
from ports.outbound.results import DiscoveredLink


class FakeRepository:
    """In-memory tenant-scoped repository."""

    def __init__(self) -> None:
        """Initialize storage."""
        self.run: Optional[AnalysisRun] = None

    def save_run(self, run: AnalysisRun) -> None:
        """Persist a run."""
        self.run = run

    def get_run(self, tenant_id: str, run_id: str) -> Optional[AnalysisRun]:
        """Return the matching tenant-scoped run."""
        if self.run and self.run.tenant_id == tenant_id and self.run.run_id == run_id:
            return self.run
        return None


class AllowAllPolicy:
    """Allow every evaluated target."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return an allow decision."""
        return PolicyDecision(allowed=True, code="TARGET_ALLOWED")


class LenientGovernor:
    """Allow preference validation and reservation."""

    def validate_preferences(self, max_pages: int, max_depth: int) -> BudgetDecision:
        """Allow preferences."""
        return BudgetDecision(allowed=True, code="PREFERENCES_ALLOWED")

    def reserve(
        self,
        run_id: str,
        reservation_id: str,
        amounts: Mapping[str, float],
    ) -> BudgetDecision:
        """Allow reservation."""
        return BudgetDecision(allowed=True, code="BUDGET_RESERVED")

    def reconcile(
        self,
        run_id: str,
        reservation_id: str,
        actual: Mapping[str, float],
    ) -> LimitSnapshot:
        """Return an unused snapshot."""
        return LimitSnapshot(policy_version="test", values={"pages": 0.0})


class FakeDiscovery:
    """Return deterministic same-origin discoveries."""

    def discover(self, page_url: str) -> Tuple[DiscoveredLink, ...]:
        """Return child links for the seed page only."""
        if page_url in {"https://example.com", "https://example.com/"}:
            return (
                DiscoveredLink("https://example.com/a"),
                DiscoveredLink("https://example.com/b"),
                DiscoveredLink("https://other.example/x"),
            )
        return ()


class RecordingLogger:
    """Record structured events."""

    def __init__(self) -> None:
        """Initialize event storage."""
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


def test_plan_analysis_run_persists_bounded_queue() -> None:
    """Planning should persist pages, coverage, and explicit limitations."""
    repository = FakeRepository()
    logger = RecordingLogger()
    policy = AllowAllPolicy()
    run = StartAnalysisRun(repository=repository, logger=logger).execute(
        StartAnalysisRequest("tenant-a", "https://example.com", 2, 1),
    )
    ValidateAnalysisRun(
        repository=repository,
        target_policy=policy,
        cost_governor=LenientGovernor(),
        logger=logger,
    ).execute("tenant-a", run.run_id)

    PlanAnalysisRun(
        repository=repository,
        crawl_planner=CrawlPlannerService(
            target_policy=policy,
            max_discovered_urls=20,
            denied_path_prefixes=frozenset({"/admin"}),
            tracking_query_parameters=frozenset({"utm_source"}),
        ),
        link_discovery=FakeDiscovery(),
        logger=logger,
    ).execute("tenant-a", run.run_id)

    planned = repository.run
    assert planned is not None
    assert planned.state.value == "PLANNING"
    assert [page.url for page in planned.pages] == [
        "https://example.com/",
        "https://example.com/a",
    ]
    assert planned.coverage.pages_planned == 2
    assert "MAX_PAGES_REACHED" in planned.summary["limitations"]
    assert logger.events[-1] == "analysis_run.planned"
