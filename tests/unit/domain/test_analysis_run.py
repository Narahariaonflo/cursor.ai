"""Domain invariant tests for analysis runs and findings."""

import pytest

from domain.entities.analysis_run import (
    AnalysisRun,
    Evidence,
    Finding,
    ReportArtifact,
)
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import EvidenceKind, ReportFormat, RunState, Severity
from domain.value_objects.scan import ScanPreferences, TargetUrl


def make_run() -> AnalysisRun:
    """Create a valid analysis run for state tests."""
    return AnalysisRun(
        tenant_id="tenant-a",
        target_url=TargetUrl("https://example.com/"),
        preferences=ScanPreferences(max_pages=5, max_depth=1),
    )


def make_artifact(run: AnalysisRun, format: ReportFormat) -> ReportArtifact:
    """Create immutable report metadata owned by a run."""
    return ReportArtifact(
        artifact_id=f"artifact-{format.value}",
        run_id=run.run_id,
        format=format,
        storage_ref=f"report.{format.value}",
        checksum="abc123",
    )


def test_invalid_state_transition_is_rejected() -> None:
    """A run cannot skip lifecycle states."""
    run = make_run()

    with pytest.raises(ValidationError, match="ACCEPTED -> RUNNING"):
        run.transition_to(RunState.RUNNING)


def test_completed_run_requires_report_artifact() -> None:
    """A rendered run cannot finalize without a report artifact."""
    run = make_run()
    for state in (
        RunState.VALIDATING,
        RunState.PLANNING,
        RunState.RUNNING,
        RunState.AGGREGATING,
        RunState.RENDERING,
    ):
        run.transition_to(state)

    with pytest.raises(ValidationError, match="need HTML and Markdown"):
        run.finalize()


def test_valid_run_finalizes_and_round_trips() -> None:
    """A complete run preserves state through persistence serialization."""
    run = make_run()
    for state in (
        RunState.VALIDATING,
        RunState.PLANNING,
        RunState.RUNNING,
        RunState.AGGREGATING,
        RunState.RENDERING,
    ):
        run.transition_to(state)
    run.add_artifact(make_artifact(run, ReportFormat.HTML))
    run.add_artifact(make_artifact(run, ReportFormat.MARKDOWN))
    run.finalize()

    restored = AnalysisRun.from_record(run.to_record())

    assert restored.state is RunState.COMPLETED
    assert restored.artifacts[0].storage_ref == "report.html"
    assert restored.updated_at == run.updated_at


def test_finding_requires_evidence_and_valid_confidence() -> None:
    """Findings require evidence, fingerprint, and bounded confidence."""
    with pytest.raises(ValidationError, match="must contain evidence"):
        Finding(
            finding_id="finding-1",
            category="seo",
            severity=Severity.HIGH,
            title="Missing title",
            description="The document has no title.",
            fingerprint="seo:title:missing",
            evidence=[],
        )

    evidence = Evidence(
        evidence_id="evidence-1",
        kind=EvidenceKind.DOM,
        page_url="https://example.com/",
        summary="The title element is absent.",
    )
    with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
        Finding(
            finding_id="finding-1",
            category="seo",
            severity=Severity.HIGH,
            title="Missing title",
            description="The document has no title.",
            fingerprint="seo:title:missing",
            evidence=[evidence],
            confidence=1.1,
        )


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RunState.ACCEPTED, RunState.VALIDATING),
        (RunState.VALIDATING, RunState.PLANNING),
        (RunState.PLANNING, RunState.RUNNING),
        (RunState.RUNNING, RunState.AGGREGATING),
        (RunState.AGGREGATING, RunState.RENDERING),
        (RunState.RENDERING, RunState.COMPLETED),
        (RunState.RENDERING, RunState.PARTIAL),
    ],
)
def test_all_non_failure_transitions_are_allowed(
    current: RunState,
    target: RunState,
) -> None:
    """Every documented non-failure state edge is accepted."""
    run = make_run()
    run.state = current

    run.transition_to(target)

    assert run.state is target


@pytest.mark.parametrize("state", list(RunState))
def test_terminal_states_reject_further_transitions(state: RunState) -> None:
    """Completed, partial, and failed runs are immutable."""
    if state in {RunState.COMPLETED, RunState.PARTIAL, RunState.FAILED}:
        run = make_run()
        run.state = state
        with pytest.raises(ValidationError):
            run.transition_to(RunState.VALIDATING)


@pytest.mark.parametrize(
    "state",
    [RunState.VALIDATING, RunState.PLANNING, RunState.RUNNING, RunState.AGGREGATING, RunState.RENDERING],
)
def test_failure_exits_require_and_preserve_reason(state: RunState) -> None:
    """Every documented failure exit records a non-empty terminal reason."""
    run = make_run()
    run.state = state

    run.set_failure("dependency unavailable")

    assert run.state is RunState.FAILED
    assert run.failure_reason == "dependency unavailable"


def test_direct_failed_transition_is_rejected() -> None:
    """Callers cannot enter FAILED without a reason."""
    run = make_run()
    run.transition_to(RunState.VALIDATING)

    with pytest.raises(ValidationError, match="require set_failure"):
        run.transition_to(RunState.FAILED)


def test_failure_reason_produces_partial_report() -> None:
    """Usable rendered output with a limitation finalizes as PARTIAL."""
    run = make_run()
    for state in (
        RunState.VALIDATING,
        RunState.PLANNING,
        RunState.RUNNING,
        RunState.AGGREGATING,
        RunState.RENDERING,
    ):
        run.transition_to(state)
    run.failure_reason = "one agent failed"
    run.add_artifact(make_artifact(run, ReportFormat.HTML))
    run.add_artifact(make_artifact(run, ReportFormat.MARKDOWN))

    run.finalize()

    assert run.state is RunState.PARTIAL


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evidence_id", "", "evidence_id"),
        ("summary", "", "summary"),
        ("page_url", "relative", "absolute http"),
    ],
)
def test_evidence_rejects_incomplete_identity(
    field: str,
    value: str,
    message: str,
) -> None:
    """Evidence always has identity, public location, and a summary."""
    values = {
        "evidence_id": "evidence-1",
        "kind": EvidenceKind.DOM,
        "page_url": "https://example.com/",
        "summary": "bounded evidence",
    }
    values[field] = value
    with pytest.raises(ValidationError, match=message):
        Evidence(**values)


def test_page_and_artifact_invariants_are_enforced() -> None:
    """Queued pages and report metadata reject invalid primitive values."""
    from domain.entities.analysis_run import PageTarget

    with pytest.raises(ValidationError, match="depth"):
        PageTarget(url="https://example.com/", depth=-1)
    with pytest.raises(ValidationError, match="IDs"):
        ReportArtifact(
            artifact_id="",
            run_id="run-1",
            format=ReportFormat.HTML,
            storage_ref="report.html",
            checksum="abc",
        )


def test_run_requires_tenant_and_owned_report_artifacts() -> None:
    """Run identity and artifact ownership cannot cross tenant/run boundaries."""
    with pytest.raises(ValidationError, match="tenant_id"):
        AnalysisRun(
            tenant_id="",
            target_url=TargetUrl("https://example.com/"),
            preferences=ScanPreferences(1, 0),
        )

    run = make_run()
    for state in (
        RunState.VALIDATING,
        RunState.PLANNING,
        RunState.RUNNING,
        RunState.AGGREGATING,
        RunState.RENDERING,
    ):
        run.transition_to(state)
    run.add_artifact(make_artifact(run, ReportFormat.HTML))
    run.add_artifact(
        ReportArtifact(
            artifact_id="artifact-markdown",
            run_id="another-run",
            format=ReportFormat.MARKDOWN,
            storage_ref="report.md",
            checksum="abc",
        ),
    )

    with pytest.raises(ValidationError, match="belong"):
        run.finalize()
