# Architecture planning - Rad

Produces engineering-grade Architecture & Build Plan PDF documents for any software project,
structured like the blueprint an engineer prepares before constructing a building.

## What it does

One skill, `architecture-doc`, drives a 7-phase workflow:

1. Elicit decisions and ground the document in real systems (live project IDs, credentials)
2. Write the task-level implementation plan first (complete code, verification steps)
3. Author Part I: principles, system context, data/behavior architecture, and a work
   breakdown structure - phased work packages with dependencies, acceptance gates, and
   per-package model recommendations for AI build agents
4. Build four vector diagrams (context, entity model, state machine, dependency graph)
5. Render to PDF with the bundled config-driven reportlab generator
6. Verify pages visually before delivery
7. Deliver a self-contained PDF whose Appendix A embeds the full plan

## Usage

Say things like "make an architecture document for X", "turn this plan into a build-plan PDF",
or "segment this project into linked work packages".

Requires Python with reportlab (`pip install reportlab`); poppler-utils (pdftoppm) recommended
for the visual verification step.

