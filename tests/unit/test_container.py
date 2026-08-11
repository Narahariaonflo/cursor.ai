"""Dependency-injection container smoke tests."""

from pathlib import Path

from pytest import MonkeyPatch

from bootstrap.container import Container


def test_container_builds_from_configuration(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """The composition root builds all foundational dependencies."""
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))

    container = Container.build()

    assert container.settings.database_path == tmp_path / "orca.sqlite3"
    assert container.start_analysis_run is not None
    assert container.validate_analysis_run is not None
    assert container.plan_analysis_run is not None
    assert container.get_run_status is not None
    assert container.publish_run_report is not None
    assert container.browser_evidence_collector is not None
    assert container.agent_execution_coordinator is not None
    assert container.process_analysis_run is not None
    assert container.repository is not None
