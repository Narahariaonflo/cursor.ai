"""Configuration file and environment primitive loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from domain.exceptions.errors import ValidationError


REQUIRED_CONFIG_KEYS = {
    "app_name",
    "runtime_environment",
    "development_tenant_id",
    "guardrail_policy_version",
    "data_dir",
    "database_filename",
    "artifact_directory",
    "max_pages",
    "max_pages_ceiling",
    "max_depth",
    "max_depth_ceiling",
    "run_timeout_seconds",
    "max_retries_per_operation",
    "retry_base_delay_ms",
    "retry_max_delay_ms",
    "retry_jitter_ratio",
    "max_url_length_bytes",
    "max_discovered_urls",
    "max_agent_tasks_in_flight_per_run",
    "page_navigation_timeout_seconds",
    "http_probe_timeout_seconds",
    "max_dom_chars",
    "max_html_fetch_bytes",
    "allowed_target_ports",
    "denied_target_domains",
    "denied_path_prefixes",
    "tracking_query_parameters",
    "secret_mask_patterns",
    "psi_enabled",
    "performance_thresholds",
    "latency_thresholds_ms",
    "resource_limits",
    "log_level",
}


def read_config(path: Path) -> dict[str, Any]:
    """Read and validate the required JSON configuration file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid configuration JSON: {path}") from exc
    missing = REQUIRED_CONFIG_KEYS.difference(payload)
    if missing:
        raise ValidationError(f"missing configuration keys: {sorted(missing)}")
    return payload


def read_int(env: Mapping[str, str], name: str, fallback: object) -> int:
    """Read an integer setting with a clear validation failure."""
    raw_value = env.get(name, str(fallback))
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValidationError(f"{name} must be an integer") from exc


def read_float(env: Mapping[str, str], name: str, fallback: object) -> float:
    """Read a floating-point setting with a clear validation failure."""
    raw_value = env.get(name, str(fallback))
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValidationError(f"{name} must be a number") from exc
