# User Stories
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Product name | AI Website Health Orchestrator Agent |
| Alternate / portfolio name | AI Website Reliability Engineer (ORCA) |
| Document type | User Stories |
| Version | 0.2 |
| Status | Approved |
| Upstream | `01_Product_Requirements.md` v0.2 (Approved), `04_High_Level_Design.md` v2.0 (Approved, binding) |
| Downstream | `05_Low_Level_Design.md`, `06_API_Specification.md`, `13_Testing_Strategy.md` |
| Audience | Product, Engineering, AI, DevOps, QA |
| Last updated | 2026-07-30 |
| File | `02_User_Stories.md` |

---

## 1. Purpose

This document translates the focused Website Analysis MVP HLD into backlog-ready user stories.

This revision intentionally narrows MVP scope to:

- Read-only website analysis
- Evidence-backed findings only
- HTML and Markdown report preview/download
- Explicit deferral of Git, pull request, patch, and deploy capabilities

---

## 2. Story format

Each story includes:

- `ID`
- `As a / I want / So that`
- `Phase` - MVP or Later
- `Priority` - Must or Should
- `HLD trace`
- Testable acceptance criteria

---

## 3. Personas

| Persona ID | Persona |
|---|---|
| P-SRE | Website SRE / Reliability Engineer |
| P-QA | QA Engineer |
| P-FE | Frontend / Web Engineer |
| P-PM | Product Manager / Site Owner |
| P-SEC | Security / Platform Engineer |
| P-A11Y | Accessibility / SEO Specialist |
| P-EM | Engineering Manager |
| P-AI | AI Engineer |

---

## 4. Epic catalog

| Epic ID | Epic | Phase |
|---|---|---|
| E01 | Scan intake and validation | MVP |
| E02 | Crawl planning and bounded execution | MVP |
| E03 | Evidence capture and specialised analysis | MVP |
| E04 | Findings consolidation and prioritisation | MVP |
| E05 | Report preview and download | MVP |
| E06 | Guardrails, cost limits, and observability | MVP |
| E07 | Deferred post-MVP capabilities | Later |

---

## 5. MVP user stories

### Epic E01 - Scan intake and validation

#### US-001 - Submit a website analysis request

**As a** website SRE  
**I want** to submit a public website URL with scan preferences  
**So that** the system analyses only the target and scope I requested

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 8, 10, 15 |

**Acceptance criteria**

1. Given a valid public URL, when I submit the scan request, then a new analysis run is created with a unique run identifier.
2. Given scan preferences such as `max_pages`, `max_depth`, and device profile, when the run is accepted, then those preferences are stored with the run.
3. Given an invalid or unsupported target URL, when I submit the request, then the system rejects it with a clear validation error.
4. Given two tenants, when either requests a run/status/report owned by the other, then no metadata or artifact is disclosed.

#### US-002 - Reject unsafe targets before scanning

**As a** security/platform engineer  
**I want** SSRF and allow/deny policies enforced before any crawl begins  
**So that** the system does not scan forbidden or unsafe destinations

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 5, 8, 11, 14 |

**Acceptance criteria**

1. Given a target that matches a deny rule or SSRF restriction, when validation runs, then the analysis run is failed before any browser or HTTP fetch occurs.
2. Given a rejected target, when the result is shown, then the user sees a policy-safe failure reason.
3. Given a rejected target, when logs are inspected, then the denial is recorded with correlation metadata and without secrets.

### Epic E02 - Crawl planning and bounded execution

#### US-003 - Build a bounded scan queue

**As a** DevOps-oriented operator  
**I want** crawl discovery to respect depth and page limits  
**So that** scan cost and runtime stay predictable

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 5, 6, 8, 11, 15 |

**Acceptance criteria**

1. Given configured `max_pages` and `max_depth`, when crawl planning completes, then the queue contains no more than the allowed pages and depth.
2. Given the crawl limit is reached, when eligible pages remain, then the run continues with partial coverage rather than silently expanding scope.
3. Given a completed or partial run, when the report is generated, then scan coverage limitations are shown explicitly.

#### US-004 - Run specialised agents in parallel where safe

**As an** engineering manager  
**I want** independent scanners to run concurrently  
**So that** the overall analysis completes faster without breaking isolation or limits

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 6, 8, 12, 16 |

**Acceptance criteria**

1. Given a planned queue with multiple eligible pages, when agent execution starts, then independent agent tasks may run in parallel subject to browser-pool and budget limits.
2. Given shared runtime pressure or limit exhaustion, when concurrency must be reduced, then work degrades to queued execution without losing completed findings.
3. Given parallel execution, when the run is observed, then agent durations and failures remain traceable by run correlation ID.

### Epic E03 - Evidence capture and specialised analysis

#### US-005 - Capture browser evidence

**As a** frontend engineer  
**I want** screenshots, console output, and DOM/network evidence captured for scanned pages  
**So that** findings are reproducible and explainable

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 4, 6, 9, 14 |

**Acceptance criteria**

1. Given a successfully rendered page, when browser evidence capture runs, then the system records URL plus at least one artifact such as screenshot, console message, DOM snippet, or timing detail.
2. Given screenshot budget is exhausted, when additional pages are scanned, then the run continues and records the missing screenshot as a known limitation.
3. Given a page navigation fails after retries, when the run completes, then the failure is reported as a gap rather than hidden.

#### US-006 - Detect SEO issues

**As an** SEO specialist  
**I want** metadata and structure problems identified from rendered pages  
**So that** discoverability issues appear in the health report

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 4, 6, 15 |

**Acceptance criteria**

1. Given a page missing a required SEO element such as a title or canonical tag, when the SEO agent runs, then an SEO finding is created with page URL and evidence.
2. Given structured data or social metadata issues, when detected, then the finding includes the affected page and the missing or invalid signal.

#### US-007 - Detect performance and latency issues

**As a** website SRE  
**I want** performance and latency findings backed by tool output  
**So that** slow or unstable user experience can be prioritised

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 4, 7, 14, 15 |

**Acceptance criteria**

1. Given Lighthouse or latency probes breach configured thresholds, when analysis completes, then findings are created with metric evidence.
2. Given raw tool artifacts exist, when the final report is viewed, then findings can reference the underlying artifact.
3. Given a tool execution fails, when the run finishes, then the report records the gap instead of implying success.

#### US-008 - Detect broken links and resource failures

**As a** QA engineer  
**I want** broken links, redirect problems, and missing resources reported  
**So that** users do not hit dead paths or failed assets

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 4, 6, 15 |

**Acceptance criteria**

1. Given an internal broken link in scope, when link analysis runs, then a broken-link finding is created with source page, target URL, and status evidence.
2. Given redirect chains or malformed URLs are found, when analysis completes, then they are surfaced as findings with the relevant evidence.
3. Given an external link and remaining probe budget, when link analysis runs by default, then its status/redirect evidence is validated under Target Policy.

#### US-009 - Detect HTML, accessibility, and security hygiene issues

**As a** quality and platform team member  
**I want** HTML structure, accessibility, and basic client-side security problems reported  
**So that** I can address correctness, usability, and exposure risks from one scan

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 4, 7, 11, 15 |

**Acceptance criteria**

1. Given invalid or incomplete HTML document structure, when the HTML analyzer runs, then findings include the affected page and the rule or structural issue.
2. Given axe-core detects an accessibility violation, when the accessibility agent runs, then the finding includes rule id, impact, and target evidence.
3. Given mixed content, insecure forms, missing security headers, or exposed client-side secret patterns are detected, when the security agent runs, then findings are created with masked evidence only.

### Epic E04 - Findings consolidation and prioritisation

#### US-010 - Deduplicate related findings

**As a** website SRE  
**I want** duplicate findings merged into a single normalized record  
**So that** the report is concise and repeated issues are easier to triage

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 6, 9, 10, 16 |

**Acceptance criteria**

1. Given multiple equivalent findings for the same issue pattern, when aggregation runs, then the system stores one merged finding with occurrence metadata.
2. Given a merged finding, when viewed in the report, then the user can still see all affected URLs or references.

#### US-011 - Rank findings by severity and confidence

**As an** engineering manager  
**I want** findings ordered by priority rather than discovery order  
**So that** teams work the most important issues first

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 6, 9, 10, 15, 16 |

**Acceptance criteria**

1. Given findings of mixed importance, when prioritisation completes, then critical and high-severity items appear ahead of lower-impact issues.
2. Given confidence or evidence strength varies, when ranking occurs, then the score incorporates confidence without allowing evidence-free items.
3. Given an LLM is used to help explain or cluster issues, when final priorities are assigned, then deterministic domain rules remain authoritative.

#### US-012 - Generate an executive summary with assistive AI

**As a** product manager  
**I want** a business-readable summary of the scan outcome  
**So that** I can understand the main risks without reading raw tool output

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Should |
| HLD trace | Sections 7, 11, 12, 16 |

**Acceptance criteria**

1. Given a completed or partial run with findings, when the summary is generated, then it reflects the actual findings and coverage limitations.
2. Given LLM assistance is used, when prompts are processed, then the model does not become the primary evidence source for any finding.
3. Given AI budget is exhausted, when the summary cannot be enriched further, then the report still publishes from deterministic findings if available.

### Epic E05 - Report preview and download

#### US-013 - Preview the report in the application

**As a** site owner  
**I want** to review the report before downloading it  
**So that** I can quickly inspect the scan outcome in the product

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 6, 8, 15 |

**Acceptance criteria**

1. Given a completed or partial run, when I open the result, then I can view executive summary, top findings, grouped findings, evidence references, and limitations.
2. Given the run is partial, when the preview is shown, then coverage gaps and agent failures are visible.

#### US-014 - Download HTML and Markdown reports

**As a** website SRE  
**I want** the final report downloadable as HTML and Markdown  
**So that** I can share it with both technical and non-technical stakeholders

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 2, 6, 15 |

**Acceptance criteria**

1. Given a completed or partial run, when I choose a format, then I can download a report file in HTML or Markdown.
2. Given a report artifact is published, when fetched later for the same run, then the content is immutable.
3. Given file naming is generated, when the report is downloaded, then the filename includes target domain and timestamp.

### Epic E06 - Guardrails, cost limits, and observability

#### US-015 - Enforce operational budgets and partial completion

**As a** platform engineer  
**I want** hard limits for pages, browser work, screenshots, PSI calls, and LLM tokens  
**So that** scans stay within a predictable cost envelope

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 8, 11, 12, 16, 17 |

**Acceptance criteria**

1. Given a configured limit is reached, when additional work would exceed budget, then the system stops scheduling new work for that budgeted resource.
2. Given enough findings already exist, when a limit stops the run, then the run can finish as `PARTIAL` with explicit limitations.
3. Given no usable evidence exists after unrecoverable failure, when finalisation occurs, then the run ends as `FAILED`.

#### US-016 - Record structured logs and protect sensitive output

**As a** DevOps or security engineer  
**I want** structured logs and secret-safe reports  
**So that** I can audit runs without leaking credentials or sensitive artifacts

| Field | Value |
|---|---|
| Phase | MVP |
| Priority | Must |
| HLD trace | Sections 11, 13, 16, 17 |

**Acceptance criteria**

1. Given a scan run, when logs are inspected by `scan_run_id`, then lifecycle events, agent timings, failures, and policy decisions are traceable.
2. Given a report or log contains token-like or secret-like values, when content is stored or rendered, then sensitive values are masked.
3. Given model calls are logged, when the logs are reviewed, then they contain provider/model metadata without exposing credentials.

---

## 6. Deferred post-MVP stories

The following themes are explicitly deferred by the current HLD and must not be treated as MVP delivery commitments:

- Repository integration
- Pull request creation
- Automatic code changes or patch generation
- Deployment or approval-gated remediation
- Authenticated scanning beyond explicitly supported patterns
- Legal accessibility or security certification

---

## 7. Recommended MVP backlog order

1. US-001, US-002
2. US-003, US-004
3. US-005
4. US-006, US-007, US-008, US-009
5. US-010, US-011, US-012
6. US-013, US-014
7. US-015, US-016

---

## 8. Open questions

1. Should the MVP user entry point be UI, API, CLI, or a combination?
2. What default thresholds should be used for severity, confidence, and health score calculations?
3. Should external links be checked by default or only when explicitly enabled?

---

## Document approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Product | | Approved | 2026-07-30 |
| Engineering | | Approved | 2026-07-30 |
| AI Engineering | | Approved | 2026-07-30 |
| QA | | Approved | 2026-07-30 |
| DevOps / Security | | Approved | 2026-07-30 |
