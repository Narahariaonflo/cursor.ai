"""Tests for validated configuration loading."""

import json
from pathlib import Path

import pytest

from config.settings import Settings
from domain.exceptions.errors import ValidationError


def write_config(path: Path) -> None:
    """Write a complete test configuration."""
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
                "denied_path_prefixes": ["/admin", "/logout"],
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


def test_environment_overrides_config_file(tmp_path: Path) -> None:
    """Environment values override the committed defaults."""
    path = tmp_path / "defaults.json"
    write_config(path)

    settings = Settings.load(
        environ={"MAX_PAGES": "3", "LOG_LEVEL": "debug"},
        config_path=path,
    )

    assert settings.max_pages == 3
    assert settings.max_depth == 2
    assert settings.log_level == "DEBUG"


def test_invalid_integer_has_clear_error(tmp_path: Path) -> None:
    """Invalid numeric environment values fail during startup."""
    path = tmp_path / "defaults.json"
    write_config(path)

    with pytest.raises(ValidationError, match="MAX_PAGES must be an integer"):
        Settings.load(environ={"MAX_PAGES": "many"}, config_path=path)


def test_default_guardrails_are_loaded(tmp_path: Path) -> None:
    """Committed defaults produce a complete immutable guardrail profile."""
    path = tmp_path / "defaults.json"
    write_config(path)

    settings = Settings.load(environ={}, config_path=path)

    assert settings.max_pages == 10
    assert settings.max_pages_ceiling == 50
    assert settings.max_depth_ceiling == 4
    assert settings.run_timeout_seconds == 900
    assert settings.max_retries_per_operation == 2
    assert settings.retry_jitter_ratio == 0.2


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"MAX_PAGES": "0"}, "MAX_PAGES must be >= 1"),
        ({"MAX_PAGES_CEILING": "5"}, "MAX_PAGES_CEILING must be >= MAX_PAGES"),
        ({"MAX_DEPTH": "-1"}, "MAX_DEPTH must be >= 0"),
        ({"MAX_DEPTH_CEILING": "1"}, "MAX_DEPTH_CEILING must be >= MAX_DEPTH"),
        ({"RUN_TIMEOUT_SECONDS": "0"}, "RUN_TIMEOUT_SECONDS must be >= 1"),
        ({"MAX_RETRIES_PER_OPERATION": "-1"}, "MAX_RETRIES_PER_OPERATION must be >= 0"),
        ({"RETRY_JITTER_RATIO": "1.1"}, "RETRY_JITTER_RATIO must be between"),
        ({"LOG_LEVEL": "verbose"}, "LOG_LEVEL must be one of"),
        ({"APP_NAME": " "}, "APP_NAME must not be empty"),
    ],
)
def test_invalid_guardrail_relationships_fail_startup(
    tmp_path: Path,
    override: dict[str, str],
    message: str,
) -> None:
    """Unsafe or inconsistent startup values are rejected."""
    path = tmp_path / "defaults.json"
    write_config(path)

    with pytest.raises(ValidationError, match=message):
        Settings.load(environ=override, config_path=path)
