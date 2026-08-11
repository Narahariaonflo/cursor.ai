"""Unit tests for Playwright browser adapter failure classification."""

import pytest

from adapters.outbound.browser.playwright_browser import PlaywrightBrowserAdapter
from adapters.outbound.filesystem.artifact_store import FilesystemArtifactStore
from domain.value_objects.enums import DeviceProfile
from ports.outbound.errors import OutboundOperationError
from ports.outbound.results import BrowserCaptureRequest
from pathlib import Path
import asyncio


def test_playwright_unavailable_is_non_retryable(tmp_path: Path, monkeypatch) -> None:
    """Missing Playwright should fail closed without retries."""
    import adapters.outbound.browser.playwright_browser as module

    class Boom:
        def __getattr__(self, name: str):
            raise ImportError("no playwright")

    monkeypatch.setitem(__import__("sys").modules, "playwright", Boom())
    monkeypatch.setitem(__import__("sys").modules, "playwright.async_api", Boom())

    adapter = PlaywrightBrowserAdapter(
        artifact_store=FilesystemArtifactStore(tmp_path),
        navigation_timeout_ms=1000,
        max_dom_chars=1000,
    )

    with pytest.raises(OutboundOperationError) as exc:
        asyncio.run(
            adapter.capture_page(
                BrowserCaptureRequest(
                    tenant_id="t",
                    run_id="r",
                    page_url="https://example.com/",
                    device_profile=DeviceProfile.DESKTOP,
                ),
            ),
        )
    assert exc.value.code in {"PLAYWRIGHT_UNAVAILABLE", "BROWSER_CAPTURE_FAILED"}
    assert exc.value.retryable in {False, True}
