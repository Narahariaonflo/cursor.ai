# Implementation Progress

## AI Website Health Orchestrator Agent (ORCA)


| Field | Value |
|---|---|
| Product name | AI Website Health Orchestrator Agent |
| Alternate / portfolio name | AI Website Reliability Engineer (ORCA) |
| Document type | Implementation Progress |
| Version | 0.1 |
| Status | Active |
| Upstream | `12_Implementation_Plan.md`, `16_Engineering_Backlog.md` |
| Audience | Product, Engineering, QA |
| Last updated | 2026-08-11 |
| File | `17_Implementation_Progress.md` |


---

## 1. Snapshot

ORCA’s **documentation set is complete and approved**. The **local MVP vertical slice is largely implemented**: submit URL → validate → crawl → collect evidence → run specialised agents → aggregate → publish HTML/Markdown reports via API and a minimal UI.

**Overall status:** functional local MVP is in place; production hardening and real tool adapters (axe-core, Lighthouse CLI, LLM provider) remain open.

| Area | Status |
|---|---|
| Documentation (`00`–`16`) | Complete / Approved |
| Local MVP pipeline (WP0–WP5 / M1–M20) | Largely done |
| Hardening & MVP exit checklist (WP6 / M21) | Partial |
| Production readiness (WP7 / M22–M24) | Started (Postgres/S3 + Docker Compose); not release-ready |

---

## 2. Initial plan (what we set out to build)

### 2.1 Product intent

Build a **read-only website health analyst** that:

1. Accepts a public URL and scan limits.
2. Rejects unsafe targets (SSRF / allow-deny) before crawl.
3. Runs specialised agents for SEO, performance, latency, broken links, console, HTML, security hygiene, and accessibility.
4. Deduplicates, scores, and summarises findings.
5. Lets users preview and download **immutable HTML and Markdown** reports.
6. Supports partial runs with explicit limitations; masks secrets; correlates logs by `scan_run_id`.

**Explicitly out of MVP scope:** GitHub/GitLab, PRs, patches, deploys, authenticated scanning beyond approved patterns, legal a11y/security certification, native mobile analysis, raw evidence zip packages.

### 2.2 Delivery model

Approved plan in `12_Implementation_Plan.md`:

| Work package | Goal |
|---|---|
| WP0 | Foundations — package layout, DI, config, logging, domain types |
| WP1 | Policy, limits, run lifecycle |
| WP2 | Crawl planner + Playwright browser evidence |
| WP3 | Core agents (SEO, HTML, Console, Broken Link, Accessibility) + coordinator |
| WP4 | Performance, latency, security agents |
| WP5 | Aggregation, assistive narrative, reports, preview/download |
| WP6 | Hardening, observability, functional MVP exit |
| WP7 | Production readiness (Postgres/S3, durable runtime, cost/release validation) |

Milestones **M0–M24** in `16_Engineering_Backlog.md` decompose the same plan into independently testable units across six waves.

### 2.3 Architecture principles locked in docs

- Clean Architecture with dependency injection
- Evidence-first deterministic tools; LLM assistive only with deterministic fallback
- Fail partial — one agent gap must not block a usable report
- Cost-bounded crawl/tool/token usage
- No code before documentation approval (gate satisfied)

---

## 3. Documentation progress

All planned product/engineering docs are written and approved:

| Doc | Title | Status |
|---|---|---|
| 00 | Documentation Index | Active |
| 01 | Product Requirements | Approved |
| 02 | User Stories | Approved |
| 03 | System Architecture | Approved (MVP topology superseded by 04) |
| 04 | High Level Design | Approved (binding MVP scope) |
| 05 | Low Level Design | Approved |
| 06 | API Specification | Approved |
| 07 | Agent Architecture | Approved |
| 08 | Database Design | Approved |
| 09 | AI Architecture | Approved |
| 10 | Security | Approved |
| 11 | Guardrails | Approved |
| 12 | Implementation Plan | Approved |
| 13 | Testing Strategy | Approved |
| 14 | Deployment | Approved |
| 15 | Cost Optimization | Approved |
| 16 | Engineering Backlog | Approved |

**Wave 0 (M0 — docs gate):** Done.

---

## 4. What is implemented

### 4.1 Foundations and control plane

| Capability | Location / notes |
|---|---|
| Clean Architecture layout | `src/domain`, `src/application`, `src/ports`, `src/adapters`, `src/bootstrap`, `src/config` |
| Settings from env/config | `Settings.from_env()`, `config/defaults.json`, runtime env validation |
| DI composition root | `bootstrap/container.py` |
| Structured logging | `JsonStructuredLogger` |
| Domain model | `AnalysisRun`, findings/evidence invariants, run state machine |
| Architecture boundary tests | `tests/architecture/test_layer_imports.py` |

### 4.2 Policy, limits, run lifecycle

| Capability | Notes |
|---|---|
| Target policy / SSRF checks | `TargetPolicyService` + DNS resolver port |
| Cost governor | `InMemoryCostGovernor` with page/depth/resource ceilings |
| Use cases | `StartAnalysisRun`, `ValidateAnalysisRun`, `PlanAnalysisRun`, `GetRunStatus`, `ProcessAnalysisRun`, `PublishRunReport` |
| Submit / status API | `POST /api/v1/analysis-runs`, `GET /api/v1/analysis-runs/{run_id}` |

### 4.3 Crawl and browser evidence

| Capability | Notes |
|---|---|
| Bounded crawl planner | `max_pages` / `max_depth`, deny paths, coverage limitations |
| HTML fetch + link discovery | HTTP adapters behind ports |
| Playwright browser adapter | Navigation, DOM/console/screenshot capture |
| Browser evidence collector | Budget-aware screenshots, retries, secret masking |
| Local artifact store | Filesystem artifact store |

### 4.4 Specialised agents (all eight wired)

| Agent | Service | Adapter maturity |
|---|---|---|
| SEO | `SeoAgentService` | Deterministic HTML/metadata analysis |
| HTML | `HtmlDocumentAgentService` | `RegexHtmlAnalysisAdapter` |
| Console | `ConsoleAgentService` | Uses captured browser evidence |
| Broken Link | `BrokenLinkAgentService` | `HttpLinkCheckAdapter` |
| Accessibility | `AccessibilityAgentService` | **Fixture axe adapter** (deterministic subset, not full axe-core) |
| Performance | `PerformanceAgentService` | **Mapping Lighthouse adapter** (fixture metrics; not real Lighthouse CLI) |
| Latency | `LatencyAgentService` | `SimpleHeaderProbeAdapter` + config thresholds |
| Security | `SecurityAgentService` | Header probe + regex secret scan + masking |

Coordinator: `AgentExecutionCoordinator` with concurrency limits and failure isolation.

### 4.5 Aggregation, narrative, reports, UI

| Capability | Notes |
|---|---|
| Finding aggregation / scoring | `FindingAggregationService` |
| Assistive narrative | `AssistiveNarrativeService` with deterministic fallback; **no live LLM provider wired** in container |
| Report render | HTML + Markdown via `SimpleReportRenderer` |
| Preview / download API | Report preview + HTML/Markdown download routes |
| Minimal UI | Home page for submit / status / preview / download |
| Vertical-slice integration | `tests/integration/test_vertical_slice.py` covers submit → process → report |

### 4.6 Resilience and local/production adapter start

| Capability | Notes |
|---|---|
| Bounded retries | `application/resilience/retry.py` |
| Sensitive data masking | `SensitiveDataMasker` |
| Local persistence | SQLite repository + filesystem artifacts (`local` / `test`) |
| External persistence adapters | `PostgresScanRepository`, `S3ArtifactStore` selected for `docker` / `staging` / `production` |
| Local infra compose | `docker-compose.yml` — Postgres 16 + MinIO (S3-compatible) |

### 4.7 Test coverage present

Unit, architecture, and integration tests cover domain rules, policy/governor, crawl planner, agents, coordinator, aggregation, narrative fallback, retries, settings/container, Playwright adapter behavior, production adapter selection, and the end-to-end API vertical slice.

---

## 5. Milestone status (backlog map)

| Milestone | Intent | Status |
|---|---|---|
| M0 | Documentation gate | **Done** |
| M1 | Foundations / DI / config / logging | **Done** |
| M2 | Domain + port contracts | **Done** |
| M3 | SQLite / filesystem persistence | **Done** |
| M4 | Target policy + cost governor | **Done** |
| M5 | Run lifecycle + submit/status API | **Done** |
| M6 | Crawl planner | **Done** |
| M7 | Browser evidence (Playwright) | **Done** (local path) |
| M8 | Agent execution coordinator | **Done** |
| M9–M12 | SEO, HTML, Console, Broken Link | **Done** |
| M13 | Accessibility | **Partial** — fixture axe, not production axe-core |
| M14 | Performance | **Partial** — fixture Lighthouse mapping; PSI gated/off by default |
| M15 | Latency | **Done** (header-probe based) |
| M16 | Security hygiene | **Done** (headers + masked secret patterns) |
| M17 | Aggregation / scoring | **Done** |
| M18 | Assistive narrative (LLM) | **Partial** — service + fallback done; provider adapter not wired |
| M19 | Report render / download | **Done** |
| M20 | API + minimal UI | **Done** |
| M21 | Hardening + functional MVP exit | **Partial** — retries/masking present; full acceptance/metrics checklist open |
| M22 | Production data adapters | **Started** — Postgres/S3 adapters + compose; RLS/migrations/retention incomplete vs DOC-08/14 |
| M23 | Durable deployment runtime | **Not started** — no dispatcher/worker leases/migration runtime yet |
| M24 | Production cost/release validation | **Not started** |

---

## 6. Work-package progress

| WP | Plan focus | Progress |
|---|---|---|
| WP0 Foundations | Skeleton, DI, config, logging, domain | **Complete** |
| WP1 Policy / limits / lifecycle | Safe intake + bounded control | **Complete** |
| WP2 Crawl + browser evidence | Page queue + Playwright artifacts | **Complete** (local) |
| WP3 Core agents | SEO/HTML/Console/Links/A11y + coordinator | **Mostly complete** (a11y fixture-level) |
| WP4 Perf / latency / security | Remaining agents | **Mostly complete** (perf fixture-level) |
| WP5 Aggregate + reports | Dedup, narrative, HTML/MD, preview | **Mostly complete** (deterministic narrative default) |
| WP6 Hardening / MVP exit | Retries, PARTIAL semantics, acceptance suite | **In progress** |
| WP7 Production readiness | Postgres/S3, durable topology, release gates | **Early** |

---

## 7. Remaining work (next)

### Near-term (close functional MVP / M21)

1. Replace fixture axe and mapping Lighthouse with real tool adapters (or document intentional local stubs + gap recording).
2. Wire an optional LLM assist adapter behind `LlmAssistPort` (keep deterministic fallback).
3. Complete hardening acceptance: budget → `PARTIAL`, no-evidence → `FAILED`, secret-leak regressions, required metrics/correlation assertions.
4. Expand fixture-site acceptance coverage for US-001–US-016.

### Production track (M22–M24)

1. Harden Postgres tenant isolation (RLS), migrations, retention.
2. Harden S3 immutability/checksum and private object policy.
3. Add durable API/dispatcher/worker runtime per `14_Deployment.md`.
4. Run cost/load/release validation per `15_Cost_Optimization.md`.

---

## 8. Story coverage (current reading)

| Stories | Intent | Current reading |
|---|---|---|
| US-001–US-003 | Submit, policy, crawl | Implemented in local path |
| US-004–US-009 | Agents + evidence | Implemented; a11y/perf use fixture adapters |
| US-010–US-014 | Aggregate, narrative, reports, UI | Implemented; narrative is deterministic unless LLM injected |
| US-015–US-016 | Budgets, masking, observability | Partially implemented; full M21 exit evidence still open |

---

## 9. How to read this against source docs

- **Product “why”:** `01_Product_Requirements.md`
- **MVP scope (binding):** `04_High_Level_Design.md`
- **Phased delivery plan:** `12_Implementation_Plan.md`
- **Testable milestone checklist:** `16_Engineering_Backlog.md`
- **This file:** living progress snapshot of plan vs code as of 2026-08-11

When implementation and docs diverge, **documentation wins** and code is corrected (`16_Engineering_Backlog.md` §9).
