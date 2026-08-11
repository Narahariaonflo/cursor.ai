"""Policy-gated HTML fetcher for crawl link discovery."""

from __future__ import annotations

from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from ports.outbound.policy import TargetPolicyPort


class HttpHtmlFetcher:
    """Fetch bounded HTML only after Target Policy approval."""

    def __init__(
        self,
        target_policy: TargetPolicyPort,
        timeout_seconds: int,
        max_bytes: int,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        """Store policy, bounds, and injectable opener for tests."""
        self._target_policy = target_policy
        self._timeout_seconds = timeout_seconds
        self._max_bytes = max_bytes
        self._opener = opener

    def fetch(self, url: str) -> str:
        """Return HTML text or an empty document when denied/unavailable."""
        decision = self._target_policy.evaluate(url)
        if not decision.allowed:
            return ""
        request = Request(url, headers={"User-Agent": "orca-link-discovery/1.0"})
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                payload = response.read(self._max_bytes + 1)
        except (URLError, TimeoutError, OSError, ValueError):
            return ""
        if len(payload) > self._max_bytes:
            payload = payload[: self._max_bytes]
        return payload.decode("utf-8", errors="replace")
