# API Specification
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Document ID | ORCA-API-006 |
| Version | 0.1 |
| Status | Approved |
| Scope | Read-only Website Analysis MVP |
| Upstream | `02_User_Stories.md`, `04_High_Level_Design.md`, `05_Low_Level_Design.md` (Approved) |
| Downstream | `07_Agent_Architecture.md`, `08_Database_Design.md`, `10_Security.md`, `13_Testing_Strategy.md` |
| Last updated | 2026-08-06 |

---

## 1. Purpose and decisions

This document defines the public HTTP API for submitting an analysis, tracking progress, previewing results, and downloading immutable HTML or Markdown reports.

1. MVP uses a versioned JSON API under `/api/v1`.
2. Scan execution is asynchronous; creation returns `202 Accepted`.
3. The minimal UI is a thin API consumer.
4. Tenant identity comes from authenticated server context, never a request `tenant_id`.
5. Raw evidence packages and general artifact-download APIs are out of scope.
6. No Git, patch, PR, deploy, or website-mutation routes exist.

Identity-provider details belong to `10_Security.md`; limit defaults belong to `11_Guardrails.md`.

---

## 2. Conventions

| Concern | Contract |
|---|---|
| API media type | `application/json` |
| Versioning | URI: `/api/v1` |
| IDs | Server-generated UUID strings |
| Timestamps | UTC ISO 8601 |
| Fields | `snake_case`; unknown request fields rejected |
| Authentication | `Authorization: Bearer <token>`; validation defined in Security |
| Correlation | Response `X-Correlation-ID`; valid client value may be propagated |
| Downloads | `text/html` or `text/markdown` plus attachment disposition |

All tenant data requires authorization against authenticated tenant context and requested `run_id`.

### 2.1 Enumerations

| Type | Values |
|---|---|
| Run state | `ACCEPTED`, `VALIDATING`, `PLANNING`, `RUNNING`, `AGGREGATING`, `RENDERING`, `COMPLETED`, `PARTIAL`, `FAILED` |
| Device | `desktop`, `mobile` |
| Agent | `seo`, `performance`, `latency`, `broken_link`, `console`, `html`, `security`, `accessibility` |
| Severity | `critical`, `high`, `medium`, `low`, `info` |
| Report format | `html`, `markdown` |
| Evidence kind | `metric`, `response`, `dom`, `console`, `screenshot`, `tool_output` |

Reports are available only for terminal states `COMPLETED` and `PARTIAL`.

---

## 3. Endpoint summary

| Method | Path | Purpose | Success |
|---|---|---|---|
| `POST` | `/api/v1/analysis-runs` | Submit analysis | `202` |
| `GET` | `/api/v1/analysis-runs/{run_id}` | Get state/progress | `200` |
| `GET` | `/api/v1/analysis-runs/{run_id}/report` | Preview report | `200` |
| `GET` | `/api/v1/analysis-runs/{run_id}/reports/{format}` | Download report | `200` |

Cancellation, run listing/deletion, and raw artifacts are not defined for MVP.

---

## 4. Submit analysis

### `POST /api/v1/analysis-runs`

```json
{
  "target_url": "https://example.com/",
  "scan_preferences": {
    "max_pages": 10,
    "max_depth": 2,
    "device_profile": "desktop",
    "enabled_agents": ["seo", "performance", "broken_link"],
    "check_external_links": true
  }
}
```

| Field | Required | Validation |
|---|---|---|
| `target_url` | Yes | Absolute HTTP(S); policy validation occurs before any fetch |
| `scan_preferences` | No | Omitted properties use approved server config |
| `max_pages` | No | Positive integer within guardrail |
| `max_depth` | No | Non-negative integer within guardrail |
| `device_profile` | No | Enumeration value |
| `enabled_agents` | No | Unique non-empty supported subset |
| `check_external_links` | No | Boolean; default defined by Guardrails |

`202 Accepted`:

```json
{
  "run_id": "8fd489b8-7232-44fa-a95c-93baf6f265c3",
  "state": "ACCEPTED",
  "target_url": "https://example.com/",
  "applied_preferences": {"max_pages": 10, "max_depth": 2},
  "created_at": "2026-08-06T10:30:00Z",
  "links": {"status": "/api/v1/analysis-runs/8fd489b8-7232-44fa-a95c-93baf6f265c3"}
}
```

The response returns effective preferences. Acceptance does not imply target approval or scan success.

---

## 5. Get run status

### `GET /api/v1/analysis-runs/{run_id}`

```json
{
  "run_id": "8fd489b8-7232-44fa-a95c-93baf6f265c3",
  "state": "RUNNING",
  "progress": {
    "pages_planned": 10,
    "pages_completed": 4,
    "agent_tasks_planned": 30,
    "agent_tasks_completed": 11,
    "findings_count": 7
  },
  "coverage": {
    "pages_discovered": 18,
    "pages_eligible": 10,
    "pages_scanned": 4
  },
  "limitations": [],
  "agent_failures": [],
  "failure": null,
  "created_at": "2026-08-06T10:30:00Z",
  "updated_at": "2026-08-06T10:31:12Z",
  "links": {
    "self": "/api/v1/analysis-runs/8fd489b8-7232-44fa-a95c-93baf6f265c3"
  }
}
```

Terminal successful/partial responses add `report`, `html_download`, and `markdown_download` links. For `FAILED`, `failure` contains safe `code` and `message`. Messages must not disclose internal network or policy details.

---

## 6. Preview report

### `GET /api/v1/analysis-runs/{run_id}/report`

Available only for `COMPLETED` or `PARTIAL`.

```json
{
  "run_id": "8fd489b8-7232-44fa-a95c-93baf6f265c3",
  "state": "PARTIAL",
  "target_url": "https://example.com/",
  "generated_at": "2026-08-06T10:35:00Z",
  "health_score": 72,
  "executive_summary": "Performance and metadata issues were found.",
  "top_findings": [
    {
      "finding_id": "f4ffaf17-29db-4d22-9972-569e0913b394",
      "category": "performance",
      "severity": "high",
      "confidence": 0.98,
      "title": "Largest Contentful Paint exceeds threshold",
      "impact": "Users may perceive the page as slow.",
      "recommendation": "Optimize the identified render path.",
      "affected_urls": ["https://example.com/"],
      "evidence": [{"kind": "metric", "affected_url": "https://example.com/", "summary": "LCP measured 4.2 seconds."}]
    }
  ],
  "findings_by_category": {"performance": [], "seo": []},
  "findings_by_agent": {"performance": [], "seo": []},
  "coverage": {"pages_planned": 10, "pages_scanned": 8},
  "limitations": ["Two pages timed out after retries."],
  "errors": [],
  "downloads": {"html": ".../reports/html", "markdown": ".../reports/markdown"}
}
```

Rules:

1. Every finding includes sanitized evidence.
2. `confidence` is `0.0`–`1.0`; `health_score` is integer `0`–`100`.
3. Health-score logic is outside this API specification.
4. `PARTIAL` reports include limitations/errors explaining incomplete coverage.
5. Internal paths and provider-native payloads are never exposed.
6. Grouped findings are available by HLD agent and category.

---

## 7. Download report

### `GET /api/v1/analysis-runs/{run_id}/reports/{format}`

Success headers:

```text
Content-Type: text/html; charset=utf-8
Content-Disposition: attachment; filename="website-health-report_example.com_20260806T103500Z.html"
ETag: "<artifact-checksum>"
Cache-Control: private, no-cache
```

Markdown uses `text/markdown; charset=utf-8` and `.md`.

1. Artifact is immutable for its run/format.
2. Matching `If-None-Match` returns `304 Not Modified`.
3. Download requires tenant authorization.
4. HTML is self-contained and has no internal artifact dependencies.

---

## 8. Error contract

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request is invalid.",
    "details": [{
      "field": "scan_preferences.max_pages",
      "reason": "Must be within the configured limit."
    }],
    "correlation_id": "f1582764-5492-41fb-a71d-f343206fccb6"
  }
}
```

| Status | Codes | Meaning |
|---|---|---|
| `400` | `MALFORMED_REQUEST`, `VALIDATION_ERROR` | Invalid syntax/value |
| `401` | `AUTHENTICATION_REQUIRED` | Invalid identity |
| `403` | `ACCESS_DENIED`, `TARGET_NOT_ALLOWED` | Authorization/policy denial |
| `404` | `RUN_NOT_FOUND` | Absent or invisible run |
| `409` | `REPORT_NOT_READY`, `INVALID_RUN_STATE` | State conflict |
| `422` | `UNSUPPORTED_PREFERENCE` | Unsupported preference |
| `429` | `RATE_LIMITED`, `BUDGET_EXCEEDED` | Limit denial |
| `500` | `INTERNAL_ERROR` | Unexpected failure |
| `503` | `SERVICE_UNAVAILABLE` | Required dependency unavailable |

Cross-tenant access returns `404 RUN_NOT_FOUND` to avoid revealing resource existence.

---

## 9. Reliability and security

1. POST creates one run; idempotency is not promised in MVP.
2. Polling intervals/rate limits are defined in Guardrails.
3. Logs include correlation ID, run ID, route, status, and duration—not tokens/secrets.
4. Target query values are redacted per Security policy.
5. Report/error content is sanitized before serialization.
6. CORS, TLS, token validation, and retention are defined downstream.

---

## 10. Implementation reconciliation

Existing provisional API code is non-authoritative. After approval it must be audited for:

1. Route versioning/naming and `202` asynchronous creation.
2. DTO conformance and unknown-field rejection.
3. Separate preview and format-download routes.
4. Standard errors and tenant-safe `404`.
5. Authentication/tenant integration after Security approval.

No reconciliation code may be written before approval.

---

## 11. Open downstream decisions

| Decision | Owner |
|---|---|
| Identity provider and tenant claims | `10_Security.md` |
| Limit defaults and polling/rates | `11_Guardrails.md` |
| Persistence and immutable artifacts | `08_Database_Design.md` |
| CORS, TLS, health endpoints | `10_Security.md`, `14_Deployment.md` |
| Health-score weights | Report/domain design revision |

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product | | Approved | 2026-08-06 |
| Software Architecture | | Approved | 2026-08-06 |
| Engineering | | Approved | 2026-08-06 |
| Security | | Approved | 2026-08-06 |
| QA | | Approved | 2026-08-06 |
