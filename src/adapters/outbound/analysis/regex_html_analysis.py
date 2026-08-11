"""Deterministic HTML signal extraction adapter."""

from __future__ import annotations

import re

from ports.outbound.html_analysis import HtmlAnalysisPort
from ports.outbound.results import HtmlAnalysisResult


_LANG_RE = re.compile(r"<html[^>]*\blang=(['\"])(.*?)\1", re.IGNORECASE)
_H1_RE = re.compile(r"<h1\b", re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class RegexHtmlAnalysisAdapter(HtmlAnalysisPort):
    """Extract bounded HTML signals without parser-native payloads."""

    def analyze(self, page_url: str, html: str) -> HtmlAnalysisResult:
        """Return normalized document signals for agent consumption."""
        lang_match = _LANG_RE.search(html)
        title_match = _TITLE_RE.search(html)
        return HtmlAnalysisResult(
            page_url=page_url,
            signals={
                "html_lang": lang_match.group(2) if lang_match else "missing",
                "h1_count": str(len(_H1_RE.findall(html))),
                "title": title_match.group(1).strip() if title_match else "missing",
            },
        )
