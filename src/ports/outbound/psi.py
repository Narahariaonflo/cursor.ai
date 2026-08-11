"""Optional PageSpeed Insights port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import PsiResult


class PsiPort(Protocol):
    """Fetch optional normalized PageSpeed Insights evidence."""

    def fetch(self, url: str) -> PsiResult:
        """Fetch PSI evidence for a policy-approved URL."""
