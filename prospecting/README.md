# CiV TCPA Prospecting Kit
**Built:** August 2026 · **Scope:** US-based outbound calling programs with demonstrable TCPA exposure

## Deliverables

| File | What it is |
|---|---|
| **[Google Sheet — CiV Prospect List](https://docs.google.com/spreadsheets/d/1oZPIL7WJpC6uPySdtQf4RaRbpepQ64kBwEqQ5xvj3jY/edit)** | 48 companies × 32 data points, ranked by TCPA risk |
| `civ-tcpa-prospect-list.csv` | Same data, version-controlled source of truth |
| `01-sourcing-playbook.md` | 9 repeatable public-data channels for finding outbound callers |
| `02-risk-model.md` | The 100-point scoring model, rubrics, and stated limitations |
| `03-lead-buyer-discovery.md` | How to find companies that **buy leads** and call them — 7 enumeration methods |
| `tools/partner_page_harvest.py` | Working scraper: discover → harvest → diff lead-buyer "marketing partners" pages |
| `build_list.py` | Regenerates the CSV; edit here, not in the CSV |

## The list at a glance

48 companies · **12 CRITICAL** (80–100) · **31 HIGH** (65–79) · **5 ELEVATED** (50–64)

By vertical: Insurance 17 · HVAC/Home Services 12 · Personal Finance 9 · Solar 6 · BPO 4

**Top 5 by risk:** Liberty Mutual (94) · Momentum Solar (90) · All Web Leads (89) ·
AmeriSave Mortgage (86) · American Income Life & Farmers Insurance (84)

**Best *fit* (A-rated, work these first):** Mass Markets (MCI) · Leaf Home · Beyond Finance ·
Trinity Solar · Spring Venture Group · Apex Service Partners · EverQuote · MediaAlpha ·
Power Home Remodeling · LoanStream Mortgage

> Risk rank ≠ call order. Liberty Mutual is the highest-risk name and a **C** fit — Fortune 100,
> in-house counsel, 12–18 month cycle. Sort by `CiV Fit = A`, then by risk. See `02-risk-model.md`.

## Deliberately excluded

| Company | Why |
|---|---|
| **Freedom Forever** | Chapter 11, 4/15/2026, ~$500M debts — had TCPA suits, cannot buy |
| **Sunnova** | Chapter 11, 6/2025; laid off 55% of staff |
| FTC/AG fraud defendants | Business model is the problem, not the process — fails the "reputable" test |

Solar is consolidating hard. **Re-verify solvency immediately before every outreach.**

## Data integrity — read this before quoting any number

Every numeric cell carries a basis and confidence label. Nothing was invented.

- **Seat counts are estimates** except where disclosed. Only **Mass Markets** has a sourced figure
  (~2,500 across 8 US centers; 500+ seat Sioux City facility). Everything else is derived from
  headcount and business model, marked `(est.)` / `LOW`. **Use these as sizing hypotheses to confirm
  on the call, never as claims to the prospect.**
- **Private-company revenue** is unavailable or third-party estimated (Growjo/ZoomInfo-class) and
  labelled as such. Public-company revenue comes from filings and is labelled HIGH.
- **"# of Clients" / "Client List"** apply only to B2B models (BPOs, lead marketplaces, outsourced
  acquisition). Direct-to-consumer brands show `N/A - direct to consumer` — they have customers, not
  clients. **No client roster was inferred.** Where it isn't public, the cell says so.
- Rows whose TCPA evidence begins **"Structural:"** have **no found litigation**. The score reflects
  business-model exposure. Never tell these prospects they have been sued.
- Rows flagged **UNVERIFIED** (US Solar Connect, EMPWR Solar, InsureMe, GetMeHealthCare) need entity
  confirmation before contact.

## Refresh

`python3 build_list.py` regenerates the CSV. Re-upload to Drive to update the Sheet.
Cadence and alerting are in `01-sourcing-playbook.md` (daily docket alerts → quarterly full re-score).
