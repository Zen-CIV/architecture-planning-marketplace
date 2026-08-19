# Finding Lead Buyers: The Consent-Provenance Gap
### How to locate, track, source and cold-outreach companies that buy leads and call them

This answers the question directly: **companies buying leads don't have call-specific consent
of their own — how do we find them?**

---

## 1. Why lead buyers are CiV's best segment

They are the deep pocket, they are provably reachable, and their exposure is *structural* —
it cannot be fixed by trying harder on the dialer.

**The verified proof case.** *Ward v. Liberty Mutual Insurance Co.* — Judge Brian E. Murphy
**certified two TCPA classes on June 12, 2026**, roughly **$30M** in exposure. The mechanism:
Liberty Mutual ran telemarketing on **leads purchased from third-party aggregators**, including
**All Web Leads**. The *buyer* got certified against. The aggregator is a separate defendant in
a separate suit.

**The four legal facts that make this segment structurally exposed:**

1. **Purchased leads are inherited liability.** The buyer must prove *prior express written
   consent* for the call it placed. It is proving something a stranger captured, on a webform it
   never saw, under disclosure language it did not write.
2. **Vicarious liability runs to the beneficiary.** Under actual authority, apparent authority
   and ratification, the entity that *benefits* from the call is liable for it — even though the
   lead gen or an outsourced dialer physically placed it. Plaintiff-side counsel say so openly:
   *"the entity placing the call is often not the entity benefiting from it."*
3. **TrustedForm/Jornaya certificates are not a defense — they are evidence.** A certificate
   documents *what happened on the form*; it does not establish that the form met TCPA
   requirements. **"If the disclosure language was deficient or consent was a condition of
   purchase, the certificate documents your liability."** Most buyers believe the opposite. That
   gap between belief and reality is the entire sales conversation.
4. **The one-to-one vacatur made this worse, not better.** *IMC v. FCC* (11th Cir., 1/24/2025)
   restored the old standard: one consent *can* cover multiple sellers — **but only if the
   disclosure clearly identifies who may contact them.** So the question shifts from "did you
   follow the FCC rule" to "was your name legible in that disclosure, and can you produce it?"
   Nobody rebuilt their evidence chain to answer that. Meanwhile **state mini-TCPAs (FL, OK, WA,
   MD) were never affected at all.**

**The one-sentence pitch:** *"You bought the lead, so you inherited the consent — but you never
received the evidence. In discovery, the certificate you're relying on becomes the exhibit
against you. Liberty Mutual just got two classes certified on exactly this."*

---

## 2. How to find them — seven enumeration methods, ranked by yield

### Method 1 — Harvest "marketing partners" pages *(highest yield, fully automatable)*

Every comparison-shopping site, quote form and lead-gen landing page carries a TCPA consent
checkbox. That checkbox links to a **"marketing partners" / "participating companies" /
"our partners"** page that **names every company permitted to call the consumer**.

Historically these lists ran to hundreds or thousands of names behind a small hyperlink. The
FCC tried to kill them with one-to-one consent; the 11th Circuit vacated it; **the lists are
lawful again and are back in use.**

**That page is a published, self-maintained, dated list of confirmed lead buyers.** The seller
keeps it accurate for their own legal protection. You get:

- company name (exactly as it must legally appear)
- often a linked domain, sometimes DBA/entity name
- proof they are calling on purchased leads
- **a change history**, once you diff it over time

**Where to harvest:** insurance (EverQuote, MediaAlpha, SmartFinancial, QuoteWizard, All Web
Leads, Datalot/Centerfield), home services/solar (Modernize, Networx, Angi, HomeAdvisor),
personal finance (debt-relief and refi quote funnels, credit-trigger buyers).

**Operational detail:** the consent text is usually in a `<label>` next to the submit button;
the partner list is behind an `<a>` whose text matches `/partner|participating|companies|list/i`,
frequently opening a modal or a `/partners` path. A working harvester is in
`tools/partner_page_harvest.py`.

> **The diff is the trigger.** A company that appears on a partner list *this week but not last
> week* just started buying leads in that vertical. That is a brand-new, undefended exposure and
> a perfect cold-outreach reason: *"I noticed you were added to [Seller]'s partner list on [date]."*

### Method 2 — Litigation co-defendant graph *(highest confidence)*

When a lead generator is sued, the complaint names the buyers — because plaintiffs go where the
money is. Pull the complaint from **RECAP/CourtListener** (free) and read the defendant caption
and the "Agency" allegations.

This gives you a **verified** lead-buyer relationship, court-documented. Then invert it: for any
lead seller in litigation, every named buyer is a prospect, and every *unnamed* buyer on that
seller's partner page is a prospect who has not been sued **yet** — which is a better call.

### Method 3 — Ping-post & lead-distribution platform footprints

Lead buyers connect to sellers through distribution software: **boberdoo, LeadsPedia, Phonexa,
Ringba, Retreaver, ActiveProspect**. Their public **customer pages, integration directories and
case studies** name both sides of the market. ActiveProspect's integration announcements (e.g.
with Convoso) name the dialers buyers use.

### Method 4 — Consent-platform script detection *(technographic)*

Scan target domains for **TrustedForm** (`api.trustedform.com`, `cert.trustedform.com`) or
**Jornaya/Verisk LeadiD** (`create.lidstatic.com`, `leadid.com`) scripts.

- Script on a **form page** → they are *capturing* leads (seller/originator).
- Company named in **partner lists** but no capture script → they are *buying* (pure buyer). **These are the best prospects.**

Detect with BuiltWith, Wappalyzer, or a plain `requests` + regex sweep.

### Method 5 — Hiring signals specific to lead buying

Search Indeed/LinkedIn for these exact phrases — they are written by the buyer about themselves:

`"manage lead vendors"` · `"lead acquisition manager"` · `"media buyer" + leads` · `"ping post"` ·
`"aged leads"` · `"lead quality analyst"` · `"vendor scorecard"` · `"cost per acquisition" + dialer`

**`"aged leads"` is the highest-risk phrase in the industry.** Aged leads are resold months or
years after capture; consent is stale, the consumer has forgotten, and DNC status has changed.
A company advertising that it works aged leads is telling you its consent is indefensible.

### Method 6 — Reverse the call

Consumers name the caller publicly. Search **800notes.com**, **callercenter.com**,
**robokiller lookup**, Reddit (r/scams, vertical subs) and BBB complaint text for
`"called me about [Medicare|solar|debt|my roof]"`. Complaint text frequently names the business
that answered — which is the *buyer*, not the lead gen, because the buyer is who identified
themselves on the call.

### Method 7 — Affiliate networks and offer walls

Lead buyers run offers on affiliate networks (Everflow, Cake, HasOffers/Branch, offervault-style
directories). Public offer listings name the advertiser, the vertical, and the payout — which
also tells you their volume economics.

---

## 3. Tracking: the source-of-truth schema

Cold outreach on unsourced data burns the domain and the brand. Every row must carry provenance
so any claim survives a "how do you know that?" on the call.

| Field | Purpose |
|---|---|
| `company_name` | As published on the partner list (legal name matters) |
| `domain` | **Dedupe key** — names vary, domains don't |
| `discovery_channel` | Which of the 7 methods found them |
| `evidence_url` | The exact page proving it |
| `evidence_snapshot_path` | Local copy — **partner pages change without notice** |
| `first_seen` / `last_seen` | Powers the diff trigger |
| `seller_source` | Which lead seller's list they appeared on |
| `also_seen_on` | Multiple sellers = higher volume + more consent-language variance |
| `capture_script_detected` | TrustedForm / Jornaya / none → buyer vs originator |
| `litigation_status` | From RECAP; the strongest trigger |
| `state_registrations` | FL/TX/etc. registry hits — confirms funded outbound |
| `risk_score` | From `02-risk-model.md` |
| `solvency_checked_on` | Mandatory before outreach (see the Freedom Forever/Sunnova lesson) |

**Rules that keep it clean:**
1. **Dedupe on registered domain**, not company name.
2. **Snapshot every page** at discovery — the evidence disappears when they edit the list.
3. **Re-crawl weekly, diff, and alert on additions** — the diff is the trigger, not the list.
4. **Never assert a number you cannot source.** Mark estimates as estimates. A fabricated seat
   count that a prospect corrects on the call costs you the meeting and the credibility.
5. **Re-verify solvency immediately before outreach.**

---

## 4. Turning it into cold outreach

**Sequencing by trigger strength:**

| Trigger | Window | Open with |
|---|---|---|
| Class certified / prelim. settlement approval | **30–120 days after** | The case, by name |
| Newly added to a partner list | Within 2 weeks of the diff | "I noticed you were added to [Seller]'s partner list" |
| Hiring a TCPA/compliance role | While the req is open | The job posting — they've admitted it and funded it |
| New state registration filed | Within 30 days | Their expansion into an FTSA/OTSA state |
| PE acquisition closed | 60–180 days after | Diligence and escrow exposure, to the CFO/GC |

**Entry points, by company type:** GC or Chief Compliance Officer (litigation trigger) · CFO or GC
(PE-owned) · CRO or Head of Sales Ops (BPO/marketplace, where compliance is a *revenue* argument) ·
Owner/CEO (under ~200 employees).

**Message construction — four sentences:**
1. **Specific evidence about them** (case name, partner-list date, job posting). Never generic.
2. **The mechanism**, in one line: *purchased leads = inherited liability you can't document.*
3. **The proof case**: Ward v. Liberty Mutual, two classes certified 6/12/2026.
4. **A narrow ask**: a consent-provenance audit of one vendor's lead file — not a demo.

**Two arguments that consistently outperform:**

- **"You can't insure this."** TCPA has no dedicated insurance market; where coverage exists it is
  typically defense-costs-only, ≤$1M, with a high self-insured retention. Most executives assume
  E&O covers it. It does not. Risk that cannot be transferred must be engineered out.
- **"The vacatur didn't save you."** They believe *IMC v. FCC* solved this. It restored a standard
  that still requires the disclosure to **clearly identify who may contact the consumer** — and it
  did nothing to state mini-TCPAs. Filings rose **34.3%** *after* the rule died. That single
  statistic reframes the entire call.

**What not to do:** don't cold-call a prospect about TCPA compliance using a purchased list and an
autodialer. Use email and LinkedIn, on first-party research, with the evidence URL in hand.
