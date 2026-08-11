"""Assistive narrative generation with deterministic fallback."""

from __future__ import annotations

from typing import Optional, Sequence

from domain.entities.analysis_run import Finding
from domain.value_objects.enums import Severity
from ports.outbound.errors import OutboundOperationError
from ports.outbound.llm_assist import LlmAssistPort


class AssistiveNarrativeService:
    """Produce business-readable summary text without inventing evidence."""

    def __init__(self, llm: Optional[LlmAssistPort] = None) -> None:
        """Store optional assistive LLM port."""
        self._llm = llm

    def compose(
        self,
        findings: Sequence[Finding],
        limitations: Sequence[str],
    ) -> str:
        """Return assistive narrative or a deterministic fallback summary."""
        fallback = self._deterministic_summary(findings, limitations)
        if self._llm is None:
            return fallback
        try:
            result = self._llm.assist(
                "narrative_summary",
                {
                    "finding_ids": [finding.finding_id for finding in findings],
                    "limitations": list(limitations),
                },
            )
        except OutboundOperationError:
            return fallback
        content = result.content.get("summary")
        if not isinstance(content, str) or not content.strip():
            return fallback
        mentioned = set(result.content.get("finding_ids", []))
        known = {finding.finding_id for finding in findings}
        if mentioned and not mentioned.issubset(known):
            return fallback
        return content.strip()

    @staticmethod
    def _deterministic_summary(
        findings: Sequence[Finding],
        limitations: Sequence[str],
    ) -> str:
        """Build a non-AI summary from ranked findings and limitations."""
        if not findings:
            base = "No evidence-backed findings were produced for this run."
        else:
            critical = sum(1 for item in findings if item.severity is Severity.CRITICAL)
            high = sum(1 for item in findings if item.severity is Severity.HIGH)
            base = (
                f"Analysis produced {len(findings)} findings "
                f"({critical} critical, {high} high)."
            )
        if limitations:
            return f"{base} Limitations: {', '.join(limitations)}."
        return base
