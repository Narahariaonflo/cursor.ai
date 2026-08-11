"""PostgreSQL tenant-scoped analysis-run repository."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from domain.entities.analysis_run import AnalysisRun
from domain.exceptions.errors import ValidationError
from ports.outbound.repository import ScanRepositoryPort


class PostgresScanRepository(ScanRepositoryPort):
    """Persist runs in PostgreSQL with composite tenant/run identity."""

    def __init__(
        self,
        database_url: str,
        connect: Optional[Callable[[str], Any]] = None,
    ) -> None:
        """Store connection URL and optional injectable connector."""
        if not database_url.strip():
            raise ValidationError("DATABASE_URL must not be empty for production")
        self._database_url = database_url
        self._connect = connect or self._default_connect
        self._initialize()

    def save_run(self, run: AnalysisRun) -> None:
        """Upsert one tenant-scoped run payload."""
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO analysis_runs(tenant_id, run_id, payload)
                    VALUES (%s, %s, %s::jsonb)
                    ON CONFLICT (tenant_id, run_id)
                    DO UPDATE SET payload = EXCLUDED.payload
                    """,
                    (run.tenant_id, run.run_id, json.dumps(run.to_record())),
                )
            connection.commit()

    def get_run(self, tenant_id: str, run_id: str) -> Optional[AnalysisRun]:
        """Load one run only when tenant and run identifiers both match."""
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT payload FROM analysis_runs
                    WHERE tenant_id = %s AND run_id = %s
                    """,
                    (tenant_id, run_id),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        return AnalysisRun.from_record(payload)

    def _initialize(self) -> None:
        """Ensure the tenant-scoped table exists."""
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_runs (
                        tenant_id TEXT NOT NULL,
                        run_id TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        PRIMARY KEY (tenant_id, run_id)
                    )
                    """,
                )
            connection.commit()

    @staticmethod
    def _default_connect(database_url: str) -> Any:
        """Connect through psycopg when the production extra is installed."""
        try:
            import psycopg
        except ImportError as exc:
            raise ValidationError(
                "psycopg is required for staging/production persistence",
            ) from exc
        return psycopg.connect(database_url)
