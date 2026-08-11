"""SSRF target-policy unit tests with a controlled resolver."""

from __future__ import annotations

from typing import Dict, Tuple

import pytest

from application.policy_services.target_policy import TargetPolicyService


class FakeResolver:
    """Return configured DNS answers without network access."""

    def __init__(self, answers: Dict[str, Tuple[str, ...]]) -> None:
        """Store answers by canonical hostname."""
        self._answers = answers
        self.calls: list[Tuple[str, int]] = []

    def resolve(self, hostname: str, port: int) -> Tuple[str, ...]:
        """Return configured answers or simulate resolution failure."""
        self.calls.append((hostname, port))
        if hostname not in self._answers:
            raise OSError("not resolved")
        return self._answers[hostname]


def make_policy(resolver: FakeResolver) -> TargetPolicyService:
    """Build policy with test-controlled configuration."""
    return TargetPolicyService(
        resolver=resolver,
        allowed_ports=frozenset({80, 443}),
        denied_domains=frozenset({"blocked.example"}),
        max_url_length_bytes=100,
    )


def test_public_target_returns_pinned_approved_addresses() -> None:
    """All public A/AAAA answers are normalized into the allow decision."""
    resolver = FakeResolver({"example.com": ("93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946")})

    decision = make_policy(resolver).evaluate("https://example.com/path")

    assert decision.allowed is True
    assert decision.code == "TARGET_ALLOWED"
    assert len(decision.approved_addresses) == 2
    assert resolver.calls == [("example.com", 443)]


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "fc00::1",
        "::ffff:127.0.0.1",
        "192.0.2.1",
    ],
)
def test_non_public_dns_answer_is_denied(address: str) -> None:
    """Private, metadata, mapped, loopback, and reserved answers fail closed."""
    policy = make_policy(FakeResolver({"example.com": (address,)}))

    decision = policy.evaluate("https://example.com")

    assert decision.allowed is False
    assert decision.code == "NON_PUBLIC_ADDRESS"


@pytest.mark.parametrize(
    ("url", "code"),
    [
        ("ftp://example.com", "UNSUPPORTED_TARGET"),
        ("https://user:pass@example.com", "USERINFO_FORBIDDEN"),
        ("https://example.com/path#fragment", "FRAGMENT_FORBIDDEN"),
        ("https://example.com:8443", "PORT_NOT_ALLOWED"),
        ("https://localhost", "DOMAIN_NOT_ALLOWED"),
        ("https://service.local", "DOMAIN_NOT_ALLOWED"),
        ("https://blocked.example", "DOMAIN_NOT_ALLOWED"),
        ("https://sub.blocked.example", "DOMAIN_NOT_ALLOWED"),
        ("https://example.com:bad", "MALFORMED_URL"),
    ],
)
def test_url_policy_denials_happen_before_dns(url: str, code: str) -> None:
    """Malformed or denied URL forms never invoke resolution."""
    resolver = FakeResolver({})

    decision = make_policy(resolver).evaluate(url)

    assert decision.code == code
    assert resolver.calls == []


def test_dns_failure_and_invalid_answer_fail_closed() -> None:
    """Resolver failures and malformed answers are terminal denials."""
    assert make_policy(FakeResolver({})).evaluate("https://example.com").code == "DNS_RESOLUTION_FAILED"
    decision = make_policy(FakeResolver({"example.com": ("not-an-ip",)})).evaluate(
        "https://example.com",
    )
    assert decision.code == "INVALID_DNS_ANSWER"

    empty = make_policy(FakeResolver({"example.com": ()})).evaluate("https://example.com")
    assert empty.code == "DNS_RESOLUTION_FAILED"


def test_invalid_internationalized_hostname_fails_closed() -> None:
    """Hostname canonicalization errors never reach DNS."""
    resolver = FakeResolver({})

    decision = make_policy(resolver).evaluate("https://\ud800.example")

    assert decision.code == "INVALID_HOST"
    assert resolver.calls == []


def test_url_length_is_checked_before_parsing_or_dns() -> None:
    """Oversized input consumes no resolver resources."""
    resolver = FakeResolver({})

    decision = make_policy(resolver).evaluate("https://example.com/" + ("x" * 100))

    assert decision.code == "URL_TOO_LONG"
    assert resolver.calls == []
