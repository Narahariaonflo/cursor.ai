"""Unit tests for bounded retry helper."""

from domain.value_objects.operational import RetryPolicy
from application.resilience.retry import retry_operation
from ports.outbound.errors import OutboundOperationError
import pytest


def test_retry_operation_retries_retryable_failures() -> None:
    """Retryable outbound failures should be retried within policy bounds."""
    attempts = {"count": 0}
    sleeps: list[float] = []

    def operation() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise OutboundOperationError("TEMP", True)
        return "ok"

    result = retry_operation(
        operation,
        RetryPolicy(max_retries=2, base_delay_ms=10, max_delay_ms=20, jitter_ratio=0.0),
        sleeper=sleeps.append,
        rng=lambda: 0.0,
    )

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleeps == [0.01, 0.02]


def test_retry_operation_does_not_retry_permanent_failures() -> None:
    """Permanent outbound failures should fail immediately."""
    with pytest.raises(OutboundOperationError, match="PERM"):
        retry_operation(
            lambda: (_ for _ in ()).throw(OutboundOperationError("PERM", False)),
            RetryPolicy(max_retries=3, base_delay_ms=10, max_delay_ms=10, jitter_ratio=0),
            sleeper=lambda _: None,
        )
