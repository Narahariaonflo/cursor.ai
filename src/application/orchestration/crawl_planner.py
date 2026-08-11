"""Deterministic bounded crawl planning."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, FrozenSet, Mapping, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from domain.entities.analysis_run import PageTarget
from domain.value_objects.operational import CoverageStats
from domain.value_objects.scan import ScanPreferences
from ports.outbound.policy import TargetPolicyPort
from ports.outbound.results import DiscoveredLink


@dataclass(frozen=True)
class CrawlPlan:
    """Stable planned pages plus explicit coverage metadata."""

    pages: Tuple[PageTarget, ...]
    coverage: CoverageStats
    limitations: Tuple[str, ...] = ()


class CrawlPlannerService:
    """Plan same-origin pages breadth-first under policy and hard limits."""

    def __init__(
        self,
        target_policy: TargetPolicyPort,
        max_discovered_urls: int,
        denied_path_prefixes: FrozenSet[str],
        tracking_query_parameters: FrozenSet[str],
    ) -> None:
        """Store injected safety policy and crawl configuration."""
        self._target_policy = target_policy
        self._max_discovered_urls = max_discovered_urls
        self._denied_path_prefixes = denied_path_prefixes
        self._tracking_query_parameters = tracking_query_parameters

    def build_queue(
        self,
        target_url: str,
        preferences: ScanPreferences,
        discoveries: Mapping[str, Sequence[DiscoveredLink]],
    ) -> CrawlPlan:
        """Build a deterministic same-origin breadth-first crawl plan."""
        seed = self.normalize_url(target_url)
        origin = self._origin(seed)
        pending: Deque[Tuple[str, int, str, bool]] = deque(
            [(seed, 0, "", True)],
        )
        seen: set[str] = set()
        pages: list[PageTarget] = []
        eligible = 0
        limitations: set[str] = set()

        while pending and len(seen) < self._max_discovered_urls:
            raw_url, depth, source_url, robots_allowed = pending.popleft()
            normalized = self.normalize_url(raw_url)
            if normalized in seen:
                continue
            seen.add(normalized)
            if not self._is_eligible(normalized, origin, robots_allowed):
                continue

            eligible += 1
            if len(pages) >= preferences.max_pages:
                limitations.add("MAX_PAGES_REACHED")
                continue
            pages.append(
                PageTarget(
                    url=normalized,
                    depth=depth,
                    source_url=source_url or None,
                ),
            )
            if depth >= preferences.max_depth:
                if discoveries.get(normalized):
                    limitations.add("MAX_DEPTH_REACHED")
                continue
            for link in discoveries.get(normalized, ()):
                pending.append((link.url, depth + 1, normalized, link.robots_allowed))

        if pending:
            limitations.add("MAX_DISCOVERED_URLS_REACHED")
        coverage = CoverageStats(
            pages_discovered=len(seen),
            pages_eligible=eligible,
            pages_planned=len(pages),
            pages_scanned=0,
        )
        return CrawlPlan(
            pages=tuple(pages),
            coverage=coverage,
            limitations=tuple(sorted(limitations)),
        )

    def _is_eligible(
        self,
        url: str,
        origin: Tuple[str, str, int],
        robots_allowed: bool,
    ) -> bool:
        """Apply robots, origin, path, and target-policy constraints."""
        try:
            candidate_origin = self._origin(url)
        except ValueError:
            return False
        if (
            not robots_allowed
            or candidate_origin[0] not in {"http", "https"}
            or candidate_origin != origin
        ):
            return False
        path = urlsplit(url).path.lower()
        if any(path.startswith(prefix) for prefix in self._denied_path_prefixes):
            return False
        return self._target_policy.evaluate(url).allowed

    def normalize_url(self, target_url: str) -> str:
        """Normalize fragments, path, and configured tracking parameters."""
        parts = urlsplit(target_url)
        path = parts.path or "/"
        query = urlencode(
            sorted(
                (name, value)
                for name, value in parse_qsl(parts.query, keep_blank_values=True)
                if name.lower() not in self._tracking_query_parameters
            ),
        )
        return urlunsplit(
            (parts.scheme.lower(), parts.netloc.lower(), path, query, ""),
        )

    @staticmethod
    def _origin(url: str) -> Tuple[str, str, int]:
        """Return normalized scheme, hostname, and effective port."""
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        return (
            scheme,
            (parts.hostname or "").lower(),
            parts.port or (443 if scheme == "https" else 80),
        )
