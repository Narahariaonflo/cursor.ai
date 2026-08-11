"""Unit tests for pre-persistence secret masking."""

from application.security.sensitive_data_masker import SensitiveDataMasker


def test_masker_redacts_configured_secret_patterns() -> None:
    """Configured secret values should be replaced before persistence."""
    masker = SensitiveDataMasker(
        (
            r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9_\-]{8,})",
            r"(?i)(password\s*[=:]\s*)(\S+)",
        ),
    )

    masked = masker.mask_text("api_key=abcd1234 password=hunter2 visible")

    assert "abcd1234" not in masked
    assert "hunter2" not in masked
    assert "api_key=[REDACTED]" in masked
    assert "password=[REDACTED]" in masked
    assert "visible" in masked


def test_masker_redacts_url_query_values() -> None:
    """Query names may remain while values are replaced."""
    masker = SensitiveDataMasker(())
    masked = masker.mask_url("https://example.com/path?token=secret&ok=1")

    assert "token=[REDACTED]" in masked
    assert "ok=[REDACTED]" in masked
    assert "secret" not in masked
