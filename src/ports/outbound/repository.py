"""Repository ports."""

from __future__ import annotations

from typing import Protocol
from typing import Optional

from domain.entities.analysis_run import AnalysisRun


class ScanRepositoryPort(Protocol):
    """Persistence contract for scan runs."""

    def save_run(self, run: AnalysisRun) -> None:
        """Persist a scan run."""

    def get_run(self, tenant_id: str, run_id: str) -> Optional[AnalysisRun]:
        """Load a scan run only within the authenticated tenant scope."""
