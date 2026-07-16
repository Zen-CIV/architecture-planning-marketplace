#!/usr/bin/env python3
"""Config-driven Architecture & Build Plan PDF renderer.

Usage:
    python3 render_pdf.py --config doc.json

Config keys: title, subtitle, version, date, footer, meta (list of [key, value]),
sources (list of {path, shift, skip_until?}), diagrams_module (optional), output.

Markdown support: #..#### headings, pipe tables, fenced code blocks (auto-chunked
across pages), bullet/numbered lists, checkboxes, blockquotes, ---, **bold**,
`inline code`, and @@DIAGRAM:name@@ markers resolved via the diagrams module's
DIAGRAMS = {name: (draw_fn, caption)} dict.

Built-in hard-won fixes: PDF outline level clamping, TOC counter reset across
multiBuild passes, oversized-code-block chunking, cp1252 glyph sanitization.
"""
import argparse
import html
import importlib.util
import json
import math
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String  # noqa: F401 (re-exported)
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle, XPreformatted)
from reportlab.platypus.tableofcontents import TableOfContents

PAGE_W, PAGE_H = letter
M_L, M_R, M_T, M_B = 0.85 * inch, 0.85 * inch, 0.9 * inch, 0.8 * inch
AVAIL = PAGE_W - M_L - M_R

INK = colors.HexColor("#1c2733")
MUTED = colors.HexColor("#5a6b7d")
ACCENT = colors.HexColor("#2c5f8a")
BOX_FILL = colors.HexColor("#eaf0f7")
BOX_EDGE = colors.HexColor("#5b7da3")
CODE_BG = colors.HexColor("#f5f6f8")
GRID = colors.HexColor("#c3cdd8")
HEAD_BG = colors.HexColor("#e6ecf3")

SANITIZE = {"→": "->", "←": "<-", "⇒": "=>", "‖": " | ", "∥": " | ",
            "≤": "<=", "≥": ">=", "∈": "in", "☐": "[ ]", " ": " ",
            "‘": "'", "’": "'", "“": '"', "”": '"', "✓": "OK", "✗": "X"}


def sanitize(text):
    for k, v in SANITIZE.items():
        text = text.replace(k, v)
    # Replace anything the built-in fonts can't render (avoids black boxes).
    return text.encode("cp1252", "replace").decode("cp1252")


S = {
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.6,
                           textColor=INK, spaceAfter=6),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=13.2,
                             textColor=INK, leftIndent=16, bulletIndent=6, spaceAfter=3),
    "quote": ParagraphStyle("quote", fontName="Helvetica-Oblique", fontSize=9, leading=12.6,
                            textColor=MUTED, leftIndent=14, spaceAfter=6, borderPadding=4),
    "H1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15.5, leading=19,
                         textColor=ACCENT, spaceBefore=20, spaceAfter=8, keepWithNext=1),
    "H2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=15,
                         textColor=INK, spaceBefore=14, spaceAfter=6, keepWithNext=1),
    "H3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=10.2, leading=13,
                         textColor=ACCENT, spaceBefore=11, spaceAfter=4, keepWithNext=1),
    "H4": ParagraphStyle("H4", fontName="Helvetica-BoldOblique", fontSize=9.5, leading=12.4,
                         textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7, leading=8.9, textColor=INK),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.6, leading=9.6,
                           textColor=INK),
    "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=7.6, leading=9.6,
                            textColor=INK),
    "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=8,
                              leading=10.5, textColor=MUTED, spaceBefore=3, spaceAfter=10,
                              alignment=1),
}


def inline(text):
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`",
               r'<font face="Courier" size="8.3" color="#20486e">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def wrap_code(code, width=100):
    out = []
    for line in code.split("\n"):
        while len(line) > width:
            out.append(line[:width])
            line = "    " + line[width:]
        out.append(line)
    return "\n".join(out)


def code_block(code):
    """Fenced code -> boxed monospace, chunked so no block exceeds a page."""
    lines = wrap_code(code.rstrip()).split("\n")
    out = []
    CHUNK = 62
    for c0 in range(0, len(lines), CHUNK):
        pre = XPreformatted(html.escape("\n".join(lines[c0:c0 + CHUNK])), S["code"])
        tbl = Table([[pre]], colWidths=[AVAIL])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, GRID),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        out.append(tbl)
    out.append(Spacer(1, 6))
    return out


def md_table(rows):
    ncols = max(len(r) for r in rows)
    weights = [1.0] * ncols
    for r in rows:
        for i in range(ncols):
            cell = r[i] if i < len(r) else ""
            weights[i] = max(weights[i], min(len(cell), 60))
    total = sum(weights)
    widths = [max(AVAIL * w / total, 0.55 * inch) for w in weights]
    over = sum(widths) - AVAIL
    if over > 0:
        widths = [w - over * (w / sum(widths)) for w in widths]
    data = []
    for ri, r in enumerate(rows):
        style = S["cellh"] if ri == 0 else S["cell"]
        data.append([Paragraph(inline(r[i]) if i < len(r) else "", style)
                     for i in range(ncols)])
    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [tbl, Spacer(1, 8)]


# ---------- diagram helper API (import these from diagrams.py) ----------

def dbox(d, x, y, w, h, lines, fill=BOX_FILL, edge=BOX_EDGE, fs=7.2, bold=True):
    d.add(Rect(x, y, w, h, rx=3, ry=3, fillColor=fill, strokeColor=edge, strokeWidth=0.9))
    n = len(lines)
    lh = fs + 2.2
    y0 = y + h / 2 + (n - 1) * lh / 2 - fs * 0.36
    for i, ln in enumerate(lines):
        d.add(String(x + w / 2, y0 - i * lh, ln, textAnchor="middle",
                     fontName="Helvetica-Bold" if (bold and i == 0) else "Helvetica",
                     fontSize=fs, fillColor=INK))


def arrow(d, x1, y1, x2, y2, color=BOX_EDGE, dashed=False, width=0.9):
    ln = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width)
    if dashed:
        ln.strokeDashArray = [2.5, 2.5]
    d.add(ln)
    ang = math.atan2(y2 - y1, x2 - x1)
    L, W = 5.5, 2.6
    d.add(Polygon([x2, y2,
                   x2 - L * math.cos(ang) + W * math.sin(ang),
                   y2 - L * math.sin(ang) - W * math.cos(ang),
                   x2 - L * math.cos(ang) - W * math.sin(ang),
                   y2 - L * math.sin(ang) + W * math.cos(ang)],
                  fillColor=color, strokeColor=None))


def note(d, x, y, text, fs=6.6, anchor="middle", color=MUTED):
    d.add(String(x, y, text, textAnchor=anchor, fontName="Helvetica-Oblique",
                 fontSize=fs, fillColor=color))


# ---------- markdown -> flowables ----------

def render_md(text, diagrams, shift=0):
    story = []
    lines = sanitize(text).split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        m = re.match(r"@@DIAGRAM:(\w+)@@", stripped)
        if m:
            name = m.group(1)
            if name not in diagrams:
                raise SystemExit(f"@@DIAGRAM:{name}@@ has no entry in DIAGRAMS")
            fn, cap = diagrams[name]
            story.append(Spacer(1, 6))
            story.append(fn())
            story.append(Paragraph(sanitize(cap), S["caption"]))
            i += 1
            continue
        if stripped.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            story.extend(code_block("\n".join(buf)))
            continue
        hm = re.match(r"^(#{1,4})\s+(.*)", ln)
        if hm:
            lvl = min(len(hm.group(1)) + shift, 4)
            if shift and len(hm.group(1)) >= 3:
                lvl = 3
            story.append(Paragraph(inline(hm.group(2)), S[f"H{lvl}"]))
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|$", lines[i].strip()):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            story.extend(md_table(rows))
            continue
        if stripped in ("---", "***"):
            story.append(HRFlowable(width="100%", thickness=0.6, color=GRID,
                                    spaceBefore=8, spaceAfter=8))
            i += 1
            continue
        if stripped.startswith(">"):
            story.append(Paragraph(inline(stripped.lstrip("> ")), S["quote"]))
            i += 1
            continue
        bm = re.match(r"^\s*[-*]\s+(\[.\]\s+)?(.*)", ln)
        if bm and stripped.startswith(("-", "*")):
            prefix = "[ ] " if bm.group(1) else ""
            story.append(Paragraph(inline(prefix + bm.group(2)), S["bullet"],
                                   bulletText="•" if not prefix else " "))
            i += 1
            continue
        nm = re.match(r"^\s*(\d+)\.\s+(.*)", ln)
        if nm:
            story.append(Paragraph(inline(nm.group(2)), S["bullet"],
                                   bulletText=nm.group(1) + "."))
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        para = [stripped]
        while i + 1 < len(lines) and lines[i + 1].strip() and \
                not re.match(r"^(#{1,4}\s|```|\||[-*]\s|>\s?|\d+\.\s|---$|@@)",
                             lines[i + 1].strip()):
            i += 1
            para.append(lines[i].strip())
        story.append(Paragraph(inline(" ".join(para)), S["body"]))
        i += 1
    return story


# ---------- document ----------

class ArchDoc(BaseDocTemplate):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._tocn = 0
        self._lastlvl = 0

    def beforeDocument(self):
        # multiBuild runs several passes; keys must be identical across passes
        # or TOC entries never resolve.
        self._tocn = 0
        self._lastlvl = 0

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ("H1", "H2", "H3"):
            lvl = {"H1": 0, "H2": 1, "H3": 2}[fl.style.name]
            # PDF outlines forbid level jumps (0 -> 2); clamp.
            lvl = min(lvl, self._lastlvl + 1)
            self._lastlvl = lvl
            text = fl.getPlainText()
            self._tocn += 1
            key = f"toc{self._tocn}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text[:80], key, lvl, closed=(lvl >= 1))
            self.notify("TOCEntry", (lvl, text, self.page, key))


def make_on_page(footer):
    def on_page(canv, doc):
        if doc.page == 1:
            return
        canv.saveState()
        canv.setFont("Helvetica", 7)
        canv.setFillColor(MUTED)
        canv.drawString(M_L, PAGE_H - 0.55 * inch, footer)
        canv.drawRightString(PAGE_W - M_R, 0.5 * inch, f"Page {doc.page}")
        canv.setStrokeColor(GRID)
        canv.setLineWidth(0.5)
        canv.line(M_L, PAGE_H - 0.62 * inch, PAGE_W - M_R, PAGE_H - 0.62 * inch)
        canv.restoreState()
    return on_page


def cover(cfg):
    st_title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=24, leading=30,
                              textColor=ACCENT, spaceAfter=10)
    st_sub = ParagraphStyle("s", fontName="Helvetica", fontSize=12.5, leading=18,
                            textColor=INK, spaceAfter=26)
    story = [Spacer(1, 1.7 * inch),
             Paragraph(inline(sanitize(cfg["title"])), st_title),
             Paragraph(inline(sanitize(cfg.get("subtitle", ""))), st_sub),
             HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=22)]
    meta = [["Version", cfg.get("version", "1.0")], ["Date", cfg.get("date", "")]]
    meta += [list(row) for row in cfg.get("meta", [])]
    t = Table([[Paragraph(f"<b>{html.escape(k)}</b>", S["cell"]),
                Paragraph(inline(sanitize(v)), S["cell"])] for k, v in meta],
              colWidths=[1.1 * inch, AVAIL - 1.1 * inch])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.4, GRID)]))
    story.append(t)
    story.append(PageBreak())
    return story


def load_diagrams(cfg, base):
    if not cfg.get("diagrams_module"):
        return {}
    path = os.path.join(base, cfg["diagrams_module"])
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)
    spec = importlib.util.spec_from_file_location("project_diagrams", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "DIAGRAMS", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    base = os.path.dirname(os.path.abspath(args.config))
    with open(args.config) as f:
        cfg = json.load(f)
    diagrams = load_diagrams(cfg, base)

    out = os.path.join(base, cfg["output"])
    doc = ArchDoc(out, pagesize=letter, leftMargin=M_L, rightMargin=M_R,
                  topMargin=M_T, bottomMargin=M_B,
                  title=cfg["title"], author=cfg.get("author", ""))
    frame = Frame(M_L, M_B, AVAIL, PAGE_H - M_T - M_B, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame],
                                       onPage=make_on_page(sanitize(cfg.get("footer", cfg["title"]))))])

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("t0", fontName="Helvetica-Bold", fontSize=10, leading=15,
                       textColor=INK, leftIndent=2),
        ParagraphStyle("t1", fontName="Helvetica", fontSize=9, leading=13,
                       textColor=INK, leftIndent=16),
        ParagraphStyle("t2", fontName="Helvetica", fontSize=8, leading=11.5,
                       textColor=MUTED, leftIndent=30),
    ]

    story = cover(cfg)
    story.append(Paragraph("Contents", S["H1"]))
    story.append(toc)
    story.append(PageBreak())

    for src in cfg["sources"]:
        with open(os.path.join(base, src["path"])) as f:
            text = f.read()
        if src.get("skip_until"):
            m = re.search(src["skip_until"], text)
            if m:
                text = text[m.start():]
        story.extend(render_md(text, diagrams, shift=src.get("shift", 0)))

    doc.multiBuild(story)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
