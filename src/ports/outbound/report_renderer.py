"""Report rendering port."""

from __future__ import annotations

from typing import Protocol

from domain.entities.analysis_run import AnalysisRun


class ReportRendererPort(Protocol):
    """Render report content from a scan run."""

    def render_markdown(self, run: AnalysisRun) -> str:
        """Render the report in Markdown."""

    def render_html(self, run: AnalysisRun) -> str:
        """Render the report in HTML."""
