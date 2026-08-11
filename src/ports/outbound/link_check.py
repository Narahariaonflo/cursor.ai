"""Broken-link checking port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import LinkCheckResult


class LinkCheckPort(Protocol):
    """Check policy-approved internal or external links."""

    def check(self, source_url: str, target_url: str) -> LinkCheckResult:
        """Return normalized status and redirect evidence."""
