"""SSRF-safe target policy service."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import FrozenSet, Union
from urllib.parse import urlsplit

from domain.value_objects.operational import PolicyDecision
from ports.outbound.dns_resolver import DnsResolverPort


class TargetPolicyService:
    """Validate URL syntax, DNS answers, and public-address policy."""

    def __init__(
        self,
        resolver: DnsResolverPort,
        allowed_ports: FrozenSet[int],
        denied_domains: FrozenSet[str],
        max_url_length_bytes: int,
    ) -> None:
        """Store injected policy and controlled resolver."""
        self._resolver = resolver
        self._allowed_ports = allowed_ports
        self._denied_domains = denied_domains
        self._max_url_length_bytes = max_url_length_bytes

    def evaluate(self, target_url: str) -> PolicyDecision:
        """Return a fail-closed decision without connecting to the target."""
        try:
            target_length = len(target_url.encode("utf-8"))
        except UnicodeError:
            return self._deny("INVALID_HOST", "target hostname is invalid")
        if target_length > self._max_url_length_bytes:
            return self._deny("URL_TOO_LONG", "target URL exceeds configured length")

        try:
            parsed = urlsplit(target_url)
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        except ValueError:
            return self._deny("MALFORMED_URL", "target URL is malformed")

        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return self._deny("UNSUPPORTED_TARGET", "only absolute HTTP(S) URLs are allowed")
        if parsed.username is not None or parsed.password is not None:
            return self._deny("USERINFO_FORBIDDEN", "URL user information is not allowed")
        if parsed.fragment:
            return self._deny("FRAGMENT_FORBIDDEN", "URL fragments are not allowed")
        if port not in self._allowed_ports:
            return self._deny("PORT_NOT_ALLOWED", "target port is not allowed")

        try:
            hostname = parsed.hostname.encode("idna").decode("ascii").lower().rstrip(".")
        except UnicodeError:
            return self._deny("INVALID_HOST", "target hostname is invalid")
        if self._is_denied_domain(hostname):
            return self._deny("DOMAIN_NOT_ALLOWED", "target hostname is not allowed")

        try:
            addresses = self._resolver.resolve(hostname, port)
        except OSError:
            return self._deny("DNS_RESOLUTION_FAILED", "target hostname could not be resolved")
        if not addresses:
            return self._deny("DNS_RESOLUTION_FAILED", "target hostname has no addresses")

        approved: list[str] = []
        for raw_address in addresses:
            try:
                address = ip_address(raw_address)
            except ValueError:
                return self._deny("INVALID_DNS_ANSWER", "resolver returned an invalid address")
            normalized = self._normalize_mapped_address(address)
            if not normalized.is_global:
                return self._deny("NON_PUBLIC_ADDRESS", "target resolves to a non-public address")
            approved.append(str(normalized))

        return PolicyDecision(
            allowed=True,
            code="TARGET_ALLOWED",
            approved_addresses=tuple(sorted(set(approved))),
        )

    def _is_denied_domain(self, hostname: str) -> bool:
        """Return whether a host equals or is below a denied domain."""
        if hostname == "localhost" or hostname.endswith(".local"):
            return True
        return any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in self._denied_domains
        )

    @staticmethod
    def _normalize_mapped_address(
        address: Union[IPv4Address, IPv6Address],
    ) -> Union[IPv4Address, IPv6Address]:
        """Normalize IPv4-mapped IPv6 before public-address checks."""
        if isinstance(address, IPv6Address) and address.ipv4_mapped is not None:
            return address.ipv4_mapped
        return address

    @staticmethod
    def _deny(code: str, reason: str) -> PolicyDecision:
        """Build a safe terminal deny decision."""
        return PolicyDecision(allowed=False, code=code, reason=reason)
