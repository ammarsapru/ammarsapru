"""Draws the Evidence Room profile images from profile.json.

Outputs (assets/): hero.svg, case-<id>.svg, bench.svg, record.svg, receipt.svg
Run: python scripts/build_assets.py
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

BOARD, BOARD_2, LINE = "#0b0b0c", "#121214", "#2b2b30"
PAPER, AGED, MANILA, SHADOW = "#f3ead9", "#e9dcc3", "#dccfb0", "#c4b492"
THREAD, BRIGHT, LEAD = "#4f9bea", "#9ad4ff", "#3a6a9e"
INK, INK_SOFT, INK_FAINT = "#16161a", "#3c3c42", "#5a5a60"
CHALK, CHALK_MUTED = "#e9e8e3", "#a3a3a0"
TYPE = "'Courier New', Courier, monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', monospace"


def t(x, y, s, size=14, fill=INK, font=SANS, weight=400, anchor="start", ls=0, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{escape(str(s))}</text>')


def lines(x, y, s, width, size=14, lh=1.45, **kw):
    out = []
    for i, ln in enumerate(textwrap.wrap(s, width)):
        out.append(t(x, y + i * size * lh, ln, size, **kw))
    return "\n".join(out), len(textwrap.wrap(s, width))


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>\n{body}\n</svg>\n')


def grid(w, h, step=60):
    g = [f'<rect width="{w}" height="{h}" rx="14" fill="{BOARD}"/>', f'<g stroke="#18181b" stroke-width="1">']
    g += [f'<path d="M0 {y}H{w}"/>' for y in range(step, h, step)]
    g += [f'<path d="M{x} 0V{h}"/>' for x in range(step, w, step)]
    g.append("</g>")
    return "\n".join(g)


def card(x, y, w, h, rot, paper, no, name, ev):
    return (f'<g transform="translate({x} {y}) rotate({rot} {w/2} {h/2})">'
            f'<rect x="3" y="7" width="{w}" height="{h}" fill="#000" opacity="0.45"/>'
            f'<rect width="{w}" height="{h}" fill="{paper}"/>'
            f'<circle cx="{w/2}" cy="8" r="5" fill="{BRIGHT}" stroke="{LEAD}" stroke-width="1.5"/>'
            + t(14, 30, no, 10, INK_FAINT, TYPE, 700, ls=2)
            + t(14, 52, name, 17, INK, SANS, 800)
            + t(14, 74, ev, 12, "#22384f", TYPE, 700)
            + "</g>")


def hero(p):
    W, H = 1200, 460
    pins = [(70, 48, -4, PAPER), (930, 40, 3, AGED), (60, 312, 3, AGED), (950, 300, -3, PAPER), (470, 352, 1.5, MANILA)]
    cw, ch = 200, 88
    cx, cy = 600, 200
    body = [grid(W, H)]
    # threads: animated "being drawn" stroke, then a slow glow
    body.append(f'<g fill="none" stroke="{THREAD}" stroke-width="1.8" stroke-linecap="round">')
    for i, (x, y, *_r) in enumerate(pins):
        px, py = x + cw / 2, y + 8
        d = f"M{cx} {cy} Q{(cx + px) / 2} {min(cy, py) - 40 if py < cy else max(cy, py) + 10} {px} {py}"
        body.append(f'<path d="{d}" stroke-dasharray="900" stroke-dashoffset="900">'
                    f'<animate attributeName="stroke-dashoffset" from="900" to="0" dur="1.6s" begin="{0.2 + i * 0.25:.2f}s" fill="freeze"/></path>')
    body.append("</g>")
    body.append(f'<g fill="none" stroke="{LEAD}" stroke-width="1" stroke-dasharray="4 5" opacity="0.8">'
                f'<path d="M170 140 Q150 230 160 312"/><path d="M1030 132 Q1060 220 1050 300"/></g>')
    for i, ((x, y, r, paper), c) in enumerate(zip(pins, p["cases"])):
        body.append(card(x, y, cw, ch, r, paper, f"CASE No. {c['no']}", c["name"], f"{c['metric']}"))
    # center: the investigator
    body.append(f'<g transform="translate(470 108) rotate(-1.5 130 95)">'
                f'<rect x="4" y="9" width="260" height="190" fill="#000" opacity="0.5"/>'
                f'<rect width="260" height="190" fill="{PAPER}"/>'
                f'<circle cx="130" cy="9" r="6" fill="{BRIGHT}" stroke="{LEAD}" stroke-width="1.5"/>'
                + t(18, 36, "THE INVESTIGATOR", 11, INK_FAINT, TYPE, 700, ls=3)
                + t(18, 74, p["name"], 30, INK, SANS, 800)
                + t(18, 100, "AI/ML engineer", 14, INK_SOFT, SANS, 600)
                + t(18, 120, "Penn State · Lahore", 13, INK_SOFT, SANS)
                + f'<g transform="rotate(-5 120 160)"><rect x="18" y="140" width="214" height="30" fill="none" stroke="#1d4f91" stroke-width="2.5"/>'
                + t(125, 161, "CLEARED FOR PRODUCTION", 13, "#1d4f91", TYPE, 700, "middle", 1.5) + "</g></g>")
    body.append(t(28, H - 22, f"CASE OPEN · {p['case_id']}", 12, BRIGHT, TYPE, 700, ls=3))
    body.append(t(W - 28, H - 22, "every pin on the wall is a case", 12, CHALK_MUTED, TYPE, 400, "end"))
    return svg(W, H, "\n".join(body), f"{p['name']}, the investigation board")


def case_svg(c):
    W, H = 580, 300
    b = [f'<rect width="{W}" height="{H}" rx="4" fill="{PAPER}"/>',
         f'<rect width="{W}" height="12" rx="4" fill="{MANILA}"/>',
         t(24, 42, f"CASE FILE No. {c['no']}", 11, INK_FAINT, TYPE, 700, ls=2.5),
         t(W - 24, 42, c["status"], 11, INK_FAINT, TYPE, 700, "end", 2),
         t(24, 76, c["name"], 26, INK, SANS, 800)]
    txt, n = lines(24, 106, "The problem. " + c["problem"], 66, 14, fill=INK_SOFT)
    b.append(txt)
    y = 106 + n * 20 + 12
    b.append(f'<path d="M24 {y}H{W - 24}" stroke="{SHADOW}" stroke-dasharray="5 4"/>')
    b.append(t(24, y + 26, "EVIDENCE", 11, INK_FAINT, TYPE, 700, ls=2.5))
    b.append(t(24, y + 62, c["metric"], 32, INK, SANS, 800))
    b.append(t(24, y + 86, c["metric_note"], 13, INK_SOFT, SANS))
    b.append(t(24, H - 22, " · ".join(c["stack"]), 12, "#22384f", MONO, 600))
    b.append(t(W - 24, H - 22, "open file ▸", 13, "#1d4f91", SANS, 700, "end"))
    return svg(W, H, "\n".join(b), f"Case file {c['no']}: {c['name']}")


def bench(p):
    tools = p["tools"]
    cols, kw, kh, gap = 5, 214, 58, 12
    rows = -(-len(tools) // cols)
    W, H = cols * kw + (cols - 1) * gap + 48, rows * (kh + gap) + 40
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}"/>']
    for i, tool in enumerate(tools):
        r, c = divmod(i, cols)
        x, y = 24 + c * (kw + gap), 22 + r * (kh + gap)
        b.append(f'<rect x="{x}" y="{y + 5}" width="{kw}" height="{kh}" rx="9" fill="#050506"/>')
        b.append(f'<rect x="{x}" y="{y}" width="{kw}" height="{kh}" rx="9" fill="#18181c" stroke="{LINE}"/>')
        b.append(t(x + 14, y + 35, tool, 16, CHALK, MONO, 600))
    return svg(W, H, "\n".join(b), "Tools on the evidence bench: " + ", ".join(tools))


def record(p):
    W, rowh = 720, 92
    H = 40 + rowh * len(p["record"])
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}"/>',
         f'<path d="M40 30V{H - 30}" stroke="{THREAD}" stroke-width="2"/>']
    for i, (when, role, what) in enumerate(p["record"]):
        y = 44 + i * rowh
        b.append(f'<circle cx="40" cy="{y}" r="7" fill="{BOARD}" stroke="{BRIGHT}" stroke-width="2.5"/>')
        b.append(t(64, y + 5, when, 13, CHALK_MUTED, TYPE, 700))
        b.append(t(64, y + 30, role, 18, CHALK, SANS, 700))
        txt, _ = lines(64, y + 52, what, 78, 13, fill="#bdbcb7")
        b.append(txt)
    return svg(W, H, "\n".join(b), "The record: " + "; ".join(r[1] for r in p["record"]))


def receipt(p):
    W = 380
    rows = p["receipt"]
    H = 150 + 30 * len(rows) + 72
    step = 10
    zig = " ".join(f"L{x} {H - 8 if (x // step) % 2 == 0 else H}" for x in range(W, -1, -step))
    b = [f'<path d="M0 0H{W}V{H - 8} {zig} L0 {H - 8}Z" fill="#fbf8f1"/>',
         t(W / 2, 44, f"RECORD · {p['case_id']}", 16, INK, TYPE, 700, "middle", 3),
         t(W / 2, 68, p["name"].upper(), 13, INK_FAINT, TYPE, 700, "middle", 1),
         f'<path d="M24 92H{W - 24}" stroke="#9a9a98" stroke-dasharray="4 4"/>']
    for i, (k, v) in enumerate(rows):
        y = 124 + i * 30
        b.append(t(24, y, k, 13, INK, TYPE, 400))
        b.append(t(W - 24, y, v, 13, INK, TYPE, 700, "end"))
    y = 124 + len(rows) * 30
    b.append(f'<path d="M24 {y - 10}H{W - 24}" stroke="#9a9a98" stroke-dasharray="4 4"/>')
    b.append(t(24, y + 18, "STATUS", 14, INK, TYPE, 700))
    b.append(t(W - 24, y + 18, "AVAILABLE · S27", 14, INK, TYPE, 700, "end"))
    b.append(t(W / 2, y + 58, "THANK YOU FOR INVESTIGATING", 11, INK_FAINT, TYPE, 700, "middle", 2))
    return svg(W, H, "\n".join(b), "Record summary: " + "; ".join(f"{k} {v}" for k, v in rows))


def main():
    p = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(p), encoding="utf-8")
    for c in p["cases"]:
        (OUT / f"case-{c['id']}.svg").write_text(case_svg(c), encoding="utf-8")
    (OUT / "bench.svg").write_text(bench(p), encoding="utf-8")
    (OUT / "record.svg").write_text(record(p), encoding="utf-8")
    (OUT / "receipt.svg").write_text(receipt(p), encoding="utf-8")
    print("assets written:", sorted(f.name for f in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()
