"""Deterministic HTML link discovery without browser ownership."""

from __future__ import annotations

import re
from typing import Callable, Tuple
from urllib.parse import urljoin

from ports.outbound.link_discovery import LinkDiscoveryPort
from ports.outbound.results import DiscoveredLink


_HREF_PATTERN = re.compile(
    r"""href\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)


class HtmlLinkDiscovery(LinkDiscoveryPort):
    """Extract absolute href candidates from fetched HTML."""

    def __init__(self, fetch_html: Callable[[str], str]) -> None:
        """Inject a policy-aware HTML fetcher callback."""
        self._fetch_html = fetch_html

    def discover(self, page_url: str) -> Tuple[DiscoveredLink, ...]:
        """Return unique absolute HTTP(S) links in document order."""
        html = self._fetch_html(page_url)
        discovered: list[DiscoveredLink] = []
        seen: set[str] = set()
        for match in _HREF_PATTERN.finditer(html):
            absolute = urljoin(page_url, match.group(1).strip())
            if not absolute.lower().startswith(("http://", "https://")):
                continue
            if absolute in seen:
                continue
            seen.add(absolute)
            discovered.append(DiscoveredLink(url=absolute))
        return tuple(discovered)
