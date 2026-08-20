# Datapoint catalog — public-web collectability

`datapoint_catalog_public_flags.csv` is the full 182-row TCPA datapoint catalog with two
columns appended:

- **Publicly collectible** — whether the datapoint can be obtained from openly available
  sources (company websites, government registries, court dockets, regulator databases,
  professional networks, archives) with no cooperation from the target company.
- **Public collection route** — the specific public source or technique for that datapoint.

`datapoint_catalog_collectible.csv` is the working sheet: the 134 rows marked `Yes` or
`Partial` — everything the public web can contribute to. It adds two more columns,
**What the public web gives you** and **What it does not give you**, so each `Partial` row
states its own limit rather than leaving you to guess.

`datapoint_catalog_public_only.csv` is the strict subset: the 109 `Yes` rows only.

## Marking scheme

| Value | Meaning | Count |
|---|---|---|
| `Yes` | Obtainable end-to-end from public sources. | 109 |
| `Partial` | A public source establishes part of the answer; the full value needs the company. | 25 |
| `No` | Only the company, or a closed registry/system, can supply it. | 36 |
| `Derived` | Not collected at all — computed from other datapoints. The route column notes whether its inputs are public. | 12 |

`Yes` and `Partial` together cover 134 of 182 datapoints (74%).

## What `Partial` actually covers

The 25 `Partial` rows are three distinct situations, all named per-row in the
`What it does not give you` column:

1. **Existence is public, magnitude is not.** A vendor case study proves ringless voicemail
   is in use; it will not tell you the volume. (Ringless voicemail, prerecorded voice,
   dialer platform, BPO, call recording.)
2. **The stated commitment is public, the practice is not.** A published DNC policy states a
   10-day honoring window — a quotable commitment, but not evidence it is met.
   (Honoring window, revocation methods, calling window, policy on demand.)
3. **The record is public but access is not free.** State-court dockets and phone line-type
   classification are public or commercially available, but paywalled or per-county.
   (State court TCPA matters, line type per number.)

Practical rule: a `Partial` is usually strong enough to open a conversation with, and not
strong enough to assert as a finding.

## Notes on the judgement calls

- **"ASK" as primary source is not automatically `No`.** Where a public artifact carries part
  of the answer (a published policy stating a honoring window, a vendor case study naming a
  cadence), the row is `Partial` rather than `No`.
- **Public ≠ free.** State-court dockets, PACER documents and phone line-type classification
  are public or commercially available records but are paywalled or per-jurisdiction; those
  are marked `Partial` with the access limitation named.
- **Closed registries are `No`.** The Campaign Registry (A2P 10DLC), FTC DNC subscriber/SAN
  status, and carrier CNAM/STIR-SHAKEN records are not published, even though the underlying
  activity is regulated.
- **Anything describing internal process, retention, or system architecture is `No`.** All of
  Recordkeeping (K) except disclosure reproducibility, and all of Governance (L) except the
  two headcount/identity rows, fall here.

## Where the public surface is strongest and weakest

Fully public families: Complaints (M), Enforcement (O), Jurisdiction (P), Vendor risk (Q).
Litigation (N) is public except state-court matters. Consent capture (D) is public except
the offline phone script, and Entity/Scale (A, B) are public except two mix questions.

Weakest: Recordkeeping (K), Governance (L), Timing & cadence (J), and DNC & suppression (I) —
these are the operational-control families that require the company to answer.
