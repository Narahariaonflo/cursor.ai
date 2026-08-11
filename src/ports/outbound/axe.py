"""Axe accessibility port."""

from __future__ import annotations

from typing import Optional, Protocol

from ports.outbound.results import AccessibilityAuditResult


class AxePort(Protocol):
    """Interface for automated accessibility scans."""

    def run_accessibility_scan(
        self,
        url: str,
        html: Optional[str] = None,
    ) -> AccessibilityAuditResult:
        """Run an accessibility audit for a URL using optional shared HTML."""
