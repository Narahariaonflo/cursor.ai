"""Unit tests for budget-aware browser evidence collection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Mapping, Optional

from adapters.outbound.filesystem.artifact_store import FilesystemArtifactStore
from application.evidence.browser_evidence_collector import BrowserEvidenceCollector
from application.limit_services.cost_governor import InMemoryCostGovernor
from application.security.sensitive_data_masker import SensitiveDataMasker
from domain.value_objects.enums import DeviceProfile
from ports.outbound.errors import OutboundOperationError
from ports.outbound.results import BrowserCaptureRequest, BrowserEvidenceResult


class FakeBrowser:
    """Return deterministic browser evidence for collector tests."""

    def __init__(self, fail_times: int = 0) -> None:
        """Optionally fail the first N attempts as retryable errors."""
        self.fail_times = fail_times
        self.calls = 0

    async def capture_page(
        self,
        request: BrowserCaptureRequest,
    ) -> BrowserEvidenceResult:
        """Return masked-sensitive evidence after optional retries."""
        self.calls += 1
        if self.calls <= self.fail_times:
            raise OutboundOperationError("TRANSIENT_BROWSER_ERROR", True)
        return BrowserEvidenceResult(
            page_url=request.page_url,
            dom_summary='<html>api_key=abcd1234</html>',
            console_events=("error: password=hunter2",),
            network_events=("failed:https://example.com/asset",),
            discovered_links=("https://example.com/next",),
            screenshot_ref="memory://shot.png" if request.capture_screenshot else None,
        )


class RecordingLogger:
    """Capture warning and info events."""

    def __init__(self) -> None:
        """Initialize event storage."""
        self.events: list[str] = []

    def debug(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Ignore debug events."""

    def info(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Record info events."""
        self.events.append(event)

    def warning(
        self,
        event: str,
        context: Optional[Mapping[str, object]] = None,
    ) -> None:
        """Record warning events."""
        self.events.append(event)

    def error(self, event: str, context: Optional[Mapping[str, object]] = None) -> None:
        """Record error events."""
        self.events.append(event)


def test_collector_masks_and_persists_evidence(tmp_path: Path) -> None:
    """Secrets should be masked before artifact persistence."""
    store = FilesystemArtifactStore(tmp_path)
    governor = InMemoryCostGovernor(
        max_pages=10,
        max_depth=2,
        resource_limits={"screenshots": 1},
        policy_version="test",
    )
    collector = BrowserEvidenceCollector(
        browser=FakeBrowser(),
        artifact_store=store,
        cost_governor=governor,
        masker=SensitiveDataMasker(
            (
                r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9_\-]{8,})",
                r"(?i)(password\s*[=:]\s*)(\S+)",
            ),
        ),
        logger=RecordingLogger(),
        max_retries=1,
    )

    result = asyncio.run(
        collector.collect(
            tenant_id="tenant-a",
            run_id="run-a",
            page_url="https://example.com/",
            device_profile=DeviceProfile.DESKTOP,
            capture_screenshot=True,
        ),
    )

    assert "abcd1234" not in result.dom_summary
    assert "hunter2" not in result.console_events[0]
    assert result.dom_artifact_ref is not None
    assert "abcd1234" not in Path(result.dom_artifact_ref).read_text(encoding="utf-8")
    assert result.screenshot_ref == "memory://shot.png"


def test_collector_skips_screenshot_when_budget_exhausted(tmp_path: Path) -> None:
    """Screenshot budget exhaustion should continue with an explicit gap."""
    store = FilesystemArtifactStore(tmp_path)
    governor = InMemoryCostGovernor(
        max_pages=10,
        max_depth=2,
        resource_limits={"screenshots": 0},
        policy_version="test",
    )
    logger = RecordingLogger()
    browser = FakeBrowser()
    collector = BrowserEvidenceCollector(
        browser=browser,
        artifact_store=store,
        cost_governor=governor,
        masker=SensitiveDataMasker(()),
        logger=logger,
        max_retries=0,
    )

    result = asyncio.run(
        collector.collect(
            tenant_id="tenant-a",
            run_id="run-a",
            page_url="https://example.com/",
            device_profile=DeviceProfile.DESKTOP,
            capture_screenshot=True,
        ),
    )

    assert result.screenshot_ref is None
    assert "browser_evidence.screenshot_budget_exhausted" in logger.events
