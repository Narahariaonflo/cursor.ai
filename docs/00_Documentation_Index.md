# ORCA Documentation Index

**Product:** AI Website Reliability Engineer (ORCA)  
**Rule:** Create documents **one by one** in the order below. Wait for approval before starting the next document.  
**Code:** Do not generate implementation code until relevant documentation is approved.

---

## Document order

| # | File | Title | Status |
|---|---|---|---|
| 00 | [00_Documentation_Index.md](00_Documentation_Index.md) | Documentation Index | Active |
| 01 | [01_Product_Requirements.md](01_Product_Requirements.md) | Product Requirements (PRD) | Approved v0.2 — HLD-aligned |
| 02 | [02_User_Stories.md](02_User_Stories.md) | User Stories | Approved |
| 03 | [03_System_Architecture.md](03_System_Architecture.md) | System Architecture | Approved principles; MVP topology superseded by 04 |
| 04 | [04_High_Level_Design.md](04_High_Level_Design.md) | High Level Design (Web Agent MVP v2) | Approved |
| 05 | [05_Low_Level_Design.md](05_Low_Level_Design.md) | Low Level Design | Approved |
| 06 | [06_API_Specification.md](06_API_Specification.md) | API Specification | Approved |
| 07 | [07_Agent_Architecture.md](07_Agent_Architecture.md) | Agent Architecture | Approved |
| 08 | [08_Database_Design.md](08_Database_Design.md) | Database Design | Approved |
| 09 | [09_AI_Architecture.md](09_AI_Architecture.md) | AI Architecture | Approved |
| 10 | [10_Security.md](10_Security.md) | Security | Approved |
| 11 | [11_Guardrails.md](11_Guardrails.md) | Guardrails | Approved |
| 12 | [12_Implementation_Plan.md](12_Implementation_Plan.md) | Implementation Plan | Approved |
| 13 | [13_Testing_Strategy.md](13_Testing_Strategy.md) | Testing Strategy | Approved |
| 14 | [14_Deployment.md](14_Deployment.md) | Deployment | Approved |
| 15 | [15_Cost_Optimization.md](15_Cost_Optimization.md) | Cost Optimization | Approved |
| 16 | [16_Engineering_Backlog.md](16_Engineering_Backlog.md) | Engineering Backlog | Approved |
| 17 | [17_Implementation_Progress.md](17_Implementation_Progress.md) | Implementation Progress | Active |

---

## Audience map

| Audience | Primary docs |
|---|---|
| Product Managers | 01, 02, 12, 16 |
| Software Engineers | 03–08, 12, 13, 16 |
| AI Engineers | 07, 09, 11, 15 |
| DevOps Engineers | 10, 11, 14, 15 |
| QA Engineers | 02, 13, 16 |

---

## Change control

1. Draft the next numbered document only after the previous is **Approved**.
2. Stakeholder review → Approve / Approve with changes / Revise.
3. Update status in this index and in the document header.
4. Do not skip numbers or invent parallel doc tracks.
5. `04_High_Level_Design.md` is binding for MVP; earlier documents must carry explicit supersession language and cannot widen its scope.

---

## Notes

- `01_Product_Requirements.md` remains product context; **MVP implementation scope is defined by `04_High_Level_Design.md` v2.0** (Website Analysis MVP from `HLD_WEB_Agent_Focused_MVP_v2`).
- MVP is **read-only**: HTML/Markdown report download; **no** GitHub/PR/deploy in MVP.
- System Architecture (`03`) retains Clean Architecture principles; MVP agent catalog and report model follow doc `04` v2.0.
