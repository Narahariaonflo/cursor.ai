"""Unit tests for run creation."""

from __future__ import annotations

from typing import Mapping, Optional

import pytest

from application.dto.analysis import StartAnalysisRequest
from application.use_cases.start_analysis_run import StartAnalysisRun
from application.use_cases.validate_analysis_run import ValidateAnalysisRun
from domain.entities.analysis_run import AnalysisRun
from domain.exceptions.errors import ValidationError
from domain.value_objects.operational import BudgetDecision, LimitSnapshot, PolicyDecision


class FakeRepository:
    """In-memory repository for unit tests."""

    def __init__(self) -> None:
        """Initialize storage."""
        self.run: Optional[AnalysisRun] = None

    def save_run(self, run: AnalysisRun) -> None:
        """Persist a run."""
        self.run = run

    def get_run(self, tenant_id: str, run_id: str) -> Optional[AnalysisRun]:
        """Return the stored run when identifiers match."""
        if (
            self.run
            and self.run.tenant_id == tenant_id
            and self.run.run_id == run_id
        ):
            return self.run
        return None


class AllowAllPolicy:
    """Allow all non-local targets."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return an allow decision."""
        return PolicyDecision(allowed=True, code="TARGET_ALLOWED")


class DenyAllPolicy:
    """Deny all targets safely."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return a terminal policy denial."""
        return PolicyDecision(
            allowed=False,
            code="TARGET_DENIED",
            reason="target is not allowed",
        )


class LenientGovernor:
    """Allow the requested scan limits."""

    def validate_preferences(self, max_pages: int, max_depth: int) -> BudgetDecision:
        """Return an allow decision."""
        return BudgetDecision(allowed=True, code="PREFERENCES_ALLOWED")

    def reserve(
        self,
        run_id: str,
        reservation_id: str,
        amounts: Mapping[str, float],
    ) -> BudgetDecision:
        """Accept the initial run reservation."""
        return BudgetDecision(allowed=True, code="BUDGET_RESERVED")

    def reconcile(
        self,
        run_id: str,
        reservation_id: str,
        actual: Mapping[str, float],
    ) -> LimitSnapshot:
        """Return an unused fake reconciliation snapshot."""
        return LimitSnapshot(policy_version="test", values={"pages": 0.0})


class DenyPreferencesGovernor(LenientGovernor):
    """Deny requested scan preferences."""

    def validate_preferences(self, max_pages: int, max_depth: int) -> BudgetDecision:
        """Return a safe preference denial."""
        return BudgetDecision(
            allowed=False,
            code="LIMIT_DENIED",
            reason="requested limits are not allowed",
        )


class DenyReservationGovernor(LenientGovernor):
    """Deny initial budget reservation."""

    def reserve(
        self,
        run_id: str,
        reservation_id: str,
        amounts: Mapping[str, float],
    ) -> BudgetDecision:
        """Return a safe reservation denial."""
        return BudgetDecision(
            allowed=False,
            code="BUDGET_DENIED",
            reason="budget is unavailable",
        )


class RecordingLogger:
    """Record structured events for assertions."""

    def __init__(self) -> None:
        """Initialize recorded events."""
        self.events: list[str] = []

    def info(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Record an informational event."""
        self.events.append(event)

    def error(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Record an error event."""
        self.events.append(event)


def test_start_analysis_run_accepts_without_network_work() -> None:
    """A valid request should persist an accepted run without planning."""
    logger = RecordingLogger()
    repository = FakeRepository()
    use_case = StartAnalysisRun(
        repository=repository,
        logger=logger,
    )

    run = use_case.execute(
        StartAnalysisRequest(
            tenant_id="tenant-a",
            target_url="https://example.com/demo?ref=1",
            max_pages=3,
            max_depth=1,
        ),
    )

    assert run.state.value == "ACCEPTED"
    assert run.tenant_id == "tenant-a"
    assert run.pages == []
    assert repository.run is run
    assert logger.events == ["analysis_run.accepted"]


def test_validate_analysis_run_advances_to_planning() -> None:
    """An accepted, allowed run should reserve budget and reach planning."""
    logger = RecordingLogger()
    repository = FakeRepository()
    run = StartAnalysisRun(repository=repository, logger=logger).execute(
        StartAnalysisRequest(
            tenant_id="tenant-a",
            target_url="https://example.com",
            max_pages=3,
            max_depth=1,
        ),
    )

    ValidateAnalysisRun(
        repository=repository,
        target_policy=AllowAllPolicy(),
        cost_governor=LenientGovernor(),
        logger=logger,
    ).execute("tenant-a", run.run_id)

    assert repository.run is not None
    assert repository.run.state.value == "PLANNING"
    assert logger.events[-1] == "analysis_run.planning"


@pytest.mark.parametrize(
    ("policy", "governor", "expected_event"),
    [
        (DenyAllPolicy(), LenientGovernor(), "analysis_run.target_denied"),
        (AllowAllPolicy(), DenyPreferencesGovernor(), "analysis_run.limit_denied"),
        (AllowAllPolicy(), DenyReservationGovernor(), "analysis_run.budget_denied"),
    ],
)
def test_validate_analysis_run_persists_safe_failure(
    policy: object,
    governor: object,
    expected_event: str,
) -> None:
    """Policy and budget denials should terminate the run safely."""
    logger = RecordingLogger()
    repository = FakeRepository()
    run = StartAnalysisRun(repository=repository, logger=logger).execute(
        StartAnalysisRequest("tenant-a", "https://example.com", 3, 1),
    )

    ValidateAnalysisRun(
        repository=repository,
        target_policy=policy,
        cost_governor=governor,
        logger=logger,
    ).execute("tenant-a", run.run_id)

    assert repository.run is not None
    assert repository.run.state.value == "FAILED"
    assert logger.events[-1] == expected_event


def test_validate_analysis_run_rejects_cross_tenant_lookup() -> None:
    """A run must not be visible outside its tenant boundary."""
    repository = FakeRepository()
    logger = RecordingLogger()
    run = StartAnalysisRun(repository=repository, logger=logger).execute(
        StartAnalysisRequest("tenant-a", "https://example.com", 3, 1),
    )

    with pytest.raises(ValidationError, match="not found"):
        ValidateAnalysisRun(
            repository=repository,
            target_policy=AllowAllPolicy(),
            cost_governor=LenientGovernor(),
            logger=logger,
        ).execute("tenant-b", run.run_id)
