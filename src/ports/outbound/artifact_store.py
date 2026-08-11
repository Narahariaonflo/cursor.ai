"""Artifact storage ports."""

from __future__ import annotations

from typing import Protocol


class ArtifactStorePort(Protocol):
    """Store published report artifacts."""

    def save_text(self, relative_path: str, content: str) -> str:
        """Persist text content and return its storage reference."""

    def read_text(self, relative_path: str) -> str:
        """Load stored text content."""

    def save_bytes(self, relative_path: str, content: bytes) -> str:
        """Persist binary content and return its storage reference."""

    def read_bytes(self, relative_path: str) -> bytes:
        """Load stored binary content."""
