"""Deterministic axe adapter for local/fixture execution."""

from __future__ import annotations

import re
from typing import Optional

from ports.outbound.axe import AxePort
from ports.outbound.results import AccessibilityAuditResult, AccessibilityViolation


_IMAGE_WITHOUT_ALT = re.compile(r"<img(?![^>]*\balt=)[^>]*>", re.IGNORECASE)


class FixtureAxeAdapter(AxePort):
    """Detect a small deterministic accessibility fixture corpus."""

    def run_accessibility_scan(
        self,
        url: str,
        html: Optional[str] = None,
    ) -> AccessibilityAuditResult:
        """Return violations discovered in provided HTML snapshots."""
        content = html or ""
        violations = tuple(
            AccessibilityViolation(
                rule_id="image-alt",
                impact="serious",
                target=f"img:nth-of-type({index + 1})",
                summary="Image elements must have an alt attribute.",
            )
            for index, _ in enumerate(_IMAGE_WITHOUT_ALT.finditer(content))
        )
        return AccessibilityAuditResult(page_url=url, violations=violations)
