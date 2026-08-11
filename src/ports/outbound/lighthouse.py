"""Lighthouse port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import LighthouseAuditResult


class LighthousePort(Protocol):
    """Interface for performance audit execution."""

    def run_audit(self, url: str) -> LighthouseAuditResult:
        """Run a Lighthouse audit for a URL."""
