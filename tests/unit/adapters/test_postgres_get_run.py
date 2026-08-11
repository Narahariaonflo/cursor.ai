"""Additional postgres repository isolation tests."""

from __future__ import annotations

import json
from typing import Any, Optional

from adapters.outbound.postgres.scan_repository import PostgresScanRepository
from domain.entities.analysis_run import AnalysisRun
from domain.value_objects.scan import ScanPreferences, TargetUrl


class FakeCursor:
    """Capture SQL executed by the postgres adapter."""

    def __init__(self, row: Optional[tuple[Any, ...]] = None) -> None:
        self.row = row
        self.statements: list[tuple[str, tuple[Any, ...]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.statements.append((sql, params))

    def fetchone(self) -> Optional[tuple[Any, ...]]:
        return self.row


class FakeConnection:
    """Minimal DB connection double."""

    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_obj = cursor

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def commit(self) -> None:
        return None


def test_postgres_get_run_requires_tenant_match() -> None:
    """Loaded payloads must come from tenant-scoped SELECT queries."""
    run = AnalysisRun(
        tenant_id="tenant-a",
        target_url=TargetUrl("https://example.com"),
        preferences=ScanPreferences(1, 0),
    )
    cursor = FakeCursor(row=(json.dumps(run.to_record()),))
    connection = FakeConnection(cursor)
    repo = PostgresScanRepository(
        "postgresql://example",
        connect=lambda url: connection,
    )

    loaded = repo.get_run("tenant-a", run.run_id)

    assert loaded is not None
    assert loaded.tenant_id == "tenant-a"
    assert any(
        "WHERE tenant_id = %s AND run_id = %s" in sql for sql, _ in cursor.statements
    )
