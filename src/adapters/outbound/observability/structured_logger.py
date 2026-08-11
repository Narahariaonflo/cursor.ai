"""Standard-library JSON structured logger adapter."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Mapping, Optional

from ports.outbound.logger import StructuredLoggerPort


_SENSITIVE_FIELD_FRAGMENTS = frozenset(
    {"authorization", "cookie", "credential", "password", "secret", "token"},
)


class JsonStructuredLogger(StructuredLoggerPort):
    """Write one sanitized JSON object per log event."""

    def __init__(self, name: str, level: str) -> None:
        """Create a configured application logger."""
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
        self._logger.propagate = False

    def debug(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit a diagnostic JSON event."""
        self._emit(logging.DEBUG, event, context)

    def info(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit an informational JSON event."""
        self._emit(logging.INFO, event, context)

    def error(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit an error JSON event."""
        self._emit(logging.ERROR, event, context)

    def warning(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Emit a warning JSON event."""
        self._emit(logging.WARNING, event, context)

    def _emit(
        self,
        level: int,
        event: str,
        context: Optional[Mapping[str, object]],
    ) -> None:
        """Serialize and emit a sanitized event."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "event": event,
            **self._sanitize(context or {}),
        }
        self._logger.log(level, json.dumps(payload, default=str, sort_keys=True))

    def _sanitize(self, context: Mapping[str, object]) -> dict[str, object]:
        """Mask values whose field names indicate sensitive content."""
        return {
            key: (
                "[REDACTED]"
                if any(fragment in key.lower() for fragment in _SENSITIVE_FIELD_FRAGMENTS)
                else value
            )
            for key, value in context.items()
        }
