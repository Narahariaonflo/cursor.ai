"""Unit tests for assistive narrative fallback behavior."""

from __future__ import annotations

from typing import Dict, Mapping, Optional

from application.agents.finding_factory import make_finding
from application.services.assistive_narrative import AssistiveNarrativeService
from domain.value_objects.enums import EvidenceKind, Severity
from ports.outbound.errors import OutboundOperationError
from ports.outbound.results import LlmAssistResult


class FakeLlm:
    """Return invalid or valid assistive payloads."""

    def __init__(
        self,
        payload: Optional[Dict[str, object]] = None,
        fail: bool = False,
    ) -> None:
        """Configure success payload or failure mode."""
        self.payload = payload
        self.fail = fail

    def assist(
        self,
        capability: str,
        sanitized_input: Mapping[str, object],
    ) -> LlmAssistResult:
        """Return configured assistive output."""
        del sanitized_input
        if self.fail:
            raise OutboundOperationError("LLM_UNAVAILABLE", True)
        return LlmAssistResult(
            capability=capability,
            content=self.payload or {},
            input_tokens=1,
            output_tokens=1,
            provider_alias="test",
            model_alias="test",
        )


def test_deterministic_fallback_without_llm() -> None:
    """Narrative should summarize findings without an LLM dependency."""
    finding = make_finding(
        category="seo",
        severity=Severity.HIGH,
        title="Missing title",
        description="missing",
        page_url="https://example.com/",
        summary="missing title",
        kind=EvidenceKind.DOM,
        signal="missing_title",
    )
    text = AssistiveNarrativeService().compose([finding], ["MAX_PAGES_REACHED"])
    assert "1 findings" in text
    assert "MAX_PAGES_REACHED" in text


def test_llm_output_rejected_when_finding_ids_unknown() -> None:
    """Assistive text that references unknown findings must be discarded."""
    service = AssistiveNarrativeService(
        FakeLlm({"summary": "Invented", "finding_ids": ["missing-id"]}),
    )
    text = service.compose([], [])
    assert "No evidence-backed findings" in text
