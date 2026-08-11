"""Target policy port."""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.operational import PolicyDecision


class TargetPolicyPort(Protocol):
    """Policy contract for validating target URLs."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return a structured allow/deny decision without fetching the target."""
