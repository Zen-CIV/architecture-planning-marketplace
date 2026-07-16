# Part I anatomy — 12 sections

Write Part I in this order. Every section has a purpose; if a section genuinely doesn't apply
(e.g. no credentials exist for a pure-algorithm project), keep the heading and state why in one
line rather than silently dropping it — build agents rely on the structure being predictable.

## 1. Document control

A small table: document name, version, date, owner (name + contact), intended readers
(name the build agents explicitly if AI-executed), companion artifacts, target platforms with
real identifiers. Follow it with a short "How to use this document" paragraph that tells a build
agent to read Part I once for orientation and then execute strictly from Appendix A.

## 2. Executive summary

Two paragraphs, no bullets. Paragraph 1: what the system is and does, naming the concrete
channels/components and the core traceability or correctness guarantee. Paragraph 2: how the
build is segmented — number of phases, number of work packages, one clause on what each phase
delivers, and the fact that every work package has an acceptance gate.

## 3. Architecture principles

Numbered principles (P1, P2, …), each with a bold name, a one-sentence rule, and a rationale
sentence. Principles are the document's constitution: later sections and the briefing template
cite them by number (e.g. "P2: all writes go through the RPC layer"). 5–8 is the right count.
Good principles are enforceable and testable ("single writer for rollups — verified by grep in
WP E1"), not aspirations ("the system should be maintainable").

## 4. System context

The `@@DIAGRAM:context@@` figure plus a table mapping each external actor/channel to its entry
point, identity/threading key, and return path. Explain in prose the one mechanism that unifies
them (e.g. a normalized schema, a shared queue).

## 5. Data architecture (or component architecture for non-data-centric systems)

Sub-sections as needed: entity model (`@@DIAGRAM:erd@@` + a table of tables/components with
role and key columns), identity strategy (how IDs are minted and propagated), any single-writer
or ownership rules, an API/interface catalog table (every function/endpoint with purpose and
caller), storage/security model. Always point at the Appendix task numbers that carry the full
DDL/source — this section explains, the appendix specifies.

## 6. Behavior architecture

For agentic/stateful systems: the actor roster table (who does what, special powers), the
action/output contract (exact JSON or interface), the routing/state rules as a numbered list,
`@@DIAGRAM:routing@@`, and the escalation/failure policy. For simpler systems this becomes the
main control-flow section. State the loop-termination guarantees explicitly (caps, timeouts).

## 7. Component/workflow catalog

A table: id, component, trigger/entry point, responsibility (one line), depends-on. Derive the
build order from the dependency column and say it in one sentence. Reference where the full
per-component specs live in the appendix.

## 8. Work breakdown structure — the heart of the document

Open with `@@DIAGRAM:wbs@@`. Then one table per phase. Columns, exactly these:

| WP | Task | Scope | Depends on | Gate | Model |

- **WP**: phase letter + index (A0, A1, … C4, D1…). One WP maps to exactly one appendix Task.
- **Scope**: one line, no verbs like "handle" — name the artifact produced.
- **Depends on**: WP ids only. This column IS the linkage; the WBS diagram must match it.
- **Gate**: the acceptance criterion, condensed from the task's verification steps. It must be
  evidence-demandable: a query result, an execution output, a received message. "Works" or
  "passes review" are not gates.
- **Model**: recommended executor (e.g. Sonnet for fully-specified packages, Opus for packages
  with real degrees of freedom). Justify the split later in section 9.4.

Close the section with the **critical path** (WP chain) and the **parallelization callout**
(which phases/WPs can run concurrently and why they are independent).

Phase design guidance: phases follow the dependency structure of the system, not the calendar.
A canonical split for a data-backed system: A foundation (schema/storage), B static definitions
(prompts/configs — usually parallel with A), C core orchestration, D adapters/integrations
(usually the widest parallel fan), E system verification + launch. Adapt, don't force.

## 9. Execution model for build agents

Four sub-sections:

1. **Dispatch protocol** — one WP = one fresh agent session; review gate evidence between
   dispatches; failed gates go back to the same WP with the failure evidence attached; never
   span a phase boundary in one dispatch.
2. **Briefing template** — a fenced code block the orchestrator copies verbatim, with
   `<WP-ID>` / `<N>` placeholders, the environment (real tool names, project IDs, paths), the
   hard rules (cite principles by number), the gate, and the instruction to stop and report on
   mismatch rather than improvise.
3. **Phase gates** — a table: gate id, after which phase, evidence required.
4. **Model selection rationale** — why each model gets its packages, plus an escalation rule
   (e.g. "two failed gates under the cheaper model → re-dispatch to the stronger one with the
   failure transcripts").

## 10. Environment and credentials matrix

A table of every external resource: identifier, status (exists / must be created / must be
confirmed), and who acts (build agent vs **user action item** in bold). This is where grounding
from Phase 1 pays off — real credential IDs and hostnames, not placeholders.

## 11. Risk register

A table: #, risk, likelihood, impact, mitigation. Mitigations must point at concrete mechanisms
already in the design (a cap, an index, a gate, a guard node) — a mitigation that isn't built
anywhere is a gap in the WBS, so either add the work package or downgrade the claim.

## 12. Assumptions and out of scope

Two short paragraphs. Assumptions: things the design relies on but doesn't enforce (document
them so a violation is diagnosable). Out of scope: named v2 candidates, so readers know the
omission was a decision, not an oversight.

## Appendix A heading

End part1.md with the `# Appendix A — Implementation plan (construction drawings)` heading and
a two-sentence lead-in; the renderer appends the plan file under it (with `shift: 1`).

# Quality bar

Before rendering, re-read the spec and check:

1. **Coverage map** — every spec requirement maps to a task (include the map as a table at the
   end of the plan or of Part I).
2. **Placeholder scan** — grep part1 and the plan for TBD / TODO / "appropriate" / "similar to".
   The only acceptable "to be confirmed" items are runtime discoveries that have a dedicated
   resolution step in a named WP.
3. **Cross-reference consistency** — WP↔Task mapping is 1:1; gates quote the plan's actual
   verification steps; the WBS diagram's arrows equal the Depends-on columns; function/interface
   names in Part I match the appendix exactly.
4. **Real identifiers** — anywhere a connected tool could have verified a name/ID, the document
   uses the verified value.
