"""Plan an accepted and validated analysis run under crawl guardrails."""

from __future__ import annotations

from typing import Dict, List, Tuple
from urllib.parse import urlsplit

from application.orchestration.crawl_planner import CrawlPlannerService
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import RunState
from ports.outbound.link_discovery import LinkDiscoveryPort
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.repository import ScanRepositoryPort
from ports.outbound.results import DiscoveredLink


class PlanAnalysisRun:
    """Discover candidates and persist a bounded crawl plan."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        crawl_planner: CrawlPlannerService,
        link_discovery: LinkDiscoveryPort,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store planning dependencies."""
        self._repository = repository
        self._crawl_planner = crawl_planner
        self._link_discovery = link_discovery
        self._logger = logger

    def execute(self, tenant_id: str, run_id: str) -> None:
        """Plan pages for a run already in PLANNING state."""
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            raise ValidationError("run_id not found")
        if run.state is not RunState.PLANNING:
            raise ValidationError("run must be in PLANNING state")

        discoveries = self._discover(
            self._crawl_planner.normalize_url(run.target_url.value),
            run.preferences.max_depth,
        )
        plan = self._crawl_planner.build_queue(
            run.target_url.value,
            run.preferences,
            discoveries,
        )
        run.add_pages(list(plan.pages))
        run.coverage = plan.coverage
        limitations = list(run.summary.get("limitations", []))
        for limitation in plan.limitations:
            if limitation not in limitations:
                limitations.append(limitation)
        run.summary["limitations"] = limitations
        self._repository.save_run(run)
        self._logger.info(
            "analysis_run.planned",
            {
                "tenant_id": run.tenant_id,
                "scan_run_id": run.run_id,
                "state": run.state.value,
                "pages_planned": plan.coverage.pages_planned,
            },
        )

    def _discover(
        self,
        seed_url: str,
        max_depth: int,
    ) -> Dict[str, Tuple[DiscoveredLink, ...]]:
        """Fetch same-origin neighborhoods needed for bounded planning."""
        origin = self._origin(seed_url)
        discoveries: Dict[str, Tuple[DiscoveredLink, ...]] = {}
        frontier: List[Tuple[str, int]] = [(seed_url, 0)]
        seen = {seed_url}
        while frontier:
            page_url, depth = frontier.pop(0)
            links = tuple(
                DiscoveredLink(
                    url=self._crawl_planner.normalize_url(link.url),
                    robots_allowed=link.robots_allowed,
                )
                for link in self._link_discovery.discover(page_url)
            )
            discoveries[page_url] = links
            if depth >= max_depth:
                continue
            for link in links:
                if link.url in seen or self._origin(link.url) != origin:
                    continue
                seen.add(link.url)
                frontier.append((link.url, depth + 1))
        return discoveries

    @staticmethod
    def _origin(url: str) -> Tuple[str, str, int]:
        """Return normalized scheme, host, and effective port."""
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        return (
            scheme,
            (parts.hostname or "").lower(),
            parts.port or (443 if scheme == "https" else 80),
        )
