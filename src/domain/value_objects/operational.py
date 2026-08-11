"""Validated operational value objects used by application policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

from domain.exceptions.errors import ValidationError


@dataclass(frozen=True)
class Confidence:
    """Finding confidence constrained to the approved range."""

    value: float

    def __post_init__(self) -> None:
        """Reject confidence outside zero through one."""
        if not 0.0 <= self.value <= 1.0:
            raise ValidationError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class HealthScore:
    """Deterministic report health score."""

    value: int

    def __post_init__(self) -> None:
        """Reject scores outside zero through one hundred."""
        if not 0 <= self.value <= 100:
            raise ValidationError("health score must be between 0 and 100")


@dataclass(frozen=True)
class CoverageStats:
    """Run-level discovery and scan coverage counters."""

    pages_discovered: int = 0
    pages_eligible: int = 0
    pages_planned: int = 0
    pages_scanned: int = 0

    def __post_init__(self) -> None:
        """Validate non-negative monotonic coverage relationships."""
        values = (
            self.pages_discovered,
            self.pages_eligible,
            self.pages_planned,
            self.pages_scanned,
        )
        if any(value < 0 for value in values):
            raise ValidationError("coverage counters must be non-negative")
        if self.pages_eligible > self.pages_discovered:
            raise ValidationError("eligible pages cannot exceed discovered pages")
        if self.pages_planned > self.pages_eligible:
            raise ValidationError("planned pages cannot exceed eligible pages")
        if self.pages_scanned > self.pages_planned:
            raise ValidationError("scanned pages cannot exceed planned pages")


@dataclass(frozen=True)
class LimitSnapshot:
    """Immutable effective resource limits accepted for a run."""

    policy_version: str
    values: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Require an identified policy and non-negative limits."""
        if not self.policy_version.strip():
            raise ValidationError("policy_version must not be empty")
        if any(value < 0 for value in self.values.values()):
            raise ValidationError("limit values must be non-negative")


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded retry policy injected into adapters."""

    max_retries: int
    base_delay_ms: int
    max_delay_ms: int
    jitter_ratio: float

    def __post_init__(self) -> None:
        """Validate retry bounds and delay relationships."""
        if self.max_retries < 0:
            raise ValidationError("max_retries must be non-negative")
        if self.base_delay_ms < 1:
            raise ValidationError("base_delay_ms must be positive")
        if self.max_delay_ms < self.base_delay_ms:
            raise ValidationError("max_delay_ms must be >= base_delay_ms")
        if not 0.0 <= self.jitter_ratio <= 1.0:
            raise ValidationError("jitter_ratio must be between 0.0 and 1.0")


@dataclass(frozen=True)
class PolicyDecision:
    """Structured allow/deny decision with a safe reason."""

    allowed: bool
    code: str
    reason: Optional[str] = None
    approved_addresses: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require a machine-readable decision code."""
        if not self.code.strip():
            raise ValidationError("policy decision code must not be empty")


@dataclass(frozen=True)
class BudgetDecision:
    """Structured budget reservation or validation decision."""

    allowed: bool
    code: str
    reason: Optional[str] = None
    remaining: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Require a code and non-negative remaining balances."""
        if not self.code.strip():
            raise ValidationError("budget decision code must not be empty")
        if any(value < 0 for value in self.remaining.values()):
            raise ValidationError("remaining budget must be non-negative")
