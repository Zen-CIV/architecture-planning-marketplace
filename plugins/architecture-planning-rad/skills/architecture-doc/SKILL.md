---
name: architecture-doc
description: Produce an engineering-grade Architecture & Build Plan PDF for any software project — like the blueprint an engineer prepares before constructing a building. The document combines Part I (architecture principles, system-context / entity / behavior / dependency diagrams, and a work breakdown structure of phased work packages with acceptance gates, dependency linkage, and per-package model recommendations for AI build agents) with Appendix A (the complete task-level implementation plan embedded verbatim). Use this skill whenever the user asks for an architecture document, technical design document, build plan, blueprint, work breakdown structure (WBS), phased project plan, "a plan I can hand to Claude/Opus/Sonnet agents to build", "segment the plan into linked tasks", or wants any implementation plan turned into a professional PDF — even if they don't say "architecture" explicitly. Also use it when a plan already exists in the conversation and the user wants it "organized, structured, and delivered as a PDF".
---

# Architecture & Build Plan documents

## What this produces

A single self-contained PDF, structured like a construction drawing set:

- **Cover + clickable table of contents + PDF bookmarks**
- **Part I — Architecture** (~10 pages): document control, executive summary, numbered architecture principles, system context, data/component architecture, behavior architecture, work breakdown structure, execution model for build agents, environment/credentials matrix, risk register, assumptions & out-of-scope
- **Four vector diagrams**: system context, entity/component model, behavior/state machine, and the work-package dependency graph
- **Appendix A — the full task-level implementation plan** embedded verbatim (all code, configs, verification commands), so the PDF alone is sufficient to build the system

The quality of the PDF is downstream of the quality of the plan. Never skip Phase 2.

## Workflow

### Phase 1 — Elicit and ground

Before writing anything, lock the decisions that shape the architecture: target platforms, components in scope, constraints, who executes (human team vs AI agents), and any policy choices the spec leaves open. Ask the user only what you cannot infer.

Critically, **ground the document in reality**: if MCP tools for the target systems are connected (databases, workflow platforms, cloud accounts), query them now — real project IDs, credential names, existing tables, live URLs. A document that says "credential `j3VJ...` exists; credential X must be created by the user" is worth ten that say "configure credentials". Record everything you cannot create yourself (secrets, OAuth) as explicit **user action items**.

### Phase 2 — Write the implementation plan first

The plan is the load-bearing artifact; the architecture document is its presentation layer. If a plan-writing skill is available (e.g. `superpowers:writing-plans`), use it. Either way the plan must have, for every task: exact file paths, complete copy-ready code (no "TBD", no "add error handling", no "similar to Task N"), exact verification commands with expected output, and a commit step. Save it as its own markdown file — it doubles as Appendix A and as the working file for build agents who prefer markdown.

### Phase 3 — Author Part I

Follow `references/document-structure.md` section by section — it defines the 12-section anatomy, what each section must contain, and the quality bar (evidence-demandable acceptance gates, a copy-paste briefing template, a coverage map from spec requirement → task). Write Part I as `part1.md` in a working directory, with `@@DIAGRAM:name@@` markers where figures belong.

The heart of Part I is **section 8, the work breakdown structure**: group the plan's tasks into phases, map each task to exactly one work package (WP), and give every WP a dependency list, an acceptance gate copied from the plan's verification steps, and a recommended executor model. Identify the critical path and call out which phases parallelize.

### Phase 4 — Build the diagrams

Write `diagrams.py` next to `part1.md` using the helper API from the bundled renderer. Read `references/diagram-recipes.md` for the four standard recipes (context, entity, behavior, WBS graph) with working layout coordinates. Diagrams are code, not images: flat boxes, small fonts, arrows with real meaning, one caption each. Every `@@DIAGRAM:name@@` marker must have a matching entry in the module's `DIAGRAMS` dict.

### Phase 5 — Render

```bash
pip install reportlab --break-system-packages -q
python3 scripts/render_pdf.py --config doc.json
```

`doc.json` (in the working directory) drives everything:

```json
{
  "title": "My System",
  "subtitle": "Architecture & Build Plan - <one-line stack summary>",
  "version": "1.0",
  "date": "YYYY-MM-DD",
  "footer": "My System - Architecture & Build Plan",
  "meta": [["Owner", "..."], ["Built for", "..."], ["Stack", "..."], ["Structure", "..."]],
  "sources": [
    {"path": "part1.md", "shift": 0},
    {"path": "../plans/my-plan.md", "shift": 1, "skip_until": "\\*\\*Goal:\\*\\*"}
  ],
  "diagrams_module": "diagrams.py",
  "output": "My-System-Architecture.pdf"
}
```

`shift: 1` demotes the appendix's headings one level so they nest under Part I's "Appendix A" heading; `skip_until` drops the plan's own title block. The renderer already handles the hard-won edge cases: heading-level jumps in PDF outlines, code blocks taller than a page (auto-chunked), Unicode characters missing from the built-in fonts (auto-sanitized), and multi-pass TOC resolution.

### Phase 6 — Verify visually (do not skip)

A successful exit code is not a verified PDF. Render key pages to images and look at them:

```bash
python3 -c "from pypdf import PdfReader; r=PdfReader('OUT.pdf'); print(len(r.pages)); \
[print(i+1,m) for i,p in enumerate(r.pages) for m in ['Figure 1','Figure 2','Figure 3','Figure 4'] if m in (p.extract_text() or '')]"
pdftoppm -png -r 60 -f <page> -l <page> OUT.pdf check
```

Inspect: the cover, every figure page (arrows connect the right boxes? labels overlap?), and one code-heavy appendix page. Also check extracted text for black-box glyphs (a missing-font symptom). Fix and re-render until clean.

### Phase 7 — Deliver

Present the PDF to the user. Summarize the structure in a few sentences (Part I sections, WP count, phase count) — not a page-by-page recap. If the plan will be executed by AI agents, point at section 9's briefing template as the dispatch mechanism.

## Bundled resources

- `scripts/render_pdf.py` — the config-driven markdown → PDF renderer with cover, TOC, bookmarks, headers/footers, tables, chunked code blocks, and the diagram helper API (`dbox`, `arrow`, `note`). Use it as-is; do not rewrite it per project.
- `references/document-structure.md` — the 12-section anatomy of Part I with per-section content requirements and the quality bar. Read it in Phase 3.
- `references/diagram-recipes.md` — the diagram helper API and four standard diagram recipes. Read it in Phase 4.
- `assets/part1-skeleton.md` — a fill-in skeleton for Part I. Copy it as your starting point.

## Quality bar (check before delivering)

- Every WP has a gate a reviewer could demand literal evidence for (query output, execution result, received message) — "works correctly" is not a gate.
- Every spec requirement appears in a coverage map pointing at a concrete task.
- The briefing template in section 9 can be copied, filled, and dispatched without edits.
- Zero placeholders anywhere ("TBD", "add validation", "similar to above").
- Secrets and manual steps are listed as user action items, never silently assumed.
- The document names real resources (IDs, credential names, hosts) wherever tools could verify them.

