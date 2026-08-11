"""Simple header and timing probe adapter."""

from __future__ import annotations

from time import perf_counter
from typing import Callable, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ports.outbound.errors import OutboundOperationError
from ports.outbound.header_probe import HeaderProbePort
from ports.outbound.policy import TargetPolicyPort
from ports.outbound.results import HeaderProbeResult


class SimpleHeaderProbeAdapter(HeaderProbePort):
    """Probe approved URLs for headers and coarse timings."""

    def __init__(
        self,
        target_policy: TargetPolicyPort,
        timeout_seconds: int,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        """Store policy, timeout, and injectable opener."""
        self._target_policy = target_policy
        self._timeout_seconds = timeout_seconds
        self._opener = opener

    def probe(self, url: str) -> HeaderProbeResult:
        """Return bounded header/timing evidence for one URL."""
        decision = self._target_policy.evaluate(url)
        if not decision.allowed:
            raise OutboundOperationError("TARGET_DENIED", False)
        request = Request(url, headers={"User-Agent": "orca-header-probe/1.0"})
        started = perf_counter()
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw_headers = getattr(response, "headers", {}) or {}
        except HTTPError as exc:
            status = int(exc.code)
            raw_headers = getattr(exc, "headers", {}) or {}
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise OutboundOperationError("HEADER_PROBE_FAILED", True) from exc
        elapsed_ms = (perf_counter() - started) * 1000.0
        headers: Dict[str, str] = {
            str(name): str(value)
            for name, value in dict(raw_headers).items()
            if str(name).lower()
            not in {"authorization", "cookie", "set-cookie", "proxy-authorization"}
        }
        return HeaderProbeResult(
            page_url=url,
            status_code=status,
            headers=headers,
            timings_ms={"ttfb": elapsed_ms, "document": elapsed_ms},
        )
