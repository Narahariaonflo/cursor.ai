"""Cost governor port."""

from __future__ import annotations

from typing import Mapping, Protocol

from domain.value_objects.operational import BudgetDecision, LimitSnapshot


class CostGovernorPort(Protocol):
    """Enforce high-level run limits."""

    def validate_preferences(self, max_pages: int, max_depth: int) -> BudgetDecision:
        """Validate request preferences against hard ceilings."""

    def reserve(
        self,
        run_id: str,
        reservation_id: str,
        amounts: Mapping[str, float],
    ) -> BudgetDecision:
        """Atomically reserve resource amounts before scheduling."""

    def reconcile(
        self,
        run_id: str,
        reservation_id: str,
        actual: Mapping[str, float],
    ) -> LimitSnapshot:
        """Idempotently replace a reservation with actual usage."""
