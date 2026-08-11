"""Thread-safe local cost governor for bounded MVP execution."""

from __future__ import annotations

from threading import Lock
from typing import Dict, Mapping, Tuple

from domain.exceptions.errors import ValidationError
from domain.value_objects.operational import BudgetDecision, LimitSnapshot


class InMemoryCostGovernor:
    """Atomically reserve and reconcile per-run resource budgets."""

    def __init__(
        self,
        max_pages: int,
        max_depth: int,
        resource_limits: Mapping[str, float],
        policy_version: str,
    ) -> None:
        """Store immutable ceilings and initialize local accounting."""
        self._max_pages = max_pages
        self._max_depth = max_depth
        self._limits = dict(resource_limits)
        self._policy_version = policy_version
        self._lock = Lock()
        self._reservations: Dict[Tuple[str, str], Dict[str, float]] = {}
        self._actuals: Dict[Tuple[str, str], Dict[str, float]] = {}
        self._consumed: Dict[str, Dict[str, float]] = {}

    def validate_preferences(self, max_pages: int, max_depth: int) -> BudgetDecision:
        """Reject preferences above approved hard ceilings."""
        if max_pages > self._max_pages:
            return self._deny("MAX_PAGES_EXCEEDED", f"max_pages must be <= {self._max_pages}")
        if max_depth > self._max_depth:
            return self._deny("MAX_DEPTH_EXCEEDED", f"max_depth must be <= {self._max_depth}")
        return BudgetDecision(allowed=True, code="PREFERENCES_ALLOWED")

    def reserve(
        self,
        run_id: str,
        reservation_id: str,
        amounts: Mapping[str, float],
    ) -> BudgetDecision:
        """Atomically reserve non-negative known resource amounts."""
        self._validate_identity(run_id, reservation_id)
        requested = self._validate_amounts(amounts)
        key = (run_id, reservation_id)
        with self._lock:
            if key in self._actuals:
                return self._deny("ALREADY_RECONCILED", "reservation is already reconciled")
            if key in self._reservations:
                if self._reservations[key] == requested:
                    return self._allow_with_remaining(run_id, "RESERVATION_EXISTS")
                return self._deny("RESERVATION_CONFLICT", "reservation ID has different amounts")

            remaining = self._remaining(run_id)
            if any(requested[name] > remaining[name] for name in requested):
                return self._deny("BUDGET_EXCEEDED", "requested work exceeds remaining budget")
            self._reservations[key] = requested
            return self._allow_with_remaining(run_id, "BUDGET_RESERVED")

    def reconcile(
        self,
        run_id: str,
        reservation_id: str,
        actual: Mapping[str, float],
    ) -> LimitSnapshot:
        """Idempotently consume actual usage and release unused reservation."""
        self._validate_identity(run_id, reservation_id)
        actual_values = self._validate_amounts(actual)
        key = (run_id, reservation_id)
        with self._lock:
            if key in self._actuals:
                if self._actuals[key] != actual_values:
                    raise ValidationError("reconciliation amounts conflict")
                return self._snapshot(run_id)
            reserved = self._reservations.get(key)
            if reserved is None:
                raise ValidationError("reservation does not exist")
            if any(actual_values.get(name, 0.0) > value for name, value in reserved.items()):
                raise ValidationError("actual usage cannot exceed reservation")
            if any(name not in reserved for name in actual_values):
                raise ValidationError("actual usage contains an unreserved resource")

            consumed = self._consumed.setdefault(run_id, {})
            for name, value in actual_values.items():
                consumed[name] = consumed.get(name, 0.0) + value
            self._actuals[key] = actual_values
            del self._reservations[key]
            return self._snapshot(run_id)

    def _remaining(self, run_id: str) -> Dict[str, float]:
        """Calculate remaining amounts including active reservations."""
        consumed = self._consumed.get(run_id, {})
        reserved = {name: 0.0 for name in self._limits}
        for (owner_run_id, _), amounts in self._reservations.items():
            if owner_run_id == run_id:
                for name, value in amounts.items():
                    reserved[name] += value
        return {
            name: limit - consumed.get(name, 0.0) - reserved[name]
            for name, limit in self._limits.items()
        }

    def _snapshot(self, run_id: str) -> LimitSnapshot:
        """Build the immutable remaining-budget view."""
        return LimitSnapshot(policy_version=self._policy_version, values=self._remaining(run_id))

    def _allow_with_remaining(self, run_id: str, code: str) -> BudgetDecision:
        """Build an allow decision with remaining balances."""
        return BudgetDecision(allowed=True, code=code, remaining=self._remaining(run_id))

    @staticmethod
    def _deny(code: str, reason: str) -> BudgetDecision:
        """Build a safe budget denial."""
        return BudgetDecision(allowed=False, code=code, reason=reason)

    def _validate_amounts(self, amounts: Mapping[str, float]) -> Dict[str, float]:
        """Copy and validate requested resource amounts."""
        values = dict(amounts)
        if not values:
            raise ValidationError("budget amounts must not be empty")
        if any(name not in self._limits for name in values):
            raise ValidationError("unknown budget resource")
        if any(value < 0 for value in values.values()):
            raise ValidationError("budget amounts must be non-negative")
        return values

    @staticmethod
    def _validate_identity(run_id: str, reservation_id: str) -> None:
        """Require stable run and reservation identities."""
        if not run_id.strip() or not reservation_id.strip():
            raise ValidationError("run_id and reservation_id must not be empty")
