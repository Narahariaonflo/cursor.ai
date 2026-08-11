# Engineering Backlog

## AI Website Health Orchestrator Agent


| Field         | Value                                                                                                                                              |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Product name  | AI Website Health Orchestrator Agent                                                                                                               |
| Document type | Engineering Backlog                                                                                                                                |
| Version       | 0.1                                                                                                                                                |
| Status        | Approved                                                                                                                                           |
| Upstream      | `02_User_Stories.md`, `04_High_Level_Design.md`–`13_Testing_Strategy.md` (Approved); `14`–`15` required for production milestones |
| Downstream    | Sprint planning, production release evidence                                                                                                      |
| Audience      | Engineering, QA, Product, Architecture                                                                                                             |
| Last updated  | 2026-08-05                                                                                                                                         |
| File          | `16_Engineering_Backlog.md`                                                                                                                        |


---

## 1. Purpose

This backlog decomposes the approved Implementation Plan into **independently testable milestones**.

Rules:

1. Documentation remains the source of truth.
2. No milestone starts coding until its required docs are approved.
3. Every milestone must be verifiable without depending on unfinished sibling features.
4. Placeholder adapters are forbidden.
5. Deferred PR/deploy/remediation work is excluded from MVP milestones.
6. Expedited delivery never bypasses documentation approval; any formal waiver requires recorded Architecture and Product change control.

---



## 2. Documentation gate (hard prerequisite)


| ID     | Item               | Status                                                          |
| ------ | ------------------ | --------------------------------------------------------------- |
| DOC-06 | API Specification  | Approved |
| DOC-07 | Agent Architecture | Approved |
| DOC-08 | Database Design    | Approved |
| DOC-09 | AI Architecture    | Approved |
| DOC-10 | Security           | Approved |
| DOC-11 | Guardrails         | Approved |
| DOC-13 | Testing Strategy   | Approved |
| DOC-14 | Deployment         | Approved — required before M22–M24 |
| DOC-15 | Cost Optimization  | Approved — required before M24 and production release |


**Architect rule:** Feature implementation is frozen until the docs required by each milestone below are approved.

---



## 3. Complexity scale


| Rating | Meaning                |
| ------ | ---------------------- |
| S      | 1–2 days               |
| M      | 3–5 days               |
| L      | 1–2 weeks              |
| XL     | 2+ weeks / multi-owner |


---



## 4. Milestone dependency map

```text
M0 Docs gate
 └─ M1 Foundations
     └─ M2 Domain + ports contracts
         └─ M4 Target policy + cost governor
             └─ M3 Persistence (SQLite/FS)
                 └─ M5 Run lifecycle + submit/status API
              └─ M6 Crawl planner
                   └─ M7 Browser evidence (Playwright)
                        ├─ M8 Agent coordinator
                        │    ├─ M9 SEO agent
                        │    ├─ M10 HTML agent
                        │    ├─ M11 Console agent
                        │    ├─ M12 Broken Link agent
                        │    ├─ M13 Accessibility agent
                        │    ├─ M14 Performance agent
                        │    ├─ M15 Latency agent
                        │    └─ M16 Security agent
                        └─ M17 Aggregation + scoring
                             ├─ M18 Assistive narrative (LLM)
                             └─ M19 Report render + preview/download
                                  └─ M20 API + minimal UI contract
                                       └─ M21 Hardening + functional MVP exit
                                            └─ M22 Production data adapters
                                                 └─ M23 Durable deployment runtime
                                                      └─ M24 Production cost/release validation
```

Independent testability note: M9–M16 may proceed in parallel after M7 and M8, each with fixture inputs and mocked ports.

---



## 5. Milestones



### M0 — Documentation completion gate

- **Goal:** Approve remaining architecture docs required for safe implementation.
- **Modules:** `docs/06`–`11`, `docs/13`; production extension `docs/14`–`15`
- **Estimated complexity:** L
- **Dependencies:** Approved `04`, `05`, `12`
- **Stories:** Enables all
- **Acceptance criteria:**
  1. Docs `06`–`11` and `13` are approved; `14`–`15` gate production milestones only.
  2. Open decisions in LLD/Implementation Plan are closed or explicitly accepted.
  3. Coding freeze is lifted only for milestones whose required docs are approved.
- **Tests required:** Documentation review checklist; architecture compliance review against existing scaffold.

---



### M1 — Foundations and composition root

- **Goal:** Establish production package layout, config, logging, and DI wiring.
- **Modules:** `config`, `bootstrap`, logging infrastructure
- **Estimated complexity:** M
- **Dependencies:** M0, `05` LLD
- **Stories:** Enables all
- **Acceptance criteria:**
  1. Clean Architecture package layout exists and is DI-wired.
  2. Settings load only from environment/config files.
  3. Structured logger is available to application services.
  4. Domain layer has no vendor SDK imports.
- **Tests required:**
  - Unit: settings loading defaults and overrides
  - Smoke: container builds without circular imports
  - Architecture: dependency-direction lint/check (domain isolation)

---



### M2 — Domain model and outbound port contracts

- **Goal:** Encode invariants and port interfaces without unfinished adapters.
- **Modules:** `domain/entities`, `domain/value_objects`, `domain/services`, `domain/exceptions`, `ports/outbound`
- **Estimated complexity:** M
- **Dependencies:** M1
- **Stories:** Enables US-001–US-016
- **Acceptance criteria:**
  1. `AnalysisRun`, `Finding`, `Evidence`, and related value objects enforce approved invariants.
  2. Findings without evidence are rejected by domain rules.
  3. Ports for browser/Lighthouse/axe exist as interfaces only until real adapters land.
  4. No placeholder adapter classes exist.
- **Tests required:**
  - Unit: finding evidence invariant
  - Unit: run state transition rules
  - Unit: preference validation (`max_pages`, `max_depth`)

---



### M3 — Persistence and artifact storage

- **Goal:** Persist runs/findings and immutable report artifacts with tenant isolation hooks.
- **Modules:** `adapters/outbound/sqlite`, `adapters/outbound/filesystem`, `ScanRepositoryPort`, `ArtifactStorePort`
- **Estimated complexity:** M
- **Dependencies:** M2, M4, DOC-08
- **Stories:** Enables US-001, US-013, US-014
- **Acceptance criteria:**
  1. Runs can be saved and reloaded by `run_id`.
  2. Report artifacts are immutable after write.
  3. Artifact paths are tenant-scoped (or equivalent isolation strategy from DOC-08).
  4. Persistence adapters are injectable via DI.
- **Tests required:**
  - Integration: save/load round-trip for runs
  - Integration: artifact write/read and immutability
  - Unit: repository failure classification

---



### M4 — Target policy and cost governor

- **Goal:** Enforce SSRF/allow-deny and hard operational limit checks before work expands.
- **Modules:** `policy_services`, `limit_services`, `TargetPolicyPort`, `CostGovernorPort`
- **Estimated complexity:** M
- **Dependencies:** M2, DOC-10, DOC-11
- **Stories:** US-002, US-015 (partial)
- **Acceptance criteria:**
  1. Denied/local/SSRF-unsafe targets fail before any fetch.
  2. Over-limit preferences are rejected; requests may reduce but never raise effective policy.
  3. Policy denials are logged with correlation metadata and without secrets.
- **Tests required:**
  - Unit: SSRF/deny cases
  - Unit: budget/limit validation matrix
  - Integration: denied target never triggers browser/network adapter

---



### M5 — Run lifecycle use cases

- **Goal:** Create, validate, plan, and query runs through the approved submit/status API.
- **Modules:** `application/use_cases`, `application/dto`, `ports/inbound`, submit/status API adapter
- **Estimated complexity:** M
- **Dependencies:** M3, M4
- **Stories:** US-001, US-002
- **Acceptance criteria:**
  1. Valid requests create a unique `run_id` and store preferences.
  2. Invalid URLs return clear validation errors.
  3. Status queries return state, progress counters, and terminal reason when present.
  4. This milestone owns states through `PLANNING`/policy `FAILED`; execution owns later transitions.
  5. Submit/status routes conform to DOC-06 without report/UI dependencies.
- **Tests required:**
  - Unit: start-run happy path
  - Unit: validation failure path
  - Unit: status mapping
  - Integration: create + status persistence
  - API contract: submit/status success and error schemas

---



### M6 — Bounded crawl planner

- **Goal:** Build a page queue that respects page and depth caps.
- **Modules:** `application/orchestration/crawl_planner`
- **Estimated complexity:** M
- **Dependencies:** M5, DOC-11
- **Stories:** US-003
- **Acceptance criteria:**
  1. Queue size never exceeds `max_pages`.
  2. Depth never exceeds `max_depth`.
  3. Limit exhaustion records explicit coverage limitations.
  4. Denied/excluded URLs are not queued.
- **Tests required:**
  - Unit: breadth-first planning under caps
  - Unit: exclude/deny filtering
  - Unit: coverage limitation metadata

---



### M7 — Browser evidence collection

- **Goal:** Capture real page evidence via Playwright with budget-aware screenshot handling.
- **Modules:** `adapters/outbound/browser`, `BrowserPort`, browser evidence collector
- **Estimated complexity:** L
- **Dependencies:** M3, M6, DOC-07, DOC-10
- **Stories:** US-005
- **Acceptance criteria:**
  1. Successful page load yields URL plus at least one evidence artifact.
  2. Screenshot budget exhaustion continues the run with an explicit gap.
  3. Navigation failures after retries are recorded as gaps, not silent success.
  4. No secrets appear in stored console/DOM summaries.
- **Tests required:**
  - Integration: fixture page capture
  - Unit: screenshot budget skip behavior
  - Integration: retry exhaustion gap recording
  - Security: redaction of token-like console content

---



### M8 — Agent execution coordinator

- **Goal:** Dispatch specialised agents under concurrency and budget constraints.
- **Modules:** `application/orchestration/agent_execution_coordinator`
- **Estimated complexity:** M
- **Dependencies:** M7, DOC-07, DOC-11
- **Stories:** US-004
- **Acceptance criteria:**
  1. Independent agent tasks may run in parallel within limits.
  2. Pressure/limit exhaustion degrades to queued execution without losing completed findings.
  3. Agent durations/failures are correlatable by `scan_run_id`.
  4. One agent failure does not cancel other agents.
- **Tests required:**
  - Unit: concurrency capping
  - Unit: failure isolation
  - Unit: correlation metadata on agent results
  - Integration: multi-agent fake adapters under budget pressure

---



### M9 — SEO agent

- **Goal:** Detect SEO metadata/structure issues with evidence.
- **Modules:** `agent_services/seo`, SEO-related ports/adapters as approved
- **Estimated complexity:** M
- **Dependencies:** M7, M8, DOC-07
- **Stories:** US-006
- **Acceptance criteria:**
  1. Missing title/canonical (and approved SEO signals) create evidence-backed findings.
  2. Affected page URL is always present.
  3. Agent failure records a gap and does not fail the whole run.
- **Tests required:**
  - Unit: missing title/canonical fixtures
  - Unit: evidence invariant on SEO findings
  - Integration: agent failure isolation under coordinator

---



### M10 — HTML document agent

- **Goal:** Detect document structure and markup issues.
- **Modules:** `agent_services/html`, `HtmlAnalysisPort` adapter
- **Estimated complexity:** M
- **Dependencies:** M7, M8, DOC-07
- **Stories:** US-009 (HTML portion)
- **Acceptance criteria:**
  1. Structural issues produce findings with page and rule/signal evidence.
  2. Shared DOM snapshots are reused where possible.
  3. Failures are agent-scoped.
- **Tests required:**
  - Unit: duplicate/missing tag fixtures
  - Unit: heading-order / language / viewport fixtures
  - Integration: snapshot reuse path

---



### M11 — Browser console agent

- **Goal:** Detect JS errors, failed loads, and relevant console warnings.
- **Modules:** `agent_services/console`
- **Estimated complexity:** S
- **Dependencies:** M7, M8, DOC-07
- **Stories:** US-005 (console findings), US-009 adjacency
- **Acceptance criteria:**
  1. Console errors become findings with page evidence.
  2. Sensitive values in messages are masked.
  3. Agent can operate from captured browser evidence without re-navigation when available.
- **Tests required:**
  - Unit: console error → finding mapping
  - Unit: secret masking in console text
  - Integration: fixture page with seeded console error

---



### M12 — Broken link agent

- **Goal:** Detect broken links, redirect chains, and malformed URLs.
- **Modules:** `agent_services/broken_link`, `LinkCheckPort` adapter
- **Estimated complexity:** M
- **Dependencies:** M6, M8, DOC-07, DOC-11
- **Stories:** US-008
- **Acceptance criteria:**
  1. In-scope broken links produce findings with source, target, and status evidence.
  2. Redirect/malformed URL issues are reported with evidence.
  3. External-link validation is enabled by default; explicit disable records a report coverage limitation.
- **Tests required:**
  - Unit: 404 internal link fixture
  - Unit: redirect chain fixture
  - Unit: external-link default-on and disable-with-limitation behavior
  - Integration: link checker adapter against local fixture server

---



### M13 — Accessibility agent

- **Goal:** Detect axe-core violations above configured impact.
- **Modules:** `agent_services/accessibility`, `AxePort` adapter
- **Estimated complexity:** M
- **Dependencies:** M7, M8, DOC-07
- **Stories:** US-009 (a11y portion)
- **Acceptance criteria:**
  1. Violations include rule id, impact, and target evidence.
  2. No certification claims are made in outputs.
  3. Tool failure records an explicit gap.
- **Tests required:**
  - Integration: seeded axe-detectable violation
  - Unit: impact threshold filtering
  - Unit: gap recording on tool failure

---



### M14 — Performance agent

- **Goal:** Produce Lighthouse-backed performance findings and optional PSI data.
- **Modules:** `agent_services/performance`, `LighthousePort` adapter, optional `PsiPort`
- **Estimated complexity:** L
- **Dependencies:** M7, M8, DOC-07, DOC-11
- **Stories:** US-007 (performance portion)
- **Acceptance criteria:**
  1. Threshold breaches create metric-backed findings.
  2. Raw Lighthouse artifacts are referenceable.
  3. Tool failure records a gap, not success.
  4. PSI is used only when configured and budgeted.
- **Tests required:**
  - Integration: Lighthouse fixture/threshold breach
  - Unit: PSI disabled-by-default behavior
  - Unit: artifact reference linkage
  - Unit: tool-failure gap path

---



### M15 — Latency agent

- **Goal:** Detect DNS/TLS/TTFB/document and slow-resource latency issues.
- **Modules:** `agent_services/latency`, `HeaderProbePort` / browser timing signals
- **Estimated complexity:** M
- **Dependencies:** M7, M8, DOC-07
- **Stories:** US-007 (latency portion)
- **Acceptance criteria:**
  1. Latency findings include timing evidence and page URL.
  2. Thresholds come from configuration, not hardcoding.
  3. Failures are agent-scoped and reported.
- **Tests required:**
  - Unit: timing threshold evaluation
  - Integration: captured network timing fixture
  - Unit: config-driven thresholds

---



### M16 — Security hygiene agent

- **Goal:** Detect mixed content, insecure forms, missing headers, and client-side secret patterns with masking.
- **Modules:** `agent_services/security`, `SecretScanPort`, `HeaderProbePort`
- **Estimated complexity:** M
- **Dependencies:** M7, M8, DOC-07, DOC-10
- **Stories:** US-009 (security portion), US-016 (masking adjacency)
- **Acceptance criteria:**
  1. Security findings are created with masked evidence only.
  2. Secret-like values never appear in plaintext in findings/reports/logs.
  3. Missing security headers and mixed content are detectable from approved signals.
- **Tests required:**
  - Unit: secret pattern detection + masking
  - Unit: mixed content / insecure form fixtures
  - Integration: header probe fixture
  - Security regression: no plaintext secrets in outputs

---



### M17 — Aggregation, deduplication, and scoring

- **Goal:** Normalize, dedupe, and prioritise findings using domain rules.
- **Modules:** `application/orchestration/finding_aggregation`, domain scoring services
- **Estimated complexity:** M
- **Dependencies:** M8; single-agent fixtures permit independent development, but all M9–M16 are required for MVP exit
- **Stories:** US-010, US-011
- **Acceptance criteria:**
  1. Equivalent findings merge with occurrence metadata and retained affected URLs.
  2. Critical/high findings rank above lower-impact items.
  3. Evidence-free findings cannot enter the ranked set.
  4. Deterministic domain scoring remains authoritative over any AI suggestion.
- **Tests required:**
  - Unit: fingerprint identity and dedupe
  - Unit: ranking fixtures (critical vs info)
  - Unit: evidence-less finding rejection
  - Property/unit: occurrence count preservation

---



### M18 — Assistive narrative (LLM)

- **Goal:** Produce business-readable summary assistance without becoming an evidence source.
- **Modules:** `adapters/outbound/llm`, `LlmAssistPort`, assistive narrative service
- **Estimated complexity:** M
- **Dependencies:** M17, DOC-09, DOC-11
- **Stories:** US-012
- **Acceptance criteria:**
  1. Narrative reflects actual findings and limitations.
  2. AI cannot invent findings without evidence.
  3. Token/budget exhaustion falls back to deterministic summary and still allows publish.
  4. Provider SDKs remain behind the port; prompts are externalized.
- **Tests required:**
  - Unit: reject AI output that references missing findings
  - Unit: deterministic fallback when LLM unavailable/budget exhausted
  - Integration: provider adapter contract with fake/recorder
  - Security: untrusted page content cannot override policy

---



### M19 — Report composition, preview model, and downloads

- **Goal:** Publish immutable HTML and Markdown reports with required structure.
- **Modules:** `report_services`, `ReportRendererPort` adapters, download/preview application services
- **Estimated complexity:** M
- **Dependencies:** M17; M18 optional (fallback required)
- **Stories:** US-013, US-014
- **Acceptance criteria:**
  1. Preview includes summary, top findings, grouped findings, evidence refs, limitations.
  2. HTML and Markdown downloads are available for `COMPLETED`/`PARTIAL`.
  3. Artifacts are immutable for a given run.
  4. Filenames include domain and timestamp.
- **Tests required:**
  - Unit: report model composition
  - Integration: HTML/Markdown artifact generation
  - Integration: immutability re-fetch
  - Unit: filename pattern

---



### M20 — Report API and minimal UI completion

- **Goal:** Complete preview/download routes and thin UI with no business logic leakage.
- **Modules:** `adapters/inbound/api`, `adapters/inbound/ui`, inbound ports
- **Estimated complexity:** M
- **Dependencies:** M5 submit/status API, M19, DOC-06
- **Stories:** US-001, US-013, US-014 (delivery surface)
- **Acceptance criteria:**
  1. Combined M5/M20 API supports submit, status, preview, and download per approved API spec.
  2. UI can submit a scan, show status/preview, and download reports.
  3. Adapters call use cases only; no domain logic in UI/API layers.
  4. Error model matches DOC-06.
- **Tests required:**
  - API contract tests for success and validation errors
  - Integration: end-to-end submit → publish → download
  - UI smoke: preview and download actions
  - Architecture: inbound adapter dependency checks

---



### M21 — Hardening, observability, and functional MVP exit

- **Goal:** Prove reliability, cost control, secret safety, and full MVP exit criteria.
- **Modules:** retries/timeouts, metrics, masking verification, acceptance fixtures
- **Estimated complexity:** L
- **Dependencies:** M7–M20, DOC-10, DOC-11, DOC-13
- **Stories:** US-015, US-016 + MVP exit criteria
- **Acceptance criteria:**
  1. Budget exhaustion yields `PARTIAL` with explicit limitations when usable findings exist.
  2. Unrecoverable no-evidence failures yield `FAILED`.
  3. Logs are correlatable by `scan_run_id` and contain no secrets/credentials.
  4. Required S17 run/agent/policy/budget metrics and bounded dimensions are emitted.
  5. All functional MVP exit criteria in Implementation Plan §2 are demonstrably green.
- **Tests required:**
  - Integration: budget exhaustion → PARTIAL
  - Integration: total failure → FAILED
  - Observability: correlation ID assertions
  - Observability: required metrics and forbidden-field assertions
  - Security: secret-leak regression suite
  - Acceptance: fixture-site end-to-end suite covering US-001–US-016

---

### M22 — Production data adapters

- **Goal:** Replace local-only persistence with tenant-isolated production stores.
- **Modules:** PostgreSQL repository/RLS, S3-compatible artifact adapter
- **Estimated complexity:** L
- **Dependencies:** M21, DOC-08, approved DOC-14
- **Acceptance criteria:** Repository/artifact contracts pass; RLS prevents cross-tenant reads; report objects are private, immutable, and checksum-verified.
- **Tests required:** PostgreSQL/RLS and S3 contract/integration suites; cross-tenant and failure-reconciliation tests.

---

### M23 — Durable deployment runtime

- **Goal:** Deploy recoverable API/dispatcher/scan-worker, migration, and retention units.
- **Modules:** durable leases, migrations, retention, health/metrics, deployment manifests
- **Estimated complexity:** XL
- **Dependencies:** M22, approved DOC-14
- **Acceptance criteria:** Accepted work survives worker failure; isolated jobs and restricted egress pass; migration/restore/rollback rehearsals pass.
- **Tests required:** DOC-14 deployment, fault-injection, migration, backup/restore, and isolation suites.

---

### M24 — Production cost and release validation

- **Goal:** Validate HLD cost bounds and production release evidence.
- **Modules:** capacity/load baselines, cost telemetry, optimization policy, release runbook
- **Estimated complexity:** M
- **Dependencies:** M23, approved DOC-15
- **Acceptance criteria:** Global/per-run budgets compose without overspend; measured cost envelope and release checklist are approved.
- **Tests required:** Load/cost benchmark, limit-exhaustion, scaling/fairness, and release acceptance suites.

---



## 6. Story → milestone traceability


| Story  | Primary milestones |
| ------ | ------------------ |
| US-001 | M5                 |
| US-002 | M4, M5             |
| US-003 | M6                 |
| US-004 | M8                 |
| US-005 | M7, M11            |
| US-006 | M9                 |
| US-007 | M14, M15           |
| US-008 | M12                |
| US-009 | M10, M13, M16      |
| US-010 | M17                |
| US-011 | M17                |
| US-012 | M18                |
| US-013 | M19, M20           |
| US-014 | M19, M20           |
| US-015 | M4, M21            |
| US-016 | M16, M21           |


---



## 7. Recommended delivery waves


| Wave   | Milestones | Intent                                    |
| ------ | ---------- | ----------------------------------------- |
| Wave 0 | M0         | Documentation clearance                   |
| Wave 1 | M1–M5      | Safe run control plane                    |
| Wave 2 | M6–M8      | Crawl + evidence + dispatch               |
| Wave 3 | M9–M16     | Independently testable specialised agents |
| Wave 4 | M17–M20    | Aggregation, narrative, reports, API/UI   |
| Wave 5 | M21        | Hardening and functional MVP exit         |
| Wave 6 | M22–M24    | Production readiness and release          |


---



## 8. Explicit non-backlog (MVP)

Do not schedule milestones for:

- GitHub/GitLab integration
- PR creation / patches / deploys
- Authenticated scanning beyond approved patterns
- Legal a11y/security certification
- Native mobile analysis
- Raw evidence zip package

---



## 9. Backlog governance

1. A milestone is **Ready** only when its listed documentation dependencies are approved.
2. A milestone is **Done** only when acceptance criteria and required tests pass.
3. If implementation and documentation conflict, documentation wins and code is corrected.
4. Existing provisional scaffold must be reconciled to approved docs during Wave 1; it is not an authority source.

---



## Document approval


| Role                     | Name | Decision | Date |
| ------------------------ | ---- | -------- | ---- |
| Product                  |      | Approved | 2026-08-06 |
| Engineering Architecture |      | Approved | 2026-08-06 |
| Engineering              |      | Approved | 2026-08-06 |
| QA                       |      | Approved | 2026-08-06 |
| DevOps / Security        |      | Approved | 2026-08-06 |
| AI Engineering           |      | Approved | 2026-08-06 |


