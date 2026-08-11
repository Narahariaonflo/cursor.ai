"""Deterministic sensitive-data masking before evidence persistence."""

from __future__ import annotations

import re
from typing import Pattern, Sequence
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from domain.exceptions.errors import ValidationError


_REDACTED = "[REDACTED]"


class SensitiveDataMasker:
    """Mask configured secret patterns and URL query values."""

    def __init__(self, pattern_expressions: Sequence[str]) -> None:
        """Compile configured patterns once and fail closed on invalid syntax."""
        try:
            self._patterns: tuple[Pattern[str], ...] = tuple(
                re.compile(expression, re.IGNORECASE)
                for expression in pattern_expressions
            )
        except re.error as exc:
            raise ValidationError("secret masking pattern is invalid") from exc

    def mask_text(self, content: str) -> str:
        """Replace configured sensitive matches while preserving safe context."""
        masked = content
        for pattern in self._patterns:
            masked = pattern.sub(self._replacement, masked)
        return masked

    def mask_url(self, url: str) -> str:
        """Preserve query names while replacing every query value."""
        parts = urlsplit(url)
        query = "&".join(
            f"{name}={_REDACTED}" for name, _ in parse_qsl(parts.query)
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))

    @staticmethod
    def _replacement(match: re.Match[str]) -> str:
        """Preserve an optional first capture group as safe key context."""
        prefix = match.group(1) if match.lastindex else ""
        return f"{prefix}{_REDACTED}"
