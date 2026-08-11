"""Assistive LLM boundary."""

from __future__ import annotations

from typing import Mapping, Protocol

from ports.outbound.results import LlmAssistResult


class LlmAssistPort(Protocol):
    """Run approved assistive capabilities without tool authority."""

    def assist(
        self,
        capability: str,
        sanitized_input: Mapping[str, object],
    ) -> LlmAssistResult:
        """Return validated structured assistive output."""
