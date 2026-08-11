"""Local report renderer adapter."""

from __future__ import annotations

from domain.entities.analysis_run import AnalysisRun
from domain.services.reporting import build_report_title
from ports.outbound.report_renderer import ReportRendererPort


class SimpleReportRenderer(ReportRendererPort):
    """Render deterministic HTML and Markdown reports."""

    def render_markdown(self, run: AnalysisRun) -> str:
        """Render the report in Markdown."""
        lines = [
            f"# {build_report_title(run)}",
            "",
            f"- Run ID: `{run.run_id}`",
            f"- State: `{run.state.value}`",
            f"- Target: `{run.target_url.value}`",
            f"- Planned pages: `{len(run.pages)}`",
            f"- Total findings: `{len(run.findings)}`",
        ]
        narrative = run.summary.get("narrative")
        if narrative:
            lines.extend(["", "## Summary", "", str(narrative)])
        limitations = list(run.summary.get("limitations", []))
        if run.failure_reason:
            limitations.append(run.failure_reason)
        if limitations:
            lines.extend(["", "## Limitations", ""])
            lines.extend(f"- {item}" for item in limitations)
        lines.extend(["", "## Findings", ""])
        if run.findings:
            for finding in run.findings:
                lines.extend(
                    [
                        f"### {finding.title}",
                        f"- Category: `{finding.category}`",
                        f"- Severity: `{finding.severity.value}`",
                        f"- Description: {finding.description}",
                        f"- Evidence: {finding.evidence[0].summary}",
                        "",
                    ],
                )
        else:
            lines.append("No findings are available yet for this run.")
        return "\n".join(lines)

    def render_html(self, run: AnalysisRun) -> str:
        """Render the report in HTML."""
        finding_items = "".join(
            f"<li><strong>{finding.title}</strong> "
            f"({finding.category}, {finding.severity.value})"
            f"<br>{finding.description}</li>"
            for finding in run.findings
        ) or "<li>No findings are available yet for this run.</li>"
        limitation = (
            f"<section><h2>Limitations</h2><p>{run.failure_reason}</p></section>"
            if run.failure_reason
            else ""
        )
        return (
            "<html><head><title>Website Health Report</title></head><body>"
            f"<h1>{build_report_title(run)}</h1>"
            f"<p>Run ID: {run.run_id}</p>"
            f"<p>State: {run.state.value}</p>"
            f"<p>Target: {run.target_url.value}</p>"
            f"<p>Planned pages: {len(run.pages)} | Findings: {len(run.findings)}</p>"
            f"{limitation}<section><h2>Findings</h2><ul>{finding_items}</ul></section>"
            "</body></html>"
        )
