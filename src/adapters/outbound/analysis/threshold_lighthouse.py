"""Deterministic Lighthouse adapter for local/fixture metrics."""

from __future__ import annotations

from typing import Mapping

from ports.outbound.lighthouse import LighthousePort
from ports.outbound.results import LighthouseAuditResult


class MappingLighthouseAdapter(LighthousePort):
    """Return configured metrics for known fixture URLs."""

    def __init__(self, metrics_by_url: Mapping[str, Mapping[str, float]]) -> None:
        """Store fixture metrics keyed by page URL."""
        self._metrics_by_url = {
            url: dict(metrics) for url, metrics in metrics_by_url.items()
        }

    def run_audit(self, url: str) -> LighthouseAuditResult:
        """Return normalized metrics for the requested URL."""
        return LighthouseAuditResult(
            page_url=url,
            metrics=self._metrics_by_url.get(url, {}),
            artifact_ref=f"memory://lighthouse/{url}",
        )
