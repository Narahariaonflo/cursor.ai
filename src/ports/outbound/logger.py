"""Structured logging port."""

from __future__ import annotations

from typing import Mapping, Optional, Protocol


class StructuredLoggerPort(Protocol):
    """Emit secret-safe events with tenant/run correlation where applicable."""

    def debug(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit a diagnostic event."""

    def info(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit an informational event."""

    def error(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit an error event."""

    def warning(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit a warning event."""
