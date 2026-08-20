# CiV Dossier Engine — Build Plan

**Owner:** Rad (Technical Operations) · **Requested by:** Stu (Sales Lead)
**Target:** 504 prospects × 182 datapoints → one research dossier per company, unattended.
**Status:** Plan. Nothing built yet.

---

## 0. Assumption you need to correct before Work Package 1

I do not have the actual 182-datapoint Master Catalog in front of me. Everything
below that references specific datapoints uses a **proposed 15-group structure**
that sums to exactly 182 and is shaped around what a Telephone Consumer
Protection Act (TCPA) / Do Not Call (DNC) prospecting dossier needs.

The architecture does not depend on the grouping being right. The grouping lives
in a database table (`civ_datapoint_groups`) and is edited with a Structured
Query Language (SQL) `UPDATE`, never by touching n8n. So: build the plumbing
from this document, then map the real catalog onto `civ_datapoints` in Work
Package 1 and regroup freely.

**Acronyms used throughout,** spelled out here once:
TCPA (Telephone Consumer Protection Act), DNC (Do Not Call), API (Application
Programming Interface), LLM (Large Language Model), ICP (Ideal Customer
Profile), TTL (Time To Live), DDL (Data Definition Language), VPS (Virtual
Private Server), JSON (JavaScript Object Notation), CRM (Customer Relationship
Management), BPO (Business Process Outsourcing), SDR (Sales Development
Representative), NANPA (North American Numbering Plan Administrator), FCC
(Federal Communications Commission), FTC (Federal Trade Commission), BBB (Better
Business Bureau), SOS (Secretary of State), NAICS (North American Industry
Classification System), DBA (Doing Business As), ToS (Terms of Service), WBS
(Work Breakdown Structure), SLA (Service Level Agreement).

---

## 1. The architecture in one page

Seven stages. Each is a separate n8n workflow. They communicate **only through
Supabase tables** — no workflow calls another workflow synchronously, and no
single n8n execution ever holds more than one company's one slice.

```
                    civ_companies (504 rows, status column)
                              |
   [WF-01 Gate & Enqueue]  every 30 min
        |  step 0: litigation disqualifier (deterministic, ~$0)
        |  -> status = 'disqualified'  (stop, spend nothing more)
        |  -> status = 'qualifying'    (enqueue acquire jobs)
                              |
                     civ_agent_jobs (queue)
                              |
   [WF-02 Acquire Worker]  every 5 min, claims 10 jobs
        |  chunked BY SOURCE (11 sources) — fetch each page ONCE
        |  6 of 11 sources need no agent at all (plain HTTP Request)
                              v
                  civ_company_evidence (raw markdown + structured JSON)
                              |
   [WF-03 Extract Worker]  every 5 min, claims 10 jobs
        |  chunked BY DATAPOINT GROUP (15 groups of 8-13)
        |  reads the evidence store, NOT the live web
        |  every value must carry source_url + verbatim quote or it is null
                              v
                 civ_company_datapoints  +  civ_datapoint_conflicts
                              |
   [WF-04 Score & Promote]  every 15 min
        |  mid-gate: score after groups G1/G2/G3
        |  below threshold -> stop. above -> enqueue the 11 deep groups
                              |
   [WF-05 Compose]  every 15 min
        |  deterministic Markdown template + one small LLM pass for the summary
                              v
              dossier .md file (Obsidian import) + discovery-call question list

   [WF-00 Budget Guard & Reaper]  every 5 min   — spend cap, stuck-job reaper
   [WF-06 Citation Audit]         nightly       — verify 5% of quotes actually exist
   [WF-07 Refresh Scheduler]      nightly       — TTL expiry -> re-enqueue
```

### The two design decisions that matter most

**1. Acquisition is chunked by source; extraction is chunked by datapoint.**

Your original design chunked everything by datapoint. That is correct for
extraction and wrong for acquisition, because the web is organised by page, not
by field. Employee count, funding, and executive names may all live on one
LinkedIn page. If they sit in three different datapoint groups, three agents
fetch that page, you pay Firecrawl three times, and you get three different
readings with nothing reconciling them.

Splitting into two phases keeps your core insight — no agent ever sees more than
its own slice — while eliminating the redundancy. It also makes reruns nearly
free: add datapoint #183 next month and you re-run one extraction agent against
cached evidence instead of re-crawling 504 companies.

**2. A value without evidence is null, enforced by the database, not by the prompt.**

An agent asked "how many outbound calls per day does this company make?" will not
return null. It will invent a plausible number. One fabricated fact in a dossier
that Stu acts on destroys trust in all 182. The schema below makes an unsourced
value physically impossible to store.

---

## 2. Database schema (Supabase project `hoyinfxpotpwkhzsgime`)

Full DDL. Apply as one migration named `civ_dossier_engine_v1`.

### 2.1 Companies

```sql
create table civ_companies (
  id                  uuid primary key default gen_random_uuid(),
  legal_name          text not null,
  dba_name            text,
  domain              text unique,
  linkedin_url        text,
  apollo_org_id       text,
  hq_state            text,
  operating_states    text[],
  vertical            text,        -- solar | hvac | insurance | other
  seat_estimate       int,

  status              text not null default 'new',
  -- new | gated | qualifying | qualified | disqualified
  -- | acquiring | extracting | composing | complete | failed
  disqualify_reason   text,
  fit_score           numeric,
  gate_checked_at     timestamptz,
  scored_at           timestamptz,
  dossier_path        text,
  dossier_rendered_at timestamptz,

  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);
create index civ_companies_status_idx on civ_companies (status);
create index civ_companies_domain_idx on civ_companies (domain);
```

Your ICP is 50–500 seats in solar, HVAC (heating, ventilation, air
conditioning), and insurance. `seat_estimate` and `vertical` are the two columns
that pick the 504 out of a larger list; keep them populated at load time.

### 2.2 Datapoint groups — the tuning surface

```sql
create table civ_datapoint_groups (
  id                int primary key,
  name              text not null,
  archetype         text not null,   -- api_lookup | web_research | browser | inference
  model             text not null,   -- OpenRouter model slug
  phase             text not null,   -- gate | qualify | deep
  system_prompt     text not null,
  tool_allowlist    text[],
  depends_on_sources text[],         -- evidence sources that must exist first
  max_tool_calls    int default 12,
  max_evidence_chars int default 60000,
  sort_order        int
);
```

This is the table you edit to change agent behaviour. Prompts, model choice,
tool access, and which datapoints belong to which group are **all data**. No n8n
edit is ever required to retune the system.

### 2.3 The 182 datapoints

```sql
create table civ_datapoints (
  id                 int primary key,          -- 1..182
  code               text unique not null,     -- 'firmographic.employee_count'
  label              text not null,
  definition         text not null,            -- what exactly counts as a value
  group_id           int not null references civ_datapoint_groups(id),
  method             text not null,            -- api | web_extract | inferred | discovery_call
  value_type         text not null,            -- string|number|boolean|date|enum|array|money
  enum_values        text[],
  source_priority    text[],                   -- ['linkedin','apollo','site_crawl']
  requires_browser   boolean default false,
  ttl_days           int not null default 90,
  is_gate            boolean default false,
  gate_weight        numeric default 0,
  discovery_question text,                     -- used when method='discovery_call'
  extraction_hint    text                      -- appended to the group prompt
);
```

Three columns here carry unusual weight.

**`method`** is declared in advance, never discovered at runtime. Your line —
"if a datapoint can't be reached by an agent, it becomes a question for the
discovery call" — is exactly right, but it has to be a property of the datapoint
written down before the run. Letting an agent flail and *then* conclude
unreachability is the precise condition under which it hallucinates instead.
Anything marked `discovery_call` is never sent to an agent at all; it flows
straight to the question list in the dossier.

**`ttl_days`** is what turns this from a one-time 504-company blast into the
TCPA Early Warning System. Legal entity name: 3650 days. Executive names: 180.
A job posting for "outbound sales representative": 7 — and that one is a live
buying trigger. Once WF-07 selects work by `collected_at + ttl < now()`, the
identical architecture handles initial fill and ongoing monitoring with no new
code.

**`source_priority`** is the conflict resolution rule, per datapoint. See §6.

### 2.4 Evidence store

```sql
create table civ_company_evidence (
  id             bigserial primary key,
  company_id     uuid references civ_companies(id) on delete cascade,
  source         text not null,
  url            text,
  http_status    int,
  fetched_at     timestamptz default now(),
  content_hash   text,
  raw_markdown   text,
  structured     jsonb,
  token_estimate int,
  unique (company_id, source, url)
);
create index civ_evidence_lookup_idx on civ_company_evidence (company_id, source);
```

`content_hash` is a SHA-256 of `raw_markdown`. On refresh runs, if the hash is
unchanged you skip re-extraction entirely — a large saving on the 90-day cycle.

### 2.5 Datapoint values — the evidence-or-null table

```sql
create table civ_company_datapoints (
  company_id        uuid references civ_companies(id) on delete cascade,
  datapoint_id      int  references civ_datapoints(id),
  value_text        text,
  value_num         numeric,
  value_bool        boolean,
  value_date        date,
  value_json        jsonb,
  confidence        text,      -- high | medium | low
  source_url        text,
  evidence_quote    text,
  method            text,
  reason_unavailable text,
  collected_at      timestamptz default now(),
  expires_at        timestamptz,
  agent_run_id      bigint,
  primary key (company_id, datapoint_id),

  constraint evidence_or_null check (
    (value_text is null and value_num is null and value_bool is null
     and value_date is null and value_json is null)
    or method = 'inferred'
    or (source_url is not null and evidence_quote is not null
        and length(evidence_quote) >= 10)
  )
);
create index civ_datapoints_expiry_idx on civ_company_datapoints (expires_at);
```

The `evidence_or_null` CHECK constraint is the single most important line in
this document. A row carrying a value but no source and no quote will not
insert. The database rejects it. `method='inferred'` is exempted because derived
datapoints (group G14) cite other datapoints rather than a URL — those carry
their inputs in `value_json.derived_from`.

### 2.6 Conflicts

```sql
create table civ_datapoint_conflicts (
  id               bigserial primary key,
  company_id       uuid,
  datapoint_id     int,
  candidates       jsonb,   -- [{value, source, source_url, confidence}]
  resolved_value   text,
  resolution_rule  text,
  flagged_for_human boolean default false,
  created_at       timestamptz default now()
);
```

### 2.7 Job queue

```sql
create table civ_agent_jobs (
  id           bigserial primary key,
  company_id   uuid not null references civ_companies(id) on delete cascade,
  stage        text not null,   -- acquire | extract | compose
  target       text not null,   -- source name (acquire) | group id (extract)
  status       text not null default 'pending',
  -- pending | claimed | done | failed | dead
  attempts     int default 0,
  max_attempts int default 3,
  priority     int default 100,
  claimed_at   timestamptz,
  claimed_by   text,
  completed_at timestamptz,
  last_error   text,
  created_at   timestamptz default now()
);
create unique index civ_jobs_dedupe_idx
  on civ_agent_jobs (company_id, stage, target) where status <> 'dead';
create index civ_jobs_claim_idx on civ_agent_jobs (status, priority, id);
```

The partial unique index is the idempotency guarantee: a re-fired schedule
cannot enqueue the same work twice. Lower `priority` number = claimed first.

### 2.8 Run log and budget

```sql
create table civ_agent_runs (
  id                bigserial primary key,
  job_id            bigint,
  company_id        uuid,
  stage             text,
  target            text,
  model             text,
  started_at        timestamptz,
  finished_at       timestamptz,
  prompt_tokens     int,
  completion_tokens int,
  tool_calls        int,
  fetch_count       int,
  cost_usd          numeric,
  status            text,
  error             text
);

create table civ_run_budget (
  day            date primary key default current_date,
  llm_cost_usd   numeric default 0,
  fetch_count    int default 0,
  fetch_cost_usd numeric default 0,
  llm_cap_usd    numeric default 25,
  fetch_cap      int default 8000,
  halted         boolean default false
);
```

An unattended agent loop against paid APIs with no cap is how you find a
four-figure bill on Monday morning. Every worker workflow's first node reads
`civ_run_budget` and no-ops when `halted` is true.

### 2.9 Citation audit

```sql
create table civ_citation_audits (
  id             bigserial primary key,
  company_id     uuid,
  datapoint_id   int,
  source_url     text,
  evidence_quote text,
  fetch_ok       boolean,
  quote_found    boolean,
  checked_at     timestamptz default now()
);
```

---

## 3. The 15 datapoint groups (proposed, sums to 182)

| # | Group | Count | Phase | Archetype | Model | Depends on evidence sources |
|---|-------|-------|-------|-----------|-------|------------------------------|
| G0 | Litigation & Enforcement Disqualifier | 8 | gate | api_lookup | gemini-2.5-flash | courtlistener, fcc |
| G1 | Firmographics & Identity | 13 | qualify | web_research | gemini-2.5-flash | apollo, site_crawl, sos |
| G2 | Outbound Motion Evidence | 13 | qualify | web_research | kimi-k2 | site_crawl, job_boards |
| G3 | Telephony Footprint | 12 | qualify | api_lookup | gemini-2.5-flash | telephony, site_crawl |
| G4 | Consent & Disclosure Posture | 13 | deep | browser | kimi-k2 | site_crawl |
| G5 | Lead Sources & Vendors | 12 | deep | web_research | kimi-k2 | site_crawl, tech_stack |
| G6 | Marketing Technology Stack | 13 | deep | api_lookup | gemini-2.5-flash | tech_stack, site_crawl |
| G7 | Call Center & Staffing | 12 | deep | web_research | kimi-k2 | job_boards, reviews, linkedin |
| G8 | Regulatory & Licensing | 13 | deep | browser | kimi-k2 | state_license, sos |
| G9 | Complaint & Reputation Signals | 13 | deep | web_research | kimi-k2 | reviews, fcc |
| G10 | Litigation History & Adjacency | 12 | deep | api_lookup | gemini-2.5-flash | courtlistener |
| G11 | Buying Committee & Contacts | 13 | deep | api_lookup | gemini-2.5-flash | apollo, linkedin |
| G12 | Financial & Timing Triggers | 12 | deep | web_research | kimi-k2 | site_crawl, apollo |
| G13 | Competitive & Incumbency | 13 | deep | web_research | kimi-k2 | site_crawl, tech_stack |
| G14 | Inference & Synthesis | 10 | deep | inference | kimi-k2 | *(none — reads G0–G13)* |

Total: 8+13+13+12+13+12+13+12+13+13+12+13+12+13+10 = **182**.

Group sizes land 10–13, inside your target band. G0 is 8 because it is a pure
kill-switch and should be as cheap as possible.

**G14 fetches nothing.** It reads the other 172 collected values and derives:
risk tier, estimated exposure, urgency, best entry angle, the "trigger"
narrative CiV's methodology is built on, and the recommended opening line. It
is the only group permitted to produce a value without a URL, and it must
populate `value_json.derived_from` with the datapoint identifiers it used.

---

## 4. The 11 evidence sources (acquisition, WF-02)

| Source | Agent needed? | Mechanism | Cost per company |
|--------|---------------|-----------|------------------|
| `apollo` | No | Apollo.io organisation + people enrichment API | 1–3 credits |
| `courtlistener` | No | Existing pipeline, `/api/rest/v4/search/?type=r`, `suitNature=485` | free |
| `fcc` | No | FCC SODA API, dataset `vakf-fz8e` + enforcement database | free |
| `sos` | No | State Secretary of State entity lookup | free |
| `telephony` | No | NANPA lookup, carrier-of-record, YouMail (when licensed) | varies |
| `tech_stack` | No | HTML fingerprint from the crawl + BuiltWith-style detection | ~$0.01 |
| `site_crawl` | **Yes** | Firecrawl `/crawl`, depth 2, `limit: 40` | ~40 credits |
| `job_boards` | **Yes** | Indeed / LinkedIn Jobs search + scrape | ~10 credits |
| `reviews` | **Yes** | BBB, Trustpilot, Glassdoor, Google | ~10 credits |
| `state_license` | **Yes** (browser) | Per-vertical licence portals, mostly JavaScript-gated | ~5 renders |
| `linkedin` | **Yes** | Company page + headcount trend, via Apollo/Airscale | 1–2 credits |

**Six of eleven sources need no agent at all.** They are plain n8n HTTP Request
nodes with deterministic parsing. That is roughly 55% of acquisition volume
running at near-zero token cost and around 8 seconds per job instead of 90.
Do not put an LLM in front of a REST endpoint that returns clean JSON.

**Do not give every agent a browser.** Firecrawl `/scrape` with
`formats: ['markdown']` handles the overwhelming majority of pages, faster and
cheaper than a real browser session. Reserve Browserless/Playwright for
`state_license` and the handful of JavaScript-gated review portals, declared
per-source via `requires_browser`.

---

## 5. n8n workflows, node by node

Twelve workflows total. Eight orchestration, four agent archetypes folded into
one runner.

### WF-00 — Budget Guard & Reaper (every 5 minutes)

1. **Schedule Trigger** — `*/5 * * * *`
2. **Postgres** — upsert today's budget row:
   `insert into civ_run_budget (day) values (current_date) on conflict do nothing`
3. **Postgres** — roll up spend from `civ_agent_runs` for today, write to
   `civ_run_budget`, set `halted = (llm_cost_usd >= llm_cap_usd or fetch_count >= fetch_cap)`
4. **Postgres** — reap stuck jobs:
   ```sql
   update civ_agent_jobs
      set status = 'pending', claimed_at = null, claimed_by = null
    where status = 'claimed' and claimed_at < now() - interval '30 minutes';
   ```
5. **Postgres** — kill exhausted jobs:
   ```sql
   update civ_agent_jobs set status = 'dead'
    where status = 'failed' and attempts >= max_attempts;
   ```
6. **IF** `halted` → **Slack** node, post to `#civ-ops`, once per day.

### WF-01 — Gate & Enqueue (every 30 minutes)

1. **Schedule Trigger** — `*/30 * * * *`
2. **Postgres** — budget check → **IF** halted → stop
3. **Postgres** — claim up to 50 companies with `status = 'new'`
4. **Postgres** — litigation disqualifier, deterministic, no LLM:
   ```sql
   select c.id,
          exists (
            select 1 from tcpa_dockets d
             where d.defendant ilike '%' || c.legal_name || '%'
                or (c.dba_name is not null and d.defendant ilike '%' || c.dba_name || '%')
          ) as has_docket
     from civ_companies c where c.id = any($1);
   ```
5. **HTTP Request** — FCC enforcement database check on the same names
6. **AI Agent** (Gemini 2.5 Flash, no tools) — name adjudication only. Company
   names collide; "Solar Solutions LLC" in Arizona is not the one in Florida.
   Feed it the docket defendant string, the company's legal name, DBA, and
   state, and ask for a boolean plus a one-line reason. ~2,000 tokens.
7. **Switch**
   - match → `update civ_companies set status='disqualified',
     disqualify_reason='active_or_prior_tcpa_docket', gate_checked_at=now()`
   - no match → `status='qualifying'`, then enqueue acquire jobs:
     ```sql
     insert into civ_agent_jobs (company_id, stage, target, priority)
     select $1, 'acquire', unnest(array['apollo','courtlistener','fcc','sos',
       'telephony','tech_stack','site_crawl','job_boards','reviews',
       'state_license','linkedin']), 50
     on conflict do nothing;
     ```

**This gate is the largest cost lever in the system.** CiV is prevention-only —
you will not take a client already sued or about to be sued. Litigation status
is therefore a disqualifier, and it is the cheapest datapoint you own because
`tcpa_dockets` is already populated. At a plausible 30% hit rate you avoid
roughly 2,000 downstream agent runs for essentially zero cost.

### WF-02 — Acquire Worker (every 5 minutes)

1. **Schedule Trigger** — `*/5 * * * *`
2. **Postgres** — budget check → **IF** halted → stop
3. **Postgres** — claim a batch. This SQL is the concurrency primitive:
   ```sql
   update civ_agent_jobs
      set status = 'claimed', claimed_at = now(), claimed_by = $worker_id,
          attempts = attempts + 1
    where id in (
      select id from civ_agent_jobs
       where stage = 'acquire' and status = 'pending'
       order by priority, id
       limit 10
       for update skip locked
    )
   returning *;
   ```
   `FOR UPDATE SKIP LOCKED` is what lets multiple n8n workers pull from the same
   queue without collision or double-processing. Without it, queue mode gives you
   duplicate work instead of throughput.
4. **IF** zero rows → stop
5. **Split In Batches** — batch size 1
6. **Switch** on `target` → 11 branches
   - `apollo` → **HTTP Request** `POST https://api.apollo.io/v1/organizations/enrich`
   - `courtlistener` → **HTTP Request**, existing pagination loop via
     `$getWorkflowStaticData('global')` (n8n's built-in pagination fails on the
     null `response.next` this endpoint returns)
   - `fcc` → **HTTP Request** SODA, dataset `vakf-fz8e`
   - `sos`, `telephony`, `tech_stack` → **HTTP Request**
   - `site_crawl`, `job_boards`, `reviews`, `state_license`, `linkedin` →
     **Execute Workflow** → WF-08 Agent Runner
7. **Code** — normalise every branch to a common evidence row: compute
   `content_hash = sha256(raw_markdown)`, `token_estimate = length/4`
8. **Postgres** — upsert `civ_company_evidence`
   (`on conflict (company_id, source, url) do update`)
9. **Postgres** — mark job `done`, insert `civ_agent_runs`
10. **Error Trigger path** — set job back to `pending` with `last_error`; WF-00
    promotes it to `dead` after 3 attempts.

### WF-03 — Extract Worker (every 5 minutes)

1. **Schedule Trigger** — `*/5 * * * *`
2. **Postgres** — budget check
3. **Postgres** — claim 10 `stage='extract'` jobs (same `SKIP LOCKED` pattern)
4. **Split In Batches** — size 1
5. **Postgres** — load the group definition and its datapoint specs:
   ```sql
   select g.*,
          json_agg(json_build_object(
            'id', d.id, 'code', d.code, 'label', d.label,
            'definition', d.definition, 'value_type', d.value_type,
            'enum_values', d.enum_values, 'hint', d.extraction_hint
          ) order by d.id) as datapoints
     from civ_datapoint_groups g
     join civ_datapoints d on d.group_id = g.id
    where g.id = $1 and d.method <> 'discovery_call'
    group by g.id;
   ```
   Note the `method <> 'discovery_call'` filter — unreachable datapoints are
   never shown to an agent.
6. **Postgres** — load evidence for `depends_on_sources`, ordered by
   `token_estimate` descending, truncated to `max_evidence_chars`
7. **Code** — assemble the prompt (§7)
8. **HTTP Request** — `POST https://openrouter.ai/api/v1/chat/completions`
   with `response_format: { type: 'json_schema', json_schema: {...strict: true} }`
9. **Code** — validate the response against the group's JSON schema. On failure,
   one repair call: resend with the validator error appended. Second failure →
   job `failed`.
10. **Code** — enforce the evidence rule in application code as well as the
    database constraint, so you get a clean `reason_unavailable` instead of a
    Postgres exception:
    ```javascript
    for (const dp of out.datapoints) {
      const hasEvidence = dp.source_url && dp.evidence_quote
                          && dp.evidence_quote.length >= 10;
      if (dp.value !== null && !hasEvidence && dp.method !== 'inferred') {
        dp.value = null;
        dp.reason_unavailable = 'model_returned_value_without_citation';
        dp.confidence = null;
      }
    }
    ```
11. **Postgres** — upsert `civ_company_datapoints`, setting
    `expires_at = now() + (ttl_days || ' days')::interval`
12. **Code + Postgres** — conflict detection (§6)
13. **Postgres** — mark done, log the run.

### WF-08 — Agent Runner (sub-workflow, called by WF-02 and WF-03)

This is where tool isolation lives. Four AI Agent nodes behind a Switch, rather
than 13 separate workflows.

1. **Execute Workflow Trigger** — input: `archetype, model, system_prompt,
   payload, max_tool_calls`
2. **Switch** on `archetype`:
   - `api_lookup` → **AI Agent** with tools: `[postgres_query]`
   - `web_research` → **AI Agent** with tools: `[serper_search, firecrawl_scrape]`
   - `browser` → **AI Agent** with tools: `[serper_search, firecrawl_scrape, browserless_render]`
   - `inference` → **AI Agent** with **no tools**
3. Each branch uses an **OpenRouter Chat Model** node with the model taken from
   input, so model choice stays data-driven
4. **Merge** → return `{ output, tool_calls, usage }`

Building 13 sub-workflows — one per group — would mean 13 things to version and
keep in sync. Four archetypes parameterised by a database row means you retune
with SQL.

### WF-04 — Score & Promote (every 15 minutes)

1. **Schedule Trigger** — `*/15 * * * *`
2. **Postgres** — find companies where G1, G2 and G3 extract jobs are all `done`
   and `scored_at is null`
3. **Code** — compute the fit score (§8)
4. **Switch**
   - `fit_score < 40` → `status='disqualified'`, `disqualify_reason='low_fit_score'`
   - `fit_score >= 40` → `status='extracting'`, enqueue the 11 deep groups
     (G4–G13) as extract jobs, priority 100
5. G14 (inference) is enqueued separately with priority 200 so it always runs
   after the groups it depends on.

### WF-05 — Compose (every 15 minutes)

1. **Schedule Trigger** — `*/15 * * * *`
2. **Postgres** — companies where every enqueued extract job is `done`
3. **Postgres** — load all 182 rows joined to their definitions
4. **Code** — render the dossier Markdown from a **deterministic template**.
   Same structure every time, zero invention. Includes the auto-generated
   discovery-call question list: every datapoint where `method='discovery_call'`
   or `value is null`, rendered as its `discovery_question`.
5. **HTTP Request** — one small LLM pass for a three-sentence "why this company,
   why now" summary, hard-constrained to reference only datapoints that carry
   evidence. Pass it the evidenced values only; it cannot cite what it cannot see.
6. **Code** — splice the summary into the template
7. **Supabase Storage** (or Google Drive) — write
   `dossiers/{vertical}/{legal_name}.md`
8. **Postgres** — `status='complete'`, set `dossier_path`, `dossier_rendered_at`
9. **Slack** — post to `#civ-dossiers` with the company name, fit score, and link.

**The compose step is the one your original five-stage shape was missing.** 182
rows in Postgres is not a dossier. And it should be a template, not an agent:
you want identical structure across 504 companies so Stu can scan them, and you
want zero opportunity for invention at the final step.

### WF-06 — Citation Audit (nightly, 02:00)

1. **Schedule Trigger** — `0 2 * * *`
2. **Postgres** — sample 5% of datapoints written in the last 24 hours that have
   a `source_url`
3. **HTTP Request** — fetch each `source_url`
4. **Code** — normalise whitespace, check whether `evidence_quote` appears in the
   body. This is a `fetch` and an `indexOf`. **No LLM required.**
5. **Postgres** — write `civ_citation_audits`
6. **Postgres** — aggregate failure rate per `group_id`
7. **IF** any group exceeds 10% citation failure → **Slack** alert.

This is the cheapest quality control in the system and it is what tells you a
prompt is broken in week one rather than month four. Watch the per-group rate,
not the global average.

### WF-07 — Refresh Scheduler (nightly, 03:00)

1. **Schedule Trigger** — `0 3 * * *`
2. **Postgres** —
   ```sql
   select company_id, d.group_id, count(*) as stale
     from civ_company_datapoints cd
     join civ_datapoints d on d.id = cd.datapoint_id
    where cd.expires_at < now()
    group by company_id, d.group_id
   having count(*) >= 3;
   ```
3. Enqueue the acquire jobs for that group's `depends_on_sources`, then the
   extract job, at priority 300 (behind all new-company work)
4. On re-acquisition, if `content_hash` is unchanged, skip the extract job
   entirely and just bump `expires_at`.

---

## 6. Conflict handling — keep the disagreement, don't hide it

With source-major acquisition you *will* get conflicts. LinkedIn says 120
employees, Apollo says 85.

Resolution runs in WF-03 step 12:

1. Order candidates by the datapoint's `source_priority` array.
2. Write the winner to `civ_company_datapoints`.
3. Write **all** candidates to `civ_datapoint_conflicts`.
4. If the spread exceeds a per-type threshold (numbers: >25% relative
   difference; enums: any disagreement), set `flagged_for_human = true`.

Flagged conflicts render in the dossier as an explicit line:

> **Employee count:** 120 (LinkedIn, verified 2026-08-20) · conflicting: 85
> (Apollo). Discrepancy of 41% may indicate contractor or BPO-heavy staffing.

That is *more* useful to Stu than a single averaged number. A headcount gap
between LinkedIn and Apollo on a solar company very often means outsourced
outbound — which is precisely the CiV signal, and precisely the opening for the
"unify with your call center and vendors" positioning rather than the adversarial
framing.

---

## 7. Prompt template (extraction agents)

Assembled by WF-03 step 7. Every extraction agent receives exactly this shape.

```
SYSTEM
------
You are a research extraction agent for Compliance IV. You are given evidence
collected from public sources about one company, and a list of {N} datapoints
to extract from that evidence.

ABSOLUTE RULES
1. Extract only what the evidence literally supports. You are not permitted to
   use background knowledge about this company or its industry.
2. Every non-null value MUST include source_url and evidence_quote.
   evidence_quote must be a VERBATIM substring of the supplied evidence,
   at least 10 characters, that a person could locate on that page.
3. If the evidence does not support a datapoint, set value to null and write
   reason_unavailable. Returning null is a correct and expected outcome.
   A wrong value is far worse than a missing one.
4. Never infer, estimate, approximate, or round unless the datapoint definition
   explicitly says to.
5. Respect value_type and enum_values exactly.

{group.system_prompt}

DATAPOINTS TO EXTRACT
---------------------
{for each datapoint}
[{id}] {code} — {label}
  Definition: {definition}
  Type: {value_type}{, one of: enum_values}
  {extraction_hint}
{end}

OUTPUT
------
Return JSON matching the supplied schema. One object per datapoint id above.
Return every id, including those you could not find.

USER
----
COMPANY: {legal_name} ({domain}), {vertical}, HQ {hq_state}

EVIDENCE
{for each evidence row}
=== SOURCE: {source} | URL: {url} | FETCHED: {fetched_at} ===
{raw_markdown, truncated}
{end}
```

Two things about this prompt are deliberate and should not be softened.

**"Returning null is a correct and expected outcome"** — models default to
helpfulness and will fill gaps. You have to explicitly make abstention a success
state or you get fabrication.

**"You are not permitted to use background knowledge"** — without this line the
model blends training data with the evidence, and you get plausible facts that
are not in any source and cannot be audited. The citation audit catches these,
but preventing them is cheaper.

The JSON schema sent with `response_format`:

```json
{
  "type": "object",
  "required": ["datapoints"],
  "properties": {
    "datapoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["datapoint_id","value","confidence",
                     "source_url","evidence_quote","reason_unavailable"],
        "properties": {
          "datapoint_id":       {"type": "integer"},
          "value":              {"type": ["string","number","boolean","array","null"]},
          "confidence":         {"type": ["string","null"], "enum": ["high","medium","low",null]},
          "source_url":         {"type": ["string","null"]},
          "evidence_quote":     {"type": ["string","null"]},
          "reason_unavailable": {"type": ["string","null"]}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

## 8. Fit scoring (WF-04)

Score 0–100 from the qualify-phase groups. Promote at ≥ 40.

| Signal | Source | Points |
|--------|--------|--------|
| Seat count 50–500 | G1 | 20 |
| Vertical is solar / HVAC / insurance | G1 | 15 |
| Evidence of outbound calling (dialer, SDR postings, call-center vendor) | G2 | 25 |
| Owns telephone numbers / toll-free footprint | G3 | 10 |
| Poor or missing STIR/SHAKEN attestation posture | G3 | 10 |
| Consent language absent or non-compliant with the 2024 one-to-one rule | G2/G4 | 10 |
| Multi-state operation (raises state DNC surface area) | G1 | 5 |
| Complaint signals mentioning unwanted calls | G9 | 5 |
| **Penalty:** already retains a named compliance vendor | G13 | −15 |

Store the component breakdown in `civ_companies.fit_score` plus a
`score_breakdown jsonb` column so the dossier can show *why* a company scored
what it did. A score without its components is not actionable.

**Tune the 40 threshold after the pilot, not before.** Run 20 companies, have
Stu read all 20 dossiers regardless of score, and set the threshold where his
own yes/no split actually falls.

---

## 9. Cost and time

### Cost per full pass over 504 companies

Assumes 30% disqualified at the gate (353 proceed) and 55% of those clearing the
mid-gate (194 reach deep collection).

| Line item | Volume | Rate | Cost |
|-----------|--------|------|------|
| Gate adjudication (Gemini 2.5 Flash) | 504 × 2k tokens | $0.30/M in | ~$1 |
| Acquisition, agentic (Kimi K2) | 1,765 runs × 25k in / 2k out | ~$0.55/M in, $2.20/M out | ~$32 |
| Acquisition, agentless | 2,118 runs | HTTP only | $0 |
| Extraction, qualify phase | 353 × 3 = 1,059 runs | Gemini 2.5 Flash | ~$19 |
| Extraction, deep phase | 194 × 11 = 2,134 runs | Gemini 2.5 Flash | ~$39 |
| Inference (G14) | 194 runs × 15k in | Kimi K2 | ~$3 |
| Compose summary | 194 × 4k | Gemini 2.5 Flash | ~$1 |
| **LLM subtotal** | | | **~$95** |
| Firecrawl | ~25,000 page credits | Standard plan, 100k credits | $83/mo |
| Serper search | ~9,000 queries | $50 / 100k | ~$5 |
| Browserless renders | ~1,000 | | ~$10 |
| Apollo.io | ~700 credits | existing plan | — |
| **Fetch subtotal** | | | **~$98** |
| **Total per full pass** | | | **~$195** |

Roughly **$0.39 per company** for a fully cited 182-datapoint dossier. The
token cost is genuinely not the constraint here — do not optimise it.

### Time

| Stage | Runs | Seconds each | Single-threaded |
|-------|------|--------------|-----------------|
| Acquire, agentless | 2,118 | ~8 | 4.7 h |
| Acquire, agentic | 1,765 | ~90 | 44 h |
| Extract | 3,387 | ~35 | 33 h |
| Compose | 194 | ~15 | 0.8 h |
| **Total** | | | **~83 h** |

At 8 concurrent workers in n8n queue mode: **roughly 11 hours of machine time.**
Allowing for retries, third-party rate limits, and overnight windows, plan on
**2–3 calendar days for the first full pass.**

Wall-clock time, not money, is your constraint. That is what makes the two gates
worth building — they remove roughly half the runs, not half the dollars.

---

## 10. Infrastructure changes required on Hostinger

**n8n must run in queue mode.** This is not optional at this volume. In default
mode you get a single main process, all item data held in memory, and 7,000 jobs
will take a week while risking out-of-memory kills on the VPS.

```
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
N8N_CONCURRENCY_PRODUCTION_LIMIT=8
```

Run Redis plus 2–4 worker containers alongside the main container.

**Execution data pruning.** This workflow generates enormous execution history
and will fill the disk within days.

```
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=72
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_ON_ERROR=all
```

Saving nothing on success is deliberate: `civ_agent_runs` is your audit trail,
and it is a database table you can query, not an n8n execution blob you cannot.

**Credentials to create in n8n:**

| Credential | Type | Used by |
|------------|------|---------|
| Supabase Postgres | Postgres | every workflow |
| OpenRouter | HTTP Header Auth (`Authorization: Bearer …`) | WF-01, 03, 05, 08 |
| Firecrawl | HTTP Header Auth | WF-02, WF-08 |
| Serper | HTTP Header Auth (`X-API-KEY`) | WF-08 |
| Browserless | HTTP Query Auth (`token`) | WF-08 |
| Apollo.io | HTTP Header Auth | WF-02 |
| CourtListener | HTTP Header Auth (`Authorization: Token …`) | WF-02 |
| FCC SODA | HTTP Query Auth (`$$app_token`) | WF-02 |
| Slack | OAuth2 | WF-00, 05, 06 |

---

## 11. Model assignment

"No Claude in the CiV agent stack" is the constraint and this design respects it.
Split by role rather than picking one model for everything:

**Kimi K2 (`moonshotai/kimi-k2`) for tool-using work** — the five agentic
acquisition sources, and groups G2, G4, G5, G7, G8, G9, G12, G13, G14. It is the
stronger of the two candidates at multi-step tool calling and agentic loops,
which is what acquisition actually is.

**Gemini 2.5 Flash (`google/gemini-2.5-flash`) for extraction** — not DeepSeek.
It is already in your stack via OpenRouter, its structured-output adherence is
materially better, its long context comfortably swallows a 60,000-character
evidence bundle, and adding DeepSeek as a third vendor for the highest-volume
tier violates your own stated principle of keeping the fewest companies
involved for no measurable gain.

Both models drift on JSON under load. The single repair retry in WF-03 step 9
is mandatory, not defensive padding — expect it to fire on 3–8% of calls.

Because `model` is a column on `civ_datapoint_groups`, swapping a model for one
group is a SQL `UPDATE`. Benchmark on the pilot's 20 companies before committing
across all 504.

---

## 12. Work breakdown

| WP | Work package | Depends on | Est. |
|----|--------------|-----------|------|
| WP-1 | Apply schema migration; load the real 182 catalog into `civ_datapoints`; write group definitions and prompts | — | 1.5 d |
| WP-2 | WF-00 Budget Guard & Reaper | WP-1 | 0.5 d |
| WP-3 | WF-01 Gate & Enqueue (litigation disqualifier) | WP-1 | 0.5 d |
| WP-4 | WF-02 Acquire Worker — the 6 agentless sources | WP-1, WP-2 | 1 d |
| WP-5 | WF-08 Agent Runner (4 archetypes) | WP-1 | 1 d |
| WP-6 | WF-02 Acquire Worker — the 5 agentic sources | WP-4, WP-5 | 1.5 d |
| WP-7 | WF-03 Extract Worker + schema validation + repair loop | WP-5, WP-6 | 2 d |
| WP-8 | WF-04 Score & Promote | WP-7 | 0.5 d |
| WP-9 | WF-05 Compose + dossier template + question list | WP-7 | 1.5 d |
| WP-10 | WF-06 Citation Audit, WF-07 Refresh Scheduler | WP-7 | 1 d |
| WP-11 | Hostinger: queue mode, Redis, workers, pruning | — (parallel) | 0.5 d |
| WP-12 | Pilot: 20 companies end to end; Stu reads all 20; tune threshold and prompts | WP-9 | 2 d |
| WP-13 | Full 504 run | WP-12 | 3 d elapsed |

**Build effort: ~13 days.** Critical path runs WP-1 → WP-5 → WP-6 → WP-7 →
WP-9 → WP-12. WP-11 is independent and should start immediately since it is
infrastructure, not code.

### Acceptance gates

- **After WP-3:** run the gate against all 504. The disqualified count should
  land 20–40%. Outside that band, the name-matching is wrong — fix before proceeding.
- **After WP-7:** run one company through all 15 groups. Manually verify 10
  random citations by opening the URL. Fewer than 9 of 10 correct → stop and fix
  prompts.
- **After WP-9:** Stu reads three dossiers cold and states, for each, whether he
  could write an opener from it. Three no's means the composition template is
  wrong, not the collection.
- **After WP-12:** citation audit failure rate under 10% per group, and the fit
  threshold calibrated against Stu's own 20-company yes/no split.

---

## 13. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fabricated datapoints reach a dossier Stu acts on | Medium | **Severe** — destroys trust in all 182 | CHECK constraint + application-level enforcement + nightly citation audit + per-group failure alerting |
| n8n stays in default mode; full pass takes a week | High if WP-11 slips | High | WP-11 starts day 1, independent of code |
| LinkedIn / Apollo ToS exposure from scraping | Medium | Medium | Go through Apollo and Airscale APIs, never direct LinkedIn scraping |
| Firecrawl credit burn from unbounded crawls | Medium | Medium | `limit: 40`, depth 2, hard-coded; `fetch_cap` in budget guard |
| Kimi/Gemini JSON drift under load | High | Low | Schema validation + one repair retry, expected on 3–8% of calls |
| Real catalog does not map cleanly onto 15 groups | High | Low | Grouping is a database table; regroup with SQL, no workflow edit |
| Company-name collisions cause wrong disqualification | Medium | High — you lose a real prospect silently | Gate adjudication step with state + DBA; log every disqualification with reason; review the list manually after WP-3 |
| Stuck jobs silently stall the queue | Medium | Medium | 30-minute reaper in WF-00 |

The name-collision risk deserves particular attention. A false positive at the
gate removes a real prospect from the run and nothing downstream will ever
surface it. Review the disqualified list by hand once, after WP-3.

---

## 14. What changes versus your original five-stage shape

| Your shape | This plan | Why |
|-----------|-----------|-----|
| Trigger → pull companies needing work | WF-01, plus a litigation gate before any spend | Prevention-only ICP makes litigation a disqualifier; it is your cheapest datapoint and removes ~30% of the run |
| Divide datapoints into groups | Two axes: **source** for acquisition, **datapoint group** for extraction | Fetching each page once instead of 13 times; conflicts become detectable rather than invisible |
| Fan out to agents | Job queue table with `FOR UPDATE SKIP LOCKED` | n8n sub-workflows execute in the parent process; in-execution fan-out will exhaust VPS memory |
| Collect results | Schema validation + evidence-or-null enforcement + conflict capture | Without this the dossier cannot be trusted, and an untrusted dossier is worth nothing |
| Store to Supabase, update status | Store, **then compose** | 182 rows is not a dossier; the composition step and the auto-generated discovery-call question list were missing |
| — | Mid-gate scoring after 3 groups | Halves the deep-collection volume |
| — | TTL per datapoint + refresh scheduler | Same architecture serves the initial fill and ongoing monitoring; this is what makes it an Early Warning System rather than a one-time blast |

The core insight you started with — chunk it, never hand one agent 182
datapoints — is correct and is the load-bearing idea in this entire document.
Everything above is plumbing around it.

---

## 15. First three actions

1. **Send me the real 182-datapoint catalog** so WP-1 can map it onto
   `civ_datapoints` with `method`, `ttl_days`, and `source_priority` assigned
   per datapoint. This blocks the critical path and nothing else does.
2. **Rad starts WP-11** (queue mode + Redis + workers on Hostinger) today. It is
   independent of every code decision here.
3. **Confirm the pilot list**: 20 companies spanning all three verticals and the
   full seat range, so WP-12 calibrates against something representative rather
   than 20 solar companies in Arizona.
