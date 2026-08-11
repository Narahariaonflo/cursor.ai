"""Client-side secret detection port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import SecretScanResult


class SecretScanPort(Protocol):
    """Detect secret-like content while returning masked values only."""

    def scan(self, page_url: str, content: str) -> SecretScanResult:
        """Return normalized masked detections."""
