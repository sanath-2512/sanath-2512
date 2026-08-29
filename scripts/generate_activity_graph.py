#!/usr/bin/env python3
"""Generate a themed GitHub contribution visualization SVG."""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

USERNAME = "sanath-2512"
API_URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "activity-graph.svg"

# Theme: dark futuristic cyan/violet
COLORS = ["#0f172a", "#1e293b", "#164e63", "#0891b2", "#00d4ff"]
BG = "#0d1117"
TEXT = "#94a3b8"
TITLE = "#e2e8f0"
LINE = "#00d4ff"
POINT = "#8b5cf6"
ACCENT = "#22d3ee"


def fetch_contributions() -> dict:
    with urllib.request.urlopen(API_URL, timeout=30) as resp:
        return json.load(resp)


def level_color(count: int, max_count: int) -> str:
    if count == 0:
        return COLORS[0]
    idx = min(len(COLORS) - 1, max(1, round((count / max(max_count, 1)) * (len(COLORS) - 1))))
    return COLORS[idx]


def build_svg(data: dict) -> str:
    contribs = data["contributions"]
    total = data["total"].get("lastYear", sum(c["count"] for c in contribs))
    max_count = max((c["count"] for c in contribs), default=1)

    # Last 31 days for line chart
    recent = contribs[-31:]
    chart_w, chart_h = 740, 120
    chart_x, chart_y = 40, 48
    points = []
    for i, day in enumerate(recent):
        x = chart_x + (i / max(len(recent) - 1, 1)) * chart_w
        y = chart_y + chart_h - (day["count"] / max(max_count, 1)) * (chart_h - 10)
        points.append((x, y, day["count"]))

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    area = polyline + f" {chart_x + chart_w:.1f},{chart_y + chart_h:.1f} {chart_x:.1f},{chart_y + chart_h:.1f}"

    # Heatmap: last 26 weeks
    weeks = [contribs[i : i + 7] for i in range(max(0, len(contribs) - 26 * 7), len(contribs), 7)]
    cell, gap = 11, 3
    heat_x, heat_y = 40, 200

    heat_cells = []
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = heat_x + wi * (cell + gap)
            y = heat_y + di * (cell + gap)
            heat_cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{level_color(day["count"], max_count)}"/>'
            )

    point_dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{POINT}" opacity="0.9"/>'
        for x, y, c in points if c > 0
    )

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 290" role="img" aria-label="Contribution activity">
  <defs>
    <linearGradient id="panel" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00d4ff" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#00d4ff" stop-opacity="0"/>
    </linearGradient>
    <style>
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
      .pulse {{ animation: pulse 3s ease-in-out infinite; }}
      @keyframes pulse {{ 0%,100% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} }}
    </style>
  </defs>
  <rect width="820" height="290" rx="12" fill="url(#panel)"/>
  <text x="40" y="28" class="mono" fill="{TITLE}" font-size="13" letter-spacing="2">CONTRIBUTION ACTIVITY</text>
  <text x="780" y="28" text-anchor="end" class="mono" fill="{ACCENT}" font-size="11">{total} commits / last 12 months</text>

  <line x1="40" y1="{chart_y + chart_h}" x2="780" y2="{chart_y + chart_h}" stroke="#1f2937" stroke-width="1"/>
  <polygon points="{area}" fill="url(#areaGrad)"/>
  <polyline points="{polyline}" fill="none" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>
  {point_dots}
  <text x="40" y="{chart_y + chart_h + 18}" class="mono" fill="{TEXT}" font-size="10">31-day activity trend</text>

  {''.join(heat_cells)}
  <text x="40" y="278" class="mono" fill="{TEXT}" font-size="10">contribution heatmap / updated {updated}</text>
  <circle cx="770" cy="278" r="3" fill="{ACCENT}" class="pulse"/>
</svg>
'''


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT
    data = fetch_contributions()
    svg = build_svg(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
