"""Outbound link-discovery contract used by crawl planning."""

from __future__ import annotations

from typing import Protocol, Tuple

from ports.outbound.results import DiscoveredLink


class LinkDiscoveryPort(Protocol):
    """Discover candidate same-page links without browser ownership."""

    def discover(self, page_url: str) -> Tuple[DiscoveredLink, ...]:
        """Return discovered links for one approved page URL."""
