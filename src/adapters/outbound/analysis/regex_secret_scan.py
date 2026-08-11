"""Secret-pattern scanner that returns masked matches only."""

from __future__ import annotations

import re
from typing import Callable, Sequence

from ports.outbound.results import SecretScanResult
from ports.outbound.secret_scan import SecretScanPort


class RegexSecretScanAdapter(SecretScanPort):
    """Detect configured secret patterns and return masked summaries."""

    def __init__(
        self,
        pattern_expressions: Sequence[str],
        mask_text: Callable[[str], str],
    ) -> None:
        """Compile patterns and store an injected masking function."""
        self._patterns = tuple(
            re.compile(expression, re.IGNORECASE) for expression in pattern_expressions
        )
        self._mask_text = mask_text

    def scan(self, page_url: str, content: str) -> SecretScanResult:
        """Return masked secret-like matches only."""
        matches = [
            self._mask_text(match.group(0))
            for pattern in self._patterns
            for match in pattern.finditer(content)
        ]
        return SecretScanResult(page_url=page_url, masked_matches=tuple(matches))
