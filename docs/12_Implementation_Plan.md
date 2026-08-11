# Implementation Plan
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Product name | AI Website Health Orchestrator Agent |
| Alternate / portfolio name | AI Website Reliability Engineer (ORCA) |
| Document type | Implementation Plan |
| Version | 0.1 |
| Status | Approved |
| Upstream | `02_User_Stories.md`, `04_High_Level_Design.md`–`11_Guardrails.md` (Approved) |
| Downstream | Coding work packages, `13_Testing_Strategy.md`, `14_Deployment.md` |
| Audience | Product, Engineering, AI, DevOps, QA |
| Last updated | 2026-08-04 |
| File | `12_Implementation_Plan.md` |

---

## 1. Purpose

This plan turns the approved MVP HLD and user stories into phased work packages suitable for delivery. Scope is **read-only website analysis** with HTML/Markdown report download. Git/PR/patch/deploy are out of scope.

**Documentation note:** Documents `06`–`11` are approved. Local implementation follows their locked contracts; production-release work remains gated by approved `14_Deployment.md` and `15_Cost_Optimization.md`.

---

## 2. MVP exit criteria

A release is MVP-complete when:

1. User can submit a public URL with scan limits and receive a run ID.
2. Unsafe targets are rejected before crawl (SSRF / allow-deny).
3. Specialised agents produce evidence-backed findings for SEO, performance, latency, broken links, console, HTML, security hygiene, and accessibility.
4. Findings are deduplicated, scored, and summarised.
5. User can preview and download immutable HTML and Markdown reports.
6. Partial runs publish with explicit limitations; secrets are masked; logs are correlated by `scan_run_id`.

Story coverage: **US-001 through US-016**.

---

## 3. Delivery principles

| Principle | Practice |
|---|---|
| Clean Architecture | Domain/application first; adapters last |
| Evidence first | Deterministic tools before LLM assist |
| Fail partial | Agent gaps do not block usable reports |
| Cost bounded | Hard limits on pages, browsers, screenshots, PSI, tokens |
| No premature code | Wait for documentation approval gate |

---

## 4. Work packages

### WP0 — Foundations (Week 1)

| Item | Detail |
|---|---|
| Goal | Project skeleton, DI, config, logging, domain types |
| Deliverables | Package layout (`scan_domain`, `scan_application`, `ports`, adapters, bootstrap); env/config loading; structured logger; `AnalysisRun` state model |
| Stories | Enables all |
| Exit | Domain invariants unit-tested; no vendor SDK in domain |

### WP1 — Policy, limits, run lifecycle (Week 1–2)

| Item | Detail |
|---|---|
| Goal | Safe intake and bounded execution control |
| Deliverables | `TargetPolicyPort` + SSRF checks; `CostGovernorPort`; `StartAnalysisRun` / `GetRunStatus`; run states through `VALIDATING`/`PLANNING`/`FAILED` |
| Stories | US-001, US-002, US-015 (partial) |
| Exit | Denied targets never fetch; budgets reserve/deny correctly |

### WP2 — Crawl planner + browser evidence (Week 2–3)

| Item | Detail |
|---|---|
| Goal | Bounded page queue and shared page evidence |
| Deliverables | `CrawlPlannerService`; Playwright `BrowserPort`; screenshots/DOM/console capture; artifact store adapter (filesystem or object store) |
| Stories | US-003, US-005 |
| Exit | `max_pages`/`max_depth` enforced; evidence refs stored |

### WP3 — Core specialised agents (Week 3–4)

| Item | Detail |
|---|---|
| Goal | First parallel agent set with shared contracts |
| Deliverables | SEO, HTML, Console, Broken Link, Accessibility agents; `AgentExecutionCoordinator` with concurrency limits |
| Stories | US-004, US-006, US-008, US-009 (a11y/HTML) |
| Exit | Each agent returns findings + evidence; one agent failure continues the run |

### WP4 — Perf, latency, security agents (Week 4–5)

| Item | Detail |
|---|---|
| Goal | Remaining analysis agents |
| Deliverables | Lighthouse + optional PSI; latency probes; security headers/secret scan (masked) |
| Stories | US-007, US-009 (security) |
| Exit | Tool gaps recorded; no secret plaintext in findings/reports |

### WP5 — Aggregation, narrative, reports (Week 5–6)

| Item | Detail |
|---|---|
| Goal | Prioritised downloadable output |
| Deliverables | Dedup/fingerprint/scoring; assistive LLM narrative with deterministic fallback; HTML + Markdown renderers; preview + download path |
| Stories | US-010–US-014 |
| Exit | Immutable reports for `COMPLETED`/`PARTIAL`; filenames include domain + timestamp |

### WP6 — Hardening and MVP exit (Week 6–7)

| Item | Detail |
|---|---|
| Goal | Reliability, observability, acceptance |
| Deliverables | Retries/timeouts; budget exhaustion → `PARTIAL`; secret masking tests; correlation logs/metrics; fixture-site acceptance suite |
| Stories | US-015, US-016 |
| Exit | MVP exit criteria checklist green |

### WP7 — Production readiness (after MVP functional exit)

| Item | Detail |
|---|---|
| Goal | Deploy the HLD runtime with tenant-isolated production persistence |
| Deliverables | PostgreSQL/RLS and S3 adapters; migrations/retention; approved dispatcher/runtime topology; deployment manifests; staging restore/rollback |
| Dependencies | WP0–WP6; approved `14_Deployment.md`, `15_Cost_Optimization.md` |
| Exit | Deployment and release gates pass in staging; no SQLite/filesystem in production |

---

## 5. Recommended sprint backlog order

| Sprint | Focus | Stories |
|---|---|---|
| S1 | WP0 + WP1 | US-001, US-002 |
| S2 | WP2 | US-003, US-005 |
| S3 | WP3 | US-004, US-006, US-008, US-009 |
| S4 | WP4 | US-007, US-009 |
| S5 | WP5 | US-010–US-014 |
| S6 | WP6 | US-015, US-016 + acceptance |
| S7 | WP7 | Production readiness |

Parallelisation tip: after WP2, agent adapters can be built in parallel by different owners if contracts stay stable.

---

## 6. Dependency graph

```text
WP0 Foundations
  └─► WP1 Policy / Limits / Run lifecycle
        └─► WP2 Crawl + Browser evidence
              ├─► WP3 Core agents ──┐
              └─► WP4 Perf/Latency/Security ─┼─► WP5 Aggregate + Reports
                                             └─► WP6 Functional MVP Exit
                                                   └─► WP7 Production Readiness
```

---

## 7. Roles and ownership (suggested)

| Area | Owner focus |
|---|---|
| Domain + orchestration | Backend / platform engineer |
| Playwright + browser agents | Frontend / automation engineer |
| Lighthouse / PSI / latency | Performance-minded engineer |
| axe / HTML / SEO | Quality / a11y-capable engineer |
| Secret scan + SSRF | Security-minded engineer |
| Report HTML/MD + UI preview | Product-facing engineer |
| LLM assist gateway | AI engineer |
| Logging / budgets / deploy prep | DevOps |

---

## 8. Approved technical decisions

| Decision | Approved choice | Authority |
|---|---|---|
| Language | Python async | `05_Low_Level_Design.md` |
| Entry surface | Thin HTTP API + minimal UI preview | `06_API_Specification.md` |
| Metadata | SQLite local; PostgreSQL staging/production | `08_Database_Design.md` |
| Artifacts | Filesystem local; S3-compatible staging/production | `08_Database_Design.md` |
| LLM | Provider-independent assistive gateway with deterministic fallback | `09_AI_Architecture.md` |
| External links | Validation on by default under policy/probe budget | `11_Guardrails.md` |

---

## 9. Definition of Done (per work package)

1. Ports defined; adapters injectable; no vendor SDK in domain.
2. Unit tests for domain/application rules; integration tests for adapters where feasible.
3. Structured logs with `scan_run_id`; no secrets in logs/reports.
4. Retries bounded; failures classified (retryable vs terminal).
5. Config via env/config files only.
6. Story acceptance criteria for the package are demonstrable.

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Browser flakiness | Retries, partial reports, agent-level gaps |
| Cost overrun | Enforce WP1 governors before heavy agents |
| Scope creep (PR/deploy) | Explicit backlog filter; no adapters for VCS/deploy |
| Production docs unfinished | Hold WP7 until `14` and `15` approval |
| LLM hallucination | Assistive only; reject evidence-less narrative |

---

## 11. Explicit non-goals (MVP)

- GitHub/GitLab integration, PRs, patches, deploys
- Authenticated scanning beyond supported patterns
- Legal a11y/security certification
- Native mobile app analysis
- Raw evidence zip package (later phase)

---

## 12. Approval gate for coding

Coding may begin only when:

1. This Implementation Plan is **Approved**
2. `05_Low_Level_Design.md` is **Approved**
3. Each work package’s listed supporting documents are **Approved**
4. Production release work additionally requires approved `14_Deployment.md` and `15_Cost_Optimization.md`

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product | | Approved | 2026-08-04 |
| Engineering | | Approved | 2026-08-04 |
| AI Engineering | | Approved | 2026-08-04 |
| QA | | Approved | 2026-08-04 |
| DevOps / Security | | Approved | 2026-08-04 |
