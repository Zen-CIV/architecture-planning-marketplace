# Datapoint catalog — public-web collectability

`datapoint_catalog_public_flags.csv` is the full 182-row TCPA datapoint catalog with two
columns appended:

- **Publicly collectible** — whether the datapoint can be obtained from openly available
  sources (company websites, government registries, court dockets, regulator databases,
  professional networks, archives) with no cooperation from the target company.
- **Public collection route** — the specific public source or technique for that datapoint.

`datapoint_catalog_public_only.csv` is the same file filtered to `Publicly collectible = Yes`.

## Marking scheme

| Value | Meaning | Count |
|---|---|---|
| `Yes` | Obtainable end-to-end from public sources. | 109 |
| `Partial` | A public source establishes part of the answer; the full value needs the company. | 25 |
| `No` | Only the company, or a closed registry/system, can supply it. | 36 |
| `Derived` | Not collected at all — computed from other datapoints. The route column notes whether its inputs are public. | 12 |

`Yes` and `Partial` together cover 134 of 182 datapoints (74%).

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
