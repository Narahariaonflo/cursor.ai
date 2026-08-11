"""Normalize, deduplicate, and rank agent findings."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from application.agents.contracts import AgentResult
from domain.entities.analysis_run import Finding
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import Severity


_SEVERITY_RANK = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


@dataclass(frozen=True)
class AggregationResult:
    """Deduplicated findings plus agent-scoped limitations."""

    findings: Tuple[Finding, ...]
    limitations: Tuple[str, ...]
    agent_failures: Tuple[str, ...]


class FindingAggregationService:
    """Apply authoritative domain ranking and fingerprint deduplication."""

    def aggregate(self, results: Sequence[AgentResult]) -> AggregationResult:
        """Merge agent outputs into a ranked, evidence-backed finding set."""
        merged: "OrderedDict[str, Finding]" = OrderedDict()
        occurrences: Dict[str, int] = {}
        limitations: List[str] = []
        failures: List[str] = []

        for result in results:
            limitations.extend(result.warnings)
            if result.failure is not None:
                failures.append(
                    f"{result.agent_name.value}:{result.page_url}:{result.failure.code}",
                )
            for finding in result.findings:
                if not finding.evidence:
                    raise ValidationError("evidence-free findings cannot be aggregated")
                key = finding.fingerprint
                occurrences[key] = occurrences.get(key, 0) + 1
                if key not in merged:
                    merged[key] = finding

        ranked = sorted(
            merged.values(),
            key=lambda item: (
                _SEVERITY_RANK[item.severity],
                item.category,
                item.title,
                item.fingerprint,
            ),
        )
        return AggregationResult(
            findings=tuple(ranked),
            limitations=tuple(sorted(set(limitations))),
            agent_failures=tuple(sorted(set(failures))),
        )
