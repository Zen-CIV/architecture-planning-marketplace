# CiV Prospect Sourcing Playbook
### How to find US companies running outbound calling programs with real TCPA exposure

**Core principle:** never prospect on "companies that might call people." Prospect on
**public records that prove two things at once** — (a) this company places outbound calls,
and (b) something about how it places them is already generating legal friction.

Every channel below produces *evidence with a URL*, so the list is defensible on a discovery
call and re-runnable next quarter.

---

## Why now — the 2026 market conditions

| Fact | Source | Why it sells |
|---|---|---|
| TCPA filings **up 34.3% YTD** through June 2026 vs 2025 | WebRecon | The risk is compounding, not stable |
| April 2026: **330 TCPA cases, 255 class actions** in one month (+40% YoY) | TCPAWorld | Class actions are ~76% of filings — this is a bet-the-company risk |
| Feb 2026: **211 class actions**, a record month | TCPAWorld | Trend line is still climbing |
| Insurance = **28%** of TCPA cases; debt/collections **22%**; legal services **18%** | WebRecon | Confirms CiV's chosen verticals are the right ones |
| Statutory damages **$500–$1,500 per call**, no cap | TCPA | 10,000 bad calls = $5M–$15M |
| **TCPA liability is effectively uninsurable** — no dedicated market; when available, typically **defense-costs-only, ≤$1M, high self-insured retention** | CRC Group, Munich Re | **The single best talk track.** You cannot transfer this risk. You can only engineer it out. |
| One-to-one consent rule **vacated** (*Insurance Marketing Coalition v. FCC*, 11th Cir. 1/24/2025), FCC repealed it 9/2025 | 11th Cir. / FCC | Buyers *think* they got relief. They did not — see §1. |
| **30 states require telemarketer registration; 17 require a surety bond** | State registries | 30 public databases of confirmed outbound callers |

> **The wedge:** the industry read the vacatur as "we're fine now." The vacatur removed a
> *federal rule*. It did not remove the consent requirement, it did not touch **state
> mini-TCPAs** (FL, OK, WA, MD and 10+ more), and it did nothing about **vicarious liability**
> for purchased leads. Companies relaxed exactly when filings rose 34%.

---

## Channel 1 — The Lead-Buyer Graph *(highest yield; see `03-lead-buyer-discovery.md`)*

Companies that **buy** leads and call them are CiV's best segment, because the buyer is the
deep pocket and the buyer cannot prove consent it never captured.

**This is not theory — it is the single largest verified event in this list.** In
*Ward v. Liberty Mutual* the court **certified two TCPA classes on 6/12/2026** (~$30M exposure)
against the **buyer**, over leads purchased from **All Web Leads**.

The enumeration mechanism: because one-to-one consent is dead, lead sellers are once again
publishing **"marketing partners" / "participating companies" pages** that name every buyer
who may call you. **That page is a published prospect list of confirmed lead buyers**, kept
current by the seller for their own legal protection. Harvest and diff it. Full method in
`03-lead-buyer-discovery.md`, with a working scraper in `tools/`.

---

## Channel 2 — Litigation dockets (proof of active pain)

The strongest buying signal in existence: someone is already suing them.

- **PACER / RECAP (CourtListener)** — free, full-text federal dockets. Query `nature of suit 470`
  (Telephone Consumer Protection Act) filtered to the last 90 days. **Set a RECAP alert** so new
  defendants arrive automatically.
- **WebRecon** — monthly named-defendant lists and volume stats (subscription).
- **TCPAWorld** (Troutman/Eric Troutman) — free, fast, names defendants and explains the theory.
- **ClassAction.org / TopClassActions / ClaimDepot** — settlement announcements with amounts.
- **State courts** — FTSA cases in FL state court and OTSA in OK are *not* in PACER. Check FL
  clerk portals (Hillsborough, Broward, Miami-Dade, Pinellas) directly.

**Timing rule:** the best moment to call is **30–120 days after a class certification or
preliminary settlement approval** — remediation budget exists, counsel has told them to fix
the root cause, and the fix is not yet chosen.

## Channel 3 — State telemarketer registration databases (proof of outbound)

**30 states require registration; 17 require a bond.** These are public, searchable, and
downloadable. A company that posted a **$25,000–$50,000 surety bond** to make phone calls is
not a maybe — it is a confirmed, funded outbound program.

Highest-value registries:
- **Florida (FDACS)** — Commercial Telephone Seller licence, searchable business database.
  Florida is also an FTSA private-right-of-action state, so an FL registrant is both *confirmed
  outbound* and *maximum exposure*. Start here.
- **Texas, Pennsylvania ($25K bond), New York ($25K bond), Arkansas ($50K bond), Oklahoma,
  Arizona, California, Utah, Kentucky, Maine, Ohio, Delaware.**

Cross-reference registrants against your target SIC/NAICS codes to filter to insurance,
finance, solar and home services.

## Channel 4 — Complaint data (proof of consumer friction)

- **FTC National DNC Registry Data Book** (FY2025: **2.6M+ DNC complaints**, 258M+ registrations)
  — published annually with **downloadable CSVs** at ftc.gov/data. Complaint topic and type
  (robocall vs live caller) let you rank *categories*, and state-level breakdowns let you rank geography.
- **FCC Consumer Complaint Data** — data.fcc.gov, unwanted-call complaints, often with the
  offending number.
- **Reverse-lookup complaint boards** — 800notes.com, callercenter.com, robokiller lookup. Consumers
  routinely *name the business* in complaint text. Search your target's brand name to gauge volume.
- **BBB complaint patterns** — filter by "Advertising/Sales" issues mentioning calls.
- **YouMail Robocall Index** — monthly volume by campaign category.

## Channel 5 — Dialer & martech footprint (proof of capability)

A predictive dialer is a capital commitment to outbound. Find who owns one:

- **Vendor customer stories and logo pages** — Convoso, Five9, Genesys, NICE, Talkdesk, LiveVox,
  Vici, Ytel, CallTools, Regal.io. **Convoso is the single highest-signal vendor for CiV** — it
  explicitly markets to insurance, final expense, Medicare, solar, financial services and home
  services. Confirmed Convoso references already found: **EverQuote**, **Long Home Products**,
  **Dynamic Insurance Services**.
- **Consent-capture platforms** — sites running **ActiveProspect TrustedForm** or **Jornaya/Verisk
  LeadiD** scripts are, by definition, in the paid-lead ecosystem. Detect via page source or
  BuiltWith/Wappalyzer.
- **Call-tracking & routing** — Retreaver, Phonexa, Ringba, boberdoo, LeadsPedia. Their public
  customer lists and integration directories name active lead buyers and sellers.

## Channel 6 — Hiring signals (proof of scale and of the gap)

Job postings are free, dated, and describe the operation in the company's own words.

- **Seat-count proxy:** count concurrent openings for `Outbound Sales Representative`,
  `Appointment Setter`, `Licensed Insurance Agent`, `Inside Sales`. Sustained volume ≈ floor size.
- **Dialer proof:** postings naming `Convoso`, `Five9`, `Genesys`, `predictive dialer`, `power dialer`.
- **Lead-buying proof:** `manage lead vendors`, `media buyer`, `lead acquisition`, `ping post`.
- **The gap signal — highest value:** a company posting `TCPA Compliance Manager`,
  `Telemarketing Compliance`, `Director of Compliance` **has admitted the problem and funded a
  headcount.** That is a live buying cycle. Set alerts on Indeed/LinkedIn for these titles.

## Channel 7 — Ownership & capital events (proof of budget and mandate)

- **PE-backed roll-ups** are structurally the best fit. Every tuck-in acquisition imports a
  customer list *and its undiligenced consent history*. HVAC is the clearest case: **~800 HVAC/
  plumbing/electrical companies acquired by PE since 2022**; platforms include **Apex Service
  Partners** (Alpine), **Wrench Group** (Leonard Green), **Sila** (Goldman), **ARS/Rescue Rooter**
  (GI Partners), **TurnPoint** (OMERS), **Service Experts** (Brookfield).
- **Why it converts:** institutional owners price contingent statutory-damages liability at exit.
  Unprovable consent becomes an **escrow holdback**. Sell to the CFO/GC as enterprise value, not compliance.
- Track via PitchBook, Axial, and the public PE roll-up trackers (ctacquisitions, DealSeam).

## Channel 8 — Trade associations & events (concentrated target lists)

- **PACE** (Professional Association for Customer Engagement) — member directory is a
  self-identified list of outbound callers.
- **LeadsCon** — attendee/sponsor lists are the lead-buying economy in one room.
- **ALMIA** (Alliance of Licensed Medicare Insurance Agencies) — members include **GoHealth,
  SelectQuote, eHealth, TRANZACT, HealthPlanOne, Spring Venture Group**. Forming a
  self-regulatory body is an admission of known exposure.
- **ACA International** (collections), **AFSA** (consumer finance).

## Channel 9 — Regulatory & enforcement feeds

- **FCC Enforcement Bureau** — citations, NALs, and robocall-related consent decrees.
- **State AG press releases** — FL, TX, MO, WA are the most active on telemarketing.
- **FTC enforcement** — *use this as an exclusion filter as much as a source*: an FTC fraud action
  means **not a reputable prospect**.
- **CMS marketing complaint data** — Medicare Advantage agent marketing complaints.

---

## Disqualification filters (the "reputable businesses" test)

CiV sells to companies it can help, not to companies that should not be calling at all. Screen out:

1. **Insolvent.** Verify before every outreach. Already screened out of this list:
   **Freedom Forever** (Ch. 11, 4/15/2026, ~$500M debts) and **Sunnova** (Ch. 11, 6/2025) — both had
   TCPA exposure, neither can buy. Solar is consolidating hard; check status before every call.
2. **FTC/AG fraud defendants.** A deception case (not a consent case) means the business model is
   the problem. Check the FTC's banned-debt-relief list and AG actions.
3. **Unverifiable entities.** Several small defendants in this list are flagged
   `UNVERIFIED - diligence required`. Confirm the legal entity, address and officers before contact.
4. **Pure offshore boiler rooms.** No US nexus, no assets, no purchase intent.

**Keep:** a real business with real customers, real revenue, and a *process* problem. A TCPA
class action against an otherwise legitimate company is the ideal signal — it means they have
something to protect and a board asking what happened.

---

## Operating cadence

| Cadence | Action |
|---|---|
| **Daily** | RECAP/CourtListener alert on new NOS-470 filings; triage new defendants into the sheet |
| **Weekly** | Re-crawl partner/marketing-partner pages; diff for newly added lead buyers (§Channel 1) |
| **Weekly** | Job-posting alerts for `TCPA Compliance` / `dialer` titles |
| **Monthly** | WebRecon + TCPAWorld stat posts; refresh vertical base rates |
| **Quarterly** | Re-pull state registration databases; refresh FTC DNC data; re-score the whole list |
| **Annually** | FTC DNC Data Book release (~Dec) — refresh complaint-topic weightings |
