"""Unit tests for HTTP link-check adapter."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional
from urllib.error import HTTPError

from adapters.outbound.network.http_link_check import HttpLinkCheckAdapter
from domain.value_objects.operational import PolicyDecision


class AllowPolicy:
    """Allow all targets."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return allow."""
        return PolicyDecision(allowed=True, code="TARGET_ALLOWED")


class DenyPolicy:
    """Deny all targets."""

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return deny."""
        return PolicyDecision(allowed=False, code="DENIED")


class FakeResponse:
    """Minimal URL response double."""

    def __init__(
        self,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status = status
        self.headers = headers or {}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_link_check_returns_zero_for_denied_target() -> None:
    """Denied targets must not be probed."""
    adapter = HttpLinkCheckAdapter(DenyPolicy(), timeout_seconds=1, max_redirects=1)
    result = adapter.check("https://example.com/", "https://evil.example/")
    assert result.status_code == 0


def test_link_check_reports_http_error_status() -> None:
    """HTTP errors should surface as status evidence."""

    def opener(request: Any, timeout: int) -> Any:
        raise HTTPError(
            url="https://example.com/missing",
            code=404,
            msg="missing",
            hdrs=None,
            fp=BytesIO(),
        )

    adapter = HttpLinkCheckAdapter(
        AllowPolicy(),
        timeout_seconds=1,
        max_redirects=1,
        opener=opener,
    )
    result = adapter.check("https://example.com/", "https://example.com/missing")
    assert result.status_code == 404


def test_link_check_follows_redirect_chain() -> None:
    """Redirect responses should accumulate chain evidence."""
    calls = {"count": 0}

    def opener(request: Any, timeout: int) -> Any:
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse(302, {"Location": "https://example.com/final"})
        return FakeResponse(200)

    adapter = HttpLinkCheckAdapter(
        AllowPolicy(),
        timeout_seconds=1,
        max_redirects=2,
        opener=opener,
    )
    result = adapter.check("https://example.com/", "https://example.com/start")
    assert result.status_code == 200
    assert result.redirect_chain[-1] == "https://example.com/final"
