"""Validated application configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import FrozenSet, Mapping, Optional, Tuple

from config.environment import validate_runtime_environment
from config.loading import read_config, read_float, read_int
from domain.exceptions.errors import ValidationError


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "defaults.json"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings loaded from config and environment."""

    app_name: str
    runtime_environment: str
    development_tenant_id: str
    guardrail_policy_version: str
    database_path: Path
    artifact_root: Path
    database_url: Optional[str]
    s3_bucket: Optional[str]
    s3_endpoint_url: Optional[str]
    s3_access_key_id: Optional[str]
    s3_secret_access_key: Optional[str]
    s3_region: str
    max_pages: int
    max_pages_ceiling: int
    max_depth: int
    max_depth_ceiling: int
    run_timeout_seconds: int
    max_retries_per_operation: int
    retry_base_delay_ms: int
    retry_max_delay_ms: int
    retry_jitter_ratio: float
    max_url_length_bytes: int
    max_discovered_urls: int
    max_agent_tasks_in_flight_per_run: int
    page_navigation_timeout_seconds: int
    http_probe_timeout_seconds: int
    max_dom_chars: int
    max_html_fetch_bytes: int
    allowed_target_ports: FrozenSet[int]
    denied_target_domains: FrozenSet[str]
    denied_path_prefixes: FrozenSet[str]
    tracking_query_parameters: FrozenSet[str]
    secret_mask_patterns: Tuple[str, ...]
    psi_enabled: bool
    performance_thresholds: Mapping[str, float]
    latency_thresholds_ms: Mapping[str, float]
    resource_limits: Mapping[str, float]
    log_level: str

    @classmethod
    def load(
        cls,
        environ: Optional[Mapping[str, str]] = None,
        config_path: Optional[Path] = None,
    ) -> "Settings":
        """Load validated settings from a JSON config with environment overrides."""
        env = environ if environ is not None else os.environ
        path = config_path or Path(env.get("APP_CONFIG_FILE", _DEFAULT_CONFIG_PATH))
        config = read_config(path)
        data_root = Path(env.get("APP_DATA_DIR", str(config["data_dir"])))
        settings = cls(
            app_name=env.get("APP_NAME", str(config["app_name"])),
            runtime_environment=env.get(
                "RUNTIME_ENVIRONMENT",
                str(config["runtime_environment"]),
            ).lower(),
            development_tenant_id=env.get(
                "DEVELOPMENT_TENANT_ID",
                str(config["development_tenant_id"]),
            ),
            guardrail_policy_version=env.get(
                "GUARDRAIL_POLICY_VERSION",
                str(config["guardrail_policy_version"]),
            ),
            database_path=data_root / str(config["database_filename"]),
            artifact_root=data_root / str(config["artifact_directory"]),
            database_url=env.get("DATABASE_URL"),
            s3_bucket=env.get("S3_BUCKET"),
            s3_endpoint_url=env.get("S3_ENDPOINT_URL"),
            s3_access_key_id=env.get("S3_ACCESS_KEY_ID"),
            s3_secret_access_key=env.get("S3_SECRET_ACCESS_KEY"),
            s3_region=env.get("S3_REGION", "us-east-1"),
            max_pages=read_int(env, "MAX_PAGES", config["max_pages"]),
            max_pages_ceiling=read_int(
                env,
                "MAX_PAGES_CEILING",
                config["max_pages_ceiling"],
            ),
            max_depth=read_int(env, "MAX_DEPTH", config["max_depth"]),
            max_depth_ceiling=read_int(
                env,
                "MAX_DEPTH_CEILING",
                config["max_depth_ceiling"],
            ),
            run_timeout_seconds=read_int(
                env,
                "RUN_TIMEOUT_SECONDS",
                config["run_timeout_seconds"],
            ),
            max_retries_per_operation=read_int(
                env,
                "MAX_RETRIES_PER_OPERATION",
                config["max_retries_per_operation"],
            ),
            retry_base_delay_ms=read_int(
                env,
                "RETRY_BASE_DELAY_MS",
                config["retry_base_delay_ms"],
            ),
            retry_max_delay_ms=read_int(
                env,
                "RETRY_MAX_DELAY_MS",
                config["retry_max_delay_ms"],
            ),
            retry_jitter_ratio=read_float(
                env,
                "RETRY_JITTER_RATIO",
                config["retry_jitter_ratio"],
            ),
            max_url_length_bytes=read_int(
                env,
                "MAX_URL_LENGTH_BYTES",
                config["max_url_length_bytes"],
            ),
            max_discovered_urls=read_int(
                env,
                "MAX_DISCOVERED_URLS",
                config["max_discovered_urls"],
            ),
            max_agent_tasks_in_flight_per_run=read_int(
                env,
                "MAX_AGENT_TASKS_IN_FLIGHT_PER_RUN",
                config["max_agent_tasks_in_flight_per_run"],
            ),
            page_navigation_timeout_seconds=read_int(
                env,
                "PAGE_NAVIGATION_TIMEOUT_SECONDS",
                config["page_navigation_timeout_seconds"],
            ),
            http_probe_timeout_seconds=read_int(
                env,
                "HTTP_PROBE_TIMEOUT_SECONDS",
                config["http_probe_timeout_seconds"],
            ),
            max_dom_chars=read_int(
                env,
                "MAX_DOM_CHARS",
                config["max_dom_chars"],
            ),
            max_html_fetch_bytes=read_int(
                env,
                "MAX_HTML_FETCH_BYTES",
                config["max_html_fetch_bytes"],
            ),
            allowed_target_ports=frozenset(
                int(port) for port in config["allowed_target_ports"]
            ),
            denied_target_domains=frozenset(
                str(domain).lower() for domain in config["denied_target_domains"]
            ),
            denied_path_prefixes=frozenset(
                str(prefix).lower() for prefix in config["denied_path_prefixes"]
            ),
            tracking_query_parameters=frozenset(
                str(name).lower() for name in config["tracking_query_parameters"]
            ),
            secret_mask_patterns=tuple(
                str(pattern) for pattern in config["secret_mask_patterns"]
            ),
            psi_enabled=str(
                env.get("PSI_ENABLED", config["psi_enabled"]),
            ).lower()
            in {"1", "true", "yes"},
            performance_thresholds={
                str(name): float(value)
                for name, value in config["performance_thresholds"].items()
            },
            latency_thresholds_ms={
                str(name): float(value)
                for name, value in config["latency_thresholds_ms"].items()
            },
            resource_limits={
                str(name): float(value)
                for name, value in config["resource_limits"].items()
            },
            log_level=env.get("LOG_LEVEL", str(config["log_level"])).upper(),
        )
        settings.validate()
        return settings

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings using the process environment."""
        return cls.load()

    def validate(self) -> None:
        """Validate configuration invariants before dependency construction."""
        if not self.app_name.strip():
            raise ValidationError("APP_NAME must not be empty")
        validate_runtime_environment(
            self.runtime_environment,
            self.database_url,
            self.s3_bucket,
            self.s3_endpoint_url,
            self.s3_access_key_id,
            self.s3_secret_access_key,
        )
        if not self.s3_region.strip():
            raise ValidationError("S3_REGION must not be empty")
        if not self.development_tenant_id.strip():
            raise ValidationError("DEVELOPMENT_TENANT_ID must not be empty")
        if not self.guardrail_policy_version.strip():
            raise ValidationError("GUARDRAIL_POLICY_VERSION must not be empty")
        if self.max_pages < 1:
            raise ValidationError("MAX_PAGES must be >= 1")
        if self.max_pages_ceiling < self.max_pages:
            raise ValidationError("MAX_PAGES_CEILING must be >= MAX_PAGES")
        if self.max_depth < 0:
            raise ValidationError("MAX_DEPTH must be >= 0")
        if self.max_depth_ceiling < self.max_depth:
            raise ValidationError("MAX_DEPTH_CEILING must be >= MAX_DEPTH")
        if self.run_timeout_seconds < 1:
            raise ValidationError("RUN_TIMEOUT_SECONDS must be >= 1")
        if self.max_retries_per_operation < 0:
            raise ValidationError("MAX_RETRIES_PER_OPERATION must be >= 0")
        if self.retry_base_delay_ms < 1:
            raise ValidationError("RETRY_BASE_DELAY_MS must be >= 1")
        if self.retry_max_delay_ms < self.retry_base_delay_ms:
            raise ValidationError("RETRY_MAX_DELAY_MS must be >= RETRY_BASE_DELAY_MS")
        if not 0.0 <= self.retry_jitter_ratio <= 1.0:
            raise ValidationError("RETRY_JITTER_RATIO must be between 0.0 and 1.0")
        if self.max_url_length_bytes < 1:
            raise ValidationError("MAX_URL_LENGTH_BYTES must be >= 1")
        if self.max_discovered_urls < 1:
            raise ValidationError("MAX_DISCOVERED_URLS must be >= 1")
        if self.max_agent_tasks_in_flight_per_run < 1:
            raise ValidationError("MAX_AGENT_TASKS_IN_FLIGHT_PER_RUN must be >= 1")
        if self.page_navigation_timeout_seconds < 1:
            raise ValidationError("PAGE_NAVIGATION_TIMEOUT_SECONDS must be >= 1")
        if self.http_probe_timeout_seconds < 1:
            raise ValidationError("HTTP_PROBE_TIMEOUT_SECONDS must be >= 1")
        if self.max_dom_chars < 1:
            raise ValidationError("MAX_DOM_CHARS must be >= 1")
        if self.max_html_fetch_bytes < 1:
            raise ValidationError("MAX_HTML_FETCH_BYTES must be >= 1")
        if not self.allowed_target_ports or any(
            port < 1 or port > 65535 for port in self.allowed_target_ports
        ):
            raise ValidationError("allowed_target_ports must contain valid ports")
        if any(not prefix.startswith("/") for prefix in self.denied_path_prefixes):
            raise ValidationError("denied_path_prefixes must start with '/'")
        if not self.secret_mask_patterns:
            raise ValidationError("secret_mask_patterns must not be empty")
        if not self.performance_thresholds:
            raise ValidationError("performance_thresholds must not be empty")
        if not self.latency_thresholds_ms:
            raise ValidationError("latency_thresholds_ms must not be empty")
        if not self.resource_limits or any(
            value < 0 for value in self.resource_limits.values()
        ):
            raise ValidationError("resource_limits must be non-empty and non-negative")
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_levels:
            raise ValidationError(f"LOG_LEVEL must be one of {sorted(valid_levels)}")
