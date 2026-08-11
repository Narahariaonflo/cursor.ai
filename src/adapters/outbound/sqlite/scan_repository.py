"""SQLite repository adapter."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from domain.entities.analysis_run import AnalysisRun
from ports.outbound.repository import ScanRepositoryPort


class SqliteScanRepository(ScanRepositoryPort):
    """Persist scan runs in SQLite as JSON payloads."""

    def __init__(self, database_path: Path) -> None:
        """Initialize the repository and ensure the schema exists."""
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_run(self, run: AnalysisRun) -> None:
        """Persist or replace a run payload."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analysis_runs(tenant_id, run_id, payload)
                VALUES (?, ?, ?)
                """,
                (run.tenant_id, run.run_id, json.dumps(run.to_record())),
            )

    def get_run(self, tenant_id: str, run_id: str) -> Optional[AnalysisRun]:
        """Load a run by tenant and identifier."""
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT payload FROM analysis_runs
                WHERE tenant_id = ? AND run_id = ?
                """,
                (tenant_id, run_id),
            ).fetchone()
        if row is None:
            return None
        return AnalysisRun.from_record(json.loads(row[0]))

    def _initialize(self) -> None:
        """Create the backing table when missing."""
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    tenant_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, run_id)
                )
                """,
            )
