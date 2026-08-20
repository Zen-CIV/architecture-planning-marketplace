# Part I — Architecture

## 1. Document control

| Field | Value |
|---|---|
| Document | CiV Dossier Engine — Architecture & Build Plan |
| Version | 1.0 |
| Date | 2026-08-20 |
| Owner | Rad — Technical Operations, Compliance IV |
| Requested by | Stu — Sales Lead, Compliance IV |
| Intended readers | AI build agents executing Appendix A; Rad reviewing gate evidence |
| Companion artifact | `plans/civ-dossier-engine-implementation.md` (embedded as Appendix A) |
| Target database | Supabase project `hoyinfxpotpwkhzsgime` (504 companies loaded) |
| Target orchestrator | n8n, self-hosted on Hostinger (105 workflows present) |
| Runtime models | Kimi K2 and DeepSeek V3 via OpenRouter credential `WkivISO0KPmV0dNq` |
| Catalog | 134 publicly-collectible datapoints across 18 categories |
| Chunk graph | 30 chunks already defined in `civ_chunk_def` |

**How to use this document.** Read Part I once for orientation — it explains why the system is
shaped the way it is and which invariants must not be broken. Then execute strictly from
Appendix A, which carries the complete Data Definition Language (DDL), the workflow node lists,
the code, and the verification query for every task. Where the two disagree, Appendix A is
authoritative for *what to type* and Part I is authoritative for *what must remain true*.

Acronyms are spelled out at first use throughout: TCPA (Telephone Consumer Protection Act), DNC
(Do Not Call), PEWC (Prior Express Written Consent), DDL (Data Definition Language), API
(Application Programming Interface), LLM (Large Language Model), ICP (Ideal Customer Profile),
TTL (Time To Live), DOM (Document Object Model), BPO (Business Process Outsourcing), DID (Direct
Inward Dialing number), NANPA (North American Numbering Plan Administrator), FCC (Federal
Communications Commission), FTC (Federal Trade Commission), BBB (Better Business Bureau).

## 2. Executive summary

The CiV Dossier Engine collects 134 publicly-verifiable datapoints about each of 504 prospect
companies and produces one evidence-cited research dossier per company, unattended. It runs as
five n8n workflows over a Supabase database, dispatching work through a 30-node dependency graph
in which each node — a "chunk" — collects between three and fifteen related datapoints and
nothing else. No agent ever sees the whole company. The correctness guarantee that makes the
output usable is structural rather than procedural: every stored value must reference a stored
artifact and quote a verbatim string from it, enforced by a database CHECK constraint, and a
release gate refuses to render any dossier whose quotes cannot be found in the bytes on file.
A human reads the dossier and decides what to send; the engine writes no outbound message.

The build is segmented into five phases and nineteen work packages. Phase A establishes the
findings table, the claimable run queue and the dependency-resolution view. Phase B loads the
catalog, adds an n8n execution layer to the existing chunk graph, writes the anti-fabrication
prompts and seeds the state-statute overlay. Phase C builds the three orchestration workflows —
budget guard, scheduler and chunk runner. Phase D implements the chunk bodies across five
archetypes, of which eight run as pure SQL with no model in the path. Phase E adds scoring, the
citation gate, dossier composition, the refresh scheduler and a twenty-company pilot. Every work
package carries an acceptance gate stated as a query whose expected output is written down, so a
reviewer can demand literal evidence rather than a status report.

## 3. Architecture principles

**P1 — Chunk by dependency, never by convenience.**
Work is dispatched only from `civ_ready_chunk`, a view that derives runnable work from the
`depends_on` arrays already stored in `civ_chunk_def`. *Rationale:* the chunk order is data, so
regrouping datapoints or inserting a chunk is a SQL `UPDATE`, never a workflow edit. n8n contains
no knowledge of the graph.

**P2 — A value without evidence cannot be stored.**
`civ_finding.citation_gate` is a CHECK constraint requiring `artifact_id`, `source_url` and an
`evidence_quote` of at least twelve characters for every non-null value. *Rationale:* models
asked for an unobtainable fact invent one. Prompt instructions reduce this; a constraint
eliminates it. Verified in WP A1 by an insert that must fail.

**P3 — Quotes are verified against stored bytes, not against the live web.**
`civ_artifact` holds the body every quote came from, so `civ_citation_violation` checks 100% of
findings with a SQL substring test and no HTTP request. *Rationale:* sampling misses systematic
prompt failures, and re-fetching introduces a second source of truth that drifts.

**P4 — Single writer for every rollup.**
`companies.civ` is written only by `civ_project_company()`, called once per company by PC-23.
*Rationale:* twenty-four per-company chunks running concurrently against one JSONB column is a
lost-update race in which the last writer silently discards the rest.

**P5 — No model where a join will do.**
Eight of the thirty chunks are declared `archetype = 'sql'` and carry no model. *Rationale:*
placing an LLM in front of a REST endpoint that returns clean JSON, or in front of a Postgres
join, adds cost, latency and a fabrication surface for no gain. Verified in WP D2 by a query
asserting zero recorded models on those chunks.

**P6 — Unreachable datapoints are declared, not discovered.**
The 25 datapoints marked `Partial` in the catalog carry `method = 'ask'` and are filtered out of
every agent dispatch. *Rationale:* an agent that flails and then concludes unreachability is in
exactly the state where it fabricates instead. Their `discovery_question` renders in the dossier
as a question for the sales call.

**P7 — Cost and concurrency are bounded by the database, not by hope.**
`civ_budget` halts every workflow on a daily cap; `civ_claim_chunks` bounds in-flight work;
`max_tool_calls` bounds each agent. *Rationale:* an unattended loop against paid APIs with no
cap is how a weekend produces a four-figure bill.

**P8 — Allegations are never described as findings.**
PC-22 rejects any composed text that states a legal conclusion. *Rationale:* CiV's positioning is
compliance risk management, never legal advice, and a dossier that reads as an accusation is
unusable in the sales conversation it exists to support.

## 4. System context

@@DIAGRAM:context@@

| External source | Entry point | Identity key | Returns into |
|---|---|---|---|
| Company brand websites | Apify actor (real Chrome) | brand domain | `civ_artifact` (kind `form_probe`, `policy`, `page`) |
| Open web / directories | Tavily search API | query string | `civ_artifact` (kind `page`) |
| CourtListener | REST `/api/rest/v4/search/?type=r&suitNature=485` | docket id | `court_cases`, `civ_artifact` |
| FCC complaint corpus | already loaded — `fcc_violations` (80,536 rows) | telephone number | `civ_finding` M01–M05 |
| FTC DNC corpus | already loaded — `ftc_dnc` (466,196 rows) | telephone number | `civ_finding` M01–M05 |
| NANPA block assignments | already loaded — `npanxx_blocks` (204,462 rows) | NPA-NXX | `civ_finding` G05–G09 |
| State statutes | REF-02, primary-source text only | state code | `civ_state_overlay` |
| LinkedIn | Airscale credential `vRVJcn1nRmJtDkLw` | company URL | `civ_artifact` |
| Slack `#civ-ops`, `#civ-dossiers` | outbound only | — | operator notifications |

The mechanism that unifies these is `civ_artifact`. Every source, whether an agent read it or a
deterministic fetch retrieved it, deposits its bytes there with a SHA-256 hash before any finding
may reference it. That single rule is what lets a quote in a dossier be checked without leaving
the database, and it is why the citation audit costs nothing to run at full coverage.

## 5. Data architecture

@@DIAGRAM:erd@@

| Table | Role | Key columns |
|---|---|---|
| `companies` | 504 prospects; pipeline state | `id`, `civ_status`, `civ` (projection), `website` |
| `civ_chunk_def` | The 30-chunk graph + execution config | `chunk_id`, `depends_on`, `produces`, `archetype`, `model` |
| `civ_datapoint` | The 134-datapoint catalog | `datapoint_id`, `chunk_id`, `method`, `ttl_days`, `discovery_question` |
| `civ_chunk_run` | Claimable work queue and run log | `run_id`, `company_id`, `chunk_id`, `status`, `cost_usd` |
| `civ_artifact` | Stored bytes behind every quote | `artifact_id`, `company_id`, `url`, `body`, `sha256` |
| `civ_finding` | One row per company × datapoint | PK `(company_id, datapoint_id)`, `evidence_quote`, `expires_at` |
| `civ_state_overlay` | Primary-source statutory text | `state`, `citation`, `verification_string`, `verified` |
| `civ_budget` | Daily spend cap and halt flag | `day`, `llm_cost_usd`, `halted` |
| `vendors`, `vendor_sellers` | Vendor litigation graph (14 / 35 rows) | `vendor_name`, `case_count`, `settled_count` |

**Identity strategy.** `companies.id` is the uuid every table hangs from. Datapoint identifiers
are the category letter plus a zero-padded ordinal (`A01`, `D09`, `S01`) and already appear in
`civ_chunk_def.produces`, so WP B1 binds catalog to graph with a single join rather than a manual
mapping. Chunk identifiers are the existing `PC-nn`, `REF-nn`, `SCR-nn` strings.

**Single-writer rule.** `civ_finding` is written by many chunks but each row belongs to exactly
one chunk, because `civ_datapoint.chunk_id` assigns every datapoint to one producer. The primary
key `(company_id, datapoint_id)` therefore cannot be contended by two concurrent chunks.
`companies.civ` has one writer, `civ_project_company()` (P4).

**Interface catalog.**

| Interface | Purpose | Called by |
|---|---|---|
| `civ_ready_chunk` (view) | Which company × chunk pairs are runnable now | WF-CIV-01 scheduler |
| `civ_claim_chunks(worker, limit)` | Atomically claim N pending runs | WF-CIV-10 runner |
| `civ_citation_violation` (view) | Findings whose quote is absent from its artifact | PC-22 gate, WF-CIV-05 audit |
| `civ_project_company(uuid)` | Collapse findings into `companies.civ` | PC-23 only |
| `classify_tns` (existing RPC) | Line type and carrier per number | PC-11 |

Full DDL is in Appendix A Tasks A1–A4; the catalog loader is Task B1.

## 6. Behavior architecture

@@DIAGRAM:routing@@

Seven archetypes, assigned in Task B2, determine how a claimed chunk executes:

| Archetype | Chunks | Model | Tools | What it writes |
|---|---|---|---|---|
| `sql` | 8 | none | none | findings from joins |
| `api` | 2 | DeepSeek V3 | HTTP, Postgres | artifacts + findings |
| `fetch` | 4 | none | Apify render/scrape | artifacts only |
| `extract` | 4 | DeepSeek V3 | none | findings from stored artifacts |
| `research` | 10 | Kimi K2 | Tavily, Apify | artifacts + findings |
| `compute` | 1 | none | none | derived scores |
| `compose` | 1 | DeepSeek V3 | none | dossier file |

**Routing rules.**

1. A company enters at `civ_status = 'new'` and is admitted to `'queued'` by the scheduler, which
   holds the working set at 40 concurrent companies.
2. `civ_ready_chunk` emits a chunk only when every entry in its `depends_on` array has a run with
   status `done` for that company. SCR-01 is the only per-company chunk with no dependencies, so
   it is always first.
3. SCR-01 is the disqualifier gate. A confirmed federal TCPA docket sets
   `civ_status = 'disqualified'` and marks the company's remaining chunks `skipped`. CiV is
   prevention-only; the catalog annotates datapoint N02 as *"ICP disqualifier"*.
4. Rate-limited chunks (`SCR-01`, `REF-05`) receive priority 10 and are claimed ahead of others.
5. A failed run returns to `pending` with `last_error` set; after three attempts the guard marks
   it `dead`, which releases dependent chunks from ever becoming ready — the company ends
   `failed` rather than silently incomplete.
6. PC-22 is the release gate: any row in `civ_citation_violation` for that company blocks PC-23.
7. PC-23 composes, calls `civ_project_company()`, and sets `civ_status = 'complete'`.

**Loop-termination guarantees.** Agent loops terminate on `max_tool_calls` (default 12, per
chunk). Run retries terminate on `max_attempts` (3). Stuck claims are reaped after 30 minutes.
The daily spend cap in `civ_budget` halts all five workflows regardless of queue depth. There is
no unbounded loop anywhere in the design.

**Failure policy.** Failures are recorded, never silently swallowed: `civ_chunk_run.last_error`
holds the message, `#civ-ops` receives the budget halt, and a `dead` chunk leaves the company
diagnosable through `civ_chunks` in the projection.

## 7. Workflow catalog

| ID | Workflow | Trigger | Responsibility | Depends on |
|---|---|---|---|---|
| WF-CIV-00 | Guard and Reaper | `*/5 * * * *` | Roll up spend, set halt flag, reap stuck claims, kill exhausted runs | A2, A4 |
| WF-CIV-01 | Scheduler | `*/15 * * * *` | Admit companies, enqueue ready chunks from the view | A3, C1 |
| WF-CIV-10 | Chunk Runner | `*/5 * * * *` | Claim, dispatch by archetype, validate, write findings | C2, B2, B3 |
| WF-CIV-20 | Refresh Scheduler | `0 3 * * *` | Re-enqueue chunks whose findings passed their TTL | E2 |
| WF-CIV-05 | Citation Audit | `0 2 * * *` | Report `civ_citation_violation` counts per chunk to Slack | A4 |

Build order follows the dependency column: WF-CIV-00 first because every other workflow reads its
halt flag, then the scheduler, then the runner, then the two nightly jobs. The existing *NANPA
Monthly Refresh* workflow (`LX7srZ3KlMeQVmYy`) already implements REF-03 and is called rather
than rebuilt. Per-node specifications are in Appendix A Tasks C1–C3 and E3.

## 8. Work breakdown structure

@@DIAGRAM:wbs@@

### Phase A — Foundation

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| A1 | A1 | `civ_datapoint` + `civ_finding` with `citation_gate` CHECK | — | Insert of an uncited value raises `violates check constraint "citation_gate"` | Sonnet |
| A2 | A2 | `civ_chunk_run` queue + `civ_claim_chunks` with SKIP LOCKED | A1 | 3 rows inserted, `civ_claim_chunks(w,2)` returns exactly 2; statuses read claimed=2 pending=1 | Sonnet |
| A3 | A3 | `civ_ready_chunk` dependency view | A2 | With one company queued, view returns exactly one row and it is `SCR-01` | Opus |
| A4 | A4 | `civ_budget`, `civ_citation_violation`, `civ_project_company()` | A1, A2 | `civ_citation_violation` returns 0; `civ_project_company()` returns `{}`; budget row reads halted=false cap=20.00 | Sonnet |

### Phase B — Definitions (parallel with A after A1)

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| B1 | B1 | Load 134-row catalog, bind to graph, derive discovery questions | A1 | `civ_datapoint` count = 134; null `chunk_id` = 0; `discovery_question` not null = 25; per-category counts match A 12 / D 15 / N 10 | Sonnet |
| B2 | B2 | Archetype, model, tool allowlist columns on `civ_chunk_def` | — | Archetype counts read api 2, compose 1, compute 1, extract 4, fetch 4, research 10, sql 8; null archetype = 0 | Sonnet |
| B3 | B3 | Anti-fabrication preamble + per-chunk task prompts | B2 | Every `extract`/`research`/`api`/`compose` chunk has non-null `system_prompt`; PC-07/08/09 exceed the shared preamble length | Opus |
| B4 | B4 | Seed `civ_state_overlay` for mini-TCPA footprint states | — | ≥12 rows, all with `citation`, `canonical_url`, `verification_string`; ≥12 `verified` after REF-01 | Opus |

### Phase C — Core orchestration

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| C1 | C1 | WF-CIV-00 guard and reaper | A2, A4 | Cap set to 0 → `halted` reads true and one Slack message lands in `#civ-ops`; cap restored | Sonnet |
| C2 | C2 | WF-CIV-01 scheduler | A3, C1 | After one manual execution: `civ_chunk_run` = 40 rows, `select distinct chunk_id` returns only `SCR-01` | Opus |
| C3 | C3 | WF-CIV-10 runner, seven-archetype dispatch | C2, B2, B3 | One company through SCR-01: run status `done`, N01–N10 findings present, `civ_citation_violation` = 0 | Opus |

### Phase D — Chunk implementations (parallel after C3)

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| D1 | D1 | SCR-01 litigation disqualifier with name adjudication | C3 | Disqualified share falls between 20% and 40%; three matched dockets manually confirmed as the same company | Opus |
| D2 | D2 | Eight SQL chunk bodies | C3, B4 | Each chunk has `done` runs; `select model from civ_chunk_run where chunk_id in (...) and model is not null` returns 0 rows | Sonnet |
| D3 | D3 | PC-05/PC-06/PC-10 acquisition, real Chrome for the form probe | C3 | `civ_artifact` null `sha256` = 0; a `form_probe` artifact contains a non-empty `checkboxes` array with `defaultChecked` | Opus |
| D4 | D4 | PC-07/PC-08/PC-09/PC-14 extraction | D3 | `civ_citation_violation` = 0; 9 of 10 hand-checked quotes located at their `source_url` | Opus |
| D5 | D5 | Eight agentic research chunks on Kimi K2 | C3 | `civ_citation_violation` = 0; no chunk averaging its `max_tool_calls` ceiling | Opus |

### Phase E — Scoring, gate, dossier, pilot

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| E1 | E1 | PC-21 exposure scoring from `scoring_weights` | D2, D4, D5 | Every `S%` finding carries a non-empty `derived_from` array; count of null `derived_from` = 0 | Sonnet |
| E2 | E2 | PC-22 citation gate and PC-23 dossier composition | E1 | `civ_citation_violation` = 0; three dossiers read cold and Stu confirms he can write an opener from each | Opus |
| E3 | E3 | WF-CIV-20 TTL refresh scheduler | E2 | Expiring one chunk's findings re-enqueues exactly that chunk at priority 300 | Sonnet |
| E4 | E4 | Twenty-company pilot and calibration | E2, E3 | Citation violations 0; grade-A fill ≥60%; cost per company <$1.00; Stu's three-dossier confirmation | Opus |

**Critical path.** A1 → A2 → A3 → C2 → C3 → D3 → D4 → E1 → E2 → E4. Nine hops. Every other work
package hangs off it.

**Parallelization.** B1, B2 and B4 have no dependency on the Phase A queue work beyond A1 and
should start immediately — B4 in particular is on nobody's critical path but blocks six
jurisdiction datapoints, so starting it late is the most common way this build ends with an empty
section 2 of the dossier. Within Phase D, D2, D3 and D5 are mutually independent once C3 exists
and are the widest parallel fan in the build; only D4 must wait, because it reads what D3 stores.

## 9. Execution model for build agents

### 9.1 Dispatch protocol

One work package, one fresh agent session. Review the gate evidence before dispatching the next.
A failed gate returns to the same work package with the failure output attached, never forward to
the next. Never span a phase boundary in a single dispatch — the phase gates in 9.3 exist because
the failure modes they catch are invisible from inside a single package.

### 9.2 Briefing template

```
You are building work package <WP-ID> of the CiV Dossier Engine.

ENVIRONMENT
- Supabase project: hoyinfxpotpwkhzsgime (MCP tools available)
- n8n: self-hosted, MCP tools available. Credentials already present:
    Compliance Supabase  Nm1h0bjPqIZc2MAB
    OpenRouter           WkivISO0KPmV0dNq
    CourtListener Token  pCvA69grsS2sgc4P
    Tavily               aGz5l9Pc4hhk9VXd
    Apify                KC4i5wo7SNt8e4XS
    Slack                sykoBGqJPyOBA1Kz
    Airscale             vRVJcn1nRmJtDkLw
- Plan: plans/civ-dossier-engine-implementation.md, Task <N>. Execute it verbatim.

HARD RULES
- P2: never relax the citation_gate constraint. If an insert fails it, fix the caller.
- P4: only civ_project_company() writes companies.civ.
- P5: if your package is an archetype 'sql' chunk, no model call may appear anywhere in it.
- P6: never dispatch a datapoint whose method = 'ask' to a model.
- No Claude, Anthropic or OpenAI model in any runtime path. Kimi K2 and DeepSeek V3 only.

GATE
<paste the Gate cell from the section 8 table>

Run the verification queries from Task <N> and paste their actual output. If the output does
not match what the task says to expect, STOP and report the mismatch. Do not improvise a fix,
do not adjust the expectation, and do not proceed to the next task.
```

### 9.3 Phase gates

| Gate | After phase | Evidence required |
|---|---|---|
| G-A | A | Output of the deliberately-failing insert showing `violates check constraint "citation_gate"` |
| G-B | B | Catalog counts by category, and the archetype distribution query |
| G-C | C | One company's `civ_chunk_run` row at status `done` with N01–N10 findings listed |
| G-D | D | `civ_citation_violation` = 0 plus ten hand-verified quotes with their URLs |
| G-E | E | The four pilot numbers: completion, per-category fill, citation integrity, cost per company |

### 9.4 Model selection rationale

Packages that are fully specified by the plan — DDL application, column additions, catalog
loading, a scheduled workflow with fixed nodes — go to Sonnet. Packages with real degrees of
freedom go to Opus: the dependency view (A3) because a subtly wrong `NOT EXISTS` produces a
queue that looks right and runs chunks out of order; the prompts (B3) because they are the
system's only defence against fabrication before the constraint catches it; the runner (C3)
because seven archetypes share one control flow; the disqualifier (D1) because name matching is
judgement; and every gate-bearing package in D and E.

**Escalation rule.** Two failed gates on the same work package under Sonnet — re-dispatch to Opus
with both failure transcripts attached.

Note that this selection governs the **build agents only**. The runtime contains no Claude model
of any kind: collection runs on Kimi K2 and DeepSeek V3 through OpenRouter, per the constraint
that Claude stays out of the CiV agent stack.

## 10. Environment and credentials matrix

| Resource | Identifier | Status | Who acts |
|---|---|---|---|
| Supabase project | `hoyinfxpotpwkhzsgime` | Exists, 504 companies loaded | Build agent |
| n8n Compliance Supabase | `Nm1h0bjPqIZc2MAB` | Exists | Build agent |
| OpenRouter | `WkivISO0KPmV0dNq` | Exists | Build agent |
| CourtListener token | `pCvA69grsS2sgc4P` | Exists | Build agent |
| Tavily search | `aGz5l9Pc4hhk9VXd` | Exists | Build agent |
| Apify | `KC4i5wo7SNt8e4XS` | Exists | Build agent |
| Slack | `sykoBGqJPyOBA1Kz` | Exists | Build agent |
| Airscale (LinkedIn) | `vRVJcn1nRmJtDkLw` | Exists | Build agent |
| NANPA refresh workflow | `LX7srZ3KlMeQVmYy` | Exists and active | Build agent calls it |
| `pg_trgm` extension | — | **Must be confirmed enabled** — required by D1 name matching | **User action item** |
| Slack channels `#civ-ops`, `#civ-dossiers` | — | **Must be created** | **User action item** |
| Supabase Storage bucket `dossiers` | — | **Must be created** | **User action item** |
| Kimi K2 / DeepSeek V3 spend limit on OpenRouter | — | **Must be set** before the full run | **User action item** |
| n8n queue mode (Redis + workers) | — | **Must be configured on Hostinger** — see risk 2 | **User action item** |
| Apify monthly plan | — | **Must be confirmed** sized for ~30,000 page renders per pass | **User action item** |
| Tavily plan | — | **Must be confirmed** sized for ~11,000 searches per pass | **User action item** |

No credential in this table is created by a build agent. Everything marked as a user action item
is a secret, a billing decision, or an infrastructure change that only Rad can make.

## 11. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | A fabricated datapoint reaches a dossier Stu acts on | Medium | Severe — destroys trust in all 134 | `citation_gate` CHECK (A1), runner-side enforcement (C3), `civ_citation_violation` at 100% coverage (A4), PC-22 release gate (E2) |
| 2 | n8n stays in default single-process mode; a full pass takes a week and risks out-of-memory | High if not addressed | High | Queue mode listed as a user action item in section 10; the queue design already supports multiple workers via `FOR UPDATE SKIP LOCKED` (A2) |
| 3 | Concurrent chunks overwrite each other in `companies.civ` | High if P4 is violated | High — silent data loss | Findings moved to their own table with PK `(company_id, datapoint_id)` (A1); `companies.civ` written only by `civ_project_company()` (A4) |
| 4 | Name collision disqualifies a real prospect at SCR-01 | Medium | High — the prospect is lost silently | Adjudication step using state and DBA (D1); disqualified share must land 20–40% or the package fails its gate; every disqualification stores its reason |
| 5 | `civ_state_overlay` never gets seeded; six jurisdiction datapoints stay empty | Medium | Medium | B4 is a named work package with its own gate; PC-20's verification explicitly expects 0 findings until B4 runs |
| 6 | Apify returns static HTML; D04 (pre-checked box) and G03 (call-tracking DIDs) become unanswerable | Medium | Medium | D3's gate requires a non-empty `checkboxes` array with `defaultChecked` present in a stored artifact before D4 may start |
| 7 | DeepSeek drifts on strict JSON under load | High | Low | One repair retry with the validator error appended (D4); a second failure marks the run `failed` and the reaper retries it |
| 8 | Unattended spend runs away | Medium | High | `civ_budget` daily cap checked as the first node of every workflow (C1); `max_tool_calls` per chunk (B2); OpenRouter spend limit as a user action item |
| 9 | Stuck claims silently stall the queue | Medium | Medium | 30-minute reaper in WF-CIV-00 (C1) |
| 10 | The catalog's grade-C datapoints prove uncollectable at scale, and coverage disappoints | Medium | Low | E4's per-category fill query makes it visible at 20 companies rather than 504; grade-A fill ≥60% is the gate, grade-C is not gated |

## 12. Assumptions and out of scope

**Assumptions.** The 134-row catalog supplied on 2026-08-20 is the collectible subset of a larger
list; the chunk graph's `produces` arrays reference 160 codes, the extra 26 being 16 ask-only
datapoints and the 10 computed `S` scores, so 26 codes in the graph will have no catalog row
until that fuller list is loaded — WP B1's gate reports them rather than inventing them. The
`civ_chunk_def` dependency graph is assumed correct as authored; this plan does not re-derive it.
`companies.industry_type` is assumed to be a usable vertical label — it currently reads 258 solar
and 220 HVAC with no insurance rows, so the insurance segment of the stated ICP is not
represented in the present 504 and no work package will surface that absence. Public sources are
assumed to remain reachable without authentication; a source that begins requiring login becomes
an ask-only datapoint rather than a build failure.

**Out of scope.** No outbound message of any kind is generated — no cold email, no one-pager, no
deck. The deliverable is the dossier; a human decides what to send. State-court litigation (N03)
is out of scope in v1 because access is per-county and largely paywalled. PC-24, consent change
history from Wayback Machine snapshots, is marked optional in the graph and deferred to v2.
YouMail data is not integrated; the telephony chunks use NANPA and the public complaint corpora
only. Attio and Instantly synchronisation, though credentialed and present in the stack, is a
downstream concern once dossiers exist and is deliberately not wired into this engine.

# Appendix A — Implementation plan (construction drawings)

What follows is the complete task-level plan. Every task carries its exact DDL or node list, the
code to be typed, and a verification query whose expected output is stated. Build agents execute
from here; Part I above exists to explain why these instructions are shaped the way they are.
