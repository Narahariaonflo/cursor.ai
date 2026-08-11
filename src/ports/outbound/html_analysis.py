"""HTML structure analysis port."""

from __future__ import annotations

from typing import Protocol

from ports.outbound.results import HtmlAnalysisResult


class HtmlAnalysisPort(Protocol):
    """Analyze bounded HTML without exposing parser-native payloads."""

    def analyze(self, page_url: str, html: str) -> HtmlAnalysisResult:
        """Return normalized HTML signals."""
