"""HTTP link status and redirect-chain adapter."""

from __future__ import annotations

from typing import Callable, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ports.outbound.link_check import LinkCheckPort
from ports.outbound.policy import TargetPolicyPort
from ports.outbound.results import LinkCheckResult


class HttpLinkCheckAdapter(LinkCheckPort):
    """Probe approved links with bounded redirects."""

    def __init__(
        self,
        target_policy: TargetPolicyPort,
        timeout_seconds: int,
        max_redirects: int,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        """Store policy, bounds, and injectable opener."""
        self._target_policy = target_policy
        self._timeout_seconds = timeout_seconds
        self._max_redirects = max_redirects
        self._opener = opener

    def check(self, source_url: str, target_url: str) -> LinkCheckResult:
        """Return status and redirect evidence for one target URL."""
        decision = self._target_policy.evaluate(target_url)
        if not decision.allowed:
            return LinkCheckResult(
                source_url=source_url,
                target_url=target_url,
                status_code=0,
                redirect_chain=(),
            )
        chain: List[str] = [target_url]
        current = target_url
        for _ in range(self._max_redirects + 1):
            request = Request(
                current,
                method="HEAD",
                headers={"User-Agent": "orca-link-check/1.0"},
            )
            try:
                with self._opener(request, timeout=self._timeout_seconds) as response:
                    status = getattr(response, "status", 200)
                    headers = getattr(response, "headers", {})
                    location = headers.get("Location") if headers else None
                    if location and 300 <= int(status) < 400:
                        current = location
                        chain.append(current)
                        continue
                    return LinkCheckResult(
                        source_url=source_url,
                        target_url=target_url,
                        status_code=int(status),
                        redirect_chain=tuple(chain),
                    )
            except HTTPError as exc:
                return LinkCheckResult(
                    source_url=source_url,
                    target_url=target_url,
                    status_code=int(exc.code),
                    redirect_chain=tuple(chain),
                )
            except (URLError, TimeoutError, OSError, ValueError):
                return LinkCheckResult(
                    source_url=source_url,
                    target_url=target_url,
                    status_code=0,
                    redirect_chain=tuple(chain),
                )
        return LinkCheckResult(
            source_url=source_url,
            target_url=target_url,
            status_code=0,
            redirect_chain=tuple(chain),
        )
