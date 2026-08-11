"""Unit tests for production persistence adapter contracts."""

from __future__ import annotations

import json
from typing import Any, Optional

import pytest

from adapters.outbound.postgres.scan_repository import PostgresScanRepository
from adapters.outbound.s3.artifact_store import S3ArtifactStore
from domain.entities.analysis_run import AnalysisRun
from domain.value_objects.scan import ScanPreferences, TargetUrl


class FakeCursor:
    """Capture SQL executed by the postgres adapter."""

    def __init__(self, row: Optional[tuple[Any, ...]] = None) -> None:
        """Initialize optional fetch result."""
        self.row = row
        self.statements: list[tuple[str, tuple[Any, ...]]] = []

    def __enter__(self) -> "FakeCursor":
        """Return the cursor context."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Ignore context exit."""

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        """Record SQL and parameters."""
        self.statements.append((sql, params))

    def fetchone(self) -> Optional[tuple[Any, ...]]:
        """Return the configured row."""
        return self.row


class FakeConnection:
    """Minimal DB connection double."""

    def __init__(self, cursor: FakeCursor) -> None:
        """Store the cursor double."""
        self.cursor_obj = cursor
        self.committed = False

    def __enter__(self) -> "FakeConnection":
        """Return the connection context."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Ignore context exit."""

    def cursor(self) -> FakeCursor:
        """Return the fake cursor."""
        return self.cursor_obj

    def commit(self) -> None:
        """Mark commit."""
        self.committed = True


class FakeS3Client:
    """In-memory S3 client double."""

    def __init__(self) -> None:
        """Initialize object storage."""
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:
        """Store an object."""
        self.objects[(Bucket, Key)] = Body

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        """Load an object body."""

        class Body:
            """Bytes body adapter."""

            def __init__(self, data: bytes) -> None:
                self._data = data

            def read(self) -> bytes:
                return self._data

        return {"Body": Body(self.objects[(Bucket, Key)])}


def test_postgres_repository_scopes_queries_by_tenant() -> None:
    """Reads and writes must include tenant_id in the primary key path."""
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    repo = PostgresScanRepository(
        "postgresql://example",
        connect=lambda url: connection,
    )
    run = AnalysisRun(
        tenant_id="tenant-a",
        target_url=TargetUrl("https://example.com"),
        preferences=ScanPreferences(1, 0),
    )

    repo.save_run(run)

    assert any("tenant_id" in sql and "run_id" in sql for sql, _ in cursor.statements)
    assert cursor.statements[-1][1][0] == "tenant-a"


def test_s3_artifact_store_uses_bucket_prefix_and_blocks_escape() -> None:
    """Artifacts should stay under the configured key prefix."""
    client = FakeS3Client()
    store = S3ArtifactStore("reports", client_factory=lambda: client)
    ref = store.save_text("tenant-a/run/report.md", "# hi")

    assert ref == "s3://reports/artifacts/tenant-a/run/report.md"
    assert store.read_text("tenant-a/run/report.md") == "# hi"
    with pytest.raises(Exception, match="artifact path"):
        store.save_text("../escape.md", "nope")
