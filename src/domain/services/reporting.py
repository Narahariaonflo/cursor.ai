"""Domain services for report shaping."""

from __future__ import annotations

from collections import Counter

from domain.entities.analysis_run import AnalysisRun, Finding


def summarize_findings(findings: list[Finding]) -> dict[str, object]:
    """Build a deterministic summary from available findings."""
    categories = Counter(f.category for f in findings)
    severities = Counter(f.severity.value for f in findings)
    return {
        "total_findings": len(findings),
        "categories": dict(categories),
        "severities": dict(severities),
    }


def build_report_title(run: AnalysisRun) -> str:
    """Return a deterministic title for report outputs."""
    return f"Website health report for {run.target_url.value}"
