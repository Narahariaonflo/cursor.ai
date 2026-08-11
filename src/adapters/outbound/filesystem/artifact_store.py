"""Filesystem artifact storage adapter."""

from __future__ import annotations

from pathlib import Path

from domain.exceptions.errors import ValidationError
from ports.outbound.artifact_store import ArtifactStorePort


class FilesystemArtifactStore(ArtifactStorePort):
    """Store report artifacts under a local directory."""

    def __init__(self, root: Path) -> None:
        """Ensure the artifact root exists."""
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save_text(self, relative_path: str, content: str) -> str:
        """Persist text content and return the saved path."""
        path = self._path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def read_text(self, relative_path: str) -> str:
        """Load text content from the artifact root."""
        return self._path(relative_path).read_text(encoding="utf-8")

    def save_bytes(self, relative_path: str, content: bytes) -> str:
        """Persist binary content and return the saved path."""
        path = self._path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def read_bytes(self, relative_path: str) -> bytes:
        """Load binary content from the artifact root."""
        return self._path(relative_path).read_bytes()

    def _path(self, relative_path: str) -> Path:
        """Resolve a relative artifact path without allowing root escape."""
        candidate = (self._root / relative_path).resolve()
        if candidate == self._root or self._root not in candidate.parents:
            raise ValidationError("artifact path must remain below artifact root")
        return candidate
