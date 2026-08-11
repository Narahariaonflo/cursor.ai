"""Unit tests for deterministic bounded crawl planning."""

from __future__ import annotations

from application.orchestration.crawl_planner import CrawlPlannerService
from domain.value_objects.operational import PolicyDecision
from domain.value_objects.scan import ScanPreferences
from ports.outbound.results import DiscoveredLink


class PathPolicy:
    """Allow targets except a deterministic denied path."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return a structured path-policy decision."""
        allowed = "/private" not in target_url
        return PolicyDecision(
            allowed=allowed,
            code="TARGET_ALLOWED" if allowed else "PATH_DENIED",
        )


def make_planner(max_discovered_urls: int = 20) -> CrawlPlannerService:
    """Build a planner with explicit test guardrails."""
    return CrawlPlannerService(
        target_policy=PathPolicy(),
        max_discovered_urls=max_discovered_urls,
        denied_path_prefixes=frozenset({"/admin", "/logout"}),
        tracking_query_parameters=frozenset({"utm_source", "gclid"}),
    )


def test_breadth_first_plan_filters_and_reports_page_limit() -> None:
    """The planner should retain stable BFS order and exclude unsafe links."""
    seed = "https://example.com/"
    plan = make_planner().build_queue(
        seed,
        ScanPreferences(max_pages=3, max_depth=2),
        {
            seed: (
                DiscoveredLink("https://example.com/a?utm_source=test"),
                DiscoveredLink("https://example.com/b"),
                DiscoveredLink("https://other.example/page"),
                DiscoveredLink("https://example.com/robots", robots_allowed=False),
                DiscoveredLink("https://example.com/admin/users"),
                DiscoveredLink("https://example.com/private"),
            ),
            "https://example.com/a": (DiscoveredLink("https://example.com/a/child"),),
        },
    )

    assert [page.url for page in plan.pages] == [
        "https://example.com/",
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert plan.coverage.pages_planned == 3
    assert plan.coverage.pages_eligible == 4
    assert plan.limitations == ("MAX_PAGES_REACHED",)


def test_depth_and_discovery_limits_are_explicit() -> None:
    """Depth and discovery exhaustion should never expand silently."""
    seed = "https://example.com/"
    discoveries = {
        seed: (
            DiscoveredLink("https://example.com/a"),
            DiscoveredLink("https://example.com/b"),
            DiscoveredLink("https://example.com/c"),
        ),
        "https://example.com/a": (DiscoveredLink("https://example.com/a/child"),),
    }

    depth_plan = make_planner().build_queue(
        seed,
        ScanPreferences(max_pages=10, max_depth=1),
        discoveries,
    )
    discovery_plan = make_planner(max_discovered_urls=2).build_queue(
        seed,
        ScanPreferences(max_pages=10, max_depth=2),
        discoveries,
    )

    assert "MAX_DEPTH_REACHED" in depth_plan.limitations
    assert discovery_plan.coverage.pages_discovered == 2
    assert discovery_plan.limitations == ("MAX_DISCOVERED_URLS_REACHED",)


def test_tracking_variants_share_one_page_budget_entry() -> None:
    """Configured tracking parameters should not create duplicate pages."""
    seed = "https://example.com/"
    plan = make_planner().build_queue(
        seed,
        ScanPreferences(max_pages=10, max_depth=1),
        {
            seed: (
                DiscoveredLink("https://example.com/product?id=1&utm_source=a"),
                DiscoveredLink("https://example.com/product?utm_source=b&id=1#details"),
            ),
        },
    )

    assert [page.url for page in plan.pages] == [
        "https://example.com/",
        "https://example.com/product?id=1",
    ]
