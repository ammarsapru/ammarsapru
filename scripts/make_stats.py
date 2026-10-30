"""Reads your GitHub account and draws stats.svg, languages.svg and activity.svg in the board style.

Runs daily in .github/workflows/profile.yml. Locally: GITHUB_TOKEN=... python scripts/make_stats.py
Uses GraphQL for the contribution calendar and commit/PR counts (needs a token; the Action's built-in
token works). Language bytes come from each of your own non-fork repos. Set STATS_TOKEN as a repo secret
(a fine-grained token with read access to your repos) to include private repos in the language mix.
Offline demo: python scripts/make_stats.py --demo
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import (BOARD, BRIGHT, CHALK, CHALK_MUTED, LEAD, LINE, MONO, SANS, THREAD, TYPE,  # noqa: E402
                          svg, t)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
API = "https://api.github.com"
# blue-only palette for languages, light to dark, so the board keeps one hue
LANG_SHADES = ["#9ad4ff", "#6fb6f5", "#4f9bea", "#3a7fc4", "#2d6399", "#22486f", "#6c6c72"]
HEAT = ["#16161a", "#1d3047", "#25507a", "#3a7fc4", "#9ad4ff"]


def _req(url, data=None):
    tok = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"User-Agent": "evidence-room-profile", "Accept": "application/vnd.github+json"})
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def collect(user: str) -> dict:
    repos, page = [], 1
    private = bool(os.environ.get("STATS_TOKEN"))
    while True:
        url = (f"{API}/user/repos?per_page=100&page={page}&affiliation=owner" if private
               else f"{API}/users/{user}/repos?per_page=100&page={page}&type=owner")
        batch = _req(url)
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r.get("fork")]
    langs: dict[str, int] = {}
    for r in own:
        try:
            for k, v in _req(r["languages_url"]).items():
                langs[k] = langs.get(k, 0) + v
        except Exception:
            pass
    for skip in ("Jupyter Notebook", "HTML", "CSS"):   # markup and notebook output would swamp real code
        langs.pop(skip, None)
    q = """query($login:String!){user(login:$login){
      contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
        restrictedContributionsCount contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST],includeUserRepositories:false){totalCount}
      followers{totalCount}}}"""
    g = _req(f"{API}/graphql", {"query": q, "variables": {"login": user}})["data"]["user"]
    cc = g["contributionsCollection"]
    return {
        "repos": len([r for r in own if not r.get("private")]),
        "private_repos": len([r for r in own if r.get("private")]),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": cc["totalPullRequestContributions"],
        "contributed_to": g["repositoriesContributedTo"]["totalCount"],
        "followers": g["followers"]["totalCount"],
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "weeks": [[d["contributionCount"] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]],
        "languages": langs,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def demo() -> dict:
    import random
    random.seed(7)
    return {"repos": 27, "private_repos": 9, "stars": 14, "commits": 912, "prs": 31, "contributed_to": 4,
            "followers": 12, "contributions": 1046,
            "weeks": [[max(0, int(random.gauss(3, 3))) if random.random() > 0.3 else 0 for _ in range(7)] for _ in range(53)],
            "languages": {"Python": 5_200_000, "TypeScript": 3_900_000, "JavaScript": 900_000, "R": 120_000,
                          "C#": 80_000, "Shell": 20_000},
            "updated": "demo data"}


def stats_svg(s: dict) -> str:
    W, H = 580, 250
    cand = [("COMMITS · 12 MO", s["commits"]), ("PULL REQUESTS", s["prs"]), ("PUBLIC REPOS", s["repos"]),
            ("REPOS CONTRIBUTED TO", s["contributed_to"]), ("CONTRIBUTIONS · 12 MO", s["contributions"]),
            ("STARS EARNED", s["stars"]), ("LANGUAGES USED", len(s["languages"])), ("FOLLOWERS", s["followers"])]
    items = [(k, f"{v:,}") for k, v in cand if v][:6]   # never show an empty zero
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}" stroke="{LINE}"/>',
         t(24, 38, "ON GITHUB", 12, CHALK_MUTED, TYPE, 700, ls=3),
         t(W - 24, 38, f"updated {s['updated']}", 11, CHALK_MUTED, TYPE, 400, "end")]
    for i, (k, v) in enumerate(items):
        col, row = i % 3, i // 3
        x, y = 24 + col * 184, 92 + row * 86
        b.append(t(x, y, v, 32, CHALK, SANS, 800))
        b.append(t(x, y + 22, k, 10.5, BRIGHT, TYPE, 700, ls=1.5))
    return svg(W, H, "\n".join(b), "GitHub activity: " + ", ".join(f"{k.lower()} {v}" for k, v in items))


def languages_svg(s: dict) -> str:
    W, H = 580, 250
    langs = sorted(s["languages"].items(), key=lambda kv: -kv[1])
    grand = sum(v for _, v in langs) or 1
    keep = [kv for kv in langs if kv[1] / grand >= 0.01][:6]          # under 1% folds into Other
    top, rest = keep, sum(v for k, v in langs if (k, v) not in keep)
    if rest / grand >= 0.005:
        top.append(("Other", rest))
    total = sum(v for _, v in top) or 1
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}" stroke="{LINE}"/>',
         t(24, 38, "LANGUAGES ON FILE", 12, CHALK_MUTED, TYPE, 700, ls=3),
         t(W - 24, 38, "by bytes, own repos", 11, CHALK_MUTED, TYPE, 400, "end")]
    x0, bw, y0 = 24, W - 48, 60
    x = x0
    b.append(f'<clipPath id="bar"><rect x="{x0}" y="{y0}" width="{bw}" height="14" rx="7"/></clipPath><g clip-path="url(#bar)">')
    for i, (name, v) in enumerate(top):
        w = bw * v / total
        b.append(f'<rect x="{x:.1f}" y="{y0}" width="{w + 0.5:.1f}" height="14" fill="{LANG_SHADES[i % len(LANG_SHADES)]}"/>')
        x += w
    b.append("</g>")
    for i, (name, v) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 24 + col * 272, 108 + row * 34
        b.append(f'<rect x="{lx}" y="{ly - 11}" width="12" height="12" rx="3" fill="{LANG_SHADES[i % len(LANG_SHADES)]}"/>')
        b.append(t(lx + 22, ly, name, 15, CHALK, SANS, 600))
        b.append(t(lx + 248, ly, f"{100 * v / total:.1f}%", 14, BRIGHT, MONO, 600, "end"))
    return svg(W, H, "\n".join(b), "Top languages: " + ", ".join(f"{n} {100 * v / total:.0f}%" for n, v in top))


def activity_svg(s: dict) -> str:
    weeks = s["weeks"][-53:]
    cell, gap = 15, 4
    W = 48 + len(weeks) * (cell + gap)
    H = 60 + 7 * (cell + gap) + 30
    peak = max([c for w in weeks for c in w] or [1]) or 1
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BOARD}" stroke="{LINE}"/>',
         t(24, 36, "CASE LOG · LAST 12 MONTHS", 12, CHALK_MUTED, TYPE, 700, ls=3),
         t(W - 24, 36, f"{s['contributions']:,} contributions", 12, BRIGHT, TYPE, 700, "end")]
    for wi, w in enumerate(weeks):
        for di, c in enumerate(w):
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            x, y = 24 + wi * (cell + gap), 52 + di * (cell + gap)
            b.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{HEAT[lvl]}"/>')
    ly = H - 18
    b.append(t(W - 24 - 5 * (cell + gap) - 44, ly + 2, "less", 11, CHALK_MUTED, TYPE, 400, "end"))
    for i, c in enumerate(HEAT):
        b.append(f'<rect x="{W - 24 - 5 * (cell + gap) - 36 + i * (cell + gap)}" y="{ly - 11}" width="{cell - 3}" height="{cell - 3}" rx="3" fill="{c}"/>')
    b.append(t(W - 24, ly + 2, "more", 11, CHALK_MUTED, TYPE, 400, "end"))
    return svg(W, H, "\n".join(b), f"{s['contributions']} contributions in the last 12 months")


def main():
    p = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    s = demo() if "--demo" in sys.argv else collect(p["user"])
    OUT.mkdir(exist_ok=True)
    (OUT / "stats.svg").write_text(stats_svg(s), encoding="utf-8")
    (OUT / "languages.svg").write_text(languages_svg(s), encoding="utf-8")
    (OUT / "activity.svg").write_text(activity_svg(s), encoding="utf-8")
    print("stats written:", {k: v for k, v in s.items() if k not in ("weeks", "languages")}, "languages:", list(s["languages"])[:8])


if __name__ == "__main__":
    main()
