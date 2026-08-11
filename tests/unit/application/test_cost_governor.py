"""Atomic cost-governor unit tests."""

from __future__ import annotations

import pytest

from application.limit_services.cost_governor import InMemoryCostGovernor
from domain.exceptions.errors import ValidationError


def make_governor() -> InMemoryCostGovernor:
    """Build a small deterministic budget for boundary tests."""
    return InMemoryCostGovernor(
        max_pages=50,
        max_depth=4,
        resource_limits={"pages": 50.0, "tokens": 100.0},
        policy_version="test-v1",
    )


def test_preferences_may_reduce_but_not_raise_ceilings() -> None:
    """Request values at/below ceilings pass and values above fail."""
    governor = make_governor()

    assert governor.validate_preferences(50, 4).allowed is True
    assert governor.validate_preferences(51, 4).code == "MAX_PAGES_EXCEEDED"
    assert governor.validate_preferences(50, 5).code == "MAX_DEPTH_EXCEEDED"


def test_reservation_is_atomic_bounded_and_idempotent() -> None:
    """Repeated IDs do not double reserve and overspend is denied."""
    governor = make_governor()

    first = governor.reserve("run-1", "task-1", {"pages": 30.0})
    repeated = governor.reserve("run-1", "task-1", {"pages": 30.0})
    denied = governor.reserve("run-1", "task-2", {"pages": 21.0})

    assert first.allowed is True
    assert first.remaining["pages"] == 20.0
    assert repeated.code == "RESERVATION_EXISTS"
    assert repeated.remaining["pages"] == 20.0
    assert denied.code == "BUDGET_EXCEEDED"


def test_reconciliation_consumes_actual_and_releases_surplus() -> None:
    """Actual usage replaces reservation exactly once."""
    governor = make_governor()
    governor.reserve("run-1", "task-1", {"pages": 30.0, "tokens": 50.0})

    snapshot = governor.reconcile(
        "run-1",
        "task-1",
        {"pages": 10.0, "tokens": 20.0},
    )
    repeated = governor.reconcile(
        "run-1",
        "task-1",
        {"pages": 10.0, "tokens": 20.0},
    )

    assert snapshot.values == {"pages": 40.0, "tokens": 80.0}
    assert repeated.values == snapshot.values


def test_conflicting_or_invalid_operations_fail_closed() -> None:
    """Unknown, negative, conflicting, and unreserved usage is rejected."""
    governor = make_governor()
    with pytest.raises(ValidationError, match="unknown"):
        governor.reserve("run-1", "task-1", {"unknown": 1.0})
    with pytest.raises(ValidationError, match="must not be empty"):
        governor.reserve("run-1", "task-1", {})
    with pytest.raises(ValidationError, match="must not be empty"):
        governor.reserve("", "task-1", {"pages": 1.0})
    with pytest.raises(ValidationError, match="non-negative"):
        governor.reserve("run-1", "task-1", {"pages": -1.0})
    with pytest.raises(ValidationError, match="does not exist"):
        governor.reconcile("run-1", "missing", {"pages": 1.0})

    governor.reserve("run-1", "task-1", {"pages": 2.0})
    assert governor.reserve("run-1", "task-1", {"pages": 1.0}).code == "RESERVATION_CONFLICT"
    with pytest.raises(ValidationError, match="cannot exceed"):
        governor.reconcile("run-1", "task-1", {"pages": 3.0})
    with pytest.raises(ValidationError, match="unreserved"):
        governor.reconcile("run-1", "task-1", {"pages": 1.0, "tokens": 1.0})


def test_reconciled_reservation_cannot_be_reused() -> None:
    """A reconciled task ID cannot create a second charge."""
    governor = make_governor()
    governor.reserve("run-1", "task-1", {"pages": 2.0})
    governor.reconcile("run-1", "task-1", {"pages": 1.0})

    decision = governor.reserve("run-1", "task-1", {"pages": 2.0})

    assert decision.code == "ALREADY_RECONCILED"

    with pytest.raises(ValidationError, match="conflict"):
        governor.reconcile("run-1", "task-1", {"pages": 0.5})


def test_reservations_for_other_runs_do_not_reduce_balance() -> None:
    """Per-run accounting remains isolated."""
    governor = make_governor()
    governor.reserve("run-1", "task-1", {"pages": 50.0})

    decision = governor.reserve("run-2", "task-1", {"pages": 50.0})

    assert decision.allowed is True
    assert decision.remaining["pages"] == 0.0
