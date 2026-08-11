# Testing Strategy
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Document ID | ORCA-TST-013 |
| Version | 0.1 |
| Status | Approved |
| Scope | Read-only Website Analysis MVP |
| Upstream | `02_User_Stories.md`, `04_High_Level_Design.md`–`12_Implementation_Plan.md` (Approved) |
| Downstream | `14_Deployment.md`, `16_Engineering_Backlog.md` |
| Last updated | 2026-08-06 |

---

## 1. Objectives

Testing must prove:

1. domain invariants and run transitions are deterministic;
2. unsafe targets never cause network access;
3. tenant data cannot cross boundaries;
4. every finding is evidence-backed and secret-safe;
5. budgets, concurrency, retries, and deadlines remain bounded;
6. independent failures produce explicit partial results where possible;
7. HTML/Markdown reports and API contracts match approved documentation;
8. provider adapters can be replaced without changing application behavior.

No milestone is Done until its acceptance criteria and required tests pass.

---

## 2. Test principles

1. Follow the test pyramid: many unit/property tests, focused contract/integration tests, few end-to-end tests.
2. Test behavior at public boundaries, not private implementation details.
3. Inject clocks, ID generators, policies, ports, and configuration.
4. Prefer small fakes/builders over interaction-heavy mocks.
5. Mandatory CI is deterministic and does not depend on the public internet or paid providers.
6. Every bug fix begins with a failing regression test.
7. Tests run independently, in any order, and in parallel where isolation permits.
8. Randomized tests emit/reuse their seed.
9. Retries never hide flaky tests.
10. Sensitive test values are synthetic and unmistakably non-production.

---

## 3. Test levels

| Level | Scope | Dependencies | Typical cadence |
|---|---|---|---|
| Unit | Domain, services, DTO validation, analyzers | In-process fakes | Every change |
| Property | Invariants, URL forms, budgets, dedup | Generated values | Every change |
| Architecture | Import/dependency and package rules | Source AST | Every change |
| Contract | Every port and API schema | Shared conformance suites | Every change |
| Adapter integration | SQLite/PostgreSQL, filesystem/S3, browser/tools, OIDC | Local containers/processes | Every PR |
| Component | API/worker with real internal adapters and fake externals | Ephemeral stack | Every PR |
| End-to-end | Submit → scan → report → download | Full ephemeral stack + fixture sites | Main/release |
| Security/resilience | SSRF, isolation, injection, failure/timeout | Adversarial fixtures/faults | PR + scheduled |
| Performance | Latency, throughput, memory/capacity | Production-like stack | Release |

---

## 4. Tooling

| Concern | Preferred tool |
|---|---|
| Python tests | `pytest`, `pytest-asyncio` |
| Coverage | `pytest-cov` / Coverage.py |
| Property tests | Hypothesis |
| HTTP/API | HTTPX + FastAPI test transport |
| HTTP provider fakes | RESPX or local fake servers |
| Browser | Playwright against local fixture sites |
| Infrastructure | Testcontainers for PostgreSQL, object storage, and required services |
| Static quality | Ruff, mypy strict project profile |
| Security | pip-audit, secret scanner, Semgrep/Bandit profile, container scanner |

Tools are development dependencies with versions fixed by the project lock artifact. A tool may be replaced only if equivalent gates remain.

---

## 5. Test layout and markers

```text
tests/
  unit/domain/
  unit/application/
  property/
  architecture/
  contract/
  integration/adapters/
  integration/api/
  component/
  e2e/
  security/
  resilience/
  performance/
  fixtures/sites/
  builders/
```

Markers: `unit`, `property`, `contract`, `integration`, `browser`, `e2e`, `security`, `resilience`, `performance`, `slow`.

Unregistered markers fail collection. Test modules mirror production module responsibility.

---

## 6. Unit and property strategy

### 6.1 Domain

Exhaustively test:

- every allowed and forbidden `AnalysisRun` transition;
- entity/value-object invariants and serialization round trips;
- evidence-required finding creation;
- deterministic fingerprint, deduplication, ranking, scoring, and report ordering;
- UTC timestamps and immutable artifact/finding semantics.

### 6.2 Application

Use port fakes to cover success, terminal failure, retryable failure, timeout, cancellation, exhausted budget, partial evidence, and persistence failure for every use case/coordinator.

### 6.3 Properties

Generated inputs must prove:

- URL normalization is idempotent and equivalent encodings cannot bypass policy;
- crawl output never exceeds page/depth/scope limits;
- reserves/consumption never make remaining budget negative;
- deduplication is deterministic, idempotent, and order-independent;
- score remains `0`–`100`;
- masking never emits a seeded synthetic secret.

---

## 7. Contract testing

Each outbound port has one reusable conformance suite executed against every fake and real adapter.

| Port | Required contract assertions |
|---|---|
| Repository | Tenant scope, transactions, optimistic version, round trip, not-found |
| Artifact store | Tenant key, checksum, immutability, atomic publish, idempotent delete |
| Target policy | Same decision taxonomy; no fetch on denial |
| Cost governor | Atomic reservation, idempotent reconcile, no overspend |
| Browser | Typed bounded evidence, timeout, cleanup, read-only permissions |
| Lighthouse/PSI/axe | Typed normalization, bounded artifact, failure classification |
| Header/link probes | Timing/headers/status/redirect contracts, timeout taxonomy, external-link preference/budget |
| LLM assist | Strict schema, grounded IDs, token accounting, deterministic fallback |
| Report renderer | Escaping, determinism, checksum stability, both formats |

Inbound API contract tests validate routes, DTOs, status/error codes, headers, media types, ETag behavior, unknown-field rejection, and OpenAPI compatibility with `06_API_Specification.md`.

---

## 8. Adapter integration testing

1. Run repository suites against SQLite and PostgreSQL; production release requires PostgreSQL/RLS tests.
2. Run artifact suites against filesystem and the selected S3-compatible service.
3. Use a local OIDC/JWKS issuer to test valid, expired, premature, wrong issuer/audience, disallowed algorithm, rotated key, absent tenant, and role claims.
4. Run Playwright in the same browser/runtime family as production.
5. Run Lighthouse and axe against fixed local pages with tool versions recorded.
6. Simulate provider timeout, throttle, malformed output, oversized output, and connection loss.
7. Prove cleanup after exceptions and no persistent browser/session state between runs.

Tests use isolated database schemas/buckets/directories and unique tenant/run IDs.

---

## 9. Deterministic fixture websites

The repository owns versioned local fixture sites:

| Fixture | Required signals |
|---|---|
| `healthy` | Valid baseline with no intentional high findings |
| `seo_html` | Missing/duplicate metadata, heading/semantic defects |
| `performance` | Fixed slow/large resources and metric thresholds |
| `latency` | Deterministic DNS/TLS/TTFB/document and slow-resource thresholds |
| `links` | Broken, malformed, redirect-chain, excluded links |
| `console` | JS error, rejection, failed resource, warning |
| `accessibility` | Known axe rule violations |
| `security` | Mixed content/form/header issues and synthetic masked tokens |
| `crawl` | Depth, duplicates, query variants, robots, sitemap, denied paths |
| `slow_failure` | Timeout, reset, oversized response, partial availability |
| `adversarial` | XSS, prompt injection, malicious filenames/content |

Fixtures contain no real credentials. Intentional issues are documented in a machine-readable manifest used by acceptance assertions.

---

## 10. Security test strategy

Release-blocking security suites cover:

1. SSRF corpus: private/reserved/metadata ranges, IPv6, mapped addresses, numeric encodings, DNS aliases/rebinding, redirects, and blocked ports.
2. A network spy assertion proving denied inputs make zero DNS/HTTP/browser/provider calls.
3. JWT and role/tenant authorization, ID enumeration, PostgreSQL RLS, and object-store isolation.
4. Browser permissions, sandbox, egress, download/upload, context destruction, and no cross-run storage.
5. XSS/active HTML/Markdown, prompt injection, path traversal, header injection, and oversized payloads.
6. Secret masking before every persistence/log/provider/report boundary.
7. Static dependency, image, SBOM, source-secret, and IaC scans.

High/critical exploitable findings block release; exceptions require time-bounded Security approval.

---

## 11. Resilience and concurrency testing

Fault injection covers browser crash, tool/provider outage, DNS failure, database conflict, object-store interruption, worker termination, queue saturation, malformed artifacts, and retention cleanup races.

Use fake clocks for deadline/retry tests. Concurrency tests force interleavings around budget reservations, state versions, report publication, lease release, and tenant-fair queues.

Assertions:

- no duplicate charge or report publication;
- no leaked semaphore/browser/database resource;
- no transition after terminal state;
- completed evidence survives independent failures;
- HLD §8.4 agent failure and §8.5 budget exhaustion stop scheduling and publish authorized `PARTIAL` downloads when evidence is usable;
- restart recovery resumes or safely finalizes durable work.

---

## 12. Report and UI testing

1. Structural tests require HLD §15.3 summary/score, top critical/high, grouped findings, affected URLs/evidence, impact/remediation, and coverage/limitations/timestamp sections.
2. Variable IDs/timestamps are injected or normalized—not broadly ignored.
3. Parse rendered HTML and Markdown structurally; avoid fragile whole-file snapshots.
4. Verify escaping, CSP, no scripts/external resources, secret absence, filenames, checksum/ETag, immutability, and terminal-state authorization.
5. UI smoke tests cover submit, progress, partial limitations, preview, format download, validation, and inaccessible-run behavior.
6. Automated UI accessibility checks run on primary states; critical violations block release.

---

## 13. Performance and resource tests

Release baseline uses production-like PostgreSQL, object storage, browser workers, and local deterministic providers.

| Scenario | Acceptance threshold |
|---|---|
| Submit/status API excluding scan work | p95 ≤ 300 ms, error rate < 1% |
| Report metadata/preview API excluding artifact transfer | p95 ≤ 500 ms |
| Capacity | 10 simultaneous runs across 5 tenants without limit breach |
| Fairness | No tenant starvation while runnable capacity exists |
| Bounds | No budget/concurrency/payload ceiling exceeded |
| Memory | No sustained growth across repeated bounded/oversized inputs |

Thresholds are measured after warm-up and stored with environment/tool versions. Scan duration is fixture-dependent and must stay inside the approved run deadline. Performance regressions above 10% require investigation or approved baseline change.

---

## 14. Coverage and quality gates

| Scope | Required gate |
|---|---:|
| Overall changed production code | ≥ 90% line and branch coverage |
| Domain state/invariants and security policy | 100% decision coverage |
| Guardrail/governor modules | ≥ 95% branch coverage |
| New/changed public behavior | Acceptance + negative-path test |

Coverage exclusions require documented justification and cannot exclude business/security logic.

PR gate: formatting, lint, type check, unit, property, architecture, contract, API, adapter integration, security-static, and coverage.

Main/release gate adds browser, component, end-to-end, dynamic security, resilience, migration, performance, dependency/image, and artifact reproducibility tests.

---

## 15. Acceptance traceability

Primary proof: US-001–002 API/identity/policy; US-003–005 crawl/concurrency/browser; US-006–009 fixture-based agents; US-010–012 aggregation/AI fallback; US-013–014 report/UI/download; US-015–016 budget/resilience/logging/masking.

Every acceptance test records story ID, requirement, fixture, and evidence. Must stories block release; US-012’s optional AI enrichment may defer only when its deterministic fallback passes.

---

## 16. Flaky-test policy

1. Automatic test reruns are disabled in required gates.
2. Failure artifacts include seed, logs, traces, screenshots, tool versions, and safe correlation IDs.
3. A confirmed flaky test is quarantined only with owner, issue, rationale, and expiry no longer than seven days.
4. Quarantine cannot bypass security, tenant isolation, migration, or core acceptance tests.
5. Repeated flakiness blocks release and is treated as a product reliability defect.

---

## 17. Test evidence and implementation

Builders use minimal isolated records; clocks, UUIDs, DNS, and providers are controlled. Test logs/artifacts use production masking and contain no environment credentials. CI publishes access-controlled JUnit, coverage, security, performance, and traceability evidence under `10_Security.md` retention.
After approval, add locked tools/markers, reorganize existing tests without weakening assertions, add conformance suites/fixtures/builders, enforce CI gates, and map each backlog milestone to evidence.
## Document approval
| Role | Name | Decision | Date |
|---|---|---|---|
| Architecture / Security | | Approved | 2026-08-06 |
| Engineering / Platform | | Approved | 2026-08-06 |
| QA / Product | | Approved | 2026-08-06 |
