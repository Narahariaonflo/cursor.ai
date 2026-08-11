# Product Requirements Document
## AI Website Reliability Engineer (ORCA)

| Field | Value |
|---|---|
| Product name | AI Website Reliability Engineer (ORCA) |
| Document type | Product Requirements Document (PRD) |
| Version | 0.2 |
| Status | Approved |
| Owners | Product, Engineering, AI Platform |
| Last updated | 2026-08-06 |
| Source | ORCA AI Website Maintenance Agent Research |
| Binding MVP scope | `04_High_Level_Design.md` v2.0 (Approved); it supersedes conflicting PRD scope |

---

## 1. Executive Summary

ORCA is an **AI Website Reliability Engineer**. The focused MVP performs user-initiated, read-only analysis of public websites for SEO, performance, latency, broken links, console/runtime, HTML, security hygiene, and basic accessibility, then produces evidence-backed health reports.

Unlike traditional uptime monitors or scripted test suites, ORCA combines:

- Playwright browser evidence and deterministic scanners (Lighthouse, axe-core, HTML/SEO, headers and link probes)
- Eight specialized analysis agents coordinated under bounded cost and security policy
- Assistive LLM explanation, deduplication support, and narrative with deterministic fallback
- Tenant-isolated findings, artifacts, preview, and immutable HTML/Markdown downloads

**Positioning:** ORCA is a read-only website health analyst in MVP. Remediation, repository access, PRs, and deployment are later-phase capabilities.

**MVP outcome:** Submit → validate → bounded crawl → analyze → prioritize → preview/download HTML and Markdown.  
**Later phases:** Root-cause analysis, regressions, patches/PRs, then autonomous validation with explicit deploy approval.

---

## 2. Goals

### 2.1 Primary goals

1. **Unify website health signals** into one workflow: SEO, performance, latency, broken links, console, HTML, security hygiene, and accessibility.
2. **Deliver actionable prioritized findings** ranked by business impact, not raw issue dumps.
3. **Reduce manual website QA and SRE toil** for bounded on-demand checks.
4. **Keep humans in control** of deployments, merges, DNS, DB, and production mutations.
5. **Control cost and noise** via crawl/tool/token budgets, bounded evidence, and caching.
6. **Establish a replaceable AI stack** (provider-agnostic) suitable for enterprise deployment and future local/cloud models.

### 2.2 Product outcomes

| Outcome | Description |
|---|---|
| Unified visibility | Operators receive one evidence-backed health view per analysis run |
| Faster triage | Issues classified, deduplicated, and prioritized automatically |
| Actionable guidance | Reports explain impact and recommended remediation without changing systems |
| Trustworthy automation | Guardrails, approval gates, and auditability for enterprise use |

---

## 3. Non Goals

The following are explicitly **out of scope** for the product vision as currently defined (especially MVP):

1. **Fully autonomous production operations** — no automatic deploy, merge, DNS, DB, secret, billing, or auth changes.
2. **General-purpose website builder / CMS** — ORCA does not author or publish marketing content as a primary product.
3. **Replacement of APM / infrastructure monitoring platforms** — ORCA complements (does not replace) Datadog, New Relic, Prometheus, etc. for infra/backend telemetry.
4. **Arbitrary remote code execution on production** — never execute unrestricted production shell commands.
5. **Guaranteed zero false positives** — baselines and thresholds reduce noise; perfect precision is not promised.
6. **Monolithic single-agent design as the target architecture** — research recommends multi-agent; a monolith is not a long-term goal.
7. **Unlimited page crawling / unbounded AI spend** — operational limits and budgets are mandatory.
8. **Legal/compliance certification as a product claim in MVP** — accessibility scans assist WCAG efforts; ORCA does not claim formal certification.

---

## 4. Business Requirements

| ID | Requirement | Rationale |
|---|---|---|
| BR-01 | Product must be positioned and sold/used as an **AI Website Reliability Engineer**, not a simple maintenance script. | Research recommendation; clearer enterprise value. |
| BR-02 | System must produce **prioritized maintenance reports** usable by engineering and product stakeholders. | Actionability over volume. |
| BR-03 | High-impact actions require **human approval**. | Risk, compliance, trust. |
| BR-04 | Solution must support **cost-aware operation** (MVP hard budgets/limits; incremental work later). | AI + browser infra cost control. |
| BR-05 | Findings must be **comparable over time** (baselines, trends, regression detection in later phases). | Reduce false positives; show reliability improvement. |
| BR-06 | Product roadmap must ship in **phased value**: MVP report → assisted maintenance engineer → approval-gated autonomy. | Avoid overbuilding before validation. |
| BR-07 | Architecture must allow **provider interchangeability** and future local models where feasible. | Cost, latency, data residency, vendor lock-in. |
| BR-08 | All secrets and credentials must come from **environment/config**, never hardcoded. | Enterprise security baseline. |
| BR-09 | System behavior must be **auditable** (structured logs of decisions, scans, approvals). | Enterprise operations and incident review. |
| BR-10 | Features should remain **independently deployable** where practical. | Scalability and team ownership. |

---

## 5. Functional Requirements

### 5.1 Website discovery and crawling

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Accept a target site (base URL / site config) and discover pages within configured scope. | MVP |
| FR-02 | Support crawl limits (max pages, depth, include/exclude patterns). | MVP |
| FR-03 | Detect internal and external broken links/status/redirect issues under target policy and probe budget. | MVP |
| FR-04 | Support authenticated target flows and consent/cookie automation. | Phase 2 |

### 5.2 Browser execution

| ID | Requirement | Priority |
|---|---|---|
| FR-05 | Launch a browser agent to load pages in a real browser context (Playwright-class automation). | MVP |
| FR-06 | Capture bounded screenshots only when required as report evidence. | MVP |
| FR-07 | Collect browser console logs and surface errors/warnings in findings. | MVP |
| FR-08 | Handle modern web behaviors where feasible: lazy loading, dynamic content, basic feature-flag awareness. | Phase 2 |
| FR-09 | Reuse browser sessions where safe to reduce cost/latency. | MVP |

### 5.3 Deterministic quality scans

| ID | Requirement | Priority |
|---|---|---|
| FR-10 | Run performance audits (e.g., Lighthouse and/or PageSpeed Insights API). | MVP |
| FR-11 | Run accessibility scans (e.g., axe-core). | MVP |
| FR-12 | Perform SEO analysis via DOM/metadata parsing (titles, meta, headings, canonical, robots signals as applicable). | MVP |
| FR-13 | Persist raw scan artifacts for audit and re-analysis. | MVP |

### 5.4 AI analysis and vision

| ID | Requirement | Priority |
|---|---|---|
| FR-14 | Use an LLM only to explain evidence-backed findings, assist deduplication, and generate narrative; deterministic rules own findings/severity/confidence. | MVP |
| FR-15 | Use vision-capable models for visual/branding analysis. | Phase 2 |
| FR-16 | Route assistive AI through provider-independent `LlmAssistPort`, preferring approved local models when feasible. | MVP |
| FR-17 | Use capability/cost routing only for approved assistive AI tasks. | Phase 2 |
| FR-18 | Use embeddings for historical issue similarity / retrieval (at least designed; may land Phase 2). | Phase 2 |

### 5.5 Multi-agent orchestration

| ID | Requirement | Priority |
|---|---|---|
| FR-19 | Orchestrate SEO, performance, latency, broken-link, console, HTML, security, and accessibility agents plus report generation. | MVP |
| FR-20 | Planner produces a scan/analysis plan within operational limits. | MVP |
| FR-21 | Report Generator publishes structured preview plus immutable HTML and Markdown health reports. | MVP |

### 5.6 Reporting and prioritization

| ID | Requirement | Priority |
|---|---|---|
| FR-22 | Produce preview and downloadable HTML/Markdown reports with severity, category, evidence, recommended action, impact, coverage, and limitations. | MVP |
| FR-23 | Support configurable thresholds and baseline comparison to suppress known/noisy findings. | Phase 2 |
| FR-24 | Generate weekly/periodic maintenance reports. | Phase 2 |
| FR-25 | Provide historical trend / regression views. | Phase 2 |

### 5.7 Remediation assistance (post-MVP)

| ID | Requirement | Priority |
|---|---|---|
| FR-26 | Perform root-cause analysis linking symptoms to likely causes. | Phase 2 |
| FR-27 | Suggest code patches and create pull requests (never auto-merge). | Phase 2 |
| FR-28 | Generate fixes, run tests, validate changes; deploy **only** after explicit user approval. | Phase 3 |

### 5.8 Guardrails and approvals

| ID | Requirement | Priority |
|---|---|---|
| FR-29 | **Allowed without approval:** read site content, screenshots, Lighthouse/a11y/SEO scans, console inspection, reports, suggest fixes, create PRs (PR creation may be Phase 2). | MVP+ |
| FR-30 | **Require approval:** deploy, merge PRs, modify production systems, change DNS, edit databases, publish content. | All phases |
| FR-31 | **Never automatic:** arbitrary production shell commands, secret rotation, exposing env vars, modifying billing or authentication settings. | All phases |
| FR-32 | Enforce operational limits: confidence thresholds, API budgets, page scan limits, retries, timeouts, recursion depth. | MVP |

---

## 6. Non Functional Requirements

### 6.1 Reliability and resilience

| ID | Requirement |
|---|---|
| NFR-01 | Gracefully handle page load failures, timeouts, and partial scan failures without aborting the entire job when recoverable. |
| NFR-02 | Implement retries with bounded attempts for transient browser/API failures. |
| NFR-03 | Never swallow exceptions; record structured failure reasons. |

### 6.2 Performance and cost

| ID | Requirement |
|---|---|
| NFR-04 | Optimize for **cost first**, reliability second, speed third (product principle). |
| NFR-05 | Minimize assistive AI calls via bounded context, caching, and deterministic fallback. |
| NFR-06 | Avoid unnecessary screenshots; capture only when required for evidence. |
| NFR-07 | MVP scans are on-demand and bounded; scheduling, baselines, and incremental comparison are Phase 2. |

### 6.3 Security and privacy

| ID | Requirement |
|---|---|
| NFR-08 | Secrets only from environment variables / secure config. |
| NFR-09 | Least-privilege workload identity for browser, storage, database, and approved provider APIs. |
| NFR-10 | Validate external inputs (URLs, selectors, configs); sanitize AI outputs before acting on them. |
| NFR-11 | Never log secrets, tokens, or raw credential material. |

### 6.4 Observability

| ID | Requirement |
|---|---|
| NFR-12 | Structured logging for scan jobs, agent decisions, model calls (metadata), and approvals. |
| NFR-13 | Traceability from report finding → evidence artifact → scan run ID. |

### 6.5 Architecture quality

| ID | Requirement |
|---|---|
| NFR-14 | Clean Architecture; domain separated from infrastructure; DI throughout. |
| NFR-15 | Business logic must not depend on a specific LLM vendor; assistive AI uses `LlmAssistPort`. |
| NFR-16 | Modules replaceable; no circular dependencies; one responsibility per module/class. |
| NFR-17 | Prompt templates externalized (e.g., config/prompts), not embedded in business logic. |
| NFR-18 | Public methods: type hints + docstrings; testable units; target ≥90% coverage for product code. |
| NFR-19 | Prefer async I/O; pathlib for filesystem; keep files ≤300 lines unless justified. |

### 6.6 Scalability

| ID | Requirement |
|---|---|
| NFR-20 | Design for future multi-site / multi-tenant and distributed agents without redesigning domain core. |
| NFR-21 | Features independently deployable where practical. |

### 6.7 Usability (report consumers)

| ID | Requirement |
|---|---|
| NFR-22 | Reports must be readable by both engineers and non-engineers: plain-language summary + technical evidence. |
| NFR-23 | Default report length optimized for action (top issues first); full detail available on demand. |

---

## 7. Success Metrics

Success is measured by whether ORCA **finds real issues, ranks them usefully, stays affordable, and earns trust**.

| Metric | Definition | MVP target (indicative) |
|---|---|---|
| Time-to-first-report | Time from configured site → first usable prioritized report | ≤ 30–60 min for a small site (≤25 pages), excluding cold infra setup |
| Actionable finding rate | % of top-priority findings accepted as valid by a human reviewer | ≥ 70% |
| Critical miss rate | % of known seeded critical issues missed in controlled eval sites | ≤ 10% |
| Noise rate | % of findings dismissed as false positive / non-actionable in top N | ≤ 30% initially; improve with baselines |
| Scan completion rate | % of requested MVP runs that complete with partial-or-full report | ≥ 95% |
| Cost per scan | Fully loaded AI + browser cost per standard scan profile | Within agreed budget envelope (set per env) |
| Approval compliance | High-impact actions attempted without approval | 0 |

---

## 8. KPIs

### 8.1 Product KPIs

| KPI | Description | Cadence |
|---|---|---|
| Sites under active scan | Number of sites/environments regularly scanned | Weekly |
| Findings resolved | Count/rate of ORCA findings closed by teams | Monthly |
| Median time-to-triage | Time from finding created → human first action | Weekly |
| Recurring issue reduction | Repeat findings of same fingerprint over time | Monthly |
| Report adoption | % of reports reviewed by an owner within SLA | Weekly |

### 8.2 Engineering / AI ops KPIs

| KPI | Description | Cadence |
|---|---|---|
| Token/$ spend per site | AI cost efficiency | Weekly |
| Cache hit rate | Reused embeddings/results/screenshots avoided | Weekly |
| Agent failure rate | Browser/vision/planner hard failures | Daily |
| Mean scan duration | p50/p95 job duration by profile | Weekly |
| Guardrail block events | Blocked disallowed actions | Weekly |

### 8.3 Quality KPIs

| KPI | Description | Cadence |
|---|---|---|
| Precision@Top10 | Valid issues in top 10 prioritized findings | Per eval cycle |
| Accessibility issue confirmation rate | Confirmed a11y findings vs dismissed | Monthly |
| Visual regression precision | Confirmed visual defects vs noise | Monthly |
| SEO finding usefulness score | Stakeholder rating 1–5 | Monthly |

---

## 9. User Personas

| Persona | Goals | Needs from ORCA | Pain today |
|---|---|---|---|
| **Website SRE / Reliability Engineer** | Keep marketing/app sites healthy; reduce incidents from front-door failures | Prioritized reliability signals, console errors, perf regressions, audit trail | Fragmented tools; alert fatigue |
| **Frontend / Web Engineer** | Fix real UX/perf/a11y issues quickly | Evidence (screenshots, traces), suggested patches/PRs, reproducible steps | Manual Lighthouse/a11y runs; flaky E2E scripts |
| **QA Engineer** | Catch regressions before/after release | Visual + functional health diffs, baselines, repeatable scan profiles | Brittle selectors; incomplete coverage |
| **DevOps / Platform Engineer** | Operate scans safely in CI/CD and prod-adjacent envs | Budgets, secrets via env, approvals, observability, least privilege | Unbounded crawlers; unsafe automation |
| **AI Engineer** | Improve agent quality and cost | Provider abstraction, eval harness, prompt/config separation, metrics | Vendor lock-in; untestable prompts in code |
| **Product Manager / Site Owner** | Understand business impact of site issues | Plain-language summary, prioritized backlog, weekly health narrative | Technical dumps with no prioritization |
| **Accessibility / SEO Specialist** | Improve compliance and discoverability | Structured a11y/SEO findings with evidence | One-off audits that go stale |
| **Engineering Manager** | Prove ROI and risk reduction | KPIs, trend reduction, cost controls | Unclear value of AI tooling |

---

## 10. Constraints

| ID | Constraint |
|---|---|
| C-01 | Human approval required for all high-impact production mutations. |
| C-02 | No automatic execution of forbidden actions (secrets, billing, auth settings, arbitrary prod shell). |
| C-03 | AI providers must be interchangeable via interface; no business-logic vendor coupling. |
| C-04 | Configuration and secrets via env/config only. |
| C-05 | Operational limits mandatory: budgets, page caps, timeouts, retries, recursion depth, confidence gates. |
| C-06 | MVP must remain intentionally narrow: crawl + scan + analyze + report. |
| C-07 | Modern web complexity (auth, banners, lazy load, flags) may limit completeness; document assumptions per site profile. |
| C-08 | Cost envelope must be enforceable per environment/tenant. |
| C-09 | Clean Architecture / SOLID / DI / testability standards apply to all implementation (post-doc approval). |
| C-10 | Prefer approved local models when feasible; cloud models require clear assistive value and approved data handling. |

---

## 11. Risks

| ID | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-01 | Scope creep into full autonomous DevOps in MVP | High | High | Hard Non-Goals + phased roadmap; approval gate on docs/code |
| R-02 | AI + browser cost overrun | High | High | Page/browser/tool/screenshot/token budgets and deterministic fallback |
| R-03 | False positives erode trust | High | High | Evidence invariants, deterministic rules, confidence, fixture evaluation |
| R-04 | Flaky scans on dynamic/SPA sites | Medium | High | Stable wait strategies, retry policy, partial-result reports |
| R-05 | Auth / cookie / bot walls block crawling | High | Medium | Public unauthenticated target constraint and explicit coverage limitations |
| R-06 | Dynamic content reduces repeatability | Medium | Medium | Bounded retries, stable fixtures, timestamps, explicit limitations |
| R-07 | Unsafe remediation suggestions applied carelessly | High | Medium | Suggest-only in Phase 2; never auto-merge/deploy; policy engine |
| R-08 | Vendor lock-in / model breakage | Medium | Medium | `LlmAssistPort`; provider adapters; prompt externalization; fallback |
| R-09 | Legal exposure from overclaiming a11y compliance | Medium | Low | Position as assistance, not certification |
| R-10 | Data leakage via prompts/logs (PII on pages) | High | Medium | Redaction policies, log scrubbing, retention limits |

---

## 12. Acceptance Criteria

### 12.1 Document / product definition acceptance

- [x] Stakeholders agree ORCA is positioned as **AI Website Reliability Engineer**
- [x] Goals / Non-Goals accepted without contradiction
- [x] MVP vs Phase 2 / Phase 3 boundaries accepted
- [x] Guardrail matrix (Allowed / Approval / Never) accepted

### 12.2 MVP functional acceptance

- [ ] Given a configured site and scan profile, ORCA crawls within limits
- [ ] Browser agent loads pages, captures screenshots, collects console logs
- [ ] All eight HLD analysis agents produce typed evidence-backed results or explicit limitations
- [ ] Deterministic prioritization and optional assistive narrative produce required report sections
- [ ] Tenant-authorized preview and immutable HTML/Markdown downloads are available
- [ ] Operational limits enforced (page cap, timeout, budget, retries)
- [ ] Disallowed actions cannot be invoked by agents
- [ ] Structured logs exist for the scan run end-to-end
- [ ] Failures are surfaced; partial results still yield a usable report when possible

### 12.3 Quality acceptance (MVP)

- [ ] On at least one reference site, top findings reviewed by humans meet actionable-rate target
- [ ] Seeded critical broken-link / console / obvious a11y issues are detected in eval harness
- [ ] Cost for reference scan profile is within agreed budget

### 12.4 Non-functional acceptance

- [ ] AI access only through provider abstraction
- [ ] No secrets in code or logs
- [ ] Configuration externalized
- [ ] Unit tests for domain/prioritization/guardrails; coverage policy defined and measured

---

## 13. MVP Scope

**Phase 1 — MVP: “Observe, analyze, report”**

**In scope**

1. Site configuration + bounded crawl
2. Browser agent execution (Playwright-class)
3. Screenshots + console log capture
4. Lighthouse performance audit
5. Accessibility scan (axe-core)
6. SEO/DOM metadata analysis
7. Broken link detection within crawl scope
8. Latency analysis
9. HTML document and security hygiene analysis
10. Assistive LLM explanation/dedup/narrative with deterministic fallback
11. Prioritized in-app report preview
12. Immutable HTML and Markdown downloads
13. Guardrails, budgets, timeouts, retries, structured logging, and tenant isolation
14. Provider-independent `LlmAssistPort`

**Explicitly out of MVP**

- Root-cause deep graphs / historical trend warehouse
- First-class Vision Agent or visual/branding-model checks
- Automatic code patch application
- Pull request generation (design OK; ship Phase 2)
- Test generation + deploy pipelines
- Full auth-matrix coverage for all IdPs
- Multi-tenant SaaS billing
- Autonomous operations of any kind

**MVP exit definition:** A tenant-isolated, read-only analysis run that safely scans a public site and provides evidence-backed preview plus HTML/Markdown reports under approved limits.

---

## 14. Future Scope

### Phase 2 — AI Maintenance Engineer

- Root-cause analysis
- Regression detection vs baselines
- Historical trend analysis + embeddings similarity
- Suggested code patches
- Pull request generation (no auto-merge)
- Weekly maintenance reports
- Stronger handling of auth, cookie banners, lazy load, feature flags
- Improved false-positive controls (thresholds, ignore rules, baselines)

### Phase 3 — Autonomous Operations (approval-gated)

- Generate fixes
- Run tests
- Validate changes
- Create pull requests
- **Deploy only after explicit user approval**
- Broader multi-agent distribution / multi-site scale
- Optional local model routing for eligible tasks
- Deeper integrations (CI, issue trackers, chatops) under the same guardrail model

### Later considerations (backlog, not committed)

- Multi-brand visual design systems validation packs
- Synthetic user-journey reliability scoring
- Policy-as-code packs per industry (e.g., stricter a11y gates)
- Federated/on-prem deployment modes for regulated customers

---

## 15. Assumptions and Dependencies

| Assumption / Dependency | Notes |
|---|---|
| Target sites are HTTP(S) web apps reachable from the runner network | Private sites need network/VPN access |
| Playwright-compatible browsers available in runtime | Container/CI image dependency |
| Lighthouse / axe-core / SEO parsers available as integrations | Prefer documented SDKs/CLIs only |
| Model APIs (or local runtimes) provisioned with keys in env | No hardcoded credentials |
| Humans available to review reports and approve later-phase actions | Product trust model |
| “GPT-5.5 / Vision / mini / embeddings” in research are **capability targets**, not hard vendor SKUs | Final model matrix chosen in Architecture/AI Design docs |

---

## 16. Open Questions

1. Primary delivery form for MVP: CLI job, API service, dashboard, or CI plugin?
2. Single-tenant internal tool first, or multi-site from day one?
3. Hard cost budget per scan/site for MVP?
4. Which environments are first-class: production only, or staging+prod?
5. Is PR creation allowed in Phase 2 against customer repos by default, or opt-in only?
6. Data retention period for screenshots and page HTML snapshots?

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product | | Approved | 2026-07-24 |
| Engineering | | Approved | 2026-07-24 |
| AI / ML | | Approved | 2026-07-24 |
| DevOps / Security | | Approved | 2026-07-24 |
| QA | | Approved | 2026-07-24 |
