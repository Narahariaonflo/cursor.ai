"""Playwright-backed browser evidence adapter."""

from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urljoin
from uuid import uuid4

from ports.outbound.artifact_store import ArtifactStorePort
from ports.outbound.browser import BrowserPort
from ports.outbound.errors import OutboundOperationError
from ports.outbound.results import BrowserCaptureRequest, BrowserEvidenceResult


_HREF_PATTERN = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


class PlaywrightBrowserAdapter(BrowserPort):
    """Capture DOM, console, network, links, and optional screenshots."""

    def __init__(
        self,
        artifact_store: ArtifactStorePort,
        navigation_timeout_ms: int,
        max_dom_chars: int,
    ) -> None:
        """Store artifact persistence and capture bounds."""
        self._artifact_store = artifact_store
        self._navigation_timeout_ms = navigation_timeout_ms
        self._max_dom_chars = max_dom_chars

    async def capture_page(
        self,
        request: BrowserCaptureRequest,
    ) -> BrowserEvidenceResult:
        """Navigate once and return bounded immutable page evidence."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise OutboundOperationError("PLAYWRIGHT_UNAVAILABLE", False) from exc

        console_events: List[str] = []
        network_events: List[str] = []
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 720},
                        is_mobile=request.device_profile.value == "mobile",
                    )
                    page = await context.new_page()
                    page.on(
                        "console",
                        lambda message: console_events.append(
                            f"{message.type}: {message.text}",
                        ),
                    )
                    page.on(
                        "requestfailed",
                        lambda failed: network_events.append(
                            f"failed:{failed.url}:{failed.failure}",
                        ),
                    )
                    response = await page.goto(
                        request.page_url,
                        wait_until="domcontentloaded",
                        timeout=self._navigation_timeout_ms,
                    )
                    if response is None:
                        raise OutboundOperationError("NAVIGATION_FAILED", True)
                    html = await page.content()
                    truncated = len(html) > self._max_dom_chars
                    dom_summary = html[: self._max_dom_chars]
                    screenshot_ref: Optional[str] = None
                    if request.capture_screenshot:
                        image = await page.screenshot(full_page=False)
                        screenshot_ref = self._artifact_store.save_bytes(
                            (
                                f"{request.tenant_id}/{request.run_id}/"
                                f"{uuid4()}.png"
                            ),
                            image,
                        )
                    links: list[str] = []
                    for match in _HREF_PATTERN.finditer(html):
                        absolute = urljoin(request.page_url, match.group(1).strip())
                        if absolute.lower().startswith(("http://", "https://")):
                            links.append(absolute)
                    return BrowserEvidenceResult(
                        page_url=request.page_url,
                        dom_summary=dom_summary,
                        console_events=tuple(console_events),
                        network_events=tuple(network_events),
                        discovered_links=tuple(dict.fromkeys(links)),
                        screenshot_ref=screenshot_ref,
                        truncated=truncated,
                    )
                finally:
                    await browser.close()
        except OutboundOperationError:
            raise
        except Exception as exc:
            raise OutboundOperationError("BROWSER_CAPTURE_FAILED", True) from exc
