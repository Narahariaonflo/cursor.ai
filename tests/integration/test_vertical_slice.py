"""Integration tests for the first vertical slice."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

from fastapi.testclient import TestClient

from adapters.inbound.api.app import create_app
from bootstrap.container import Container


class PublicFixtureResolver:
    """Resolve the fixture hostname without public DNS."""

    def resolve(self, hostname: str, port: int) -> Tuple[str, ...]:
        """Return a documentation-only global address for policy testing."""
        return ("93.184.216.34",)


def test_create_processes_and_exposes_report(tmp_path: Path) -> None:
    """Submit should accept immediately and background processing should publish."""
    os.environ["APP_DATA_DIR"] = str(tmp_path)
    os.environ["MAX_PAGES"] = "5"
    os.environ["MAX_DEPTH"] = "2"
    with TestClient(
        create_app(Container.build(resolver=PublicFixtureResolver())),
    ) as client:
        created = client.post(
            "/api/v1/analysis-runs",
            json={
                "target_url": "https://example.com",
                "scan_preferences": {"max_pages": 1, "max_depth": 1},
            },
        )
        assert created.status_code == 202
        run_id = created.json()["run_id"]
        assert created.json()["state"] == "ACCEPTED"

        status = client.get(f"/api/v1/analysis-runs/{run_id}")
        assert status.status_code == 200
        payload = status.json()
        assert payload["state"] in {"COMPLETED", "PARTIAL"}
        assert payload["links"]["report"].endswith("/report")

        preview = client.get(f"/api/v1/analysis-runs/{run_id}/report")
        assert preview.status_code == 200
        assert preview.json()["run_id"] == run_id

        html = client.get(f"/api/v1/analysis-runs/{run_id}/reports/html")
        markdown = client.get(f"/api/v1/analysis-runs/{run_id}/reports/markdown")
        assert html.status_code == 200
        assert markdown.status_code == 200


def test_submit_and_status_errors_use_safe_contract(tmp_path: Path) -> None:
    """Request-shape and missing-run failures should use approved envelopes."""
    os.environ["APP_DATA_DIR"] = str(tmp_path)
    client = TestClient(create_app(Container.build(resolver=PublicFixtureResolver())))

    invalid = client.post(
        "/api/v1/analysis-runs",
        json={"target_url": "https://example.com", "unexpected": True},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    missing = client.get("/api/v1/analysis-runs/not-present")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RUN_NOT_FOUND"
