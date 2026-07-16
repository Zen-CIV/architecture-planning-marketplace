# 1. Document control

| Field | Value |
|---|---|
| Document | <Project> — Architecture & Build Plan |
| Version | 1.0 |
| Date | <YYYY-MM-DD> |
| Owner | <name (contact)> |
| Intended readers | <build agents / team> |
| Companion artifact | Appendix A of this document (full task-level implementation plan) |
| Target platforms | <platforms with real identifiers> |

**How to use this document.** Part I (sections 2–12) is the architecture. Appendix A is the
construction drawing set: every work package points to a numbered Task with complete,
copy-ready content. A build agent should read Part I once for orientation, then execute its
assigned work package strictly from Appendix A.

# 2. Executive summary

<Paragraph 1: what the system is — components, channels, the core guarantee.>

<Paragraph 2: how the build is segmented — N phases, M work packages, one clause per phase,
every WP has an acceptance gate.>

# 3. Architecture principles

**P1 — <name>.** <Rule.> <Rationale.>

**P2 — <name>.** <Rule.> <Rationale.>

# 4. System context

@@DIAGRAM:context@@

| Actor/channel | Entry point | Identity key | Return path |
|---|---|---|---|
| | | | |

# 5. Data architecture

## 5.1 Entity model

@@DIAGRAM:erd@@

| Table/component | Role | Key columns/fields |
|---|---|---|
| | | |

## 5.2 Identity and traceability strategy

## 5.3 <ownership / single-writer rules>

## 5.4 Interface catalog

| Function/endpoint | Purpose | Called by |
|---|---|---|
| | | |

## 5.5 Storage and security

# 6. Behavior architecture

## 6.1 Actor roster

| Actor | Scope | Special powers |
|---|---|---|
| | | |

## 6.2 Output/action contract

## 6.3 Control flow

@@DIAGRAM:routing@@

## 6.4 Escalation/failure policy

# 7. Component catalog

| # | Component | Trigger | Responsibility | Depends on |
|---|---|---|---|---|
| | | | | |

# 8. Work breakdown structure

@@DIAGRAM:wbs@@

Legend: each work package (WP) maps to exactly one Task in Appendix A. "Gate" is the
evidence-demandable acceptance criterion. "Model" is the recommended executor.

## Phase A — <name>

| WP | Task | Scope | Depends on | Gate | Model |
|---|---|---|---|---|---|
| | | | | | |

**Critical path:** <WP chain>. <Parallelization callout.>

# 9. Execution model for build agents

## 9.1 Dispatch protocol

## 9.2 Work package briefing template (copy, fill, dispatch)

```
You are executing work package <WP-ID> of <Project>.
Authoritative spec: Appendix A, Task <N> of the architecture document.
Environment: <real tool names, project IDs, paths>
Hard rules (architecture principles): <cite by number>
Acceptance gate for this WP: <paste Gate cell>.
Do not report completion without pasting literal evidence that the gate passed.
If a step's expected output does not match, STOP, diagnose, and report.
```

## 9.3 Verification gates between phases

| Gate | After | Evidence required |
|---|---|---|
| | | |

## 9.4 Model selection rationale

# 10. Environment and credentials matrix

| Resource | Identifier | Status |
|---|---|---|
| | | |

# 11. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| | | | | |

# 12. Assumptions and out of scope

**Assumptions:**

**Out of scope (v2 candidates):**

---

# Appendix A — Implementation plan (construction drawings)

Everything below is the complete task-level build plan. Work packages in section 8 map 1:1 to
Tasks here. All code, verification queries, and expected outputs are authoritative and
copy-ready.
