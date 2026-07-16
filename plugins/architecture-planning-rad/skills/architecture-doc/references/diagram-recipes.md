# Diagram recipes

Diagrams live in a `diagrams.py` module next to `part1.md`. The renderer imports it and looks
for one dict:

```python
DIAGRAMS = {
    "context": (diagram_context, "Figure 1 - System context: ..."),
    "erd":     (diagram_erd,     "Figure 2 - Entity model: ..."),
    "routing": (diagram_routing, "Figure 3 - Behavior/state machine: ..."),
    "wbs":     (diagram_wbs,     "Figure 4 - Work-package dependency graph (...)"),
}
```

Each function returns a `reportlab.graphics.shapes.Drawing`. A `@@DIAGRAM:name@@` line in any
markdown source is replaced by the drawing plus its caption.

## Helper API (import from render_pdf)

```python
from render_pdf import Drawing, dbox, arrow, note, INK, MUTED, BOX_FILL, BOX_EDGE
```

- `dbox(d, x, y, w, h, lines, fill=..., edge=..., fs=7.2)` — rounded box; `lines` is a list of
  strings, first line bold. Keep 1–3 lines, <= ~28 chars each.
- `arrow(d, x1, y1, x2, y2, dashed=False)` — line with an arrowhead at (x2, y2). Solid = hard
  dependency / data flow; dashed = conditional or annotation flow. Be consistent and say what
  dashed means in the caption or a `note`.
- `note(d, x, y, text, fs=6.6, anchor="middle")` — small italic annotation.

Coordinate system: origin bottom-left, y grows upward. Standard canvas: `Drawing(480, H)` with
H between 230 and 330. Body width available is ~478pt, so 480 fills the text column.

Color roles (stay flat, 2–3 accent families max):
- default blue (`BOX_FILL`/`BOX_EDGE`) for ordinary components
- amber `#fdf3e4` / `#b98a3e` for the orchestration core / hub entity
- green `#f0f4ea` / `#7a955c` for inputs/adapters; `#eaf5e6` / `#5d8a4e` for success terminals
- red `#f9e9e6` / `#a85b4b` for escalation/failure terminals

## Recipe 1 — System context (layered rows)

Four rows top-to-bottom: external actors/channels, adapters, the core (one wide amber box,
centered), shared services. Boxes 105–115 wide on x positions like `[3, 123, 243, 363]`;
vertical arrows actor→adapter; converging arrows adapter→core (spread the arrow endpoints on
the core's top edge, e.g. x = 150 + i*60); diverging arrows core→services. Put the system's
one-sentence invariant as a `note` at the bottom.

## Recipe 2 — Entity/component model (hub and spokes)

Hub entity (amber) center-left; parent/master entity to its left; child/audit entities as a
right-hand stack of 4 boxes (ys like `[196, 148, 100, 52]`, h=34). Arrows parent→hub and
hub→each child, each labeled `1:N` with a `note` at the arrow midpoint. Auxiliary mechanisms
(counters, triggers) as a small box connected with a dashed arrow. Bottom note: the structural
guarantee (e.g. "every child row requires the hub FK — orphans are impossible").

## Recipe 3 — Behavior/state machine

Left-to-right: input box → classifier/router (amber) → one large box listing the actors/states
(use 4–5 short lines inside). Terminals as green (success) and red (failure/escalation) boxes
on a bottom row with arrows from the actor box. A dashed bypass arrow for the "already
assigned/continuing" path. Self-loops are hard to draw well: fake one with three short lines
down the right edge (two `Line`s + one `arrow` back in) and a note explaining it. Always
annotate the loop-termination rule (the cap) near the loop.

## Recipe 4 — WBS dependency graph (phase columns)

One column per phase, x positions like `{"A": 4, "B": 110, "C": 208, "D": 318, "E": 414}`,
box w=88 h=26, vertical gap 9, first row at y = 296 - h. Column headers via `note(..., fs=7,
color=INK)` at y=308. Write a tiny `wp(col, row, label, sub)` closure that computes the box
position and returns (x, y) — then draw arrows from the returned coordinates. Chain arrows
within a column; cross-column arrows from box right-edge to target left-edge. Color the core
packages amber and the launch package green. Bottom note: "Solid arrows = build dependency"
plus the parallelization statement. The arrows MUST agree with the Depends-on column of the
section-8 tables — that consistency is checked in the quality bar.

## Layout discipline

- 6.4–7.8pt fonts inside diagrams; nothing below 6.
- Never let arrows cross box interiors; route around or reorder boxes.
- If a diagram needs more than ~20 boxes, split it (overview + detail) rather than shrinking.
- After rendering, ALWAYS inspect the figure pages as images (Phase 6) — coordinate bugs are
  invisible in code and obvious in pixels.
