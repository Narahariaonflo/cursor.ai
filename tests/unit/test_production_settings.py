"""Settings validation for staging/production readiness."""

import json
from pathlib import Path

import pytest

from config.settings import Settings
from domain.exceptions.errors import ValidationError


def _write_config(path: Path) -> None:
    """Write a complete configuration for production validation tests."""
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


def test_production_requires_database_and_bucket(tmp_path: Path) -> None:
    """Staging/production startup must require external persistence config."""
    path = tmp_path / "defaults.json"
    _write_config(path)

    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings.load(
            environ={"RUNTIME_ENVIRONMENT": "production"},
            config_path=path,
        )

    settings = Settings.load(
        environ={
            "RUNTIME_ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://example/orca",
            "S3_BUCKET": "orca-artifacts",
            "S3_REGION": "us-east-1",
        },
        config_path=path,
    )
    assert settings.database_url is not None
    assert settings.s3_bucket == "orca-artifacts"
