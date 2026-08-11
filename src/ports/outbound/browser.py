"""Browser automation port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import BrowserCaptureRequest, BrowserEvidenceResult


class BrowserPort(Protocol):
    """Interface for browser-backed evidence collection."""

    async def capture_page(
        self,
        request: BrowserCaptureRequest,
    ) -> BrowserEvidenceResult:
        """Collect page evidence for a URL."""
