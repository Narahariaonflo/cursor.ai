"""Structured logger security tests."""

import json

from pytest import CaptureFixture

from adapters.outbound.observability.structured_logger import JsonStructuredLogger


def test_sensitive_context_is_redacted(capsys: CaptureFixture[str]) -> None:
    """Sensitive fields never appear in emitted structured logs."""
    logger = JsonStructuredLogger("orca-test-logger", "INFO")

    logger.info(
        "test.event",
        {"scan_run_id": "run-1", "authorization_token": "do-not-log"},
    )

    output = capsys.readouterr().err
    payload = json.loads(output)
    assert payload["scan_run_id"] == "run-1"
    assert payload["authorization_token"] == "[REDACTED]"
    assert "do-not-log" not in output


def test_all_public_log_levels_emit_json(capsys: CaptureFixture[str]) -> None:
    """Debug, warning, and error methods preserve the structured contract."""
    logger = JsonStructuredLogger("orca-test-levels", "DEBUG")

    logger.debug("debug.event", {"tenant_id": "tenant-a"})
    logger.warning("warning.event", {"tenant_id": "tenant-a"})
    logger.error("error.event", {"tenant_id": "tenant-a"})

    records = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    assert [record["level"] for record in records] == ["DEBUG", "WARNING", "ERROR"]
    assert all(record["tenant_id"] == "tenant-a" for record in records)
