# Low Level Design
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Product name | AI Website Health Orchestrator Agent |
| Alternate / portfolio name | AI Website Reliability Engineer (ORCA) |
| Document type | Low Level Design (LLD) |
| Version | 0.1 |
| Status | Approved |
| Upstream | `02_User_Stories.md` (Approved), `03_System_Architecture.md` (Approved), `04_High_Level_Design.md` (Approved) |
| Downstream | `06_API_Specification.md`, `07_Agent_Architecture.md`, `08_Database_Design.md`, `13_Testing_Strategy.md` |
| Audience | Software Engineering, AI Engineering, DevOps, QA, Security |
| Last updated | 2026-08-04 |
| File | `05_Low_Level_Design.md` |

---

## 1. Purpose

This document converts the approved HLD into implementable module-level design for the read-only Website Analysis MVP.

It covers module boundaries, domain objects, application flows, agent contracts, port abstractions, persistence shape, and failure handling. It does not define concrete HTTP payloads, vendor SDK code, physical DDL, or any Git/PR/deploy behavior.

---

## 2. MVP design constraints

1. Read-only website analysis only
2. Every finding must reference evidence
3. Domain logic must not depend on Playwright, Lighthouse, axe-core, or LLM SDKs directly
4. LLM is assistive only and cannot create evidence-less findings
5. Scan cost must be bounded by configured limits
6. Partial completion is preferred over silent failure
7. Tenant data, artifacts, and reports must remain isolated

---

## 3. Module decomposition

| Module | Responsibility | Layer |
|---|---|---|
| `scan_domain` | Entities, value objects, rules, scoring, dedup invariants | Domain |
| `scan_application` | Start run, track progress, aggregate findings, publish report | Application |
| `agent_services` | Per-agent orchestration logic over ports | Application |
| `policy_services` | Target validation and capability denial | Application |
| `limit_services` | Budget reservation, consumption, enforcement | Application |
| `report_services` | Normalize findings, render report model, publish artifacts | Application |
| `ports` | Browser, tool, AI, store, repository, renderer abstractions | Boundary |
| `adapters_inbound` | UI/API/CLI entry points | Inbound |
| `adapters_outbound` | Playwright, Lighthouse, axe, storage, DB, logging, LLM | Outbound |
| `bootstrap` | Dependency injection and configuration composition root | Bootstrap |

---

## 4. Domain model

| Entity | Key fields | Notes |
|---|---|---|
| `AnalysisRun` | `run_id`, `tenant_id`, `target_url`, `state`, `preferences`, `coverage`, `created_at` | Aggregate root |
| `PageTarget` | `url`, `depth`, `source_url`, `eligibility_status` | Planned scan unit |
| `Finding` | `finding_id`, `category`, `severity`, `confidence`, `title`, `description`, `fingerprint` | Must have evidence refs |
| `Evidence` | `evidence_id`, `kind`, `page_url`, `artifact_ref`, `summary` | Immutable once stored |
| `ScanSummary` | `health_score`, `coverage_stats`, `limitations`, `agent_failures` | Built at aggregation |
| `ReportArtifact` | `artifact_id`, `format`, `run_id`, `storage_ref`, `checksum` | Immutable download |

`ScanPreferences`, `Severity`, `Confidence`, `HealthScore`, `CoverageStats`, `LimitSnapshot`, `PolicyDecision`, `RetryPolicy`, `AgentResult`.

### 4.1 Invariants

1. A `Finding` must reference one or more `Evidence` records.
2. `COMPLETED` and `PARTIAL` runs must have at least one report artifact.
3. `FAILED` runs must include a failure reason.
4. Deduplication must never discard affected URL references.
5. Secret-like content must be masked before report rendering.
6. AI-enriched text may explain findings but may not introduce new authoritative facts without existing evidence.

---

## 5. Run state machine

State progression is `ACCEPTED -> VALIDATING -> PLANNING -> RUNNING -> AGGREGATING -> RENDERING -> COMPLETED|PARTIAL`, with failure exits from `VALIDATING`, `PLANNING`, and `RUNNING`. `PARTIAL` is used whenever usable findings exist but coverage or agent execution is incomplete.

---

## 6. Application use cases

### 6.1 `StartAnalysisRun`

1. Validate request shape.
2. Create `AnalysisRun` in `ACCEPTED`.
3. Transition to `VALIDATING`; evaluate target via `TargetPolicyPort`.
4. Reserve initial budgets with `CostGovernorPort`.
5. Transition to `PLANNING`; build queue via `CrawlPlannerService`.
6. Transition to `RUNNING`.
7. Execute agents; transition to `AGGREGATING` and build the normalized summary.
8. Transition to `RENDERING`; publish both report artifacts, then enter the applicable terminal state.

### 6.2 `GetRunStatus`

Return state, progress counters, agent progress, coverage, and terminal reason.

### 6.3 `PublishRunReport`

Load normalized summary, render both formats, store immutable artifacts, and mark `COMPLETED` or `PARTIAL`.

---

## 7. Internal services

### 7.1 `CrawlPlannerService`

Normalizes the base URL, discovers candidate links, applies page/depth rules, filters denied targets, and returns a stable `PageTarget` queue with coverage metadata. The planner uses breadth-first discovery starting from depth `0` and stops when hard limits are reached.

### 7.2 `AgentExecutionCoordinator`

Builds the per-page/per-agent task matrix, enforces concurrency and limits, retries transient failures, and collects structured `AgentResult` objects.

Rules:

- Browser-dependent agents may share a page session only through `BrowserPort`
- No agent writes report artifacts directly
- One agent failure does not fail the run if usable evidence exists elsewhere

### 7.3 `FindingAggregationService`

Converts raw agent outputs into normalized findings, computes fingerprints, deduplicates equivalent records, assigns severity/confidence/priority, and builds `ScanSummary`.

Fingerprint pattern: `category + normalized locator + normalized signal + optional rule id`

### 7.4 `ReportCompositionService`

Groups findings by severity and category, masks secrets in evidence text, and produces a renderer-neutral report model.

### 7.5 `AssistiveNarrativeService`

Requests summary/grouping suggestions from `LlmAssistPort`, rejects AI output that references missing findings, and falls back to deterministic summary when AI is unavailable.

---

## 8. Specialised agent design

| Agent service | Input | Output | Primary ports |
|---|---|---|---|
| `SeoAgentService` | `PageTarget`, page snapshot | SEO findings | `BrowserPort`, `HtmlAnalysisPort` |
| `PerformanceAgentService` | `PageTarget` | perf findings + artifact refs | `LighthousePort`, `PsiPort` optional |
| `LatencyAgentService` | `PageTarget` | timing findings | `BrowserPort`, `HeaderProbePort` |
| `BrokenLinkAgentService` | `PageTarget`, extracted links | link findings | `LinkCheckPort` |
| `ConsoleAgentService` | `PageTarget` | console findings | `BrowserPort` |
| `HtmlDocumentAgentService` | `PageTarget`, HTML snapshot | markup findings | `HtmlAnalysisPort` |
| `SecurityAgentService` | `PageTarget`, HTML/assets/headers | security hygiene findings | `SecretScanPort`, `HeaderProbePort` |
| `AccessibilityAgentService` | `PageTarget` | a11y findings | `AxePort` |

### 8.1 Shared contract

Each agent returns `agent_name`, `page_url`, `findings[]`, `evidence[]`, `artifacts[]`, `warnings[]`, optional `failure_reason`, and `retry_count`.

### 8.2 Per-page flow

1. `BrowserEvidenceCollector` acquires page context and shared evidence.
2. Non-browser parsers reuse shared snapshots where possible.
3. Tool-based agents run in parallel subject to limits.
4. Artifacts are persisted before final aggregation.

---

## 9. Port contracts

| Port | Capability |
|---|---|
| `BrowserPort` | Navigate, capture DOM snapshot, console events, screenshot, network timing |
| `LighthousePort` | Run audit and return metrics plus raw artifact reference |
| `PsiPort` | Fetch optional PageSpeed Insights result |
| `AxePort` | Execute axe-core and return violations |
| `HtmlAnalysisPort` | Analyze document structure and metadata |
| `SecretScanPort` | Detect token/secret-like patterns in HTML or assets |
| `HeaderProbePort` | Retrieve security headers and timing info |
| `LinkCheckPort` | Resolve URL status and redirect chain |
| `LlmAssistPort` | Summarize, cluster, explain with token accounting |
| `ArtifactStorePort` | Save and retrieve immutable artifacts |
| `ScanRepositoryPort` | Persist runs, findings, summary metadata, statuses |
| `ReportRendererPort` | Render HTML and Markdown from normalized report model |
| `TargetPolicyPort` | Evaluate target safety and scope eligibility |
| `CostGovernorPort` | Reserve, consume, and deny work by budget policy |

### 9.1 Port rules

1. All ports return structured result objects, not provider-native payloads.
2. All outbound failures are classified as retryable or terminal.
3. No port may leak credentials into result payloads or logs.

---

## 10. Persistence design

| Record | Minimum fields |
|---|---|
| `analysis_runs` | ids, tenant, target, preferences, state, timestamps, terminal reason |
| `page_targets` | run id, url, depth, eligibility, discovery source |
| `findings` | run id, category, severity, confidence, fingerprint, summary, occurrence count |
| `evidence` | finding id, kind, page url, artifact ref, masked summary |
| `agent_executions` | run id, agent name, page url, state, retries, duration, failure reason |
| `report_artifacts` | run id, format, storage ref, checksum, created at |

### 10.1 Storage rules

1. Findings and evidence are append-oriented during a run.
2. Report artifacts are immutable after publish.
3. Raw artifacts are stored separately from normalized finding records.
4. Tenant isolation must be enforced in both metadata and artifact paths.

---

## 11. Error handling and retries

| Failure type | Handling |
|---|---|
| Target denied | Mark run `FAILED`; do not start crawl |
| Page navigation timeout | Retry within `RetryPolicy`; record limitation if exhausted |
| Tool failure on one page | Record agent failure; continue other agents/pages |
| Budget exhaustion | Stop new work; aggregate completed results; publish `PARTIAL` if possible |
| Artifact store write failure | Retry; if report cannot be stored, terminal failure |
| LLM unavailable | Fall back to deterministic summary and keep run publishable |

### 11.1 Retry rules

Retry only transient failures, use bounded retries with jitter/backoff in the adapter layer, persist retry count for auditability, and never retry policy denials.

---

## 12. Limit enforcement points

| Limit | Enforced in |
|---|---|
| Max pages / depth | `CrawlPlannerService` |
| Browser concurrency | `AgentExecutionCoordinator` + `CostGovernorPort` |
| Browser minutes | `BrowserPort` lease accounting + `CostGovernorPort` |
| Screenshot count | `BrowserEvidenceCollector` |
| PSI calls | `PerformanceAgentService` |
| LLM tokens | `AssistiveNarrativeService` + `CostGovernorPort` |
| Total run timeout | Run supervisor / application layer |

---

## 13. Observability design

Every major operation logs `scan_run_id`, `tenant_id`, `agent_name` where relevant, redacted `page_url`, `state_transition`, `duration_ms`, `retry_count`, `budget_event`, and created `artifact_ref`.

Metrics to emit: run success/partial/fail counts, agent failure rate by category, average run duration, findings by severity, and screenshot/PSI/token consumption.

---

## 14. Security and privacy controls

1. Run `TargetPolicyPort` before any network fetch.
2. Treat webpage content and AI prompt content as untrusted input.
3. Mask secrets before persistence into finding summaries or reports.
4. Restrict report downloads to tenant-authorized callers.
5. Apply retention TTLs to screenshots, DOM snapshots, logs, and report artifacts per later security policy.

---

## 15. Implementation sequencing

1. Domain model and repository contracts
2. Target policy and cost governor
3. Crawl planner and run state transitions
4. Browser evidence collection
5. SEO, HTML, console, broken-link, and accessibility agents
6. Performance, latency, and security agents
7. Aggregation and report rendering
8. AI-assisted narrative fallback path
9. Partial-failure and masking tests

---

## 16. Open decisions for downstream docs

1. API surface: web UI only, API only, or both
2. DB and artifact store products
3. Default scoring weights for `HealthScore`
4. Concurrency defaults for browser pool
5. Exact retention defaults and tenant authorization model

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product | | Approved | 2026-08-04 |
| Engineering | | Approved | 2026-08-04 |
| AI Engineering | | Approved | 2026-08-04 |
| QA | | Approved | 2026-08-04 |
| DevOps / Security | | Approved | 2026-08-04 |
