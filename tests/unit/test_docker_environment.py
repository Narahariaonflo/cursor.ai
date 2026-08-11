"""Tests for docker-backed persistence environment configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bootstrap.container import Container
from config.settings import Settings
from domain.exceptions.errors import ValidationError


def _write_config(path: Path) -> None:
    """Write a complete configuration for docker environment tests."""
    path.write_text(
        json.dumps(
            {
                "app_name": "ORCA Test",
                "runtime_environment": "test",
                "development_tenant_id": "test-tenant",
                "guardrail_policy_version": "test-v1",
                "data_dir": ".test-data",
                "database_filename": "test.sqlite3",
                "artifact_directory": "artifacts",
                "max_pages": 10,
                "max_pages_ceiling": 50,
                "max_depth": 2,
                "max_depth_ceiling": 4,
                "run_timeout_seconds": 900,
                "max_retries_per_operation": 2,
                "retry_base_delay_ms": 500,
                "retry_max_delay_ms": 5000,
                "retry_jitter_ratio": 0.2,
                "max_url_length_bytes": 2048,
                "max_discovered_urls": 200,
                "max_agent_tasks_in_flight_per_run": 8,
                "page_navigation_timeout_seconds": 30,
                "http_probe_timeout_seconds": 10,
                "max_dom_chars": 200000,
                "max_html_fetch_bytes": 500000,
                "allowed_target_ports": [80, 443],
                "denied_target_domains": [],
                "denied_path_prefixes": ["/admin"],
                "tracking_query_parameters": ["utm_source"],
                "secret_mask_patterns": ["(?i)(api[_-]?key\\s*[=:]\\s*)(\\S+)"],
                "psi_enabled": False,
                "performance_thresholds": {"largest_contentful_paint": 2500},
                "latency_thresholds_ms": {"ttfb": 800},
                "resource_limits": {"pages": 50, "browser_minutes": 20},
                "log_level": "INFO",
            },
        ),
        encoding="utf-8",
    )


def test_docker_environment_requires_minio_endpoint_and_keys(tmp_path: Path) -> None:
    """Docker mode must fail closed without MinIO connection settings."""
    path = tmp_path / "defaults.json"
    _write_config(path)

    with pytest.raises(ValidationError, match="S3_ENDPOINT_URL"):
        Settings.load(
            environ={
                "RUNTIME_ENVIRONMENT": "docker",
                "DATABASE_URL": "postgresql://orca:orca@localhost:5432/orca",
                "S3_BUCKET": "orca-artifacts",
            },
            config_path=path,
        )


def test_docker_persistence_selects_postgres_and_s3(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Docker composition should wire PostgreSQL and S3-compatible storage."""
    path = tmp_path / "defaults.json"
    _write_config(path)
    settings = Settings.load(
        environ={
            "RUNTIME_ENVIRONMENT": "docker",
            "DATABASE_URL": "postgresql://orca:orca@localhost:5432/orca",
            "S3_BUCKET": "orca-artifacts",
            "S3_ENDPOINT_URL": "http://localhost:9000",
            "S3_ACCESS_KEY_ID": "orca_minio",
            "S3_SECRET_ACCESS_KEY": "orca_minio_dev_only",
            "S3_REGION": "us-east-1",
            "APP_DATA_DIR": str(tmp_path),
        },
        config_path=path,
    )
    captured: dict[str, Any] = {}

    class FakePostgres:
        def __init__(self, database_url: str) -> None:
            captured["database_url"] = database_url

    class FakeS3:
        def __init__(self, **kwargs: Any) -> None:
            captured["s3"] = kwargs

    monkeypatch.setattr(
        "bootstrap.container.PostgresScanRepository",
        FakePostgres,
    )
    monkeypatch.setattr(
        "bootstrap.container.S3ArtifactStore",
        FakeS3,
    )

    repository, artifact_store = Container._build_persistence(settings)

    assert isinstance(repository, FakePostgres)
    assert isinstance(artifact_store, FakeS3)
    assert captured["database_url"].startswith("postgresql://")
    assert captured["s3"]["endpoint_url"] == "http://localhost:9000"
    assert captured["s3"]["bucket"] == "orca-artifacts"
