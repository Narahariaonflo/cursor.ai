"""Budget-aware browser evidence collection with pre-persistence masking."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from application.security.sensitive_data_masker import SensitiveDataMasker
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import DeviceProfile
from ports.outbound.artifact_store import ArtifactStorePort
from ports.outbound.browser import BrowserPort
from ports.outbound.cost_governor import CostGovernorPort
from ports.outbound.errors import OutboundOperationError
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.results import BrowserCaptureRequest, BrowserEvidenceResult


class BrowserEvidenceCollector:
    """Capture, mask, and persist immutable page evidence references."""

    def __init__(
        self,
        browser: BrowserPort,
        artifact_store: ArtifactStorePort,
        cost_governor: CostGovernorPort,
        masker: SensitiveDataMasker,
        logger: StructuredLoggerPort,
        max_retries: int,
    ) -> None:
        """Store injected browser, storage, budget, and masking dependencies."""
        self._browser = browser
        self._artifact_store = artifact_store
        self._cost_governor = cost_governor
        self._masker = masker
        self._logger = logger
        self._max_retries = max_retries

    async def collect(
        self,
        tenant_id: str,
        run_id: str,
        page_url: str,
        device_profile: DeviceProfile,
        capture_screenshot: bool,
    ) -> BrowserEvidenceResult:
        """Collect one page of evidence under screenshot budget controls."""
        screenshot_reservation: Optional[str] = None
        if capture_screenshot:
            screenshot_reservation = f"screenshot:{uuid4()}"
            decision = self._cost_governor.reserve(
                run_id=run_id,
                reservation_id=screenshot_reservation,
                amounts={"screenshots": 1.0},
            )
            if not decision.allowed:
                capture_screenshot = False
                screenshot_reservation = None
                self._logger.warning(
                    "browser_evidence.screenshot_budget_exhausted",
                    {"tenant_id": tenant_id, "scan_run_id": run_id},
                )

        request = BrowserCaptureRequest(
            tenant_id=tenant_id,
            run_id=run_id,
            page_url=page_url,
            device_profile=device_profile,
            capture_screenshot=capture_screenshot,
        )
        raw = await self._capture_with_retries(request)
        masked = self._mask_result(raw)
        persisted = self._persist(tenant_id, run_id, masked)

        if screenshot_reservation is not None:
            actual = {"screenshots": 1.0 if persisted.screenshot_ref else 0.0}
            self._cost_governor.reconcile(run_id, screenshot_reservation, actual)
            if capture_screenshot and persisted.screenshot_ref is None:
                self._logger.warning(
                    "browser_evidence.screenshot_gap",
                    {"tenant_id": tenant_id, "scan_run_id": run_id},
                )
        return persisted

    async def _capture_with_retries(
        self,
        request: BrowserCaptureRequest,
    ) -> BrowserEvidenceResult:
        """Retry only classified retryable browser failures."""
        attempts = self._max_retries + 1
        last_error: Optional[OutboundOperationError] = None
        for _ in range(attempts):
            try:
                return await self._browser.capture_page(request)
            except OutboundOperationError as exc:
                last_error = exc
                if not exc.retryable:
                    break
        raise ValidationError(
            last_error.code if last_error else "browser capture failed",
        )

    def _mask_result(self, result: BrowserEvidenceResult) -> BrowserEvidenceResult:
        """Mask DOM and console summaries before persistence."""
        return BrowserEvidenceResult(
            page_url=result.page_url,
            dom_summary=self._masker.mask_text(result.dom_summary),
            console_events=tuple(
                self._masker.mask_text(event) for event in result.console_events
            ),
            network_events=tuple(
                self._masker.mask_text(event) for event in result.network_events
            ),
            discovered_links=result.discovered_links,
            screenshot_ref=result.screenshot_ref,
            truncated=result.truncated,
        )

    def _persist(
        self,
        tenant_id: str,
        run_id: str,
        result: BrowserEvidenceResult,
    ) -> BrowserEvidenceResult:
        """Persist text evidence and return immutable storage references."""
        prefix = f"{tenant_id}/{run_id}/{uuid4()}"
        dom_ref = self._artifact_store.save_text(
            f"{prefix}/dom.txt",
            result.dom_summary,
        )
        console_ref = self._artifact_store.save_text(
            f"{prefix}/console.txt",
            "\n".join(result.console_events),
        )
        return BrowserEvidenceResult(
            page_url=result.page_url,
            dom_summary=result.dom_summary,
            console_events=result.console_events,
            network_events=result.network_events,
            discovered_links=result.discovered_links,
            screenshot_ref=result.screenshot_ref,
            dom_artifact_ref=dom_ref,
            console_artifact_ref=console_ref,
            truncated=result.truncated,
        )
