"""Diagrams for the CiV Dossier Engine architecture document."""

from reportlab.lib import colors
from render_pdf import Drawing, Line, dbox, arrow, note, INK, MUTED, BOX_FILL, BOX_EDGE


def route(d, pts, dashed=False):
    """Orthogonal multi-segment connector; arrowhead on the final segment."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:-1]):
        ln = Line(x1, y1, x2, y2, strokeColor=BOX_EDGE, strokeWidth=0.9)
        if dashed:
            ln.strokeDashArray = [2.5, 2.5]
        d.add(ln)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    arrow(d, x1, y1, x2, y2, dashed=dashed)

AMB_F, AMB_E = colors.HexColor("#fdf3e4"), colors.HexColor("#b98a3e")
GRN_F, GRN_E = colors.HexColor("#f0f4ea"), colors.HexColor("#7a955c")
OKG_F, OKG_E = colors.HexColor("#eaf5e6"), colors.HexColor("#5d8a4e")
RED_F, RED_E = colors.HexColor("#f9e9e6"), colors.HexColor("#a85b4b")


# ---------------------------------------------------------------- Figure 1
def diagram_context():
    d = Drawing(480, 300)

    # Row 1 - external sources
    srcs = [
        (3,   ["Brand websites", "forms, policies, SMS terms"]),
        (123, ["Open web", "directories, boards, press"]),
        (243, ["CourtListener", "federal TCPA dockets"]),
        (363, ["Loaded corpora", "FCC 80.5k / FTC 466k / NANPA"]),
    ]
    for x, lines in srcs:
        dbox(d, x, 252, 114, 30, lines, fill=GRN_F, edge=GRN_E, fs=6.8)

    # Row 2 - adapters
    adps = [
        (3,   ["Apify", "real Chrome render"]),
        (123, ["Tavily", "search API"]),
        (243, ["HTTP Request", "rate-limited 5/min"]),
        (363, ["Postgres", "joins, no model"]),
    ]
    for x, lines in adps:
        dbox(d, x, 194, 114, 28, lines, fs=6.8)
    for x, _ in srcs:
        arrow(d, x + 57, 252, x + 57, 222)

    # Row 3 - the core
    dbox(d, 60, 122, 360, 44,
         ["WF-CIV-10  Chunk Runner", "claims 8 - dispatches by archetype - validates",
          "sql | api | fetch | extract | research | compute | compose"],
         fill=AMB_F, edge=AMB_E, fs=7.4)
    for i, (x, _) in enumerate(adps):
        arrow(d, x + 57, 194, 120 + i * 80, 166)

    # Row 4 - stores
    dbox(d, 3,   58, 150, 34, ["civ_artifact", "stored bytes + sha256"], fs=6.9)
    dbox(d, 165, 58, 150, 34, ["civ_finding", "one row per company x datapoint"], fs=6.9)
    dbox(d, 327, 58, 150, 34, ["civ_chunk_run", "queue + cost/token log"], fs=6.9)
    arrow(d, 180, 122, 78,  92)
    arrow(d, 240, 122, 240, 92)
    arrow(d, 300, 122, 402, 92)

    # Terminal
    dbox(d, 165, 8, 150, 32, ["Dossier (.md)", "one per company"], fill=OKG_F, edge=OKG_E, fs=7)
    arrow(d, 240, 58, 240, 40)
    note(d, 78, 46, "written before any finding may cite it", fs=6.2)
    note(d, 240, 2,
         "Invariant: no finding may reference text absent from civ_artifact.", fs=6.6, color=INK)
    return d


# ---------------------------------------------------------------- Figure 2
def diagram_erd():
    d = Drawing(480, 290)

    dbox(d, 4, 200, 118, 40, ["companies", "504 rows", "civ_status, civ (projection)"], fs=6.9)
    dbox(d, 4, 96,  118, 40, ["civ_chunk_def", "30 chunks", "depends_on, produces"], fs=6.9)
    dbox(d, 4, 20,  118, 36, ["civ_datapoint", "134 rows", "method, ttl_days"], fs=6.9)

    dbox(d, 168, 112, 128, 62,
         ["civ_finding", "PK (company_id,", "datapoint_id)",
          "citation_gate CHECK"], fill=AMB_F, edge=AMB_E, fs=7)

    ys = [214, 160, 106, 52]
    kids = [
        ["civ_artifact", "body + sha256"],
        ["civ_chunk_run", "queue + cost log"],
        ["civ_state_overlay", "statutes, verified"],
        ["civ_budget", "daily cap, halted"],
    ]
    for y, lines in zip(ys, kids):
        dbox(d, 348, y, 128, 36, lines, fs=6.9)

    arrow(d, 122, 214, 168, 168); note(d, 142, 186, "1:N")
    arrow(d, 122, 116, 168, 143); note(d, 146, 134, "1:N")
    arrow(d, 122, 38,  168, 118); note(d, 138, 66,  "1:N")

    arrow(d, 296, 156, 348, 226); note(d, 322, 196, "FK required")
    arrow(d, 296, 148, 348, 178); note(d, 322, 168, "run_id")
    arrow(d, 296, 132, 348, 124); note(d, 322, 122, "P01-P06")
    arrow(d, 296, 120, 348, 70);  note(d, 322, 90,  "guards")

    dbox(d, 168, 206, 128, 32, ["civ_project_company()", "single writer"],
         fill=GRN_F, edge=GRN_E, fs=6.6)
    arrow(d, 232, 174, 232, 206, dashed=True)
    arrow(d, 168, 222, 122, 222, dashed=True)

    note(d, 240, 12,
         "Dashed = the only path that writes companies.civ (P4).", fs=6.4, color=INK)
    note(d, 240, 2,
         "A value with no artifact_id and no verbatim quote cannot be inserted (P2).",
         fs=6.4, color=INK)
    return d


# ---------------------------------------------------------------- Figure 3
def diagram_routing():
    d = Drawing(480, 300)

    dbox(d, 4, 236, 108, 34, ["companies", "civ_status = new"], fill=GRN_F, edge=GRN_E, fs=7)
    dbox(d, 138, 232, 128, 42,
         ["civ_ready_chunk", "depends_on satisfied?", "-> pending run"],
         fill=AMB_F, edge=AMB_E, fs=7)
    arrow(d, 112, 253, 138, 253)

    dbox(d, 292, 236, 184, 34,
         ["civ_claim_chunks(worker, 8)", "FOR UPDATE SKIP LOCKED"], fs=7)
    arrow(d, 266, 253, 292, 253)

    dbox(d, 292, 150, 184, 74,
         ["Archetype dispatch", "sql 8  ·  research 10  ·  extract 4",
          "fetch 4  ·  api 2  ·  compute 1", "compose 1"], fs=6.9)
    arrow(d, 384, 236, 384, 224)

    dbox(d, 4, 150, 108, 62,
         ["SCR-01", "litigation screen", "GATE G1", "runs first, always"],
         fill=RED_F, edge=RED_E, fs=6.9)
    arrow(d, 202, 232, 112, 200, dashed=True)
    note(d, 158, 208, "no depends_on", fs=6.2)

    dbox(d, 4, 74, 108, 36, ["disqualified", "remaining chunks", "skipped"],
         fill=RED_F, edge=RED_E, fs=6.8)
    arrow(d, 58, 150, 58, 110)
    note(d, 64, 128, "docket match", fs=6.2, anchor="start")

    dbox(d, 168, 74, 128, 40, ["PC-22 assertion gate", "civ_citation_violation", "must be 0"],
         fill=AMB_F, edge=AMB_E, fs=6.9)
    arrow(d, 340, 150, 250, 114)

    dbox(d, 330, 74, 146, 40, ["PC-23 dossier", "template + 1 summary call",
                               "civ_status = complete"], fill=OKG_F, edge=OKG_E, fs=6.9)
    arrow(d, 296, 94, 330, 94)

    dbox(d, 168, 12, 128, 36, ["run failed", "attempts < 3 -> pending", "else dead"],
         fill=RED_F, edge=RED_E, fs=6.8)
    arrow(d, 340, 150, 296, 40, dashed=True)
    arrow(d, 232, 48, 232, 74, dashed=True)

    note(d, 240, 2,
         "Caps that terminate every loop: max_tool_calls 12, max_attempts 3, "
         "30-min claim reaper, daily civ_budget halt.", fs=6.4, color=INK)
    return d


# ---------------------------------------------------------------- Figure 4
def diagram_wbs():
    d = Drawing(480, 268)
    COLS = {"A": 4, "B": 110, "C": 216, "D": 322, "E": 402}
    W, H, GAP = 78, 26, 9
    ROW = {r: 244 - H - r * (H + GAP) for r in range(5)}   # 218 183 148 113 78
    pos = {}

    for c, x in COLS.items():
        note(d, x + W / 2, 256, f"Phase {c}", fs=7, color=INK)

    def wp(col, row, label, sub, fill=BOX_FILL, edge=BOX_EDGE):
        x, y = COLS[col], ROW[row]
        dbox(d, x, y, W, H, [label, sub], fill=fill, edge=edge, fs=6.4)
        pos[label] = (x, y)

    wp("A", 0, "A1", "findings + gate")
    wp("A", 1, "A2", "queue + claim")
    wp("A", 2, "A3", "ready view", AMB_F, AMB_E)
    wp("A", 3, "A4", "guards + proj")

    wp("B", 0, "B1", "134 catalog")
    wp("B", 1, "B2", "archetypes")
    wp("B", 2, "B3", "prompts", AMB_F, AMB_E)
    wp("B", 3, "B4", "state overlay")

    wp("C", 0, "C1", "WF-00 guard")
    wp("C", 1, "C2", "WF-01 sched")
    wp("C", 2, "C3", "WF-10 runner", AMB_F, AMB_E)

    wp("D", 0, "D1", "SCR-01 screen")
    wp("D", 1, "D2", "8 sql chunks")
    wp("D", 2, "D3", "3 fetch chunks")
    wp("D", 3, "D4", "4 extract")
    wp("D", 4, "D5", "10 research")

    # Phase E reads bottom-to-top so D5 -> E1 is a clean horizontal.
    wp("E", 4, "E1", "PC-21 score")
    wp("E", 3, "E2", "gate + dossier", AMB_F, AMB_E)
    wp("E", 2, "E3", "TTL refresh")
    wp("E", 1, "E4", "pilot x20", OKG_F, OKG_E)

    def chain(a, b):
        """Vertical link inside one column."""
        ax, ay = pos[a]
        bx, by = pos[b]
        if ay > by:
            arrow(d, ax + W / 2, ay, bx + W / 2, by + H)
        else:
            arrow(d, ax + W / 2, ay + H, bx + W / 2, by)

    def side(a, b):
        """Horizontal link between adjacent columns."""
        ax, ay = pos[a]
        bx, by = pos[b]
        arrow(d, ax + W, ay + H / 2, bx, by + H / 2)

    for a, b in [("A1", "A2"), ("A2", "A3"), ("A3", "A4"),
                 ("B1", "B2"), ("B2", "B3"), ("B3", "B4"),
                 ("C1", "C2"), ("C2", "C3"),
                 ("D1", "D2"), ("D2", "D3"), ("D3", "D4"), ("D4", "D5"),
                 ("E1", "E2"), ("E2", "E3"), ("E3", "E4")]:
        chain(a, b)

    side("A1", "B1")      # A1 -> B1
    side("B3", "C3")      # B3 -> C3
    side("D5", "E1")      # D5 -> E1

    # Cross-column links that would otherwise cut through Phase B or C boxes
    # are routed orthogonally through the clear band beneath every column.
    ab, bc, cd = 96, 202, 308           # inter-column lanes
    route(d, [(COLS["A"] + W, ROW[3] + H / 2), (ab, ROW[3] + H / 2),
              (ab, 60), (196, 60), (196, ROW[0] + H / 2),
              (COLS["C"], ROW[0] + H / 2)])                      # A4 -> C1
    route(d, [(COLS["A"] + W, ROW[2] + H / 2), (ab + 12, ROW[2] + H / 2),
              (ab + 12, 72), (bc + 6, 72), (bc + 6, ROW[1] + H / 2),
              (COLS["C"], ROW[1] + H / 2)])                      # A3 -> C2
    route(d, [(COLS["B"] + W / 2, ROW[3]), (COLS["B"] + W / 2, 84),
              (cd, 84), (cd, ROW[1] + H / 2),
              (COLS["D"], ROW[1] + H / 2)])                      # B4 -> D2
    route(d, [(COLS["C"] + W / 2, ROW[2]), (COLS["C"] + W / 2, 96),
              (cd - 8, 96), (cd - 8, ROW[0] + H / 2),
              (COLS["D"], ROW[0] + H / 2)])                      # C3 -> D1

    note(d, 441, 62, "Phase E reads upward", fs=6.2)
    note(d, 240, 30,
         "Solid arrows = build dependency; they match the Depends-on column of section 8.",
         fs=6.5, color=INK)
    note(d, 240, 18,
         "Critical path  A1 > A2 > A3 > C2 > C3 > D3 > D4 > E1 > E2 > E4.", fs=6.5, color=INK)
    note(d, 240, 6,
         "Phase B runs parallel to A after A1; D2, D3 and D5 are mutually independent after C3.",
         fs=6.5)
    return d


DIAGRAMS = {
    "context": (diagram_context,
                "Figure 1 - System context: every external source deposits bytes into "
                "civ_artifact before any finding may cite it."),
    "erd": (diagram_erd,
            "Figure 2 - Entity model: civ_finding is the hub; the citation_gate CHECK makes an "
            "uncited value unstorable."),
    "routing": (diagram_routing,
                "Figure 3 - Behavior: dependency-driven dispatch, SCR-01 as the disqualifier "
                "gate, PC-22 as the release gate."),
    "wbs": (diagram_wbs,
            "Figure 4 - Work-package dependency graph (19 packages across 5 phases)."),
}
