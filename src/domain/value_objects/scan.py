"""Domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet
from urllib.parse import urlparse

from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import AgentKind, DeviceProfile


@dataclass(frozen=True)
class ScanPreferences:
    """Scan limits supplied by the caller."""

    max_pages: int
    max_depth: int
    device_profile: DeviceProfile = DeviceProfile.DESKTOP
    enabled_agents: FrozenSet[AgentKind] = field(
        default_factory=lambda: frozenset(AgentKind),
    )
    check_external_links: bool = True

    def __post_init__(self) -> None:
        """Validate scan bounds."""
        if self.max_pages < 1:
            raise ValidationError("max_pages must be >= 1")
        if self.max_depth < 0:
            raise ValidationError("max_depth must be >= 0")
        if not self.enabled_agents:
            raise ValidationError("enabled_agents must not be empty")


@dataclass(frozen=True)
class TargetUrl:
    """Validated public target URL."""

    value: str

    def __post_init__(self) -> None:
        """Ensure the URL is suitable for MVP scanning."""
        parsed = urlparse(self.value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("target_url must be an absolute http(s) URL")
