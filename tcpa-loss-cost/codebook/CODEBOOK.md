# CiV TCPA Complaint Codebook — v0.1 (draft)

Instrument 1 of the CiV TCPA Loss Cost Report · Status: **draft for owner review** · 2026-10-06

The human coders and the LLM (large language model) classifier use this same text, and there are no private rules.
If a rule exists only in a coder's head, the classifier doesn't have it, and the agreement score will show the gap.

- **Sections 1–9** are the coding rules. They go to the LLM verbatim as its instructions.
- **Sections 10–13** are governance: how agreement is measured, how the codebook changes, and decisions still open.

Companion files in this folder:

- `complaint_coding.schema.json`: the output contract. It covers one record per docket, from a human or an LLM.
- `hand_coding_sheet.csv`: column headers for the hand-coded gold set, in the same field order.
- `examples/fictional_record.json`: a fictional record that shows the format and validates against the schema.

---

## 1. Unit, source document, reading order

- **Unit:** one docket. Code the earliest complaint on the docket. That means the original complaint, or the state-court complaint attached to a notice of removal. If only an amended complaint is available, code it and set A1 = `amended`.
- **Multiple plaintiffs:** code the first-named plaintiff wherever a field asks about "the plaintiff" (D2, D3, F5).
- **Reading order (humans):** read these parts, in this order:
  1. Caption (page 1).
  2. "Parties."
  3. "Factual Allegations."
  4. "Class Allegations."
  5. Each "Count" or "Cause of Action."
  6. Signature block.
- **Time box (humans):** 12 minutes per complaint. If a field can't be decided in that time, mark it `unclear` and move on. An `unclear` is input for the next codebook version, not a failure.
- **Rule B0 applies to everyone:** a statute quoted in the "Background" or "The TCPA" section is **not** pleaded. Complaints routinely quote the whole statute. Code only what a count invokes.

## 2. What you code here, and what you don't

| Coded from the complaint (this codebook) | Computed elsewhere, **do not code** |
|---|---|
| Whether there is a TCPA or state telemarketing count (Part A) | Court, district, circuit, filing date, nature-of-suit code, removed vs. original (from the FJC Integrated Database) |
| The legal hooks pleaded (Part B) | Outcome and termination date (Instrument 2, §11) |
| Fact flags: revocation, AI voice, lead generation, third-party caller, wrong number, prior relationship (Part C) | Settlement amounts (Instrument 2, §11) |
| Channels, contacts alleged, contact dates (Part D) | Serial-plaintiff and repeat-defendant flags (counts across the whole dataset) |
| Class allegations (Part E) | Each defendant's 6-digit NAICS code and employee band (entity resolution) |
| Defendants and their roles, industry group, plaintiff state, pro se status, plaintiff counsel (Part F) | Forum exposure (circuit plus state-statute exposure) |

## 3. Part A: Screen

| ID | Field | Values |
|---|---|---|
| A1 | `a1_document_type` | `original` · `amended` · `removed_state_complaint` · `not_a_complaint` (stop here) |
| A2 | `a2_statute_scope` | `federal_tcpa`: at least one count under 47 U.S.C. §227 · `state_only`: counts only under a state telemarketing or telephone-solicitation statute · `out_of_scope`: neither, so fill in A3–A4 and stop |
| A3 | `a3_total_counts`, `a3_telemarketing_counts` | Integers. Telemarketing counts are those under §227 or a state telemarketing statute. |
| A4 | `a4_companion_claims` | Multi-select: `fdcpa` · `fcra` · `state_udap` · `privacy_tort` · `contract` · `other`. Leave it empty if there are none. |

The screen exists because our existing `court_cases` table is not a clean TCPA set:

- 1,201 of its 6,194 dockets (19%) carry non-TCPA nature-of-suit codes, such as 110 Insurance, 190 Contract and 445 ADA–Employment.
- Some of those dockets do contain TCPA counts. Debt cases filed as 480 Consumer Credit often do. Many contain none.

The screen decides which dockets count, and the out-of-scope rate is published.

## 4. Part B: Claim types (the legal hook)

**Rule B0.** Code the provision that a **count** invokes. Use the factual allegations only to work out which provision a vaguely headed count relies on. Claim types are multi-select, and most complaints have one to three. Claim types are recorded per complaint, not per defendant.

| ID | Code | Present when a count alleges… | Typical citation |
|---|---|---|---|
| B1 | `ATDS` | Calls or texts to a cell number using an automatic telephone dialing system | §227(b)(1)(A)(iii) |
| B2 | `ARTIFICIAL_PRERECORDED` | Calls using an artificial or prerecorded voice, to a cell number or a residential line. This includes ringless voicemail and AI-generated voices. | §227(b)(1)(A)(iii); §227(b)(1)(B) |
| B3 | `NATIONAL_DNC` | Two or more telephone solicitations within 12 months to a number on the National Do Not Call Registry | §227(c)(5); 47 C.F.R. §64.1200(c)(2) |
| B4 | `INTERNAL_DNC` | Failure to keep or follow company do-not-call procedures: no written policy, no training, a stop request not recorded or honored, or the caller not identified | §227(c)(5); 47 C.F.R. §64.1200(d) |
| B5 | `CALLING_HOURS` | Telephone solicitations before 8 a.m. or after 9 p.m. at the called party's location | 47 C.F.R. §64.1200(c)(1) |
| B6 | `JUNK_FAX` | Unsolicited advertisements sent by fax, including a missing or deficient opt-out notice on such a fax | §227(b)(1)(C) |
| B7 | `STATE_STATUTE` | A count under a state telemarketing or telephone-solicitation statute. Record each one as {state, citation as written}. | See the list below |
| B8 | `OTHER_FEDERAL` | Any other TCPA count, such as caller-ID transmission (§64.1601(e)) or abandoned-call rules (§64.1200(a)(7)). Record the citation as written. | — |

### Decision rules (binding; these are the cases where coders disagree)

- **R1. A §227(b) count that alleges both a dialer and a voice.** Code B1 and B2 only if the facts allege each one.
  - A "dead air" pause, a "click" before a live person, or dialing "en masse" supports B1.
  - A "prerecorded message," an "artificial voice," or a voice message left without a live caller supports B2.
- **R2. Texts.** A text under §227(b) is B1, never B2. Ringless voicemail is B2.
- **R3. §227(c) counts.** Read the regulation the count cites.
  - §64.1200(c)(2), or "National Do Not Call Registry": code B3.
  - §64.1200(d), "internal do-not-call," "no written policy," or "failed to honor my request": code B4.
  - Both are cited: code both.
  - Only "§227(c)" is cited, with no regulation: code B3 if the plaintiff alleges National Registry registration. Code B4 if the only allegation is that a stop request was ignored.
- **R4. "Quiet hours" texts.** Messages sent before 8 a.m. or after 9 p.m. are B5, with channel `text`.
- **R5. One set of contacts, several defendants.** This is one claim type, not one per defendant. Roles go in F1.
- **R6. Revocation is a fact, not a claim type.** A "revocation case" is usually B1 or B2 (calls continued after consent was withdrawn) or B4 (a stop request was not honored). Code that hook in Part B and set C1.
- **R7. State statutes.** Code each distinct state statute once.
  - A general consumer-protection act (UDAP) goes in A4.
  - Exception: a telemarketing statute that is enforced *through* a UDAP is still B7, recorded under the telemarketing citation. Texas chapter 302 enforced through the DTPA is an example.
  - A Washington CEMA count belongs in B7 only if it concerns texts. Email-only suits are `out_of_scope`.
- **R8. A §227 count you can't place under R1–R3.** Code it as B8, with the citation as written and a one-line note.

### State statutes you will see (recognize them; no need to memorize)

| State | Statute |
|---|---|
| FL | Fla. Stat. §501.059 (Florida Telephone Solicitation Act) |
| OK | 15 Okla. Stat. §775C.1 et seq. (Oklahoma Telephone Solicitation Act) |
| MD | Md. Code, Com. Law §14-4501 et seq. (Stop the Spam Calls Act); §14-3201 et seq. (Maryland Telephone Consumer Protection Act) |
| TX | Tex. Bus. & Com. Code ch. 302 (extended to texts from Sept. 1, 2025) and §305.053 |
| VA | Va. Code §59.1-510 et seq. (Virginia Telephone Privacy Protection Act) |
| WA | RCW 80.36.390; RCW 19.190 (CEMA), texts only |

### How the earlier eight categories map to this scheme

| Earlier category | In this codebook |
|---|---|
| Autodialer | B1 |
| Prerecorded / AI voice | B2, plus C2 for AI |
| National DNC | B3 |
| Internal DNC | B4 |
| Revocation | C1 flag, alongside B1, B2 or B4 |
| Texts | D1 channel = `text`, with any B |
| Calling hours | B5 |
| State statute | B7 |
| *(missing before)* | B6 junk fax, B8 other federal |

**Why the categories changed.** The earlier list mixed three different questions:

- legal hooks, such as DNC;
- a channel (texts);
- a fact (revocation).

Coders would split, for example, on whether a DNC text case counts as "texts" or "national DNC." Asking three independent questions is what makes a Cohen's kappa (κ) of 0.80 reachable. Every earlier category can still be reported as a combination.

## 5. Part C: Fact flags

Each flag has a value of `yes` · `no` · `unclear`, plus evidence (see §9).

- Code what the complaint **alleges**, not what you believe happened.
- If the complaint is silent, the value is `no`, except for C6.

| ID | Field | `yes` when the complaint alleges… |
|---|---|---|
| C1 | `c1_revocation_alleged` | The plaintiff told the defendant to stop (on a call, by replying STOP, by email, or any other way) **and** contacts continued afterwards. Both halves are required. |
| C2 | `c2_ai_voice_alleged` | The voice was AI-generated, synthetic, cloned, a "virtual agent," an "avatar," or "artificial intelligence." "Robotic-sounding" or "prerecorded" alone is `no`. |
| C3 | `c3_lead_gen_alleged` | The number or the "consent" came from a third-party website, lead generator, comparison or quote site, sweepstakes, or purchased list. Also `yes` if a lead generator is named as a defendant. |
| C4 | `c4_third_party_caller_alleged` | Someone other than the seller made the contacts on the seller's behalf: a vendor, call center, affiliate or "agent." This is the vicarious-liability pattern. |
| C5 | `c5_wrong_number_alleged` | The contacts were meant for someone else, through a reassigned number, a wrong number, or a debtor who is not the plaintiff. |
| C6 | `c6_prior_relationship` | Values: `customer_or_inquiry` · `no_relationship_alleged` · `not_stated`. The first applies when the plaintiff was a customer of the defendant, or applied or inquired with it. The second applies when the complaint says there was no relationship ("never did business with Defendant"). The third applies when the complaint is silent. |

## 6. Part D: Channel and contacts

| ID | Field | Rule |
|---|---|---|
| D1 | `d1_channels` | Multi-select: `voice` (live or prerecorded calls) · `text` (SMS, MMS or RCS) · `ringless_voicemail` · `fax` · `unspecified` |
| D2 | `d2_contacts_to_plaintiff` | An integer, as alleged. "At least 7 calls" is 7. If there is a call-log table, count its rows. "Numerous," "multiple" or "repeated" means blank. Add across channels only when the complaint gives each number. |
| D3 | `d3_first_contact`, `d3_last_contact` | As alleged, in the form `YYYY-MM-DD` or `YYYY-MM`. Blank if not stated. |

## 7. Part E: Class allegations

| ID | Field | Rule |
|---|---|---|
| E1 | `e1_is_class_action` | `true` if the complaint proposes a class definition (Rule 23 or a state equivalent) |
| E2 | `e2_class_count` | The number of classes plus subclasses defined. Blank if E1 is false. |
| E3 | `e3_class_size_numeric` | Only a number the complaint writes: "over 10,000 persons" is 10000. Words such as "thousands" mean blank. |
| E4 | `e4_class_size_text` | The size phrase, verbatim, in 15 words or fewer |
| E5 | `e5_class_lookback_years` | The lookback in the class definition. "Four years prior to the filing of this Complaint" is 4. |

## 8. Part F: Parties and industry

| ID | Field | Rule |
|---|---|---|
| F1 | `f1_defendants` | One entry per named defendant, with the name exactly as in the caption. Skip "Does 1–10." For each, give a role (see the list below the table). |
| F3 | `f3_industry_group` | One per complaint, for the **seller** (the business whose product the contacts promoted), using the table below. If no seller is named, code the industry of the product promoted. A creditor collecting its own debt gets its own industry. A collection agency is `debt_collection`. |
| F4 | `f4_product_promoted` | Six words or fewer, as the complaint describes it ("Medicare Advantage plans," "auto warranty"). |
| F5 | `f5_plaintiff_state` | The two-letter state of residence alleged for the first-named plaintiff. |
| F6 | `f6_pro_se` | `true` if the plaintiff signs without a lawyer. |
| F7 | `f7_plaintiff_counsel` | Firm names exactly as in the signature block. Leave it empty if the plaintiff is pro se. |

Roles for F1:

- `seller`: the business whose product the contacts promoted, or the creditor for a collection call.
- `caller_vendor`: placed the contacts for someone else. If a defendant both generated the lead and placed the contacts, use this role. C3 already records the lead generation.
- `lead_generator`: sold or generated the lead, or the "consent."
- `platform`: a carrier or software provider sued for enabling the contacts.
- `individual`: a natural person.
- `unclear`.

### Industry groups (F3)

The NAICS anchor is only the starting point for joining to Census counts. Entity resolution assigns the final 6-digit code later.

| Code | Covers | NAICS anchor |
|---|---|---|
| `insurance` | Health, Medicare, life, final expense, auto, home | 524 |
| `warranty` | Vehicle and home warranties, service contracts | 524 (approximate) |
| `lending_credit` | Mortgage, personal, auto and business loans; cards; debt relief | 522 |
| `debt_collection` | Collection agencies (third party) | 561440 |
| `real_estate` | Agents, brokers, "we buy houses" investors, property management | 531 |
| `solar_energy` | Solar installers, retail energy suppliers, utilities | 238210, 2211 |
| `home_services` | HVAC, roofing, windows, plumbing, pest control, remodeling | 238, 561710 |
| `healthcare` | Providers, pharmacies, medical devices | 62, 456 |
| `education` | Schools, training, student-loan help | 611 |
| `retail_ecommerce` | Retailers and consumer brands contacting customers | 44–45 |
| `auto` | Dealers, repair and service | 441, 8111 |
| `telecom_tech` | Carriers, software and SaaS sellers | 517, 513, 518 |
| `travel_hospitality` | Travel, timeshare, hotels, cruises | 5615, 721 |
| `marketing_services` | Lead generators, call centers, agencies selling their own services | 5418, 561422 |
| `political_nonprofit` | Campaigns, PACs, charities | 813 |
| `other` | Anything else. Describe it in F4. | — |
| `unknown` | Product not identifiable from the complaint | — |

## 9. Evidence rule

- **LLM:** every coded field except counts, names and dates carries `{page, quote}`. The quote must be verbatim from the complaint, 40 words or fewer.
  - A deterministic check confirms each quote appears in the complaint text.
  - If a quote doesn't match, the record fails and goes to human review.
  - No quote, no code.
- **Humans:** a page number per field. The quote is optional.
- Flags coded `no` because the complaint is silent carry no evidence.

This is CiV's standing rule, applied to the classifier: no finding without a stored artifact behind it.

---

## 10. Reliability protocol: how κ is earned, and the improvement loop

**Gold set.** 100 complaints, coded **blind**: coders never see LLM output for gold items. The set is stratified so that every category is tested:

- every filing year from 2019 to 2026;
- at least 30 class actions and 30 individual suits;
- at least 15 text cases and 8 fax cases;
- at least 10 dockets from non-485 nature-of-suit codes, to test the screen;
- at least 8 pro se cases and at least 5 state-only cases.

Rare categories (calling hours, AI voice) are enriched by keyword search over the docket text.

**Who codes what.**

- Both coders code the same 30 complaints. Their agreement with each other is the ceiling for any machine.
- Each coder then codes 35 of the remaining 70.
- Disagreements on the shared 30 are adjudicated by the codebook owner.
- If the two humans fall below κ 0.80 on a field, the rule is the problem, not the coders. Rewrite the rule before measuring the LLM against it.

**How to fill in `hand_coding_sheet.csv`.**

- **One row per docket.**
- **B1–B6:** enter `y` or `n`. Never leave them blank, because a blank can't be scored.
- **B7:** enter `FL: Fla. Stat. §501.059; OK: 15 Okla. Stat. §775C.1`.
- **B8:** enter the citations, separated by `;`.
- **Multi-selects (A4, D1, F7):** separate values with `;`.
- **F1:** enter `Name | role; Name | role`.
- **`minutes_spent`:** record it, because it tests the 12-minute time box.

**Split.** After adjudication, the 100 are randomly split into **DEV (40)** and **TEST (60, locked)**.

**The loop.** Each pass is a new codebook version.

1. The LLM codes DEV under codebook vN.
2. A script lists every disagreement with gold, with both pieces of evidence side by side.
3. The owner rules on each disagreement:
   - (a) The LLM misapplied a clear rule: add a worked example.
   - (b) The rule is ambiguous: rewrite it.
   - (c) The gold answer was wrong: correct it and log the change.
   - (d) The question can't be decided from the complaint: define the `unclear` path.
4. Bump the version, add a changelog entry, and re-run DEV.
5. When DEV disagreements stop teaching anything new (or after three passes), run TEST **once**. Record the model, prompt version, codebook version and per-field κ in `classification_run`.
6. In production, some records go to a human queue: any record with an `unclear` value, a failed quote check, or a schema error. Those human rulings feed **DEV** for the next version, never TEST.
7. Every quarter, add 25 fresh blind-coded complaints to TEST. This is the drift check, and new fact patterns appear here first.

**Gates for publishing.** A field can appear in a published table only if it meets three conditions:

- TEST κ ≥ 0.80;
- at least 10 positive cases in TEST;
- human–human κ ≥ 0.80 on that field.

Fields that miss a gate are published with their measured κ and the label "not yet validated," or folded into "other." Per-field κ, precision, recall and the number of positive cases appear in the methodology appendix.

**The one rule: the loop learns, the ruler doesn't.** TEST items never appear in prompts, examples, or discussions about rewriting rules. If they leak, the published κ measures memory, not accuracy, and an actuary will ask.

## 11. Instrument 2: Resolution coding (outline, separate from complaint coding)

- **Sources, in order:**
  1. FJC Integrated Database disposition fields.
  2. Docket entries.
  3. Final-approval orders and settlement agreements, for amounts.

  Press coverage and blogs are never a source.
- **Outcome values:** `voluntary_dismissal` · `settled_notice` · `class_settlement_approved` · `dismissed_on_motion` · `compelled_arbitration` · `judgment_defendant` · `judgment_plaintiff` · `default_judgment` · `transferred_mdl` · `pending` · `other`.
- **Amount fields:**
  - `settlement_fund_total`
  - `attorney_fees_awarded`
  - `class_members`
  - `per_claimant_amount`, if stated
  - `source_document`: the docket entry number plus the sha256 of the stored file
- The mapping from FJC disposition codes to these outcomes is written from the FJC civil codebook when the file is downloaded, not from memory.

## 12. Version control

- Versions are numbered `vMAJOR.MINOR`.
  - **MINOR:** a rule is rewritten or an example is added.
  - **MAJOR:** a value is added, removed or redefined. That breaks comparability, so old outputs must be re-run before tables combine them.
- Every LLM run records `codebook_version`, and every published number cites a run.
- The schema's `codebook_version` value is updated with every version.

**Changelog**

- **v0.1** (2026-10-06): first draft for owner review. Splits the earlier eight categories into three dimensions: legal hook, channel, and fact flags. Adds junk fax and other federal claims, the A2 screen, the evidence rule, and the reliability protocol.

## 13. Open decisions for the codebook owner (before hand-coding starts)

1. **Debt collectors.** They are a large share of TCPA suits, but they aren't CiV's or Falcon's insureds. The proposal is to code them, then report them as a separate row so they don't inflate telemarketing frequency.
2. **Class vs. individual suits.** Severity differs by orders of magnitude between the two. The proposal is to always report frequency and severity split by E1.
3. **Second coder.** The candidates are Connor or a paid contractor. Each coder needs about 13 hours: 65 complaints at 12 minutes each, spread over two weeks.
4. **Legal read.** Send rules R1–R8 to Larry Zanger's network for one 30-minute read before coding starts. A defense lawyer's objection now is cheaper than a κ failure later.
5. **Unit of severity when cases consolidate (MDL, related cases).** The choice is per docket or per consolidated group. The proposal is to code per docket and link consolidated dockets in Instrument 2.
