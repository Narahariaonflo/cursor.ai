"""Helpers for evidence-backed agent findings."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from domain.entities.analysis_run import Evidence, Finding
from domain.value_objects.enums import EvidenceKind, Severity


def make_finding(
    *,
    category: str,
    severity: Severity,
    title: str,
    description: str,
    page_url: str,
    summary: str,
    kind: EvidenceKind,
    signal: str,
    rule_id: str = "",
    artifact_ref: Optional[str] = None,
    confidence: float = 1.0,
) -> Finding:
    """Create one finding with required evidence and deterministic fingerprint."""
    evidence = Evidence(
        evidence_id=str(uuid4()),
        kind=kind,
        page_url=page_url,
        summary=summary,
        artifact_ref=artifact_ref,
    )
    fingerprint = "|".join(
        part for part in (category, page_url, signal, rule_id) if part
    )
    return Finding(
        finding_id=str(uuid4()),
        category=category,
        severity=severity,
        title=title,
        description=description,
        fingerprint=fingerprint,
        evidence=[evidence],
        confidence=confidence,
    )
