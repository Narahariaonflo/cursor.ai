"""Controlled DNS resolution port."""

from __future__ import annotations

from typing import Protocol, Tuple


class DnsResolverPort(Protocol):
    """Resolve all addresses for one canonical host and port."""

    def resolve(self, hostname: str, port: int) -> Tuple[str, ...]:
        """Return unique textual IPv4/IPv6 addresses."""
