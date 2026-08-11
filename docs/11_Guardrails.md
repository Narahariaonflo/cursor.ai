# Operational Guardrails
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Document ID | ORCA-GRD-011 |
| Version | 0.1 |
| Status | Approved |
| Scope | Read-only Website Analysis MVP |
| Upstream | `04_High_Level_Design.md`–`10_Security.md` (Approved) |
| Downstream | `13_Testing_Strategy.md`, `14_Deployment.md`, `15_Cost_Optimization.md` |
| Last updated | 2026-08-06 |

---

## 1. Purpose

This document defines enforceable safety, reliability, capacity, and cost boundaries. All values are named validated configuration. Business logic consumes typed policies through dependency injection and contains no numeric or string policy literals.

Guardrails must:

1. reject unsafe or unsupported work before resource allocation;
2. prevent one tenant/run/tool from exhausting capacity;
3. stop new work before a hard budget is exceeded;
4. preserve completed evidence and publish a transparent partial report where possible;
5. fail closed for security and evidence-integrity controls.

---

## 2. Policy precedence and changes

The effective value is the most restrictive applicable value:

1. system hard ceiling;
2. deployment/tenant policy;
3. accepted request preference;
4. remaining run budget.

Requests may reduce but never exceed policy. Invalid values return API `400 VALIDATION_ERROR`; unsupported preferences return `422 UNSUPPORTED_PREFERENCE`. Runtime exhaustion records a limitation and follows §12.

Default increases require Architecture, Security, Product, and Platform approval plus load/cost evidence. Emergency decreases may be applied operationally and must be audited.

---

## 3. Target and crawl guardrails

`10_Security.md` owns SSRF/address safety. This section owns crawl scope.

| Configuration | Default | Hard ceiling |
|---|---:|---:|
| `MAX_PAGES_PER_RUN` | 10 | 50 |
| `MAX_CRAWL_DEPTH` | 2 | 4 |
| `MAX_DISCOVERED_URLS` | 200 | 1,000 |
| `MAX_REDIRECTS_PER_NAVIGATION` | 5 | 10 |
| `MAX_URL_LENGTH_BYTES` | 2,048 | 4,096 |
| `MAX_QUERY_PARAMETERS` | 25 | 50 |

Rules:

1. Seed URL is depth `0`; breadth-first discovery is deterministic.
2. Crawl is same-origin by default: normalized scheme, host, and effective port.
3. `www`/apex and subdomains are distinct origins unless tenant policy explicitly permits them.
4. Fragments are removed; tracking parameters are removed by configured name list.
5. Canonical duplicate URLs share one page budget entry.
6. Non-HTTP(S), logout, delete, admin, account, cart/checkout, and configured path patterns are denied.
7. `robots.txt` is respected by default; override requires owner authorization and policy approval.
8. Sitemap discovery may add candidates but cannot bypass depth/page/policy limits.
9. External link validation is enabled by default under Target Policy and HTTP-probe budget; a request may disable it only with an explicit report coverage limitation.
10. Every candidate and redirect passes Target Policy before network access.

---

## 4. Run and task timeouts

| Configuration | Default |
|---|---:|
| `RUN_TIMEOUT_SECONDS` | 900 |
| `QUEUE_WAIT_TIMEOUT_SECONDS` | 120 |
| `PAGE_NAVIGATION_TIMEOUT_SECONDS` | 30 |
| `HTTP_PROBE_TIMEOUT_SECONDS` | 10 |
| `STANDARD_AGENT_TASK_TIMEOUT_SECONDS` | 60 |
| `LIGHTHOUSE_TIMEOUT_SECONDS` | 120 |
| `PSI_TIMEOUT_SECONDS` | 20 |
| `LLM_TIMEOUT_SECONDS` | 30 |
| `REPORT_RENDER_TIMEOUT_SECONDS` | 60 |
| `ARTIFACT_OPERATION_TIMEOUT_SECONDS` | 15 |

1. Deadlines use a monotonic clock.
2. Child deadline never exceeds the run deadline; Lighthouse uses its dedicated 120-second task class rather than the standard-agent timeout.
3. Timeout cancels affected work and releases leases/reservations in `finally` paths.
4. Run timeout stops scheduling and aggregates usable completed results.
5. Security validation and report integrity timeout fail closed.

---

## 5. Retry policy

| Configuration | Default |
|---|---:|
| `MAX_RETRIES_PER_OPERATION` | 2 |
| `RETRY_BASE_DELAY_MS` | 500 |
| `RETRY_MAX_DELAY_MS` | 5,000 |
| `RETRY_JITTER_RATIO` | 0.20 |
| `MAX_RETRY_AFTER_SECONDS` | 30 |

Maximum attempts are one initial attempt plus retries. Exponential backoff uses full configured jitter.

Retryable: connection reset, transient DNS failure after safe revalidation, timeout when deadline remains, HTTP `408`/`429`, provider throttling, and HTTP `5xx` where operation is idempotent.

Terminal: validation/policy denial, authentication/authorization failure, most HTTP `4xx`, schema failure, deterministic analyzer failure, budget denial, secret-masking failure, and artifact-integrity failure.

Each retry rechecks deadline, policy, and budget; consumes budget; preserves task lineage; and records a safe reason. Nested adapters must not independently multiply retries.

---

## 6. Concurrency and queue limits

| Configuration | Default |
|---|---:|
| `MAX_ACTIVE_RUNS_PER_TENANT` | 2 |
| `MAX_QUEUED_RUNS_PER_TENANT` | 10 |
| `MAX_PARALLEL_PAGES_PER_RUN` | 2 |
| `MAX_AGENT_TASKS_IN_FLIGHT_PER_RUN` | 8 |
| `MAX_BROWSER_CONTEXTS_PER_RUN` | 2 |
| `MAX_LIGHTHOUSE_TASKS_PER_RUN` | 1 |
| `MAX_PSI_CALLS_IN_FLIGHT_PER_RUN` | 2 |
| `MAX_HTTP_PROBES_IN_FLIGHT_PER_RUN` | 10 |
| `MAX_LLM_CALLS_IN_FLIGHT_PER_RUN` | 1 |

Global limits are validated deployment configuration; proposed `14_Deployment.md` values become binding only when that document is approved.

Queues are bounded and tenant-fair. No unbounded task creation is allowed. A run acquires capacity immediately before work and releases it on every terminal path. Browser and Lighthouse capacity take priority over optional PSI/AI work.

---

## 7. Per-run cost and resource budgets

| Configuration | Default hard limit |
|---|---:|
| `MAX_PAGES_PER_RUN` | 50 |
| `MAX_BROWSER_MINUTES_PER_RUN` | 20 |
| `MAX_LIGHTHOUSE_CALLS_PER_RUN` | 10 |
| `MAX_PSI_CALLS_PER_RUN` | 10 |
| `MAX_HTTP_PROBES_PER_RUN` | 250 |
| `MAX_SCREENSHOTS_PER_RUN` | 20 |
| `MAX_LLM_CALLS_PER_RUN` | 10 |
| `MAX_LLM_TOKENS_PER_RUN` | 50,000 |
| `MAX_ARTIFACT_BYTES_PER_RUN` | 104,857,600 |

Optional PSI is disabled by default even when credentials exist: `PSI_ENABLED=false`. AI fallback is governed by `09_AI_Architecture.md`.

The Cost Governor uses atomic reserve → consume/reconcile → release operations:

1. reserve the initial run envelope before crawl planning, then reserve worst-case incremental cost before each task;
2. deny when reservation could exceed remaining budget;
3. record actual usage and release surplus;
4. make repeated reconciliation idempotent by task ID;
5. retain usage for audit even when a task fails.

---

## 8. Evidence and payload bounds

| Configuration | Default |
|---|---:|
| `MAX_API_REQUEST_BYTES` | 16,384 |
| `MAX_HTTP_RESPONSE_BYTES` | 5,242,880 |
| `MAX_DOM_SNAPSHOT_BYTES` | 2,097,152 |
| `MAX_TOOL_OUTPUT_BYTES` | 10,485,760 |
| `MAX_SCREENSHOT_BYTES` | 2,097,152 |
| `MAX_CONSOLE_EVENTS_PER_PAGE` | 500 |
| `MAX_NETWORK_EVENTS_PER_PAGE` | 1,000 |
| `MAX_EVIDENCE_SUMMARY_CHARS` | 2,000 |

Oversized streams are terminated without full buffering. Truncation is explicit in evidence metadata and reports. A finding cannot cite discarded content. Screenshots are captured only when required by an analyzer/evidence rule, not unconditionally.

---

## 9. API rate limits

Defaults are per authenticated tenant; a lower per-subject limit may also apply.

| Route class | Default |
|---|---:|
| Submit analysis | 10 requests/minute |
| Status/preview reads | 60 requests/minute |
| Report downloads | 20 requests/minute |
| Concurrent report streams | 5 |

The API returns `429 RATE_LIMITED` with a bounded `Retry-After`. Clients should poll no faster than every two seconds. Rate-limit storage must be shared in multi-instance production deployments.

---

## 10. Agent capability guardrails

1. Enabled agents must be a non-empty subset of the approved registry.
2. Default registry enables all required MVP agents.
3. Agents receive immutable scoped tasks and only assigned ports.
4. Browser actions remain read-only per Security; page content cannot request actions.
5. Tools cannot bypass target, budget, timeout, or artifact policies.
6. LLM output cannot add findings/evidence or change authoritative severity.
7. A disabled optional provider degrades predictably without adapter import/runtime failure.
8. No dynamic plugin loading or page-supplied code execution is allowed.

---

## 11. Finding and report guardrails

1. Every finding has valid URL, fingerprint, confidence, and at least one persisted evidence reference.
2. Unknown severity/category/evidence types are rejected.
3. Duplicate fingerprints merge deterministically without duplicating evidence.
4. Secret masking must succeed before persistence and rendering.
5. Health score is deterministic and bounded `0`–`100`.
6. AI narrative references only existing finding IDs.
7. `PARTIAL` reports state omitted pages/agents, exhausted limits, and failed tools.
8. Reports publish atomically in both required formats with checksums.

---

## 12. Exhaustion and degradation behavior

| Condition | Required behavior |
|---|---|
| Request exceeds configured limit | Reject before run creation |
| Tenant active capacity reached | Queue within bound; otherwise `429` |
| Page/depth/discovery limit reached | Stop discovery; continue planned work |
| Optional PSI/AI budget exhausted | Use deterministic fallback; disclose if material |
| Screenshot/tool budget exhausted | Skip new optional artifact; preserve valid findings |
| Browser/run deadline exhausted | Stop new work; aggregate completed evidence |
| One agent exhausts retries | Record failure; continue independent work |
| Security or masking guard fails | Quarantine affected data; safe remainder may publish `PARTIAL` |
| Unrecoverable crawl/planning failure | `FAILED`; no report/download |
| No usable evidence | `FAILED`; no report |
| Usable evidence with material gaps | `PARTIAL`; publish limitations |

Budget exhaustion is never silently converted to success.

---

## 13. Configuration validation and observability

Startup fails when values are missing, malformed, non-positive where required, exceed ceilings, or violate relationships (for example, page parallelism exceeding browser contexts).

Configuration layers are immutable for an accepted run; the applied policy version and limits are recorded. Logs and metrics include safe tenant/run/task IDs, policy version, reservations, actual usage, denials, queue delay, retries, timeouts, and exhaustion reason. They exclude content, tokens, secrets, and raw query values.

Alerts cover repeated target denials, queue saturation, timeout/retry spikes, budget exhaustion, reconciliation mismatch, and approaching global capacity.

---

## 14. Required tests

Required suites:

- boundary/property tests at below/equal/above every limit;
- deterministic breadth-first crawl and canonical deduplication;
- same-origin, path denial, robots, redirect, and Target Policy composition;
- deadline propagation with fake clocks;
- retry classification/backoff/jitter and retry-storm prevention;
- atomic concurrent reservation, idempotent reconciliation, and no overspend;
- semaphore/queue release on success, exception, timeout, and cancellation;
- tenant fairness and API rate limiting;
- streaming truncation/memory bounds;
- graceful `PARTIAL`/`FAILED` outcome matrix;
- configuration startup rejection and policy-version persistence.

Guardrail and governor modules require at least 95% branch coverage; overall project target remains at least 90%.

---

## 15. Implementation reconciliation

After approval:

1. expand typed Settings and `config/defaults.json` to this approved schema;
2. separate request defaults from immutable hard ceilings;
3. replace the provisional Cost Governor with atomic budget accounting;
4. implement shared retry/deadline policies and bounded coordinators;
5. expose safe `422`/`429` errors and report limitations;
6. do not implement browser/provider work until these controls have tests.

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Software Architecture | | Approved | 2026-08-06 |
| Security | | Approved | 2026-08-06 |
| Product | | Approved | 2026-08-06 |
| Engineering | | Approved | 2026-08-06 |
| DevOps / Platform | | Approved | 2026-08-06 |
| QA | | Approved | 2026-08-06 |
