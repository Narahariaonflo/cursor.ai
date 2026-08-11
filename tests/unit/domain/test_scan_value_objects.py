"""Boundary tests for scan preferences and target URLs."""

import pytest

from domain.exceptions.errors import ValidationError
from domain.value_objects.scan import ScanPreferences, TargetUrl


@pytest.mark.parametrize(
    ("max_pages", "max_depth"),
    [(1, 0), (10, 2), (50, 4)],
)
def test_scan_preferences_accept_domain_valid_values(
    max_pages: int,
    max_depth: int,
) -> None:
    """Positive page counts and non-negative depths are domain-valid."""
    preferences = ScanPreferences(max_pages=max_pages, max_depth=max_depth)

    assert preferences.max_pages == max_pages
    assert preferences.max_depth == max_depth


@pytest.mark.parametrize(
    ("max_pages", "max_depth", "message"),
    [(0, 0, "max_pages"), (1, -1, "max_depth")],
)
def test_scan_preferences_reject_invalid_values(
    max_pages: int,
    max_depth: int,
    message: str,
) -> None:
    """Invalid primitive bounds are rejected before policy evaluation."""
    with pytest.raises(ValidationError, match=message):
        ScanPreferences(max_pages=max_pages, max_depth=max_depth)


@pytest.mark.parametrize(
    "value",
    ["https://example.com/", "http://example.com/path"],
)
def test_target_url_accepts_absolute_http_urls(value: str) -> None:
    """Only absolute HTTP(S) targets are domain-valid."""
    assert TargetUrl(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "example.com", "ftp://example.com/file", "/relative"],
)
def test_target_url_rejects_unsupported_values(value: str) -> None:
    """Unsupported schemes and relative targets are rejected."""
    with pytest.raises(ValidationError, match="absolute http"):
        TargetUrl(value)
