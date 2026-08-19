# CiV TCPA Risk Scoring Model v1.0

A 100-point weighted model. Every prospect in `civ-tcpa-prospect-list.csv` carries its six
component scores alongside the total, so any ranking can be challenged and re-derived on a call.

## Weighting rationale

| Factor | Max | Why this weight |
|---|---|---|
| **Litigation & enforcement history** | 30 | The only *observed* rather than inferred signal. A certified class is not a risk estimate — it is a realised loss with a dollar figure. |
| **Lead-sourcing / consent provenance** | 25 | The documented root cause of the largest 2026 events. Purchased leads are inherited liability the buyer cannot document. This is also precisely what CiV fixes. |
| **Outbound volume & dialer posture** | 20 | Statutory damages are **per call**. Volume is the multiplier that turns a process defect into a class action. |
| **Vertical base rate** | 12 | Empirical case-mix: insurance **28%**, debt/collections **22%**, legal services **18%** (WebRecon). |
| **Regulatory surface** | 8 | State mini-TCPAs stack independent statutory damages on the same call. FL/OK/WA/MD carry private rights of action untouched by the federal vacatur. |
| **Compliance maturity gap** | 5 | Inverse capability: no named compliance owner, no consent-capture platform, no revocation workflow. Small weight — it is the *least* verifiable factor from outside. |

## Scoring rubrics

**Litigation & enforcement (0–30)**
| Score | Condition |
|---|---|
| 28–30 | Class **certified**, or 8-figure settlement, within 24 months |
| 22–27 | Active TCPA class action filed within 24 months, or 7-figure settlement |
| 15–21 | Individual TCPA suits, older settlement, or adjacent regulatory action (DOJ/FTC/state AG) |
| 6–14 | Documented complaint pattern, no suit |
| 0–5 | Nothing found |

**Lead sourcing / consent provenance (0–25)**
| Score | Condition |
|---|---|
| 23–25 | Buys aggregated/shared leads from multiple vendors, resells leads, works aged leads, or dials client-supplied lists as an agent |
| 18–22 | Buys leads from a limited vetted set; or distributed agent/franchise/dealer channel buying independently |
| 10–17 | Mixed owned first-party + purchased |
| 0–9 | Predominantly owned first-party consent with retained evidence |

**Outbound volume & dialer posture (0–20)** — scales with estimated seats and dialer
aggressiveness. 18–20: 1,000+ seats and/or confirmed predictive dialer with prerecorded or AI
voice. 12–17: 200–1,000 seats. 5–11: under 200 seats. 0–4: minimal or purely inbound.

**Vertical base rate (0–12)** — Insurance (incl. Medicare/final expense) and debt relief: 12.
Mortgage/personal finance: 12. Solar: 11. HVAC/home services: 10. BPO/other: 9.

**Regulatory surface (0–8)** — 8: nationwide footprint including FL/OK/WA/MD. 6–7: multi-state,
some mini-TCPA. 3–5: single-state, non-mini-TCPA. 0–2: minimal.

**Compliance maturity gap (0–5)** — 5: no evidence of any compliance function. 3–4: some
function, no consent-provenance tooling. 1–2: named compliance leadership and tooling. 0: mature.

## Bands

| Band | Score | Sales meaning |
|---|---|---|
| **1 – CRITICAL** | 80–100 | Active or realised loss. Contact now; remediation budget exists. |
| **2 – HIGH** | 65–79 | Structural exposure plus a trigger. Primary pipeline. |
| **3 – ELEVATED** | 50–64 | Real exposure, no acute event. Nurture until a trigger fires. |
| **4 – MODERATE** | 35–49 | Monitor. |
| **5 – WATCH** | <35 | Not a near-term prospect. |

## Two things the risk score deliberately does *not* measure

**1. `CiV Fit` (A/B/C) is scored separately.** Highest risk ≠ best deal. Liberty Mutual scores 94
but rates **C** — a Fortune 100 carrier has in-house counsel, a procurement process and a
12–18 month cycle. **Mass Markets**, **Leaf Home**, **Beyond Finance** and the PE-backed HVAC
platforms score lower on risk but rate **A**: mid-market, acute exposure, no in-house TCPA bench,
and a single decision-maker. **Work the A-fits first; use the C-fits as reference logos.**

**2. `Solvency / Reputability` is a hard gate, not a score input.** A company in Chapter 11 has
maximum TCPA risk and zero purchase capacity. **Freedom Forever** (Ch. 11, 4/15/2026) and
**Sunnova** (Ch. 11, 6/2025) were both excluded on this basis despite heavy TCPA exposure.
Re-verify solvency immediately before every outreach — the solar vertical in particular is
consolidating fast.

## Known limitations — read before quoting any figure

- **Seat counts are mostly estimates.** Almost no company publishes them. Where a figure is
  disclosed it is marked HIGH (e.g. **Mass Markets: ~2,500 across 8 US centers, with a 500+ seat
  Sioux City facility** — company/press disclosed). Everything else is derived from headcount and
  business model and marked `(est.)` with `LOW` confidence. **Treat these as sizing hypotheses to
  confirm on the call, never as assertions to the prospect.**
- **Private-company revenue is unavailable or third-party estimated.** Aggregator figures
  (Growjo/ZoomInfo-class) are marked as such and can be materially wrong. Public-company revenue
  is from filings and marked HIGH.
- **"Number of clients / client list" only applies to B2B models** — BPOs, lead marketplaces and
  outsourced acquisition firms. For direct-to-consumer brands it is recorded as
  `N/A - direct to consumer`, because they have customers, not clients. **No client list has been
  inferred or invented**; where a roster is not public it says so.
- **Structural risk is inference, not evidence.** Rows whose TCPA evidence begins "Structural:"
  have no found litigation — the score reflects business-model exposure. Do not tell these
  prospects they have been sued.
- **Several small defendants are flagged `UNVERIFIED`.** Confirm the legal entity before contact.
