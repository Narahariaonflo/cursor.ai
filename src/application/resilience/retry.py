"""Bounded retry helper for classified outbound failures."""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

from domain.value_objects.operational import RetryPolicy
from ports.outbound.errors import OutboundOperationError


T = TypeVar("T")


def retry_operation(
    operation: Callable[[], T],
    policy: RetryPolicy,
    sleeper: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> T:
    """Retry only outbound failures explicitly marked retryable."""
    attempt = 0
    while True:
        try:
            return operation()
        except OutboundOperationError as exc:
            if not exc.retryable or attempt >= policy.max_retries:
                raise
            delay_ms = min(
                policy.max_delay_ms,
                int(policy.base_delay_ms * (2**attempt)),
            )
            jitter = delay_ms * policy.jitter_ratio * rng()
            sleeper((delay_ms + jitter) / 1000.0)
            attempt += 1
