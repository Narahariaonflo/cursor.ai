# Cost Optimization
## AI Website Health Orchestrator Agent

| Field | Value |
|---|---|
| Document ID | ORCA-COST-015 |
| Version | 0.1 |
| Status | Approved |
| Scope | Read-only Website Analysis MVP |
| Upstream | `04_High_Level_Design.md`–`14_Deployment.md` (Approved) |
| Downstream | `16_Engineering_Backlog.md`, production capacity/release evidence |
| Last updated | 2026-08-06 |

---

## 1. Purpose and authority

This document defines how the MVP minimizes and attributes cost without reducing HLD scope, evidence integrity, security, tenant isolation, or report availability.

Authority boundaries:

| Concern | Authority |
|---|---|
| Per-run hard resource limits and degradation | `11_Guardrails.md` |
| Global capacity and runtime sizing | `14_Deployment.md` |
| Retention and data handling | `10_Security.md` |
| AI routing, caching, and fallback | `09_AI_Architecture.md` |
| Optimization tactics, measurement, forecasting | This document |

This document never raises an approved ceiling. More restrictive deployment/tenant policies may lower cost.

---

## 2. Principles

1. Validate target and reserve a cost envelope before crawl.
2. Deterministic local analysis precedes paid external assistance.
3. Reuse safe immutable evidence; never duplicate expensive acquisition.
4. Prefer approved local AI when it passes quality/security gates.
5. Cloud AI is used only when it adds clear configured value.
6. Optional enrichment degrades before required HLD analysis.
7. Cost optimizations cannot remove required agents or fabricate coverage.
8. Completed evidence is retained when a budget stops new work.
9. Every billable/resource unit is attributable to tenant and run.
10. Concurrency controls spend rate and latency; it is not assumed to reduce total work.

---

## 3. Cost units

| Resource | Accounting unit | HLD owner/use |
|---|---|---|
| Pages | eligible page dispatched | S3/S16 |
| Browser | active context milliseconds | S5–S12 evidence/S16 |
| Lighthouse | completed attempt | S6 |
| PSI | API request | S6 optional |
| HTTP probes | request attempt | S7/S8/S11 |
| Screenshots | stored count and bytes | Browser evidence |
| LLM | input/output tokens and calls | S15 assistive |
| Artifacts | stored byte-days | S14 |
| Reports | stored byte-days and transfer bytes | S13/S14 |
| Compute | worker CPU/memory seconds | Deployment |

Retries consume the same units as initial attempts. Reservations and actual usage are persisted in `budget_usage`.

---

## 4. Standard scan profile

The standard benchmark uses Guardrails defaults: 10 pages, depth 2, desktop, all eight HLD agents, external probes enabled, Lighthouse within limit, PSI off, evidence-driven screenshots, approved AI only, and deterministic fallback.

Cost comparisons must state target fixture version, tool/browser/model versions, environment, cache state, and whether AI/PSI ran.

---

## 5. Cost envelope and admission

Before crawl planning, the Cost Governor reserves worst-case units for the accepted standard/request profile.

```text
estimated_variable_cost =
  provider_call_cost
  + token_cost
  + object_storage_cost
  + report_transfer_cost
  + attributable_worker_cost
```

1. Price inputs come from versioned environment configuration, never domain constants.
2. `MAX_VARIABLE_COST_MICRO_USD_PER_RUN` is required when paid providers are enabled.
3. Unknown provider prices make that paid capability unavailable.
4. Admission denies work when worst-case resource or monetary reservation exceeds policy.
5. Each task reserves incremental units atomically before scheduling.
6. Actual usage reconciles by idempotent task ID and releases surplus.
7. Estimates round conservatively; reconciliation stores original currency and normalized micro-USD.
8. Tenant/month financial quotas may be added as policy without changing domain findings.

No API response promises a price quote; metrics are operational showback unless a billing product is separately approved.

---

## 6. Crawl optimization

1. Breadth-first discovery and canonical URL dedup prevent repeated pages.
2. Fragment/tracking normalization occurs before queue/budget reservation.
3. Same-origin crawl avoids uncontrolled domain expansion.
4. Sitemap candidates remain subject to page/depth/policy caps.
5. Denied, excluded, duplicate, and already-terminal pages consume no page-dispatch unit.
6. Discovery stops at approved caps; remaining candidates become coverage limitations.
7. Requests may reduce page/depth limits but cannot raise ceilings.

The system does not use AI to select crawl URLs in MVP.

---

## 7. Browser and shared-evidence optimization

1. Navigate once per page/device profile when immutable evidence can be shared.
2. Attach console/network listeners before navigation to avoid repeat loads.
3. Agents consume `PageEvidenceRef`; they do not independently reopen pages.
4. Lighthouse may use separate execution when shared-page state would invalidate metrics.
5. Browser contexts are reused only within one run and compatible device profile.
6. Context lease duration is metered from acquisition through release.
7. Contexts/processes close immediately after terminal work or deadline.
8. Browser reuse never crosses tenant/run boundaries.

Resource blocking, script suppression, or cache manipulation is forbidden when it would change the evidence being measured.

---

## 8. Tool-call optimization

### Lighthouse and PSI

- Lighthouse runs at most once per canonical page/profile/tool version.
- Results are shared by Performance and SEO paths where applicable.
- If pages exceed Lighthouse budget, deterministic selection is seed page then breadth-first eligible order; omitted pages are disclosed.
- PSI remains `PSI_ENABLED=false` by default and requires explicit capability, credential, price, and budget configuration.
- PSI never replaces required local Lighthouse evidence.

### Header and link probes

- Deduplicate probe targets by normalized URL and approved method.
- Share safe status/header/timing results across Latency, Broken Link, and Security agents.
- External probes remain Target Policy validated and budgeted.
- Use `HEAD` only when semantically supported; bounded `GET` fallback is allowed when required for reliable status evidence.
- Do not retry deterministic `4xx` responses except approved `408`/`429` handling.

---

## 9. Screenshot and artifact optimization

1. Screenshots are evidence-driven, not captured for every page.
2. One compatible screenshot may support multiple findings.
3. Enforce configured dimensions/encoding/byte bound before storage.
4. Store artifacts by content checksum; deduplicate only within the same tenant and retention boundary.
5. Stream bounded artifacts to storage; do not buffer whole oversized content.
6. Persist normalized findings/summaries rather than duplicate raw provider payloads.
7. Apply Security retention defaults and object lifecycle deletion.
8. HTML reports are self-contained but do not embed large raw tool artifacts.

Cross-tenant deduplication is forbidden even if content hashes match.

---

## 10. AI optimization

Optimization order:

1. deterministic template/fallback when enrichment is not material;
2. approved tenant-isolated validated cache;
3. approved local model meeting evaluation thresholds;
4. lowest-cost approved cloud capability meeting quality/data policy;
5. higher-capability cloud fallback only when configured value justifies it.

Inputs contain normalized findings and bounded sanitized summaries, not raw DOM/assets. Calls may batch compatible findings within schema/context limits. Cache keys include tenant, capability, prompt version, model alias, and sanitized-input hash.

Model prices, context limits, aliases, and provider order are versioned configuration. Budget exhaustion skips new AI calls and uses deterministic narrative without blocking report publication.

---

## 11. Storage and retention optimization

1. Evidence objects follow the 7-day default; reports 30 days; metadata 90 days per Security.
2. Compression is allowed only when media type/checksum behavior remains deterministic.
3. Object lifecycle rules mirror application retention and clean incomplete uploads.
4. Metadata stores opaque refs/checksums, not duplicate object content.
5. Cleanup batches bounded records and is idempotent/restartable.
6. Tenant retention may shorten but not silently extend policy.
7. Legal holds require explicit authorization and cost ownership.

Storage-tier changes must preserve authorized report availability and restore objectives.

---

## 12. Database and worker efficiency

1. Batch atomic result writes by task while preserving evidence constraints.
2. Use approved indexes and bounded connection pools.
3. Avoid N+1 reads during aggregation/report composition.
4. Stream report/artifact transfer.
5. Scale scan Jobs from durable queue age/depth within global ceilings.
6. Do not keep idle browser Jobs warm by default.
7. Dispatcher leases prevent duplicate active work; idempotency prevents duplicate charges.
8. Retention/vacuum/maintenance runs outside peak scan capacity where possible.

Optimization cannot weaken transactions, RLS, checksums, or durable state.

---

## 13. Degradation order

When projected usage exceeds remaining policy:

1. reject work that cannot fit its initial hard envelope;
2. disable/skip optional PSI;
3. stop additional assistive AI and use deterministic fallback;
4. skip optional new screenshots/artifacts;
5. stop new page/tool work at the exhausted resource;
6. aggregate completed safe evidence;
7. publish `PARTIAL` with explicit coverage/tool limitations, or `FAILED` if no usable evidence.

Required security validation, masking, tenant checks, evidence invariants, HTML/Markdown report pair, and HLD agent truthfulness are never degraded for cost.

---

## 14. Measurement and showback

Required dimensions: environment, tenant, run, agent/tool, page, provider/model alias, prompt version, cache status, retry, and outcome.

Required metrics:

- estimated/reserved/consumed/released units by resource;
- variable micro-USD by run/tenant/provider capability;
- browser minutes and worker CPU/memory seconds;
- Lighthouse/PSI/probe/screenshot/LLM counts;
- input/output tokens, AI cache hit, local/cloud/fallback rates;
- artifact/report byte-days and transfer;
- budget denial/exhaustion and partial-run rate;
- cost per completed/partial standard scan.

`BUDGET_WARNING_RATIO=0.80` emits an operational warning. The hard ceiling remains `1.00`; warnings never authorize overspend.

---

## 15. Forecasting and capacity review

Monthly forecast:

```text
forecast_cost =
  expected_runs
  × measured_standard_scan_cost_by_profile
  + fixed_platform_cost
  + storage_retention_cost
```

Use p50/p95 consumption and separate local, cloud-AI, PSI, and high-page profiles. Review provider price changes, cache effectiveness, partial rates, retries, queue age, browser utilization, and storage growth.

Any limit/capacity increase requires staging load evidence, forecast, budget owner, Security/Architecture review, and configuration change record.

---

## 16. Optimization release gates

A production release requires:

1. standard-profile benchmark within configured monetary/resource envelopes;
2. no limit overspend under concurrent reservation tests;
3. deterministic report publication with AI/PSI unavailable;
4. all eight HLD agents run or disclose genuine tool/coverage limitations;
5. no cross-tenant cache/artifact reuse;
6. storage lifecycle and retention verified;
7. measured p95 fits Deployment capacity and Guardrails deadlines;
8. cost telemetry reconciles with provider/runtime samples within configured tolerance.

No universal dollar target is invented here; Product/Finance supplies environment budgets through approved configuration.

---

## 17. Required tests

Required suites: price/config validation; envelope admit/deny; atomic concurrent reservations; retry charging; reconciliation/idempotency; page/canonical/probe dedup; shared-browser evidence; screenshot-on-demand; Lighthouse selection; PSI default-off; AI local/cloud/cache/fallback order; token accounting; cross-tenant cache denial; artifact lifecycle; streaming memory bounds; degradation outcome; standard-profile benchmark; and forecast calculation.

Cost/governor modules retain Guardrails’ 95% branch-coverage requirement.

---

## 18. Decision and implementation gate

Approval accepts: Guardrails own hard units; paid providers require an environment monetary cap; PSI and idle warm workers default off; cache/dedup is tenant-scoped; Product/Finance owns monetary targets.

After approval, implement typed prices, unit/cost persistence, envelope admission, safe reuse, telemetry, benchmarks, forecasts, and M24 evidence. No optimization code precedes approval.
## Document approval
| Role | Name | Decision | Date |
|---|---|---|---|
| Product / Finance / Architecture | | Approved | 2026-08-06 |
| Engineering / AI / SRE / Security / QA | | Approved | 2026-08-06 |
