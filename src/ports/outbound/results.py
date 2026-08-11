"""Provider-independent outbound tool result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

from domain.value_objects.enums import DeviceProfile


@dataclass(frozen=True)
class DiscoveredLink:
    """One link discovered from an approved page response."""

    url: str
    robots_allowed: bool = True


@dataclass(frozen=True)
class BrowserCaptureRequest:
    """Tenant/run-scoped immutable browser capture request."""

    tenant_id: str
    run_id: str
    page_url: str
    device_profile: DeviceProfile
    capture_screenshot: bool = False


@dataclass(frozen=True)
class BrowserEvidenceResult:
    """Bounded immutable evidence captured from one rendered page."""

    page_url: str
    dom_summary: str
    console_events: Tuple[str, ...] = ()
    network_events: Tuple[str, ...] = ()
    discovered_links: Tuple[str, ...] = ()
    screenshot_ref: Optional[str] = None
    dom_artifact_ref: Optional[str] = None
    console_artifact_ref: Optional[str] = None
    truncated: bool = False


@dataclass(frozen=True)
class LighthouseAuditResult:
    """Normalized Lighthouse metrics plus an optional raw artifact reference."""

    page_url: str
    metrics: Mapping[str, float] = field(default_factory=dict)
    artifact_ref: Optional[str] = None


@dataclass(frozen=True)
class AccessibilityViolation:
    """Normalized automated accessibility violation."""

    rule_id: str
    impact: str
    target: str
    summary: str


@dataclass(frozen=True)
class AccessibilityAuditResult:
    """Bounded accessibility result for one page."""

    page_url: str
    violations: Tuple[AccessibilityViolation, ...] = ()
    artifact_ref: Optional[str] = None


@dataclass(frozen=True)
class PsiResult:
    """Normalized optional PageSpeed Insights response."""

    page_url: str
    metrics: Mapping[str, float] = field(default_factory=dict)
    artifact_ref: Optional[str] = None


@dataclass(frozen=True)
class HtmlAnalysisResult:
    """Normalized HTML structure signals."""

    page_url: str
    signals: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SecretScanResult:
    """Secret-pattern result containing masked summaries only."""

    page_url: str
    masked_matches: Tuple[str, ...] = ()


@dataclass(frozen=True)
class HeaderProbeResult:
    """Normalized response headers and timing values."""

    page_url: str
    status_code: int
    headers: Mapping[str, str] = field(default_factory=dict)
    timings_ms: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class LinkCheckResult:
    """Normalized link status and redirect-chain result."""

    source_url: str
    target_url: str
    status_code: int
    redirect_chain: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LlmAssistResult:
    """Validated assistive model output with usage accounting."""

    capability: str
    content: Mapping[str, object]
    input_tokens: int
    output_tokens: int
    provider_alias: str
    model_alias: str
