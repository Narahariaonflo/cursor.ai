"""Standard-library controlled DNS resolver adapter."""

from __future__ import annotations

import socket
from typing import Tuple

from ports.outbound.dns_resolver import DnsResolverPort


class SocketDnsResolver(DnsResolverPort):
    """Resolve all address records without connecting to the target."""

    def resolve(self, hostname: str, port: int) -> Tuple[str, ...]:
        """Return deterministic unique IPv4/IPv6 addresses."""
        records = socket.getaddrinfo(
            hostname,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
        return tuple(sorted({record[4][0] for record in records}))
