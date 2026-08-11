"""HTTP header and latency probe port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import HeaderProbeResult


class HeaderProbePort(Protocol):
    """Probe approved URLs for normalized headers and timing evidence."""

    def probe(self, url: str) -> HeaderProbeResult:
        """Return bounded header and timing evidence."""
