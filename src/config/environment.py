"""Runtime environment classification helpers."""

from __future__ import annotations

from typing import FrozenSet, Optional

from domain.exceptions.errors import ValidationError


LOCAL_ENVIRONMENTS: FrozenSet[str] = frozenset({"local", "test"})
EXTERNAL_PERSISTENCE_ENVIRONMENTS: FrozenSet[str] = frozenset(
    {"docker", "staging", "production"},
)
ALLOWED_ENVIRONMENTS: FrozenSet[str] = LOCAL_ENVIRONMENTS | EXTERNAL_PERSISTENCE_ENVIRONMENTS


def validate_runtime_environment(
    runtime_environment: str,
    database_url: Optional[str],
    s3_bucket: Optional[str],
    s3_endpoint_url: Optional[str],
    s3_access_key_id: Optional[str],
    s3_secret_access_key: Optional[str],
) -> None:
    """Validate environment identity and required persistence settings."""
    if runtime_environment not in ALLOWED_ENVIRONMENTS:
        raise ValidationError(
            "RUNTIME_ENVIRONMENT must be local, test, docker, staging, or production",
        )
    if runtime_environment not in EXTERNAL_PERSISTENCE_ENVIRONMENTS:
        return
    if not database_url or not database_url.strip():
        raise ValidationError("DATABASE_URL is required outside local/test")
    if not s3_bucket or not s3_bucket.strip():
        raise ValidationError("S3_BUCKET is required outside local/test")
    if runtime_environment == "docker":
        if not s3_endpoint_url or not s3_endpoint_url.strip():
            raise ValidationError("S3_ENDPOINT_URL is required for docker environment")
        if not s3_access_key_id or not s3_access_key_id.strip():
            raise ValidationError("S3_ACCESS_KEY_ID is required for docker environment")
        if not s3_secret_access_key or not s3_secret_access_key.strip():
            raise ValidationError(
                "S3_SECRET_ACCESS_KEY is required for docker environment",
            )
