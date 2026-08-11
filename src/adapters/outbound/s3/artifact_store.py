"""S3-compatible artifact store for docker/staging/production."""

from __future__ import annotations

from typing import Any, Callable, Optional

from domain.exceptions.errors import ValidationError
from ports.outbound.artifact_store import ArtifactStorePort


class S3ArtifactStore(ArtifactStorePort):
    """Store artifacts under tenant-safe object keys."""

    def __init__(
        self,
        bucket: str,
        client_factory: Optional[Callable[[], Any]] = None,
        key_prefix: str = "artifacts",
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ) -> None:
        """Store bucket identity and injectable/configurable client factory."""
        if not bucket.strip():
            raise ValidationError("S3_BUCKET must not be empty for object storage")
        self._bucket = bucket
        self._key_prefix = key_prefix.strip("/")
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._region_name = region_name
        self._client_factory = client_factory or self._build_client

    def save_text(self, relative_path: str, content: str) -> str:
        """Persist UTF-8 text and return the object URI."""
        return self.save_bytes(relative_path, content.encode("utf-8"))

    def read_text(self, relative_path: str) -> str:
        """Load UTF-8 text from object storage."""
        return self.read_bytes(relative_path).decode("utf-8")

    def save_bytes(self, relative_path: str, content: bytes) -> str:
        """Persist binary content under the configured bucket."""
        key = self._key(relative_path)
        client = self._client_factory()
        client.put_object(Bucket=self._bucket, Key=key, Body=content)
        return f"s3://{self._bucket}/{key}"

    def read_bytes(self, relative_path: str) -> bytes:
        """Load binary content from object storage."""
        key = self._key(relative_path)
        client = self._client_factory()
        response = client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def _key(self, relative_path: str) -> str:
        """Build a non-escaping object key below the artifact prefix."""
        cleaned = relative_path.replace("\\", "/").lstrip("/")
        if not cleaned or ".." in cleaned.split("/"):
            raise ValidationError("artifact path must remain below artifact root")
        return f"{self._key_prefix}/{cleaned}"

    def _build_client(self) -> Any:
        """Create a boto3 S3 client for AWS or S3-compatible endpoints."""
        try:
            import boto3
            from botocore.client import Config
        except ImportError as exc:
            raise ValidationError(
                "boto3 is required for docker/staging/production artifact storage",
            ) from exc
        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self._region_name,
            "config": Config(signature_version="s3v4"),
        }
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        if self._access_key_id and self._secret_access_key:
            kwargs["aws_access_key_id"] = self._access_key_id
            kwargs["aws_secret_access_key"] = self._secret_access_key
        return boto3.client(**kwargs)
