"""Tests for bounded operational value objects."""

import pytest

from domain.exceptions.errors import ValidationError
from domain.value_objects.operational import (
    BudgetDecision,
    Confidence,
    CoverageStats,
    HealthScore,
    LimitSnapshot,
    PolicyDecision,
    RetryPolicy,
)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_confidence_accepts_closed_unit_interval(value: float) -> None:
    """Confidence includes both approved boundaries."""
    assert Confidence(value).value == value


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_confidence_rejects_out_of_range_values(value: float) -> None:
    """Confidence cannot escape its approved range."""
    with pytest.raises(ValidationError):
        Confidence(value)


@pytest.mark.parametrize("value", [0, 50, 100])
def test_health_score_accepts_approved_range(value: int) -> None:
    """Health scores include zero and one hundred."""
    assert HealthScore(value).value == value


@pytest.mark.parametrize("value", [-1, 101])
def test_health_score_rejects_out_of_range_values(value: int) -> None:
    """Health scores remain bounded."""
    with pytest.raises(ValidationError):
        HealthScore(value)


def test_coverage_requires_monotonic_counts() -> None:
    """Scanned/planned/eligible counts cannot exceed their parents."""
    with pytest.raises(ValidationError, match="planned pages"):
        CoverageStats(pages_discovered=2, pages_eligible=2, pages_planned=3)


@pytest.mark.parametrize(
    "coverage",
    [
        CoverageStats(pages_discovered=1, pages_eligible=1, pages_planned=1, pages_scanned=1),
        CoverageStats(),
    ],
)
def test_coverage_accepts_monotonic_counts(coverage: CoverageStats) -> None:
    """Coverage accepts empty and fully completed runs."""
    assert coverage.pages_scanned <= coverage.pages_planned


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pages_discovered": -1},
        {"pages_discovered": 1, "pages_eligible": 2},
        {"pages_discovered": 2, "pages_eligible": 2, "pages_planned": 1, "pages_scanned": 2},
    ],
)
def test_coverage_rejects_invalid_relationships(kwargs: dict[str, int]) -> None:
    """Every coverage counter relationship is enforced."""
    with pytest.raises(ValidationError):
        CoverageStats(**kwargs)


def test_retry_policy_requires_consistent_delays() -> None:
    """Maximum delay cannot be lower than base delay."""
    with pytest.raises(ValidationError, match="max_delay_ms"):
        RetryPolicy(max_retries=2, base_delay_ms=500, max_delay_ms=100, jitter_ratio=0.2)


@pytest.mark.parametrize(
    "policy",
    [
        {"max_retries": -1, "base_delay_ms": 1, "max_delay_ms": 1, "jitter_ratio": 0.0},
        {"max_retries": 0, "base_delay_ms": 0, "max_delay_ms": 1, "jitter_ratio": 0.0},
        {"max_retries": 0, "base_delay_ms": 1, "max_delay_ms": 1, "jitter_ratio": 1.1},
    ],
)
def test_retry_policy_rejects_each_invalid_boundary(policy: dict[str, float]) -> None:
    """Retry policy validation covers every independent bound."""
    with pytest.raises(ValidationError):
        RetryPolicy(**policy)


def test_limit_snapshot_rejects_negative_values() -> None:
    """Accepted resource limits are never negative."""
    with pytest.raises(ValidationError, match="non-negative"):
        LimitSnapshot(policy_version="v1", values={"pages": -1})

    with pytest.raises(ValidationError, match="policy_version"):
        LimitSnapshot(policy_version="", values={})


def test_policy_decision_requires_code() -> None:
    """Policy decisions always expose a stable machine-readable code."""
    with pytest.raises(ValidationError, match="code"):
        PolicyDecision(allowed=False, code="")


def test_budget_decision_requires_safe_non_negative_state() -> None:
    """Budget decisions always expose a code and valid remaining balances."""
    with pytest.raises(ValidationError, match="code"):
        BudgetDecision(allowed=False, code="")
    with pytest.raises(ValidationError, match="remaining"):
        BudgetDecision(allowed=True, code="OK", remaining={"pages": -1.0})
